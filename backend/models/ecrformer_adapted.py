import torch
import torch.nn as nn
from typing import Tuple, List

from models.ecrformer_model import ECRformerModel

CLEAR_CHANNEL_MEANS = [0.0847, 0.0919, 0.1127, 0.1884] # Sentinel-2 B04, B03, B02, B08

class ECRformerAdaptedModel(nn.Module):
    """
    Adapted ECRformer-Light for Direct Optical Reconstruction:
    4-Band Optical + 2-Band SAR + 1-Band Soft Cloud Mask.

    Inputs:
      - s2_cloudy: Cloudy optical Sentinel-2 (4 channels: B04, B03, B02, B08) in [0, 1]
      - s1: Sentinel-1 SAR (2 channels: VV, VH) in dB
      - mask: Soft cloud mask (1 channel) in [0, 1]
    Total input channels = 2 (SAR) + 5 (Optical + Mask) = 7.

    Architecture:
      - Branch 0 (Radar stem): Conv2d(2, 16, kernel_size=7, padding=3)
      - Branch 1 (Optical + Mask stem): Conv2d(5, 16, kernel_size=7, padding=3)
      - Backbone: ECRformer-Light (4 stages, TSA bottleneck, CBAM)
      - Final conv: Conv2d(64, 4, kernel_size=3, padding=1) predicting absolute reflectance P
      - Auxiliary heads: 3 down_proj heads (4 ch) and 3 up_proj heads (4 ch) for SDFL,
        all predicting multi-scale absolute optical reflectance

    Output:
      - out: Reconstructed Sentinel-2 blended through mask:
             out = (1.0 - mask) * s2_cloudy + mask * pred_direct
             (Clear regions are 100% authentic; cloudy regions receive direct reconstruction P)
      - pred_direct: Raw 4-channel absolute reflectance P predicted by backbone final_conv
      - projs: Tuple of (down_projs, up_projs) for multi-scale SDFL supervision
    """
    def __init__(
        self,
        features_start: int = 32,
        num_blocks: list = [2, 2, 1, 1],
        num_refine: int = 2,
        bottle_neck: str = 'tsa',
        cbam: str = '1ca2+1sa2',
        drop_path_rate: float = 0.0,
        mask_blend: bool = True,
        head_init: str = 'mean_prior'
    ):
        super().__init__()
        self.mask_blend = mask_blend
        self.in_chans = [2, 5] # Branch 0: SAR (2), Branch 1: Optical (4) + Mask (1)
        self.out_chans = 4      # 4 optical output channels (B04, B03, B02, B08)
        self.head_init = head_init

        self.backbone = ECRformerModel(
            in_chans=self.in_chans,
            out_chans=self.out_chans,
            cbam=cbam,
            pos_encoding=None,
            num_layers=4,
            num_blocks=num_blocks,
            bottle_neck=bottle_neck,
            num_refine=num_refine,
            features_start=features_start,
            drop_path_rate=drop_path_rate,
            conv_type='conv',
            norm_type='batch',
            block_type=['ecrformer', 'ecrformer'],
            decoupled_input=True
        )

        if head_init == 'mean_prior':
            prior_t = torch.tensor(CLEAR_CHANNEL_MEANS, dtype=torch.float32)
            with torch.no_grad():
                # Initialize final_conv bias to clear optical terrain mean
                self.backbone.final_conv.bias.copy_(prior_t)
                nn.init.normal_(self.backbone.final_conv.weight, mean=0.0, std=0.005)

                # Initialize multi-scale SDFL auxiliary heads to same prior
                for head in self.backbone.down_proj:
                    head.bias.copy_(prior_t)
                    nn.init.normal_(head.weight, mean=0.0, std=0.005)
                for head in self.backbone.up_proj:
                    head.bias.copy_(prior_t)
                    nn.init.normal_(head.weight, mean=0.0, std=0.005)

    def forward(
        self,
        s2_cloudy: torch.Tensor,
        s1: torch.Tensor,
        mask: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, Tuple[List[torch.Tensor], List[torch.Tensor]]]:
        """
        Forward pass.
        Args:
            s2_cloudy: [B, 4, H, W]
            s1:        [B, 2, H, W]
            mask:      [B, 1, H, W]
        Returns:
            out:         [B, 4, H, W] blended prediction
            pred_direct: [B, 4, H, W] direct absolute optical prediction P
            projs:       (down_projs, up_projs) auxiliary multi-scale projections
        """
        x_in = torch.cat([s1, s2_cloudy, mask], dim=1) # [B, 7, H, W]

        # Backbone direct prediction P
        pred_direct, projs = self.backbone(x_in)

        if self.mask_blend:
            # Direct substitution inside mask:
            # Clear regions (mask=0) strictly preserved from input
            # Cloudy regions (mask=1) receive direct reconstruction P
            out = (1.0 - mask) * s2_cloudy + mask * pred_direct
        else:
            out = pred_direct

        return out, pred_direct, projs
