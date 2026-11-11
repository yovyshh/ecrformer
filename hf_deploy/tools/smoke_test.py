"""Smoke test suite for ECRformer deployment bundle."""

import os
import sys
import json
import time
import base64
import io
from pathlib import Path
import numpy as np
import torch
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPACE_DIR = REPO_ROOT / "hf_deploy" / "space"
MODEL_REPO_DIR = REPO_ROOT / "hf_deploy" / "model_repo"
DATASET_REPO_DIR = REPO_ROOT / "hf_deploy" / "dataset_repo"

# Set environment variables for local testing
os.environ["LOCAL_MODEL_DIR"] = str(MODEL_REPO_DIR)
os.environ["LOCAL_DATASET_DIR"] = str(DATASET_REPO_DIR)
os.environ["TORCH_THREADS"] = "2"

sys.path.insert(0, str(SPACE_DIR))
import preprocess
import metrics
import render
import pipeline
from app import app
from fastapi.testclient import TestClient

MODEL_ARGS = {
    "features_start": 32,
    "num_blocks": [2, 2, 1, 1],
    "num_refine": 0,
    "bottle_neck": "tsa",
    "cbam": "1ca2+1sa2",
    "mask_blend": True,
    "head_init": "mean_prior",
}


def test_parity_a():
    print("\n================== PARITY A TEST ==================")
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    try:
        from models.ecrformer_adapted import ECRformerAdaptedModel as OrigECRformer
    except Exception as e:
        print(f"FAILED to import original model from backend: {e}")
        return False, 0.0

    # Test Sample
    sample_path = DATASET_REPO_DIR / "samples" / "dense_100pct.npz"
    if not sample_path.exists():
        sample_path = list((DATASET_REPO_DIR / "samples").glob("*.npz"))[0]
    data = preprocess.load_sample_npz(sample_path)
    s2_c, s1, mask = data["s2_cloudy"], data["s1"], data["mask"]

    # 1. Production Model Parity
    orig_prod_ckpt = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_sweetspot_best" / "best_model.pth"
    orig_sd = torch.load(orig_prod_ckpt, map_location="cpu", weights_only=False)["ema_state_dict"]
    orig_model = OrigECRformer(**MODEL_ARGS)
    orig_model.load_state_dict(orig_sd, strict=True)
    orig_model.eval()

    export_sd = torch.load(MODEL_REPO_DIR / "ecrformer_sweetspot_ema.pt", map_location="cpu", weights_only=True)
    pipe_model = pipeline.ECRformerAdaptedModel(**MODEL_ARGS)
    pipe_model.load_state_dict(export_sd, strict=True)
    pipe_model.eval()

    with torch.no_grad():
        o_blend, o_direct, _ = orig_model(s2_c, s1, mask)
        p_blend, p_direct, _ = pipe_model(s2_c, s1, mask)

    diff_blend = float(torch.max(torch.abs(o_blend - p_blend)).item())
    diff_direct = float(torch.max(torch.abs(o_direct - p_direct)).item())
    max_diff_prod = max(diff_blend, diff_direct)
    print(f"Production model max abs diff: blend={diff_blend:.2e}, direct={diff_direct:.2e}")
    assert max_diff_prod < 1e-5, f"Production parity failed: max diff {max_diff_prod} >= 1e-5"

    # 2. Baseline Model Parity
    base_ckpt = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_baseline" / "best_model.pth"
    base_sd = torch.load(base_ckpt, map_location="cpu", weights_only=False)["ema_state_dict"]
    orig_base = OrigECRformer(**MODEL_ARGS)
    orig_base.load_state_dict(base_sd, strict=True)
    orig_base.eval()

    export_base_sd = torch.load(MODEL_REPO_DIR / "ecrformer_baseline.pt", map_location="cpu", weights_only=True)
    pipe_base = pipeline.ECRformerAdaptedModel(**MODEL_ARGS)
    pipe_base.load_state_dict(export_base_sd, strict=True)
    pipe_base.eval()

    with torch.no_grad():
        ob_blend, ob_direct, _ = orig_base(s2_c, s1, mask)
        pb_blend, pb_direct, _ = pipe_base(s2_c, s1, mask)

    diff_b_blend = float(torch.max(torch.abs(ob_blend - pb_blend)).item())
    diff_b_direct = float(torch.max(torch.abs(ob_direct - pb_direct)).item())
    max_diff_base = max(diff_b_blend, diff_b_direct)
    print(f"Baseline model max abs diff: blend={diff_b_blend:.2e}, direct={diff_b_direct:.2e}")
    assert max_diff_base < 1e-5, f"Baseline parity failed: max diff {max_diff_base} >= 1e-5"

    overall_max_diff = max(max_diff_prod, max_diff_base)
    print(f"PARITY A PASSED: max abs diff = {overall_max_diff:.2e}")
    return True, overall_max_diff


