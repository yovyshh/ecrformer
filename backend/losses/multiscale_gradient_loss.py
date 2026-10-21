"""
Multi-Scale Spatial Gradient Loss for Satellite Image Cloud Removal.

Evaluates spatial gradients across multiple resolution scales (1x, 2x downsampled,
and 4x downsampled) across all Sentinel-2 optical bands.

Why Multi-Scale Spatial Gradient works on multi-date satellite pairs:
  1. Local & Physical: Operates in image space on local terrain boundaries
     (agricultural parcels, ridges, water bodies) rather than global Fourier phases.
  2. Scale-Shift Invariance: At 2x (64x64) and 4x (32x32) scales, a 1-pixel
     multi-temporal registration shift is reduced to 0.5 and 0.25 pixels,
     preventing the objective from penalizing minor seasonal/alignment differences.
  3. No ImageNet or External Weights: Completely native, differentiable PyTorch
     operations that run at maximum speed with zero domain mismatch.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiScaleGradientLoss(nn.Module):
    """
    Computes spatial gradient L1 loss across multiple downsampled scales.

    Args:
        scales (int): Number of multi-scale pyramid levels. Default: 3 (1x, 2x, 4x).
    """

    def __init__(self, scales: int = 3):
        super().__init__()
        self.scales = scales
        self.downsample = nn.AvgPool2d(kernel_size=2, stride=2)

    def _gradient_step(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Compute mean L1 difference of horizontal and vertical gradients."""
        # Horizontal difference along width (axis 3)
        diff_p_x = pred[..., :, 1:] - pred[..., :, :-1]
        diff_t_x = target[..., :, 1:] - target[..., :, :-1]
        l1_x = torch.abs(diff_p_x - diff_t_x).mean()

        # Vertical difference along height (axis 2)
        diff_p_y = pred[..., 1:, :] - pred[..., :-1, :]
        diff_t_y = target[..., 1:, :] - target[..., :-1, :]
        l1_y = torch.abs(diff_p_y - diff_t_y).mean()

        return 0.5 * (l1_x + l1_y)

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred:   [B, C, H, W] prediction (float32)
            target: [B, C, H, W] clear target (float32)

        Returns:
            Scalar multi-scale gradient loss.
        """
        # Ensure float32 for loss computation
        p = pred.float()
        t = target.float()

        total_loss = torch.tensor(0.0, device=pred.device)
        for s in range(self.scales):
            loss_scale = self._gradient_step(p, t)
            total_loss = total_loss + loss_scale
            if s < self.scales - 1:
                p = self.downsample(p)
                t = self.downsample(t)

        return total_loss / float(self.scales)
