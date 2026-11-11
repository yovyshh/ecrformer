<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Backend Integration & Architecture

- **Local Backend**: The frontend connects to the local FastAPI backend specified by `BACKEND_URL` (default: `http://127.0.0.1:7860`).
- **No Mocks**: No mock data or external placeholder image URLs (e.g. picsum) are used. All sample listings, previews, and inference outputs come directly from the local backend via `src/app/api/` proxy endpoints.
- **Metric Definitions**:
  - SAM (Spectral Angle Mapper): Displayed in degrees (°), lower is better.
  - HF Retention: Frequency ratio against ground truth target (1.0 indicates perfect high-frequency match).
