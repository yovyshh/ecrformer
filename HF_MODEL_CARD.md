---
license: apache-2.0
tags:
  - remote-sensing
  - satellite
  - cloud-removal
  - sentinel-2
  - sentinel-1
  - sar-optical-fusion
  - pytorch
  - vision
datasets:
  - sen12ms-cr
metrics:
  - psnr
  - ssim
---

# ECRformer: SAR-Guided Optical Satellite Cloud Removal

Official repository for **ECRformer-Lite with Soft-Mask Guided Preservation and Scale-Decoupled Conditional PatchGAN Sharpening** on Sentinel-2 and Sentinel-1 imagery (SEN12MS-CR).

![Pipeline Architecture](paper_pipeline_architecture1.png)

## 🌟 Highlights
- **Parameter Efficient:** Active generator has only **3.62 Million parameters** (~14.5 MB in memory).
- **Overcoming the Blurriness Trap:** Standard $/SSIM models suffer from regression to the conditional mean under thick clouds. Our multi-scale structural supervision and 11-channel High-Pass PatchGAN discriminator boost high-frequency detail retention (**Detail Ratio**) from **0.354 to 0.907–0.931 (+142% gain)**.
- **100% Clear-Sky Preservation:** Integrated soft-mask alpha blending preserves original cloud-free optical ground reflectance with zero neural distortion.
- **Trained on Consumer Hardware:** Fully trained and fine-tuned on a single GPU across four systematic optimization stages.

---

## 📊 Benchmark Results (SEN12MS-CR)

| Cloud Coverage Regime | Evaluation Pool | Baseline ECRformer-Lite | Ours (Sweet-Spot Model) | Sharpness Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Sparse Clouds (~10%)** | 117 patches | 33.17 dB / 0.472 DR | **33.27 dB / 0.907 DR** | **+92% sharper** |
| **Moderate Clouds (~40%)** | 187 patches | 34.25 dB / 0.448 DR | **33.31 dB / 0.907 DR** | **+102% sharper** |
| **Semi-Transparent Haze** | 283 patches | 33.47 dB / 0.387 DR | **32.80 dB / 0.902 DR** | **+133% sharper** |
| **Heavy / Dense Overcast (70–100%)** | 370 patches | 30.34 dB / 0.632 DR | **29.98 dB / 0.931 DR** | **+47% sharper** |

*(Detail Ratio = ratio of high-frequency gradient energy to ground truth, 1.00 = 100% natural texture)*

---

## 🚀 Quickstart & Inference

`python
import torch
from models.ecrformer_adapted import ECRformerAdaptedModel

# 1. Instantiate Generator
model = ECRformerAdaptedModel(
    features_start=32,
    num_blocks=[2, 2, 1, 1],
    num_refine=0,
    bottle_neck='tsa',
    cbam='1ca2+1sa2',
    mask_blend=True,
    head_init='mean_prior'
)

# 2. Load Sweet-Spot Checkpoint
ckpt = torch.load('best_model.pth', map_location='cpu', weights_only=False)
model.load_state_dict(ckpt.get('ema_state_dict', ckpt.get('model_state_dict')))
model.eval()

# 3. Inputs:
# s2_cloudy: [B, 4, H, W] in [0, 1] reflectance (B04, B03, B02, B08)
# s1_sar:    [B, 2, H, W] normalized backscatter (VV: [-25, 0]->[0, 1], VH: [-35, 0]->[0, 1])
# mask:      [B, 1, H, W] continuous soft cloud mask in [0, 1]
with torch.no_grad():
    blended_output, direct_pred, _ = model(s2_cloudy, s1_sar, mask)
`

---

## 📂 Checkpoint Contents
- est_model.pth (~34.3 MB): Contains generator state dict, EMA state dict, and 11-channel PatchGAN discriminator weights.
- model_metadata.json: Exact training hyperparameter specifications and architectural metadata.
- models/: Standalone PyTorch modules (ecrformer_adapted.py, ecrformer_model.py, module.py).
