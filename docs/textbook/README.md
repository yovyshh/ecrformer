# Understanding ECRformer-Light: A Beginner-to-Research-Level Textbook

This directory contains the complete LaTeX source code, modular TikZ figures, verified BibTeX citations, and compiled PDF textbook for:

> **"Understanding ECRformer-Light: A Beginner-to-Research-Level Guide to Multimodal Satellite Image Cloud Removal"**  
> *From Neural Network Fundamentals to SAR-Guided Optical Reconstruction, Transformer Attention, Cloud Masks, Loss Functions, and Model Training*

---

## 📁 Directory Structure

```text
docs/textbook/
├── ecrformer_textbook.tex     # Master LaTeX book entry point
├── references.bib             # Verified academic BibTeX references
├── README.md                  # Compilation instructions & overview
├── ecrformer_textbook.pdf     # The compiled, publication-ready PDF textbook
├── figures/                   # Standalone, editable TikZ vector diagrams
│   ├── fig_tensor_layout.tex      # 7-channel input tensor & DecoupledEncoder split
│   ├── fig_pipeline_overview.tex  # Complete data, training, & inference pipeline
│   ├── fig_encoder_decoder.tex    # 4-stage U-Net hierarchy with exact dimensions
│   ├── fig_ecrformer_block.tex    # MDTA + MDWA + GDFN inside ECRformerBlock
│   ├── fig_patchgan_11ch.tex      # 11-channel High-Pass PatchGAN Discriminator
│   └── fig_backprop_graph.tex     # Forward & backward gradient computational graph
└── chapters/                  # 24 modular textbook chapters & appendix
    ├── ch01.tex               # Understanding the Satellite Cloud Removal Problem
    ├── ch02.tex               # Understanding Satellite Image Bands and Tensors
    ├── ch03.tex               # Python, PyTorch, and Deep Learning Foundations
    ├── ch04.tex               # Neural Networks From Scratch
    ├── ch05.tex               # Convolutional Neural Networks and Image Features
    ├── ch06.tex               # The Complete Data Pipeline
    ├── ch07.tex               # SEN12MS-CR Dataset and Preprocessing
    ├── ch08.tex               # Cloud Masks and Mask-Guided Learning
    ├── ch09.tex               # Encoder-Decoder Architecture
    ├── ch10.tex               # Transformers and Attention Mechanisms From Scratch
    ├── ch11.tex               # ECRformer Architecture in Detail
    ├── ch12.tex               # Understanding the Loss Functions
    ├── ch13.tex               # Generative Adversarial Networks — GANs From Scratch
    ├── ch14.tex               # Backpropagation Through the Actual Architecture
    ├── ch15.tex               # Training Loop and Experiment Configuration
    ├── ch16.tex               # Evaluation Metrics and Result Interpretation
    ├── ch17.tex               # Inference and Final Satellite Image Reconstruction
    ├── ch18.tex               # Understanding the Entire Codebase
    ├── ch19.tex               # Common Problems, Debugging, and Failure Analysis
    ├── ch20.tex               # Understanding the Novel Modifications
    ├── ch21.tex               # Ablation Studies and Scientific Evaluation
    ├── ch22.tex               # A Complete Worked Example
    ├── ch23.tex               # Frequently Asked Questions
    ├── ch24.tex               # Glossary and Learning Roadmap
    └── appendix_traceability.tex # Master Traceability & Parameter Audit
```

---

## 🛠️ How to Compile the PDF

### Recommended: Using Tectonic (Zero-Configuration Engine)
Tectonic automatically resolves packages, runs BibTeX, and handles multiple passes in a single command:

```powershell
# From the project root (C:\Users\Windows 11 Pro\Videos\Projects\ECRformer):
tectonic -X compile docs/textbook/ecrformer_textbook.tex
```

Or using the local executable path:
```powershell
& "$env:LOCALAPPDATA\tectonic\tectonic.exe" -X compile docs/textbook/ecrformer_textbook.tex
```

### Alternative: Using TeX Live / MiKTeX (Standard Toolchain)
```bash
cd docs/textbook
pdflatex ecrformer_textbook.tex
bibtex ecrformer_textbook
pdflatex ecrformer_textbook.tex
pdflatex ecrformer_textbook.tex
```

---

## 🔬 Core Architectural Facts Verified in the Book
1. **Active Generator Parameter Count:** Exactly **3,619,070 parameters** across 277 tensors (not 8.3M, which was the sum of generator + EMA shadow + discriminator stored together in the `.pth` checkpoint).
2. **Hybrid Dual Attention:** Every single `ECRformerBlock` contains **both** Transposed Attention (MDTA, channel-wise cross-covariance) and Multi-Dilated Window Attention (MDWA, local spatial dilation rates $[1, 2, 3, 4]$) in series, scaled by learnable residual LayerScale parameters ($\gamma = 0.01$).
3. **11-Channel High-Pass Discriminator:** The active Stage 4 sweetspot model was trained with a Spectral-Normalized PatchGAN receiving: base optical ($3.0 \times \mathbf{Y}$, 4 ch), high-pass residual ($10.0 \times (\mathbf{Y} - \text{AvgPool}_{5\times 5}(\mathbf{Y}))$, 4 ch), Sentinel-1 SAR condition ($\mathbf{X}_{S1}$, 2 ch), and soft cloud mask ($\mathbf{M}$, 1 ch).
4. **Soft-Mask Output Gate:** Clear pixels are preserved with 100% radiometric truth via $\hat{\mathbf{Y}} = (1 - \mathbf{M})\odot \mathbf{X}_{S2} + \mathbf{M}\odot \mathbf{P}_{\text{dir}}$.
