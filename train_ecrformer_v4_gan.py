import os
import sys
import time
import copy
import json
import hashlib
import argparse
import numpy as np

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.cache_dataset import CachedSEN12MSCRDataset
from models.ecrformer_adapted import ECRformerAdaptedModel
from losses.cloud_structure_loss import (
    CloudStructurePerceptualLoss,
    apply_opaque_cloud_cutout,
)
from losses.patchgan_loss import (
    ConditionalPatchGANDiscriminator,
    compute_d_loss,
    compute_g_gan_and_fm_loss,
    compute_scale_decoupled_l1,
)

BASELINE_EXPECTED_SHA256 = "2f02aca75619a8b4db52ca5ef4910a0ad305e80c68d48c035c0bb975e5b1a5b6"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_baseline_untouched(path: str) -> None:
    assert os.path.isfile(path), f"Baseline checkpoint missing at {path}"
    digest = sha256_file(path)
    assert digest == BASELINE_EXPECTED_SHA256, (
        f"CRITICAL: Baseline SHA256 mismatch! Expected {BASELINE_EXPECTED_SHA256}, got {digest}"
    )


def update_ema(ema_model: nn.Module, model: nn.Module, decay: float = 0.992) -> None:
    with torch.no_grad():
        for ema_p, p in zip(ema_model.parameters(), model.parameters()):
            ema_p.data.mul_(decay).add_(p.data, alpha=1.0 - decay)
        for ema_b, b in zip(ema_model.buffers(), model.buffers()):
            ema_b.data.copy_(b.data)


def gaussian_window(window_size: int = 11, sigma: float = 1.5) -> torch.Tensor:
    coords = torch.arange(window_size, dtype=torch.float32) - window_size // 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g /= g.sum()
    return (g.unsqueeze(1) * g.unsqueeze(0)).unsqueeze(0).unsqueeze(0)


def compute_ssim_map(img1: torch.Tensor, img2: torch.Tensor, window: torch.Tensor, C1: float = 0.01**2, C2: float = 0.03**2) -> torch.Tensor:
    pad = window.shape[-1] // 2
    mu1 = nn.functional.conv2d(img1, window, padding=pad)
    mu2 = nn.functional.conv2d(img2, window, padding=pad)
    mu1_sq, mu2_sq, mu1_mu2 = mu1.pow(2), mu2.pow(2), mu1 * mu2
    sigma1_sq = nn.functional.conv2d(img1 * img1, window, padding=pad) - mu1_sq
    sigma2_sq = nn.functional.conv2d(img2 * img2, window, padding=pad) - mu2_sq
    sigma12 = nn.functional.conv2d(img1 * img2, window, padding=pad) - mu1_mu2
    return ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))


def masked_pearson(pred: torch.Tensor, target: torch.Tensor, mask_bool: torch.Tensor) -> float:
    p = pred[:, mask_bool].float()
    t = target[:, mask_bool].float()
    if p.numel() < 4:
        return 0.0
    p_mean = p.mean(dim=1, keepdim=True)
    t_mean = t.mean(dim=1, keepdim=True)
    p_diff = p - p_mean
    t_diff = t - t_mean
    num = (p_diff * t_diff).sum(dim=1)
    den = torch.sqrt((p_diff ** 2).sum(dim=1) * (t_diff ** 2).sum(dim=1)) + 1e-8
    return float((num / den).mean().item())


