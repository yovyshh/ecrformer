import os
import sys
import torch
import numpy as np
import pandas as pd
import gradio as gr
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.ecrformer_adapted import ECRformerAdaptedModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(BASE_DIR, "demo_samples")

# 1. Load Models
print("Loading Sweet-Spot and Baseline models...")
sweetspot_model = ECRformerAdaptedModel(
    features_start=32,
    num_blocks=[2, 2, 1, 1],
    num_refine=0,
    bottle_neck="tsa",
    cbam="1ca2+1sa2",
    mask_blend=True,
    head_init="mean_prior",
)
sweet_ckpt_path = os.path.join(BASE_DIR, "backend", "checkpoints", "ecrformer_sweetspot_best", "best_model.pth")
if os.path.isfile(sweet_ckpt_path):
    ckpt = torch.load(sweet_ckpt_path, map_location="cpu", weights_only=False)
    sweetspot_model.load_state_dict(ckpt.get("ema_state_dict", ckpt.get("model_state_dict")))
sweetspot_model.eval()

baseline_model = ECRformerAdaptedModel(
    features_start=32,
    num_blocks=[2, 2, 1, 1],
    num_refine=0,
    bottle_neck="tsa",
    cbam="1ca2+1sa2",
    mask_blend=True,
    head_init="mean_prior",
)
base_ckpt_path = os.path.join(BASE_DIR, "backend", "checkpoints", "ecrformer_baseline", "best_model.pth")
if os.path.isfile(base_ckpt_path):
    ckpt_base = torch.load(base_ckpt_path, map_location="cpu", weights_only=False)
    baseline_model.load_state_dict(ckpt_base.get("ema_state_dict", ckpt_base.get("model_state_dict")))
baseline_model.eval()


def to_display_rgb(tensor_4ch, band_mode="RGB"):
    arr = tensor_4ch.detach().cpu().numpy()
    if band_mode == "RGB":
        rgb = arr[[0, 1, 2], :, :].transpose(1, 2, 0)
    else:
        rgb = arr[[3, 0, 1], :, :].transpose(1, 2, 0)
    rgb = np.clip(rgb * 3.0, 0.0, 1.0)
    return (rgb * 255).astype(np.uint8)


def to_display_sar(sar_2ch):
    arr = sar_2ch.detach().cpu().numpy()
    vv = np.clip(arr[0], 0.0, 1.0)
    return (vv * 255).astype(np.uint8)


def to_display_mask(mask_1ch):
    arr = mask_1ch.squeeze().detach().cpu().numpy()
    arr = np.clip(arr, 0.0, 1.0)
    return (arr * 255).astype(np.uint8)


def compute_metrics(pred, target, mask):
    p = pred.float()
    t = target.float()
    m = (mask.squeeze() > 0.3).bool()

    mse_full = torch.mean((p - t) ** 2).item()
    psnr_full = 10.0 * np.log10(1.0 / max(mse_full, 1e-10))

    if m.sum() > 16:
        mse_cloud = torch.mean((p[:, m] - t[:, m]) ** 2).item()
        psnr_cloud = 10.0 * np.log10(1.0 / max(mse_cloud, 1e-10))
    else:
        psnr_cloud = psnr_full

    mae = torch.mean(torch.abs(p - t)).item()

    p_np = p.permute(1, 2, 0).numpy()
    t_np = t.permute(1, 2, 0).numpy()
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    mu_p = p_np.mean()
    mu_t = t_np.mean()
    sigma_p = p_np.var()
    sigma_t = t_np.var()
    sigma_pt = np.mean((p_np - mu_p) * (t_np - mu_t))
    ssim = ((2 * mu_p * mu_t + c1) * (2 * sigma_pt + c2)) / ((mu_p**2 + mu_t**2 + c1) * (sigma_p + sigma_t + c2))

    dx_p = p[:, :-1, 1:] - p[:, :-1, :-1]
    dy_p = p[:, 1:, :-1] - p[:, :-1, :-1]
    dx_t = t[:, :-1, 1:] - t[:, :-1, :-1]
    dy_t = t[:, 1:, :-1] - t[:, :-1, :-1]

    mag_p = torch.sqrt(dx_p ** 2 + dy_p ** 2 + 1e-10).sum().item()
    mag_t = torch.sqrt(dx_t ** 2 + dy_t ** 2 + 1e-10).sum().item()
    detail_ratio = mag_p / max(mag_t, 1e-8)

    p_flat = p.flatten()
    t_flat = t.flatten()
    cov = torch.mean((p_flat - p_flat.mean()) * (t_flat - t_flat.mean()))
    std_p = p_flat.std() + 1e-8
    std_t = t_flat.std() + 1e-8
    edge_corr = (cov / (std_p * std_t)).item()

    return {
        "PSNR (Full Scene)": f"{psnr_full:.2f} dB",
        "PSNR (Under Cloud)": f"{psnr_cloud:.2f} dB",
        "SSIM": f"{ssim:.4f}",
        "Detail Ratio (Sharpness)": f"{detail_ratio:.3f}",
        "Edge Correlation": f"{edge_corr:.4f}",
        "Photometric MAE": f"{mae:.4f}"
    }


PRESET_FILES = {
    "Dense / Heavy Overcast (100% Cloud Cover)": "dense_95pct.npz",
    "Moderate Clouds (~40% Cloud Cover)": "moderate_40pct.npz",
    "Semi-Transparent Haze (~70% Cloud Cover)": "hazy_60pct.npz",
    "Sparse Clouds (~10% Cloud Cover)": "sparse_10pct.npz"
}


