import os, sys, torch, numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
from PIL import Image

sys.path.insert(0, r"C:\Users\Windows 11 Pro\Videos\Projects\ECRformer")
from models.ecrformer_adapted import ECRformerAdaptedModel
from data.cache_dataset import CachedSEN12MSCRDataset

REPO = r"C:\Users\Windows 11 Pro\Videos\Projects\ECRformer"
CACHE = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3"
OUT = os.path.join(REPO, "assets")
BRAIN_ARTIFACTS = r"C:\Users\Windows 11 Pro\.gemini\antigravity\brain\565f98e1-faa5-48e4-bedd-0a52dc32b283"
os.makedirs(OUT, exist_ok=True)

# 1. Load real sample thumbnails
ds = CachedSEN12MSCRDataset(os.path.join(CACHE, "val"), sar_norm="paper_exact", crop_size=None)
sample_idx = 420
c, s1, t, cf, m = ds[sample_idx]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
m_sweet = ECRformerAdaptedModel(
    features_start=32, num_blocks=[2,2,1,1], num_refine=0,
    bottle_neck="tsa", cbam="1ca2+1sa2", mask_blend=True, head_init="mean_prior"
).to(device)
ck = torch.load(os.path.join(REPO, "checkpoints", "ecrformer_sweetspot_best", "best_model.pth"), map_location=device, weights_only=False)
key = "ema_state_dict" if "ema_state_dict" in ck else "model_state_dict"
m_sweet.load_state_dict(ck[key])
m_sweet.eval()

with torch.no_grad():
    p_blended, p_direct, _ = m_sweet(c.unsqueeze(0).to(device), s1.unsqueeze(0).to(device), m.unsqueeze(0).to(device))
    # Compute actual high-pass residual (x - avg_pool5x5(x)) * 10
    opt_f = p_direct.float()
    low = torch.nn.functional.avg_pool2d(torch.nn.functional.pad(opt_f, (2, 2, 2, 2), mode="reflect"), kernel_size=5, stride=1)
    hp_res = (opt_f - low) * 10.0

def to_pil_rgb(tensor, brightness=3.0):
    rgb = tensor[:3].detach().cpu().numpy().transpose(1, 2, 0)
    rgb = np.clip(rgb * brightness * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb)

def to_pil_sar(tensor):
    vv = tensor[0].detach().cpu().numpy()
    vv = np.clip(vv * 255.0, 0, 255).astype(np.uint8)
    radar_rgb = np.stack([np.clip(vv*0.65,0,255), vv, np.clip(vv*0.85,0,255)], axis=-1).astype(np.uint8)
    return Image.fromarray(radar_rgb)

def to_pil_mask(tensor):
    m_np = tensor[0].detach().cpu().numpy()
    m_uint8 = np.clip(m_np * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([m_uint8, m_uint8, m_uint8], axis=-1))