def compute_edge_metrics(pred: torch.Tensor, target: torch.Tensor, mask_bool: torch.Tensor = None):
    p = pred.float()
    t = target.float()
    dx_p = p[:, :-1, 1:] - p[:, :-1, :-1]
    dy_p = p[:, 1:, :-1] - p[:, :-1, :-1]
    dx_t = t[:, :-1, 1:] - t[:, :-1, :-1]
    dy_t = t[:, 1:, :-1] - t[:, :-1, :-1]

    mag_p = torch.sqrt(dx_p ** 2 + dy_p ** 2 + 1e-12)
    mag_t = torch.sqrt(dx_t ** 2 + dy_t ** 2 + 1e-12)

    if mask_bool is not None:
        m_sub = mask_bool[:-1, :-1]
        if m_sub.sum() > 16:
            mp = mag_p[:, m_sub]
            mt = mag_t[:, m_sub]
        else:
            mp = mag_p.flatten(1)
            mt = mag_t.flatten(1)
    else:
        mp = mag_p.flatten(1)
        mt = mag_t.flatten(1)

    ratio = float((mp.mean() / (mt.mean() + 1e-8)).item())

    mp_1d = mp.mean(dim=0)
    mt_1d = mt.mean(dim=0)
    mp_c = mp_1d - mp_1d.mean()
    mt_c = mt_1d - mt_1d.mean()
    corr = float(((mp_c * mt_c).sum() / (torch.sqrt((mp_c ** 2).sum() * (mt_c ** 2).sum()) + 1e-8)).item())
    return ratio, corr


def validate(val_loader, model_eval, device, max_batches=None):
    model_eval.eval()
    keys = ["all", "heavy"]
    stats = {
        k: {"sq": 0.0, "elem": 0.0, "ssim": 0.0, "r": 0.0, "detail_ratio": 0.0, "grad_corr": 0.0, "count": 0}
        for k in keys
    }
    ssim_win = gaussian_window(11, 1.5).to(device)

    with torch.no_grad():
        for b_idx, (s2_c, s1, s2_t, cf, mask) in enumerate(val_loader):
            if max_batches is not None and b_idx >= max_batches:
                break
            s2_c = s2_c.to(device, non_blocking=True)
            s1 = s1.to(device, non_blocking=True)
            s2_t = s2_t.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)

            _, pred_raw, _ = model_eval(s2_c, s1, mask)
            sq_diff = ((pred_raw - s2_t) ** 2) * mask

            b_size, ch = s2_t.shape[0], s2_t.shape[1]
            for i in range(b_size):
                cf_val = float(cf[i])
                m_sum = float(mask[i].sum().item())
                if m_sum <= 0:
                    continue
                mask_bool = mask[i, 0] > 0.1
                if mask_bool.sum() < 16:
                    continue

                p_i = pred_raw[i]
                t_i = s2_t[i]
                sq_val = float(sq_diff[i].sum().item())
                elem_val = m_sum * ch
                r_val = masked_pearson(p_i, t_i, mask_bool)
                ssim_map = compute_ssim_map(p_i.unsqueeze(1).float(), t_i.unsqueeze(1).float(), ssim_win).squeeze(1)
                ssim_val = float(ssim_map[:, mask_bool].mean().item())
                d_ratio, g_corr = compute_edge_metrics(p_i, t_i, mask_bool=mask_bool)

                matched = ["all"]
                if cf_val >= 0.66:
                    matched.append("heavy")
                for k in matched:
                    stats[k]["sq"] += sq_val
                    stats[k]["elem"] += elem_val
                    stats[k]["ssim"] += ssim_val
                    stats[k]["r"] += r_val
                    stats[k]["detail_ratio"] += d_ratio
                    stats[k]["grad_corr"] += g_corr
                    stats[k]["count"] += 1

    res = {}
    for k in keys:
        c = max(1, stats[k]["count"])
        mse = stats[k]["sq"] / max(1e-8, stats[k]["elem"])
        res[k] = {
            "psnr": float(10.0 * np.log10(1.0 / max(mse, 1e-10))),
            "ssim": float(stats[k]["ssim"] / c),
            "pearson": float(stats[k]["r"] / c),
            "detail_ratio": float(stats[k]["detail_ratio"] / c),
            "grad_corr": float(stats[k]["grad_corr"] / c),
        }
    return res


