import os
import sys
import time
import copy
import argparse
import contextlib
import csv
import hashlib
import math
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from tqdm import tqdm
import matplotlib.pyplot as plt

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from models.ecrformer_adapted import ECRformerAdaptedModel
from losses.sdfl_loss import SDFLLoss
from data.cache_dataset import CachedSEN12MSCRDataset
from experiments.ecrformer_gradient_pilot.gradient_loss import add_gradient_term


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pilot_options(args):
    weight = float(args.lambda_gradient)
    if not math.isfinite(weight) or weight < 0.0:
        raise ValueError("lambda_gradient must be finite and non-negative")
    if args.resume and args.init_from_ema:
        raise ValueError("--resume and --init_from_ema cannot be combined")
    has_init = bool(args.init_from_ema)
    has_experiment_dir = bool(args.experiment_dir)
    if has_init != has_experiment_dir:
        raise ValueError("--init_from_ema and --experiment_dir must be supplied together")
    if weight > 0.0 and not (has_init and has_experiment_dir):
        raise ValueError("positive --lambda_gradient requires --init_from_ema and --experiment_dir")
    if args.init_from_ema and not os.path.isfile(args.init_from_ema):
        raise FileNotFoundError(f"Initialization checkpoint not found: {args.init_from_ema}")


def resolve_experiment_dirs(experiment_dir, run_name, repo_root=REPO_ROOT):
    if not run_name or os.path.basename(run_name) != run_name or run_name in {".", ".."}:
        raise ValueError("run_name must be a single safe path component")
    root = Path(repo_root).resolve()
    if experiment_dir is None:
        return (os.path.join(str(root), "checkpoints", run_name),
                os.path.join(str(root), "outputs", run_name))
    experiment_root = Path(experiment_dir)
    if not experiment_root.is_absolute():
        experiment_root = root / experiment_root
    experiment_root = experiment_root.resolve()
    expected_root = (root / "experiments" / "ecrformer_gradient_pilot").resolve()
    if experiment_root != expected_root:
        raise ValueError(f"experiment_dir must resolve to {expected_root}")
    checkpoint_dir = experiment_root / "checkpoints" / run_name
    output_dir = experiment_root / "outputs" / run_name
    for path in (checkpoint_dir, output_dir):
        if path.exists() and any(child.is_file() for child in path.rglob("*")):
            raise FileExistsError(f"Refusing to reuse non-empty experiment path: {path}")
    return str(checkpoint_dir), str(output_dir)


def load_epoch30_ema(model, model_ema, checkpoint_path):
    checkpoint_path = os.fspath(checkpoint_path)
    if os.path.basename(checkpoint_path).lower() == "latest_model.pth":
        raise ValueError("latest_model.pth is not a permitted EMA initialization source")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if int(checkpoint.get("epoch", -1)) != 30:
        raise ValueError("Expected the epoch-30 baseline checkpoint")
    if "ema_state_dict" not in checkpoint:
        raise ValueError("Expected checkpoint to contain ema_state_dict")
    model.load_state_dict(checkpoint["ema_state_dict"], strict=True)
    model_ema.load_state_dict(model.state_dict(), strict=True)
    model_state = model.state_dict()
    ema_state = model_ema.state_dict()
    if model_state.keys() != ema_state.keys() or not all(
        torch.equal(model_state[key], ema_state[key]) for key in model_state
    ):
        raise RuntimeError("EMA initialization mismatch before optimizer creation")
    return checkpoint, sha256_file(checkpoint_path)


def compose_training_loss(existing_loss, existing_metrics, pred_direct, target, lambda_gradient):
    total_loss, gradient = add_gradient_term(existing_loss, pred_direct, target, lambda_gradient)
    metrics = dict(existing_metrics)
    weighted_gradient = float(lambda_gradient) * gradient.detach().item()
    metrics["loss_existing"] = existing_loss.detach().item()
    metrics["loss_gradient"] = gradient.detach().item()
    metrics["loss_gradient_weighted"] = weighted_gradient
    metrics["loss_total"] = total_loss.detach().item()
    return total_loss, metrics


def update_ema(ema_model, model, decay=0.999):
    with torch.no_grad():
        for ema_v, model_v in zip(ema_model.state_dict().values(), model.state_dict().values()):
            if ema_v.dtype.is_floating_point:
                ema_v.mul_(decay).add_(model_v, alpha=1.0 - decay)

def gaussian_window(window_size=11, sigma=1.5):
    coords = torch.arange(window_size, dtype=torch.float32) - window_size // 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g = g / g.sum()
    window = g.outer(g).unsqueeze(0).unsqueeze(0)
    return window

