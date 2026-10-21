import torch
import torch.nn as nn
from typing import Tuple, List, Dict
from util.pytorch_ssim import SSIM

class SDFLLoss(nn.Module):
    """
    Semantic-Decoupled Feature Learning (SDFL) Loss.

    Adapted for 4-band Sentinel-2 cloud removal with soft cloud-mask guidance.

    Loss components:
      1. Encoder Multi-Scale Structural Supervision (down_proj):
         Emphasizes SSIM (structural consistency):
         loss_down_s = w_enc_ssim * (1 - SSIM(down_proj_s, target_s)) + w_enc_l1 * L1(down_proj_s, target_s)
         (Defaults: w_enc_ssim = 0.9, w_enc_l1 = 0.1)

      2. Decoder Multi-Scale Texture Supervision (up_proj):
         Emphasizes L1 (radiometric / texture fidelity):
         loss_up_s = w_dec_l1 * L1(up_proj_s, target_s) + w_dec_ssim * (1 - SSIM(up_proj_s, target_s))
         (Defaults: w_dec_l1 = 0.9, w_dec_ssim = 0.1)

      3. Final Output Composite Loss:
         Area-normalized cloudy-pixel L1 + full-domain structural SSIM:
         loss_main = w_main_l1 * L1_cloudy(pred, target, mask) + w_main_ssim * (1 - SSIM(pred, target))
         (Defaults: w_main_l1 = 0.9, w_main_ssim = 0.1)

      4. Total Multi-Task Loss:
         loss_total = (1 - lambda_enc - lambda_dec) * loss_main + lambda_enc * loss_enc + lambda_dec * loss_dec
         (Defaults: lambda_enc = 0.05, lambda_dec = 0.05)
    """
    def __init__(
        self,
        lambda_enc: float = 0.05,
        lambda_dec: float = 0.05,
        sdfl_mode: str = 'official_repo',
        total_loss_form: str = 'repo_convex',
        w_enc_ssim: float = None,
        w_enc_l1: float = None,
        w_dec_l1: float = None,
        w_dec_ssim: float = None,
        w_main_l1: float = 0.9,
        w_main_ssim: float = 0.1,
        window_size: int = 11,
        full_domain_main: bool = True
    ):
        super().__init__()
        self.lambda_enc = lambda_enc
        self.lambda_dec = lambda_dec
        self.sdfl_mode = sdfl_mode
        self.total_loss_form = total_loss_form
        self.full_domain_main = full_domain_main

        if total_loss_form not in ['repo_convex', 'paper_additive']:
            raise ValueError(f"Unknown total_loss_form: {total_loss_form}. Choose 'repo_convex' or 'paper_additive'.")

        if sdfl_mode == 'paper_strict':
            # Strict paper formulation: 100% SSIM for encoder, 100% L1 for decoder
            self.w_enc_ssim = 1.0 if w_enc_ssim is None else w_enc_ssim
            self.w_enc_l1 = 0.0 if w_enc_l1 is None else w_enc_l1
            self.w_dec_l1 = 1.0 if w_dec_l1 is None else w_dec_l1
            self.w_dec_ssim = 0.0 if w_dec_ssim is None else w_dec_ssim
        elif sdfl_mode == 'official_repo':
            # Official repository author implementation: 90/10 mixed regularization
            self.w_enc_ssim = 0.9 if w_enc_ssim is None else w_enc_ssim
            self.w_enc_l1 = 0.1 if w_enc_l1 is None else w_enc_l1
            self.w_dec_l1 = 0.9 if w_dec_l1 is None else w_dec_l1
            self.w_dec_ssim = 0.1 if w_dec_ssim is None else w_dec_ssim
        else:
            raise ValueError(f"Unknown sdfl_mode: {sdfl_mode}. Choose 'official_repo' or 'paper_strict'.")

        self.w_main_l1 = w_main_l1
        self.w_main_ssim = w_main_ssim

        self.ssim_module = SSIM(window_size=window_size)
        self.downsample = nn.AvgPool2d(kernel_size=2, stride=2)

    def ssim_loss(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Compute 1.0 - SSIM(pred, target)."""
        val = self.ssim_module(pred, target)
        return 1.0 - val

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor,
        projs: Tuple[List[torch.Tensor], List[torch.Tensor]],
        pred_direct: torch.Tensor = None
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Forward computation.
        Args:
            pred:        [B, 4, H, W] final blended prediction Y_hat = (1-M)*S2_c + M*P
            target:      [B, 4, H, W] ground-truth clear Sentinel-2 Y
            mask:        [B, 1, H, W] soft cloud mask M in [0, 1]
            projs:       (down_projs, up_projs)
                         down_projs: [scale0 (H, W), scale1 (H/2, W/2), scale2 (H/4, W/4)]
                         up_projs:   [scale2 (H/4, W/4), scale1 (H/2, W/2), scale0 (H, W)]
            pred_direct: [B, 4, H, W] raw direct optical reflectance prediction P
        Returns:
            loss_total:  scalar Tensor for backprop
            metrics:     dictionary of individual float loss components
        """
        down_projs, up_projs = projs

        # -------------------------------------------------------------
        # 1. Multi-Scale Auxiliary SDFL Supervision
        # -------------------------------------------------------------
        down_loss_sum = torch.tensor(0.0, device=pred.device)
        up_loss_sum = torch.tensor(0.0, device=pred.device)

        mid_target = target
        num_scales = len(down_projs)

        for down_p, up_p in zip(down_projs, up_projs[::-1]):
            # Verify spatial dimensions match
            assert down_p.shape[-2:] == mid_target.shape[-2:], \
                f"down_proj shape {down_p.shape} does not match target shape {mid_target.shape}"
            assert up_p.shape[-2:] == mid_target.shape[-2:], \
                f"up_proj shape {up_p.shape} does not match target shape {mid_target.shape}"

            # Encoder intermediate: Structural SSIM supervision
            loss_down_ssim = self.ssim_loss(down_p, mid_target)
            loss_down_l1 = nn.functional.l1_loss(down_p, mid_target) if self.w_enc_l1 > 0.0 else torch.tensor(0.0, device=pred.device)
            loss_down_scale = self.w_enc_ssim * loss_down_ssim + self.w_enc_l1 * loss_down_l1
            down_loss_sum = down_loss_sum + loss_down_scale

            # Decoder intermediate: Texture-oriented L1 supervision
            loss_up_l1 = nn.functional.l1_loss(up_p, mid_target)
            loss_up_ssim = self.ssim_loss(up_p, mid_target) if self.w_dec_ssim > 0.0 else torch.tensor(0.0, device=pred.device)
            loss_up_scale = self.w_dec_l1 * loss_up_l1 + self.w_dec_ssim * loss_up_ssim
            up_loss_sum = up_loss_sum + loss_up_scale

            # Downsample target for next coarser scale
            mid_target = self.downsample(mid_target)

        loss_enc = down_loss_sum / max(1, num_scales)
        loss_dec = up_loss_sum / max(1, num_scales)

        # -------------------------------------------------------------
        # 2. Final Output Objective
        # -------------------------------------------------------------
        # Area-normalized cloudy L1 loss on blended output (diagnostic metric)
        num_channels = pred.shape[1]
        denom = mask.sum() * num_channels + 1e-8
        loss_l1_cloudy = (torch.abs(pred - target) * mask).sum() / denom

        if self.full_domain_main:
            # Full-domain supervision on raw absolute reflectance P directly against clear target Y:
            # L_main = w_main_l1 * mean_abs(P - Y) + w_main_ssim * (1 - SSIM(P, Y))
            p_target = pred_direct if pred_direct is not None else pred
            loss_l1_main = nn.functional.l1_loss(p_target, target)
            if self.w_main_ssim > 0.0:
                loss_ssim_main = self.ssim_loss(p_target, target)
                loss_main = self.w_main_l1 * loss_l1_main + self.w_main_ssim * loss_ssim_main
            else:
                with torch.no_grad():
                    loss_ssim_main = self.ssim_loss(p_target, target)
                loss_main = self.w_main_l1 * loss_l1_main
        else:
            # Legacy masked supervision on blended output
            if self.w_main_ssim > 0.0:
                loss_ssim_main = self.ssim_loss(pred, target)
                loss_main = self.w_main_l1 * loss_l1_cloudy + self.w_main_ssim * loss_ssim_main
            else:
                with torch.no_grad():
                    loss_ssim_main = self.ssim_loss(pred, target)
                loss_main = self.w_main_l1 * loss_l1_cloudy
            loss_l1_main = loss_l1_cloudy

        # -------------------------------------------------------------
        # 3. Total Multi-Task Loss
        # -------------------------------------------------------------
        if self.total_loss_form == 'repo_convex':
            w_main = max(0.0, 1.0 - self.lambda_enc - self.lambda_dec)
            loss_total = w_main * loss_main + self.lambda_enc * loss_enc + self.lambda_dec * loss_dec
        elif self.total_loss_form == 'paper_additive':
            # Strict paper equation: L_total = L_main + lambda_enc * L_enc + lambda_dec * L_dec (main loss weight = 1.0)
            loss_total = loss_main + self.lambda_enc * loss_enc + self.lambda_dec * loss_dec
        else:
            raise ValueError(f"Unknown total_loss_form: {self.total_loss_form}")

        metrics = {
            "loss_total": loss_total.item(),
            "loss_main": loss_main.item(),
            "loss_l1_main": loss_l1_main.item(),
            "loss_l1_cloudy": loss_l1_cloudy.item(),
            "loss_ssim_main": loss_ssim_main.item(),
            "loss_enc_aux": loss_enc.item(),
            "loss_dec_aux": loss_dec.item(),
        }

        return loss_total, metrics
