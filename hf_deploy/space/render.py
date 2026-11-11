"""Rendering and image encoding utilities for ECRformer Space."""

import io
import base64
import numpy as np
import torch
from PIL import Image


def to_rgb_image(image: np.ndarray | torch.Tensor, bands=(0, 1, 2), brightness: float = 3.0) -> np.ndarray:
    """Convert a multi-band CHW or HWC satellite tensor/array to uint8 RGB."""
    if isinstance(image, torch.Tensor):
        image = image.detach().cpu().numpy()

    if image.ndim == 4:
        image = image[0]

    # Handle HWC -> CHW if necessary
    if image.ndim == 3 and image.shape[2] in [2, 4, 13] and image.shape[0] not in [2, 4, 13]:
        image = np.transpose(image, (2, 0, 1))

    if image.ndim != 3:
        raise ValueError(f"Expected CHW image, got shape {image.shape}")
    if max(bands) >= image.shape[0]:
        raise ValueError(f"RGB bands {bands} exceed channel count {image.shape[0]}")

    rgb = np.transpose(image[list(bands)], (1, 2, 0))
    rgb = np.clip(rgb * brightness, 0.0, 1.0)
    return (rgb * 255.0).round().astype(np.uint8)


def png_bytes(image_array: np.ndarray) -> bytes:
    """Convert uint8 numpy array (H, W, 3) or (H, W) to PNG bytes."""
    if image_array.dtype != np.uint8:
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
    img = Image.fromarray(image_array)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def data_uri(image_bytes: bytes) -> str:
    """Encode PNG bytes as data URI string."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def sar_preview(s1: np.ndarray | torch.Tensor) -> bytes:
    """Generate grayscale PNG bytes of SAR VV channel normalized with paper_exact."""
    if isinstance(s1, torch.Tensor):
        s1 = s1.detach().cpu().numpy()
    if s1.ndim == 4:
        s1 = s1[0]
    # If HWC, transpose to CHW
    if s1.ndim == 3 and s1.shape[2] == 2:
        s1 = np.transpose(s1, (2, 0, 1))

    vv = s1[0].astype(np.float32)
    # Check if raw dB (values < 0) or already normalized [0, 1]
    if vv.min() < 0.0:
        vv_norm = np.clip((vv - (-25.0)) / (0.0 - (-25.0)), 0.0, 1.0)
    else:
        vv_norm = np.clip(vv, 0.0, 1.0)

    vv_u8 = (vv_norm * 255.0).round().astype(np.uint8)
    return png_bytes(vv_u8)


def mask_preview(mask: np.ndarray | torch.Tensor) -> bytes:
    """Generate grayscale PNG bytes of refined cloud mask in [0, 1]."""
    if isinstance(mask, torch.Tensor):
        mask = mask.detach().cpu().numpy()
    if mask.ndim == 4:
        mask = mask[0, 0]
    elif mask.ndim == 3:
        mask = mask[0] if mask.shape[0] == 1 else mask[:, :, 0]

    mask_norm = np.clip(mask.astype(np.float32), 0.0, 1.0)
    mask_u8 = (mask_norm * 255.0).round().astype(np.uint8)
    return png_bytes(mask_u8)


def blank_image(size: int = 256, gray: int = 128) -> bytes:
    """Generate mid-gray 256x256 RGB PNG bytes."""
    arr = np.full((size, size, 3), gray, dtype=np.uint8)
    return png_bytes(arr)