def to_pil_hp(tensor):
    hp = tensor[0, :3].detach().cpu().numpy().transpose(1, 2, 0)
    hp = np.clip((hp * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(hp)

img_cloudy = to_pil_rgb(c)
img_sar = to_pil_sar(s1)
img_mask = to_pil_mask(m)
img_target = to_pil_rgb(t)
img_pred_dir = to_pil_rgb(p_direct[0])
img_pred_blend = to_pil_rgb(p_blended[0])
img_hp = to_pil_hp(hp_res)

# 2. Setup Figure matching the 2-Tier Paper Reference Layout
fig = plt.figure(figsize=(22, 9.5), dpi=300, facecolor="#FFFFFF")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 110)
ax.set_ylim(0, 48)
ax.axis("off")

# Color Palette matching the user's reference figure
COL_STEM   = "#FACC15"  # Warm Yellow (Decoupled Conv 7x7 Stem / Final Conv)
COL_ECR    = "#0D9488"  # Deep Teal (ECRformer Multi-Dilated Block)
COL_CBAM   = "#9CA3AF"  # Cool Grey (CBAM: Channel + Spatial Attention)
COL_SHUF   = "#86EFAC"  # Mint Green (PixelUnshuffle / PixelShuffle)
COL_SKIP   = "#BFDBFE"  # Soft Sky Blue (Skip Concat + 3x3 Fuser)
COL_TSA    = "#15803D"  # Forest Green (TSA Bottleneck: Restormer MDTA + GDFN)
COL_SDFL   = "#F97316"  # Orange (SDFL Multi-Scale Aux Projection Head)
COL_SN     = "#374151"  # Charcoal Dark Slate (GroupNorm / SpectralNorm)

def draw_3d_slab(ax, x, y_center, w, h, dx=0.45, dy=0.42, col="#0D9488", edge_col="#1E293B", lw=0.75, zorder=5):
    """Draws a crisp 3D isometric slab centered vertically at y_center."""
    y = y_center - h / 2.0
    rgb = np.array(plt.matplotlib.colors.to_rgb(col))
    top_col = np.clip(rgb * 1.22 + 0.05, 0, 1)
    side_col = np.clip(rgb * 0.72, 0, 1)

    front = patches.Rectangle((x, y), w, h, facecolor=col, edgecolor=edge_col, linewidth=lw, zorder=zorder)
    top = Polygon([[x, y+h], [x+dx, y+h+dy], [x+w+dx, y+h+dy], [x+w, y+h]],
                  facecolor=top_col, edgecolor=edge_col, linewidth=lw, zorder=zorder+0.1)
    side = Polygon([[x+w, y], [x+w, y+h], [x+w+dx, y+h+dy], [x+w+dx, y+dy]],
                   facecolor=side_col, edgecolor=edge_col, linewidth=lw, zorder=zorder)
    ax.add_patch(front)
    ax.add_patch(top)
    ax.add_patch(side)
    return x + w

def draw_ortho_arrow(ax, pts, col="#111827", lw=1.4, zorder=8, ls="-", arrow=True):
    """Draws clean 90-degree orthogonal polyline with an arrowhead at the final segment."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if len(pts) > 2:
        ax.plot(xs[:-1], ys[:-1], color=col, linewidth=lw, linestyle=ls, solid_capstyle="round", zorder=zorder)
    if arrow:
        arr = FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>,head_length=5,head_width=3",
                              color=col, linewidth=lw, linestyle=ls, zorder=zorder)
        ax.add_patch(arr)
    else:
        ax.plot(xs[-2:], ys[-2:], color=col, linewidth=lw, linestyle=ls, zorder=zorder)

# =========================================================================
# TIER 1 (TOP): ZOOMED-IN 3D LAYER ARCHITECTURE OF GENERATOR G
# =========================================================================
# Outer grey background frame + red dashed inner border (exact style of user's reference)
callout_bg = patches.Rectangle((17.5, 29.0), 62.5, 16.5, facecolor="#F3F4F6", edgecolor="#D1D5DB", linewidth=1.2, zorder=1)
callout_dash = patches.Rectangle((17.8, 29.3), 61.9, 15.9, facecolor="none", edgecolor="#EF4444", linewidth=1.1, linestyle="--", zorder=2)
ax.add_patch(callout_bg)
ax.add_patch(callout_dash)

ax.text(48.75, 44.2, "Detailed 3D Layer Architecture of Generator G (ECRformer-Light: 8.31M Params, Decoupled Stem + 4 Stages)",
        fontsize=9.5, fontweight="bold", color="#111827", ha="center", va="center", zorder=10)

yc = 36.8  # Vertical center of the 3D layer stack

# Build tight sequence of (width, height, color, stage_tag)
# Heights decrease as spatial resolution drops (256 -> 128 -> 64 -> 32) and increase back to 256
slabs = [
    # Decoupled Stem (256x256, C=16+16->32)
    (1.10, 9.8, COL_STEM,  "Decoupled Stem\n(2+5 -> 32)"),
    (0.75, 9.8, COL_SKIP,  None),
    ("gap", 1.95),
    # Stage 1 Encoder (256x256, C=32, 2x ECRformerBlock + CBAM + SDFL + PixelUnshuffle)
    (1.05, 9.5, COL_ECR,   None),
    (1.05, 9.5, COL_ECR,   "Enc 1\n(256², C=32)"),
    (0.75, 9.5, COL_CBAM,  None),
    (0.60, 9.5, COL_SDFL,  None),
    (0.90, 7.2, COL_SHUF,  None),
    ("gap", 1.85),
    # Stage 2 Encoder (128x128, C=64, 2x ECRformerBlock + CBAM + SDFL + PixelUnshuffle)
    (1.25, 7.2, COL_ECR,   None),
    (1.25, 7.2, COL_ECR,   "Enc 2\n(128², C=64)"),
    (0.85, 7.2, COL_CBAM,  None),
    (0.60, 7.2, COL_SDFL,  None),
    (1.00, 5.2, COL_SHUF,  None),
    ("gap", 1.85),
    # Stage 3 Encoder (64x64, C=128, 1x ECRformerBlock + CBAM + SDFL + PixelUnshuffle)
    (1.55, 5.2, COL_ECR,   "Enc 3\n(64², C=128)"),
    (0.95, 5.2, COL_CBAM,  None),
    (0.65, 5.2, COL_SDFL,  None),
    (1.10, 3.5, COL_SHUF,  None),
    ("gap", 2.00),
    # Stage 4 Bottleneck: TSA RestormerBlock (32x32, C=256, MDTA + GDFN)
    (0.85, 3.4, COL_CBAM,  None),
    (2.80, 3.4, COL_TSA,   "TSA Bottleneck\nRestormer (32², C=256)"),
    (2.80, 3.4, COL_TSA,   None),
    (0.85, 3.4, COL_CBAM,  None),
    ("gap", 2.00),
    # Stage 3 Decoder (64x64, C=128: PixelShuffle + Skip Fuser + 1x ECRformerBlock + CBAM + SDFL)
    (1.10, 5.2, COL_SHUF,  None),
    (0.95, 5.2, COL_SKIP,  "Up 3"),
    (1.55, 5.2, COL_ECR,   "Dec 3\n(64², C=128)"),
    (0.95, 5.2, COL_CBAM,  None),
    (0.65, 5.2, COL_SDFL,  None),
    ("gap", 1.85),
    # Stage 2 Decoder (128x128, C=64: PixelShuffle + Skip Fuser + 2x ECRformerBlock + CBAM + SDFL)
    (1.00, 7.2, COL_SHUF,  None),
    (0.85, 7.2, COL_SKIP,  "Up 2"),
    (1.25, 7.2, COL_ECR,   "Dec 2\n(128², C=64)"),
    (1.25, 7.2, COL_ECR,   None),
    (0.85, 7.2, COL_CBAM,  None),
    (0.60, 7.2, COL_SDFL,  None),
    ("gap", 1.85),
    # Stage 1 Decoder (256x256, C=64: PixelShuffle + Identity Concat + 2x ECRformerBlock + CBAM + SDFL)
    (0.90, 9.5, COL_SHUF,  None),
    (0.80, 9.5, COL_SKIP,  "Up 1"),
    (1.10, 9.5, COL_ECR,   "Dec 1\n(256², C=64)"),
    (1.10, 9.5, COL_ECR,   None),
    (0.75, 9.5, COL_CBAM,  None),
    (0.60, 9.5, COL_SDFL,  None),
    ("gap", 1.75),
    # Final Conv (256x256, 64 -> 4)
    (1.15, 9.8, COL_STEM,  "Final Conv\n(64 -> 4)"),
]

curr_x = 19.3
z_base = 5
stage_centers = {}
for item in slabs:
    if item[0] == "gap":
        curr_x += item[1]
        continue
    w, h, col, lbl = item
    draw_3d_slab(ax, curr_x, yc, w, h, dx=0.42, dy=0.38, col=col, zorder=z_base)
    if lbl:
        key_name = lbl.split("\n")[0]
        stage_centers[key_name] = (curr_x + w / 2.0, yc + h / 2.0 + 0.45)
        if not key_name.startswith("Up "):
            ax.text(curr_x + w / 2.0 + 0.3, yc - h / 2.0 - 0.85, lbl,
                    fontsize=6.8, fontweight="bold", color="#1F2937", ha="center", va="top", zorder=15)
    curr_x += w + 0.08
    z_base += 0.2

# Draw skip connection arcs neatly inside the top of the callout box
skip_pairs = [
    ("Decoupled Stem", "Up 1", 42.6, "Skip 0 (C=32, Identity Concat)"),
    ("Enc 1",          "Up 2", 41.7, "Skip 1 (C=64, 3x3 Fuser)"),
    ("Enc 2",          "Up 3", 40.8, "Skip 2 (C=128, 3x3 Fuser)"),
]
for s_from, s_to, y_arc, s_lbl in skip_pairs:
    if s_from in stage_centers and s_to in stage_centers:
        x1, y1 = stage_centers[s_from]
        x2, y2 = stage_centers[s_to]
        draw_ortho_arrow(ax, [(x1, y1), (x1, y_arc), (x2, y_arc), (x2, y2)],
                         col="#64748B", lw=1.0, ls="--", zorder=12)

ax.text(48.75, 43.0, "Skip Connections (Multi-Scale Feature Concatenation + 3x3 Conv Fuser)",
        fontsize=7.2, fontstyle="italic", color="#475569", ha="center", zorder=12)

# =========================================================================
# TIER 2 (MIDDLE): MACRO PIPELINE FLOW (LEFT -> G -> BLEND -> D)
# =========================================================================

# -------------------------------------------------------------------------
# 2A. Left Box: Decoupled Multimodal Input & Stem
# -------------------------------------------------------------------------
box_in = patches.Rectangle((1.5, 11.5), 25.5, 13.5, facecolor="#DCFCE7", edgecolor="#EF4444",
                           linewidth=1.1, linestyle="--", zorder=1)
ax.add_patch(box_in)
ax.text(14.25, 24.1, "1. Decoupled Multimodal Input & Stem", fontsize=9.0, fontweight="bold", color="#14532D", ha="center")

# Input thumbnails (stacked neatly on left)
ax.imshow(img_cloudy, extent=[2.4, 6.6, 19.3, 23.3], zorder=5)
ax.add_patch(patches.Rectangle((2.4, 19.3), 4.2, 4.0, facecolor="none", edgecolor="#1E293B", lw=1.0, zorder=6))
ax.text(4.5, 18.6, r"Cloudy $\mathbf{X}_{S2}$ (4ch)", fontsize=7.0, fontweight="bold", ha="center", color="#111827")

ax.imshow(img_mask, extent=[7.4, 11.6, 19.3, 23.3], zorder=5)
ax.add_patch(patches.Rectangle((7.4, 19.3), 4.2, 4.0, facecolor="none", edgecolor="#1E293B", lw=1.0, zorder=6))
ax.text(9.5, 18.6, r"Mask $\mathbf{M}$ (1ch)", fontsize=7.0, fontweight="bold", ha="center", color="#111827")

ax.imshow(img_sar, extent=[4.9, 9.1, 13.0, 17.0], zorder=5)
ax.add_patch(patches.Rectangle((4.9, 13.0), 4.2, 4.0, facecolor="none", edgecolor="#1E293B", lw=1.0, zorder=6))
ax.text(7.0, 12.2, r"SAR $\mathbf{X}_{S1}$ (2ch: VV,VH)", fontsize=7.0, fontweight="bold", ha="center", color="#111827")

# Stacked Stem cards (just like "Forward diffusion" stacked rectangles in reference)
for offset in [0.4, 0.2, 0.0]:
    ax.add_patch(patches.Rectangle((14.2+offset, 18.8+offset), 6.2, 3.6, facecolor="#E2F2D5", edgecolor="#1E293B", lw=0.9, zorder=4))
    ax.add_patch(patches.Rectangle((14.2+offset, 13.2+offset), 6.2, 3.6, facecolor="#E2F2D5", edgecolor="#1E293B", lw=0.9, zorder=4))

ax.text(17.3, 20.6, "Optical+Mask\nStem (5->16)\n7x7 Conv+BN", fontsize=7.0, fontweight="bold", ha="center", va="center", color="#14532D", zorder=6)
ax.text(17.3, 15.0, "SAR Radar\nStem (2->16)\n7x7 Conv+BN", fontsize=7.0, fontweight="bold", ha="center", va="center", color="#14532D", zorder=6)

draw_ortho_arrow(ax, [(11.6, 21.0), (14.2, 21.0)], lw=1.3)
draw_ortho_arrow(ax, [(9.1, 15.0), (14.2, 15.0)], lw=1.3)

# Stem Fusion Node
ax.add_patch(patches.Circle((23.8, 17.8), 1.2, facecolor="#FEF08A", edgecolor="#1E293B", lw=1.2, zorder=6))
ax.text(23.8, 17.8, "Concat\n32 ch", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=7)
draw_ortho_arrow(ax, [(20.8, 20.6), (23.8, 20.6), (23.8, 19.0)], lw=1.2)
draw_ortho_arrow(ax, [(20.8, 15.0), (23.8, 15.0), (23.8, 16.6)], lw=1.2)

# -------------------------------------------------------------------------
# 2B. Center: Generator G Bowtie Polygon + Zoom Lines + SDFL Pill
# -------------------------------------------------------------------------
g_poly = Polygon([
    [30.0, 24.5],
    [39.0, 21.2],
    [48.0, 24.5],
    [48.0, 12.5],
    [39.0, 15.8],
    [30.0, 12.5]
], facecolor="#93C5FD", edgecolor="#2563EB", linewidth=1.5, zorder=4)
ax.add_patch(g_poly)
ax.text(39.0, 19.2, r"$\mathbf{G}(\mathbf{X}_{S2}, \mathbf{X}_{S1}, \mathbf{M})$", fontsize=10.5, fontweight="bold", color="#1E3A8A", ha="center", va="center", zorder=6)
ax.text(39.0, 17.5, "ECRformer-Light\n(4 Stages + TSA)", fontsize=7.8, color="#1E40AF", ha="center", va="center", zorder=6)

# Dashed Zoom-Out Lines connecting G Bowtie to Top Callout Box (exact match to reference!)
ax.plot([30.0, 17.8], [24.5, 29.3], color="#4B5563", linewidth=1.3, linestyle="--", zorder=3)
ax.plot([48.0, 79.7], [24.5, 29.3], color="#4B5563", linewidth=1.3, linestyle="--", zorder=3)

# Arrow from Stem Concat into G
draw_ortho_arrow(ax, [(25.0, 17.8), (30.0, 17.8)], lw=1.6)

# Below G: Multi-Scale SDFL + Scale-Decoupled L1 Pill (matching "Time Embedding" pill in reference)
pill_sdfl = FancyBboxPatch((30.2, 7.6), 17.6, 3.2, boxstyle="round,pad=0.3,rounding_size=1.2",
                           facecolor="#FEF9C3", edgecolor="#CA8A04", linewidth=1.2, zorder=4)
ax.add_patch(pill_sdfl)
for cx in [32.4, 35.4, 38.4]:
    ax.add_patch(patches.Circle((cx, 9.2), 1.0, facecolor="#FFFBEB", edgecolor="#78350F", lw=1.0, zorder=5))
ax.text(32.4, 9.2, "1/2", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=6)
ax.text(35.4, 9.2, "1/4", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=6)
ax.text(38.4, 9.2, "1/8", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=6)
ax.text(43.8, 9.2, "SDFL Aux &\n4x4/8x8 Pool L1", fontsize=7.0, fontweight="bold", color="#78350F", ha="center", va="center", zorder=6)
ax.text(39.0, 6.4, r"Scale-Decoupled Supervision ($\mathcal{L}_{L1}^{dec} + \mathcal{L}_{Sobel}$)", fontsize=7.8, fontweight="bold", color="#1F2937", ha="center")

draw_ortho_arrow(ax, [(39.0, 15.8), (39.0, 11.1)], lw=1.3, col="#B45309")

# -------------------------------------------------------------------------
# 2C. Right-Center Box: Direct Prediction -> Mask Blending & High-Pass Residual
# -------------------------------------------------------------------------
box_post = patches.Rectangle((51.5, 11.5), 32.0, 13.5, facecolor="#ECFDF5", edgecolor="#EF4444",
                             linewidth=1.1, linestyle="--", zorder=1)
ax.add_patch(box_post)
ax.text(67.5, 24.1, "2. Mask-Guided Blending & High-Pass Detail Extraction", fontsize=9.0, fontweight="bold", color="#065F46", ha="center")

# Direct output P_dir thumbnail
ax.imshow(img_pred_dir, extent=[53.0, 58.0, 15.3, 20.3], zorder=5)
ax.add_patch(patches.Rectangle((53.0, 15.3), 5.0, 5.0, facecolor="none", edgecolor="#1E293B", lw=1.1, zorder=6))
ax.text(55.5, 14.1, r"Direct $\mathbf{P}_{dir}$", fontsize=7.5, fontweight="bold", ha="center", color="#111827")

draw_ortho_arrow(ax, [(48.0, 17.8), (53.0, 17.8)], lw=1.6)

# Stacked Mask-Blend Operation Cards (matching "Posterior sampling" cards in reference)
for offset in [0.4, 0.2, 0.0]:
    ax.add_patch(patches.Rectangle((61.0+offset, 15.0+offset), 8.2, 5.2, facecolor="#E2F2D5", edgecolor="#1E293B", lw=0.9, zorder=4))
ax.text(65.1, 18.5, "Mask Blending &\n5x5 High-Pass", fontsize=7.5, fontweight="bold", color="#14532D", ha="center", va="center", zorder=6)
ax.text(65.1, 16.2, r"$\hat{\mathbf{Y}}=(1-\mathbf{M})\mathbf{X}_{S2}+\mathbf{M}\mathbf{P}_{dir}$", fontsize=6.6, color="#1E293B", ha="center", va="center", zorder=6)

draw_ortho_arrow(ax, [(58.0, 17.8), (61.0, 17.8)], lw=1.4)

# Blended Final Output & High-Pass Residual thumbnails
ax.imshow(img_pred_blend, extent=[72.2, 76.8, 18.2, 22.8], zorder=5)
ax.add_patch(patches.Rectangle((72.2, 18.2), 4.6, 4.6, facecolor="none", edgecolor="#059669", lw=1.3, zorder=6))
ax.text(74.5, 17.3, r"Blended $\hat{\mathbf{Y}}$ (4ch)", fontsize=7.0, fontweight="bold", ha="center", color="#065F46")

ax.imshow(img_hp, extent=[77.8, 82.4, 18.2, 22.8], zorder=5)
ax.add_patch(patches.Rectangle((77.8, 18.2), 4.6, 4.6, facecolor="none", edgecolor="#D97706", lw=1.3, zorder=6))
ax.text(80.1, 17.3, r"High-Pass $\mathbf{R}_{HP}$ (4ch)", fontsize=7.0, fontweight="bold", ha="center", color="#B45309")

draw_ortho_arrow(ax, [(69.6, 19.2), (72.2, 19.2)], lw=1.3)

# Clear Ground Truth Reference Pill above Discriminator
pill_gt = FancyBboxPatch((82.5, 29.0), 14.0, 6.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                         facecolor="#FEF9C3", edgecolor="#CA8A04", linewidth=1.2, zorder=4)
ax.add_patch(pill_gt)
ax.imshow(img_target, extent=[83.4, 88.0, 29.8, 34.4], zorder=6)
ax.add_patch(patches.Rectangle((83.4, 29.8), 4.6, 4.6, facecolor="none", edgecolor="#059669", lw=1.2, zorder=7))
ax.text(92.4, 32.8, "Clear Target S2\n" + r"$\mathbf{Y}_{real} \in \mathbb{R}^{4\times H\times W}$", fontsize=7.2, fontweight="bold", color="#14532D", ha="center", va="center", zorder=6)
ax.text(92.4, 30.6, "+ High-Pass\nResidual (4ch)", fontsize=6.8, color="#78350F", ha="center", va="center", zorder=6)

# -------------------------------------------------------------------------
# 2D. Far Right: Trapezoidal Conditional PatchGAN Discriminator D
# -------------------------------------------------------------------------
# Trapezoid matching the exact shape on the right of user's reference image!
disc_trap = Polygon([
    [90.5, 25.0],
    [105.5, 22.0],
    [105.5, 13.6],
    [90.5, 10.6]
], facecolor="#FFEDD5", edgecolor="#EF4444", linewidth=1.2, linestyle="--", zorder=2)
ax.add_patch(disc_trap)

# Tightly stacked 3D slabs inside Discriminator D (4 SN-Conv layers + 1x16x16 Head)
d_slabs = [
    # Layer 1: SN-Conv 4x4 (11 -> 64, s=2)
    (91.5, 0.90, 9.2, COL_ECR,  "L1\n64"),
    (92.5, 0.45, 9.2, COL_SN,   None),
    # Layer 2: SN-Conv 4x4 (64 -> 128, s=2) + GroupNorm(8)
    (94.1, 1.00, 7.4, COL_ECR,  "L2\n128"),
    (95.2, 0.50, 7.4, COL_SN,   None),
    # Layer 3: SN-Conv 4x4 (128 -> 256, s=2) + GroupNorm(16)
    (96.8, 1.15, 5.8, COL_ECR,  "L3\n256"),
    (98.0, 0.50, 5.8, COL_SN,   None),
    # Layer 4: SN-Conv 3x3 (256 -> 256, s=1) + GroupNorm(16)
    (99.6, 1.15, 4.6, COL_ECR,  "L4\n256"),
    (100.8, 0.50, 4.6, COL_SN,  None),
    # Head: SN-Conv 3x3 (256 -> 1, s=1) -> 16x16 Patch Map
    (102.5, 0.85, 3.4, COL_STEM, "16²\nMap"),
]
for dx_pos, dw, dh, dcol, dlbl in d_slabs:
    draw_3d_slab(ax, dx_pos, 17.8, dw, dh, dx=0.35, dy=0.32, col=dcol, zorder=6)
    if dlbl:
        ax.text(dx_pos + dw/2.0 + 0.1, 17.8 - dh/2.0 - 0.85, dlbl,
                fontsize=6.2, fontweight="bold", color="#1F2937", ha="center", va="top", zorder=10)

ax.text(98.0, 8.8, r"$\mathbf{D}(\mathbf{Y}_{opt}, \mathbf{R}_{HP}, \mathbf{X}_{S1}, \mathbf{M})$",
        fontsize=9.2, fontweight="bold", color="#9A3412", ha="center")
ax.text(98.0, 7.2, r"11-Ch Spectral-Norm PatchGAN ($\mathcal{L}_{adv} + \mathcal{L}_{FM}$)",
        fontsize=7.5, color="#C2410C", ha="center")

# Curly brace & Vertical "Real / Fake?" on far right (exact match to reference!)
ax.text(106.3, 17.8, "}", fontsize=34, fontweight="light", color="#374151", ha="center", va="center", zorder=10)
ax.text(108.3, 17.8, "Real / Fake?\n(Mask-Weighted Hinge)", fontsize=8.0, fontweight="bold", color="#111827",
        ha="center", va="center", rotation=90, zorder=10)

# Orthogonal routing arrows into Discriminator D (Zero text overlap!)
# 1. From Post-Processing (Fake Optical + High-Pass) into D
draw_ortho_arrow(ax, [(83.5, 19.2), (90.5, 19.2)], lw=1.5, col="#111827")
# 2. From Real Target Pill into D
draw_ortho_arrow(ax, [(89.5, 29.0), (89.5, 20.6), (90.5, 20.6)], lw=1.4, col="#059669")
# 3. Clean Bottom Orthogonal Bus Lines from SAR X_S1 and Mask M into Blending & D (just like reference!)
# Mask M bus line -> Blending & D
draw_ortho_arrow(ax, [(9.5, 11.5), (9.5, 4.8), (65.1, 4.8), (65.1, 15.0)], lw=1.2, col="#374151")
draw_ortho_arrow(ax, [(65.1, 4.8), (88.2, 4.8), (88.2, 16.4), (90.5, 16.4)], lw=1.2, col="#374151")
ax.text(52.0, 5.2, r"Conditioning Bus: Cloud Mask $\mathbf{M}$ (1ch) & Sentinel-1 SAR $\mathbf{X}_{S1}$ (2ch)",
        fontsize=7.2, fontweight="bold", color="#374151", ha="center")

# SAR X_S1 bus line -> D
draw_ortho_arrow(ax, [(7.0, 11.5), (7.0, 3.8), (89.2, 3.8), (89.2, 15.0), (90.5, 15.0)], lw=1.2, col="#0D9488")

# =========================================================================
# TIER 3 (BOTTOM): 3D ISOMETRIC CUBE LEGEND BAR
# =========================================================================
legend_items = [
    (COL_STEM, "7x7 Stem / 3x3 Head"),
    (COL_ECR,  "ECRformer / SN-Conv"),
    (COL_CBAM, "CBAM (CA + SA)"),
    (COL_SHUF, "PixelUnshuffle / Shuffle"),
    (COL_SKIP, "Skip Concat + Fuser"),
    (COL_TSA,  "TSA Restormer (MDTA+GDFN)"),
    (COL_SDFL, "SDFL Multi-Scale Head"),
    (COL_SN,   "GroupNorm + LeakyReLU"),
]

start_lx = 9.0
spacing_lx = 11.8
for i, (lcol, ltext) in enumerate(legend_items):
    lx = start_lx + i * spacing_lx
    draw_3d_slab(ax, lx, 1.6, 1.1, 1.3, dx=0.35, dy=0.30, col=lcol, zorder=10)
    ax.text(lx + 1.75, 1.6, ltext, fontsize=7.5, fontweight="bold", color="#1F2937", va="center", ha="left", zorder=10)

out_fig = os.path.join(OUT, "paper_pipeline_architecture.png")
plt.savefig(out_fig, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.close(fig)

artifact_path = os.path.join(BRAIN_ARTIFACTS, "paper_pipeline_architecture.png")
im_saved = Image.open(out_fig)
im_saved.save(artifact_path)

print(f"Successfully generated v2 paper pipeline figure: {out_fig}")
print(f"Saved artifact copy: {artifact_path}")
