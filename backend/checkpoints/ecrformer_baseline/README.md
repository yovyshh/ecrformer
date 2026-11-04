# ECRformer-Lite: Baseline Model (Epoch 30 EMA)

This checkpoint represents the **Baseline Model** trained with pixel-wise reconstruction ($L_1$ and multiscale SDFL frequency loss) prior to conditional PatchGAN adversarial sharpening.

## 🎯 Model Overview
- **Parameters:** ~3.62 Million parameters (ECRformer-Lite generator).
- **Training Epochs:** 30 epochs on SEN12MS-CR-TS ($128 \times 128$ crops).
- **Supervision:** $L_1$ photometric loss + Scale-Decoupled Frequency Loss (SDFL). No PatchGAN discriminator; no Opaque Cloud Cutout.
- **Characteristics:** Achieves high PSNR (~30.20 dB) and high SSIM (0.875), but exhibits conditional mean regression (smooth/blurry textures) under heavy cloud cover where SAR guidance is subtle. It serves as the official benchmark against which our Sweet-Spot GAN-sharpened model is evaluated.

---

## 📊 Comparison with Sweet-Spot Model

| Metric | Baseline Checkpoint (This Model) | Sweet-Spot Best Model | Delta |
| :--- | :---: | :---: | :---: |
| **High-Frequency Detail Ratio (Heavy Clouds)** | 0.354 *(Over-smoothed)* | **0.907–0.931** *(Natural crispness)* | **+142% gain** |
| **Validation PSNR (Overall)** | **30.20 dB** | 29.98 dB | -0.22 dB |
| **Validation SSIM (Overall)** | 0.875 | 0.880 | +0.005 |
| **Inference Time per $256\times 256$ Scene** | ~18 ms | ~18 ms | Identical Generator |

---

## 🚀 How to Load for Inference in Python

```python
import torch
from models.ecrformer_adapted import ECRformerAdaptedModel

# 1. Initialize architecture
model = ECRformerAdaptedModel(
    features_start=32,
    num_blocks=[2, 2, 1, 1],
    num_refine=0,
    bottle_neck="tsa",
    cbam="1ca2+1sa2",
    mask_blend=True,
    head_init="mean_prior"
)

# 2. Load baseline checkpoint weights
checkpoint_path = r"backend/checkpoints/ecrformer_baseline/best_model.pth"
ck = torch.load(checkpoint_path, map_location="cuda" if torch.cuda.is_available() else "cpu", weights_only=False)
model.load_state_dict(ck["ema_state_dict"])
model.eval()

# 3. Forward pass (supports 128x128 or native 256x256)
# Inputs:
# - s2_cloudy: [B, 4, H, W] in [0, 1] reflectance
# - s1_sar:    [B, 2, H, W] normalized backscatter
# - mask:      [B, 1, H, W] soft cloud mask in [0, 1]
with torch.no_grad():
    blended_output, direct_pred, projs = model(s2_cloudy, s1_sar, mask)
```
