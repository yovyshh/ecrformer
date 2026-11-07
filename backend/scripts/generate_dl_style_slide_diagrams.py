import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

OUT_DIR = r"c:\Users\Windows 11 Pro\Videos\Projects\ECRformer\backend\assets\ppt_diagrams"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Segoe UI", "Calibri", "Arial"]
plt.rcParams["mathtext.fontset"] = "dejavusans"


def draw_box(ax, x, y, w, h, text="", title="", facecolor="#F8FAFC", edgecolor="#64748B",
             title_color="#1E293B", text_color="#334155", fontsize=10, title_fontsize=11,
             lw=1.5, radius=0.02, align="center", title_top_only=False):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.005,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, zorder=2
    )
    ax.add_patch(box)
    n_title_lines = title.count("\n") + 1 if title else 0
    text_offset = 0.028 + 0.036 * n_title_lines
    if title and (text or title_top_only):
        ax.text(
            x + (w / 2 if align == "center" else 0.015),
            y + h - 0.022,
            title,
            ha=align, va="top", fontsize=title_fontsize, fontweight="bold",
            color=title_color, zorder=3, linespacing=1.25
        )
        if text:
            ax.text(
                x + (w / 2 if align == "center" else 0.015),
                y + h - text_offset,
                text,
                ha=align, va="top", fontsize=fontsize,
                color=text_color, zorder=3, linespacing=1.32
            )
    elif title:
        ax.text(
            x + w / 2, y + h / 2, title,
            ha="center", va="center", fontsize=title_fontsize, fontweight="bold",
            color=title_color, zorder=3
        )
    elif text:
        ax.text(
            x + (w / 2 if align == "center" else 0.015),
            y + h / 2,
            text,
            ha=align, va="center", fontsize=fontsize,
            color=text_color, zorder=3, linespacing=1.32
        )


def arrow(ax, x1, y1, x2, y2, color="#334155", lw=1.8, style="->"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0),
        zorder=5
    )


