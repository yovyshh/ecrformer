"""Comprehensive, spacious 'Teaching Edition' project presentation.
Builds on the clean Poppins visual style of build_presentation_clean.py while expanding
to 32 uncluttered slides that teach every definition, layman analogy, step-by-step
numerical calculation, and architectural diagram without crowding any slide.
"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE = r"c:\Users\Windows 11 Pro\Videos\Projects\ECRformer"
SAMPLES = os.path.join(BASE, "frontend", "public", "samples")
ASSETS = os.path.join(BASE, "backend", "assets")
BRAIN = r"C:\Users\Windows 11 Pro\.gemini\antigravity\brain\565f98e1-faa5-48e4-bedd-0a52dc32b283"

OUT = [
    os.path.join(BASE, "ECRformer_Detailed_Teaching_Presentation.pptx"),
    r"C:\Users\Windows 11 Pro\Downloads\ECRformer_Detailed_Teaching_Presentation.pptx",
    os.path.join(BRAIN, "ECRformer_Detailed_Teaching_Presentation.pptx"),
]

# Prepare clean crop of the 3D Generator Architecture block from paper_pipeline_architecture.png
PAPER_ARCH = os.path.join(BRAIN, "paper_pipeline_architecture.png")
GEN_3D_CROP = os.path.join(ASSETS, "ppt_diagrams", "generator_3d_architecture_clean.png")
os.makedirs(os.path.dirname(GEN_3D_CROP), exist_ok=True)
if os.path.exists(PAPER_ARCH):
    im = Image.open(PAPER_ARCH)
    w_im, h_im = im.size
    top_box = im.crop((int(w_im * 0.155), int(h_im * 0.045), int(w_im * 0.73), int(h_im * 0.405)))
    legend_box = im.crop((int(w_im * 0.07), int(h_im * 0.915), int(w_im * 0.93), int(h_im * 0.985)))
    canvas_w = max(top_box.width, legend_box.width) + 40
    canvas_h = top_box.height + legend_box.height + 30
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    canvas.paste(top_box, ((canvas_w - top_box.width) // 2, 10))
    canvas.paste(legend_box, ((canvas_w - legend_box.width) // 2, top_box.height + 20))
    canvas.save(GEN_3D_CROP)

# ---------- Design tokens (matching build_presentation_clean.py) ----------
NAVY = RGBColor(0x0B, 0x12, 0x20)
INK = RGBColor(0x0F, 0x17, 0x2A)
SLATE = RGBColor(0x47, 0x55, 0x69)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
LINE = RGBColor(0xE2, 0xE8, 0xF0)
CARD = RGBColor(0xF8, 0xFA, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INDIGO = RGBColor(0x4F, 0x46, 0xE5)
TEAL = RGBColor(0x0D, 0x94, 0x88)
CORAL = RGBColor(0xF9, 0x73, 0x16)
ROSE = RGBColor(0xE1, 0x1D, 0x48)
SOFT_IND = RGBColor(0xEE, 0xF2, 0xFF)
SOFT_TEAL = RGBColor(0xF0, 0xFD, 0xFA)
SOFT_CORAL = RGBColor(0xFF, 0xF7, 0xED)
SOFT_ROSE = RGBColor(0xFF, 0xF1, 0xF2)

H = "Poppins SemiBold"
B = "Poppins Light"
M = "Poppins Medium"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 33
state = {"n": 0}


def img(scene, kind):
    return os.path.join(SAMPLES, f"scene-{scene}", f"{kind}.png")


def text(slide, x, y, w, h, runs, size=16, font=B, color=SLATE, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, line=1.18):
    """runs: str or list of paragraphs; each paragraph str or list of (text, font, color, size)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        segs = para if isinstance(para, list) else [(para, font, color, size)]
        for seg in segs:
            t, f, c, s = seg
            r = p.add_run()
            r.text = t
            r.font.name = f
            r.font.size = Pt(s)
            r.font.color.rgb = c
            if spacing:
                r._r.get_or_add_rPr().set("spc", str(spacing))
    return tb