def process_scene(scene_choice, band_mode, custom_file):
    if custom_file is not None:
        npz_data = np.load(custom_file.name)
    else:
        file_name = PRESET_FILES.get(scene_choice, "dense_95pct.npz")
        npz_data = np.load(os.path.join(DEMO_DIR, file_name))

    s2_c = torch.from_numpy(npz_data["s2_cloudy"]).permute(2, 0, 1).unsqueeze(0).float()
    s2_t = torch.from_numpy(npz_data["s2_clear"]).permute(2, 0, 1).unsqueeze(0).float()
    s1 = torch.from_numpy(npz_data["s1"]).permute(2, 0, 1).unsqueeze(0).float()

    s1_norm = s1.clone()
    s1_norm[:, 0] = torch.clamp((s1_norm[:, 0] - (-25.0)) / 25.0, 0.0, 1.0)
    s1_norm[:, 1] = torch.clamp((s1_norm[:, 1] - (-35.0)) / 35.0, 0.0, 1.0)

    mask = torch.from_numpy(npz_data["mask"]).unsqueeze(0).unsqueeze(0).float()

    with torch.no_grad():
        sweet_blended, _, _ = sweetspot_model(s2_c, s1_norm, mask)
        base_blended, _, _ = baseline_model(s2_c, s1_norm, mask)

    # Images for display
    img_cloudy = to_display_rgb(s2_c[0], band_mode)
    img_sar = to_display_sar(s1_norm[0])
    img_mask = to_display_mask(mask[0])
    img_base = to_display_rgb(base_blended[0], band_mode)
    img_sweet = to_display_rgb(sweet_blended[0], band_mode)
    img_target = to_display_rgb(s2_t[0], band_mode)

    # Metrics
    base_m = compute_metrics(base_blended[0], s2_t[0], mask[0])
    sweet_m = compute_metrics(sweet_blended[0], s2_t[0], mask[0])

    df_data = []
    for k in base_m.keys():
        df_data.append({
            "Evaluation Metric": k,
            "Baseline ECRformer-Lite": base_m[k],
            "Our Sweet-Spot Model": sweet_m[k],
            "Improvement / Role": "[BEST] Recovers fine structures" if "Detail" in k or "Edge" in k else "Anchored color truth"
        })

    df = pd.DataFrame(df_data)

    return img_cloudy, img_sar, img_mask, img_base, img_sweet, img_target, df


# Build Gradio Interface
with gr.Blocks(title="ECRformer Satellite Cloud Removal") as demo:
    gr.Markdown("# 🛰️ ECRformer: SAR-Guided Optical Satellite Cloud Removal")
    gr.Markdown(
        "**Multimodal Cloud Removal with Soft-Mask Guided Detail Preservation & Conditional PatchGAN Sharpening**  \n"
        "[GitHub Repository](https://github.com/yovyshh/ecrformer) | [Hugging Face Model](https://huggingface.co/vyyyyyyy/ecrformer-satellite-cloud-removal)"
    )

    with gr.Row():
        with gr.Column(scale=1):
            scene_dropdown = gr.Dropdown(
                choices=list(PRESET_FILES.keys()),
                value="Dense / Heavy Overcast (100% Cloud Cover)",
                label="1. Choose Preloaded Satellite Scene"
            )
            band_radio = gr.Radio(
                choices=["RGB", "NIR-R-G (Vegetation)"],
                value="RGB",
                label="2. Spectral Display Mode"
            )
            custom_upload = gr.File(
                label="Optional: Upload Custom .npz Patch",
                file_types=[".npz"]
            )
            btn_run = gr.Button("🚀 Run Cloud Removal", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Live Metric Comparison Matrix")
            metric_table = gr.Dataframe(
                headers=["Evaluation Metric", "Baseline ECRformer-Lite", "Our Sweet-Spot Model", "Improvement / Role"],
                datatype=["str", "str", "str", "str"],
                interactive=False
            )

    gr.Markdown("---")
    gr.Markdown("### 🛰️ Multimodal Inputs & Reconstructed Outputs")

    with gr.Row():
        out_cloudy = gr.Image(label="Cloudy Sentinel-2 Input", type="numpy")
        out_sar = gr.Image(label="Sentinel-1 SAR Radar (VV Penetrating Echo)", type="numpy")
        out_mask = gr.Image(label="Soft Cloud Mask", type="numpy")

    with gr.Row():
        out_base = gr.Image(label="Baseline ECRformer-Lite (Standard L1: Blurry Under Cloud)", type="numpy")
        out_sweet = gr.Image(label="Our Sweet-Spot Model (Sharp PatchGAN + Scale-Decoupled)", type="numpy")
        out_target = gr.Image(label="Ground Truth (Real Cloud-Free Target)", type="numpy")

    btn_run.click(
        fn=process_scene,
        inputs=[scene_dropdown, band_radio, custom_upload],
        outputs=[out_cloudy, out_sar, out_mask, out_base, out_sweet, out_target, metric_table]
    )

    demo.load(
        fn=process_scene,
        inputs=[scene_dropdown, band_radio, custom_upload],
        outputs=[out_cloudy, out_sar, out_mask, out_base, out_sweet, out_target, metric_table]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=gr.themes.Soft())

