# ECRformer Cloud Removal — Frontend (v2)

Next.js frontend application for interactive multispectral Sentinel-2 cloud removal using the ECRformer architecture.

## Overview

The frontend connects directly to a locally running FastAPI backend (`hf_deploy/space`):
- Local backend URL configured via `BACKEND_URL` in `.env.local` (default: `http://127.0.0.1:7860`).
- No external Hugging Face cloud dependencies or mock data.

## API Proxy Routes

All model operations and dataset requests are routed through Next.js server-side API handlers:
- `GET /api/samples`: Retrieves the list of available samples from the backend.
- `GET /api/samples/[id]/preview/[kind]`: Streams pre-rendered preview PNGs (`cloudy`, `sar`, `mask`) with HTTP cache headers.
- `POST /api/remove-clouds`: Dispatches inference requests with `{ imageId }` to the backend and returns computed output stages (base64 PNG data URIs) and metrics (PSNR, SAM in degrees, Edge Correlation, HF Retention).

## Quick Start

```bash
# Install dependencies
npm install

# Set up local backend endpoint
cp .env.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

