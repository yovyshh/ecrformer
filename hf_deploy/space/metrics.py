"""Image quality and edge metrics for ECRformer evaluation."""

import math
import torch


def psnr(pred: torch.Tensor, target: torch.Tensor, mask_bool: torch.Tensor = None, eps: float = 1e-9) -> float:
    """Compute peak signal-to-noise ratio over masked cloud region or full image across all channels."""
    p = pred.float()
    t = target.float()
    if p.ndim == 4:
        p = p[0]
    if t.ndim == 4:
        t = t[0]

    if mask_bool is not None and mask_bool.sum() >= 16:
        p_sub = p[:, mask_bool]
        t_sub = t[:, mask_bool]
        rmse = torch.sqrt(torch.mean(torch.square(p_sub - t_sub)))
    else:
        rmse = torch.sqrt(torch.mean(torch.square(p - t)))
    val = 20.0 * torch.log10(1.0 / (rmse + eps))
    return float(val.item())


def sam(pred: torch.Tensor, target: torch.Tensor, mask_bool: torch.Tensor = None, eps: float = 1e-9) -> float:
    """Compute Spectral Angle Mapper (SAM) in degrees over masked cloud region or full image."""
    p = pred.float()
    t = target.float()
    if p.ndim == 4:
        p = p[0]
    if t.ndim == 4:
        t = t[0]

    if mask_bool is not None and mask_bool.sum() >= 16:
        p_sub = p[:, mask_bool]
        t_sub = t[:, mask_bool]
        mat = torch.mean(p_sub * t_sub, dim=0) / (
            torch.sqrt(torch.mean(p_sub * p_sub, dim=0)) * torch.sqrt(torch.mean(t_sub * t_sub, dim=0)) + eps
        )
        sam_deg = torch.mean(torch.acos(torch.clamp(mat, -1.0, 1.0))) * 180.0 / torch.pi
    else:
        mat = torch.mean(p * t, dim=0) / (
            torch.sqrt(torch.mean(p * p, dim=0)) * torch.sqrt(torch.mean(t * t, dim=0)) + eps
        )
        sam_deg = torch.mean(torch.acos(torch.clamp(mat, -1.0, 1.0))) * 180.0 / torch.pi

    return float(sam_deg.item())


def compute_edge_metrics(pred: torch.Tensor, target: torch.Tensor, mask_bool: torch.Tensor = None):
    """Verbatim edge correlation and detail ratio from backend/train_ecrformer_v4_gan.py."""
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


def _clean_val(v: float) -> float:
    if v is None or math.isnan(v) or math.isinf(v):
        return 0.0
    return round(float(v), 4)


def compute_all(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> dict:
    """Compute all image quality metrics: psnr, sam, edgeCorr, hfRetention."""
    p4 = pred if pred.ndim == 4 else pred.unsqueeze(0)
    t4 = target if target.ndim == 4 else target.unsqueeze(0)
    p3 = p4[0]
    t3 = t4[0]

    if mask.ndim == 4:
        mask_2d = mask[0, 0]
    elif mask.ndim == 3:
        mask_2d = mask[0]
    else:
        mask_2d = mask
    mask_bool = mask_2d > 0.1

    psnr_val = psnr(p3, t3, mask_bool=mask_bool)
    sam_val = sam(p3, t3, mask_bool=mask_bool)
    ratio_val, corr_val = compute_edge_metrics(p3, t3, mask_bool=mask_bool)

    return {
        "psnr": _clean_val(psnr_val),
        "sam": _clean_val(sam_val),
        "edgeCorr": _clean_val(corr_val),
        "hfRetention": _clean_val(ratio_val),
    }


def zero_metrics() -> dict:
    """Return empty/zero metrics set."""
    return {
        "psnr": 0.0,
        "sam": 0.0,
        "edgeCorr": 0.0,
        "hfRetention": 0.0,
    }

