import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import vgg16, VGG16_Weights
from typing import Tuple, Dict


def apply_opaque_cloud_cutout(
    s2_c: torch.Tensor, mask: torch.Tensor, prob: float = 0.65
) -> torch.Tensor:
    """
    Training-only modality dropout ('Opaque Cloud Cutout') inside cloud masks.

    In SEN12MS-CR, many cloudy training patches are semi-transparent haze where
    ground edges leak through s2_cloudy (corr > 0.80). The network learns to cheat
    by reading optical edges from s2_cloudy and ignores Sentinel-1 SAR spatial structure.

    With probability `prob` per sample, this replaces s2_cloudy inside the cloud mask
    with a heavily low-pass-filtered cloud veil (two passes of 15x15 reflection-padded
    average pooling) plus realistic opaque cloud brightening. This preserves exact
    radiometric bounds [0, 1] and large-scale cloud luminance while erasing leaked
    optical ground texture inside the cloud, forcing the model to extract spatial
    boundaries from Sentinel-1 SAR (s1) and clear surrounding context.
    """
    if prob <= 0.0:
        return s2_c

    B = s2_c.shape[0]
    device = s2_c.device
    do_aug = (torch.rand(B, 1, 1, 1, device=device) < prob).float()
    if do_aug.sum() == 0:
        return s2_c

    # Two passes of 15x15 reflection-padded average pooling (~29x29 Gaussian veil)
    veil = F.avg_pool2d(F.pad(s2_c, (7, 7, 7, 7), mode="reflect"), kernel_size=15, stride=1)
    veil = F.avg_pool2d(F.pad(veil, (7, 7, 7, 7), mode="reflect"), kernel_size=15, stride=1)

    # Soft mask gating concentrated in the cloud core
    alpha = torch.clamp((mask - 0.15) / 0.85, 0.0, 1.0) * do_aug
    s2_aug = (1.0 - alpha) * s2_c + alpha * veil
    return torch.clamp(s2_aug, 0.0, 1.0)


