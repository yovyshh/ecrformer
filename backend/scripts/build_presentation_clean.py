"""Clean, minimal, stylish project presentation (Poppins typography, low text density)."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE = r"c:\Users\Windows 11 Pro\Videos\Projects\ECRformer"
SAMPLES = os.path.join(BASE, "frontend", "public", "samples")
ASSETS = os.path.join(BASE, "backend", "assets")
OUT = [os.path.join(BASE, "ECRformer_Project_Presentation.pptx"),
       r"C:\Users\Windows 11 Pro\Downloads\ECRformer_Project_Presentation.pptx"]

# ---------- Design tokens ----------
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

H = "Poppins SemiBold"
B = "Poppins Light"
M = "Poppins Medium"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 18
state = {"n": 0}


def img(scene, kind):
    return os.path.join(SAMPLES, f"scene-{scene}", f"{kind}.png")


def text(slide, x, y, w, h, runs, size=18, font=B, color=SLATE, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, line=1.15):
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


def box(slide, x, y, w, h, fill=CARD, line=None, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
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
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def content_slide(kicker, title, subtitle=None):
    state["n"] += 1
    s = prs.slides.add_slide(BLANK)
    box(s, 0.8, 0.62, 0.55, 0.06, fill=INDIGO, shape=MSO_SHAPE.RECTANGLE)
    text(s, 1.5, 0.5, 9, 0.3, kicker.upper(), size=11, font=H, color=INDIGO, spacing=300)
    text(s, 0.8, 0.85, 11.8, 0.9, title, size=32, font=H, color=INK)
    if subtitle:
        text(s, 0.8, 1.62, 11.8, 0.5, subtitle, size=16, font=B, color=SLATE)
    text(s, 0.8, 7.0, 8, 0.3, "SAR-Guided Satellite Cloud Removal", size=9, font=B, color=MUTED)
    text(s, 11.5, 7.0, 1.05, 0.3, f"{state['n']:02d} / {TOTAL}", size=9, font=M, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def dark_slide():
    state["n"] += 1
    s = prs.slides.add_slide(BLANK)
    box(s, 0, 0, 13.333, 7.5, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    return s


def number_badge(slide, x, y, n, color=INDIGO, size=0.55):
    c = box(slide, x, y, size, size, fill=color, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(n)
    r.font.name = H; r.font.size = Pt(16); r.font.color.rgb = WHITE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def captioned_image(slide, path, x, y, size, caption, color=SLATE):
    picture(slide, path, x, y, w=size, h=size)
    text(slide, x, y + size + 0.1, size, 0.35, caption, size=12, font=M, color=color, align=PP_ALIGN.CENTER)


# ============ 1. TITLE ============
s = dark_slide()
text(s, 0.9, 0.9, 7, 0.3, "M.SC. PROJECT PRESENTATION  ·  CUSAT", size=11, font=H, color=RGBColor(0x81, 0x8C, 0xF8), spacing=300)
text(s, 0.9, 1.4, 7.2, 2.2, [[("SAR-Guided", H, WHITE, 46)], [("Satellite Cloud", H, WHITE, 46)],
                              [("Removal", H, RGBColor(0x5E, 0xEA, 0xD4), 46)]], line=1.0)
text(s, 0.9, 3.85, 6.8, 0.8, "Seeing through clouds by combining radar\nwith deep learning", size=17, font=B,
     color=RGBColor(0xCB, 0xD5, 0xE1))
box(s, 0.9, 4.95, 0.5, 0.04, fill=RGBColor(0x5E, 0xEA, 0xD4), shape=MSO_SHAPE.RECTANGLE)
text(s, 0.9, 5.15, 3.4, 0.3, "TEAM", size=10, font=H, color=MUTED, spacing=300)
text(s, 0.9, 5.45, 3.6, 1.2, ["Agnal K V", "Bivin Balu", "Vaishnav T Prakash"], size=15, font=M, color=WHITE, line=1.25)
text(s, 4.4, 5.15, 3.4, 0.3, "GUIDE", size=10, font=H, color=MUTED, spacing=300)
text(s, 4.4, 5.45, 3.6, 0.5, "Dr. Sabu M K", size=15, font=M, color=WHITE)
# before / after images
picture(s, img("suburban", "cloudy"), 8.25, 1.05, w=2.25, h=2.25)
picture(s, img("suburban", "blended"), 10.6, 1.05, w=2.25, h=2.25)
picture(s, img("farms", "cloudy"), 8.25, 3.75, w=2.25, h=2.25)
picture(s, img("farms", "blended"), 10.6, 3.75, w=2.25, h=2.25)
text(s, 8.25, 6.12, 2.25, 0.3, "Cloudy input", size=11, font=M, color=MUTED, align=PP_ALIGN.CENTER)
text(s, 10.6, 6.12, 2.25, 0.3, "Our output", size=11, font=M, color=RGBColor(0x5E, 0xEA, 0xD4), align=PP_ALIGN.CENTER)

# ============ 2. AGENDA ============
s = content_slide("Overview", "What we will cover")
items = [("The problem", "Why clouds are a big issue"), ("The data", "Satellites, dataset, preparation"),
         ("The model", "How ECRformer works"), ("Sharper results", "Fixing blur with smart losses"),
         ("Results", "What the model produces"), ("Conclusion", "Limits and takeaways")]
for i, (t, d) in enumerate(items):
    col, row = i % 3, i // 3
    x, y = 0.8 + col * 4.0, 2.2 + row * 2.2
    box(s, x, y, 3.65, 1.85, fill=CARD)
    text(s, x + 0.35, y + 0.3, 1, 0.6, f"0{i+1}", size=28, font=H, color=INDIGO)
    text(s, x + 0.35, y + 0.95, 3.1, 0.4, t, size=18, font=H, color=INK)
    text(s, x + 0.35, y + 1.35, 3.1, 0.4, d, size=13, font=B, color=SLATE)

# ============ 3. PROBLEM ============
s = content_slide("01 · The problem", "Clouds hide the ground")
text(s, 0.8, 2.2, 6.2, 3.6, [
    [("More than half ", H, INK, 22), ("of the Earth is covered by cloud at any moment.", B, SLATE, 22)],
    [("", B, SLATE, 12)],
    [("Optical satellites ", H, INK, 22), ("cannot see through them — the ground simply disappears.", B, SLATE, 22)],
    [("", B, SLATE, 12)],
    [("Goal: ", H, INDIGO, 22), ("rebuild the hidden ground so the image is usable again.", B, SLATE, 22)],
], line=1.2)
captioned_image(s, img("forest", "cloudy"), 7.9, 1.9, 4.4, "A real cloudy Sentinel-2 image")

# ============ 4. TWO SATELLITES ============
s = content_slide("01 · The idea", "Two satellites, two strengths")
for i, (name, sub, good, bad, path, col, soft) in enumerate([
        ("Sentinel-2", "Optical camera", "Rich natural colour", "Blocked by clouds", img("suburban", "cloudy"), CORAL, SOFT_CORAL),
        ("Sentinel-1", "SAR radar", "Passes through clouds", "No natural colour", img("suburban", "sar"), TEAL, SOFT_TEAL)]):
    x = 0.8 + i * 6.0
    box(s, x, 2.1, 5.7, 4.0, fill=soft)
    picture(s, path, x + 0.35, 2.45, w=2.3, h=2.3)
    text(s, x + 2.95, 2.5, 2.6, 0.5, name, size=24, font=H, color=INK)
    text(s, x + 2.95, 3.05, 2.6, 0.4, sub, size=14, font=M, color=col)
    text(s, x + 2.95, 3.75, 2.6, 1.2, [[("+  ", H, TEAL, 15), (good, B, INK, 15)],
                                       [("–  ", H, ROSE, 15), (bad, B, INK, 15)]], line=1.5)
    text(s, x + 0.35, 5.05, 5.0, 0.8,
         "Sees sunlight reflected by the ground" if i == 0 else "Sends its own microwaves and listens for echoes",
         size=13, font=B, color=SLATE)
text(s, 0.8, 6.35, 11.8, 0.5, [[("Our idea → ", H, INDIGO, 17), ("use radar structure to fill in what the clouds hide.", B, INK, 17)]])

# ============ 5. DATASET ============
s = content_slide("02 · The data", "SEN12MS-CR dataset",
                  "Paired radar, cloudy and cloud-free images of the same place")
for i, (num, lab) in enumerate([("33,468", "training patches"), ("1,115", "validation patches"),
                                ("256 × 256", "pixels per patch · 10 m each")]):
    x = 0.8 + i * 4.0
    box(s, x, 2.5, 3.65, 1.9, fill=CARD)
    text(s, x + 0.35, 2.75, 3.1, 0.8, num, size=34, font=H, color=INDIGO)
    text(s, x + 0.35, 3.6, 3.1, 0.6, lab, size=14, font=B, color=SLATE)
text(s, 0.8, 4.85, 11.8, 0.3, "WHAT GOES INTO THE MODEL", size=10, font=H, color=MUTED, spacing=300)
chips = [("4", "optical bands", CORAL, SOFT_CORAL), ("+", "", None, None), ("2", "radar bands", TEAL, SOFT_TEAL),
         ("+", "", None, None), ("1", "cloud mask", INDIGO, SOFT_IND), ("=", "", None, None), ("7", "input channels", INK, CARD)]
x = 0.8
for n, lab, col, soft in chips:
    if col is None:
        text(s, x, 5.35, 0.5, 0.7, n, size=24, font=B, color=MUTED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += 0.6
    else:
        box(s, x, 5.35, 2.3, 0.75, fill=soft)
        text(s, x + 0.2, 5.35, 2.0, 0.75, [[(n + "  ", H, col, 22), (lab, M, INK, 13)]], anchor=MSO_ANCHOR.MIDDLE)
        x += 2.45

# ============ 6. PREPARATION ============
s = content_slide("02 · The data", "Preparing the data in 3 steps")
steps = [("Find the clouds", "ESA's s2cloudless tool marks every cloudy pixel, giving a cloud mask."),
         ("Scale the radar", "Radar values (in decibels) are rescaled to the range 0 – 1."),
         ("Stop shortcuts", "In 65% of training samples, cloudy areas are blurred so the model must rely on radar.")]
for i, (t, d) in enumerate(steps):
    x = 0.8 + i * 4.05
    box(s, x, 2.2, 3.6, 3.3, fill=CARD)
    number_badge(s, x + 0.35, 2.55, i + 1)
    text(s, x + 0.35, 3.35, 3.0, 0.5, t, size=19, font=H, color=INK)
    text(s, x + 0.35, 3.95, 2.95, 1.5, d, size=14, font=B, color=SLATE, line=1.25)
    if i < 2:
        text(s, x + 3.6, 3.4, 0.45, 0.6, "→", size=26, font=B, color=MUTED, align=PP_ALIGN.CENTER)
mx = 0.8
for lab, k in [("Cloudy", "cloudy"), ("Cloud mask", "mask"), ("Radar", "sar")]:
    picture(s, img("ridge", k), mx, 5.75, w=0.95, h=0.95)
    text(s, mx + 1.05, 6.05, 1.6, 0.4, lab, size=12, font=M, color=SLATE)
    mx += 2.7

# ============ 7. PIPELINE OVERVIEW ============
s = content_slide("03 · The model", "How the system works")
flow = [("Inputs", "Cloudy image\nRadar · Cloud mask", SOFT_CORAL, CORAL),
        ("ECRformer", "Deep network that\nrebuilds the ground", SOFT_IND, INDIGO),
        ("Prediction", "A full cloud-free\nguess of the scene", SOFT_TEAL, TEAL),
        ("Blend", "Keep real clear pixels,\nfill only the clouds", CARD, INK)]
for i, (t, d, soft, col) in enumerate(flow):
    x = 0.8 + i * 3.1
    box(s, x, 2.3, 2.6, 2.2, fill=soft)
    text(s, x + 0.25, 2.55, 2.2, 0.5, t, size=20, font=H, color=col)
    text(s, x + 0.25, 3.2, 2.2, 1.2, d, size=13, font=B, color=SLATE, line=1.25)
    if i < 3:
        text(s, x + 2.6, 3.0, 0.5, 0.6, "→", size=26, font=B, color=MUTED, align=PP_ALIGN.CENTER)
box(s, 0.8, 5.0, 11.75, 1.4, fill=WHITE, line=LINE)
text(s, 1.15, 5.2, 5.5, 1.1, [[("Training  ", H, INDIGO, 15)],
                              [("Random 128 × 128 crops. A critic network (PatchGAN) judges if the result looks real.", B, SLATE, 13)]], line=1.2)
text(s, 7.0, 5.2, 5.4, 1.1, [[("Testing  ", H, TEAL, 15)],
                             [("Full 256 × 256 scenes. The critic is removed — only ECRformer runs.", B, SLATE, 13)]], line=1.2)

# ============ 8. INSIDE ECRFORMER ============
s = content_slide("03 · The model", "Inside ECRformer",
                  "An hourglass-shaped network: shrink to understand, expand to rebuild")
parts = [("Two-door input", "Radar and optical enter through separate layers first — they behave very differently."),
         ("Encoder", "Shrinks the image step by step while learning richer features."),
         ("Attention core", "Looks at the whole scene at once to connect distant clues."),
         ("Decoder", "Expands back to full size. Skip links carry fine edges across.")]
for i, (t, d) in enumerate(parts):
    x = 0.8 + i * 3.0
    h_ = [3.4, 2.9, 2.4, 2.9][i]
    y = 2.5 + (3.4 - h_) / 2
    box(s, x, y, 2.75, h_, fill=[SOFT_CORAL, SOFT_IND, SOFT_TEAL, SOFT_IND][i])
    text(s, x + 0.25, y + 0.3, 2.3, 0.5, t, size=17, font=H, color=INK)
    text(s, x + 0.25, y + 0.9, 2.3, h_ - 1.0, d, size=12.5, font=B, color=SLATE, line=1.25)
text(s, 0.8, 6.25, 11.8, 0.4, [[("Model size: ", H, INK, 14), ("about 8.3 million parameters — light enough for a single desktop GPU.", B, SLATE, 14)]])

# ============ 9. TRAIN SMALL, TEST BIG ============
s = content_slide("03 · The model", "Train small, test big")
box(s, 0.8, 2.1, 5.7, 3.2, fill=CARD)
text(s, 1.15, 2.4, 5.0, 0.5, "Normal attention", size=20, font=H, color=ROSE)
text(s, 1.15, 3.05, 5.0, 2.0, ["Compares every pixel with every pixel.",
                               "Its size grows with the image — change the image size and it breaks."],
     size=15, font=B, color=SLATE, line=1.3)
box(s, 6.85, 2.1, 5.7, 3.2, fill=SOFT_TEAL)
text(s, 7.2, 2.4, 5.0, 0.5, "ECRformer attention (MDTA)", size=20, font=H, color=TEAL)
text(s, 7.2, 3.05, 5.0, 2.0, ["Compares feature channels with each other.",
                              "Its size stays the same for any image size."],
     size=15, font=B, color=SLATE, line=1.3)
text(s, 0.8, 5.75, 11.8, 0.6, [[("Result → ", H, INDIGO, 20), ("trained on 128 × 128 crops, runs directly on 256 × 256 scenes.", M, INK, 20)]],
     align=PP_ALIGN.CENTER)

# ============ 10. THE BLUR PROBLEM ============
s = content_slide("04 · Sharper results", "The blur problem")
captioned_image(s, img("suburban", "pregan"), 0.8, 2.0, 3.3, "Basic model (blurry)", ROSE)
captioned_image(s, img("suburban", "clear"), 4.3, 2.0, 3.3, "Real clear image", TEAL)
text(s, 8.1, 2.1, 4.5, 4.0, [
    [("Why does it blur?", H, INK, 20)], [("", B, SLATE, 8)],
    [("1  ", H, INDIGO, 16), ("Unsure what lies under the cloud, the model plays safe and paints an average.", B, SLATE, 15)],
    [("", B, SLATE, 8)],
    [("2  ", H, INDIGO, 16), ("Radar and optical images are often shifted by 1–2 pixels, so sharp edges get punished.", B, SLATE, 15)],
], line=1.25)

# ============ 11. LOSSES ============
s = content_slide("04 · Sharper results", "Teaching the model to be sharp",
                  "Seven loss functions, grouped by what they check")
groups = [("Colour", "Is the colour right?", ["Scale-decoupled L1"], CORAL, SOFT_CORAL),
          ("Structure", "Are the edges right?", ["VGG perceptual", "Multi-scale gradient", "Edge correlation", "Local contrast"], INDIGO, SOFT_IND),
          ("Realism", "Does it look real?", ["PatchGAN adversarial", "Feature matching"], TEAL, SOFT_TEAL)]
for i, (t, q, ls, col, soft) in enumerate(groups):
    x = 0.8 + i * 4.0
    box(s, x, 2.4, 3.65, 3.9, fill=soft)
    text(s, x + 0.35, 2.7, 3.0, 0.5, t, size=22, font=H, color=col)
    text(s, x + 0.35, 3.3, 3.0, 0.4, q, size=14, font=B, color=SLATE)
    box(s, x + 0.35, 3.85, 0.4, 0.03, fill=col, shape=MSO_SHAPE.RECTANGLE)
    text(s, x + 0.35, 4.05, 3.0, 2.1, ls, size=15, font=M, color=INK, line=1.45)

# ============ 12. PATCHGAN ============
s = content_slide("04 · Sharper results", "The PatchGAN critic")
text(s, 0.8, 2.1, 6.3, 4.2, [
    [("A second network that acts like a ", B, SLATE, 18), ("strict art examiner.", H, INK, 18)],
    [("", B, SLATE, 10)],
    [("•  ", H, INDIGO, 16), ("Looks at small regions and scores each one real or fake.", B, SLATE, 16)],
    [("•  ", H, INDIGO, 16), ("Blurry patches get low scores, pushing ECRformer to draw sharp detail.", B, SLATE, 16)],
    [("•  ", H, INDIGO, 16), ("Checks cloudy areas 4× more strictly than clear ones.", B, SLATE, 16)],
    [("", B, SLATE, 10)],
    [("Used only during training — removed at test time.", M, TEAL, 15)],
], line=1.3)
vals = [["+1.1", "+0.9", "+0.8", "+1.0"], ["+0.9", "−0.8", "−1.1", "+0.7"],
        ["+1.0", "−0.9", "−0.7", "+0.8"], ["+1.2", "+0.8", "+0.9", "+1.1"]]
for r in range(4):
    for c in range(4):
        bad = vals[r][c].startswith("−")
        cell = box(s, 7.9 + c * 1.05, 2.1 + r * 0.95, 0.95, 0.85, fill=RGBColor(0xFE, 0xE2, 0xE2) if bad else SOFT_TEAL, radius=0.12)
        tf = cell.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        rr = p.add_run(); rr.text = vals[r][c]; rr.font.name = M; rr.font.size = Pt(14)
        rr.font.color.rgb = ROSE if bad else TEAL
text(s, 7.9, 6.0, 4.15, 0.6, "Illustration: each score judges one region\n(red = looks blurry / fake)", size=11, font=B,
     color=MUTED, align=PP_ALIGN.CENTER)

# ============ 13. FINAL BLEND ============
s = content_slide("05 · Results", "Building the final image")
box(s, 0.8, 2.2, 11.75, 1.6, fill=SOFT_IND)
text(s, 0.8, 2.2, 11.75, 1.6, [[("Output  =  ", H, INK, 28), ("(1 − M)", H, CORAL, 28), (" × Cloudy  +  ", H, INK, 28),
                                ("M", H, TEAL, 28), (" × Prediction", H, INK, 28)]],
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
for i, (t, d, col) in enumerate([("Clear sky  (M = 0)", "Real satellite pixels are kept exactly as they are.", CORAL),
                                 ("Thick cloud  (M = 1)", "The model's reconstruction fills the gap.", TEAL),
                                 ("Cloud edges", "Soft blending, so no visible seams.", INDIGO)]):
    x = 0.8 + i * 4.0
    text(s, x, 4.4, 3.6, 0.5, t, size=18, font=H, color=col)
    text(s, x, 4.95, 3.5, 1.2, d, size=15, font=B, color=SLATE, line=1.25)

# ============ 14. VISUAL RESULTS ============
s = content_slide("05 · Results", "Results on real scenes")
cols = [("Cloudy input", "cloudy", SLATE), ("Basic model", "pregan", ROSE), ("Our model", "blended", TEAL), ("Real clear image", "clear", SLATE)]
scenes = ["suburban", "farms", "lake"]
sz = 1.45
x0 = 2.45
for c, (lab, _, col) in enumerate(cols):
    text(s, x0 + c * (sz + 0.95), 1.7, sz + 0.6, 0.3, lab, size=12, font=H, color=col, align=PP_ALIGN.CENTER)
for r, sc in enumerate(scenes):
    text(s, 0.8, 2.1 + r * (sz + 0.12) + sz / 2 - 0.15, 1.5, 0.3, sc.capitalize(), size=13, font=M, color=INK)
    for c, (_, k, _) in enumerate(cols):
        picture(s, img(sc, k), x0 + 0.3 + c * (sz + 0.95), 2.1 + r * (sz + 0.12), w=sz, h=sz)

# ============ 15. NUMBERS ============
s = content_slide("05 · Results", "What the numbers say",
                  "Compared with the basic model, across four cloud-cover groups")
stats = [("+47% to +133%", "more fine detail recovered", TEAL),
         ("≈ 0.9", "detail ratio (1.0 = as sharp as reality)", INDIGO),
         ("30 – 32 dB", "PSNR under the cloud", CORAL)]
for i, (n, lab, col) in enumerate(stats):
    x = 0.8 + i * 4.0
    box(s, x, 2.5, 3.65, 2.4, fill=CARD)
    text(s, x + 0.35, 2.85, 3.1, 0.8, n, size=30, font=H, color=col)
    text(s, x + 0.35, 3.75, 3.0, 0.9, lab, size=14, font=B, color=SLATE, line=1.2)
text(s, 0.8, 5.4, 11.8, 1.0, [[("Basic model detail ratio: 0.39 – 0.63  →  Ours: 0.90 – 0.93", M, INK, 16)],
                              [("Detail ratio = how much of the real image's fine texture is reproduced.", B, MUTED, 13)]], line=1.4)

# ============ 16. HONEST VIEW ============
s = content_slide("06 · Conclusion", "An honest look")
box(s, 0.8, 2.1, 5.7, 4.3, fill=SOFT_IND)
text(s, 1.15, 2.4, 5.0, 0.5, "The trade-off", size=20, font=H, color=INDIGO)
text(s, 1.15, 3.05, 5.0, 3.2, [[("•  ", H, INDIGO, 14), ("Sharper images score slightly lower on PSNR (0.3 – 1.2 dB).", B, SLATE, 14)], [("", B, SLATE, 6)],
                               [("•  ", H, INDIGO, 14), ("PSNR rewards safe, blurry averages — the known perception–distortion trade-off.", B, SLATE, 14)], [("", B, SLATE, 6)],
                               [("•  ", H, INDIGO, 14), ("We chose sharpness, which matters for real use.", B, SLATE, 14)]],
     line=1.3)
box(s, 6.85, 2.1, 5.7, 4.3, fill=SOFT_CORAL)
text(s, 7.2, 2.4, 5.0, 0.5, "Limitations", size=20, font=H, color=CORAL)
text(s, 7.2, 3.05, 5.0, 3.2, [[("•  ", H, CORAL, 14), ("Cloud shadows are not always caught by the cloud mask.", B, SLATE, 14)], [("", B, SLATE, 6)],
                              [("•  ", H, CORAL, 14), ("The clear reference image is taken on a different day.", B, SLATE, 14)], [("", B, SLATE, 6)],
                              [("•  ", H, CORAL, 14), ("Training too long adds artificial grain, so we keep the best checkpoint.", B, SLATE, 14)]],
     line=1.3)

# ============ 17. CONCLUSION / THANK YOU ============
s = dark_slide()
text(s, 0.9, 0.9, 7, 0.3, "CONCLUSION", size=11, font=H, color=RGBColor(0x81, 0x8C, 0xF8), spacing=300)
text(s, 0.9, 1.35, 7.5, 0.9, "What we achieved", size=34, font=H, color=WHITE)
for i, t in enumerate(["Removed clouds by combining radar with optical images",
                       "Turned blurry reconstructions into sharp, detailed ones",
                       "Trained on small crops, works on full scenes"]):
    y = 2.6 + i * 0.85
    box(s, 0.9, y + 0.12, 0.12, 0.12, fill=RGBColor(0x5E, 0xEA, 0xD4), shape=MSO_SHAPE.OVAL)
    text(s, 1.25, y, 7.0, 0.5, t, size=17, font=B, color=RGBColor(0xE2, 0xE8, 0xF0))
text(s, 0.9, 5.3, 7, 0.9, [[("Thank you", H, RGBColor(0x5E, 0xEA, 0xD4), 34)]])
text(s, 0.9, 6.25, 8, 0.4, "Questions are welcome", size=15, font=B, color=MUTED)
picture(s, img("lake", "cloudy"), 9.2, 1.0, w=2.6, h=2.6)
picture(s, img("lake", "blended"), 9.2, 3.85, w=2.6, h=2.6)
text(s, 9.2, 6.5, 2.6, 0.3, "Before  ·  After", size=11, font=M, color=MUTED, align=PP_ALIGN.CENTER)

# ============ 18. APPENDIX ============
s = content_slide("Appendix", "Detailed pipeline (for reference)")
picture(s, os.path.join(ASSETS, "pipeline_training_vs_testing_complete.png"), 1.6, 1.7, h=5.15)

for p in OUT:
    prs.save(p)
    print("saved", p)
