"""Single inference pipeline for ECRformer cloud removal on HF Space."""

import os
import re
import json
import time
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Dict, Any, List

import torch

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None

from models.ecrformer_adapted import ECRformerAdaptedModel
from preprocess import load_sample_npz
from metrics import compute_all, zero_metrics
from render import to_rgb_image, png_bytes, data_uri, sar_preview, mask_preview, blank_image


ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

DEFAULT_PROD_ARGS = {
    "features_start": 32,
    "num_blocks": [2, 2, 1, 1],
    "num_refine": 0,
    "bottle_neck": "tsa",
    "cbam": "1ca2+1sa2",
    "mask_blend": True,
    "head_init": "mean_prior",
}


class CloudRemovalPipeline:
    """Manages models, dataset indexing, and end-to-end inference."""

    def __init__(self):
        self.production_model: Optional[ECRformerAdaptedModel] = None
        self.baseline_model: Optional[ECRformerAdaptedModel] = None
        self.baseline_status: str = "placeholder"
        self.model_loaded: bool = False

        # Device configuration: auto (default) | cpu | cuda
        device_env = os.environ.get("DEVICE", "auto").strip().lower()
        if device_env == "cuda":
            if torch.cuda.is_available():
                dev_idx = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(dev_idx)
                self.torch_device = torch.device(f"cuda:{dev_idx}")
                self.device = f"cuda:{dev_idx} ({gpu_name})"
            else:
                import logging
                logging.warning("[Pipeline] CUDA requested via DEVICE env, but torch.cuda.is_available() is False. Falling back to CPU.")
                print("[Pipeline] WARNING: CUDA requested but unavailable. Falling back to CPU.")
                self.torch_device = torch.device("cpu")
                self.device = "cpu"
        elif device_env == "auto":
            if torch.cuda.is_available():
                dev_idx = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(dev_idx)
                self.torch_device = torch.device(f"cuda:{dev_idx}")
                self.device = f"cuda:{dev_idx} ({gpu_name})"
            else:
                self.torch_device = torch.device("cpu")
                self.device = "cpu"
        else:
            self.torch_device = torch.device("cpu")
            self.device = "cpu"

        self.hf_model_repo = os.environ.get("HF_MODEL_REPO", "")
        self.hf_dataset_repo = os.environ.get("HF_DATASET_REPO", "")
        self.hf_token = os.environ.get("HF_TOKEN") or None
        self.local_model_dir = os.environ.get("LOCAL_MODEL_DIR", "")
        self.local_dataset_dir = os.environ.get("LOCAL_DATASET_DIR", "")

        self.index_ttl = int(os.environ.get("INDEX_TTL", "60"))
        self._index_cache: Optional[List[Dict[str, Any]]] = None
        self._index_time: float = 0.0

        self.result_cache_size = int(os.environ.get("RESULT_CACHE_SIZE", "64"))
        self.result_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.cache_lock = threading.Lock()
        self.forward_lock = threading.Lock()

        # Thread configuration (applies on CPU)
        if self.torch_device.type == "cpu" and "TORCH_THREADS" in os.environ:
            torch_threads = int(os.environ["TORCH_THREADS"])
            torch.set_num_threads(torch_threads)

        self._load_models()
        self._warmup()

    def _warmup(self):
        """Perform one dummy forward pass of each loaded model on the active device."""
        if not self.model_loaded or self.production_model is None:
            return
        mem_fmt = torch.channels_last if self.torch_device.type == "cpu" else torch.preserve_format
        dummy_s2 = torch.zeros((1, 4, 256, 256), dtype=torch.float32, device=self.torch_device).to(memory_format=mem_fmt)
        dummy_s1 = torch.zeros((1, 2, 256, 256), dtype=torch.float32, device=self.torch_device).to(memory_format=mem_fmt)
        dummy_mask = torch.zeros((1, 1, 256, 256), dtype=torch.float32, device=self.torch_device).to(memory_format=mem_fmt)

        with torch.inference_mode():
            if self.torch_device.type == "cuda":
                torch.cuda.synchronize(self.torch_device)
            t0 = time.perf_counter()
            _ = self.production_model(dummy_s2, dummy_s1, dummy_mask)
            if self.torch_device.type == "cuda":
                torch.cuda.synchronize(self.torch_device)
            prod_ms = (time.perf_counter() - t0) * 1000
            print(f"[Pipeline] Production model warm-up: {prod_ms:.2f} ms")

            if self.baseline_model is not None:
                if self.torch_device.type == "cuda":
                    torch.cuda.synchronize(self.torch_device)
                t0 = time.perf_counter()
                _ = self.baseline_model(dummy_s2, dummy_s1, dummy_mask)
                if self.torch_device.type == "cuda":
                    torch.cuda.synchronize(self.torch_device)
                base_ms = (time.perf_counter() - t0) * 1000
                print(f"[Pipeline] Baseline model warm-up: {base_ms:.2f} ms")

    def _resolve_model_path(self, filename: str) -> Optional[str]:
        if self.local_model_dir:
            p = os.path.join(self.local_model_dir, filename)
            if os.path.exists(p):
                return p
        if self.hf_model_repo and hf_hub_download:
            try:
                return hf_hub_download(
                    repo_id=self.hf_model_repo,
                    filename=filename,
                    token=self.hf_token,
                )
            except Exception as e:
                print(f"[Pipeline] HF download failed for {filename}: {e}")
        return None

    def _load_models(self):
        # 1. Load config if present
        config_path = self._resolve_model_path("config.json")
        config = {}
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"[Pipeline] Failed to parse config.json: {e}")

        prod_cfg = config.get("production", {})
        prod_file = prod_cfg.get("file", "ecrformer_sweetspot_ema.pt")
        prod_args = prod_cfg.get("constructor_args", DEFAULT_PROD_ARGS)

        base_cfg = config.get("baseline", {})
        base_file = base_cfg.get("file", "ecrformer_baseline.pt") if base_cfg else "ecrformer_baseline.pt"
        base_args = base_cfg.get("constructor_args", DEFAULT_PROD_ARGS) if base_cfg else DEFAULT_PROD_ARGS

        # 2. Load production model
        prod_path = self._resolve_model_path(prod_file)
        if prod_path and os.path.exists(prod_path):
            try:
                model = ECRformerAdaptedModel(**prod_args)
                state_dict = torch.load(prod_path, map_location="cpu", weights_only=True)
                if "ema_state_dict" in state_dict:
                    state_dict = state_dict["ema_state_dict"]
                elif "model_state_dict" in state_dict:
                    state_dict = state_dict["model_state_dict"]
                model.load_state_dict(state_dict, strict=True)
                model.to(self.torch_device)
                if self.torch_device.type == "cpu":
                    model.to(memory_format=torch.channels_last)
                model.eval()
                self.production_model = model
                self.model_loaded = True
                print(f"[Pipeline] Production model loaded successfully on {self.device}.")
            except Exception as e:
                print(f"[Pipeline] Error loading production model: {e}")
                self.production_model = None
                self.model_loaded = False

        # 3. Load baseline model (safe fallback to placeholder)
        base_path = self._resolve_model_path(base_file)
        if base_path and os.path.exists(base_path):
            try:
                model = ECRformerAdaptedModel(**base_args)
                state_dict = torch.load(base_path, map_location="cpu", weights_only=True)
                if "ema_state_dict" in state_dict:
                    state_dict = state_dict["ema_state_dict"]
                elif "model_state_dict" in state_dict:
                    state_dict = state_dict["model_state_dict"]
                model.load_state_dict(state_dict, strict=True)
                model.to(self.torch_device)
                if self.torch_device.type == "cpu":
                    model.to(memory_format=torch.channels_last)
                model.eval()
                self.baseline_model = model
                self.baseline_status = "loaded"
                print(f"[Pipeline] Baseline model loaded successfully on {self.device}.")
            except Exception as e:
                print(f"[Pipeline] Baseline failed to load ({e}). Using placeholder fallback.")
                self.baseline_model = None
                self.baseline_status = "placeholder"
        else:
            self.baseline_model = None
            self.baseline_status = "placeholder"

    def get_index(self) -> List[Dict[str, Any]]:
        """Fetch index.json with TTL caching."""
        now = time.time()
        if self._index_cache is not None and (now - self._index_time < self.index_ttl):
            return self._index_cache

        index_data = []
        if self.local_dataset_dir:
            idx_path = os.path.join(self.local_dataset_dir, "index.json")
            if os.path.exists(idx_path):
                try:
                    with open(idx_path, "r", encoding="utf-8") as f:
                        index_data = json.load(f)
                except Exception as e:
                    print(f"[Pipeline] Error reading local index.json: {e}")
        elif self.hf_dataset_repo and hf_hub_download:
            try:
                p = hf_hub_download(
                    repo_id=self.hf_dataset_repo,
                    filename="index.json",
                    repo_type="dataset",
                    token=self.hf_token,
                )
                with open(p, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception as e:
                print(f"[Pipeline] Error downloading HF index.json: {e}")

        self._index_cache = index_data
        self._index_time = now
        return index_data

    def get_sample_path(self, sample_id: str) -> str:
        """Resolve path to samples/{sample_id}.npz."""
        filename = f"samples/{sample_id}.npz"
        if self.local_dataset_dir:
            p = os.path.join(self.local_dataset_dir, filename)
            if os.path.exists(p):
                return p
        if self.hf_dataset_repo and hf_hub_download:
            return hf_hub_download(
                repo_id=self.hf_dataset_repo,
                filename=filename,
                repo_type="dataset",
                token=self.hf_token,
            )
        raise FileNotFoundError(f"Sample file {filename} could not be resolved.")

    def get_preview_bytes(self, sample_id: str, kind: str) -> bytes:
        """Retrieve preview PNG bytes from disk, HF Hub, or render dynamically."""
        if not ID_PATTERN.match(sample_id):
            raise ValueError(f"Invalid sample ID: {sample_id}")
        if kind not in ["cloudy", "sar", "mask"]:
            raise ValueError(f"Invalid preview kind: {kind}")

        rel_path = f"previews/{sample_id}_{kind}.png"
        if self.local_dataset_dir:
            p = os.path.join(self.local_dataset_dir, rel_path)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    return f.read()

        if self.hf_dataset_repo and hf_hub_download:
            try:
                p = hf_hub_download(
                    repo_id=self.hf_dataset_repo,
                    filename=rel_path,
                    repo_type="dataset",
                    token=self.hf_token,
                )
                with open(p, "rb") as f:
                    return f.read()
            except Exception:
                pass

        # Dynamic fallback from sample data
        sample_path = self.get_sample_path(sample_id)
        data = load_sample_npz(sample_path)
        if kind == "cloudy":
            return png_bytes(to_rgb_image(data["s2_cloudy"]))
        elif kind == "sar":
            return sar_preview(data["s1"])
        elif kind == "mask":
            return mask_preview(data["mask"])
        raise ValueError(f"Unable to generate preview for {kind}")

    def build_result(self, sample_id: str, sample_data: dict) -> tuple[dict, dict]:
        """Run model inference and construct the Result dictionary, returning (result, timings)."""
        s2_cloudy = sample_data["s2_cloudy"]
        s1 = sample_data["s1"]
        mask = sample_data["mask"]
        target = sample_data["target"]

        mem_fmt = torch.channels_last if self.torch_device.type == "cpu" else torch.preserve_format
        with self.forward_lock:
            with torch.inference_mode():
                s2_cloudy_dev = s2_cloudy.to(self.torch_device, memory_format=mem_fmt)
                s1_dev = s1.to(self.torch_device, memory_format=mem_fmt)
                mask_dev = mask.to(self.torch_device, memory_format=mem_fmt)

                if self.torch_device.type == "cuda":
                    torch.cuda.synchronize(self.torch_device)
                t_prod = time.perf_counter()
                p_blend, p_direct, _ = self.production_model(s2_cloudy_dev, s1_dev, mask_dev)
                if self.torch_device.type == "cuda":
                    torch.cuda.synchronize(self.torch_device)
                prod_ms = (time.perf_counter() - t_prod) * 1000

                p_blend = p_blend.to("cpu")
                p_direct = p_direct.to("cpu")

                if self.baseline_model is not None:
                    if self.torch_device.type == "cuda":
                        torch.cuda.synchronize(self.torch_device)
                    t_base = time.perf_counter()
                    _, b_direct, _ = self.baseline_model(s2_cloudy_dev, s1_dev, mask_dev)
                    if self.torch_device.type == "cuda":
                        torch.cuda.synchronize(self.torch_device)
                    base_ms = (time.perf_counter() - t_base) * 1000
                    b_direct = b_direct.to("cpu")
                else:
                    base_ms = 0.0
                    b_direct = None

        t_render = time.perf_counter()
        stages = {
            "baseline": data_uri(png_bytes(to_rgb_image(b_direct))) if b_direct is not None else data_uri(blank_image()),
            "sharpened": data_uri(png_bytes(to_rgb_image(p_direct))),
            "final": data_uri(png_bytes(to_rgb_image(p_blend))),
            "target": data_uri(png_bytes(to_rgb_image(target))),
        }
        render_ms = (time.perf_counter() - t_render) * 1000

        t_metrics = time.perf_counter()
        metrics = {
            "cloudy": compute_all(s2_cloudy, target, mask),
            "baseline": compute_all(b_direct, target, mask) if b_direct is not None else zero_metrics(),
            "sharpened": compute_all(p_direct, target, mask),
            "final": compute_all(p_blend, target, mask),
        }
        metrics_ms = (time.perf_counter() - t_metrics) * 1000

        timings = {
            "prod_ms": prod_ms,
            "base_ms": base_ms,
            "render_ms": render_ms,
            "metrics_ms": metrics_ms,
        }
        return {"stages": stages, "metrics": metrics}, timings

    def run(self, sample_id: str, return_timing: bool = False):
        """Execute full inference pipeline for a sample with LRU caching."""
        if not self.model_loaded or self.production_model is None:
            raise RuntimeError("Production model is not loaded.")

        if not ID_PATTERN.match(sample_id):
            raise ValueError(f"Invalid sample ID format: '{sample_id}'")

        t_start = time.perf_counter()

        # Validate index membership if index exists
        index = self.get_index()
        if index and not any(s.get("id") == sample_id for s in index):
            raise KeyError(f"Sample ID '{sample_id}' not found in dataset index.")

        if self.result_cache_size > 0:
            with self.cache_lock:
                if sample_id in self.result_cache:
                    self.result_cache.move_to_end(sample_id)
                    total_ms = (time.perf_counter() - t_start) * 1000
                    print(f"[Pipeline] Request timing ({sample_id}) [CACHED]: total={total_ms:.1f}ms")
                    if return_timing:
                        return self.result_cache[sample_id], total_ms
                    return self.result_cache[sample_id]

        try:
            sample_path = self.get_sample_path(sample_id)
        except Exception:
            raise KeyError(f"Sample file for '{sample_id}' could not be located.")

        t_load = time.perf_counter()
        sample_data = load_sample_npz(sample_path)
        load_ms = (time.perf_counter() - t_load) * 1000

        result, timings = self.build_result(sample_id, sample_data)

        if self.torch_device.type == "cuda":
            torch.cuda.synchronize(self.torch_device)
        total_ms = (time.perf_counter() - t_start) * 1000

        print(
            f"[Pipeline] Request timing ({sample_id}): "
            f"load={load_ms:.1f}ms prod={timings['prod_ms']:.1f}ms base={timings['base_ms']:.1f}ms "
            f"render={timings['render_ms']:.1f}ms metrics={timings['metrics_ms']:.1f}ms total={total_ms:.1f}ms"
        )

        if self.result_cache_size > 0:
            with self.cache_lock:
                self.result_cache[sample_id] = result
                while len(self.result_cache) > self.result_cache_size:
                    self.result_cache.popitem(last=False)

        if return_timing:
            return result, total_ms
        return result

