import os
import sys
import torch
import numpy as np

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from models.ecrformer_adapted import ECRformerAdaptedModel
from losses.sdfl_loss import SDFLLoss
from data.cache_dataset import CachedSEN12MSCRDataset

def test_loss_formulations():
    print("=" * 70)
    print("TEST 1: LOSS EQUATION VERIFICATION (repo_convex vs paper_additive)")
    print("=" * 70)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    
    criterion_convex = SDFLLoss(
        lambda_enc=0.05,
        lambda_dec=0.05,
        sdfl_mode='official_repo',
        total_loss_form='repo_convex',
        w_main_l1=0.9,
        w_main_ssim=0.1
    ).to(device)

    criterion_additive = SDFLLoss(
        lambda_enc=0.05,
        lambda_dec=0.05,
        sdfl_mode='official_repo',
        total_loss_form='paper_additive',
        w_main_l1=0.9,
        w_main_ssim=0.1
    ).to(device)

    # Synthetic inputs
    torch.manual_seed(42)
    B, H, W = 2, 256, 256
    pred = torch.rand(B, 4, H, W, device=device)
    target = torch.rand(B, 4, H, W, device=device)
    mask = torch.rand(B, 1, H, W, device=device)

    down_projs = [
        torch.rand(B, 4, 256, 256, device=device),
        torch.rand(B, 4, 128, 128, device=device),
        torch.rand(B, 4, 64, 64, device=device),
    ]
    up_projs = [
        torch.rand(B, 4, 64, 64, device=device),
        torch.rand(B, 4, 128, 128, device=device),
        torch.rand(B, 4, 256, 256, device=device),
    ]
    projs = (down_projs, up_projs)

    loss_conv, m_conv = criterion_convex(pred, target, mask, projs)
    loss_add, m_add = criterion_additive(pred, target, mask, projs)

    L_main = m_conv['loss_main']
    L_enc = m_conv['loss_enc_aux']
    L_dec = m_conv['loss_dec_aux']

    expected_conv = 0.90 * L_main + 0.05 * L_enc + 0.05 * L_dec
    expected_add = 1.00 * L_main + 0.05 * L_enc + 0.05 * L_dec

    print(f"Components: L_main={L_main:.6f}, L_enc={L_enc:.6f}, L_dec={L_dec:.6f}")
    print(f"repo_convex:    actual={loss_conv.item():.6f}, expected={expected_conv:.6f}, diff={abs(loss_conv.item() - expected_conv):.2e}")
    print(f"paper_additive: actual={loss_add.item():.6f}, expected={expected_add:.6f}, diff={abs(loss_add.item() - expected_add):.2e}")

    assert abs(loss_conv.item() - expected_conv) < 1e-5, "Mismatch in repo_convex total loss!"
    assert abs(loss_add.item() - expected_add) < 1e-5, "Mismatch in paper_additive total loss!"
    print("--> TEST 1 PASSED: Both loss formulations mathematically verified.")

def test_sar_normalization():
    print("\n" + "=" * 70)
    print("TEST 2: SENTINEL-1 CHANNEL NORMALIZATION ON REAL CACHED PATCHES")
    print("=" * 70)
    val_dir = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3\val"

    ds_default = CachedSEN12MSCRDataset(val_dir, sar_norm='paper_default')
    ds_resnet = CachedSEN12MSCRDataset(val_dir, sar_norm='sen12ms_resnet')
    ds_raw = CachedSEN12MSCRDataset(val_dir, sar_norm='raw')

    # Inspect first 10 patches
    for idx in range(5):
        _, s1_def, _, _, _ = ds_default[idx]
        _, s1_res, _, _, _ = ds_resnet[idx]
        _, s1_raw, _, _, _ = ds_raw[idx]

        # Mode: paper_default ([-25, 0] dB for both VV and VH -> [0, 1])
        assert s1_def.min() >= 0.0 and s1_def.max() <= 1.0, f"s1_def out of [0, 1]: {s1_def.min()} to {s1_def.max()}"

        # Mode: sen12ms_resnet (VV in [-25, 0], VH in [-32.5, 0] -> [0, 1])
        assert s1_res.min() >= 0.0 and s1_res.max() <= 1.0, f"s1_res out of [0, 1]: {s1_res.min()} to {s1_res.max()}"

        # Mode: raw
        assert s1_raw[0].min() < 0.0 and s1_raw[1].min() < 0.0, "Raw SAR should be negative dB values"

    # Detailed channel statistics on patch 0
    _, s1_def, _, _, _ = ds_default[0]
    _, s1_res, _, _, _ = ds_resnet[0]
    _, s1_raw, _, _, _ = ds_raw[0]

    print(f"Raw SAR patch 0:      VV in [{s1_raw[0].min():.2f}, {s1_raw[0].max():.2f}] dB | VH in [{s1_raw[1].min():.2f}, {s1_raw[1].max():.2f}] dB")
    print(f"paper_default patch 0: VV in [{s1_def[0].min():.4f}, {s1_def[0].max():.4f}]    | VH in [{s1_def[1].min():.4f}, {s1_def[1].max():.4f}]")
    print(f"sen12ms_resnet patch 0:VV in [{s1_res[0].min():.4f}, {s1_res[0].max():.4f}]    | VH in [{s1_res[1].min():.4f}, {s1_res[1].max():.4f}]")
    print("--> TEST 2 PASSED: SAR on-the-fly normalization verified for both modes.")