def main():
    parser = argparse.ArgumentParser(description="ECRformer V4 Conditional PatchGAN + Scale-Decoupled L1")
    parser.add_argument("--cache_dir", type=str, default=r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--max_steps_per_epoch", type=int, default=1600)
    parser.add_argument("--val_max_batches", type=int, default=None)
    parser.add_argument("--d_warmup_steps", type=int, default=200, help="Discriminator-only warmup micro-batches")
    parser.add_argument("--micro_batch_size", type=int, default=4)
    parser.add_argument("--accum_steps", type=int, default=4)
    parser.add_argument("--lr_g", type=float, default=1.5e-4)
    parser.add_argument("--lr_d", type=float, default=2.5e-4)
    parser.add_argument("--sar_lr_mult", type=float, default=2.0)
    parser.add_argument("--min_lr", type=float, default=1e-5)
    parser.add_argument("--cutout_prob", type=float, default=0.65)
    parser.add_argument("--w_adv", type=float, default=0.04)
    parser.add_argument("--w_fm", type=float, default=0.35)
    parser.add_argument("--dr_weight", type=float, default=0.15, help="Weight of detail ratio in best-checkpoint score (edge corr weight is 1.0)")
    parser.add_argument("--lambda_struct", type=float, default=1.25)
    parser.add_argument("--ema_decay", type=float, default=0.990)
    parser.add_argument("--crop_size", type=int, default=128)
    parser.add_argument("--sar_norm", type=str, default="paper_exact")
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run_name", type=str, default="ecrformer_v4_gan")
    parser.add_argument(
        "--baseline_ckpt",
        type=str,
        default=r"C:\Users\Windows 11 Pro\Videos\Projects\ECRformer\checkpoints\ecrformer_light_128_50ep\best_model.pth",
    )
    parser.add_argument(
        "--init_ckpt",
        type=str,
        default=r"C:\Users\Windows 11 Pro\Videos\Projects\ECRformer\checkpoints\ecrformer_v3_structure\best_structure_model.pth",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    verify_baseline_untouched(args.baseline_ckpt)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ckpt_dir = os.path.join(base_dir, "checkpoints", args.run_name)
    out_dir = os.path.join(base_dir, "outputs", args.run_name)
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, "training_log.txt")

    train_dataset = CachedSEN12MSCRDataset(
        os.path.join(args.cache_dir, "train"),
        sar_norm=args.sar_norm,
        crop_size=args.crop_size,
        deterministic=False,
    )
    val_dataset = CachedSEN12MSCRDataset(
        os.path.join(args.cache_dir, "val"),
        sar_norm=args.sar_norm,
        crop_size=args.crop_size,
        deterministic=True,
    )

    g = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.micro_batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=False,
        drop_last=True,
        generator=g,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.micro_batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=False,
    )

    model = ECRformerAdaptedModel(
        features_start=32,
        num_blocks=[2, 2, 1, 1],
        num_refine=0,
        bottle_neck="tsa",
        cbam="1ca2+1sa2",
        drop_path_rate=0.0,
        mask_blend=True,
        head_init="mean_prior",
    ).to(device)
    model_ema = copy.deepcopy(model).to(device)
    model_ema.eval()

    init_path = args.init_ckpt if os.path.isfile(args.init_ckpt) else args.baseline_ckpt
    ck_init = torch.load(init_path, map_location="cpu", weights_only=False)
    src_state = ck_init.get("ema_state_dict", ck_init.get("model_state_dict"))
    model.load_state_dict(src_state, strict=True)
    model_ema.load_state_dict(src_state, strict=True)
    del ck_init
    print(f"Initialized Generator from: {init_path}")

    disc = ConditionalPatchGANDiscriminator(in_ch=11, base_ch=64).to(device)

    struct_criterion = CloudStructurePerceptualLoss(
        w_vgg=0.008,
        w_ms_grad=0.35,
        w_edge_corr=0.004,
        w_local_std=0.50,
        cloud_boost=2.5,
        reflectance_scale=2.5,
    ).to(device)

    sar_params = []
    other_params = []
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "stem.branch.0" in name or "encoder.0" in name:
            sar_params.append(param)
        else:
            other_params.append(param)

    opt_g = optim.Adam(
        [
            {"params": other_params, "lr": args.lr_g},
            {"params": sar_params, "lr": args.lr_g * args.sar_lr_mult},
        ],
        betas=(0.5, 0.999),
        weight_decay=0.0,
    )
    opt_d = optim.Adam(disc.parameters(), lr=args.lr_d, betas=(0.5, 0.999), weight_decay=0.0)

    sched_g = CosineAnnealingLR(opt_g, T_max=args.epochs, eta_min=args.min_lr)
    sched_d = CosineAnnealingLR(opt_d, T_max=args.epochs, eta_min=args.min_lr)

    print("Running initial reference validation...")
    base_val = validate(val_loader, model_ema, device, max_batches=args.val_max_batches)
    print(
        f"Initial Ref -> Heavy PSNR: {base_val['heavy']['psnr']:.2f} dB | "
        f"Heavy Detail: {base_val['heavy']['detail_ratio']:.4f} | "
        f"Heavy EdgeCorr: {base_val['heavy']['grad_corr']:.4f}"
    )

    best_score = base_val["heavy"]["grad_corr"] + args.dr_weight * min(base_val["heavy"]["detail_ratio"], 1.0)
    history = {"initial_ref": base_val, "epochs": []}
    start_epoch = 0
    global_step = 0

    if args.resume:
        latest_ckpt = os.path.join(ckpt_dir, "latest_model.pth")
        history_file = os.path.join(out_dir, "history.json")
        best_ckpt = os.path.join(ckpt_dir, "best_gan_model.pth")
        if os.path.isfile(best_ckpt):
            ck_b = torch.load(best_ckpt, map_location="cpu", weights_only=False)
            vm = ck_b.get("val_metrics", {}).get("heavy", {})
            if vm:
                best_score = vm.get("grad_corr", 0.0) + args.dr_weight * min(vm.get("detail_ratio", 1.0), 1.0)
                print(f"Resumed best_score from best_gan_model.pth: {best_score:.4f} (gc={vm.get('grad_corr'):.4f}, dr={vm.get('detail_ratio'):.4f})")
        if os.path.isfile(history_file):
            try:
                with open(history_file, "r") as hf:
                    history = json.load(hf)
            except Exception:
                pass
        if os.path.isfile(latest_ckpt):
            print(f"Resuming V4 GAN from: {latest_ckpt}")
            ck_r = torch.load(latest_ckpt, map_location=device, weights_only=False)
            model.load_state_dict(ck_r["model_state_dict"])
            model_ema.load_state_dict(ck_r["ema_state_dict"])
            disc.load_state_dict(ck_r["disc_state_dict"])
            opt_g.load_state_dict(ck_r["opt_g_state_dict"])
            opt_d.load_state_dict(ck_r["opt_d_state_dict"])
            sched_g.load_state_dict(ck_r["sched_g_state_dict"])
            sched_d.load_state_dict(ck_r["sched_d_state_dict"])
            start_epoch = int(ck_r.get("epoch", 0))
            global_step = int(ck_r.get("global_step", args.d_warmup_steps + 1))
            del ck_r

    for epoch in range(start_epoch, args.epochs):
        t0 = time.time()
        model.train()
        disc.train()
        opt_g.zero_grad()

        total_steps = min(len(train_loader), args.max_steps_per_epoch) if args.max_steps_per_epoch else len(train_loader)
        pbar = tqdm(train_loader, total=total_steps, desc=f"GAN Ep {epoch+1:02d}/{args.epochs}")

        for step, (s2_c, s1, s2_t, cf, mask) in enumerate(pbar):
            if args.max_steps_per_epoch and step >= args.max_steps_per_epoch:
                break

            global_step += 1
            s2_c = s2_c.to(device, non_blocking=True)
            s1 = s1.to(device, non_blocking=True)
            s2_t = s2_t.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)

            s2_c_in = apply_opaque_cloud_cutout(s2_c, mask, prob=args.cutout_prob)

            # 1. Forward Generator
            if global_step <= args.d_warmup_steps:
                with torch.no_grad():
                    _, pred_direct, projs = model(s2_c_in, s1, mask)
            else:
                _, pred_direct, projs = model(s2_c_in, s1, mask)

            # 2. Update Discriminator D
            opt_d.zero_grad()
            loss_d, d_met = compute_d_loss(disc, pred_direct.detach(), s2_t, s1, mask)
            loss_d.backward()
            torch.nn.utils.clip_grad_norm_(disc.parameters(), max_norm=1.0)
            opt_d.step()

            # 3. Update Generator G (after D warmup)
            if global_step > args.d_warmup_steps:
                loss_l1, l1_met = compute_scale_decoupled_l1(pred_direct, s2_t, mask, projs)
                loss_struct, s_met = struct_criterion(pred_direct, s2_t, mask)
                loss_gan, g_met = compute_g_gan_and_fm_loss(
                    disc, pred_direct, s2_t, s1, mask, w_adv=args.w_adv, w_fm=args.w_fm
                )

                loss_g = loss_l1 + args.lambda_struct * loss_struct + loss_gan
                (loss_g / args.accum_steps).backward()

                if (step + 1) % args.accum_steps == 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    opt_g.step()
                    opt_g.zero_grad()
                    update_ema(model_ema, model, decay=args.ema_decay)

                    pbar.set_postfix(
                        d=f"{d_met['d_loss']:.2f}",
                        fm=f"{g_met['g_fm']:.3f}",
                        ecorr=f"{1.0 - s_met['loss_edge_corr']:.3f}",
                        lstd=f"{s_met['loss_local_std']:.4f}",
                    )
            else:
                pbar.set_postfix(warmup=f"{global_step}/{args.d_warmup_steps}", d=f"{d_met['d_loss']:.2f}")

        sched_g.step()
        sched_d.step()

        val_res = validate(val_loader, model_ema, device, max_batches=args.val_max_batches)
        dt = (time.time() - t0) / 60.0

        h_psnr = val_res["heavy"]["psnr"]
        h_dr = val_res["heavy"]["detail_ratio"]
        h_gc = val_res["heavy"]["grad_corr"]
        score = h_gc + args.dr_weight * min(h_dr, 1.0)

        status = ""
        if score > best_score and h_psnr >= 27.50:
            best_score = score
            status = f" [NEW BEST GAN: grad_corr={h_gc:.4f}, detail={h_dr:.4f}]"
            torch.save(
                {
                    "epoch": epoch + 1,
                    "global_step": global_step,
                    "model_state_dict": model.state_dict(),
                    "ema_state_dict": model_ema.state_dict(),
                    "disc_state_dict": disc.state_dict(),
                    "val_metrics": val_res,
                },
                os.path.join(ckpt_dir, "best_gan_model.pth"),
            )

        torch.save(
            {
                "epoch": epoch + 1,
                "global_step": global_step,
                "model_state_dict": model.state_dict(),
                "ema_state_dict": model_ema.state_dict(),
                "disc_state_dict": disc.state_dict(),
                "opt_g_state_dict": opt_g.state_dict(),
                "opt_d_state_dict": opt_d.state_dict(),
                "sched_g_state_dict": sched_g.state_dict(),
                "sched_d_state_dict": sched_d.state_dict(),
                "val_metrics": val_res,
            },
            os.path.join(ckpt_dir, "latest_model.pth"),
        )

        msg = (
            f"Epoch {epoch+1:02d} ({dt:.2f}m) | "
            f"ALL: PSNR={val_res['all']['psnr']:.2f} dB, SSIM={val_res['all']['ssim']:.4f}, "
            f"Detail={val_res['all']['detail_ratio']:.4f}, EdgeCorr={val_res['all']['grad_corr']:.4f} | "
            f"HEAVY: PSNR={h_psnr:.2f} dB, Detail={h_dr:.4f}, EdgeCorr={h_gc:.4f}{status}"
        )
        print("\n" + msg)
        with open(log_file, "a") as lf:
            lf.write(msg + "\n")

        history["epochs"].append(val_res)
        with open(os.path.join(out_dir, "history.json"), "w") as hf:
            json.dump(history, hf, indent=2)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    verify_baseline_untouched(args.baseline_ckpt)
    print("V4 GAN Training complete. Baseline SHA256 verified untouched.")


if __name__ == "__main__":
    main()
