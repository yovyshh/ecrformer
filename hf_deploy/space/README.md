---
title: ECRformer Cloud Removal Space
emoji: 🛰️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ECRformer Cloud Removal Space

FastAPI service for Sentinel-1/Sentinel-2 multimodal satellite cloud removal using ECRformer.

## Endpoints

- `GET /health`: Health and model readiness status.
- `GET /samples`: List available demo satellite scenes with preview links.
- `GET /samples/{id}/preview/{kind}`: Retrieve PNG previews (`cloudy`, `sar`, `mask`).
- `POST /remove-clouds`: Run inference pipeline (`{"imageId": "<sample_id>"}`) and return stages & metrics.

## Configuration (Environment Variables)

- `HF_MODEL_REPO`: Hugging Face repo holding model weights and `config.json`.
- `HF_DATASET_REPO`: Hugging Face dataset repo holding `index.json`, `samples/`, and `previews/`.
- `HF_TOKEN`: Hugging Face token for private repos (optional).
- `LOCAL_MODEL_DIR`: Local filesystem fallback for model weights and config.
- `LOCAL_DATASET_DIR`: Local filesystem fallback for dataset index and samples.
- `INDEX_TTL`: Cache duration in seconds for `index.json` (default 60s).
- `TORCH_THREADS`: PyTorch intra-op CPU threads (default 2).
- `ALLOWED_ORIGINS`: Comma-separated CORS allowed origins (default `*`).