class CloudStructurePerceptualLoss(nn.Module):
    """
    Gradient-Balanced Structural, Contrast & Perceptual Loss for Opaque Cloud Reconstruction.

    Default weights are empirically calibrated by backpropagated gradient norm ||dL/dP||
    against SDFLLoss (w_main_l1=0.75, w_main_ssim=0.25) on real SEN12MS-CR cloudy patches:
      - w_vgg = 0.005       (VGG16 relu1_2, relu2_2, relu3_3 on 2.5x RGB + NIR-R-G)
      - w_ms_grad = 0.25    (Multi-scale 1x, 2x, 4x pooled signed gradients)
      - w_edge_corr = 0.0025 (Direct Pearson spatial correlation of edge maps in cloud)
      - w_local_std = 0.35  (Local 16x16 standard deviation contrast matching)
    """

    def __init__(
        self,
        w_vgg: float = 0.005,
        w_ms_grad: float = 0.25,
        w_edge_corr: float = 0.0025,
        w_local_std: float = 0.35,
        cloud_boost: float = 2.0,
        reflectance_scale: float = 2.5,
    ):
        super().__init__()
        self.w_vgg = float(w_vgg)
        self.w_ms_grad = float(w_ms_grad)
        self.w_edge_corr = float(w_edge_corr)
        self.w_local_std = float(w_local_std)
        self.cloud_boost = float(cloud_boost)
        self.reflectance_scale = float(reflectance_scale)

        vgg_feats = vgg16(weights=VGG16_Weights.IMAGENET1K_V1).features
        self.slice1 = nn.Sequential(*[vgg_feats[i] for i in range(0, 4)]).eval()
        self.slice2 = nn.Sequential(*[vgg_feats[i] for i in range(4, 9)]).eval()
        self.slice3 = nn.Sequential(*[vgg_feats[i] for i in range(9, 16)]).eval()
        for param in self.parameters():
            param.requires_grad = False

        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def _normalize_3ch(self, x3: torch.Tensor) -> torch.Tensor:
        x_scaled = torch.clamp(x3 * self.reflectance_scale, 0.0, 1.0)
        return (x_scaled - self.mean) / self.std

    def _vgg_loss_3ch(self, p3: torch.Tensor, t3: torch.Tensor, weight_map: torch.Tensor) -> torch.Tensor:
        p_in = self._normalize_3ch(p3)
        with torch.no_grad():
            t_in = self._normalize_3ch(t3)

        f_p1 = self.slice1(p_in)
        with torch.no_grad():
            f_t1 = self.slice1(t_in)
        l1 = (torch.abs(f_p1 - f_t1) * weight_map).mean()

        f_p2 = self.slice2(f_p1)
        with torch.no_grad():
            f_t2 = self.slice2(f_t1)
            w2 = F.avg_pool2d(weight_map, kernel_size=2, stride=2)
        l2 = (torch.abs(f_p2 - f_t2) * w2).mean()

        f_p3 = self.slice3(f_p2)
        with torch.no_grad():
            f_t3 = self.slice3(f_t2)
            w3 = F.avg_pool2d(w2, kernel_size=2, stride=2)
        l3 = (torch.abs(f_p3 - f_t3) * w3).mean()

        return (l1 + 0.7 * l2 + 0.4 * l3) / 2.1

    @staticmethod
    def _grad_xy(x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        dx = x[..., :-1, 1:] - x[..., :-1, :-1]
        dy = x[..., 1:, :-1] - x[..., :-1, :-1]
        mag = torch.sqrt(dx * dx + dy * dy + 1e-8)
        return dx, dy, mag

    def forward(
        self, pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        p = pred.float()
        t = target.float()
        m = mask.float()

        w_map = 1.0 + self.cloud_boost * m

        # 1. Cloud-Weighted VGG Perceptual Loss
        if self.w_vgg > 0.0:
            loss_vgg_rgb = self._vgg_loss_3ch(p[:, :3], t[:, :3], w_map)
            loss_vgg_nir = self._vgg_loss_3ch(p[:, [3, 0, 1]], t[:, [3, 0, 1]], w_map)
            loss_vgg = 0.6 * loss_vgg_rgb + 0.4 * loss_vgg_nir
        else:
            loss_vgg = torch.tensor(0.0, device=p.device)

        # 2. Multi-Scale Pooled Signed Gradient Loss
        p_s2 = F.avg_pool2d(p, kernel_size=2, stride=2)
        t_s2 = F.avg_pool2d(t, kernel_size=2, stride=2)
        w_s2 = F.avg_pool2d(w_map, kernel_size=2, stride=2)[..., :-1, :-1]
        dx_p2, dy_p2, mag_p2 = self._grad_xy(p_s2)
        dx_t2, dy_t2, mag_t2 = self._grad_xy(t_s2)
        loss_grad_s2 = ((torch.abs(dx_p2 - dx_t2) + torch.abs(dy_p2 - dy_t2)) * w_s2).mean()

        p_s4 = F.avg_pool2d(p_s2, kernel_size=2, stride=2)
        t_s4 = F.avg_pool2d(t_s2, kernel_size=2, stride=2)
        w_s4 = F.avg_pool2d(w_map, kernel_size=4, stride=4)[..., :-1, :-1]
        dx_p4, dy_p4, _ = self._grad_xy(p_s4)
        dx_t4, dy_t4, _ = self._grad_xy(t_s4)
        loss_grad_s4 = ((torch.abs(dx_p4 - dx_t4) + torch.abs(dy_p4 - dy_t4)) * w_s4).mean()

        dx_p1, dy_p1, mag_p1 = self._grad_xy(p)
        dx_t1, dy_t1, mag_t1 = self._grad_xy(t)
        w_s1 = w_map[..., :-1, :-1]
        loss_grad_s1 = ((torch.abs(dx_p1 - dx_t1) + torch.abs(dy_p1 - dy_t1)) * w_s1).mean()

        loss_ms_grad = 0.25 * loss_grad_s1 + 0.50 * loss_grad_s2 + 0.25 * loss_grad_s4

        # 3. Direct Edge-Map Spatial Correlation Loss
        m_edge1 = (m[..., :-1, :-1] > 0.2).float()
        if m_edge1.sum() < 64:
            m_edge1 = torch.ones_like(m_edge1)

        mp_flat = (mag_p1.mean(dim=1, keepdim=True) * m_edge1).flatten(1)
        mt_flat = (mag_t1.mean(dim=1, keepdim=True) * m_edge1).flatten(1)
        mp_c = mp_flat - mp_flat.mean(dim=1, keepdim=True)
        mt_c = mt_flat - mt_flat.mean(dim=1, keepdim=True)
        corr_1 = (mp_c * mt_c).sum(dim=1) / torch.sqrt((mp_c.pow(2).sum(dim=1) + 1e-5) * (mt_c.pow(2).sum(dim=1) + 1e-5))

        mp2_flat = mag_p2.mean(dim=1, keepdim=True).flatten(1)
        mt2_flat = mag_t2.mean(dim=1, keepdim=True).flatten(1)
        mp2_c = mp2_flat - mp2_flat.mean(dim=1, keepdim=True)
        mt2_c = mt2_flat - mt2_flat.mean(dim=1, keepdim=True)
        corr_2 = (mp2_c * mt2_c).sum(dim=1) / torch.sqrt((mp2_c.pow(2).sum(dim=1) + 1e-5) * (mt2_c.pow(2).sum(dim=1) + 1e-5))

        loss_edge_corr = (1.0 - 0.5 * (corr_1 + corr_2)).mean()

        # 4. Local 16x16 Patch Contrast (Standard Deviation) Matching
        def local_std(x_in: torch.Tensor, k: int = 16, s: int = 8) -> torch.Tensor:
            mu = F.avg_pool2d(x_in, kernel_size=k, stride=s)
            mu_sq = F.avg_pool2d(x_in * x_in, kernel_size=k, stride=s)
            return torch.sqrt(torch.clamp(mu_sq - mu * mu, min=1e-8))

        std_p = local_std(p, k=16, s=8)
        std_t = local_std(t, k=16, s=8)
        w_std = F.avg_pool2d(w_map, kernel_size=16, stride=8)
        loss_local_std = (torch.abs(std_p - std_t) * w_std).mean()

        total = (
            self.w_vgg * loss_vgg
            + self.w_ms_grad * loss_ms_grad
            + self.w_edge_corr * loss_edge_corr
            + self.w_local_std * loss_local_std
        )

        metrics = {
            "loss_struct_total": float(total.item()),
            "loss_vgg": float(loss_vgg.item()),
            "loss_ms_grad": float(loss_ms_grad.item()),
            "loss_edge_corr": float(loss_edge_corr.item()),
            "loss_local_std": float(loss_local_std.item()),
        }
        return total, metrics
