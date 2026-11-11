---
license: apache-2.0
tags:
- remote-sensing
- earth-observation
- cloud-removal
- pytorch
- vision
pipeline_tag: image-to-image
---

# ECRformer Cloud Removal Model Weights

Production and baseline model checkpoints for ECRformer (Edge-guided Cross-modal Recurrent Transformer for Multimodal Cloud Removal).

## Checkpoints
- `ecrformer_sweetspot_ema.pt`: Production PatchGAN model trained with EMA weights (`ecrformer_sweetspot_best`).
- `ecrformer_baseline.pt`: Baseline model weights (`ecrformer_baseline`).
- `config.json`: Architecture parameters and input tensor specifications.