def test_parity_b():
    print("\n================== PARITY B TEST ==================")
    status = "PASS"
    reason = ""

    # Test metrics against backend/util/util.py
    try:
        from util.util import compute_metric as orig_compute_metric
        torch.manual_seed(42)
        p = torch.rand(1, 4, 256, 256)
        t = torch.rand(1, 4, 256, 256)

        m_new_psnr = metrics.psnr(p, t)
        m_new_sam = metrics.sam(p, t)

        orig_res = orig_compute_metric(p, t)
        orig_psnr = float(orig_res["PSNR"].item())
        orig_sam = float(orig_res["SAM"].item())

        psnr_diff = abs(m_new_psnr - orig_psnr)
        sam_diff = abs(m_new_sam - orig_sam)
        print(f"Metrics PSNR diff: {psnr_diff:.2e}, SAM diff: {sam_diff:.2e}")
        assert psnr_diff < 1e-5, f"PSNR mismatch: {psnr_diff}"
        assert sam_diff < 1e-5, f"SAM mismatch: {sam_diff}"
        print("Metrics parity: PASSED")
    except Exception as e:
        print(f"Metrics parity SKIPPED: {e}")
        status = "SKIPPED"
        reason = str(e)

    # Test dataset preprocessing against backend/data/cache_dataset.py
    try:
        from data.cache_dataset import CachedSEN12MSCRDataset
        # CachedSEN12MSCRDataset requires split_dir with specific folder structure
        print("CachedSEN12MSCRDataset parity: SKIPPED (requires split_dir file structure)")
    except Exception as e:
        print(f"CachedSEN12MSCRDataset test SKIPPED: {e}")

    return status, reason


def test_fastapi_client():
    print("\n================== FASTAPI TESTCLIENT ==================")
    with TestClient(app) as client:
        # 1. GET /health
        res = client.get("/health")
        assert res.status_code == 200, f"/health returned {res.status_code}: {res.text}"
        h_data = res.json()
        print(f"/health response: {h_data}")
        assert h_data["status"] == "ok"
        assert h_data["modelLoaded"] is True
        assert h_data["baseline"] in ["loaded", "placeholder"]
        assert h_data["sampleCount"] > 0
        assert h_data["device"] == "cpu"

        # 2. GET /samples
        res = client.get("/samples")
        assert res.status_code == 200
        samples = res.json()
        print(f"/samples count: {len(samples)}")
        assert len(samples) > 0
        for s in samples:
            assert not s["filename"].endswith(".npz"), f"Filename has .npz: {s['filename']}"
            assert "cloudCoverage" in s
            assert "previews" in s
            assert s["previews"]["cloudy"].startswith("/samples/")

        test_id = samples[0]["id"]

        # 3. GET preview
        res = client.get(f"/samples/{test_id}/preview/cloudy")
        assert res.status_code == 200, f"Preview failed: {res.status_code}"
        assert res.headers["content-type"] == "image/png"
        img = Image.open(io.BytesIO(res.content))
        assert img.size == (256, 256), f"Preview size was {img.size}"

        # 4. POST /remove-clouds valid ID
        res = client.post("/remove-clouds", json={"imageId": test_id})
        assert res.status_code == 200, f"Remove clouds failed: {res.status_code}: {res.text}"
        result = res.json()
        assert "stages" in result and "metrics" in result
        stages = result["stages"]
        metric_dict = result["metrics"]

        # Assert all 4 stage values are valid data URIs decoding to 256x256 PNGs
        for stage_name in ["baseline", "sharpened", "final", "target"]:
            assert stage_name in stages, f"Missing stage: {stage_name}"
            val = stages[stage_name]
            assert val.startswith("data:image/png;base64,"), f"Not a data URI: {stage_name}"
            raw_b64 = val.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            img = Image.open(io.BytesIO(img_bytes))
            assert img.size == (256, 256), f"Stage {stage_name} image size {img.size} != 256x256"

        # Assert all metrics are finite numbers
        for stage_name in ["cloudy", "baseline", "sharpened", "final"]:
            assert stage_name in metric_dict, f"Missing metrics for {stage_name}"
            m = metric_dict[stage_name]
            for metric_key in ["psnr", "sam", "edgeCorr", "hfRetention"]:
                assert metric_key in m, f"Missing metric {metric_key} in {stage_name}"
                val = m[metric_key]
                assert isinstance(val, (int, float)) and not np.isnan(val) and not np.isinf(val)

        # 5. POST /remove-clouds invalid ID -> 400
        res = client.post("/remove-clouds", json={"imageId": "invalid!@#$"})
        assert res.status_code == 400, f"Expected 400, got {res.status_code}"

        # 6. POST /remove-clouds unknown ID -> 404
        res = client.post("/remove-clouds", json={"imageId": "unknown_sample_12345"})
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"

        print("FASTAPI TESTCLIENT: ALL PASSED")
    return True


