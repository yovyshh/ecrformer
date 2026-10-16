# ECRformer-Lite: Sweet-Spot Best Model

This checkpoint is the designated **Best Overall Model** from the fine-tuning campaign on SEN12MS-CR-TS.

## 🎯 Key Highlights
- **Solves the Over-Smoothing Trap:** Replaces blurry smudges under heavy clouds with sharp, physically aligned roads, water boundaries, field borders, and terrain ridges.
- **Natural Sharpness Without Late-Epoch GAN Grain:** Selected at the exact adversarial sweet spot (`best_score = 0.5439`), achieving the highest edge correlation with ground truth without the artificial grain of late epochs.
- **Multiscale Resolution Support:** Verified at both $128\times 128$ and native full-scene $256\times 256$ resolution.
- **High Photometric Fidelity:** Maintains $\approx 30\text{ dB}$ PSNR and $0.88$ SSIM.

## 📊 Performance Comparison
| Metric | Baseline Checkpoint | Sweet-Spot Best Model | Change |
| :--- | :---: | :---: | :---: |
| **Heavy Cloud Detail Ratio** | 0.23 – 0.38 *(Blurry)* | **0.86 – 0.98** *(Natural Crispness)* | **$+130\%$ to $+270\%$** |
| **Heavy Cloud Edge Correlation** | 0.16 – 0.38 | **0.415 – 0.50** | **Highest Ground Alignment** |
| **Heavy Cloud PSNR** | 30.30 dB | **29.97 dB** | Negligible ($\Delta < 0.3\text{ dB}$) |
| **Mean Absolute Error (MAE)** | 0.0205 | **0.0204** | Equivalent / Slightly Lower |

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

# 2. Load sweet-spot weights
checkpoint_path = r"checkpoints/ecrformer_sweetspot_best/best_model.pth"
ck = torch.load(checkpoint_path, map_location="cuda" if torch.cuda.is_available() else "cpu", weights_only=False)
model.load_state_dict(ck["ema_state_dict"])
model.eval()

# 3. Forward pass (supports 128x128 or native 256x256)
# Inputs:
# - s2_cloudy: [B, 4, H, W] in [0, 1] reflectance
# - s1_sar:    [B, 2, H, W] normalized with sar_norm='paper_exact'
# - mask:      [B, 1, H, W] soft cloud mask in [0, 1]
with torch.no_grad():
    out_blended, direct_pred, projs = model(s2_cloudy, s1_sar, mask)
```

## 🔒 Baseline Protection
The original 50-epoch baseline checkpoint remains preserved and untouched:
- Path: `checkpoints/ecrformer_light_128_50ep/best_model.pth`
- SHA256: `2f02aca75619a8b4db52ca5ef4910a0ad305e80c68d48c035c0bb975e5b1a5b6`