# ==============================================================================
# FIGURE 1: SAR VS OPTICAL PHYSICS (WHY 2 SATELLITES?)
# ==============================================================================
def make_fig1_physics():
    fig, ax = plt.subplots(figsize=(12, 5.6), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Left panel: Sentinel-2 Optical
    draw_box(ax, 0.02, 0.06, 0.46, 0.88, facecolor="#FFFDF9", edgecolor="#D97706", lw=2.0, radius=0.02)
    ax.text(0.25, 0.90, "Satellite #1: Sentinel-2 (Optical Camera)", ha="center", va="top",
            fontsize=13, fontweight="bold", color="#991B1B", zorder=3)
    ax.text(0.25, 0.84, "Passive Sensor: Needs Sunlight  |  Wavelength: 490–842 nm (Tiny)",
            ha="center", va="top", fontsize=9.2, color="#475569", fontweight="bold", zorder=3)

    # Sun + Satellite
    draw_box(ax, 0.05, 0.67, 0.18, 0.11, title="Sunlight", text="Visible + NIR\n(B04, B03, B02, B08)",
             facecolor="#FEF3C7", edgecolor="#F59E0B", title_color="#B45309", fontsize=8.3, title_fontsize=9.8)
    draw_box(ax, 0.27, 0.67, 0.18, 0.11, title="Sentinel-2", text="4-Band Optical\n[4, 256, 256]",
             facecolor="#EFF6FF", edgecolor="#2563EB", title_color="#1D4ED8", fontsize=8.3, title_fontsize=9.8)

    # Cloud Barrier
    draw_box(ax, 0.06, 0.39, 0.38, 0.16, title="THICK CLOUD COVER (Water Droplets ~10 μm)",
             text="Optical wavelength (0.5 μm) << Droplet size (10 μm)\n100% Mie Scattering: Sunlight bounces back as a WHITE BLOB!",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.4, title_fontsize=9.6)

    arrow(ax, 0.14, 0.67, 0.20, 0.55, color="#D97706", lw=2.2)
    arrow(ax, 0.28, 0.55, 0.35, 0.67, color="#DC2626", lw=2.2)
    ax.text(0.245, 0.60, "Blocked & Scattered!", ha="center", fontsize=8.8, fontweight="bold", color="#DC2626", zorder=4)

    # Ground below cloud
    draw_box(ax, 0.05, 0.10, 0.40, 0.19, title="Ground Terrain Underneath (10 m/pixel)",
             text="✔ Rich natural colors (Green forests, Red roofs, Blue water)\n✘ COMPLETELY HIDDEN whenever clouds roll in (>50% of Earth)",
             facecolor="#F1F5F9", edgecolor="#94A3B8", title_color="#334155", fontsize=8.4, title_fontsize=9.8)
    ax.text(0.25, 0.33, "✘ Optical Cannot Reach Ground", ha="center", fontsize=9.5, fontweight="bold", color="#991B1B", zorder=4)

    # Right panel: Sentinel-1 SAR Radar
    draw_box(ax, 0.52, 0.06, 0.46, 0.88, facecolor="#F8FAFC", edgecolor="#059669", lw=2.0, radius=0.02)
    ax.text(0.75, 0.90, "Satellite #2: Sentinel-1 (C-Band SAR Radar)", ha="center", va="top",
            fontsize=13, fontweight="bold", color="#065F46", zorder=3)
    ax.text(0.75, 0.84, "Active Sensor: Shoots Own Microwaves  |  Wavelength: ~5.5 cm (Huge!)",
            ha="center", va="top", fontsize=9.2, color="#475569", fontweight="bold", zorder=3)

    draw_box(ax, 0.56, 0.67, 0.38, 0.11, title="Sentinel-1 SAR Transceiver",
             text="Sends Vertical (V) Microwave Pulse  |  2 Channels: VV & VH in dB",
             facecolor="#ECFDF5", edgecolor="#059669", title_color="#065F46", fontsize=8.3, title_fontsize=9.8)

    # Cloud passed through
    draw_box(ax, 0.55, 0.42, 0.40, 0.12, title="Cloud Layer (Invisible to 5.5 cm Radar Waves!)",
             text="5.5 cm wave is 5,500× larger than droplets → Passes straight through!",
             facecolor="#E0F2FE", edgecolor="#0284C7", title_color="#0369A1", fontsize=8.2, title_fontsize=9.4)

    arrow(ax, 0.65, 0.67, 0.65, 0.32, color="#059669", lw=2.4)
    arrow(ax, 0.85, 0.32, 0.85, 0.67, color="#0284C7", lw=2.4)

    # VV and VH boxes at bottom
    draw_box(ax, 0.54, 0.10, 0.20, 0.21, title="Channel 1: VV [-25, 0 dB]",
             text="Vertical → Vertical\nSurface Roughness:\n• Calm Water: Dark (-22 dB)\n• Buildings: Bright (-3 dB)",
             facecolor="#DCFCE7", edgecolor="#16A34A", title_color="#166534", fontsize=8.0, title_fontsize=9.2)
    draw_box(ax, 0.76, 0.10, 0.20, 0.21, title="Channel 2: VH [-35, 0 dB]",
             text="Vertical → Horizontal\n3D Volume Scattering:\n• Tree canopies & crops twist\n  the wave horizontally!",
             facecolor="#FEF9C3", edgecolor="#CA8A04", title_color="#854D0E", fontsize=8.0, title_fontsize=9.2)

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig1_sar_vs_optical_physics.png"), dpi=240)
    plt.close()


# ==============================================================================
# FIGURE 2: PREPROCESSING & S2CLOUDLESS + ROLE M1 (VAE-ENCODER STYLE)
# ==============================================================================
def make_fig2_preprocessing():
    fig, ax = plt.subplots(figsize=(12, 5.6), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.03, 0.76, 0.56, 0.18,
             title="Raw Cached Sample: ROIs1970_fall_s2_*.npz (32-bit Float Arrays)",
             text="• s2_cloudy: [4, 256, 256] in [0.0, 1.0] (B04 Red, B03 Green, B02 Blue, B08 NIR)\n"
                  "• s1 (SAR):  [2, 256, 256] in dB (VV ∈ [-25, 0], VH ∈ [-35, 0])\n"
                  "• s2_clear:  [4, 256, 256] in [0.0, 1.0] (Co-registered Cloud-Free Target Y)",
             facecolor="#EFF6FF", edgecolor="#2563EB", title_color="#1D4ED8", fontsize=8.6, title_fontsize=10.0, align="left")

    draw_box(ax, 0.03, 0.52, 0.27, 0.17,
             title="ESA s2cloudless + 3-Step Refine",
             text="13-band Cirrus (B10) + SWIR\n9×9 Mean > 0.5 → 5×5 Dilate\n→ 11×11 Gauss Blur = Soft M",
             facecolor="#FEF3C7", edgecolor="#D97706", title_color="#92400E", fontsize=8.4, title_fontsize=9.4)

    draw_box(ax, 0.32, 0.52, 0.27, 0.17,
             title="SAR paper_exact Norm",
             text="VV_norm = (clamp(VV,-25,0)+25)/25\nVH_norm = (clamp(VH,-35,0)+35)/35\nMaps negative dB → [0.0, 1.0]",
             facecolor="#ECFDF5", edgecolor="#059669", title_color="#065F46", fontsize=8.4, title_fontsize=9.4)

    arrow(ax, 0.16, 0.76, 0.16, 0.69, color="#2563EB")
    arrow(ax, 0.45, 0.76, 0.45, 0.69, color="#059669")

    draw_box(ax, 0.03, 0.28, 0.56, 0.17,
             title="Role M1: Opaque Cloud Cutout (Anti-Cheating Augmentation, prob = 0.65)",
             text="In thin haze, optical ground edges leak through (corr > 0.80), so AI cheats & ignores SAR!\n"
                  "Fix: Replace cloudy pixels with two passes of 15×15 AvgPool (~29×29 featureless veil)\n"
                  "s2_aug = (1 - α)·s2_cloudy + α·Veil   →   Forces Generator to extract geometry from SAR!",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.4, title_fontsize=9.6, align="left")

    arrow(ax, 0.16, 0.52, 0.16, 0.45, color="#D97706")
    arrow(ax, 0.45, 0.52, 0.45, 0.45, color="#059669")

    draw_box(ax, 0.03, 0.05, 0.56, 0.16,
             title="Final Model Input Tensor X_in = [S1, S2_aug, M]",
             text="• Phase 1 (Training): Same random 128×128 crop window across all tensors → [B, 7, 128, 128]\n"
                  "• Phase 2 (Testing):  Full native resolution with Cutout OFF → [B, 7, 256, 256]",
             facecolor="#F0FDF4", edgecolor="#16A34A", title_color="#166534", fontsize=8.6, title_fontsize=9.8, align="left")

    arrow(ax, 0.31, 0.28, 0.31, 0.21, color="#16A34A")

    steps = [
        ("Step 1: Why .npz Instead of .jpg?",
         "Normal JPEGs hold only 3 bands (0–255 integers).\nWe have 6 sensor bands (including NIR & negative\nradar dB) needing exact 32-bit float precision."),
        ("Step 2: Snow vs. Cloud Trap",
         "White snow & concrete roofs look bright in RGB!\ns2cloudless checks Cirrus Band 10 (1375 nm)\nwhere water vapor absorbs ground light completely."),
        ("Step 3: Stopping Optical Shortcut",
         "Without Cutout, the network boosts thin haze\ncontrast and ignores SAR. Blinding 65% of clouds\nwith a 29×29 veil forces true SAR fusion."),
        ("Step 4: Strict Split Integrity",
         "Train: 33,468 patches  |  Val: 1,115 patches\nHeld-out test tile s2_139 is NEVER touched\nduring training or hyperparameter tuning.")
    ]
    y_positions = [0.76, 0.52, 0.28, 0.05]
    for (stitle, stext), ypos in zip(steps, y_positions):
        draw_box(ax, 0.63, ypos, 0.34, 0.18 if ypos == 0.76 else 0.17,
                 title=stitle, text=stext,
                 facecolor="#F4F4F0", edgecolor="#A8A29E",
                 title_color="#1E293B", text_color="#44403C",
                 fontsize=8.3, title_fontsize=9.4, align="left")

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig2_npz_and_s2cloudless.png"), dpi=240)
    plt.close()


# ==============================================================================
# FIGURE 3: ECRFORMER STEP-BY-STEP ARCHITECTURE (DL TEACHING STYLE)
# ==============================================================================
def make_fig3_ecrformer():
    fig, ax = plt.subplots(figsize=(12, 5.6), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Top row boxes (taller: y=0.64, h=0.27)
    draw_box(ax, 0.02, 0.64, 0.22, 0.27,
             title="1. Decoupled Stem",
             text="Branch 0 (SAR 2ch):\nConv7×7(2 → 16)\n\nBranch 1 (Opt 4ch + M 1ch):\nConv7×7(5 → 16) [Role M2]\nConcat → 32 Channels",
             facecolor="#EFF6FF", edgecolor="#2563EB", title_color="#1D4ED8", fontsize=8.1, title_fontsize=9.8)

    draw_box(ax, 0.27, 0.64, 0.22, 0.27,
             title="2. 4-Stage Encoder",
             text="num_blocks = [2, 2, 1, 1]\nPixelUnshuffle (2×2 → 4×Ch)\n• Stage 1: 32 ch  (H × W)\n• Stage 2: 64 ch  (H/2 × W/2)\n• Stage 3: 128 ch (H/4 × W/4)\n• Stage 4: 256 ch (H/8 × W/8)",
             facecolor="#ECFDF5", edgecolor="#059669", title_color="#065F46", fontsize=8.1, title_fontsize=9.8)

    draw_box(ax, 0.52, 0.64, 0.22, 0.27,
             title="3. TSA Bottleneck",
             text="At H/8 × W/8 (256 ch):\n• Train: [B, 256, 16, 16]\n• Test:  [B, 256, 32, 32]\n\nChannel Attention (MDTA)\n256×256 Covariance Matrix\n+ CBAM (1ca2+1sa2)",
             facecolor="#FEF3C7", edgecolor="#D97706", title_color="#92400E", fontsize=8.1, title_fontsize=9.8)

    draw_box(ax, 0.77, 0.64, 0.21, 0.27,
             title="4. Decoder + Skips",
             text="PixelShuffle Unfolding:\n256 → 128 → 64 ch\n\n3 Overhead Skip Bridges\ncopy crisp road/river edges\nfrom Encoder → Decoder",
             facecolor="#F3E8FF", edgecolor="#7C3AED", title_color="#5B21B6", fontsize=8.1, title_fontsize=9.8)

    arrow(ax, 0.24, 0.775, 0.27, 0.775, color="#1D4ED8", lw=2.2)
    arrow(ax, 0.49, 0.775, 0.52, 0.775, color="#059669", lw=2.2)
    arrow(ax, 0.74, 0.775, 0.77, 0.775, color="#D97706", lw=2.2)

    ax.annotate(
        "3 Multi-Scale Skip Connections (Preserve 1-px Spatial Alignment)",
        xy=(0.85, 0.915), xytext=(0.38, 0.95),
        ha="center", fontsize=9, fontweight="bold", color="#7C3AED",
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.10", color="#7C3AED", lw=1.8),
        zorder=5
    )

    draw_box(ax, 0.52, 0.34, 0.46, 0.23,
             title="5. Mean-Prior Output Head & Auxiliary SDFL Projections",
             text="• final_conv: Conv3×3(64 → 4) predicts raw 4-band reflectance P_dir ∈ [B, 4, H, W]\n"
                  "• Bias initialized to clear-terrain band means: [0.0847, 0.0919, 0.1127, 0.1884]\n"
                  "• Auxiliary heads: 3 down_proj (Encoder) + 3 up_proj (Decoder) for multi-scale SDFL",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.3, title_fontsize=9.6, align="left")

    arrow(ax, 0.87, 0.64, 0.87, 0.57, color="#7C3AED", lw=2.2)

    draw_box(ax, 0.02, 0.05, 0.46, 0.52,
             title="Key Architectural Insights (No Black Boxes!)",
             text="1. Why Two Separate Front Doors (Decoupled Stem)?\n"
                  "   SAR is microwave backscatter; Sentinel-2 is sunlight reflectance.\n"
                  "   Separate 7×7 stems translate each sensor into 16 feature maps\n"
                  "   before fusion, while Role M2 tells Branch 1 where clouds are.\n\n"
                  "2. Why PixelUnshuffle Instead of MaxPool/Strided Conv?\n"
                  "   Folding a 2×2 pixel block into 4 channels loses ZERO spatial\n"
                  "   information during downsampling!\n\n"
                  "3. Why Initialize Output Bias to Clear Means?\n"
                  "   Natural clear Earth reflectance averages ~0.08–0.18, while clouds\n"
                  "   are ~0.80. Starting at [0.085, 0.092, 0.113, 0.188] stabilizes early\n"
                  "   gradients immediately.",
             facecolor="#F4F4F0", edgecolor="#78716C", title_color="#1E293B", fontsize=8.2, title_fontsize=9.8, align="left")

    draw_box(ax, 0.52, 0.05, 0.46, 0.22,
             title="6. How P_dir Is Used in Training vs. Testing",
             text="• Phase 1 (Training, 128×128): Raw P_dir goes DIRECTLY to all 7 Losses & PatchGAN.\n"
                  "  (Golden Rule: Never blend M before loss, or clear regions get zero gradient!)\n"
                  "• Phase 2 (Testing, 256×256): Soft-Mask Gate blends clear pixels + sharp cloud core:\n"
                  "  Y_hat = (1 - M) ⊙ S2_cloudy + M ⊙ P_dir   (0.04 sec / patch, PatchGAN discarded!)",
             facecolor="#DCFCE7", edgecolor="#16A34A", title_color="#166534", fontsize=8.2, title_fontsize=9.6, align="left")

    arrow(ax, 0.75, 0.34, 0.75, 0.27, color="#DC2626", lw=2.2)

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig3_ecrformer_step_by_step.png"), dpi=240)
    plt.close()


# ==============================================================================
# FIGURE 4: MDTA CHANNEL ATTENTION NUMERICAL EXAMPLE (LIKE DL ATTENTION SLIDE)
# ==============================================================================
def make_fig4_mdta():
    fig, ax = plt.subplots(figsize=(12, 5.4), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.02, 0.77, 0.46, 0.19,
             title="✘ Standard ViT (Spatial Pixel-to-Pixel Attention)",
             text="• Multiplies [HW × C] × [C × HW]  →  Attention Matrix is [HW × HW]\n"
                  "• At 128² (bottleneck 16×16): HW = 256  →  Matrix is 256 × 256\n"
                  "• At 256² (bottleneck 32×32): HW = 1024 →  Matrix jumps 16× to 1024 × 1024!\n"
                  "• Fixed spatial positional embeddings CRASH when resolution changes!",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.4, title_fontsize=9.6, align="left")

    draw_box(ax, 0.52, 0.77, 0.46, 0.19,
             title="✔ ECRformer MDTA (Channel-to-Channel Transposed Attention)",
             text="• Multiplies Q [C × HW] × K^T [HW × C]  →  Attention Matrix is [C × C]!\n"
                  "• Spatial pixel count (HW) is contracted (summed out) in the dot product!\n"
                  "• Whether input is 128×128 (HW=256) or 256×256 (HW=1024), C = 256 is FIXED!\n"
                  "• Result: 256×256 Channel Covariance Matrix works at ANY resolution!",
             facecolor="#DCFCE7", edgecolor="#16A34A", title_color="#166534", fontsize=8.4, title_fontsize=9.6, align="left")

    draw_box(ax, 0.02, 0.05, 0.96, 0.67, facecolor="#FFFDF9", edgecolor="#94A3B8", lw=1.6)
    ax.text(0.50, 0.68, "Concrete Toy Example (3 Channels, 4 Spatial Pixels: C = 3, HW = 4)",
            ha="center", va="top", fontsize=11.5, fontweight="bold", color="#991B1B", zorder=4)

    ch_labels = ["Ch 1: SAR Building Edge", "Ch 2: Red Roof Optical", "Ch 3: Smooth Water"]
    for idx, lbl in enumerate(ch_labels):
        y = 0.46 - idx * 0.105
        ax.text(0.035, y + 0.04, lbl, ha="left", va="center", fontsize=8.8, fontweight="bold", color="#1D4ED8", zorder=4)

    # Matrix Q (3 x 4)
    ax.text(0.32, 0.59, "Query Q (C × HW = 3 × 4)", ha="center", fontsize=9.5, fontweight="bold", color="#1E293B", zorder=4)
    q_vals = [
        ["0.6", "0.0", "0.8", "0.0"],
        ["0.5", "0.1", "0.8", "0.2"],
        ["0.0", "0.9", "0.0", "0.4"]
    ]
    q_colors = ["#DBEAFE", "#FCE7F3", "#E0E7FF"]
    for r in range(3):
        for c in range(4):
            rx = 0.22 + c * 0.05
            ry = 0.46 - r * 0.105
            rect = Rectangle((rx, ry), 0.048, 0.088, facecolor=q_colors[r], edgecolor="#64748B", lw=1.2, zorder=3)
            ax.add_patch(rect)
            ax.text(rx + 0.024, ry + 0.044, q_vals[r][c], ha="center", va="center", fontsize=9, fontweight="bold", zorder=4)

    ax.text(0.455, 0.39, "×", ha="center", va="center", fontsize=18, fontweight="bold", color="#1E293B", zorder=4)

    # Matrix K^T (4 x 3)
    ax.text(0.565, 0.59, "Key K^T (HW × C = 4 × 3)", ha="center", fontsize=9.5, fontweight="bold", color="#1E293B", zorder=4)
    kt_vals = [
        ["0.6", "0.5", "0.0"],
        ["0.0", "0.1", "0.9"],
        ["0.8", "0.8", "0.0"],
        ["0.0", "0.2", "0.4"]
    ]
    for r in range(4):
        for c in range(3):
            rx = 0.49 + c * 0.05
            ry = 0.485 - r * 0.088
            rect = Rectangle((rx, ry), 0.048, 0.08, facecolor="#FEF3C7", edgecolor="#64748B", lw=1.2, zorder=3)
            ax.add_patch(rect)
            ax.text(rx + 0.024, ry + 0.04, kt_vals[r][c], ha="center", va="center", fontsize=9, fontweight="bold", zorder=4)

    ax.text(0.675, 0.39, "=", ha="center", va="center", fontsize=18, fontweight="bold", color="#1E293B", zorder=4)

    # Resulting Channel Attention Matrix A (3 x 3)
    ax.text(0.815, 0.59, "Attention A = Q·K^T (C × C = 3 × 3)", ha="center", fontsize=9.5, fontweight="bold", color="#065F46", zorder=4)
    a_vals = [
        ["1.00", "0.94", "0.00"],
        ["0.94", "0.94", "0.17"],
        ["0.00", "0.17", "0.97"]
    ]
    for r in range(3):
        for c in range(3):
            rx = 0.72 + c * 0.065
            ry = 0.46 - r * 0.105
            highlight = (r == 0 and c == 1) or (r == 1 and c == 0)
            fc = "#86EFAC" if highlight else "#ECFDF5"
            ec = "#15803D" if highlight else "#64748B"
            rect = Rectangle((rx, ry), 0.062, 0.088, facecolor=fc, edgecolor=ec, lw=2.2 if highlight else 1.2, zorder=3)
            ax.add_patch(rect)
            ax.text(rx + 0.031, ry + 0.044, a_vals[r][c], ha="center", va="center", fontsize=9.5, fontweight="bold", zorder=4)

    ax.text(0.50, 0.10,
            "Takeaway: Score A[Ch1, Ch2] = 0.94 means 'SAR Building Edges' strongly activate 'Red Roof Optical' across the whole patch!\n"
            "Because HW (4 pixels here, 256 in 128² train, 1024 in 256² test) cancels out, A is ALWAYS [C × C]!",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color="#1E293B",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF08A", edgecolor="#CA8A04", lw=1.2), zorder=4)

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig4_mdta_numerical_example.png"), dpi=240)
    plt.close()


# ==============================================================================
# FIGURE 5: WHY STANDARD L1 BLURS & HOW SCALE-DECOUPLED L1 SOLVES IT
# ==============================================================================
def make_fig5_blur_trap():
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.02, 0.52, 0.46, 0.43,
             title="Trap #1: Conditional-Mean Safe Average",
             text="• Under a thick opaque cloud, SAR shows a forest canopy.\n"
                  "• True optical pixel could be dark green (0.05) or bright (0.15).\n"
                  "• Standard 1×1 L1 punishes sharp texture guesses that miss by 1 px.\n"
                  "• Cowardly minimum of E[|P - Y|]: Predict flat blurry average 0.10!\n"
                  "• Result in our 50-ep Baseline: High PSNR (30.3 dB) but ONLY\n"
                  "  21%–38% high-frequency detail retained (blurry smudge!).",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.5, title_fontsize=10, align="left")

    draw_box(ax, 0.02, 0.05, 0.46, 0.43,
             title="Trap #2: The 1-Pixel Radar Shift 'Double-Edge Penalty'",
             text="• Sentinel-1 (Radar) & Sentinel-2 (Optical) fly in different orbits,\n"
                  "  causing 1–2 pixel geometric co-registration shifts.\n"
                  "• Suppose a sharp road is at pixel x=5 in Ground Truth, but SAR\n"
                  "  guides the generator to draw a crisp road at pixel x=6:\n"
                  "  → 1×1 Pixel L1 penalizes x=5 (missed road) AND x=6 (false road)!\n"
                  "• To avoid double punishment, 1×1 L1 smears the road into a\n"
                  "  wide, blurry gray band covering x=4..7!",
             facecolor="#FEF3C7", edgecolor="#D97706", title_color="#92400E", fontsize=8.5, title_fontsize=10, align="left")

    draw_box(ax, 0.52, 0.52, 0.46, 0.43,
             title="Our Fix #1 — Role M3: Scale-Decoupled L1 Loss",
             text="We decouple color calibration from 1-pixel edge alignment:\n\n"
                  "1. Outside Clouds (1 - 0.8·M): Keep strict 1×1 pixel-wise L1\n"
                  "   so clear sky stays 100% pixel-accurate.\n"
                  "2. Inside Clouds (M = 1): Replace 80% of 1×1 L1 with\n"
                  "   4×4 and 8×8 Average-Pooled L1 (weighted by 1 + M_pool)!\n"
                  "   → A 1-pixel shifted sharp road has the EXACT SAME 4×4 average\n"
                  "     color as the target! Zero double-edge penalty!",
             facecolor="#DCFCE7", edgecolor="#16A34A", title_color="#166534", fontsize=8.5, title_fontsize=10, align="left")

    draw_box(ax, 0.52, 0.05, 0.46, 0.43,
             title="Our Fix #2 — Role M4: Cloud-Boosted Structural Losses",
             text="Inside the cloud mask (w_map = 1.0 + 2.0·M), we apply 4 losses:\n\n"
                  "• VGG-16 Perceptual (w=0.005): relu1_2, relu2_2, relu3_3 on\n"
                  "  both RGB (0.6) and False-Color NIR-R-G (0.4).\n"
                  "• Multi-Scale Signed Gradients (w=0.25): 1×, 2×, 4× dx & dy.\n"
                  "• Edge Pearson Correlation (w=0.0025): Aligns gradient magnitudes.\n"
                  "• 16×16 Local Std Contrast (w=0.35): Matches terrain roughness σ.",
             facecolor="#EFF6FF", edgecolor="#2563EB", title_color="#1D4ED8", fontsize=8.5, title_fontsize=10, align="left")

    arrow(ax, 0.48, 0.73, 0.52, 0.73, color="#16A34A", lw=2.5)
    arrow(ax, 0.48, 0.26, 0.52, 0.26, color="#2563EB", lw=2.5)

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig5_blur_trap_and_scale_decoupled_l1.png"), dpi=240)
    plt.close()


# ==============================================================================
# FIGURE 6: 11-CHANNEL PATCHGAN CRITIC & 16x16 LOGIT SCORECARD
# ==============================================================================
def make_fig6_patchgan():
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=240)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.02, 0.08, 0.29, 0.86,
             title="1. 11-Channel Input Stack\n[B, 11, 128, 128]",
             text="Why 11 Channels?\n\n"
                  "• 4 ch: Optical (3.0 × P_dir or Y)\n"
                  "  Scaled to visible range.\n\n"
                  "• 4 ch: 5×5 High-Pass Residual\n"
                  "  R_HP = 10 · (x - AvgPool5×5(x))\n"
                  "  Subtracts smooth color so\n"
                  "  blurry cloud holes become\n"
                  "  flat ZERO (instantly caught!).\n\n"
                  "• 2 ch: Sentinel-1 SAR (VV, VH)\n"
                  "  Checks if roads match radar!\n\n"
                  "• 1 ch: Soft Cloud Mask M\n"
                  "  Tells critic where cloud was.",
             facecolor="#EFF6FF", edgecolor="#2563EB", title_color="#1D4ED8", fontsize=8.2, title_fontsize=9.8, align="left")

    draw_box(ax, 0.35, 0.28, 0.27, 0.66,
             title="2. Spectral-Norm Critic D\n(70×70 Receptive Field)",
             text="4 Strided Conv Blocks:\n\n"
                  "• Layer 1: Conv4×4, s=2 → 64×64\n"
                  "  (SpectralNorm + LeakyReLU)\n"
                  "• Layer 2: Conv4×4, s=2 → 32×32\n"
                  "  (SN + GroupNorm8 + LReLU)\n"
                  "• Layer 3: Conv4×4, s=2 → 16×16\n"
                  "  (SN + GroupNorm16 + LReLU)\n"
                  "• Layer 4: Conv3×3, s=1 → 16×16\n"
                  "• Head:    Conv3×3, s=1 → [B,1,16,16]\n\n"
                  "Feature Matching (L_FM):\n"
                  "Matches intermediate [f1,f2,f3,f4]\n"
                  "between Real Y and Fake P_dir!",
             facecolor="#FEF3C7", edgecolor="#D97706", title_color="#92400E", fontsize=8.1, title_fontsize=9.8, align="left")

    arrow(ax, 0.31, 0.61, 0.35, 0.61, color="#2563EB", lw=2.2)

    draw_box(ax, 0.66, 0.28, 0.32, 0.66,
             title="3. Output: 16×16 Logit Grid\n(Numbers, NOT an Image!)",
             text="",
             facecolor="#ECFDF5", edgecolor="#059669", title_color="#065F46", fontsize=8.5, title_fontsize=9.8,
             title_top_only=True)

    arrow(ax, 0.62, 0.61, 0.66, 0.61, color="#D97706", lw=2.2)

    grid_vals = [
        ["+1.1", "+0.9", "+0.8", "+1.0"],
        ["+0.9", "-0.8", "-1.1", "+0.7"],
        ["+1.0", "-0.9", "-0.7", "+0.8"],
        ["+1.2", "+0.8", "+0.9", "+1.1"]
    ]
    for r in range(4):
        for c in range(4):
            gx = 0.70 + c * 0.06
            gy = 0.72 - r * 0.065
            is_cloud = (1 <= r <= 2 and 1 <= c <= 2)
            fc = "#FCA5A5" if is_cloud else "#BBF7D0"
            ec = "#DC2626" if is_cloud else "#16A34A"
            rect = Rectangle((gx, gy), 0.056, 0.058, facecolor=fc, edgecolor=ec, lw=1.6, zorder=3)
            ax.add_patch(rect)
            ax.text(gx + 0.028, gy + 0.029, grid_vals[r][c], ha="center", va="center", fontsize=8.2, fontweight="bold", zorder=4)

    ax.text(0.82, 0.40,
            "Each cell grades a 70×70 px patch!\n"
            "Green (+) = Real/Sharp | Red (-) = Blurry\n\n"
            "• Role M5 Cloud Focus:\n"
            "  w_patch = 0.25 + 0.75 · M_down\n"
            "  → 1.00 inside clouds (4× stronger!)\n"
            "  → 0.25 in clear sky",
            ha="center", va="center", fontsize=8.1, fontweight="bold", color="#1E293B", zorder=4)

    draw_box(ax, 0.35, 0.08, 0.63, 0.16,
             title="Backpropagation Feedback Loop (∇L_G) & Test-Time Removal",
             text="• Training: Hinge Loss (w_adv=0.015) + Feature Matching (w_fm=0.15) send ∇L_G back into ECRformer.\n"
                  "• Testing (256×256): PatchGAN is COMPLETELY REMOVED! ECRformer generates crisp textures on its own.",
             facecolor="#FEE2E2", edgecolor="#DC2626", title_color="#991B1B", fontsize=8.0, title_fontsize=9.4, align="left")

    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT_DIR, "slide_fig6_patchgan_detective_grid.png"), dpi=240)
    plt.close()


if __name__ == "__main__":
    make_fig1_physics()
    make_fig2_preprocessing()
    make_fig3_ecrformer()
    make_fig4_mdta()
    make_fig5_blur_trap()
    make_fig6_patchgan()
    print("Re-generated all 6 DL-style teaching diagrams cleanly!")