def compute_ssim_map(img1, img2, window, C1=0.01**2, C2=0.03**2):
    # img1, img2: [C, 1, H, W]
    mu1 = nn.functional.conv2d(img1, window, padding=window.shape[-1]//2)
    mu2 = nn.functional.conv2d(img2, window, padding=window.shape[-1]//2)
    mu1_sq, mu2_sq, mu1_mu2 = mu1 ** 2, mu2 ** 2, mu1 * mu2
    sigma1_sq = nn.functional.conv2d(img1 * img1, window, padding=window.shape[-1]//2) - mu1_sq
    sigma2_sq = nn.functional.conv2d(img2 * img2, window, padding=window.shape[-1]//2) - mu2_sq
    sigma12 = nn.functional.conv2d(img1 * img2, window, padding=window.shape[-1]//2) - mu1_mu2
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return ssim_map.squeeze(1) # [C, H, W]

def masked_pearson(pred, target, mask_bool):
    corrs = []
    for c in range(pred.shape[0]):
        p_c = pred[c][mask_bool].float()
        t_c = target[c][mask_bool].float()
        if p_c.numel() < 2:
            corrs.append(0.0)
            continue
        p_dev = p_c - p_c.mean()
        t_dev = t_c - t_c.mean()
        denom = torch.sqrt((p_dev ** 2).sum() * (t_dev ** 2).sum() + 1e-12)
        if (p_dev ** 2).sum() < 1e-8 or (t_dev ** 2).sum() < 1e-8:
            corrs.append(0.0)
        else:
            corrs.append(((p_dev * t_dev).sum() / denom).item())
    return float(np.mean(corrs))

def validate(val_loader, model_ema, device, max_batches=None, precision='fp32', select='raw'):
    """
    Evaluates on cloudy pixels (mask > 0.1) across validation patches.

    Scores TWO tensors from the SAME forward pass, both labelled explicitly:

      'raw'   = pred_direct, the network output BEFORE mask blending.
                PRIMARY experimental result.
      'blend' = (1 - mask) * s2_cloudy + mask * pred_direct.
                COMPARISON ONLY. Where mask == 0 this tensor is EXACTLY the cloudy
                input, so in clear regions it is identical to the no-removal baseline
                and is NOT an independent cloud-removal result. The blend guarantees
                clear pixels are left untouched; it does NOT guarantee accuracy there
                (measured clear-region MAE is worse than 'raw').

    Every metric is returned for both variants under '<variant>_<metric>' keys. The
    legacy unsuffixed keys ('psnr', 'ssim', 'l1', 'pearson', 'ndvi_mae', 'ndvi_r')
    alias the variant named by `select`, so existing consumers keep working.
    """
    model_ema.eval()
    keys = ['all', 'light', 'medium', 'heavy', 'heavy_opaque', 'heavy_hazy']
    VARIANTS = ('raw', 'blend')
    if select not in VARIANTS:
        raise ValueError(f"select must be one of {VARIANTS}, got {select!r}")

    def _blank():
        return {k: {'sq_m': 0.0, 'elements': 0.0, 'l1_m': 0.0, 'ssim_m': 0.0, 'r_m': 0.0,
                    'ndvi_mae': 0.0, 'ndvi_r': 0.0, 'count': 0} for k in keys}

    buckets = {v: _blank() for v in VARIANTS}
    ssim_win = gaussian_window(window_size=11, sigma=1.5).to(device)

    l1_band_acc = {v: [0.0, 0.0, 0.0, 0.0] for v in VARIANTS}
    m_band_acc = {v: 0.0 for v in VARIANTS}
    p_band_sum = {v: [0.0, 0.0, 0.0, 0.0] for v in VARIANTS}
    t_band_sum = [0.0, 0.0, 0.0, 0.0]
    pix_cnt = 0

    with torch.no_grad():
        for b_idx, (s2_c, s1, s2_t, cf, mask) in enumerate(val_loader):
            if max_batches is not None and b_idx >= max_batches:
                break
            s2_c = s2_c.to(device, non_blocking=True)
            s1 = s1.to(device, non_blocking=True)
            s2_t = s2_t.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)

            with (torch.autocast(device_type='cuda', dtype=torch.bfloat16)
                              if precision == 'bf16' else contextlib.nullcontext()):
                # model.forward returns (blended_out, pred_direct, projs)
                pred_blend, pred_raw, _ = model_ema(s2_c, s1, mask)
                preds = {'raw': pred_raw, 'blend': pred_blend}
                diff = {v: torch.abs(preds[v] - s2_t) * mask for v in VARIANTS}
                sq_diff = {v: ((preds[v] - s2_t) ** 2) * mask for v in VARIANTS}

            b_size = s2_c.shape[0]
            ch = s2_t.shape[1]

            mask_b = mask[:, 0] > 0.1
            if mask_b.sum() > 0:
                pix_cnt += mask_b.sum().item()
                for c in range(4):
                    t_band_sum[c] += s2_t[:, c][mask_b].float().sum().item()
                for v in VARIANTS:
                    for c in range(4):
                        p_band_sum[v][c] += preds[v][:, c][mask_b].float().sum().item()

            for v in VARIANTS:
                for c in range(4):
                    l1_band_acc[v][c] += diff[v][:, c].sum().item()
                m_band_acc[v] += mask.sum().item()

            for i in range(b_size):
                cf_val = float(cf[i])
                m_sum = float(mask[i].sum().item())
                if m_sum <= 0:
                    continue

                matched = ['all']
                if cf_val < 0.33:
                    matched.append('light')
                elif cf_val < 0.66:
                    matched.append('medium')
                else:
                    matched.append('heavy')
                    mask_bool_dense = mask[i, 0] > 0.1
                    if mask_bool_dense.sum() > 0:
                        mean_b02 = float(s2_c[i, 2][mask_bool_dense].mean().item())
                        if mean_b02 > 0.3:
                            matched.append('heavy_opaque')
                        else:
                            matched.append('heavy_hazy')

                mask_bool = mask[i, 0] > 0.1
                elem_val = m_sum * ch

                for v in VARIANTS:
                    p_i = preds[v][i]
                    l1_val = float(diff[v][i].sum().item()) / (m_sum * ch)
                    sq_val = float(sq_diff[v][i].sum().item())
                    r_val = masked_pearson(p_i, s2_t[i], mask_bool) if mask_bool.sum() > 1 else 0.0

                    # NDVI = (NIR - Red)/(NIR + Red); band3=NIR(B08), band0=Red(B04)
                    ndvi_p = (p_i[3] - p_i[0]) / (p_i[3] + p_i[0] + 1e-6)
                    ndvi_t = (s2_t[i, 3] - s2_t[i, 0]) / (s2_t[i, 3] + s2_t[i, 0] + 1e-6)
                    ndvi_mae_val = float((ndvi_p - ndvi_t).abs()[mask_bool].mean().item()) if mask_bool.sum() > 0 else 0.0
                    ndvi_r_val = masked_pearson(ndvi_p.unsqueeze(0), ndvi_t.unsqueeze(0), mask_bool) if mask_bool.sum() > 1 else 0.0

                    # Masked SSIM
                    ssim_map = compute_ssim_map(p_i.unsqueeze(1).float(), s2_t[i].unsqueeze(1).float(), ssim_win)
                    ssim_val = float(ssim_map[:, mask_bool].mean().item()) if mask_bool.sum() > 0 else 0.0

                    for k in matched:
                        buckets[v][k]['l1_m'] += l1_val
                        buckets[v][k]['sq_m'] += sq_val
                        buckets[v][k]['elements'] += elem_val
                        buckets[v][k]['ssim_m'] += ssim_val
                        buckets[v][k]['r_m'] += r_val
                        buckets[v][k]['ndvi_mae'] += ndvi_mae_val
                        buckets[v][k]['ndvi_r'] += ndvi_r_val
                        buckets[v][k]['count'] += 1

    per_variant = {}
    for v in VARIANTS:
        res = {}
        for k, bv in buckets[v].items():
            cnt = max(1, bv['count'])
            elem = max(1.0, bv['elements'])
            mse = bv['sq_m'] / elem
            psnr = 10.0 * np.log10(1.0 / max(mse, 1e-10)) if bv['elements'] > 0 else 0.0
            res[k] = {
                'l1': bv['l1_m'] / cnt,
                'psnr': psnr,
                'ssim': bv['ssim_m'] / cnt,
                'pearson': bv['r_m'] / cnt,
                'ndvi_mae': bv['ndvi_mae'] / cnt,
                'ndvi_r': bv['ndvi_r'] / cnt,
                'count': bv['count']
            }
        res['all']['l1_bands'] = [a / max(1.0, m_band_acc[v]) for a in l1_band_acc[v]]
        res['all']['p_means'] = [s / max(1, pix_cnt) for s in p_band_sum[v]]
        res['all']['t_means'] = [s / max(1, pix_cnt) for s in t_band_sum]
        per_variant[v] = res

    # Merge: explicit '<variant>_<metric>' for every key, plus legacy unsuffixed
    # aliases taken from `select` so existing consumers keep working unchanged.
    results = {}
    for k in keys:
        merged = {}
        for v in VARIANTS:
            for mk in ('l1', 'psnr', 'ssim', 'pearson', 'ndvi_mae', 'ndvi_r', 'count'):
                merged[f"{v}_{mk}"] = per_variant[v][k][mk]
        for mk in ('l1', 'psnr', 'ssim', 'pearson', 'ndvi_mae', 'ndvi_r', 'count'):
            merged[mk] = per_variant[select][k][mk]
        merged['select'] = select
        results[k] = merged
    for mk in ('l1_bands', 'p_means', 't_means'):
        for v in VARIANTS:
            results['all'][f"{v}_{mk}"] = per_variant[v]['all'][mk]
        results['all'][mk] = per_variant[select]['all'][mk]
    return results

def main():
    parser = argparse.ArgumentParser(description="Controlled ECRformer-Light Training with SDFL")
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--micro_batch_size', type=int, default=2)
    parser.add_argument('--accum_steps', type=int, default=8)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--min_lr', type=float, default=1e-5)
    parser.add_argument('--lambda_enc', type=float, default=0.05, help="Auxiliary encoder loss weight")
    parser.add_argument('--lambda_dec', type=float, default=0.05, help="Auxiliary decoder loss weight")
    parser.add_argument('--sdfl_mode', type=str, default='official_repo', choices=['official_repo', 'paper_strict'],
                        help="SDFL auxiliary supervision: 'official_repo' (90/10 mixed) or 'paper_strict' (100%% pure SSIM/L1)")
    parser.add_argument('--total_loss_form', type=str, default='repo_convex', choices=['repo_convex', 'paper_additive'],
                        help="Total loss weighting: 'repo_convex' ((1-l_enc-l_dec)*L_main + ...) or 'paper_additive' (L_main + l_enc*L_enc + ...)")
    parser.add_argument('--sar_norm', type=str, default='paper_exact', choices=['paper_exact', 'paper_default', 'sen12ms_resnet', 'raw', 'paper'],
                        help="SAR normalization: 'paper_exact' (VV [-25,0], VH [-35,0] -> [0,1]), 'paper_default' ([-25,0] dB -> [0,1]), 'sen12ms_resnet' (VV [-25,0], VH [-32.5,0] -> [0,1]), or 'raw'")
    parser.add_argument('--w_main_l1', type=float, default=1.0)
    parser.add_argument('--w_main_ssim', type=float, default=0.0)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num_workers', type=int, default=4)
    parser.add_argument('--head_init', type=str, default='mean_prior', choices=['mean_prior', 'standard'],
                        help="Head initialization: 'mean_prior' (empirical clear terrain reflectance prior) or 'standard'")
    parser.add_argument('--num_refine', type=int, default=0,
                        help="Number of Restormer refinement blocks (0 = direct decoder output, bypassing refinement)")
    parser.add_argument('--run_name', type=str, default='ecrformer_light_sdfl_run6',
                        help="Run identifier for checkpoint and output directories")
    parser.add_argument('--crop_size', type=int, default=None,
                        help="If set, train/eval on shared square crops of this size "
                             "(e.g. 128). None = full 256x256 patches. Train crops are "
                             "random; validation crops are centre-fixed for determinism.")
    parser.add_argument('--precision', type=str, default='fp32', choices=['fp32', 'bf16'],
                        help="Autocast precision: 'fp32' (default) runs without autocast; "
                             "'bf16' runs under torch.autocast bfloat16.")
    parser.add_argument('--full_domain_main', action='store_true', default=True,
                        help="Supervise raw prediction P directly across the full domain (unmasked)")
    parser.add_argument('--resume', action='store_true', help="Resume training from latest checkpoint")
    parser.add_argument('--dry_run', action='store_true', help="2-step test run")
    parser.add_argument('--select_metric', type=str, default='raw', choices=['raw', 'blend'],
                        help="Which output drives the reported 'psnr'/'ssim'/... aliases and best-checkpoint "
                             "selection: 'raw' = pred_direct (default, primary result) or 'blend' = the "
                             "mask-blended output (legacy behaviour). Both are always measured and saved.")
    parser.add_argument('--resume_force_lr', action='store_true',
                        help="On resume from a LEGACY checkpoint with no scheduler state, force the LR to the "
                             "on-schedule cosine value for the resume epoch. Without this flag the LR saved in "
                             "the checkpoint is kept as-is (never silently rewritten).")
    parser.add_argument('--lambda_gradient', type=float, default=0.0,
                        help="Optional finite-difference loss weight; positive values require isolated EMA init.")
    parser.add_argument('--init_from_ema', type=str, default=None,
                        help="Initialize a fresh run from the epoch-30 EMA checkpoint; never resumes optimizer state.")
    parser.add_argument('--experiment_dir', type=str, default=None,
                        help="Isolated pilot root; paths are placed below its checkpoints/ and outputs/ directories.")
    args = parser.parse_args()

    # Normalize alias 'paper' -> 'paper_default'
    if args.sar_norm == 'paper':
        args.sar_norm = 'paper_default'
    validate_pilot_options(args)

    # Reproducibility
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    # Output and Checkpoint directories strictly isolated per run
    ckpt_dir, output_dir = resolve_experiment_dirs(args.experiment_dir, args.run_name, REPO_ROOT)
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 85)
    print("CONTROLLED ECRFORMER-LIGHT TRAINING RUN (WITH SDFL)")
    print(f"Device: {device} | Epochs: {args.epochs} | Micro-Batch: {args.micro_batch_size} | Accum Steps: {args.accum_steps}")
    print(f"Effective Batch Size: {args.micro_batch_size * args.accum_steps} | LR: {args.lr} -> {args.min_lr}")
    print(f"SDFL Mode: {args.sdfl_mode} | Total Loss Form: {args.total_loss_form} | Full-Domain Main: {args.full_domain_main}")
    print(f"Loss Weights: lambda_enc={args.lambda_enc}, lambda_dec={args.lambda_dec}, w_main=[{args.w_main_l1}, {args.w_main_ssim}]")
    print(f"Gradient loss weight: lambda_gradient={args.lambda_gradient}")
    print(f"Outputs scored: raw=pred_direct (PRIMARY) | blend=(1-mask)*cloudy+mask*pred_direct (comparison on top of the same forward pass)")
    print(f"select_metric={args.select_metric} (drives the reported psnr/ssim aliases and best-checkpoint selection)")
    print(f"SAR Normalization: {args.sar_norm.upper()} | Head Init: {args.head_init} | Num Refine: {args.num_refine}")
    print(f"Checkpoints: {ckpt_dir} | Outputs: {output_dir}")
    print("=" * 85)

    # Dataset paths
    cache_root = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3"
    train_dir = os.path.join(cache_root, "train")
    val_dir = os.path.join(cache_root, "val")

    train_dataset = CachedSEN12MSCRDataset(train_dir, sar_norm=args.sar_norm,
                                           crop_size=args.crop_size, deterministic=False)
    val_dataset = CachedSEN12MSCRDataset(val_dir, sar_norm=args.sar_norm,
                                         crop_size=args.crop_size, deterministic=True)

    # Dedicated seeded generator for identical minibatch permutation
    loader_generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.micro_batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=(args.num_workers > 0),
        generator=loader_generator,
        drop_last=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.micro_batch_size * 2, # Micro-batch 4 for eval
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=(args.num_workers > 0)
    )

    print(f"Train Dataset: {len(train_dataset):,} patches ({len(train_loader):,} micro-batches) [SAR Norm: {args.sar_norm.upper()}]")
    print(f"Val Dataset:   {len(val_dataset):,} patches ({len(val_loader):,} micro-batches) [SAR Norm: {args.sar_norm.upper()}]")

    # Model
    model = ECRformerAdaptedModel(
        features_start=32,
        num_blocks=[2, 2, 1, 1],
        num_refine=args.num_refine,
        bottle_neck='tsa',
        cbam='1ca2+1sa2',
        mask_blend=True,
        head_init=args.head_init
    ).to(device)

    model_ema = copy.deepcopy(model).eval()
    for p in model_ema.parameters():
        p.requires_grad = False

    pilot_checkpoint_metadata = {}
    if args.init_from_ema:
        init_checkpoint, baseline_checkpoint_hash = load_epoch30_ema(
            model, model_ema, args.init_from_ema
        )
        pilot_checkpoint_metadata = {
            "lambda_gradient": args.lambda_gradient,
            "baseline_checkpoint_path": os.path.relpath(os.path.abspath(args.init_from_ema), REPO_ROOT),
            "baseline_checkpoint_sha256": baseline_checkpoint_hash,
            "initialization_epoch": int(init_checkpoint["epoch"]),
            "run_config": vars(args).copy(),
        }
        del init_checkpoint

    # Loss
    criterion = SDFLLoss(
        lambda_enc=args.lambda_enc,
        lambda_dec=args.lambda_dec,
        sdfl_mode=args.sdfl_mode,
        total_loss_form=args.total_loss_form,
        w_main_l1=args.w_main_l1,
        w_main_ssim=args.w_main_ssim,
        full_domain_main=args.full_domain_main
    )

    # Optimizer & Scheduler
    optimizer = optim.Adam(model.parameters(), lr=args.lr, betas=(0.9, 0.999), weight_decay=0.0)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=args.min_lr)

    epochs_to_run = 1 if args.dry_run else args.epochs
    start_epoch = 0
    best_psnr = -float('inf')
    history = {
        'psnr_all': [], 'l1_all': [], 'ssim_all': [], 'pearson_all': [],
        'ndvi_mae_all': [], 'ndvi_r_all': [],
        'model_psnr_all': [], 'model_l1_all': [], 'model_ssim_all': [], 'model_pearson_all': [],
        'model_ndvi_mae_all': [], 'model_ndvi_r_all': [],
        # explicit per-variant series (EMA weights): 'raw' = pred_direct, 'blend' = mask-blended
        'raw_psnr_all': [], 'raw_l1_all': [], 'raw_ssim_all': [], 'raw_pearson_all': [],
        'raw_ndvi_mae_all': [], 'raw_ndvi_r_all': [],
        'blend_psnr_all': [], 'blend_l1_all': [], 'blend_ssim_all': [], 'blend_pearson_all': [],
        'blend_ndvi_mae_all': [], 'blend_ndvi_r_all': [],
        'select_metric': args.select_metric,
        'learning_rates': []
    }

    latest_ckpt_path = os.path.join(ckpt_dir, "latest_model.pth")
    if args.resume and os.path.exists(latest_ckpt_path):
        print(f"Resuming training from {latest_ckpt_path}...")
        ckpt = torch.load(latest_ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt['model_state_dict'])
        model_ema.load_state_dict(ckpt['ema_state_dict'])
        optimizer.load_state_dict(ckpt['optimizer_state_dict'])
        start_epoch = ckpt['epoch']
        best_psnr = ckpt.get('psnr', -float('inf'))

        # ---- scheduler restoration -------------------------------------------------
        # Do NOT rebuild a fresh scheduler and replay `start_epoch` steps: that
        # overwrites the LR restored by optimizer.load_state_dict() with a value from a
        # freshly-constructed schedule and silently drives the run off-schedule.
        ckpt_lr = float(optimizer.param_groups[0]['lr'])
        intended_lr = args.min_lr + (args.lr - args.min_lr) * (
            1.0 + np.cos(np.pi * start_epoch / args.epochs)) / 2.0
        ckpt_select = ckpt.get('psnr_select')
        if ckpt_select is None:
            print(f"  NOTE: LEGACY checkpoint has no 'psnr_select'. best_psnr={best_psnr:.3f} refers to the "
                  f"mask-BLENDED output. With --select_metric={args.select_metric} the first epoch will "
                  f"almost certainly register a new 'best' for a different output definition.")
        elif ckpt_select != args.select_metric:
            print(f"  WARNING: checkpoint was selected on '{ckpt_select}' but --select_metric="
                  f"'{args.select_metric}'. best_psnr={best_psnr:.3f} refers to '{ckpt_select}'; "
                  f"the first epoch may immediately register a new 'best'.")
        if 'scheduler_state_dict' in ckpt:
            scheduler.load_state_dict(ckpt['scheduler_state_dict'])
            print(f"  Scheduler: restored saved state (last_epoch={scheduler.last_epoch}) -> "
                  f"lr={float(optimizer.param_groups[0]['lr']):.6e} "
                  f"(checkpoint lr {ckpt_lr:.6e}, on-schedule {intended_lr:.6e})")
        else:
            # Legacy checkpoint: the true scheduler position was never saved.
            scheduler.last_epoch = start_epoch
            print(f"  Scheduler: LEGACY checkpoint WITHOUT scheduler state -- position is unknown.")
            print(f"    checkpoint optimizer lr   : {ckpt_lr:.6e}")
            print(f"    on-schedule lr for epoch {start_epoch + 1}: {intended_lr:.6e} (T_max={args.epochs})")
            if args.resume_force_lr:
                for _g in optimizer.param_groups:
                    _g['lr'] = intended_lr
                print(f"    --resume_force_lr: LR FORCED to the on-schedule value {intended_lr:.6e}.")
            else:
                print(f"    LR left AS SAVED ({ckpt_lr:.6e}) -- not rewritten. Pass --resume_force_lr "
                      f"if you intend to continue on the original cosine schedule.")

        history_path = os.path.join(output_dir, "history.json")
        if os.path.exists(history_path):
            import json
            _default_keys = list(history.keys())
            with open(history_path, 'r') as f_h:
                history = json.load(f_h)
            # Backfill ANY key this code expects but the older history.json lacks,
            # padded with None so every series stays index-aligned with psnr_all.
            _n = len(history.get('psnr_all', []))
            for _k in _default_keys:
                if _k not in history:
                    history[_k] = [None] * _n
        print(f"Successfully resumed at Epoch {start_epoch + 1}/{epochs_to_run} (Best Val PSNR: {best_psnr:.2f} dB, select={args.select_metric})")

    lr_trace_file = None
    lr_trace_writer = None
    if args.experiment_dir:
        lr_trace_file = open(os.path.join(output_dir, "optimizer_lr_trace.csv"), "x", newline="", encoding="utf-8")
        lr_trace_writer = csv.writer(lr_trace_file)
        lr_trace_writer.writerow(["epoch", "optimizer_update", "lr"])
        lr_trace_file.flush()

    t_start = time.time()
    torch.cuda.reset_peak_memory_stats()

    for epoch in range(start_epoch, epochs_to_run):
        ep_t0 = time.time()
        model.train()
        current_lr = optimizer.param_groups[0]['lr']
        history['learning_rates'].append(current_lr)

        loop = tqdm(train_loader, desc=f"ECRformer-Light Ep {epoch+1}/{epochs_to_run} (lr={current_lr:.2e})")
        running_loss = 0.0
        n_updates = 0
        n_microbatches = 0
        pilot_loss_sums = {key: 0.0 for key in (
            "loss_existing", "loss_gradient", "loss_gradient_weighted", "loss_total"
        )}
        optimizer.zero_grad()

        for step, (s2_c, s1, s2_t, cf, mask) in enumerate(loop):
            if args.dry_run and step >= (args.accum_steps * 2):
                break

            s2_c = s2_c.to(device, non_blocking=True)
            s1 = s1.to(device, non_blocking=True)
            s2_t = s2_t.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)

            with (torch.autocast(device_type='cuda', dtype=torch.bfloat16)
                  if args.precision == 'bf16' else contextlib.nullcontext()):
                pred, pred_direct, projs = model(s2_c, s1, mask)
                loss_existing, loss_dict = criterion(pred, s2_t, mask, projs, pred_direct=pred_direct)
                loss_step, loss_dict = compose_training_loss(
                    loss_existing, loss_dict, pred_direct, s2_t, args.lambda_gradient
                )
                for key in pilot_loss_sums:
                    pilot_loss_sums[key] += float(loss_dict[key])
                n_microbatches += 1
                loss_scaled = loss_step / args.accum_steps

            loss_scaled.backward()
            running_loss += loss_step.item()

            if (step + 1) % args.accum_steps == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                update_lr = float(optimizer.param_groups[0]['lr'])
                optimizer.step()
                if lr_trace_writer is not None:
                    lr_trace_writer.writerow([epoch + 1, n_updates + 1, format(update_lr, ".17g")])
                    lr_trace_file.flush()
                optimizer.zero_grad()
                update_ema(model_ema, model, decay=0.999)
                n_updates += 1

                loop.set_postfix(
                    total=f"{loss_dict['loss_total']:.4f}",
                    l1_m=f"{loss_dict.get('loss_l1_main', 0.0):.4f}",
                    l1_c=f"{loss_dict.get('loss_l1_cloudy', 0.0):.4f}",
                    ssim=f"{loss_dict['loss_ssim_main']:.4f}",
                    enc=f"{loss_dict['loss_enc_aux']:.4f}",
                    dec=f"{loss_dict['loss_dec_aux']:.4f}"
                )

        scheduler.step()

        # Validation at end of epoch (evaluating both EMA and active Model weights)
        val_batches = 2 if args.dry_run else None
        val_res_ema = validate(val_loader, model_ema, device, max_batches=val_batches,
                               precision=args.precision, select=args.select_metric)
        val_res_model = validate(val_loader, model, device, max_batches=val_batches,
                                 precision=args.precision, select=args.select_metric)

        # Legacy aliases follow --select_metric; both variants are always kept.
        psnr_ema = val_res_ema['all']['psnr']
        l1_ema = val_res_ema['all']['l1']
        ssim_ema = val_res_ema['all']['ssim']
        r_ema = val_res_ema['all']['pearson']
        ndvi_mae_ema = val_res_ema['all']['ndvi_mae']
        ndvi_r_ema = val_res_ema['all']['ndvi_r']

        psnr_model = val_res_model['all']['psnr']
        l1_model = val_res_model['all']['l1']
        ssim_model = val_res_model['all']['ssim']
        r_model = val_res_model['all']['pearson']
        ndvi_mae_model = val_res_model['all']['ndvi_mae']
        ndvi_r_model = val_res_model['all']['ndvi_r']

        # explicit per-variant (EMA) values
        raw_psnr = val_res_ema['all']['raw_psnr'];         blend_psnr = val_res_ema['all']['blend_psnr']
        raw_ssim = val_res_ema['all']['raw_ssim'];         blend_ssim = val_res_ema['all']['blend_ssim']
        raw_l1 = val_res_ema['all']['raw_l1'];             blend_l1 = val_res_ema['all']['blend_l1']
        raw_r = val_res_ema['all']['raw_pearson'];         blend_r = val_res_ema['all']['blend_pearson']
        raw_ndvi_mae = val_res_ema['all']['raw_ndvi_mae']; blend_ndvi_mae = val_res_ema['all']['blend_ndvi_mae']
        raw_ndvi_r = val_res_ema['all']['raw_ndvi_r'];     blend_ndvi_r = val_res_ema['all']['blend_ndvi_r']

        history['psnr_all'].append(psnr_ema)
        history['l1_all'].append(l1_ema)
        history['ssim_all'].append(ssim_ema)
        history['pearson_all'].append(r_ema)
        history['ndvi_mae_all'].append(ndvi_mae_ema)
        history['ndvi_r_all'].append(ndvi_r_ema)
        history['model_psnr_all'].append(psnr_model)
        history['model_l1_all'].append(l1_model)
        history['model_ssim_all'].append(ssim_model)
        history['model_pearson_all'].append(r_model)
        history['model_ndvi_mae_all'].append(ndvi_mae_model)
        history['model_ndvi_r_all'].append(ndvi_r_model)
        history['raw_psnr_all'].append(raw_psnr);       history['blend_psnr_all'].append(blend_psnr)
        history['raw_l1_all'].append(raw_l1);           history['blend_l1_all'].append(blend_l1)
        history['raw_ssim_all'].append(raw_ssim);       history['blend_ssim_all'].append(blend_ssim)
        history['raw_pearson_all'].append(raw_r);       history['blend_pearson_all'].append(blend_r)
        history['raw_ndvi_mae_all'].append(raw_ndvi_mae); history['blend_ndvi_mae_all'].append(blend_ndvi_mae)
        history['raw_ndvi_r_all'].append(raw_ndvi_r);   history['blend_ndvi_r_all'].append(blend_ndvi_r)

        is_best = psnr_ema > best_psnr
        if is_best:
            best_psnr = psnr_ema
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'ema_state_dict': model_ema.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'psnr': best_psnr,
                'psnr_select': args.select_metric,
                'psnr_raw': raw_psnr,
                'psnr_blend': blend_psnr,
                'val_metrics': {'ema': val_res_ema, 'model': val_res_model},
                **pilot_checkpoint_metadata,
            }, os.path.join(ckpt_dir, "best_model.pth"))

        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'ema_state_dict': model_ema.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'psnr': psnr_ema,
            'psnr_select': args.select_metric,
            'psnr_raw': raw_psnr,
            'psnr_blend': blend_psnr,
            'val_metrics': {'ema': val_res_ema, 'model': val_res_model},
            **pilot_checkpoint_metadata,
        }, os.path.join(ckpt_dir, "latest_model.pth"))

        ep_duration = (time.time() - ep_t0) / 60.0
        pilot_loss_means = {
            key: value / max(1, n_microbatches) for key, value in pilot_loss_sums.items()
        }
        best_str = f" [BEST: {best_psnr:.2f} dB]" if is_best else ""
        l1_b_ema = val_res_ema['all'].get('l1_bands', [0, 0, 0, 0])
        p_m_ema = val_res_ema['all'].get('p_means', [0, 0, 0, 0])
        l1_b_mod = val_res_model['all'].get('l1_bands', [0, 0, 0, 0])
        p_m_mod = val_res_model['all'].get('p_means', [0, 0, 0, 0])

        log_line = (
            f"Epoch {epoch+1:02d} Complete | Time: {ep_duration:.2f}m | select={args.select_metric}\n"
            f"  OUTPUT DEFINITIONS: raw = pred_direct (network output, no blending)  |  "
            f"blend = (1-mask)*cloudy + mask*pred_direct  [in clear regions blend == cloudy input]\n"
            f"  EMA  RAW   (primary): Val PSNR: {raw_psnr:.2f} dB{best_str} | SSIM: {raw_ssim:.4f} | r: {raw_r:.4f} | L1: {raw_l1:.4f}"
            f" | NDVI-MAE: {raw_ndvi_mae:.4f} | NDVI-r: {raw_ndvi_r:.4f}\n"
            f"  EMA  BLEND (compare): Val PSNR: {blend_psnr:.2f} dB | SSIM: {blend_ssim:.4f} | r: {blend_r:.4f} | L1: {blend_l1:.4f}"
            f" | NDVI-MAE: {blend_ndvi_mae:.4f} | NDVI-r: {blend_ndvi_r:.4f}\n"
            f"  EMA  SELECTED({args.select_metric}): Val PSNR: {psnr_ema:.2f} dB | SSIM: {ssim_ema:.4f} | r: {r_ema:.4f} | L1: {l1_ema:.4f}\n"
            f"                 Per-Band L1: Red={l1_b_ema[0]:.4f}, Green={l1_b_ema[1]:.4f}, Blue={l1_b_ema[2]:.4f}, NIR={l1_b_ema[3]:.4f}\n"
            f"                 Pred Means:  Red={p_m_ema[0]:.4f}, Green={p_m_ema[1]:.4f}, Blue={p_m_ema[2]:.4f}, NIR={p_m_ema[3]:.4f}\n"
            f"  Model SELECTED({args.select_metric}): Val PSNR: {psnr_model:.2f} dB | SSIM: {ssim_model:.4f} | r: {r_model:.4f} | L1: {l1_model:.4f}"
            f" | NDVI-MAE: {ndvi_mae_model:.4f} | NDVI-r: {ndvi_r_model:.4f}\n"
            f"                 Per-Band L1: Red={l1_b_mod[0]:.4f}, Green={l1_b_mod[1]:.4f}, Blue={l1_b_mod[2]:.4f}, NIR={l1_b_mod[3]:.4f}\n"
            f"                 Pred Means:  Red={p_m_mod[0]:.4f}, Green={p_m_mod[1]:.4f}, Blue={p_m_mod[2]:.4f}, NIR={p_m_mod[3]:.4f}\n"
            f"  Train objective means/microbatch: existing={pilot_loss_means['loss_existing']:.6f} | "
            f"gradient={pilot_loss_means['loss_gradient']:.6f} | "
            f"weighted={pilot_loss_means['loss_gradient_weighted']:.6f} | "
            f"total={pilot_loss_means['loss_total']:.6f} | lambda_gradient={args.lambda_gradient:.8g} | "
            f"optimizer_updates={n_updates}"
        )
        print(log_line)

        # Persistent log file & history saving
        log_file_path = os.path.join(output_dir, "training_log.txt")
        with open(log_file_path, "a") as f_log:
            f_log.write(log_line + "\n")

        import json
        with open(os.path.join(output_dir, "history.json"), "w") as f_json:
            json.dump(history, f_json, indent=2)

    if lr_trace_file is not None:
        lr_trace_file.close()
    total_time_min = (time.time() - t_start) / 60.0
    peak_vram_gb = torch.cuda.max_memory_allocated(device) / (1024 ** 3)
    print("\n" + "=" * 85)
    print(f"TRAINING COMPLETE: Total Time = {total_time_min:.2f} min | Peak VRAM = {peak_vram_gb:.2f} GB | Best Val PSNR = {best_psnr:.2f} dB")
    print("=" * 85)

if __name__ == "__main__":
    main()
