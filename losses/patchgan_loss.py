import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import spectral_norm
from typing import Tuple, List, Dict


class ConditionalPatchGANDiscriminator(nn.Module):
    """
    Spectral-Normalized Conditional PatchGAN Discriminator for SAR-Guided Cloud Inpainting.

    Input channels (11 total):
      - 4 ch: Optical reflectance (scaled by 3.0x into visual dynamic range)
      - 4 ch: Explicit high-pass detail residual (x - AvgPool5x5(x)) * 10.0
              (Makes blurry cloud smudges immediately distinguishable from sharp real terrain)
      - 2 ch: Sentinel-1 SAR (VV, VH) structural conditioning
      - 1 ch: Soft cloud mask M
    """

    def __init__(self, in_ch: int = 11, base_ch: int = 64):
        super().__init__()
        self.layer1 = nn.Sequential(
            spectral_norm(nn.Conv2d(in_ch, base_ch, kernel_size=4, stride=2, padding=1, padding_mode="reflect")),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.layer2 = nn.Sequential(
            spectral_norm(nn.Conv2d(base_ch, base_ch * 2, kernel_size=4, stride=2, padding=1, padding_mode="reflect")),
            nn.GroupNorm(8, base_ch * 2),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.layer3 = nn.Sequential(
            spectral_norm(nn.Conv2d(base_ch * 2, base_ch * 4, kernel_size=4, stride=2, padding=1, padding_mode="reflect")),
            nn.GroupNorm(16, base_ch * 4),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.layer4 = nn.Sequential(
            spectral_norm(nn.Conv2d(base_ch * 4, base_ch * 4, kernel_size=3, stride=1, padding=1, padding_mode="reflect")),
            nn.GroupNorm(16, base_ch * 4),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.head = spectral_norm(nn.Conv2d(base_ch * 4, 1, kernel_size=3, stride=1, padding=1, padding_mode="reflect"))

    @staticmethod
    def _build_input(opt: torch.Tensor, s1: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        opt_f = opt.float()
        low = F.avg_pool2d(F.pad(opt_f, (2, 2, 2, 2), mode="reflect"), kernel_size=5, stride=1)
        high_pass = (opt_f - low) * 10.0
        opt_scaled = opt_f * 3.0
        return torch.cat([opt_scaled, high_pass, s1.float(), mask.float()], dim=1)

    def forward(
        self, opt: torch.Tensor, s1: torch.Tensor, mask: torch.Tensor
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        x = self._build_input(opt, s1, mask)
        f1 = self.layer1(x)
        f2 = self.layer2(f1)
        f3 = self.layer3(f2)
        f4 = self.layer4(f3)
        logits = self.head(f4)
        return logits, [f1, f2, f3, f4]


def compute_d_loss(
    disc: ConditionalPatchGANDiscriminator,
    pred_direct: torch.Tensor,
    target: torch.Tensor,
    s1: torch.Tensor,
    mask: torch.Tensor,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Hinge GAN loss for Discriminator focused on cloudy regions."""
    real_logits, _ = disc(target.detach(), s1.detach(), mask.detach())
    fake_logits, _ = disc(pred_direct.detach(), s1.detach(), mask.detach())

    # Spatial mask weight at 1/8 resolution (16x16 for 128x128 input)
    m_down = F.interpolate(mask.float(), size=real_logits.shape[-2:], mode="bilinear", align_corners=False)
    w_patch = 0.25 + 0.75 * m_down

    loss_real = (F.relu(1.0 - real_logits) * w_patch).mean()
    loss_fake = (F.relu(1.0 + fake_logits) * w_patch).mean()
    loss_d = 0.5 * (loss_real + loss_fake)

    return loss_d, {
        "d_loss": float(loss_d.item()),
        "d_real": float(real_logits.mean().item()),
        "d_fake": float(fake_logits.mean().item()),
    }


def compute_g_gan_and_fm_loss(
    disc: ConditionalPatchGANDiscriminator,
    pred_direct: torch.Tensor,
    target: torch.Tensor,
    s1: torch.Tensor,
    mask: torch.Tensor,
    w_adv: float = 0.015,
    w_fm: float = 0.08,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Generator Adversarial Hinge Loss + Multi-Layer Discriminator Feature Matching Loss.
    """
    with torch.no_grad():
        _, real_feats = disc(target, s1, mask)

    fake_logits, fake_feats = disc(pred_direct, s1, mask)
    m_down = F.interpolate(mask.float(), size=fake_logits.shape[-2:], mode="bilinear", align_corners=False)
    w_patch = 0.25 + 0.75 * m_down

    loss_adv = -(fake_logits * w_patch).mean()

    loss_fm = torch.tensor(0.0, device=pred_direct.device)
    for f_fake, f_real in zip(fake_feats, real_feats):
        m_f = F.interpolate(mask.float(), size=f_fake.shape[-2:], mode="bilinear", align_corners=False)
        w_f = 0.3 + 0.7 * m_f
        loss_fm = loss_fm + (torch.abs(f_fake - f_real.detach()) * w_f).mean()
    loss_fm = loss_fm / len(fake_feats)

    total = w_adv * loss_adv + w_fm * loss_fm
    return total, {
        "g_adv": float(loss_adv.item()),
        "g_fm": float(loss_fm.item()),
    }


def compute_scale_decoupled_l1(
    pred_direct: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    projs: Tuple[List[torch.Tensor], List[torch.Tensor]] = None,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Scale-Decoupled L1 Supervision:
      - Outside thick clouds (1 - mask): Full 1x1 pixel-wise L1 preserves exact clear detail.
      - Inside thick clouds (mask): Replaces 80% of 1x1 pixel L1 with 4x4 and 8x8 low-pass
        pooled L1. This enforces exact regional color/reflectance calibration while freeing
        the generator from the double-edge penalty on 1-2px shifted SAR-guided sharp edges!
    """
    p = pred_direct.float()
    t = target.float()
    m = mask.float()

    # 1. Clear / translucent region: exact 1x1 L1
    l1_1x1_clear = (torch.abs(p - t) * (1.0 - 0.80 * m)).mean()

    # 2. Cloudy region: 4x4 and 8x8 low-pass color-preserving L1
    p_4 = F.avg_pool2d(p, kernel_size=4, stride=2, padding=1)
    t_4 = F.avg_pool2d(t, kernel_size=4, stride=2, padding=1)
    m_4 = F.avg_pool2d(m, kernel_size=4, stride=2, padding=1)
    l1_low_4 = (torch.abs(p_4 - t_4) * (1.0 + m_4)).mean()

    p_8 = F.avg_pool2d(p, kernel_size=8, stride=4, padding=2)
    t_8 = F.avg_pool2d(t, kernel_size=8, stride=4, padding=2)
    m_8 = F.avg_pool2d(m, kernel_size=8, stride=4, padding=2)
    l1_low_8 = (torch.abs(p_8 - t_8) * (1.0 + m_8)).mean()

    loss_main = 0.35 * l1_1x1_clear + 0.40 * l1_low_4 + 0.25 * l1_low_8

    # Optional light multi-scale auxiliary head supervision on coarse scales only
    loss_aux = torch.tensor(0.0, device=p.device)
    if projs is not None:
        down_projs, up_projs = projs
        mid_t = t
        for s_idx, (dp, up) in enumerate(zip(down_projs, up_projs[::-1])):
            if s_idx == 0:
                # At full scale (scale 0), use 4x4 pooled L1 so up_proj[2] doesn't force 1x1 blur!
                dp_low = F.avg_pool2d(dp.float(), 4, 2, 1)
                up_low = F.avg_pool2d(up.float(), 4, 2, 1)
                mt_low = F.avg_pool2d(mid_t, 4, 2, 1)
                loss_aux = loss_aux + 0.5 * (torch.abs(dp_low - mt_low).mean() + torch.abs(up_low - mt_low).mean())
            else:
                loss_aux = loss_aux + 0.5 * (torch.abs(dp.float() - mid_t).mean() + torch.abs(up.float() - mid_t).mean())
            mid_t = F.avg_pool2d(mid_t, kernel_size=2, stride=2)
        loss_aux = loss_aux / max(1, len(down_projs))

    total = 0.90 * loss_main + 0.10 * loss_aux
    return total, {
        "l1_decoupled": float(total.item()),
        "l1_low4": float(l1_low_4.item()),
    }
