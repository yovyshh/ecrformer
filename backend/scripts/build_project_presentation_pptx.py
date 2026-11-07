import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = r"c:\Users\Windows 11 Pro\Videos\Projects\ECRformer"
ASSETS_DIR = os.path.join(BASE_DIR, "backend", "assets")
DIAG_DIR = os.path.join(ASSETS_DIR, "ppt_diagrams")

OUT_PPTX_PROJECT = os.path.join(BASE_DIR, "ECRformer_Project_Presentation.pptx")
OUT_PPTX_DOWNLOADS = r"C:\Users\Windows 11 Pro\Downloads\ECRformer_Project_Presentation.pptx"

# DL Slide Palette (Modeled after CUSAT DL Lecture Slides)
CRIMSON = RGBColor(153, 0, 0)        # #990000 Slide Titles & Table Headers
DARK_NAVY = RGBColor(15, 23, 42)     # #0F172A Deep Headings
ROYAL_BLUE = RGBColor(0, 51, 204)    # #0033CC Key Technical Terms
DEEP_GREEN = RGBColor(6, 95, 70)     # #065F46 Positive / Solution Highlights
DARK_TEXT = RGBColor(30, 41, 59)     # #1E293B Body Text
MUTED_TEXT = RGBColor(100, 116, 139) # #64748B Footer / Captions
WHITE = RGBColor(255, 255, 255)

BG_SOFT_BLUE = RGBColor(239, 246, 255)
BORDER_BLUE = RGBColor(37, 99, 235)

BG_SOFT_GREEN = RGBColor(236, 253, 245)
BORDER_GREEN = RGBColor(5, 150, 105)

BG_SOFT_AMBER = RGBColor(254, 243, 199)
BORDER_AMBER = RGBColor(217, 119, 6)

BG_SOFT_RED = RGBColor(254, 226, 226)
BORDER_RED = RGBColor(220, 38, 38)

BG_SOFT_GREY = RGBColor(244, 244, 240)
BORDER_GREY = RGBColor(168, 162, 158)

