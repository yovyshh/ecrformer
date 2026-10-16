import os
import sys
import copy
import glob
import torch
import torch.nn as nn
import torch.optim as optim

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from models.ecrformer_adapted import ECRformerAdaptedModel
from losses.sdfl_loss import SDFLLoss
from data.cache_dataset import CachedSEN12MSCRDataset

def run_verification():
    print("=" * 85)
    print("ECRFORMER-LIGHT FINAL PRE-TRAINING VERIFICATION")
    print("=" * 85)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f"Active Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    # -------------------------------------------------------------------------
    # 1. PRODUCTION MODEL INSTANTIATION & PARAMETER COUNT
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("1. PRODUCTION MODEL ARCHITECTURE & PARAMETER AUDIT")
    print("-" * 75)
    model = ECRformerAdaptedModel(
        features_start=32,
        num_blocks=[2, 2, 1, 1],
        num_refine=2,
        bottle_neck='tsa',
        cbam='1ca2+1sa2',
        residual_blend=True,
        zero_init_final=False
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"Total Model Parameters:     {total_params:,} (scalar weights & biases)")
    print(f"Trainable Model Parameters: {trainable_params:,}")
    print(f"Model In-Channels:          Branch 0 = {model.in_chans[0]} (SAR), Branch 1 = {model.in_chans[1]} (Optical + Mask)")
    print(f"Model Out-Channels:         {model.out_chans} (4-band Sentinel-2 B04, B03, B02, B08)")
    print(f"Residual Blending:          {model.residual_blend} (Active convex blend)")

    # Architectural component verification
    bb = model.backbone
    print(f"Backbone Submodules:")
    print(f"  - Stem: DecoupledStem (Radar Conv2d 2->16, Optical Conv2d 5->16, Merged 32)")
    print(f"  - Encoder Stages: {len(bb.encoder)} stages, blocks = [2, 2, 1, 1], feats = [32, 64, 128, 256]")
    print(f"  - Attention: CBAM (1ca2+1sa2) across all encoder & decoder blocks")
    print(f"  - Bottleneck: TSA / RestormerBlock ({type(bb.bottle_neck_module[0]).__name__})")
    print(f"  - Decoder Stages: {len(bb.decoder)} stages with skip connections and upsamplers")
    print(f"  - Refinement: {len(bb.refine)} RestormerBlocks (dilations [1, 2, 4])")
    print(f"  - Down-Projection Heads: {len(bb.down_proj)} heads (4 ch each at 1x, 1/2x, 1/4x)")
    print(f"  - Up-Projection Heads:   {len(bb.up_proj)} heads (4 ch each at 1/4x, 1/2x, 1x)")
    print(f"  - Final Conv: {bb.final_conv.in_channels} -> {bb.final_conv.out_channels} (predicts 4-band residual)")

    assert total_params == 3709578, f"Parameter count mismatch! Expected 3,709,578, got {total_params}"
    assert trainable_params == total_params, "Found non-trainable parameters in fresh model!"

    # -------------------------------------------------------------------------
    # 2. TWO-STEP TRAINING DRY-RUN
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("2. TWO-STEP PRODUCTION TRAINING DRY-RUN (RTX 5070 BF16)")
    print("-" * 75)

    model_ema = copy.deepcopy(model).eval()
    for p in model_ema.parameters():
        p.requires_grad = False

    def update_ema(ema_m, m, decay=0.999):
        with torch.no_grad():
            for ema_v, m_v in zip(ema_m.state_dict().values(), m.state_dict().values()):
                if ema_v.dtype.is_floating_point:
                    ema_v.mul_(decay).add_(m_v, alpha=1.0 - decay)

    criterion = SDFLLoss(
        lambda_enc=0.05,
        lambda_dec=0.05,
        sdfl_mode='paper_strict',
        total_loss_form='paper_additive',
        w_main_l1=0.9,
        w_main_ssim=0.1
    ).to(device)

    print(f"SDFL Mode:           {criterion.sdfl_mode} (Encoder = pure 1-SSIM, Decoder = pure L1)")
    print(f"Total Loss Formula:  {criterion.total_loss_form} (L_total = 1.0 * L_main + 0.05 * L_enc + 0.05 * L_dec)")
    print(f"Encoder Loss Weight: w_enc_ssim = {criterion.w_enc_ssim}, w_enc_l1 = {criterion.w_enc_l1}")
    print(f"Decoder Loss Weight: w_dec_l1 = {criterion.w_dec_l1}, w_dec_ssim = {criterion.w_dec_ssim}")

    optimizer = optim.Adam(model.parameters(), lr=1e-4, betas=(0.9, 0.999), weight_decay=0.0)

    val_dir = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3\val"
    ds = CachedSEN12MSCRDataset(val_dir, sar_norm='paper_exact')
    print(f"SAR Normalization:   {ds.sar_norm} (VV in [-25, 0] dB -> [0, 1], VH in [-35, 0] dB -> [0, 1])")

    # Record initial weights of a sample layer to verify optimizer updates
    initial_w = model.backbone.final_conv.weight.clone().detach()
    initial_ema_w = model_ema.backbone.final_conv.weight.clone().detach()

    for step in range(2):
        s2_c, s1, s2_t, cf, mask = ds[step]
        # Batch size 2 by repeating or stacking
        s2_c_b = torch.stack([s2_c, ds[step + 1][0]]).to(device)
        s1_b   = torch.stack([s1,   ds[step + 1][1]]).to(device)
        s2_t_b = torch.stack([s2_t, ds[step + 1][2]]).to(device)
        mask_b = torch.stack([mask, ds[step + 1][4]]).to(device)

        print(f"Step {step + 1} Input Shapes: S2_c={list(s2_c_b.shape)}, S1={list(s1_b.shape)}, Mask={list(mask_b.shape)}, Target={list(s2_t_b.shape)}")
        print(f"Step {step + 1} Input Ranges: S2_c in [{s2_c_b.min():.3f}, {s2_c_b.max():.3f}], S1 in [{s1_b.min():.3f}, {s1_b.max():.3f}], Mask in [{mask_b.min():.3f}, {mask_b.max():.3f}]")

        model.train()
        optimizer.zero_grad()

        with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
            pred, raw_res, projs = model(s2_c_b, s1_b, mask_b)
            loss, metrics = criterion(pred, s2_t_b, mask_b, projs)

        # Output shape validation
        assert pred.shape == (2, 4, 256, 256), f"Output shape mismatch: {pred.shape}"
        assert raw_res.shape == (2, 4, 256, 256), f"Raw residual shape mismatch: {raw_res.shape}"
        assert len(projs[0]) == 3 and len(projs[1]) == 3, f"Projection heads mismatch: {len(projs[0])}, {len(projs[1])}"

        # Finite loss check
        assert torch.isfinite(loss).item(), f"Non-finite loss encountered: {loss.item()}"
        expected_total = metrics['loss_main'] + 0.05 * metrics['loss_enc_aux'] + 0.05 * metrics['loss_dec_aux']
        assert abs(metrics['loss_total'] - expected_total) < 1e-5, f"Loss equation mismatch! got {metrics['loss_total']}, expected {expected_total}"
        print(f"Step {step + 1} Losses: total={metrics['loss_total']:.4f} (matches L_main + 0.05*enc + 0.05*dec: {expected_total:.4f}), main={metrics['loss_main']:.4f}, l1_c={metrics['loss_l1_cloudy']:.4f}, ssim={metrics['loss_ssim_main']:.4f}, enc={metrics['loss_enc_aux']:.4f}, dec={metrics['loss_dec_aux']:.4f}")

        # Backward pass
        loss.backward()

        # Finite gradient check
        max_grad = max(p.grad.abs().max().item() for p in model.parameters() if p.grad is not None)
        assert max_grad < 1e5, f"Gradient explosion: max_grad={max_grad}"
        nan_grads = [name for name, p in model.named_parameters() if p.grad is not None and (torch.isnan(p.grad).any() or torch.isinf(p.grad).any())]
        assert len(nan_grads) == 0, f"NaN gradients in: {nan_grads}"

        # Optimizer step
        optimizer.step()

        # EMA update
        update_ema(model_ema, model, decay=0.999)

    # Verify optimizer actually changed weights
    updated_w = model.backbone.final_conv.weight.detach()
    w_delta = torch.norm(updated_w - initial_w).item()
    print(f"Weight update delta after 2 steps: {w_delta:.6f}")
    assert w_delta > 0, "Optimizer step failed to modify model weights!"

    # Verify EMA updated
    updated_ema_w = model_ema.backbone.final_conv.weight.detach()
    ema_delta = torch.norm(updated_ema_w - initial_ema_w).item()
    print(f"EMA weight delta after 2 steps:   {ema_delta:.6f}")
    assert ema_delta > 0, "EMA failed to update!"

    # Checkpoint save/load verification
    test_ckpt_path = os.path.join(REPO_ROOT, "checkpoints", "test_verification_ckpt.pth")
    os.makedirs(os.path.dirname(test_ckpt_path), exist_ok=True)
    torch.save({
        'epoch': 1,
        'model_state_dict': model.state_dict(),
        'ema_state_dict': model_ema.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'psnr': 21.5
    }, test_ckpt_path)

    assert os.path.exists(test_ckpt_path), "Checkpoint file was not created!"
    loaded_data = torch.load(test_ckpt_path, map_location=device, weights_only=False)

    # Fresh models to test loading
    test_model = ECRformerAdaptedModel().to(device)
    test_model.load_state_dict(loaded_data['model_state_dict'])

    # Verify exact parameter identity
    for k in model.state_dict():
        assert torch.equal(model.state_dict()[k], test_model.state_dict()[k]), f"Mismatch in loaded parameter {k}"

    print(f"Checkpoint save & load verified successfully ({os.path.getsize(test_ckpt_path) / 1024**2:.2f} MB).")
    os.remove(test_ckpt_path)

    # -------------------------------------------------------------------------
    # 3. SPLIT ISOLATION & CACHE AUDIT
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("3. SPLIT ISOLATION & CACHE INTEGRITY AUDIT")
    print("-" * 75)

    cache_root = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3"
    train_files = glob.glob(os.path.join(cache_root, "train", "*.npz"))
    val_files = glob.glob(os.path.join(cache_root, "val", "*.npz"))

    # Extract scene IDs from filenames
    # Example format: ROIs1970_fall_s2_3_p12.npz -> scene is s2_3
    def extract_scene(filepath):
        base = os.path.basename(filepath)
        # Match pattern like s2_<number>
        parts = base.split('_')
        for i, p in enumerate(parts):
            if p == 's2' and i + 1 < len(parts):
                return f"s2_{parts[i+1]}"
        return "unknown"

    train_scenes = set(extract_scene(f) for f in train_files)
    val_scenes = set(extract_scene(f) for f in val_files)

    print(f"Train Patches: {len(train_files):,} across {len(train_scenes)} scenes")
    print(f"Val Patches:   {len(val_files):,} across {len(val_scenes)} scenes")
    print(f"Validation Scenes: {sorted(list(val_scenes))}")

    overlap = train_scenes.intersection(val_scenes)
    print(f"Overlap between Train and Val Scenes: {overlap}")
    assert len(overlap) == 0, f"DATA LEAKAGE DETECTED! Overlapping scenes: {overlap}"

    # Confirm s2_139 holdout scene is absent from both train and val
    assert "s2_139" not in train_scenes, "Holdout test scene s2_139 found in training cache!"
    assert "s2_139" not in val_scenes, "Holdout test scene s2_139 found in validation cache!"
    print("Holdout Test Scene 's2_139': CONFIRMED STRICTLY ABSENT from both train and val splits.")

    print("\n" + "=" * 85)
    print("PRE-TRAINING VERIFICATION COMPLETE: ALL CHECKS PASSED.")
    print("=" * 85)

if __name__ == "__main__":
    run_verification()