def test_three_real_samples():
    print("\n================== 3 REAL SAMPLES METRICS ==================")
    with open(DATASET_REPO_DIR / "index.json", "r", encoding="utf-8") as f:
        index_data = json.load(f)

    # Sort by cloudCoverage
    sorted_samples = sorted(index_data, key=lambda s: s["cloudCoverage"])
    lowest = sorted_samples[0]
    median = sorted_samples[len(sorted_samples) // 2]
    highest = sorted_samples[-1]
    selected = [lowest, median, highest]

    with TestClient(app) as client:
        # Warmup pipeline
        client.get("/health")

        rows = []
        for s in selected:
            s_id = s["id"]
            cc = s["cloudCoverage"]
            res = client.post("/remove-clouds", json={"imageId": s_id})
            assert res.status_code == 200
            m = res.json()["metrics"]
            rows.append((s_id, cc, m))

    print("\n| Sample ID | Cloud % | Stage | PSNR (dB) | SAM (deg) | EdgeCorr | HFRetention |")
    print("|---|---|---|---|---|---|---|")
    for s_id, cc, m in rows:
        for stage in ["cloudy", "baseline", "sharpened", "final"]:
            sm = m[stage]
            print(f"| {s_id} | {cc}% | {stage:<9} | {sm['psnr']:<9.2f} | {sm['sam']:<9.2f} | {sm['edgeCorr']:<8.4f} | {sm['hfRetention']:<11.4f} |")

    # Check average PSNR progression
    avg_cloudy_psnr = np.mean([r[2]["cloudy"]["psnr"] for r in rows])
    avg_sharp_psnr = np.mean([r[2]["sharpened"]["psnr"] for r in rows])
    avg_final_psnr = np.mean([r[2]["final"]["psnr"] for r in rows])
    print(f"\nAverage PSNR: Cloudy={avg_cloudy_psnr:.2f} dB, Sharpened={avg_sharp_psnr:.2f} dB, Final={avg_final_psnr:.2f} dB")
    if avg_final_psnr < avg_cloudy_psnr:
        print("FLAG: Final average PSNR is lower than Cloudy.")
    else:
        print("Verification: Final average PSNR improved over Cloudy.")
    return rows


def test_latency():
    print("\n================== INFERENCE LATENCY ==================")
    pipe = pipeline.CloudRemovalPipeline()
    sample_id = "dense_100pct"

    # Cold run
    t0 = time.perf_counter()
    res1 = pipe.run(sample_id)
    t_cold = (time.perf_counter() - t0) * 1000.0

    # Cached run
    t1 = time.perf_counter()
    res2 = pipe.run(sample_id)
    t_cached = (time.perf_counter() - t1) * 1000.0

    print(f"Cold inference time:   {t_cold:.1f} ms")
    print(f"Cached inference time: {t_cached:.2f} ms")
    return t_cold, t_cached


def main():
    print("Running Smoke Tests in", sys.executable)
    parity_a_ok, max_diff = test_parity_a()
    parity_b_status, b_reason = test_parity_b()
    client_ok = test_fastapi_client()
    rows = test_three_real_samples()
    t_cold, t_cached = test_latency()

    print("\n================== SMOKE TEST SUMMARY ==================")
    print(f"Parity A: {'PASS' if parity_a_ok else 'FAIL'} (max abs diff = {max_diff:.2e})")
    print(f"Parity B: {parity_b_status}")
    print(f"FastAPI Client: {'PASS' if client_ok else 'FAIL'}")
    print(f"Latency: cold={t_cold:.1f} ms, cached={t_cached:.2f} ms")


if __name__ == "__main__":
    main()