BG_YELLOW_HL = RGBColor(254, 240, 138)


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    total_slides = 18

    def add_header_footer(slide, title_text, subtitle_text="", slide_num=1):
        # Top Crimson Title (DL Slide Style)
        tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = "Calibri"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = CRIMSON

        if subtitle_text:
            tb_sub = slide.shapes.add_textbox(Inches(0.55), Inches(0.76), Inches(12.2), Inches(0.32))
            tf_sub = tb_sub.text_frame
            tf_sub.word_wrap = True
            tf_sub.margin_left = tf_sub.margin_top = tf_sub.margin_right = tf_sub.margin_bottom = 0
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle_text
            p_sub.font.name = "Calibri"
            p_sub.font.size = Pt(13.5)
            p_sub.font.bold = True
            p_sub.font.color.rgb = ROYAL_BLUE

        # Thin separator line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(1.10 if subtitle_text else 0.85), Inches(12.23), Inches(0.02)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(203, 213, 225)
        line.line.fill.background()

        # Footer
        tb_f = slide.shapes.add_textbox(Inches(0.55), Inches(7.12), Inches(12.23), Inches(0.28))
        tf_f = tb_f.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        pf = tf_f.paragraphs[0]
        pf.text = f"SAR-Guided Satellite Cloud Removal (ECRformer + PatchGAN)   |   Guide: Dr. Sabu M. K.   |   Slide {slide_num} of {total_slides}"
        pf.font.name = "Calibri"
        pf.font.size = Pt(10.5)
        pf.font.color.rgb = MUTED_TEXT

    def add_card(slide, left, top, width, height, title, bullets,
                 bg_color=BG_SOFT_GREY, border_color=BORDER_GREY,
                 title_color=CRIMSON, font_size=13.5, title_size=15.5):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
        )
        shape.adjustments[0] = 0.03
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(
            Inches(left + 0.16), Inches(top + 0.12), Inches(width - 0.32), Inches(height - 0.22)
        )
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        if title:
            p0 = tf.paragraphs[0]
            p0.text = title
            p0.font.name = "Calibri"
            p0.font.size = Pt(title_size)
            p0.font.bold = True
            p0.font.color.rgb = title_color
            p0.space_after = Pt(6)

        for idx, b in enumerate(bullets):
            p = tf.paragraphs[0] if (idx == 0 and not title) else tf.add_paragraph()
            if isinstance(b, tuple):
                lead, rest = b
                r1 = p.add_run()
                r1.text = lead
                r1.font.name = "Calibri"
                r1.font.size = Pt(font_size)
                r1.font.bold = True
                r1.font.color.rgb = ROYAL_BLUE

                r2 = p.add_run()
                r2.text = rest
                r2.font.name = "Calibri"
                r2.font.size = Pt(font_size)
                r2.font.bold = False
                r2.font.color.rgb = DARK_TEXT
            else:
                p.text = b
                p.font.name = "Calibri"
                p.font.size = Pt(font_size)
                p.font.color.rgb = DARK_TEXT
            p.space_after = Pt(4)

    def add_styled_table(slide, left, top, width, height, headers, rows, col_widths=None, font_size=12):
        table_shape = slide.shapes.add_table(
            len(rows) + 1, len(headers), Inches(left), Inches(top), Inches(width), Inches(height)
        )
        table = table_shape.table
        if col_widths:
            for i, cw in enumerate(col_widths):
                table.columns[i].width = Inches(cw)

        # Header row (Crimson like DL Slide 71!)
        for c_idx, h_text in enumerate(headers):
            cell = table.cell(0, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CRIMSON
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = h_text
            p.font.name = "Calibri"
            p.font.size = Pt(font_size + 1)
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT

        for r_idx, r_data in enumerate(rows):
            bg = RGBColor(255, 255, 255) if r_idx % 2 == 0 else RGBColor(241, 245, 249)
            for c_idx, val in enumerate(r_data):
                cell = table.cell(r_idx + 1, c_idx)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = cell.text_frame.paragraphs[0]
                is_bold = False
                if val.startswith("**") and val.endswith("**"):
                    val = val[2:-2]
                    is_bold = True
                p.text = val
                p.font.name = "Calibri"
                p.font.size = Pt(font_size)
                p.font.bold = is_bold or (c_idx == 0)
                p.font.color.rgb = ROYAL_BLUE if is_bold else DARK_TEXT
                p.alignment = PP_ALIGN.LEFT if c_idx in (0, 1) else PP_ALIGN.CENTER

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE (FIRST PAGE)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    # Top decorative crimson banner bar
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.28))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = CRIMSON
    top_bar.line.fill.background()

    # Main Title Box
    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(2.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "SAR-Guided Satellite Cloud Removal"
    p1.font.name = "Calibri"
    p1.font.size = Pt(42)
    p1.font.bold = True
    p1.font.color.rgb = CRIMSON
    p1.alignment = PP_ALIGN.CENTER
    p1.space_after = Pt(10)

    p2 = tf1.add_paragraph()
    p2.text = "High-Frequency Optical Terrain Reconstruction via ECRformer-Light,\nScale-Decoupled Supervision & Conditional PatchGAN"
    p2.font.name = "Calibri"
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = DARK_NAVY
    p2.alignment = PP_ALIGN.CENTER

    # Subtitle badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.3), Inches(2.85), Inches(8.73), Inches(0.58))
    badge.adjustments[0] = 0.2
    badge.fill.solid()
    badge.fill.fore_color.rgb = BG_SOFT_BLUE
    badge.line.color.rgb = BORDER_BLUE
    badge.line.width = Pt(1.5)
    bp = badge.text_frame.paragraphs[0]
    bp.text = "Multimodal Sentinel-1 SAR (VV, VH) + Sentinel-2 Optical (B04, B03, B02, B08)  |  SEN12MS-CR Benchmark"
    bp.font.name = "Calibri"
    bp.font.size = Pt(14)
    bp.font.bold = True
    bp.font.color.rgb = ROYAL_BLUE
    bp.alignment = PP_ALIGN.CENTER

    # Team Members Card (Left) & Project Guide Card (Right)
    add_card(
        s1, left=1.2, top=3.80, width=5.3, height=2.55,
        title="Presented By (Team Members)",
        bullets=[
            ("• Agnal K. V.", ""),
            ("• Bivin Balu", ""),
            ("• Vaishnav T. Prakash", ""),
            "",
            "M.Sc. Computer Science (Artificial Intelligence)"
        ],
        bg_color=BG_SOFT_GREY, border_color=BORDER_GREY,
        title_color=CRIMSON, font_size=16, title_size=18
    )

    add_card(
        s1, left=6.8, top=3.80, width=5.3, height=2.55,
        title="Under the Guidance of",
        bullets=[
            ("Dr. Sabu M. K.", ""),
            "Professor, Department of Computer Applications / CS",
            "Cochin University of Science and Technology (CUSAT)",
            "Kochi, Kerala",
            ""
        ],
        bg_color=BG_SOFT_GREEN, border_color=BORDER_GREEN,
        title_color=DEEP_GREEN, font_size=16, title_size=18
    )

    # Bottom bar
    bot_bar = s1.shapes.add_textbox(Inches(0.8), Inches(6.75), Inches(11.7), Inches(0.4))
    bp2 = bot_bar.text_frame.paragraphs[0]
    bp2.text = "Cochin University of Science & Technology (CUSAT)   •   Complete Step-by-Step Technical Presentation"
    bp2.font.name = "Calibri"
    bp2.font.size = Pt(13)
    bp2.font.bold = True
    bp2.font.color.rgb = MUTED_TEXT
    bp2.alignment = PP_ALIGN.CENTER

    # ==========================================================================
    # SLIDE 2: PRESENTATION ROADMAP (FROM START TO FINISH)
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header_footer(s2, "Presentation Roadmap: Understanding the Project from Scratch",
                      "Structured Step-by-Step Flow: Problem → Physics → Data → Architecture → Losses → Results", 2)

    add_card(s2, 0.55, 1.30, 3.9, 2.65,
             "Part 1: The Task & Physics",
             [
                 ("• What is the problem? ", ">50% of Earth is covered by clouds at any moment."),
                 ("• Optical Failure: ", "Sentinel-2 light bounces off cloud droplets as white blobs."),
                 ("• Radar Superpower: ", "Sentinel-1 C-band SAR (5.5 cm) pierces straight through clouds.")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE)

    add_card(s2, 4.70, 1.30, 3.9, 2.65,
             "Part 2: Data & Preprocessing",
             [
                 ("• SEN12MS-CR (fall): ", "33,468 train + 1,115 val patches (.npz float32 tensors)."),
                 ("• Cloud Detection: ", "ESA s2cloudless (Cirrus B10 + SWIR) + 3-step soft mask M."),
                 ("• Anti-Cheating (M1): ", "Opaque Cloud Cutout (prob=0.65) stops thin-haze shortcuts.")
             ], bg_color=BG_SOFT_AMBER, border_color=BORDER_AMBER)

    add_card(s2, 8.85, 1.30, 3.9, 2.65,
             "Part 3: ECRformer Generator",
             [
                 ("• Decoupled Stem (M2): ", "Separate 7×7 doors for SAR (2ch) and Optical+Mask (5ch)."),
                 ("• Hourglass U-Net: ", "PixelUnshuffle/Shuffle + 3 overhead skip bridges."),
                 ("• MDTA Attention: ", "[C×C] channel covariance scales 128² train → 256² test.")
             ], bg_color=BG_SOFT_GREEN, border_color=BORDER_GREEN)

    add_card(s2, 0.55, 4.20, 3.9, 2.65,
             "Part 4: Solving the Blur Trap",
             [
                 ("• Why L1 Blurs: ", "Safe conditional mean + 1-px radar shift double-edge penalty."),
                 ("• Role M3: ", "Scale-Decoupled L1 (4×4 & 8×8 pooled L1 inside clouds)."),
                 ("• Role M4: ", "Cloud-boosted VGG-16, Multi-scale Gradients, Edge Corr & Local Std.")
             ], bg_color=BG_SOFT_RED, border_color=BORDER_RED)

    add_card(s2, 4.70, 4.20, 3.9, 2.65,
             "Part 5: 11-Ch PatchGAN Critic",
             [
                 ("• High-Pass Input: ", "5×5 edge residual R_HP = 10(x - AvgPool5×5(x)) exposes blur."),
                 ("• 16×16 Scorecard: ", "Grades 70×70 local patches (numbers, not an image)."),
                 ("• Role M5: ", "w_patch = 0.25 + 0.75·M focuses 4× harder inside clouds.")
             ], bg_color=BG_SOFT_GREY, border_color=BORDER_GREY)

    add_card(s2, 8.85, 4.20, 3.9, 2.65,
             "Part 6: 256² Inference & Results",
             [
                 ("• Fast Deployment: ", "PatchGAN removed at test time (0.04s per 256×256 scene)."),
                 ("• Soft-Mask Gate (I2): ", "Preserves 100% real clear sky + sharp cloud reconstruction."),
                 ("• Honest Evaluation: ", "+47% to +133% detail sharpness & full trade-off analysis.")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE)

    # ==========================================================================
    # SLIDE 3: THE CORE PROBLEM & SATELLITE PHYSICS
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header_footer(s3, "1. The Core Problem: Why Do We Need Two Satellites?",
                      "Goal: Reconstruct missing optical ground reflectance underneath opaque clouds using SAR radar", 3)

    s3.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig1_sar_vs_optical_physics.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 4: DATASET & NOTATION AND SHAPES (DL SLIDE 71 STYLE!)
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header_footer(s4, "2. Dataset Contract, Notation and Tensor Shapes",
                      "SEN12MS-CR (ROIs1970_fall Subset) — Stored as 32-Bit Floating-Point .npz Numerical Archives", 4)

    headers_s4 = ["Symbol / Key", "Physical Meaning", "PyTorch Shape", "Numerical Range & Units"]
    rows_s4 = [
        ["S2_cloudy", "Cloud-corrupted Sentinel-2 optical (B04, B03, B02, B08)", "[B, 4, H, W]", "[0.0, 1.0] surface reflectance"],
        ["S1 (SAR)", "Co-registered Sentinel-1 C-band radar (VV, VH)", "[B, 2, H, W]", "VV∈[-25,0] dB, VH∈[-35,0] dB → [0,1]"],
        ["M (mask)", "Soft pixel-wise cloud probability mask (s2cloudless)", "[B, 1, H, W]", "[0.0 = Clear Land, 1.0 = Thick Cloud]"],
        ["X_in", "Concatenated multimodal input [S1, S2_cloudy, M]", "[B, 7, H, W]", "7 channels total in [0.0, 1.0]"],
        ["Y (s2_clear)", "Cloud-free target Sentinel-2 image (ground truth)", "[B, 4, H, W]", "[0.0, 1.0] surface reflectance"],
        ["**P_dir**", "**Raw generator direct prediction (graded by all losses)**", "**[B, 4, H, W]**", "**[0.0, 1.0] predicted everywhere**"],
        ["**Y_hat (out)**", "**Final soft-mask blended output: (1-M)⊙S2_c + M⊙P_dir**", "**[B, 4, H, W]**", "**Delivered cloud-free product**"]
    ]
    add_styled_table(s4, left=0.55, top=1.28, width=8.35, height=4.45,
                     headers=headers_s4, rows=rows_s4,
                     col_widths=[1.45, 3.25, 1.45, 2.20], font_size=11.5)

    # Right Callout Box (Just like Slide 71 of Dr. Vinod's DL slides!)
    add_card(s4, left=9.10, top=1.28, width=3.68, height=4.45,
             title="How to Read Shapes & Splits",
             bullets=[
                 ("• Tensor Convention: ", "[B, C, H, W]\n  B = Batch size (4 micro / 16 eff.)\n  C = Spectral channels\n  H × W = 128×128 (Train)\n  H × W = 256×256 (Test)"),
                 ("• Verified Dataset Split:", "\n  • Train: 33,468 patches\n  • Validation: 1,115 patches\n  • Held-out Test: Tile s2_139\n    (strictly untouched!)"),
                 ("• Spatial Resolution: ", "10 m / pixel\n  256×256 px = 2.56 km × 2.56 km")
             ], bg_color=BG_SOFT_GREY, border_color=BORDER_GREY, title_color=ROYAL_BLUE, font_size=12.5, title_size=14.5)

    # Bottom yellow highlight takeaway
    add_card(s4, left=0.55, top=5.90, width=12.23, height=1.05,
             title="",
             bullets=[
                 ("Why B08 Near-Infrared (4th Optical Channel)? ",
                  "Healthy vegetation chlorophyll strongly reflects Near-Infrared (mean = 0.1884 vs. Red = 0.0847). Including B08 alongside RGB (B04, B03, B02) gives scientific-grade agricultural and forestry reconstruction.")
             ], bg_color=BG_YELLOW_HL, border_color=BORDER_AMBER, font_size=13)

    # ==========================================================================
    # SLIDE 5: PREPROCESSING, S2CLOUDLESS & ROLE M1 (OPAQUE CLOUD CUTOUT)
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header_footer(s5, "3. Preprocessing Pipeline, Cloud Masking & Anti-Cheating Cutout",
                      "How We Detect Clouds Without Confusing Snow, Normalize Radar dB, and Force True SAR Fusion", 5)

    s5.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig2_npz_and_s2cloudless.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 6: MASTER DUAL-PHASE PIPELINE ARCHITECTURE
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header_footer(s6, "4. Complete Dual-Phase Architecture: Training vs. Inference",
                      "Top: Phase 1 Joint Adversarial Training (128×128 Crops)   |   Bottom: Phase 2 Native Inference (256×256 Scenes)", 6)

    s6.shapes.add_picture(
        os.path.join(ASSETS_DIR, "pipeline_training_vs_testing_complete.png"),
        Inches(0.55), Inches(1.20), width=Inches(8.55)
    )

    add_card(s6, left=9.25, top=1.20, width=3.53, height=5.75,
             title="7 Roles of the Cloud Mask M",
             bullets=[
                 ("Phase 1: Training (128×128)", ""),
                 ("• M1 (Cutout): ", "Blinds 65% of clouds with 29×29 veil so AI must read SAR."),
                 ("• M2 (Stem Guide): ", "Enters Branch 1 Conv7×7(5→16) with S2_cloudy."),
                 ("• M3 (Decoupled L1): ", "Switches from 1×1 L1 to 4×4 & 8×8 pooled L1 inside M."),
                 ("• M4 (Struct Boost): ", "Boosts VGG + Sobel + Local Std by (1 + 2.0·M)."),
                 ("• M5 (Critic Focus): ", "Weights 16×16 PatchGAN grid by w = 0.25 + 0.75·M."),
                 ("Phase 2: Testing (256×256)", ""),
                 ("• I1 (Stem Guide): ", "Guides full 256² forward pass."),
                 ("• I2 (Soft Blend): ", "Y_hat = (1-M)⊙S2_c + M⊙P_dir.")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE, title_color=CRIMSON, font_size=11.8, title_size=14.5)

    # ==========================================================================
    # SLIDE 7: OPENING THE GENERATOR BLACK BOX (ECRFORMER STEP-BY-STEP)
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header_footer(s7, "5. Generator Architecture: Opening the ECRformer-Light Black Box",
                      "ECRformerAdaptedModel: Decoupled Stem → 4-Stage PixelUnshuffle Encoder → TSA Bottleneck → Mean-Prior Head", 7)

    s7.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig3_ecrformer_step_by_step.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 8: MDTA CHANNEL-TRANSPOSED ATTENTION (CONCRETE NUMERICAL EXAMPLE)
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header_footer(s8, "6. How a 128×128 Trained Model Runs Natively on 256×256 Scenes",
                      "Multi-DConv Head Transposed Attention (MDTA): Computing [C × C] Channel Covariance Instead of [HW × HW]", 8)

    s8.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig4_mdta_numerical_example.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 9: LAYER-BY-LAYER TENSOR RESOLUTION MAP & PARAMETER AUDIT
    # ==========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header_footer(s9, "7. Layer-by-Layer Tensor Resolution Map (128² vs. 256²)",
                      "Every Operation Is Spatial-Dimension Agnostic — Zero Resizing, Zero Cropping, Zero Padding at Test Time", 9)

    headers_s9 = ["Stage", "Module / Operation", "Channels (C)", "Train Shape (128²)", "Test Shape (256²)"]
    rows_s9 = [
        ["Input", "Concat [S1 (2ch), S2_c (4ch), M (1ch)]", "7", "[B, 7, 128, 128]", "[B, 7, 256, 256]"],
        ["Stem", "Branch 0 Conv7×7(2→16) || Branch 1 Conv7×7(5→16)", "16 + 16 = 32", "[B, 32, 128, 128]", "[B, 32, 256, 256]"],
        ["Encoder 1", "2 × ECRformerBlock + CBAM (1ca2+1sa2)", "32", "[B, 32, 128, 128]", "[B, 32, 256, 256]"],
        ["Encoder 2", "PixelUnshuffle(↓2) + Conv + 2 × ECRformerBlock", "64", "[B, 64, 64, 64]", "[B, 64, 128, 128]"],
        ["Encoder 3", "PixelUnshuffle(↓2) + Conv + 1 × ECRformerBlock", "128", "[B, 128, 32, 32]", "[B, 128, 64, 64]"],
        ["**Bottleneck**", "**PixelUnshuffle(↓2) + TSA (MDTA 256×256 Matrix)**", "**256**", "**[B, 256, 16, 16]**", "**[B, 256, 32, 32]**"],
        ["Decoder 3→1", "3 × PixelShuffle(↑2) + Skip Bridges 2, 1, 0", "128 → 64 → 64", "[B, 64, 128, 128]", "[B, 64, 256, 256]"],
        ["Output Head", "final_conv: Conv3×3(64→4) + mean_prior bias", "4", "P_dir [B, 4, 128, 128]", "P_dir [B, 4, 256, 256]"],
        ["**Critic / Gate**", "**Train: PatchGAN D  |  Test: Soft-Mask Gate (I2)**", "**1 (Train) / 4 (Test)**", "**[B, 1, 16, 16] Logits**", "**Y_hat [B, 4, 256, 256]**"]
    ]
    add_styled_table(s9, left=0.55, top=1.25, width=8.55, height=5.65,
                     headers=headers_s9, rows=rows_s9,
                     col_widths=[1.15, 3.10, 1.25, 1.50, 1.55], font_size=11)

    add_card(s9, left=9.25, top=1.25, width=3.53, height=5.65,
             title="Verified Parameter & Speed Audit",
             bullets=[
                 ("• Checkpoint File:", "\n  best_model.pth (~34.3 MB)"),
                 ("• Total Checkpoint Params:", "\n  8,316,228 (8.31M) parameters\n  (includes multi-scale SDFL\n  auxiliary heads & buffers)."),
                 ("• Active Inference Generator:", "\n  3.62M active backbone params\n  (num_refine = 0 bypass)."),
                 ("• Differential Learning Rate:", "\n  • Generator LR: 1.2e-4\n  • SAR Stem Multiplier: 2.0×\n    (forces rapid radar adaptation)\n  • Critic D LR: 2.5e-4\n  • EMA Decay: 0.990"),
                 ("• Inference Latency:", "\n  ~0.04 seconds per 256×256\n  patch on single desktop GPU.")
             ], bg_color=BG_SOFT_GREEN, border_color=BORDER_GREEN, title_color=DEEP_GREEN, font_size=12, title_size=14.5)

    # ==========================================================================
    # SLIDE 10: WHY STANDARD L1 BLURS & HOW ROLES M3 & M4 FIX IT
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header_footer(s10, "8. Difficulty: Why Standard L1 + SSIM Produces Blurry Gray Smudges",
                      "Diagnosing the Conditional-Mean Trap & 1-Pixel Radar Shift Penalty — And How Roles M3 & M4 Solve Them", 10)

    s10.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig5_blur_trap_and_scale_decoupled_l1.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 11: COMPLETE 7-LOSS OBJECTIVE FORMULATION TABLE
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header_footer(s11, "9. Complete 7-Loss Training Formulation (Where Each Loss Is Used)",
                      "All 7 Losses Supervise the Raw Generator Prediction P_dir Directly (Never the Blended Image)", 11)

    headers_s11 = ["#", "Loss Name & Code Module", "Mathematical Formulation / Mechanism", "Weight", "Where & Why It Is Used"]
    rows_s11 = [
        ["1", "Scale-Decoupled L1\n(patchgan_loss.py)", "0.35·|P-Y|⊙(1-0.8M) + 0.40·|P↓4-Y↓4|⊙(1+M↓4)\n+ 0.25·|P↓8-Y↓8|⊙(1+M↓8) + 0.10·L_aux_SDFL", "1.00", "Role M3: Exact 1×1 pixels in clear sky; 4×4 & 8×8 pooled regional color in clouds (frees 1-px SAR edges)."],
        ["2", "PatchGAN Hinge Adv\n(patchgan_loss.py)", "L_adv = -E[ D(P_dir, S1, M) ⊙ (0.25 + 0.75·M↓8) ]\nCritic D trained with Hinge loss on Real vs Fake", "w_adv =\n0.015", "Role M5: Penalizes blurry 70×70 patches 4× harder inside clouds; forces realistic high-frequency texture."],
        ["3", "Feature Matching\n(patchgan_loss.py)", "L_FM = (1/4) Σ_i | D^(i)(P_dir) - D^(i)(Y) | ⊙ (0.3+0.7M)\n across 4 intermediate critic layers [f1..f4]", "w_fm =\n0.15", "Stabilizes adversarial training so PatchGAN sharpens edges without hallucinating fake artifacts."],
        ["4", "Cloud-Boosted VGG-16\n(cloud_structure_loss.py)", "L1 on VGG-16 relu1_2, relu2_2, relu3_3 features\n0.6·VGG(RGB) + 0.4·VGG(NIR-R-G) × (1 + 2M)", "w_vgg =\n0.005", "Role M4: Enforces semantic & perceptual realism in both visible RGB and Near-Infrared vegetation bands."],
        ["5", "Multi-Scale Gradients\n(cloud_structure_loss.py)", "(|∇x P - ∇x Y| + |∇y P - ∇y Y|) ⊙ (1 + 2M)\ncomputed across 1×, 2×, and 4× average-pooled scales", "w_grad =\n0.25", "Role M4: Directly aligns sharp horizontal and vertical road, river, and field boundaries across scales."],
        ["6", "Edge Map Correlation\n(cloud_structure_loss.py)", "L_corr = 1 - 0.5 · (PearsonCorr(|∇P|, |∇Y|)_1x + _2x)\nevaluated inside cloudy mask region (M > 0.2)", "w_corr =\n0.0025", "Role M4: Maximizes cosine/Pearson co-linearity of gradient magnitudes inside the cloud core."],
        ["7", "Local 16×16 Std Contrast\n(cloud_structure_loss.py)", "| Std_16×16(P) - Std_16×16(Y) | ⊙ (1 + 2M)\n+ Detail-Ratio floor penalty if σ_P / σ_Y < 0.92", "w_std =\n0.35", "Role M4: Forces local patch contrast (roughness) inside clouds to match real clear-sky terrain variance."]
    ]
    add_styled_table(s11, left=0.55, top=1.22, width=12.23, height=5.75,
                     headers=headers_s11, rows=rows_s11,
                     col_widths=[0.45, 2.25, 4.35, 0.95, 4.23], font_size=10.5)

    # ==========================================================================
    # SLIDE 12: OPENING THE CRITIC BLACK BOX (11-CH PATCHGAN)
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header_footer(s12, "10. Critic Architecture: 11-Channel Conditional PatchGAN (Role M5)",
                      "How the Art Detective Spots Blurry Cloud Holes Using an Explicit 5×5 High-Pass Detail Residual", 12)

    s12.shapes.add_picture(
        os.path.join(DIAG_DIR, "slide_fig6_patchgan_detective_grid.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    # ==========================================================================
    # SLIDE 13: PHASE 2 NATIVE 256x256 INFERENCE & SOFT-MASK BLENDING
    # ==========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header_footer(s13, "11. Phase 2: Native 256×256 Inference & Soft-Mask Blending",
                      "How We Deliver 100% Authentic Clear-Sky Pixels Alongside Razor-Sharp Cloud Inpainting", 13)

    add_card(s13, left=0.55, top=1.28, width=5.95, height=2.65,
             title="Step 1: Full-Scene 256×256 Forward Pass (Role I1)",
             bullets=[
                 ("• No Cropping or Resizing: ", "We pass the full [1, 7, 256, 256] tile directly into ECRformerAdaptedModel (EMA weights)."),
                 ("• PatchGAN Discarded: ", "The discriminator D is only a training teacher. At test time it is completely removed (zero memory/compute cost)."),
                 ("• Raw Output P_dir: ", "Backbone outputs a complete, sharp 4-channel 256×256 optical prediction in 0.04 seconds.")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE)

    add_card(s13, left=6.83, top=1.28, width=5.95, height=2.65,
             title="Step 2: Soft-Mask Radiometric Gate (Role I2)",
             bullets=[
                 ("• Blending Equation: ", "Y_hat = (1.0 - M) ⊙ S2_cloudy + M ⊙ P_dir"),
                 ("• Clear Sky (M = 0.0): ", "Keeps 100% of the authentic satellite observation S2_cloudy. Never overwrite real clear ground with an AI guess!"),
                 ("• Cloud Core (M = 1.0): ", "Substitutes 100% of the SAR-guided PatchGAN reconstruction P_dir.")
             ], bg_color=BG_SOFT_GREEN, border_color=BORDER_GREEN)

    add_card(s13, left=0.55, top=4.15, width=12.23, height=2.75,
             title="Step 3: Solving Unmasked Cloud Fringes & Shadows (Multi-Band Harmonization)",
             bullets=[
                 ("• Real-World Challenge Discovered in Diagnostics: ",
                  "ESA's s2cloudless detector thresholds at 0.4, which occasionally leaves thin semi-transparent cloud fringes or dark cloud cast shadows unmasked (M = 0). Naive hard blending leaks those fringes into Y_hat."),
                 ("• Our Engineering Fix: ",
                  "1) 3-step morphological dilation (radius 2) + 11×11 Gaussian feathering (σ=2.0) expands M into thin cloud borders.\n"
                  "  2) Multi-Band Laplacian Feathering (σ=6.0) & local radiometric harmonization smoothly transition albedo across cloud boundaries with zero visible cutout seams."),
                 ("• RGB Visualization Conversion: ",
                  "Raw physical surface reflectance averages ~0.08–0.18. To display as standard 8-bit RGB PNGs, we extract bands [B04, B03, B02], multiply by 3.0× visual gain, clamp to [0, 1], and scale to [0..255].")
             ], bg_color=BG_SOFT_AMBER, border_color=BORDER_AMBER, font_size=13)

    # ==========================================================================
    # SLIDE 14: 5-STAGE VISUAL PROGRESSION SHOWCASE (256x256)
    # ==========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header_footer(s14, "12. Visual Results: 5-Stage Output Progression (256×256 Native)",
                      "Evaluated on Named ROIs1970_fall Validation Scenes Across Suburban, River/Agricultural, and Forest Biomes", 14)

    s14.shapes.add_picture(
        os.path.join(ASSETS_DIR, "final_guide_showcase_5stage.png"),
        Inches(0.55), Inches(1.22), width=Inches(7.80)
    )

    add_card(s14, left=8.55, top=1.22, width=4.23, height=5.75,
             title="Understanding Columns 1 to 5",
             bullets=[
                 ("Col 1 — Original Input:", "\n  Cloudy Sentinel-2 + SAR VV/VH + Mask M."),
                 ("Col 2 — Ground Truth:", "\n  Clear Sentinel-2 reference (Y)."),
                 ("Col 3 — Pre-GAN Baseline:", "\n  Standard L1+SSIM ECRformer.\n  Notice blurry smudge in cloud core!"),
                 ("Col 4 — PatchGAN Direct (P_dir):", "\n  Raw generator output after 7-loss + PatchGAN training. Crisp roads & fields restored!"),
                 ("Col 5 — Final Blended (Y_hat):", "\n  Soft-mask fusion keeping exact clear sky + sharp cloud core."),
                 ("Scenes Shown:", "\n  • Row 1: s2_22_p428 (64.0% cloud)\n  • Row 2: s2_40_p104 (96.9% cloud)\n  • Row 3: s2_22_p108 (78.4% cloud)")
             ], bg_color=BG_SOFT_GREY, border_color=BORDER_GREY, title_color=CRIMSON, font_size=11.8, title_size=14.5)

    # ==========================================================================
    # SLIDE 15: 128x128 TRAINING CROP VS 256x256 EVALUATION DEEP-DIVE
    # ==========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header_footer(s15, "13. Visual Deep-Dive: Inside the 128×128 Crop → 256×256 Scene",
                      "Visualizing the 5×5 High-Pass Detail Residual R_HP and PatchGAN's 16×16 Critic Grid on Val #420", 15)

    s15.shapes.add_picture(
        os.path.join(ASSETS_DIR, "final_guide_128_vs_256_zoom.png"),
        Inches(0.55), Inches(1.22), width=Inches(12.23)
    )

    add_card(s15, left=0.55, top=5.35, width=12.23, height=1.62,
             title="What Figure 3 Proves (Left to Right)",
             bullets=[
                 ("• Panel 1 & 2: ", "Shows the 128×128 random training crop window inside the native 256×256 scene (ROIs1970_fall_s2_22_p428, 64% cloud)."),
                 ("• Panel 3 vs. Panel 5: ", "Pre-GAN baseline (Panel 3) smears the suburban road grid into a gray blur (13.3% HF detail), whereas our PatchGAN-trained generator P_dir (Panel 5) restores crisp street blocks (77.1% HF detail)."),
                 ("• Panel 4 (The Secret): ", "Amplified 5×5 High-Pass Residual R_HP overlaid with PatchGAN's 16×16 critic grid (each cell = 70×70 px neighborhood).")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE, font_size=12.2, title_size=14)

    # ==========================================================================
    # SLIDE 16: QUANTITATIVE PROGRESSION TABLE ON NAMED SCENES
    # ==========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header_footer(s16, "14. Quantitative Results Part 1: 5-Stage Progression on Named Scenes",
                      "Comparing Stage 3 (Pre-GAN Baseline) vs. Stage 4 (PatchGAN Direct P_dir) vs. Stage 5 (Final Blended Y_hat)", 16)

    headers_s16 = ["Scene Patch ID (Biome)", "Pipeline Stage (256×256)", "Cloud %", "PSNR (dB) ↑", "SAM (°) ↓", "Edge Corr ↑", "HF Detail ↑", "Visual Quality in Cloud Core"]
    rows_s16 = [
        ["ROIs1970_fall_s2_22_p428\n(Val #420 — Suburban)", "Stage 3: Pre-GAN Baseline", "64.0%", "31.79 dB", "4.12°", "0.430", "13.3%", "Over-smoothed road grid"],
        ["ROIs1970_fall_s2_22_p428", "Stage 4: PatchGAN Direct (P_dir)", "64.0%", "36.65 dB", "2.58°", "0.865", "77.1%", "Crisp streets & housing blocks"],
        ["ROIs1970_fall_s2_22_p428", "**Stage 5: Final Blended (Y_hat)**", "**64.0%**", "**37.95 dB**", "**2.23°**", "**0.869**", "**77.5%**", "**Exact clear sky + Sharp cloud**"],
        ["ROIs1970_fall_s2_40_p104\n(Val #725 — River/Farms)", "Stage 3: Pre-GAN Baseline", "96.9%", "33.83 dB", "4.85°", "0.307", "15.9%", "Blurry agricultural boundaries"],
        ["ROIs1970_fall_s2_40_p104", "Stage 4: PatchGAN Direct (P_dir)", "96.9%", "37.30 dB", "2.41°", "0.814", "65.3%", "Sharp crop field geometry"],
        ["ROIs1970_fall_s2_40_p104", "**Stage 5: Final Blended (Y_hat)**", "**96.9%**", "**42.03 dB**", "**1.54°**", "**0.818**", "**66.8%**", "**Seamless 96.9% recovery**"],
        ["ROIs1970_fall_s2_22_p108\n(Val #350 — Forest/Road)", "Stage 3: Pre-GAN Baseline", "78.4%", "35.58 dB", "3.94°", "0.426", "13.6%", "Smudged forest & highway"],
        ["ROIs1970_fall_s2_22_p108", "Stage 4: PatchGAN Direct (P_dir)", "78.4%", "39.31 dB", "2.12°", "0.801", "79.1%", "Razor-sharp highway line"],
        ["ROIs1970_fall_s2_22_p108", "**Stage 5: Final Blended (Y_hat)**", "**78.4%**", "**40.66 dB**", "**1.66°**", "**0.804**", "**79.5%**", "**Zero seam + Full detail**"]
    ]
    add_styled_table(s16, left=0.55, top=1.22, width=12.23, height=4.55,
                     headers=headers_s16, rows=rows_s16,
                     col_widths=[2.35, 2.35, 0.85, 1.15, 0.95, 1.05, 1.05, 2.48], font_size=10.5)

    add_card(s16, left=0.55, top=5.92, width=12.23, height=1.05,
             title="",
             bullets=[
                 ("How Each Metric Is Defined: ",
                  "• PSNR (dB) ↑: Peak Signal-to-Noise Ratio (radiometric accuracy).   "
                  "• SAM (°) ↓: Spectral Angle Mapper in degrees across 4 bands (color fidelity; <2.5° is near-exact).   "
                  "• Edge Corr ↑: Pearson correlation of Sobel gradient magnitudes.   "
                  "• HF Detail ↑: Ratio of high-pass spatial energy vs. Ground Truth.")
             ], bg_color=BG_YELLOW_HL, border_color=BORDER_AMBER, font_size=12.2)

    # ==========================================================================
    # SLIDE 17: MULTI-STRATA BENCHMARK & PERCEPTION-DISTORTION TRADE-OFF
    # ==========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    add_header_footer(s17, "15. Quantitative Results Part 2: Cloud Strata & Scientific Trade-Off",
                      "100% Honest Evaluation Across 4 Atmospheric Regimes (256×256) — Understanding PSNR vs. Sharpness", 17)

    headers_s17 = ["Atmospheric Regime", "Val Pool", "Model Checkpoint", "PSNR (Under Cloud)", "PSNR (Full Scene)", "Detail Ratio (Sharpness)", "Edge Corr (grad_corr)", "MAE ↓"]
    rows_s17 = [
        ["~10% Cloud (Sparse)", "117 patches", "Baseline (50 ep L1+SSIM)", "32.55 dB", "33.17 dB", "0.472 (Blurry)", "0.425", "0.0183"],
        ["~10% Cloud (Sparse)", "117 patches", "**Sweet-Spot Best (Ours)**", "**32.23 dB**", "**33.13 dB**", "**0.907 (+92%)**", "**0.414**", "**0.0191**"],
        ["~40% Cloud (Moderate)", "187 patches", "Baseline (50 ep L1+SSIM)", "33.24 dB", "34.25 dB", "0.448 (Blurry)", "0.478", "0.0153"],
        ["~40% Cloud (Moderate)", "187 patches", "**Sweet-Spot Best (Ours)**", "**32.09 dB**", "**33.31 dB**", "**0.907 (+102%)**", "**0.476**", "**0.0168**"],
        ["Haze (Semi-Transparent)", "283 patches", "Baseline (50 ep L1+SSIM)", "32.57 dB", "33.47 dB", "0.387 (Heavy blur)", "0.393", "0.0162"],
        ["Haze (Semi-Transparent)", "283 patches", "**Sweet-Spot Best (Ours)**", "**31.63 dB**", "**32.80 dB**", "**0.902 (+133%)**", "**0.406 (+3.3%)**", "**0.0175**"],
        ["70%–100% (Dense Overcast)", "370 patches", "Baseline (50 ep L1+SSIM)", "30.37 dB", "30.34 dB", "0.632 (Smudged)", "0.587", "0.0208"],
        ["70%–100% (Dense Overcast)", "370 patches", "**Sweet-Spot Best (Ours)**", "**30.02 dB**", "**29.98 dB**", "**0.931 (+47%)**", "**0.573**", "**0.0217**"]
    ]
    add_styled_table(s17, left=0.55, top=1.22, width=12.23, height=3.85,
                     headers=headers_s17, rows=rows_s17,
                     col_widths=[2.15, 1.15, 2.25, 1.50, 1.45, 1.65, 1.15, 0.93], font_size=10.5)

    add_card(s17, left=0.55, top=5.20, width=12.23, height=1.78,
             title="Why Does Raw PSNR Drop by ~0.3–1.1 dB When Sharpness Doubles? (The Perception–Distortion Trade-Off)",
             bullets=[
                 ("• Mathematical Truth (Blau & Michaeli, CVPR 2018): ",
                  "By definition, the conditional mean E[Y|X] (a blurry smudge!) achieves the highest possible pixel-by-pixel PSNR / lowest MSE."),
                 ("• What Happens When We Restore Sharp Edges: ",
                  "When our PatchGAN model draws a razor-sharp road guided by Sentinel-1 SAR (which has a natural 1–2 px orbital shift vs. Sentinel-2), pixel-wise 1×1 PSNR penalizes that 1-px shift by ~0.3–1.1 dB, while High-Frequency Detail Ratio jumps from 0.387–0.632 → 0.902–0.931 (+47% to +133% sharper!)."),
                 ("• Takeaway: ",
                  "Maintaining >= 30.0 dB under-cloud PSNR while recovering >90% natural terrain sharpness is the exact adversarial sweet spot.")
             ], bg_color=BG_SOFT_RED, border_color=BORDER_RED, font_size=12, title_size=14)

    # ==========================================================================
    # SLIDE 18: HONEST LIMITATIONS, ENGINEERING LESSONS & CONCLUSION
    # ==========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    add_header_footer(s18, "16. Measured Limitations, Engineering Lessons & Conclusion",
                      "Complete Scientific Transparency: What Works, What Has Limits, and Key Takeaways", 18)

    add_card(s18, left=0.55, top=1.28, width=5.95, height=4.15,
             title="Measured Limitations (Zero Hidden Flaws)",
             bullets=[
                 ("1. Unmasked Cloud Shadows & Thin Fringe:",
                  "\n   ESA's s2cloudless detects bright clouds (M=1) but often marks dark cloud cast shadows on the ground as clear (M=0). Under strict (1-M)⊙S2_c blending, dark ground shadows remain unless shadow-gated feathering is applied."),
                 ("2. Temporal Acquisition Gap in SEN12MS-CR:",
                  "\n   Cloudy S2_c and clear target Y are captured on different days. Seasonal crop changes create a natural radiometric floor (~0.015 MAE)."),
                 ("3. 128² Center-Crop vs. 256² Full-Scene Eval:",
                  "\n   The two evaluation regimes differ by up to ~2.3 dB because cloud fraction varies between the patch center and borders."),
                 ("4. Late-Epoch GAN Over-Pressure:",
                  "\n   Training too long with high w_adv introduces synthetic radar speckle grain; stopping at the Sweet-Spot EMA checkpoint prevents this.")
             ], bg_color=BG_SOFT_AMBER, border_color=BORDER_AMBER, font_size=11.8, title_size=14.5)

    add_card(s18, left=6.83, top=1.28, width=5.95, height=4.15,
             title="Core Contributions & Summary",
             bullets=[
                 ("1. Defeated the Over-Smoothing Trap:",
                  "\n   Boosted high-frequency terrain detail retention under thick clouds from 21%–38% (Baseline) to 85.8%–93.1% (Sweet-Spot Best)."),
                 ("2. 5-Role Cloud-Mask Guided Training (M1–M5):",
                  "\n   Combined Opaque Cloud Cutout (M1), Decoupled Stem (M2), Scale-Decoupled L1 (M3), Cloud-Boosted VGG/Sobel (M4), and 11-Ch High-Pass PatchGAN (M5)."),
                 ("3. Seamless 128² → 256² Resolution Scaling:",
                  "\n   Leveraged MDTA [C×C] channel covariance so memory-efficient 128×128 training executes natively on 256×256 tiles in 0.04s."),
                 ("4. Open & Reproducible Deployment:",
                  "\n   Weights hosted on Hugging Face (vyyyyyyy/ecrformer-satellite-cloud-removal) with an interactive Next.js comparison showcase.")
             ], bg_color=BG_SOFT_GREEN, border_color=BORDER_GREEN, font_size=11.8, title_size=14.5)

    add_card(s18, left=0.55, top=5.62, width=12.23, height=1.35,
             title="Thank You!   |   Questions & Discussion",
             bullets=[
                 ("Project Team: ", "Agnal K. V.  •  Bivin Balu  •  Vaishnav T. Prakash"),
                 ("Project Guide: ", "Dr. Sabu M. K. (CUSAT)"),
                 ("Repository & Weights: ", "github.com/yovyshh/ecrformer   •   huggingface.co/vyyyyyyy/ecrformer-satellite-cloud-removal")
             ], bg_color=BG_SOFT_BLUE, border_color=BORDER_BLUE, title_color=CRIMSON, font_size=13.5, title_size=17)

    prs.save(OUT_PPTX_PROJECT)
    prs.save(OUT_PPTX_DOWNLOADS)
    print("Saved PPTX to:")
    print("  1)", OUT_PPTX_PROJECT)
    print("  2)", OUT_PPTX_DOWNLOADS)


if __name__ == "__main__":
    create_deck()
