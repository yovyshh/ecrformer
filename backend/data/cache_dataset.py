import os
import glob
import numpy as np
import torch
import torchvision.transforms.functional as TF
from torch.utils.data import Dataset

class CachedSEN12MSCRDataset(Dataset):
    """
    Dataset loader for pre-cached SEN12MS-CR patches (cache_fall_v3).

    Returns:
      - s2_cloudy: [4, 256, 256] float32 in [0, 1] reflectance
      - s1:        [2, 256, 256] float32 SAR in dB
      - s2_clear:  [4, 256, 256] float32 in [0, 1] reflectance
      - cf:        float32 cloud fraction
      - mask:      [1, 256, 256] float32 soft cloud mask in [0, 1]
    """
    def __init__(self, split_dir: str, dilation_radius: int = 2, sar_norm: str = 'paper',
                 crop_size: int = None, deterministic: bool = False):
        """Cached SEN12MS-CR loader.

        crop_size:     If set, return a square crop of this size. The SAME spatial
                       window is applied to s2_cloudy, s1, s2_clear and mask so all
                       four tensors stay pixel-aligned. None = full resolution (default).
        deterministic: If True (use for validation), the crop window is fixed to the
                       image centre so repeated evaluations see identical data.
                       If False (use for training), the window is sampled randomly.
        """
        if not os.path.exists(split_dir):
            raise FileNotFoundError(f"Cache directory does not exist: {split_dir}")

        self.files = sorted(glob.glob(os.path.join(split_dir, "*.npz")))
        if len(self.files) == 0:
            raise ValueError(f"No .npz files found in {split_dir}")

        self.dilation_radius = dilation_radius
        self.sar_norm = sar_norm
        self.crop_size = crop_size
        self.deterministic = deterministic

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        data = np.load(self.files[idx])
        s2_cloudy = data['s2_cloudy'].astype(np.float32) # [256, 256, 4]
        s1 = data['s1'].astype(np.float32)               # [256, 256, 2]
        s2_clear = data['s2_clear'].astype(np.float32)   # [256, 256, 4]
        cf = float(data['cf'].item() if data['cf'].ndim == 0 else data['cf'][0])
        mask_np = data['mask'].astype(np.float32)        # [256, 256]

        s2_cloudy_t = torch.from_numpy(s2_cloudy.transpose(2, 0, 1)) # [4, 256, 256]
        s1_t = torch.from_numpy(s1.transpose(2, 0, 1))               # [2, 256, 256]
        s2_clear_t = torch.from_numpy(s2_clear.transpose(2, 0, 1))   # [4, 256, 256]

        # On-the-fly SAR Normalization:
        # 'paper_exact': paper written specification: VV [-25.0, 0.0] dB -> [0, 1], VH [-35.0, 0.0] dB -> [0, 1]
        # 'paper_default' / 'paper': official repo default: both VV & VH [-25.0, 0.0] dB -> [0, 1]
        # 'sen12ms_resnet': official SEN12MS separate clipping: VV [-25.0, 0.0] dB, VH [-32.5, 0.0] dB -> [0, 1]
        # 'raw': keep raw dB values as stored in cache (approx -37 dB to 0 dB)
        if self.sar_norm == 'paper_exact':
            vv = torch.clamp(s1_t[0:1], -25.0, 0.0)
            vv = (vv + 25.0) / 25.0
            vh = torch.clamp(s1_t[1:2], -35.0, 0.0)
            vh = (vh + 35.0) / 35.0
            s1_t = torch.cat([vv, vh], dim=0)
        elif self.sar_norm in ['paper_default', 'paper']:
            s1_t = torch.clamp(s1_t, -25.0, 0.0)
            s1_t = (s1_t + 25.0) / 25.0
        elif self.sar_norm == 'sen12ms_resnet':
            vv = torch.clamp(s1_t[0:1], -25.0, 0.0)
            vv = (vv + 25.0) / 25.0
            vh = torch.clamp(s1_t[1:2], -32.5, 0.0)
            vh = (vh + 32.5) / 32.5
            s1_t = torch.cat([vv, vh], dim=0)
        elif self.sar_norm == 'raw':
            pass
        else:
            raise ValueError(f"Unknown sar_norm mode: {self.sar_norm}. Choose 'paper_exact', 'paper_default', 'sen12ms_resnet', or 'raw'.")

        # Standard 3-step mask refinement matching U-Net pipeline:
        # 1. 9x9 mean filter, threshold 0.5 (remove speckle noise)
        mask_t = torch.from_numpy(mask_np).unsqueeze(0).unsqueeze(0)
        mean_9x9 = torch.nn.functional.avg_pool2d(mask_t, kernel_size=9, stride=1, padding=4)
        cleaned = (mean_9x9 > 0.5).float()

        # 2. Morphological dilation
        if self.dilation_radius > 0:
            k_size = 2 * self.dilation_radius + 1
            dilated = torch.nn.functional.max_pool2d(cleaned, kernel_size=k_size, stride=1, padding=self.dilation_radius)
        else:
            dilated = cleaned

        # 3. Gaussian blur for smooth soft boundary
        blurred = TF.gaussian_blur(dilated, kernel_size=11, sigma=2.0)
        mask = torch.clamp(blurred.squeeze(0), 0.0, 1.0) # [1, H, W]

        # Optional shared square crop. The SAME window is applied to s2_cloudy,
        # s1, s2_clear and mask so the four tensors remain pixel-aligned.
        if self.crop_size is not None:
            cs = self.crop_size
            H, W = s2_cloudy_t.shape[-2], s2_cloudy_t.shape[-1]
            if cs > H or cs > W:
                raise ValueError(f"crop_size={cs} larger than patch {H}x{W}")
            if self.deterministic:
                top, left = (H - cs) // 2, (W - cs) // 2
            else:
                top = int(np.random.randint(0, H - cs + 1))
                left = int(np.random.randint(0, W - cs + 1))
            s2_cloudy_t = s2_cloudy_t[:, top:top + cs, left:left + cs].clone()
            s1_t = s1_t[:, top:top + cs, left:left + cs].clone()
            s2_clear_t = s2_clear_t[:, top:top + cs, left:left + cs].clone()
            mask = mask[:, top:top + cs, left:left + cs].clone()

        return s2_cloudy_t, s1_t, s2_clear_t, cf, mask