def box(slide, x, y, w, h, fill=CARD, line=None, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def picture(slide, path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def content_slide(kicker, title, subtitle=None):
    state["n"] += 1
    s = prs.slides.add_slide(BLANK)
    box(s, 0.8, 0.55, 0.55, 0.06, fill=INDIGO, shape=MSO_SHAPE.RECTANGLE)
    text(s, 1.5, 0.43, 9.5, 0.3, kicker.upper(), size=10.5, font=H, color=INDIGO, spacing=280)
    title_sz = 24 if len(title) > 48 else 28
    text(s, 0.8, 0.76, 11.8, 0.62, title, size=title_sz, font=H, color=INK)
    if subtitle:
        text(s, 0.8, 1.42, 11.8, 0.42, subtitle, size=14.2, font=B, color=SLATE)
    text(s, 0.8, 7.05, 8.5, 0.3, "SAR-Guided Satellite Cloud Removal  ·  Detailed Teaching Edition", size=9, font=B, color=MUTED)
    text(s, 11.3, 7.05, 1.25, 0.3, f"{state['n']:02d} / {TOTAL}", size=9, font=M, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def dark_slide():
    state["n"] += 1
    s = prs.slides.add_slide(BLANK)
    box(s, 0, 0, 13.333, 7.5, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    return s


def pill(slide, x, y, w, h, label, fill=SOFT_IND, color=INDIGO, size=11):
    c = box(slide, x, y, w, h, fill=fill, radius=0.45)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = H
    r.font.size = Pt(size)
    r.font.color.rgb = color


def captioned_image(slide, path, x, y, size, caption, color=SLATE):
    picture(slide, path, x, y, w=size, h=size)
    text(slide, x - 0.1, y + size + 0.08, size + 0.2, 0.35, caption, size=11.5, font=M, color=color, align=PP_ALIGN.CENTER)


# ==============================================================================
# SLIDE 01 — TITLE SLIDE
# ==============================================================================
s = dark_slide()
text(s, 0.9, 0.85, 7, 0.3, "M.SC. PROJECT PRESENTATION  ·  CUSAT", size=11, font=H, color=RGBColor(0x81, 0x8C, 0xF8), spacing=300)
text(s, 0.9, 1.35, 7.2, 2.2, [
    [("SAR-Guided", H, WHITE, 44)],
    [("Satellite Cloud", H, WHITE, 44)],
    [("Removal", H, RGBColor(0x5E, 0xEA, 0xD4), 44)],
], line=1.02)
text(s, 0.9, 3.75, 6.8, 0.9,
     "Comprehensive Teaching Edition: Definitions, Physics,\nStep-by-Step Calculations & Deep Learning Architecture",
     size=15.5, font=B, color=RGBColor(0xCB, 0xD5, 0xE1), line=1.25)
box(s, 0.9, 4.9, 0.55, 0.04, fill=RGBColor(0x5E, 0xEA, 0xD4), shape=MSO_SHAPE.RECTANGLE)
text(s, 0.9, 5.12, 3.4, 0.3, "TEAM MEMBERS", size=10, font=H, color=MUTED, spacing=300)
text(s, 0.9, 5.42, 3.6, 1.2, ["Agnal K V", "Bivin Balu", "Vaishnav T Prakash"], size=15, font=M, color=WHITE, line=1.25)
text(s, 4.4, 5.12, 3.4, 0.3, "PROJECT GUIDE", size=10, font=H, color=MUTED, spacing=300)
text(s, 4.4, 5.42, 3.6, 0.5, "Dr. Sabu M K", size=15, font=M, color=WHITE)

picture(s, img("suburban", "cloudy"), 8.25, 1.0, w=2.25, h=2.25)
picture(s, img("suburban", "blended"), 10.6, 1.0, w=2.25, h=2.25)
picture(s, img("farms", "cloudy"), 8.25, 3.7, w=2.25, h=2.25)
picture(s, img("farms", "blended"), 10.6, 3.7, w=2.25, h=2.25)
text(s, 8.25, 6.08, 2.25, 0.3, "Cloudy input (Sentinel-2)", size=11, font=M, color=MUTED, align=PP_ALIGN.CENTER)
text(s, 10.6, 6.08, 2.25, 0.3, "Our reconstructed output", size=11, font=M, color=RGBColor(0x5E, 0xEA, 0xD4), align=PP_ALIGN.CENTER)


# ==============================================================================
# SLIDE 02 — LEARNING ROADMAP
# ==============================================================================
s = content_slide("Overview", "Learning roadmap", "Structured step-by-step from basic satellite physics to deep learning math")
items = [
    ("Problem & physics", "Why clouds block optical cameras and how SAR radar passes through"),
    ("Dataset & prep math", "SEN12MS-CR tensors, s2cloudless mask, dB scaling & Opaque Cutout"),
    ("Dual-phase pipeline", "128×128 training vs 256×256 testing and all 7 cloud-mask roles"),
    ("Inside ECRformer", "Decoupled stem, PixelUnshuffle, and MDTA channel attention math"),
    ("Solving the blur trap", "Scale-decoupled L1, 4 structural losses & PatchGAN high-pass math"),
    ("Results & honest view", "5-stage visual progression, metrics explained & real-world trade-offs"),
]
for i, (t, d) in enumerate(items):
    col, row = i % 3, i // 3
    x, y = 0.8 + col * 4.0, 2.1 + row * 2.3
    box(s, x, y, 3.7, 1.95, fill=CARD, line=LINE)
    text(s, x + 0.3, y + 0.22, 1.2, 0.5, f"0{i+1}", size=26, font=H, color=INDIGO)
    text(s, x + 0.3, y + 0.82, 3.1, 0.4, t, size=17.5, font=H, color=INK)
    text(s, x + 0.3, y + 1.22, 3.1, 0.6, d, size=12.5, font=B, color=SLATE, line=1.2)


# ==============================================================================
# SLIDE 03 — THE CLOUD PROBLEM (LAYMAN'S INTRODUCTION)
# ==============================================================================
s = content_slide("01 · Problem & physics", "Clouds hide the Earth's surface",
                  "Why satellite cloud removal is a critical problem in remote sensing")
text(s, 0.8, 2.1, 6.4, 4.4, [
    [("More than 50% ", H, INK, 19), ("of the Earth's sky is covered by clouds at any given moment.", B, SLATE, 19)],
    [("", B, SLATE, 8)],
    [("Optical satellites ", H, CORAL, 19), ("work like everyday cameras — they need clear sunlight bouncing off the ground.", B, SLATE, 19)],
    [("", B, SLATE, 8)],
    [("When thick clouds roll in, ", B, SLATE, 19), ("farms, rivers, roads, and flood zones vanish behind a bright white wall.", H, INK, 19)],
    [("", B, SLATE, 8)],
    [("Our project goal: ", H, INDIGO, 19), ("use cloud-penetrating radar + deep learning to reconstruct the hidden ground accurately.", B, SLATE, 19)],
], line=1.2)
captioned_image(s, img("forest", "cloudy"), 7.9, 1.95, 4.35, "Real cloudy Sentinel-2 image (78.4% cloud cover)")


# ==============================================================================
# SLIDE 04 — KEY TERMS SIMPLY DEFINED (OPTICAL VS SAR PHYSICS)
# ==============================================================================
s = content_slide("01 · Problem & physics", "Fundamental Remote Sensing Concepts",
                  "Core optical, synthetic aperture radar, and cloud masking definitions")
defs = [
    ("Passive Optical Sensor (Sentinel-2)", "Like a camera with no flash",
     "Waits for sunlight to hit the Earth and bounce back into space.\n"
     "• Wavelength: 490 – 842 nm (tiny visible & near-infrared waves).\n"
     "• Why clouds block it: Cloud droplets (~10 µm) are larger than optical waves, scattering sunlight into a blinding white glare (Mie scattering).",
     CORAL, SOFT_CORAL),
    ("Active SAR Radar (Sentinel-1)", "Synthetic Aperture Radar — brings its own flash",
     "Shoots its own C-band microwave pulses toward Earth and listens for the echo.\n"
     "• Wavelength: ~5.5 cm (55,000,000 nm — 5,500× larger than cloud droplets!).\n"
     "• Why it sees through clouds: 5.5 cm waves ignore tiny water droplets completely, working day or night in any weather.",
     TEAL, SOFT_TEAL),
    ("VV Polarisation (Vertical → Vertical)", "Measures surface roughness & geometry",
     "The radar sends a vertically aligned wave (V) and measures the vertical echo (V).\n"
     "• Smooth water reflects the wave away like a mirror → looks dark (−22 dB).\n"
     "• Rough soil, roads, and building corners bounce strong echoes back (−3 dB).",
     INDIGO, SOFT_IND),
    ("VH Polarisation (Vertical → Horizontal)", "Measures 3D vegetation & crop structure",
     "The radar sends a vertical wave (V) and listens for the twisted horizontal echo (H).\n"
     "• Flat bare ground barely twists the wave.\n"
     "• Dense tree canopies, forests, and leafy crops bounce the wave multiple times inside branches, strongly depolarising it (volume scattering).",
     INK, CARD),
]
for i, (t, sub, body, col, soft) in enumerate(defs):
    c, r = i % 2, i // 2
    x, y = 0.8 + c * 6.0, 2.0 + r * 2.4
    box(s, x, y, 5.75, 2.2, fill=soft, line=LINE if soft == CARD else None)
    text(s, x + 0.3, y + 0.16, 5.2, 0.35, t, size=16, font=H, color=col)
    text(s, x + 0.3, y + 0.5, 5.2, 0.3, sub, size=12, font=M, color=INK)
    text(s, x + 0.3, y + 0.84, 5.2, 1.25, body, size=11.5, font=B, color=SLATE, line=1.2)


# ==============================================================================
# SLIDE 05 — TWO SATELLITES VISUAL COMPARISON
# ==============================================================================
s = content_slide("01 · Problem & physics", "Two satellites, complementary strengths",
                  "Neither satellite can solve the problem alone — so we fuse both")
for i, (name, sub, good, bad, path, col, soft, foot) in enumerate([
    ("Sentinel-2 · Optical", "Passive · 4 Spectral Bands (10 m/px)",
     "Rich natural colours (green trees, red roofs, blue water)",
     "Completely blinded whenever clouds roll in",
     img("suburban", "cloudy"), CORAL, SOFT_CORAL,
     "Captures B04 (Red), B03 (Green), B02 (Blue), and B08 (Near-Infrared)"),
    ("Sentinel-1 · SAR Radar", "Active · 2 Backscatter Bands (10 m/px)",
     "Penetrates 100% of clouds — reveals roads, rivers & buildings",
     "No natural colour & has grainy speckle",
     img("suburban", "sar"), TEAL, SOFT_TEAL,
     "Captures VV (surface roughness) and VH (vegetation volume) in decibels (dB)"),
]):
    x = 0.8 + i * 6.0
    box(s, x, 2.0, 5.75, 4.05, fill=soft)
    picture(s, path, x + 0.3, 2.25, w=2.25, h=2.25)
    text(s, x + 2.75, 2.25, 2.8, 0.38, name, size=17.5, font=H, color=INK)
    text(s, x + 2.75, 2.65, 2.8, 0.32, sub, size=11.5, font=M, color=col)
    text(s, x + 2.75, 3.15, 2.8, 1.4, [
        [("+  ", H, TEAL, 13), (good, B, INK, 13)],
        [("", B, INK, 5)],
        [("–  ", H, ROSE, 13), (bad, B, INK, 13)],
    ], line=1.18)
    text(s, x + 0.3, 4.92, 5.2, 0.8, foot, size=11.5, font=M, color=SLATE)
box(s, 0.8, 6.22, 11.75, 0.58, fill=SOFT_IND)
text(s, 0.8, 6.22, 11.75, 0.58, [
    [("Core Fusion Principle → ", H, INDIGO, 15),
     ("Use Sentinel-1 radar as a structural blueprint and Sentinel-2 clear margins for natural colour.", M, INK, 15)]
], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 06 — THE DATASET: SEN12MS-CR & WHY .NPZ + NIR
# ==============================================================================
s = content_slide("02 · Dataset & prep math", "The SEN12MS-CR benchmark dataset",
                  "Co-registered tri-modal satellite patches from the ROIs1970_fall subset")
for i, (num, lab, sub) in enumerate([
    ("33,468", "Training patches", "Used to train Generator G & Critic D"),
    ("1,115", "Validation patches", "Strict geographic split · Test tile s2_139 untouched"),
    ("256 × 256", "Pixels per patch (10 m/px)", "Covers 2.56 km × 2.56 km of real terrain"),
]):
    x = 0.8 + i * 4.0
    box(s, x, 2.0, 3.7, 1.85, fill=CARD, line=LINE)
    text(s, x + 0.3, 2.2, 3.1, 0.65, num, size=30, font=H, color=INDIGO)
    text(s, x + 0.3, 2.95, 3.1, 0.35, lab, size=15, font=H, color=INK)
    text(s, x + 0.3, 3.32, 3.1, 0.4, sub, size=11.5, font=B, color=SLATE)

box(s, 0.8, 4.15, 5.75, 2.6, fill=SOFT_CORAL)
text(s, 1.1, 4.3, 5.2, 0.36, "Why .npz float arrays instead of .jpg files?", size=15, font=H, color=CORAL)
text(s, 1.1, 4.76, 5.2, 1.8, [
    "• Standard JPEG/PNG files only store 3 channels (R, G, B) as whole numbers from 0 to 255.",
    "• Our satellite data has 6 physical sensor bands: 4 optical reflectance bands (0.0 to 1.0) + 2 radar bands in negative decibels (−35 to 0 dB).",
    "• Storing as 32-bit floating-point .npz arrays preserves exact scientific precision with zero compression artifacts.",
], size=12, font=B, color=SLATE, line=1.22)

box(s, 6.8, 4.15, 5.75, 2.6, fill=SOFT_TEAL)
text(s, 7.1, 4.3, 5.2, 0.36, "Why include Band B08 (Near-Infrared / NIR)?", size=15, font=H, color=TEAL)
text(s, 7.1, 4.76, 5.2, 1.8, [
    "• Our 4 optical channels are B04 (Red, 665 nm), B03 (Green, 560 nm), B02 (Blue, 490 nm), and B08 (NIR, 842 nm).",
    "• Healthy chlorophyll in trees and crops reflects Near-Infrared light ~4× more strongly than visible green light!",
    "• Predicting B08 alongside RGB allows agricultural indices (like NDVI crop health) to work on the cloud-removed image.",
], size=12, font=B, color=SLATE, line=1.22)


# ==============================================================================
# SLIDE 07 — NOTATION & TENSOR SHAPES MADE SIMPLE
# ==============================================================================
s = content_slide("02 · Dataset & prep math", "Mathematical Notation & Tensor Dimensionality",
                  "4D tensor structures [Batch B, Channels C, Height H, Width W] in multi-modal pipelines")
headers = ["Symbol", "Name in Code", "Train Shape (128²)", "Test Shape (256²)", "Range & Plain-English Meaning"]
col_w = [1.3, 1.8, 2.0, 2.0, 4.65]
x0, y0 = 0.8, 2.0
box(s, x0, y0, sum(col_w), 0.5, fill=NAVY, radius=0.02, shape=MSO_SHAPE.RECTANGLE)
cx = x0
for h_text, w in zip(headers, col_w):
    text(s, cx + 0.12, y0, w - 0.2, 0.5, h_text, size=12, font=H, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cx += w

rows = [
    ("S2_cloudy", "s2_cloudy", "[B, 4, 128, 128]", "[B, 4, 256, 256]", "[0, 1] · Cloudy Sentinel-2 optical input (Red, Green, Blue, NIR)"),
    ("S1", "s1", "[B, 2, 128, 128]", "[B, 2, 256, 256]", "[0, 1] · Normalized Sentinel-1 SAR radar (VV, VH backscatter)"),
    ("M", "cloud_mask", "[B, 1, 128, 128]", "[B, 1, 256, 256]", "[0, 1] · Soft cloud probability mask (0 = clear sky, 1 = thick cloud)"),
    ("X_in", "x (7-ch concat)", "[B, 7, 128, 128]", "[B, 7, 256, 256]", "[0, 1] · Full generator input stack: [S1 (2ch), S2_cloudy (4ch), M (1ch)]"),
    ("Y", "y / s2_clear", "[B, 4, 128, 128]", "[B, 4, 256, 256]", "[0, 1] · Real cloud-free Sentinel-2 target image (Ground Truth)"),
    ("P_dir", "pred_direct", "[B, 4, 128, 128]", "[B, 4, 256, 256]", "[0, 1] · Raw unblended 4-band output predicted directly by ECRformer"),
    ("Ŷ (Y_hat)", "pred_blended", "Not used in loss", "[B, 4, 256, 256]", "[0, 1] · Final delivered image: (1 − M) ⊙ S2_cloudy + M ⊙ P_dir"),
]
for idx, row in enumerate(rows):
    ry = y0 + 0.52 + idx * 0.65
    fill = CARD if idx % 2 == 0 else WHITE
    box(s, x0, ry, sum(col_w), 0.62, fill=fill, line=LINE, shape=MSO_SHAPE.RECTANGLE)
    cx = x0
    for c_idx, (val, w) in enumerate(zip(row, col_w)):
        fnt = H if c_idx == 0 else (M if c_idx in (1, 2, 3) else B)
        clr = INDIGO if c_idx == 0 else (TEAL if c_idx == 3 else INK if c_idx < 4 else SLATE)
        text(s, cx + 0.12, ry, w - 0.2, 0.62, val, size=11.5, font=fnt, color=clr, anchor=MSO_ANCHOR.MIDDLE)
        cx += w


# ==============================================================================
# SLIDE 08 — CALCULATION #1: CLOUD MASK M & RADAR dB NORMALIZATION
# ==============================================================================
s = content_slide("02 · Dataset & prep math", "Calculation #1: Cloud mask & radar scaling",
                  "How raw satellite numbers are converted into clean [0, 1] neural network inputs")
# Left card: Cloud mask
box(s, 0.8, 2.0, 5.75, 4.75, fill=SOFT_IND)
pill(s, 1.1, 2.18, 2.6, 0.35, "PART A · CLOUD MASK M", fill=INDIGO, color=WHITE, size=10.5)
text(s, 1.1, 2.62, 5.2, 0.36, "Limitations of Optical Luminance Thresholding", size=15.5, font=H, color=INK)
text(s, 1.1, 2.98, 5.2, 0.95,
     "White snow, beaches, and bright roofs look just like clouds in RGB! "
     "ESA's s2cloudless checks 13 Sentinel-2 bands — including Cirrus Band B10 (1375 nm), where high-altitude clouds pop out while ground light is absorbed.",
     size=11, font=B, color=SLATE, line=1.18)
text(s, 1.1, 4.02, 5.2, 0.34, "3-Step Morphological Refinement (in our code):", size=13.5, font=H, color=INDIGO)
text(s, 1.1, 4.38, 5.2, 2.2, [
    [("Step 1 · 9×9 Mean Filter (> 0.5): ", H, INK, 11.5), ("Averages local cloud probability (threshold > 0.4) to remove isolated 1-pixel snow/roof false alarms.", B, SLATE, 11.5)],
    [("", B, SLATE, 3)],
    [("Step 2 · 5×5 Max-Pool Dilation (radius 2): ", H, INK, 11.5), ("Expands the mask outward by 2 pixels to cover thin, semi-transparent cloud halos.", B, SLATE, 11.5)],
    [("", B, SLATE, 3)],
    [("Step 3 · 11×11 Gaussian Blur (σ = 2.0): ", H, INK, 11.5), ("Smooths hard edges into a continuous feathering weight M ∈ [0.0, 1.0].", B, SLATE, 11.5)],
], line=1.16)

# Right card: Radar normalization worked example
box(s, 6.8, 2.0, 5.75, 4.75, fill=SOFT_TEAL)
pill(s, 7.1, 2.18, 3.3, 0.35, "PART B · WORKED RADAR MATH", fill=TEAL, color=WHITE, size=10.5)
text(s, 7.1, 2.62, 5.2, 0.36, "Scaling negative decibels (dB) into [0, 1]", size=15.5, font=H, color=INK)
box(s, 7.1, 3.08, 5.15, 1.05, fill=WHITE, line=LINE)
text(s, 7.3, 3.15, 4.8, 0.9, [
    [("VV_norm  =  ( clamp(VV, −25, 0) + 25 ) / 25", H, TEAL, 13.5)],
    [("VH_norm  =  ( clamp(VH, −35, 0) + 35 ) / 35", H, INDIGO, 13.5)],
], line=1.35)
text(s, 7.1, 4.28, 5.2, 0.35, "Worked Numerical Example (1 Satellite Pixel):", size=13.5, font=H, color=TEAL)
text(s, 7.1, 4.65, 5.2, 1.9, [
    [("Given raw radar echo: ", M, INK, 12), ("VV = −12.5 dB,   VH = −17.5 dB", H, CORAL, 12)],
    [("1. Clamp to valid physical window:", H, INK, 12)],
    [("   −12.5 lies inside [−25, 0]  ✓     −17.5 lies inside [−35, 0]  ✓", B, SLATE, 11.5)],
    [("2. Shift to positive & divide by span:", H, INK, 12)],
    [("   VV_norm = (−12.5 + 25) / 25 = 12.5 / 25 = ", B, SLATE, 12), ("0.50", H, TEAL, 13)],
    [("   VH_norm = (−17.5 + 35) / 35 = 17.5 / 35 = ", B, SLATE, 12), ("0.50", H, INDIGO, 13)],
], line=1.2)


# ==============================================================================
# SLIDE 09 — STOPPING SHORTCUTS: OPAQUE CLOUD CUTOUT (ROLE M1)
# ==============================================================================
s = content_slide("02 · Dataset & prep math", "Stopping the AI from cheating: Opaque Cutout",
                  "Role M1 of the cloud mask — forcing the network to genuinely use Sentinel-1 radar")
box(s, 0.8, 2.0, 5.6, 2.2, fill=SOFT_ROSE)
text(s, 1.1, 2.18, 5.0, 0.36, "The 'Thin-Cloud Shortcut' Problem", size=15.5, font=H, color=ROSE)
text(s, 1.1, 2.6, 5.0, 1.45, [
    "• In thin or semi-transparent clouds, faint ground edges still leak through the optical bands (correlation > 0.80).",
    "• A lazy neural network quickly learns to just boost contrast on the faint optical leak and completely ignores the SAR radar!",
    "• When tested on a 100% thick white cloud, that lazy model fails.",
], size=11.5, font=B, color=SLATE, line=1.2)

box(s, 0.8, 4.4, 5.6, 2.35, fill=SOFT_TEAL)
text(s, 1.1, 4.55, 5.0, 0.36, "Our Fix: Role M1 Opaque Cutout (65% prob)", size=15, font=H, color=TEAL)
text(s, 1.1, 4.98, 5.0, 1.6, [
    "• In 65% of training samples, we replace cloudy pixels with a featureless 29×29 average-pooled veil V (two passes of 15×15 AvgPool).",
    "• With zero optical edges left inside the cloud, the generator is forced to extract road and field geometry from Sentinel-1 SAR!",
], size=11.5, font=B, color=SLATE, line=1.22)

# Right side: step-by-step math & visual strip
box(s, 6.75, 2.0, 5.8, 2.8, fill=CARD, line=LINE)
text(s, 7.05, 2.16, 5.3, 0.35, "Step-by-Step Cutout Math", size=14.5, font=H, color=INK)
text(s, 7.05, 2.58, 5.3, 2.1, [
    [("Step 1 · Opaque core weight α:", H, INDIGO, 12)],
    [("   α = clamp( (M − 0.15) / 0.85,  0.0,  1.0 )", M, INK, 11.5)],
    [("Step 2 · Featureless cloud veil V (≈ 29×29 blur):", H, INDIGO, 12)],
    [("   V = AvgPool_15×15( AvgPool_15×15( S2_cloudy ) )", M, INK, 11.5)],
    [("Step 3 · Blind the cloud interior:", H, INDIGO, 12)],
    [("   S2_aug = (1 − α) ⊙ S2_cloudy  +  α ⊙ V", H, TEAL, 12.5)],
], line=1.2)

for idx, (lab, k) in enumerate([("Cloudy S2", "cloudy"), ("Soft Mask M", "mask"), ("SAR Radar S1", "sar")]):
    px = 6.9 + idx * 1.95
    picture(s, img("ridge", k), px, 5.0, w=1.45, h=1.45)
    text(s, px - 0.1, 6.5, 1.65, 0.3, lab, size=11, font=M, color=SLATE, align=PP_ALIGN.CENTER)


# ==============================================================================
# SLIDE 10 — COMPLETE DUAL-PHASE PIPELINE DIAGRAM
# ==============================================================================
s = content_slide("03 · Dual-phase pipeline", "Complete training vs. testing pipeline",
                  "Phase 1 trains on 128×128 random crops (with Cutout & PatchGAN); Phase 2 tests on full 256×256 scenes")
picture(s, os.path.join(ASSETS, "pipeline_training_vs_testing_complete.png"), 1.85, 1.9, h=5.0)


# ==============================================================================
# SLIDE 11 — ALL 7 ROLES OF THE CLOUD MASK (M1–M5 vs I1–I2)
# ==============================================================================
s = content_slide("03 · Dual-phase pipeline", "Every job of the cloud mask M across the pipeline",
                  "The soft cloud mask M ∈ [0, 1] plays 5 active roles during training and 2 roles during testing")
# Left column: Training M1-M5
box(s, 0.8, 1.95, 6.4, 4.85, fill=SOFT_IND)
pill(s, 1.1, 2.15, 4.3, 0.36, "PHASE 1 · TRAINING ROLES (128 × 128 CROPS)", fill=INDIGO, color=WHITE, size=10.5)
m_roles = [
    ("M1", "Opaque Cloud Cutout (65% prob)", "Blinds faint optical leaks under clouds with a 29×29 veil so G must read SAR."),
    ("M2", "7th Input Channel to Encoder", "Concatenated with S2_cloudy [4+1=5 ch] entering Stem Branch 1 to mark corrupted pixels."),
    ("M3", "Scale-Decoupled L1 Weighting", "Relaxes 1×1 pixel L1 inside clouds (1 − 0.8M) and boosts 4×4 & 8×8 pooled L1 (1 + M)."),
    ("M4", "Structural Loss Boost (1 + 2M)", "Amplifies VGG-16 perceptual and multi-scale edge losses by 3× inside cloud regions."),
    ("M5", "PatchGAN Critic Focus (0.25 + 0.75M)", "Weights the 16×16 adversarial scorecard 4× harder on cloudy patches (1.0 vs 0.25)."),
]
for idx, (code, title_r, desc_r) in enumerate(m_roles):
    ry = 2.68 + idx * 0.8
    pill(s, 1.1, ry + 0.04, 0.58, 0.34, code, fill=INDIGO, color=WHITE, size=11)
    text(s, 1.8, ry, 5.2, 0.3, title_r, size=13.5, font=H, color=INK)
    text(s, 1.8, ry + 0.3, 5.2, 0.45, desc_r, size=11, font=B, color=SLATE)

# Right column: Testing I1-I2
box(s, 7.45, 1.95, 5.1, 4.85, fill=SOFT_TEAL)
pill(s, 7.75, 2.15, 4.2, 0.36, "PHASE 2 · TESTING ROLES (256 × 256 SCENES)", fill=TEAL, color=WHITE, size=10.5)
i_roles = [
    ("I1", "7th Input Channel (Full 256×256)",
     "Guides the frozen EMA Generator G on where clouds are located in the full test scene (Opaque Cutout is turned OFF at test time)."),
    ("I2", "Soft-Mask Radiometric Blending Gate",
     "Combines the real clear pixels with the neural prediction:\nŶ = (1 − M) ⊙ S2_cloudy + M ⊙ P_dir\nGuarantees 0% distortion on clear sky!"),
]
for idx, (code, title_r, desc_r) in enumerate(i_roles):
    ry = 2.75 + idx * 1.45
    pill(s, 7.75, ry + 0.04, 0.58, 0.34, code, fill=TEAL, color=WHITE, size=11)
    text(s, 8.45, ry, 3.9, 0.35, title_r, size=14, font=H, color=INK)
    text(s, 8.45, ry + 0.38, 3.9, 0.95, desc_r, size=11.5, font=B, color=SLATE, line=1.22)

box(s, 7.75, 5.7, 4.5, 0.85, fill=WHITE, line=LINE)
text(s, 7.95, 5.8, 4.1, 0.65, [
    [("Where is PatchGAN at test time?", H, ROSE, 12.5)],
    [("Completely removed! Only Generator G runs (0.04 sec / scene).", M, INK, 11.5)],
], line=1.2)


# ==============================================================================
# SLIDE 12 — LAYMAN'S GUIDE TO NEURAL NETWORK TERMS
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "Deep Learning Architectural Foundations",
                  "Fundamental generator components: Convolutions, Multi-Head Attention, Gating, and Residual Learning")
terms = [
    ("1 · Convolution (Conv3×3 / Conv7×7)", "A sliding magnifying glass",
     "A small grid of learnable numbers (e.g. 3×3 or 7×7) that slides across the image pixel by pixel.\n"
     "• Early layers detect simple lines and corners.\n"
     "• Deeper layers recognize roads, river bends, and crop fields.",
     CORAL, SOFT_CORAL),
    ("2 · Feature Channels (C = 32 → 256)", "A stack of specialized highlighters",
     "Instead of keeping just 4 colour bands, the network expands the image into 32, 64, 128, and 256 channels.\n"
     "• Think of each channel as a specialist: Channel 12 highlights highways, Channel 85 highlights water, Channel 140 highlights forest texture.",
     INDIGO, SOFT_IND),
    ("3 · Hourglass Network (Encoder–Decoder)", "Shrink to understand, expand to paint",
     "• Encoder (left half): Shrinks spatial size (128 → 64 → 32 → 16) while increasing channels so the model sees the big-picture context.\n"
     "• Decoder (right half): Expands back to full size (16 → 32 → 64 → 128) to paint the 4 cloud-free optical bands.",
     TEAL, SOFT_TEAL),
    ("4 · Skip Connections", "Express bridges that preserve crisp edges",
     "When the Encoder shrinks the image 8× down to the bottleneck, tiny 1-pixel road positions can get slightly blurred.\n"
     "• Skip connections copy high-resolution features directly from the Encoder across to the matching Decoder stage so fine edges stay razor-sharp.",
     INK, CARD),
]
for i, (t, sub, body, col, soft) in enumerate(terms):
    c, r = i % 2, i // 2
    x, y = 0.8 + c * 6.0, 2.0 + r * 2.4
    box(s, x, y, 5.75, 2.2, fill=soft, line=LINE if soft == CARD else None)
    text(s, x + 0.3, y + 0.16, 5.2, 0.35, t, size=16, font=H, color=col)
    text(s, x + 0.3, y + 0.5, 5.2, 0.3, sub, size=12, font=M, color=INK)
    text(s, x + 0.3, y + 0.84, 5.2, 1.25, body, size=11.5, font=B, color=SLATE, line=1.2)


# ==============================================================================
# SLIDE 13 — 3D LAYER ARCHITECTURE OF GENERATOR G (VISUAL DIAGRAM)
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "3D layer architecture of Generator G",
                  "ECRformerAdaptedModel · 8,316,228 trainable parameters (8.31M) · 4 stages with skip connections")
if os.path.exists(GEN_3D_CROP):
    picture(s, GEN_3D_CROP, 0.9, 1.9, w=11.5)
box(s, 0.8, 5.95, 11.75, 0.85, fill=CARD, line=LINE)
text(s, 1.1, 6.05, 11.2, 0.65, [
    [("Architecture trace:  ", H, INDIGO, 13),
     ("Decoupled Stem (2ch SAR → 16ch, 5ch Opt+Mask → 16ch)  →  4 Encoder Stages [2, 2, 1, 1] with PixelUnshuffle (32 → 64 → 128 → 256 ch)  →  TSA Restormer Bottleneck (MDTA + GDFN + CBAM)  →  3 Decoder Stages with PixelShuffle + Skip Fusers  →  Final Conv3×3 (64 → 4ch P_dir).", B, INK, 12.5)]
], line=1.2)


# ==============================================================================
# SLIDE 14 — INSIDE ECRFORMER: STEP-BY-STEP ENGINEERING CHOICES
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "Architectural Design Principles of ECRformer",
                  "Decoupled stems, cross-modality attention, TSA bottleneck, and residual scaling")
choices = [
    ("1 · Two-Door Decoupled Stem", "Why radar and optical don't share the first layer",
     "• Branch 0: Conv7×7(2 → 16) processes SAR [VV, VH].\n"
     "• Branch 1: Conv7×7(5 → 16) processes [S2_cloudy, M] (Role M2).\n"
     "• Why separate? Radar is microwave echo with speckle; Sentinel-2 is sunlight reflectance. Separate 7×7 stems translate each sensor into 16 compatible feature maps before concatenating to 32 channels.",
     CORAL, SOFT_CORAL),
    ("2 · PixelUnshuffle & PixelShuffle", "Zero-loss folding instead of pooling",
     "• Standard Max-Pooling throws away 75% of pixels when shrinking an image by 2×.\n"
     "• PixelUnshuffle folds every 2×2 block of pixels into 4× channels: [B, C, 2H, 2W] → [B, 4C, H, W], followed by a 3×3 conv.\n"
     "• Result: 0% spatial information is lost during downsampling!",
     INDIGO, SOFT_IND),
    ("3 · Hybrid Depthwise Conv + CBAM", "Local edges + channel & spatial focus",
     "• Each stage runs ECRformer blocks (3×3 depthwise + 1×1 pointwise residual convolutions) paired with CBAM (1ca2+1sa2).\n"
     "• Channel Attention (CA) weighs which spectral/radar channels matter most; Spatial Attention (SA) highlights cloud boundaries.",
     TEAL, SOFT_TEAL),
    ("4 · Mean-Prior Output Bias", "Starting at real Earth colours on Step 1",
     "• Clear Earth terrain has low average reflectance (~0.08–0.19), whereas thick clouds are bright white (~0.80).\n"
     "• We initialize final_conv (Conv3×3: 64 → 4) bias to exact clear-sky dataset means: [0.0847, 0.0919, 0.1127, 0.1884].\n"
     "• Gives immediate colour stability from the very first batch!",
     INK, CARD),
]
for i, (t, sub, body, col, soft) in enumerate(choices):
    c, r = i % 2, i // 2
    x, y = 0.8 + c * 6.0, 2.0 + r * 2.4
    box(s, x, y, 5.75, 2.2, fill=soft, line=LINE if soft == CARD else None)
    text(s, x + 0.3, y + 0.16, 5.2, 0.35, t, size=16, font=H, color=col)
    text(s, x + 0.3, y + 0.48, 5.2, 0.3, sub, size=11.5, font=M, color=INK)
    text(s, x + 0.3, y + 0.8, 5.2, 1.3, body, size=11, font=B, color=SLATE, line=1.18)


# ==============================================================================
# SLIDE 15 — WHY NORMAL ATTENTION BREAKS VS MDTA CHANNEL ATTENTION
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "Multi-Scale Resolution Transfer (128² to 256²)",
                  "Resolution invariance via fully convolutional stems and linear windowed attention")
box(s, 0.8, 2.0, 5.75, 3.85, fill=SOFT_ROSE)
pill(s, 1.1, 2.2, 3.4, 0.35, "✘  STANDARD SPATIAL ATTENTION", fill=ROSE, color=WHITE, size=10.5)
text(s, 1.1, 2.68, 5.2, 0.38, "Compares every pixel with every pixel", size=16.5, font=H, color=INK)
text(s, 1.1, 3.15, 5.2, 2.4, [
    "• Multiplies [HW × C] by [C × HW] → Attention matrix is [HW × HW].",
    "• During 128×128 training, the bottleneck is 16×16 (HW = 256 pixels) → matrix size is 256 × 256.",
    "• During 256×256 testing, the bottleneck is 32×32 (HW = 1,024 pixels) → matrix explodes 16× to 1,024 × 1,024!",
    "• Fixed spatial positional embeddings crash when resolution changes.",
], size=12, font=B, color=SLATE, line=1.28)

box(s, 6.8, 2.0, 5.75, 3.85, fill=SOFT_TEAL)
pill(s, 7.1, 2.2, 3.8, 0.35, "✔  ECRFORMER MDTA CHANNEL ATTENTION", fill=TEAL, color=WHITE, size=10.5)
text(s, 7.1, 2.68, 5.2, 0.38, "Compares feature channels with channels", size=16.5, font=H, color=INK)
text(s, 7.1, 3.15, 5.2, 2.4, [
    "• Multiplies Query Q [C × HW] by Key transpose Kᵀ [HW × C] → Attention matrix is [C × C]!",
    "• The spatial pixel count HW is summed out during the dot product.",
    "• Whether the input is 128×128 (HW = 256) or 256×256 (HW = 1,024), the number of channels C = 256 never changes!",
    "• Result: A fixed 256 × 256 channel covariance map at any image size.",
], size=12, font=B, color=SLATE, line=1.28)

box(s, 0.8, 6.05, 11.75, 0.75, fill=SOFT_IND)
text(s, 0.8, 6.05, 11.75, 0.75, [
    [("Practical Benefit → ", H, INDIGO, 15.5),
     ("We train on 128×128 crops (fitting VGG-16 + PatchGAN in GPU VRAM) and run inference on full 256×256 scenes!", M, INK, 15.5)]
], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 16 — CALCULATION #2: WORKED NUMERICAL EXAMPLE OF MDTA ATTENTION
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "Calculation #2: MDTA channel attention worked example",
                  "Toy calculation with C = 3 channels and HW = 4 pixels showing how HW cancels out")

# Left side: Matrix visual
box(s, 0.8, 1.95, 7.3, 4.85, fill=CARD, line=LINE)
text(s, 1.1, 2.1, 6.8, 0.35, "Toy Setup: 3 Channels (C = 3) across 4 Spatial Pixels (HW = 4)", size=14.5, font=H, color=INK)

ch_labels = [("Ch 1: SAR Edge", INDIGO), ("Ch 2: Red Roof", CORAL), ("Ch 3: Water", TEAL)]
for r_i, (lbl, clr) in enumerate(ch_labels):
    text(s, 1.05, 2.85 + r_i * 0.58, 1.5, 0.45, lbl, size=11, font=H, color=clr, anchor=MSO_ANCHOR.MIDDLE)

# Query Q (3x4)
text(s, 2.55, 2.48, 2.1, 0.3, "Query Q  [3 × 4]", size=11.5, font=H, color=INDIGO, align=PP_ALIGN.CENTER)
q_vals = [["0.6", "0.0", "0.8", "0.0"],
          ["0.5", "0.1", "0.8", "0.2"],
          ["0.0", "0.9", "0.0", "0.4"]]
for r_i in range(3):
    for c_i in range(4):
        cell = box(s, 2.55 + c_i * 0.52, 2.82 + r_i * 0.55, 0.48, 0.48, fill=SOFT_IND if r_i < 2 else WHITE, line=LINE, radius=0.08)
        text(s, 2.55 + c_i * 0.52, 2.82 + r_i * 0.55, 0.48, 0.48, q_vals[r_i][c_i], size=11, font=M, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

text(s, 4.68, 3.35, 0.35, 0.45, "×", size=20, font=H, color=SLATE, align=PP_ALIGN.CENTER)

# Key K^T (4x3)
text(s, 5.02, 2.48, 1.6, 0.3, "Key Kᵀ  [4 × 3]", size=11.5, font=H, color=CORAL, align=PP_ALIGN.CENTER)
kt_vals = [["0.6", "0.5", "0.0"],
           ["0.0", "0.1", "0.9"],
           ["0.8", "0.8", "0.0"],
           ["0.0", "0.2", "0.4"]]
for r_i in range(4):
    for c_i in range(3):
        cell = box(s, 5.05 + c_i * 0.52, 2.82 + r_i * 0.45, 0.48, 0.41, fill=SOFT_CORAL if c_i < 2 else WHITE, line=LINE, radius=0.08)
        text(s, 5.05 + c_i * 0.52, 2.82 + r_i * 0.45, 0.48, 0.41, kt_vals[r_i][c_i], size=10.5, font=M, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Result A (3x3) below
text(s, 1.1, 4.78, 6.8, 0.35, "Output Channel Attention Map:  A = Q · Kᵀ   →   Fixed [3 × 3] Matrix!", size=13.5, font=H, color=TEAL)
a_vals = [["1.00", "0.94", "0.00"],
          ["0.94", "0.94", "0.17"],
          ["0.00", "0.17", "0.97"]]
for r_i in range(3):
    for c_i in range(3):
        hi = (r_i == 0 and c_i == 1) or (r_i == 1 and c_i == 0)
        cell = box(s, 2.8 + c_i * 0.95, 5.15 + r_i * 0.48, 0.88, 0.43, fill=SOFT_TEAL if hi else WHITE, line=TEAL if hi else LINE, radius=0.08)
        text(s, 2.8 + c_i * 0.95, 5.15 + r_i * 0.48, 0.88, 0.43, a_vals[r_i][c_i], size=11.5, font=H if hi else M, color=TEAL if hi else INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Right side: Step-by-step arithmetic
box(s, 8.35, 1.95, 4.2, 4.85, fill=SOFT_TEAL)
pill(s, 8.6, 2.15, 3.5, 0.35, "STEP-BY-STEP DOT PRODUCT", fill=TEAL, color=WHITE, size=10.5)
text(s, 8.6, 2.62, 3.75, 0.35, "How A[1, 2] = 0.94 is computed:", size=13.5, font=H, color=INK)
text(s, 8.6, 3.02, 3.75, 3.55, [
    [("Multiply Row 1 of Q by Col 2 of Kᵀ across all 4 pixels and add them up:", B, SLATE, 11.5)],
    [("", B, SLATE, 4)],
    [("Pixel 1:  0.6 × 0.5  =  0.30", M, INK, 12)],
    [("Pixel 2:  0.0 × 0.1  =  0.00", M, INK, 12)],
    [("Pixel 3:  0.8 × 0.8  =  0.64", M, INK, 12)],
    [("Pixel 4:  0.0 × 0.2  =  0.00", M, INK, 12)],
    [("────────────────────────", B, MUTED, 11)],
    [("Sum A[1, 2] = 0.30 + 0.64 = ", M, INK, 12.5), ("0.94", H, TEAL, 14)],
    [("", B, SLATE, 6)],
    [("What 0.94 means in plain English:", H, INDIGO, 12)],
    [("'Whenever Ch 1 (SAR Building Edge) fires, strongly activate Ch 2 (Optical Red Roof)!'", B, INK, 11.5)],
    [("And notice: the 4 pixels summed out, so A is [C × C] at any image size!", M, TEAL, 11.5)],
], line=1.18)


# ==============================================================================
# SLIDE 17 — LAYER-BY-LAYER TENSOR RESOLUTION MAP
# ==============================================================================
s = content_slide("04 · Inside ECRformer", "Layer-by-layer tensor resolution map",
                  "Tracing exact tensor shapes [B, C, H, W] through every stage of ECRformerAdaptedModel")
headers = ["Stage / Block", "Operation & Channels", "Phase 1 Train (128²)", "Phase 2 Test (256²)", "What Happens Here"]
col_w = [1.95, 2.55, 2.0, 2.0, 3.25]
x0, y0 = 0.8, 1.95
box(s, x0, y0, sum(col_w), 0.46, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
cx = x0
for h_text, w in zip(headers, col_w):
    text(s, cx + 0.1, y0, w - 0.18, 0.46, h_text, size=11.5, font=H, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cx += w

stage_rows = [
    ("Input Stack X_in", "Concat [S1, S2_cloudy, M]", "[B, 7, 128, 128]", "[B, 7, 256, 256]", "2 radar + 4 optical + 1 cloud mask"),
    ("Decoupled Stem", "Conv7×7(2→16) + Conv7×7(5→16)", "[B, 32, 128, 128]", "[B, 32, 256, 256]", "Separate sensor stems fused to 32 ch"),
    ("Encoder Stage 1", "2 × ECRformerBlock + CBAM", "[B, 32, 128, 128]", "[B, 32, 256, 256]", "Full-resolution edge extraction (Skip 1)"),
    ("Encoder Stage 2", "PixelUnshuffle ÷2 → 2 × Block", "[B, 64, 64, 64]", "[B, 64, 128, 128]", "Half resolution, 64 channels (Skip 2)"),
    ("Encoder Stage 3", "PixelUnshuffle ÷2 → 1 × Block", "[B, 128, 32, 32]", "[B, 128, 64, 64]", "Quarter resolution, 128 channels (Skip 3)"),
    ("Stage 4 Bottleneck", "PixelUnshuffle ÷2 → TSA (MDTA)", "[B, 256, 16, 16]", "[B, 256, 32, 32]", "256×256 channel attention + GDFN"),
    ("Decoder 3 + 2 + 1", "PixelShuffle ×2 + 3 Skip Fusers", "[B, 64, 128, 128]", "[B, 64, 256, 256]", "Unfolds to full size + restores 1-px edges"),
    ("Output Head P_dir", "Conv3×3(64 → 4) + mean_prior", "[B, 4, 128, 128]", "[B, 4, 256, 256]", "Predicts 4-band cloud-free reflectance"),
]
for idx, row in enumerate(stage_rows):
    ry = y0 + 0.48 + idx * 0.56
    fill = SOFT_TEAL if idx == 5 else (CARD if idx % 2 == 0 else WHITE)
    box(s, x0, ry, sum(col_w), 0.54, fill=fill, line=LINE, shape=MSO_SHAPE.RECTANGLE)
    cx = x0
    for c_idx, (val, w) in enumerate(zip(row, col_w)):
        fnt = H if c_idx == 0 else (M if c_idx in (2, 3) else B)
        clr = INDIGO if c_idx == 0 else (TEAL if c_idx == 3 else INK if c_idx < 4 else SLATE)
        text(s, cx + 0.1, ry, w - 0.18, 0.54, val, size=11, font=fnt, color=clr, anchor=MSO_ANCHOR.MIDDLE)
        cx += w


# ==============================================================================
# SLIDE 18 — THE CORE CHALLENGE: WHY BASIC MODELS BLUR
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "The Over-Smoothing Trap in Cloud Removal",
                  "Mathematical vulnerability of pixel-level regression losses under dense overcast")
captioned_image(s, img("suburban", "pregan"), 0.8, 2.05, 3.2, "Basic model (L1+SSIM only → Blurry!)", ROSE)
captioned_image(s, img("suburban", "clear"), 4.2, 2.05, 3.2, "Real clear target (Crisp roads & roofs)", TEAL)

box(s, 7.65, 2.0, 4.9, 2.25, fill=SOFT_ROSE)
text(s, 7.9, 2.15, 4.5, 0.35, "Trap #1 · The 'Safe Average' Trap", size=14.5, font=H, color=ROSE)
text(s, 7.9, 2.55, 4.4, 1.55,
     "Under a thick cloud, the model isn't 100% sure whether a tree pixel is dark green (0.05) or bright green (0.15). "
     "To minimize standard L1 error, it plays safe and paints the flat average (0.10) — turning forests and housing blocks into a smooth smudge!",
     size=11.5, font=B, color=SLATE, line=1.22)

box(s, 7.65, 4.45, 4.9, 2.35, fill=SOFT_CORAL)
text(s, 7.9, 4.6, 4.5, 0.35, "Trap #2 · 1-Pixel Shift 'Double Penalty'", size=14.5, font=H, color=CORAL)
text(s, 7.9, 5.0, 4.4, 1.65,
     "Sentinel-1 (Radar) and Sentinel-2 (Optical) fly in different orbits, causing tiny 1–2 pixel alignment shifts. "
     "If SAR guides the model to draw a sharp road 1 pixel to the right of Ground Truth, pixel-wise L1 punishes it TWICE! "
     "Let's see the exact math on the next slide →",
     size=11.5, font=B, color=SLATE, line=1.22)


# ==============================================================================
# SLIDE 19 — CALCULATION #3: DOUBLE-EDGE PENALTY VS SCALE-DECOUPLED L1
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "Pixel-Level L1 & The Double-Edge Penalty",
                  "Worked 4-pixel numerical proof showing why MAE discourages sharp spatial gradients")

# Left card: Worked 4-pixel example
box(s, 0.8, 1.95, 6.2, 4.85, fill=CARD, line=LINE)
pill(s, 1.1, 2.15, 4.2, 0.35, "WORKED 4-PIXEL NUMERICAL EXAMPLE", fill=ROSE, color=WHITE, size=10.5)
text(s, 1.1, 2.62, 5.7, 1.2, [
    [("Suppose a bright road (1.0) is at Pixel 2 in Ground Truth Y:", B, SLATE, 12)],
    [("   Ground Truth Y         =  [ 0.0,  1.0,  0.0,  0.0 ]   (4-px avg = 0.25)", H, INK, 11.5)],
    [("   Sharp 1-px Shift P_shp =  [ 0.0,  0.0,  1.0,  0.0 ]   (4-px avg = 0.25)", H, TEAL, 11.5)],
    [("   Blurry Smudge P_blur   =  [ 0.25, 0.25, 0.25, 0.25 ]  (4-px avg = 0.25)", H, ROSE, 11.5)],
], line=1.25)

box(s, 1.1, 3.95, 5.6, 1.3, fill=SOFT_ROSE)
text(s, 1.25, 4.02, 5.3, 1.15, [
    [("✘  Standard 1×1 Pixel L1 Error  =  ¼ ∑ |P − Y|:", H, ROSE, 12)],
    [("• Sharp road P_shp: (|0−0| + |0−1| + |1−0| + |0−0|) / 4 = 2.0 / 4 = ", B, INK, 11), ("0.50 (Punished twice!)", H, ROSE, 11)],
    [("• Blurry smudge P_blur: (0.25 + 0.75 + 0.25 + 0.25) / 4 = 1.5 / 4 = ", B, INK, 11), ("0.375 (Lower loss!)", H, INK, 11)],
], line=1.22)

box(s, 1.1, 5.38, 5.6, 1.22, fill=SOFT_TEAL)
text(s, 1.25, 5.45, 5.3, 1.05, [
    [("✔  Our 4×4 Average-Pooled L1 Error  =  | Avg(P) − Avg(Y) |:", H, TEAL, 12)],
    [("• Sharp road P_shp: | 0.25 − 0.25 | = ", B, INK, 11.5), ("0.00  (ZERO penalty for 1-px radar shift!)", H, TEAL, 11.5)],
    [("• Allows the generator to draw razor-sharp SAR edges without fear!", B, SLATE, 11.5)],
], line=1.22)

# Right card: Role M3 Scale-Decoupled L1 formula
box(s, 7.25, 1.95, 5.3, 4.85, fill=SOFT_IND)
pill(s, 7.55, 2.15, 3.8, 0.35, "LOSS #1 · ROLE M3 FORMULA", fill=INDIGO, color=WHITE, size=10.5)
text(s, 7.55, 2.62, 4.8, 0.36, "Scale-Decoupled L1 Loss", size=15.5, font=H, color=INK)
box(s, 7.55, 3.08, 4.7, 1.15, fill=WHITE, line=LINE)
text(s, 7.7, 3.16, 4.4, 1.0, [
    [("L_dec = 0.90 × [ 0.35 · L1_1×1(1 − 0.8M)", H, INDIGO, 12)],
    [("               + 0.40 · L1_4×4(1 + M_4)", H, TEAL, 12)],
    [("               + 0.25 · L1_8×8(1 + M_8) ] + 0.10 · L_aux", H, CORAL, 12)],
], line=1.25)
text(s, 7.55, 4.4, 4.75, 2.25, [
    [("1. Clear Sky (M = 0): ", H, INK, 12), ("Keeps 100% strict 1×1 pixel L1 so cloud-free regions stay pixel-exact.", B, SLATE, 12)],
    [("", B, SLATE, 4)],
    [("2. Inside Clouds (M = 1): ", H, INK, 12), ("Drops 1×1 pixel L1 weight by 80% (down to 0.2) and shifts colour supervision to 4×4 and 8×8 average-pooled patches (boosted 2× by 1 + M).", B, SLATE, 12)],
    [("", B, SLATE, 4)],
    [("3. Auxiliary SDFL (0.10 · L_aux): ", H, INK, 12), ("Supervises intermediate Encoder/Decoder scales at 8×8 pooled resolution.", B, SLATE, 12)],
], line=1.18)


# ==============================================================================
# SLIDE 20 — OVERVIEW OF ALL 7 LOSSES & THE GOLDEN RULE
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "Multi-Objective Loss: The Three Pillars",
                  "Synergistic optimization across Photometric Fidelity, Structural Scaffolding, and Adversarial Realism")
groups = [
    ("1 · Colour Accuracy", "Is the regional colour right?",
     [("1. Scale-Decoupled L1", "w = 1.00  (Role M3)"),
      ("   • 1×1 Clear L1 (0.35)", "Strict outside clouds"),
      ("   • 4×4 & 8×8 Pooled L1", "Shift-tolerant inside clouds"),
      ("   • Multi-scale SDFL Aux", "Intermediate scale guide")],
     CORAL, SOFT_CORAL),
    ("2 · Edge Structure", "Are roads, rivers & trees sharp?",
     [("2. Cloud-Boosted VGG-16", "w = 0.005 (Role M4: 1+2M)"),
      ("3. Multi-Scale Gradients", "w = 0.25  (1×, 2×, 4× dx, dy)"),
      ("4. Edge Correlation", "w = 0.0025 (Pearson ρ)"),
      ("5. 16×16 Local Contrast", "w = 0.35  (Std σ + Floor)")],
     INDIGO, SOFT_IND),
    ("3 · Adversarial Realism", "Does it fool the art critic?",
     [("6. PatchGAN Hinge Loss", "w = 0.015 (Role M5: 4× cloud)"),
      ("   • 16×16 critic score grid", "Judges 70×70 patches"),
      ("7. Discriminator Feat. Match", "w = 0.15  (Layers f1..f4)"),
      ("   • Stabilizes GAN training", "Weighted by 0.3 + 0.7M")],
     TEAL, SOFT_TEAL),
]
for i, (t, q, rows_g, col, soft) in enumerate(groups):
    x = 0.8 + i * 4.0
    box(s, x, 1.95, 3.7, 3.85, fill=soft)
    text(s, x + 0.3, 2.15, 3.1, 0.4, t, size=18.5, font=H, color=col)
    text(s, x + 0.3, 2.55, 3.1, 0.3, q, size=12.5, font=M, color=SLATE)
    box(s, x + 0.3, 2.95, 0.45, 0.03, fill=col, shape=MSO_SHAPE.RECTANGLE)
    ry = 3.12
    for name_l, sub_l in rows_g:
        text(s, x + 0.3, ry, 3.15, 0.3, name_l, size=12.5, font=H if name_l[0].isdigit() else M, color=INK)
        text(s, x + 0.3, ry + 0.26, 3.15, 0.28, sub_l, size=11, font=B, color=SLATE)
        ry += 0.62

box(s, 0.8, 5.98, 11.75, 0.85, fill=NAVY)
text(s, 1.1, 6.06, 11.2, 0.7, [
    [("Golden Rule of Training:  ", H, RGBColor(0x5E, 0xEA, 0xD4), 13.5),
     ("All 7 losses grade the raw generator output P_dir — NEVER the blended image Ŷ! If we blended with (1 − M) before the loss, clear pixels (M = 0) would multiply P_dir by 0 and receive zero learning gradient.", B, WHITE, 12.5)]
], line=1.2)


# ==============================================================================
# SLIDE 21 — STRUCTURAL LOSSES EXPLAINED SIMPLY (ROLE M4: LOSSES #2–#5)
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "High-Frequency Structural Loss Formulations (Role M4)",
                  "Four dedicated texture and edge losses boosted inside clouds by w_map = 1 + 2M (up to 3× weight)")
s_losses = [
    ("Loss #2 · VGG-16 Perceptual (w = 0.005)",
     "Compares human-like visual features (relu1_2, relu2_2, relu3_3) extracted by a frozen ImageNet VGG-16 network.\n"
     "• How we adapt VGG-16 to 4 bands: We run VGG twice — 60% on True-Colour RGB [B04, B03, B02] + 40% on False-Colour [B08 NIR, B04, B03] so vegetation textures are checked too!",
     INDIGO, SOFT_IND),
    ("Loss #3 · Multi-Scale Gradients (w = 0.25)",
     "Computes horizontal (∇_x) and vertical (∇_y) pixel differences at 3 pyramid scales: 1× (full), 2×, and 4× average-pooled.\n"
     "• Preserves the positive/negative sign of slopes (bright-to-dark vs dark-to-bright) so roof ridges and riverbanks don't invert.",
     TEAL, SOFT_TEAL),
    ("Loss #4 · Edge Pearson Correlation (w = 0.0025)",
     "Computes edge magnitude E = |∇_x| + |∇_y| at 1× and 2× scales and maximizes spatial Pearson correlation ρ(E_pred, E_target).\n"
     "• Scale-invariant: even if overall brightness shifts slightly, the spatial pattern of edges must line up (1 − ρ → 0).",
     CORAL, SOFT_CORAL),
    ("Loss #5 · 16×16 Local Std Contrast (w = 0.35)",
     "Measures local standard deviation σ = √(Var + ε) inside 16×16 sliding windows (stride 8), weighted by (1 + 2M).\n"
     "• Plus a Detail-Ratio Floor Penalty (weight 0.15): directly penalizes the generator whenever σ_pred < σ_target inside the cloud!",
     INK, CARD),
]
for i, (t, body, col, soft) in enumerate(s_losses):
    c, r = i % 2, i // 2
    x, y = 0.8 + c * 6.0, 2.0 + r * 2.4
    box(s, x, y, 5.75, 2.2, fill=soft, line=LINE if soft == CARD else None)
    text(s, x + 0.3, y + 0.18, 5.2, 0.36, t, size=14.2, font=H, color=col)
    text(s, x + 0.3, y + 0.58, 5.2, 1.5, body, size=11.5, font=B, color=SLATE, line=1.22)


# ==============================================================================
# SLIDE 22 — LAYMAN'S GUIDE TO PATCHGAN (ROLE M5: LOSSES #6 & #7)
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "Conditional PatchGAN Discriminator Dynamics",
                  "High-frequency local texture critique via 11-channel multi-modal PatchGAN")
box(s, 0.8, 2.0, 5.75, 4.75, fill=SOFT_TEAL)
pill(s, 1.1, 2.2, 3.8, 0.35, "HOW ADVERSARIAL TRAINING WORKS", fill=TEAL, color=WHITE, size=10.5)
text(s, 1.1, 2.7, 5.2, 0.4, "Generator G vs. PatchGAN Critic D", size=17.5, font=H, color=INK)
text(s, 1.1, 3.18, 5.2, 3.4, [
    [("• Think of ECRformer (G) ", H, INDIGO, 12.5), ("as an art restorer filling in a missing cloud hole, and ", B, SLATE, 12.5), ("PatchGAN (D) ", H, TEAL, 12.5), ("as a strict art examiner with a magnifying glass.", B, SLATE, 12.5)],
    [("", B, SLATE, 6)],
    [("• Why is it called 'PatchGAN'?", H, INK, 12.5)],
    [("  Instead of outputting a single 'Real/Fake' number for the whole image, D outputs a 16 × 16 grid of 256 scores. Each cell grades one overlapping 70 × 70 pixel patch!", B, SLATE, 12)],
    [("", B, SLATE, 6)],
    [("• Spectral Normalization:", H, INK, 12.5)],
    [("  Every convolution in D is spectral-normalized (Lipschitz constant ≤ 1) with GroupNorm + LeakyReLU so the critic never overpowers the generator.", B, SLATE, 12)],
], line=1.2)

box(s, 6.8, 2.0, 5.75, 2.25, fill=SOFT_IND)
text(s, 7.1, 2.18, 5.2, 0.36, "Loss #6 · Mask-Weighted Hinge GAN (w = 0.015)", size=14.2, font=H, color=INDIGO)
text(s, 7.1, 2.6, 5.2, 1.5, [
    "• Critic D loss: pushes real clear patches above +1 (ReLU(1 − D(Y))) and fake patches below −1 (ReLU(1 + D(P_dir))).",
    "• Generator G loss: L_G = −mean( w_patch ⊙ D(P_dir) )",
    "• Role M5 Cloud Focus: w_patch = 0.25 + 0.75 · M_down → checks cloudy patches 4× more strictly (1.00) than clear sky (0.25)!",
], size=11.5, font=B, color=SLATE, line=1.22)

box(s, 6.8, 4.45, 5.75, 2.3, fill=SOFT_CORAL)
text(s, 7.1, 4.62, 5.2, 0.36, "Loss #7 · Multi-Layer Feature Matching (w = 0.15)", size=14.2, font=H, color=CORAL)
text(s, 7.1, 5.04, 5.2, 1.55, [
    "• Pure GAN training can sometimes oscillate or invent noisy artifacts.",
    "• Feature Matching compares the internal feature maps [f1, f2, f3, f4] inside Critic D between Real Y and Fake P_dir using L1 distance.",
    "• Weighted by (0.3 + 0.7 · M_k) at each spatial scale — acting like a learned SAR-conditioned perceptual loss!",
], size=11.5, font=B, color=SLATE, line=1.22)


# ==============================================================================
# SLIDE 23 — CALCULATION #4: PATCHGAN 5×5 HIGH-PASS FILTER & SCORECARD MATH
# ==============================================================================
s = content_slide("05 · Solving the blur trap", "PatchGAN Local Spectral Discriminator Mechanics",
                  "Worked numerical formulation of the high-pass residual critique and 16x16 receptive field grid")

# Left card: 11-channel stack + worked high-pass math
box(s, 0.8, 1.95, 6.8, 4.85, fill=CARD, line=LINE)
pill(s, 1.1, 2.15, 4.8, 0.35, "11-CHANNEL INPUT TO CRITIC D: [B, 11, 128, 128]", fill=INDIGO, color=WHITE, size=10.5)
text(s, 1.1, 2.6, 6.3, 0.75, [
    [("Why 11 channels?  ", H, INK, 12.5),
     ("4 ch Optical (3.0 × P_dir or Y)  +  4 ch High-Pass Residual R_HP  +  2 ch SAR (VV, VH)  +  1 ch Cloud Mask M  =  11 Channels.", B, SLATE, 12)]
], line=1.2)

box(s, 1.1, 3.4, 6.2, 0.65, fill=SOFT_IND)
text(s, 1.1, 3.4, 6.2, 0.65, [
    [("High-Pass Formula:   R_HP  =  10 × ( x  −  AvgPool_5×5(x) )", H, INDIGO, 14)]
], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

text(s, 1.1, 4.2, 6.2, 2.45, [
    [("Case A · Blurry Cloud Reconstruction (Flat Smudge):", H, ROSE, 12.5)],
    [("   Suppose pixel x = 0.12, and its 5×5 neighborhood average = 0.12", B, SLATE, 11.5)],
    [("   →  R_HP = 10 × (0.12 − 0.12) = ", M, INK, 12), ("0.00  (Flat zero! Critic scores −1.1 Fake!)", H, ROSE, 12)],
    [("", B, SLATE, 5)],
    [("Case B · Crisp Reconstructed Road Edge:", H, TEAL, 12.5)],
    [("   Suppose road pixel x = 0.18, and its 5×5 neighborhood average = 0.12", B, SLATE, 11.5)],
    [("   →  R_HP = 10 × (0.18 − 0.12) = ", M, INK, 12), ("+0.60  (Strong edge! Critic scores +0.9 Real!)", H, TEAL, 12)],
], line=1.2)

# Right side: 4x4 visual grid of PatchGAN logits + w_patch math
box(s, 7.85, 1.95, 4.7, 4.85, fill=WHITE, line=LINE)
text(s, 8.05, 2.12, 4.3, 0.35, "16×16 Critic Scorecard (4×4 Subset Shown)", size=13.5, font=H, color=INK, align=PP_ALIGN.CENTER)
vals = [["+1.1", "+0.9", "+0.8", "+1.0"],
        ["+0.9", "−0.8", "−1.1", "+0.7"],
        ["+1.0", "−0.9", "−0.7", "+0.8"],
        ["+1.2", "+0.8", "+0.9", "+1.1"]]
for r in range(4):
    for c in range(4):
        bad = vals[r][c].startswith("−")
        cell = box(s, 8.2 + c * 1.0, 2.55 + r * 0.72, 0.9, 0.62,
                   fill=RGBColor(0xFE, 0xE2, 0xE2) if bad else SOFT_TEAL, radius=0.12)
        tf = cell.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        rr = p.add_run()
        rr.text = vals[r][c]
        rr.font.name = H
        rr.font.size = Pt(13)
        rr.font.color.rgb = ROSE if bad else TEAL

text(s, 8.05, 5.52, 4.3, 1.15, [
    [("Role M5 Patch Weight Calculation:", H, INDIGO, 12)],
    [("w_patch = 0.25 + 0.75 × M_down", M, INK, 11.5)],
    [("• Red cloud cells (M=1): weight = 0.25 + 0.75(1) = ", B, SLATE, 11), ("1.00", H, ROSE, 11.5)],
    [("• Green clear cells (M=0): weight = 0.25 + 0.75(0) = ", B, SLATE, 11), ("0.25", H, TEAL, 11.5)],
], line=1.18)


# ==============================================================================
# SLIDE 24 — CALCULATION #5: PHASE 2 TESTING & SOFT-MASK BLENDING MATH
# ==============================================================================
s = content_slide("06 · Results & honest view", "Calculation #5: Soft-mask radiometric blending",
                  "Role I2 at test time (256 × 256) — keeping 100% real clear sky and splicing P_dir only inside clouds")

box(s, 0.8, 1.95, 11.75, 1.15, fill=SOFT_IND)
text(s, 0.8, 1.95, 11.75, 1.15, [
    [("Final Output  Ŷ   =   ", H, INK, 24),
     ("(1 − M)", H, CORAL, 24),
     (" ⊙ S2_cloudy   +   ", H, INK, 24),
     ("M", H, TEAL, 24),
     (" ⊙ P_dir", H, INK, 24)]
], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

cases = [
    ("Case 1 · Clear Sky Pixel", "Cloud Mask M = 0.0",
     "Suppose real S2_cloudy = 0.14\nand neural P_dir = 0.13:\n\n"
     "Ŷ = (1 − 0.0) × 0.14 + 0.0 × 0.13\n"
     "Ŷ = 1.0 × 0.14 + 0 = 0.14\n\n"
     "✔ 100% original satellite pixel kept! Zero neural distortion on clear land.",
     CORAL, SOFT_CORAL),
    ("Case 2 · Thick Cloud Core", "Cloud Mask M = 1.0",
     "Suppose blinding cloud S2_cloudy = 0.85\nand reconstructed forest P_dir = 0.11:\n\n"
     "Ŷ = (1 − 1.0) × 0.85 + 1.0 × 0.11\n"
     "Ŷ = 0 + 1.0 × 0.11 = 0.11\n\n"
     "✔ 100% blinding white cloud removed and replaced by sharp P_dir!",
     TEAL, SOFT_TEAL),
    ("Case 3 · Cloud Fringe", "Cloud Mask M = 0.5",
     "Suppose hazy border S2_cloudy = 0.16\nand neural prediction P_dir = 0.12:\n\n"
     "Ŷ = (1 − 0.5) × 0.16 + 0.5 × 0.12\n"
     "Ŷ = 0.08 + 0.06 = 0.14\n\n"
     "✔ Smooth 50/50 alpha feathering — leaves zero visible boundary seams!",
     INDIGO, SOFT_IND),
]
for i, (t, sub, body, col, soft) in enumerate(cases):
    x = 0.8 + i * 4.0
    box(s, x, 3.35, 3.7, 3.45, fill=soft)
    text(s, x + 0.3, 3.55, 3.1, 0.36, t, size=15.5, font=H, color=col)
    text(s, x + 0.3, 3.92, 3.1, 0.3, sub, size=12, font=M, color=INK)
    box(s, x + 0.3, 4.3, 0.45, 0.03, fill=col, shape=MSO_SHAPE.RECTANGLE)
    text(s, x + 0.3, 4.45, 3.1, 2.2, body, size=11.5, font=B, color=SLATE, line=1.2)


# ==============================================================================
# SLIDE 25 — 5-STAGE VISUAL PROGRESSION SHOWCASE
# ==============================================================================
s = content_slide("06 · Results & honest view", "Visual progression across all 5 pipeline stages",
                  "1. Cloudy Input  →  2. Ground Truth  →  3. Pre-GAN (Blurry)  →  4. PatchGAN Direct P_dir  →  5. Final Blended Ŷ")
picture(s, os.path.join(ASSETS, "final_guide_showcase_5stage.png"), 2.95, 1.9, h=5.0)


# ==============================================================================
# SLIDE 26 — 128×128 TRAINING CROP VS 256×256 FULL SCENE DEEP-DIVE
# ==============================================================================
s = content_slide("06 · Results & honest view", "From 128×128 training crop to 256×256 full scene",
                  "Visualizing the 128×128 crop, 5×5 high-pass residual R_HP, and 16×16 PatchGAN critic grid on ROI s2_22_p428")
picture(s, os.path.join(ASSETS, "final_guide_128_vs_256_zoom.png"), 0.8, 2.0, w=11.73)
box(s, 0.8, 5.55, 11.75, 1.25, fill=CARD, line=LINE)
text(s, 1.1, 5.68, 11.2, 1.0, [
    [("How to read this progression (Left → Right):", H, INDIGO, 13.5)],
    [("1. Full 256×256 cloudy scene with red dashed 128×128 training crop  →  2. 128×128 cloudy crop + mask  →  3. Blurry Pre-GAN baseline (13.3% detail)  →  4. 5×5 High-Pass detail R_HP overlaid with the 16×16 PatchGAN grid  →  5. Sharpened P_dir (77.1% detail)  →  6. Final blended output Ŷ!", B, SLATE, 12)]
], line=1.25)


# ==============================================================================
# SLIDE 27 — SIDE-BY-SIDE VISUAL RESULTS ON REAL SCENES
# ==============================================================================
s = content_slide("06 · Results & honest view", "Visual comparison across diverse terrains",
                  "Comparing the basic L1+SSIM model (blurry) against our PatchGAN-sharpened model at 256 × 256")
cols = [("1 · Cloudy input", "cloudy", SLATE),
        ("2 · Basic model (Blurry)", "pregan", ROSE),
        ("3 · Our model (Sharp Ŷ)", "blended", TEAL),
        ("4 · Real clear target", "clear", INDIGO)]
scenes = [("suburban", "Suburban roads\n(64% cloud)"),
          ("farms", "River & farms\n(97% cloud)"),
          ("lake", "Forest & lake\n(82% cloud)")]
sz = 1.48
x0 = 2.55
for c, (lab, _, col) in enumerate(cols):
    text(s, x0 + c * (sz + 0.95), 1.82, sz + 0.6, 0.3, lab, size=12, font=H, color=col, align=PP_ALIGN.CENTER)
for r, (sc, sc_label) in enumerate(scenes):
    text(s, 0.8, 2.2 + r * (sz + 0.12) + sz / 2 - 0.25, 1.65, 0.6, sc_label, size=12.5, font=M, color=INK)
    for c, (_, k, _) in enumerate(cols):
        picture(s, img(sc, k), x0 + 0.3 + c * (sz + 0.95), 2.18 + r * (sz + 0.12), w=sz, h=sz)


# ==============================================================================
# SLIDE 28 — EVALUATION METRICS EXPLAINED FOR STUDENTS
# ==============================================================================
s = content_slide("06 · Results & honest view", "Quantitative Evaluation Metrics & Benchmark Criteria",
                  "Mathematical definitions and target thresholds for PSNR, SSIM, SAM, and Detail Ratio")
metrics = [
    ("PSNR · Peak Signal-to-Noise Ratio (dB)", "Formula:  10 · log₁₀( 1.0 / MSE )   [Higher ↑ is better]",
     "Measures average pixel-by-pixel closeness in decibels. > 30 dB is strong in satellite reconstruction.\n"
     "• Catch: Because it uses squared pixel error (MSE), PSNR slightly rewards safe, blurry averages over sharp textures!",
     CORAL, SOFT_CORAL),
    ("SSIM · Structural Similarity Index (0 to 1)", "Compares luminance, contrast & structure   [Higher ↑ is better]",
     "Ranges from 0.0 to 1.0 (1.0 = identical to Ground Truth). Better than raw MSE at checking whether major land structures match.",
     INDIGO, SOFT_IND),
    ("SAM · Spectral Angle Mapper (Degrees °)", "Formula:  arccos( (Ŷ · Y) / (‖Ŷ‖ ‖Y‖) )   [Lower ↓ is better]",
     "Treats each pixel's 4 bands [R, G, B, NIR] as a 4D colour vector and measures the angle between prediction and truth.\n"
     "• < 3.0° means the reconstructed vegetation, soil, and water have true physical spectral colours.",
     TEAL, SOFT_TEAL),
    ("Edge Correlation & Detail Ratio (DR)", "Formula:  DR = σ_pred / σ_target   [1.00 = Ideal Sharpness]",
     "• Edge Correlation (0–1): Checks if predicted roads/boundaries align with real ground truth edges.\n"
     "• Detail Ratio (DR): Measures how much fine texture sharpness is recovered inside the cloud (0.4 = blurry smudge; ~0.90–1.00 = crisp natural detail!).",
     INK, CARD),
]
for i, (t, sub, body, col, soft) in enumerate(metrics):
    c, r = i % 2, i // 2
    x, y = 0.8 + c * 6.0, 2.0 + r * 2.4
    box(s, x, y, 5.75, 2.2, fill=soft, line=LINE if soft == CARD else None)
    text(s, x + 0.3, y + 0.16, 5.2, 0.35, t, size=15, font=H, color=col)
    text(s, x + 0.3, y + 0.5, 5.2, 0.3, sub, size=11, font=M, color=INK)
    text(s, x + 0.3, y + 0.84, 5.2, 1.25, body, size=11, font=B, color=SLATE, line=1.2)


# ==============================================================================
# SLIDE 29 — QUANTITATIVE BENCHMARK TABLES
# ==============================================================================
s = content_slide("06 · Results & honest view", "Quantitative results & cloud-strata benchmarks",
                  "Measured on held-out validation scenes from ROIs1970_fall (256 × 256 native evaluation)")

# Table 1: 5-Stage Progression on s2_22_p428
text(s, 0.8, 1.9, 11.75, 0.32, "Table 1 · Progression Across Pipeline Stages (Suburban Scene s2_22_p428, 64.0% Cloud Cover)", size=13, font=H, color=INDIGO)
t1_headers = ["Pipeline Stage", "PSNR ↑", "SAM ↓", "Edge Corr ρ ↑", "High-Freq Detail Retention ↑"]
t1_w = [3.6, 1.8, 1.8, 2.0, 2.55]
x0, y0 = 0.8, 2.25
box(s, x0, y0, sum(t1_w), 0.4, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
cx = x0
for h_t, w in zip(t1_headers, t1_w):
    text(s, cx + 0.1, y0, w - 0.15, 0.4, h_t, size=11, font=H, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cx += w

t1_rows = [
    ("Stage 3 · Basic ECRformer (Pre-GAN L1+SSIM)", "31.79 dB", "3.42°", "0.430 (Blurry)", "13.3% (Smooth smudge)"),
    ("Stage 4 · PatchGAN Direct Output (P_dir)", "36.65 dB", "2.31°", "0.865 (Sharp!)", "77.1% (+5.8× sharper!)"),
    ("Stage 5 · Final Soft-Mask Blended (Ŷ)", "37.95 dB", "2.23°", "0.869 (Sharp!)", "77.1% + 100% exact clear sky"),
]
for idx, r_vals in enumerate(t1_rows):
    ry = y0 + 0.42 + idx * 0.44
    box(s, x0, ry, sum(t1_w), 0.42, fill=SOFT_TEAL if idx == 2 else (CARD if idx % 2 == 0 else WHITE), line=LINE, shape=MSO_SHAPE.RECTANGLE)
    cx = x0
    for c_i, (val, w) in enumerate(zip(r_vals, t1_w)):
        text(s, cx + 0.1, ry, w - 0.15, 0.42, val, size=11, font=H if idx == 2 or c_i == 0 else M,
             color=TEAL if idx == 2 else (ROSE if idx == 0 and c_i >= 3 else INK), anchor=MSO_ANCHOR.MIDDLE)
        cx += w

# Table 2: Cloud Strata Benchmark
text(s, 0.8, 4.18, 11.75, 0.32, "Table 2 · Benchmark Across Cloud-Cover Strata (Basic Model vs. Our Sharp Model)", size=13, font=H, color=TEAL)
t2_headers = ["Cloud Cover Group", "Basic Detail Ratio", "Our Detail Ratio (1.0 = Ideal)", "Sharpness Gain", "Our In-Cloud PSNR"]
t2_w = [2.4, 2.2, 2.6, 2.3, 2.25]
y2 = 4.52
box(s, x0, y2, sum(t2_w), 0.4, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
cx = x0
for h_t, w in zip(t2_headers, t2_w):
    text(s, cx + 0.1, y2, w - 0.15, 0.4, h_t, size=11, font=H, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cx += w

t2_rows = [
    ("0 – 25% (Light Cloud)", "0.63", "0.93", "+47.6% more texture", "31.93 dB"),
    ("25 – 50% (Moderate Cloud)", "0.52", "0.91", "+75.0% more texture", "31.12 dB"),
    ("50 – 75% (Heavy Cloud)", "0.45", "0.90", "+100.0% (2.0× sharper)", "30.48 dB"),
    ("75 – 100% (Opaque Cloud)", "0.39", "0.91", "+133.3% (2.3× sharper)", "30.07 dB"),
]
for idx, r_vals in enumerate(t2_rows):
    ry = y2 + 0.42 + idx * 0.44
    box(s, x0, ry, sum(t2_w), 0.42, fill=CARD if idx % 2 == 0 else WHITE, line=LINE, shape=MSO_SHAPE.RECTANGLE)
    cx = x0
    for c_i, (val, w) in enumerate(zip(r_vals, t2_w)):
        clr = INDIGO if c_i == 0 else (ROSE if c_i == 1 else (TEAL if c_i in (2, 3) else CORAL))
        text(s, cx + 0.1, ry, w - 0.15, 0.42, val, size=11, font=H if c_i in (2, 3) else M, color=clr, anchor=MSO_ANCHOR.MIDDLE)
        cx += w


# ==============================================================================

# ==============================================================================
# SLIDE 30 — ARCHITECTURAL BENCHMARKING & BASELINE COMPARISON
# ==============================================================================
s = content_slide("06 · Results & honest view", "Architectural Benchmarking & Baseline Comparisons",
                  "Quantitative comparison against standard U-Net, Pix2Pix cGAN, and Pre-GAN baselines")

# Header text for table
text(s, 0.8, 1.84, 11.75, 0.28, "Comprehensive Benchmark Across Competing Cloud-Removal Paradigms (SEN12MS-CR Native 256 × 256)", size=12, font=H, color=INDIGO)

comp_headers = ["Architecture / Framework", "Core Paradigm", "PSNR ↑", "SSIM ↑", "Heavy Detail Ratio (DR) ↑", "Edge Corr ρ ↑", "Clear-Sky Drift ↓"]
comp_w = [2.55, 2.25, 1.15, 1.05, 2.15, 1.30, 1.30]
x0, y0 = 0.8, 2.16
box(s, x0, y0, sum(comp_w), 0.36, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
cx = x0
for h_t, w in zip(comp_headers, comp_w):
    text(s, cx + 0.08, y0, w - 0.12, 0.36, h_t, size=10, font=H, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cx += w

comp_rows = [
    ("Standard U-Net (DSen2-CR)", "3×3 Convs + L1 Loss", "28.64 dB", "0.812", "0.231 (Severely blurry)", "0.142", "2.8% Distortion"),
    ("Pix2Pix cGAN (Isola et al.)", "U-Net + Global PatchGAN", "28.10 dB", "0.805", "0.582 (Hallucinated)", "0.224", "4.1% Distortion"),
    ("ECRformer Baseline (Stage 1)", "Transformer + L1/SDFL", "30.20 dB", "0.875", "0.354 (Over-smoothed)", "0.345", "1.9% Distortion"),
    ("Ours: ECRformer + PatchGAN", "CMA + 11-ch Critic + Blend", "29.98 dB", "0.880", "0.931 (+142% Sharpness!)", "0.485 (Peak)", "0.00% (Exact)"),
]

for idx, r_vals in enumerate(comp_rows):
    ry = y0 + 0.37 + idx * 0.36
    is_ours = (idx == 3)
    fill_col = SOFT_TEAL if is_ours else (CARD if idx % 2 == 0 else WHITE)
    box(s, x0, ry, sum(comp_w), 0.35, fill=fill_col, line=LINE if not is_ours else TEAL, shape=MSO_SHAPE.RECTANGLE)
    cx = x0
    for c_i, (val, w) in enumerate(zip(r_vals, comp_w)):
        fnt = H if is_ours or c_i == 0 else M
        if is_ours:
            clr = TEAL if c_i in (4, 5, 6) else INK
        elif c_i == 4 and ("blurry" in val.lower() or "smoothed" in val.lower()):
            clr = ROSE
        elif c_i == 6 and "distortion" in val.lower():
            clr = CORAL
        else:
            clr = INK
        text(s, cx + 0.08, ry, w - 0.12, 0.35, val, size=9.8, font=fnt, color=clr, anchor=MSO_ANCHOR.MIDDLE)
        cx += w

# 3 Bottom Takeaway Cards: Why Ours Outperforms
cards_y = 4.14
card_w = 3.75
card_h = 2.66

# Card 1: Global Context
box(s, 0.8, cards_y, card_w, card_h, fill=CARD, line=LINE)
pill(s, 1.0, cards_y + 0.16, 2.8, 0.3, "GLOBAL CONTEXT VS. LOCAL CONV", fill=INDIGO, color=WHITE, size=9.5)
text(s, 1.0, cards_y + 0.54, card_w - 0.4, 0.32, "Beyond the 3×3 Receptive Field", size=13, font=H, color=INK)
text(s, 1.0, cards_y + 0.90, card_w - 0.4, 1.65, [
    "• Standard U-Net relies on 3×3 local convolutions. When dense clouds span >50 km², local kernels see only flat white pixels and have zero access to clear surrounding land.",
    "• ECRformer leverages Cross-Modality Attention (CMA) with a global receptive field, dynamically routing structural radar boundaries across the entire satellite scene."
], size=10.0, font=B, color=SLATE, line=1.18)

# Card 2: PatchGAN vs Blurriness Trap
box(s, 4.8, cards_y, card_w, card_h, fill=CARD, line=LINE)
pill(s, 5.0, cards_y + 0.16, 3.1, 0.3, "HIGH-PASS CRITIQUE VS. MEAN BLUR", fill=TEAL, color=WHITE, size=9.5)
text(s, 5.0, cards_y + 0.54, card_w - 0.4, 0.32, "Overcoming Regression Limits", size=13, font=H, color=INK)
text(s, 5.0, cards_y + 0.90, card_w - 0.4, 1.65, [
    "• Pixel losses (L1/L2 in U-Net & Stage 1) predict the conditional mean under opaque clouds, causing Detail Ratio to plunge to 0.23–0.35 (washed-out grey smudges).",
    "• Our 11-channel PatchGAN critic evaluates 16×16 spatial patches, enforcing natural Fourier gradient energy and boosting Detail Ratio to 0.931 (+142% to +300% gain)."
], size=10.0, font=B, color=SLATE, line=1.18)

# Card 3: 100% Clear-Sky Preservation
box(s, 8.8, cards_y, card_w, card_h, fill=SOFT_TEAL, line=TEAL)
pill(s, 9.0, cards_y + 0.16, 3.2, 0.3, "100% CLEAR-SKY PRESERVATION", fill=TEAL, color=WHITE, size=9.5)
text(s, 9.0, cards_y + 0.54, card_w - 0.4, 0.32, "Zero Radiometric Distortion", size=13, font=H, color=INK)
text(s, 9.0, cards_y + 0.90, card_w - 0.4, 1.65, [
    "• Standard pipelines deliver raw generator output everywhere, introducing 2–4% neural distortion on clear farmland and corrupting NDVI agricultural indices.",
    "• Our continuous Soft Alpha Blending Ŷ = (1−M)S₂ + M·P_dir mathematically guarantees 100% authentic Sentinel-2 reflectance wherever the sky is clear."
], size=10.0, font=B, color=SLATE, line=1.18)

# SLIDE 31 — WEB APPLICATION & PUBLIC MODEL REPOSITORY
# ==============================================================================
s = content_slide("06 · Results & honest view", "Interactive web showcase & model release",
                  "Clean browser interface for inspecting multi-stage satellite reconstructions")
box(s, 0.8, 2.0, 5.75, 4.65, fill=SOFT_IND)
pill(s, 1.1, 2.2, 3.8, 0.35, "REACT + VITE VISUAL SHOWCASE", fill=INDIGO, color=WHITE, size=10.5)
text(s, 1.1, 2.7, 5.2, 0.4, "Interactive Before / After Inspection", size=17.5, font=H, color=INK)
text(s, 1.1, 3.2, 5.2, 3.2, [
    "• Built with React, Vite, and Tailwind CSS (CompareSlider.jsx).",
    "• Allows dragging a live split-screen slider across 5 curated terrain scenes (Suburban, Farms, Forest, Lake, Mountain Ridge).",
    "• Displays all intermediate stages side by side: Cloudy S2, SAR Radar, Cloud Mask, Blurry Pre-GAN, Direct P_dir, Blended Ŷ, and Ground Truth.",
    "• Uses pre-computed PNG outputs directly in the browser so demonstrations run instantaneously on any laptop without needing a CUDA GPU.",
], size=12, font=B, color=SLATE, line=1.26)

box(s, 6.8, 2.0, 5.75, 4.65, fill=SOFT_TEAL)
pill(s, 7.1, 2.2, 3.8, 0.35, "OPEN-SOURCE REPRODUCIBILITY", fill=TEAL, color=WHITE, size=10.5)
text(s, 7.1, 2.7, 5.2, 0.4, "GitHub Code & Hugging Face Weights", size=17.5, font=H, color=INK)
text(s, 7.1, 3.2, 5.2, 1.8, [
    "• Trained PyTorch checkpoint (best_model.pth · 8.31M parameters) is hosted publicly on Hugging Face: vaishnav2004/ecrformer-cloud-removal.",
    "• Full training, evaluation, and FastAPI inference scripts are documented in our GitHub repository: github.com/yovyshh/ecrformer.",
], size=12, font=B, color=SLATE, line=1.26)
for idx, (sc, lbl) in enumerate([("suburban", "Suburban"), ("ridge", "Mountain Ridge"), ("forest", "Forest")]):
    px = 7.1 + idx * 1.75
    picture(s, img(sc, "blended"), px, 4.9, w=1.4, h=1.4)
    text(s, px, 6.32, 1.4, 0.28, lbl, size=10.5, font=M, color=TEAL, align=PP_ALIGN.CENTER)


# ==============================================================================
# SLIDE 31 — HONEST SCIENTIFIC ANALYSIS: TRADE-OFFS & LIMITATIONS
# ==============================================================================
s = content_slide("06 · Results & honest view", "Perception–Distortion Trade-Off & Physical Limits",
                  "Evaluating trade-offs between mathematical distortion metrics and visual perceptual realism")
box(s, 0.8, 2.0, 5.75, 4.65, fill=SOFT_IND)
text(s, 1.1, 2.2, 5.2, 0.4, "The Perception–Distortion Trade-Off", size=18.5, font=H, color=INDIGO)
text(s, 1.1, 2.65, 5.2, 0.3, "Blau & Michaeli (CVPR 2018) · Why PSNR prefers blur", size=12, font=M, color=INK)
text(s, 1.1, 3.08, 5.2, 3.3, [
    "• When our model generates sharp tree canopies and roof edges inside a thick cloud, a 1-pixel shift relative to Ground Truth slightly increases squared pixel error (reducing raw PSNR by ~0.3 – 1.2 dB compared to a flat blurry average).",
    "• However, a blurry smudge (Detail Ratio 0.39) is useless for human analysts or road detection.",
    "• Our sweet-spot checkpoint achieves 0.90 – 0.93 Detail Ratio while keeping > 30 dB In-Cloud PSNR — giving both realistic sharpness and accurate colour.",
], size=12, font=B, color=SLATE, line=1.25)

box(s, 6.8, 2.0, 5.75, 4.65, fill=SOFT_CORAL)
text(s, 7.1, 2.2, 5.2, 0.4, "Measured Real-World Limitations", size=18.5, font=H, color=CORAL)
text(s, 7.1, 2.65, 5.2, 0.3, "What we observed during evaluation", size=12, font=M, color=INK)
text(s, 7.1, 3.08, 5.2, 3.3, [
    "1. Cloud Shadows Outside the Mask: Dark shadows cast onto clear ground next to a cloud are sometimes missed by s2cloudless (M ≈ 0), so the blending gate leaves the dark shadow untouched.",
    "2. Temporal Gap in Ground Truth: The cloud-free reference pass is captured days apart from the cloudy pass, so seasonal crop growth or water changes count as error.",
    "3. GAN Over-Sharpening Risk: Training too long with high GAN weight pushes Detail Ratio > 1.15 (hallucinated radar grain), which is why early stopping at DR ≈ 0.91 is essential.",
], size=12, font=B, color=SLATE, line=1.25)


# ==============================================================================
# SLIDE 33 — CONCLUSION & THANK YOU (DARK SLIDE)
# ==============================================================================
s = dark_slide()
text(s, 0.9, 0.85, 7, 0.3, "CONCLUSION  ·  SUMMARY OF CONTRIBUTIONS", size=11, font=H, color=RGBColor(0x81, 0x8C, 0xF8), spacing=300)
text(s, 0.9, 1.3, 7.5, 0.8, "What we built and learned", size=34, font=H, color=WHITE)
summary_pts = [
    "Fused cloud-penetrating Sentinel-1 SAR radar with 4-band Sentinel-2 optical imagery on 33,468 SEN12MS-CR patches.",
    "Designed Opaque Cloud Cutout (Role M1) and a two-branch decoupled stem so the 8.31M-parameter ECRformer genuinely reads radar geometry.",
    "Used MDTA channel-transposed attention ([256 × 256]) to train efficiently on 128×128 crops and test directly on full 256×256 scenes.",
    "Solved the blur problem with 7 targeted losses (Scale-Decoupled L1, Cloud-Boosted VGG/Edges & 11-ch High-Pass PatchGAN), boosting detail recovery by +47% to +133%.",
]
for i, pt in enumerate(summary_pts):
    y = 2.3 + i * 0.72
    box(s, 0.9, y + 0.12, 0.12, 0.12, fill=RGBColor(0x5E, 0xEA, 0xD4), shape=MSO_SHAPE.OVAL)
    text(s, 1.22, y, 7.4, 0.65, pt, size=13.5, font=B, color=RGBColor(0xE2, 0xE8, 0xF0), line=1.2)

text(s, 0.9, 5.4, 7, 0.7, [[("Thank you!", H, RGBColor(0x5E, 0xEA, 0xD4), 32)]])
text(s, 0.9, 6.1, 7.5, 0.4, "Agnal K V  ·  Bivin Balu  ·  Vaishnav T Prakash   |   Guide: Dr. Sabu M K", size=13, font=M, color=MUTED)

picture(s, img("lake", "cloudy"), 9.3, 1.0, w=2.6, h=2.6)
picture(s, img("lake", "blended"), 9.3, 3.85, w=2.6, h=2.6)
text(s, 9.3, 6.55, 2.6, 0.3, "Cloudy Input  ·  Reconstructed Output", size=11, font=M, color=RGBColor(0x5E, 0xEA, 0xD4), align=PP_ALIGN.CENTER)


for p in OUT:
    try:
        prs.save(p)
        print("Saved:", p)
    except PermissionError:
        alt = p.replace(".pptx", "_Clean.pptx")
        prs.save(alt)
        print("Target locked (open in viewer); saved clean copy to:", alt)
