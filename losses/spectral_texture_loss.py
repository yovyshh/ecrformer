import torch
import torch.nn as nn
from typing import Tuple, Dict


class SpectralTextureLoss(nn.Module):
    """
    Spectral & Gradient Energy Texture Loss for Cloud Removal.

    Solves the fundamental failure mode of signed finite-difference L1:
    Under temporal date shifts between Sentinel-1 SAR and Sentinel-2 optical,
    signed difference |Dx(P) - Dx(Y)| punishes slightly misaligned sharp edges
    worse than pure flat blur.

    This loss couples:
      1. Shift-Invariant FFT Amplitude Loss: Matches the power spectrum of textures
         without requiring sub-pixel phase/position alignment.
      2. Gradient Magnitude / Energy Loss: Enforces that edge energy ||grad P||
         matches ||grad Y|| rather than collapsing to conditional median 0.
    """

    def __init__(
        self,
        w_fft: float = 1.0,
        w_mag: float = 1.0,
        eps: float = 1e-8,
    ):
        super().__init__()
        self.w_fft = float(w_fft)
        self.w_mag = float(w_mag)
        self.eps = float(eps)

    def forward(
        self, pred: torch.Tensor, target: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Args:
            pred:   [B, 4, H, W] direct network optical prediction
            target: [B, 4, H, W] clear ground truth optical Sentinel-2
        Returns:
            loss: scalar Tensor
            metrics: dict of float values
        """
        # Ensure float32 for FFT and gradient computations
        p = pred.float()
        t = target.float()

        # 1. Shift-Invariant FFT Amplitude Loss
        p_fft = torch.fft.rfft2(p, norm="ortho")
        t_fft = torch.fft.rfft2(t, norm="ortho")
        loss_fft = (torch.abs(p_fft) - torch.abs(t_fft)).abs().mean()

        # 2. Gradient Magnitude (Energy) Loss
        p_dx = p[..., :, 1:] - p[..., :, :-1]
        p_dy = p[..., 1:, :] - p[..., :-1, :]
        t_dx = t[..., :, 1:] - t[..., :, :-1]
        t_dy = t[..., 1:, :] - t[..., :-1, :]

        # Align spatial dimensions for horizontal and vertical finite differences
        mag_p = torch.sqrt(p_dx[..., :-1, :] ** 2 + p_dy[..., :, :-1] ** 2 + self.eps)
        mag_t = torch.sqrt(t_dx[..., :-1, :] ** 2 + t_dy[..., :, :-1] ** 2 + self.eps)
        loss_mag = (mag_p - mag_t).abs().mean()

        total = self.w_fft * loss_fft + self.w_mag * loss_mag

        metrics = {
            "loss_spectral_total": total.item(),
            "loss_fft_amp": loss_fft.item(),
            "loss_grad_mag": loss_mag.item(),
        }
        return total, metrics