def test_finite_gradients_and_blending():
    print("\n" + "=" * 70)
    print("TEST 3: FINITE GRADIENTS & BLENDING INTEGRITY (RTX 5070 BF16)")
    print("=" * 70)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = ECRformerAdaptedModel(
        features_start=32,
        num_blocks=[2, 2, 1, 1],
        num_refine=2,
        bottle_neck='tsa',
        cbam='1ca2+1sa2',
        mask_blend=True,
        head_init='mean_prior'
    ).to(device)

    criterion = SDFLLoss(
        lambda_enc=0.05,
        lambda_dec=0.05,
        sdfl_mode='official_repo',
        total_loss_form='repo_convex'
    ).to(device)

    torch.manual_seed(42)
    B = 2
    s2_c = torch.rand(B, 4, 256, 256, device=device)
    s1 = torch.rand(B, 2, 256, 256, device=device)
    # Mask with explicit 0.0 (clear) and 1.0 (cloud) regions
    mask = torch.zeros(B, 1, 256, 256, device=device)
    mask[:, :, 50:200, 50:200] = 1.0 # 150x150 cloud core
    s2_t = torch.rand(B, 4, 256, 256, device=device)

    model.train()
    with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
        pred, pred_direct, projs = model(s2_c, s1, mask)
        loss, loss_dict = criterion(pred, s2_t, mask, projs, pred_direct=pred_direct)

    # Verify residual blending formula:
    # Where mask == 0: pred must strictly equal s2_c
    clear_region = (mask == 0.0).expand_as(pred)
    diff_clear = torch.abs(pred[clear_region] - s2_c[clear_region]).max().item()
    print(f"Max deviation in clear region (mask=0): {diff_clear:.2e}")
    assert diff_clear < 1e-4, f"Blending failed in clear background: diff={diff_clear}"

    # Where mask == 1: pred must equal pred_direct exactly
    cloud_core = (mask == 1.0).expand_as(pred)
    expected_cloud = pred_direct
    diff_cloud = torch.abs(pred[cloud_core] - expected_cloud[cloud_core]).max().item()
    print(f"Max deviation in cloud core (mask=1): {diff_cloud:.2e}")
    assert diff_cloud < 1e-4, f"Blending failed in cloud core: diff={diff_cloud}"

    # Backward pass & check gradients
    loss.backward()

    nan_params = []
    zero_grad_params = []
    total_params = 0
    grad_params = 0

    for name, p in model.named_parameters():
        total_params += 1
        if p.requires_grad:
            grad_params += 1
            if p.grad is None:
                zero_grad_params.append(name)
            elif torch.isnan(p.grad).any() or torch.isinf(p.grad).any():
                nan_params.append(name)

    print(f"Total model parameters: {total_params} | Parameters requiring grad: {grad_params}")
    print(f"NaN / Inf gradients: {len(nan_params)} | Missing gradients: {len(zero_grad_params)}")

    assert len(nan_params) == 0, f"Found NaN/Inf gradients: {nan_params}"
    assert len(zero_grad_params) == 0, f"Missing gradients on: {zero_grad_params}"
    print("--> TEST 3 PASSED: Residual blending is exact and all gradients are finite.")

if __name__ == "__main__":
    test_loss_formulations()
    test_sar_normalization()
    test_finite_gradients_and_blending()
    print("\n" + "=" * 70)
    print("ALL AUDIT CHECKS PASSED SUCCESSFULLY.")
    print("=" * 70)
