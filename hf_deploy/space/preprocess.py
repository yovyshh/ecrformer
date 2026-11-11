import os
from pathlib import Path
from typing import BinaryIO, Dict, Any, Union
import numpy as np
import torch
import torchvision.transforms.functional as TF


def load_sample_npz(
    source: Union[str, Path, BinaryIO],
    dilation_radius: int = 2,
    sar_norm: str = "paper_exact",
) -> Dict[str, Any]:
    """
    Load and preprocess a sample from a SEN12MS-CR .npz file mirroring the evaluation path
    of CachedSEN12MSCRDataset (backend/data/cache_dataset.py).

    Returns a dict with:
      - s2_cloudy: batched float32 tensor [1, 4, 256, 256] in [0, 1] reflectance
      - s1: batched float32 tensor [1, 2, 256, 256] normalized SAR in [0, 1]
      - mask: batched float32 tensor [1, 1, 256, 256] soft cloud mask in [0, 1]
      - target: batched float32 tensor [1, 4, 256, 256] in [0, 1] reflectance
      - cf: float cloud fraction in [0, 1]
    """
    if isinstance(source, (str, Path)):
        if not os.path.exists(source):
            raise ValueError(f"Sample file not found: {source}")
        data = np.load(source)
    else:
        data = np.load(source)

    # 1. Key validation
    required_keys = {"s2_cloudy", "s1", "s2_clear", "mask", "cf"}
    actual_keys = set(data.files)
    missing = required_keys - actual_keys
    if missing:
        raise ValueError(f"NPZ is missing required keys: {missing}. Present keys: {actual_keys}")

    # 2. Extract arrays
    s2_cloudy_np = data["s2_cloudy"]
    s1_np = data["s1"]
    s2_clear_np = data["s2_clear"]
    mask_np = data["mask"]
    cf_data = data["cf"]

    # 3. Shape validation
    if s2_cloudy_np.shape != (256, 256, 4):
        raise ValueError(f"Expected s2_cloudy shape (256, 256, 4), got {s2_cloudy_np.shape}")
    if s1_np.shape != (256, 256, 2):
        raise ValueError(f"Expected s1 shape (256, 256, 2), got {s1_np.shape}")
    if s2_clear_np.shape != (256, 256, 4):
        raise ValueError(f"Expected s2_clear shape (256, 256, 4), got {s2_clear_np.shape}")
    if mask_np.shape != (256, 256):
        raise ValueError(f"Expected mask shape (256, 256), got {mask_np.shape}")

    # 4. Dtype & Range conversion
    s2_cloudy_np = s2_cloudy_np.astype(np.float32)
    s1_np = s1_np.astype(np.float32)
    s2_clear_np = s2_clear_np.astype(np.float32)
    mask_np = mask_np.astype(np.float32)
    cf_val = float(cf_data.item() if cf_data.ndim == 0 else cf_data[0])

    if np.any(np.isnan(s2_cloudy_np)) or np.any(np.isnan(s1_np)) or np.any(np.isnan(s2_clear_np)):
        raise ValueError("Input arrays contain NaN values")

    # 5. Tensor conversion [C, H, W]
    s2_cloudy_t = torch.from_numpy(s2_cloudy_np.transpose(2, 0, 1))
    s1_t = torch.from_numpy(s1_np.transpose(2, 0, 1))
    s2_clear_t = torch.from_numpy(s2_clear_np.transpose(2, 0, 1))

    # 6. SAR Normalization
    if sar_norm == "paper_exact":
        vv = torch.clamp(s1_t[0:1], -25.0, 0.0)
        vv = (vv + 25.0) / 25.0
        vh = torch.clamp(s1_t[1:2], -35.0, 0.0)
        vh = (vh + 35.0) / 35.0
        s1_t = torch.cat([vv, vh], dim=0)
    elif sar_norm in ["paper_default", "paper"]:
        s1_t = torch.clamp(s1_t, -25.0, 0.0)
        s1_t = (s1_t + 25.0) / 25.0
    else:
        raise ValueError(f"Unsupported sar_norm: {sar_norm}")

    # 7. Standard 3-step mask refinement:
    # 1. 9x9 mean filter, threshold 0.5 (remove speckle noise)
    mask_t = torch.from_numpy(mask_np).unsqueeze(0).unsqueeze(0)
    mean_9x9 = torch.nn.functional.avg_pool2d(mask_t, kernel_size=9, stride=1, padding=4)
    cleaned = (mean_9x9 > 0.5).float()

    # 2. Morphological dilation
    if dilation_radius > 0:
        k_size = 2 * dilation_radius + 1
        dilated = torch.nn.functional.max_pool2d(cleaned, kernel_size=k_size, stride=1, padding=dilation_radius)
    else:
        dilated = cleaned

    # 3. Gaussian blur for smooth soft boundary
    blurred = TF.gaussian_blur(dilated, kernel_size=11, sigma=2.0)
    mask_refined = torch.clamp(blurred.squeeze(0), 0.0, 1.0)  # [1, 256, 256]

    return {
        "s2_cloudy": s2_cloudy_t.unsqueeze(0),   # [1, 4, 256, 256]
        "s1": s1_t.unsqueeze(0),                 # [1, 2, 256, 256]
        "mask": mask_refined.unsqueeze(0),       # [1, 1, 256, 256]
        "target": s2_clear_t.unsqueeze(0),       # [1, 4, 256, 256]
        "cf": cf_val,
    }

