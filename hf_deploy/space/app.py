"""FastAPI application serving ECRformer cloud removal on HF Space."""

import os
import re
import traceback
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import torch

from pipeline import CloudRemovalPipeline, ID_PATTERN


pipeline: Optional[CloudRemovalPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    print("[App] Initializing CloudRemovalPipeline...")
    pipeline = CloudRemovalPipeline()
    yield
    print("[App] Shutting down.")


app = FastAPI(title="ECRformer Cloud Removal Space", lifespan=lifespan)

# CORS setup
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models matching frontend TypeScript interfaces
class SamplePreviews(BaseModel):
    cloudy: str
    sar: str
    mask: str


class Sample(BaseModel):
    id: str
    filename: str
    cloudCoverage: int
    previews: SamplePreviews


class Metrics(BaseModel):
    psnr: float
    sam: float
    edgeCorr: float
    hfRetention: float


class ResultStages(BaseModel):
    baseline: str
    sharpened: str
    final: str
    target: str


class ResultMetrics(BaseModel):
    cloudy: Metrics
    baseline: Metrics
    sharpened: Metrics
    final: Metrics


class Result(BaseModel):
    stages: ResultStages
    metrics: ResultMetrics


class RemoveCloudsRequest(BaseModel):
    imageId: str


class HealthResponse(BaseModel):
    status: str
    modelLoaded: bool
    baseline: str
    sampleCount: int
    device: str
    torchVersion: str
    cudaVersion: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
def health():
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline is not initialized")
    samples = pipeline.get_index()
    cuda_ver = torch.version.cuda if (torch.cuda.is_available() and pipeline.torch_device.type == "cuda") else None
    return {
        "status": "ok",
        "modelLoaded": pipeline.model_loaded,
        "baseline": pipeline.baseline_status,
        "sampleCount": len(samples),
        "device": pipeline.device,
        "torchVersion": torch.__version__,
        "cudaVersion": cuda_ver,
    }


@app.get("/samples", response_model=List[Sample])
def list_samples():
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline is not initialized")
    raw_samples = pipeline.get_index()
    samples: List[Sample] = []
    for item in raw_samples:
        s_id = item.get("id", "")
        fn = item.get("filename", s_id)
        cc = int(item.get("cloudCoverage", 0))
        samples.append(
            Sample(
                id=s_id,
                filename=fn,
                cloudCoverage=cc,
                previews=SamplePreviews(
                    cloudy=f"/samples/{s_id}/preview/cloudy",
                    sar=f"/samples/{s_id}/preview/sar",
                    mask=f"/samples/{s_id}/preview/mask",
                ),
            )
        )
    return samples


@app.get("/samples/{sample_id}/preview/{kind}")
def get_preview(sample_id: str, kind: str):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline is not initialized")
    if not ID_PATTERN.match(sample_id):
        raise HTTPException(status_code=400, detail=f"Invalid sample ID format: {sample_id}")
    if kind not in ["cloudy", "sar", "mask"]:
        raise HTTPException(status_code=400, detail=f"Invalid preview kind: {kind}")

    try:
        data = pipeline.get_preview_bytes(sample_id, kind)
        return Response(
            content=data,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/remove-clouds", response_model=Result)
def remove_clouds(payload: RemoveCloudsRequest, response: Response):
    if pipeline is None or not pipeline.model_loaded:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    image_id = payload.imageId
    if not ID_PATTERN.match(image_id):
        raise HTTPException(status_code=400, detail=f"Invalid imageId: '{image_id}'")

    try:
        result, total_ms = pipeline.run(image_id, return_timing=True)
        response.headers["X-Timing-Ms"] = f"{total_ms:.2f}"
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal inference error")

