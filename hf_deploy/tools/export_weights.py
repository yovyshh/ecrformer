"""Export production and baseline model weights to clean tensors-only CPU state dicts."""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
import torch

# Ensure space/ is on sys.path to load ECRformerAdaptedModel from single source of truth
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPACE_DIR = REPO_ROOT / "hf_deploy" / "space"
MODEL_REPO_DIR = REPO_ROOT / "hf_deploy" / "model_repo"

sys.path.insert(0, str(SPACE_DIR))
from models.ecrformer_adapted import ECRformerAdaptedModel


MODEL_ARGS = {
    "features_start": 32,
    "num_blocks": [2, 2, 1, 1],
    "num_refine": 0,
    "bottle_neck": "tsa",
    "cbam": "1ca2+1sa2",
    "mask_blend": True,
    "head_init": "mean_prior",
}


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def export_checkpoint(src_ckpt: Path, key: str, dst_path: Path) -> bool:
    print(f"\n--- Exporting {src_ckpt.name} -> {dst_path.name} ---")
    if not src_ckpt.exists():
        print(f"ERROR: Checkpoint file not found: {src_ckpt}")
        return False

    raw = torch.load(src_ckpt, map_location="cpu", weights_only=False)
    if key in raw:
        sd = raw[key]
        print(f"Extracted key '{key}' with {len(sd)} parameters.")
    elif isinstance(raw, dict):
        sd = raw
        print(f"Using top-level state dict with {len(sd)} parameters.")
    else:
        print(f"ERROR: Unexpected checkpoint format: {type(raw)}")
        return False

    # Clean to pure float32 CPU tensors
    clean_sd = {k: v.cpu().float() for k, v in sd.items()}

    # Verify strict loading into model
    model = ECRformerAdaptedModel(**MODEL_ARGS)
    try:
        model.load_state_dict(clean_sd, strict=True)
        print("Verification: strict=True loading succeeded.")
    except Exception as e:
        print(f"ERROR: strict=True loading failed: {e}")
        return False

    # Save cleanly with zipfile serialization
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(clean_sd, dst_path, _use_new_zipfile_serialization=True)

    # Verify weights_only=True load
    test_sd = torch.load(dst_path, map_location="cpu", weights_only=True)
    assert len(test_sd) == len(clean_sd), "Mismatch in reloaded state dict keys"

    size_bytes = dst_path.stat().st_size
    sha = compute_sha256(dst_path)
    print(f"Success: {dst_path.name} ({size_bytes:,} bytes, {size_bytes / (1024*1024):.2f} MB)")
    print(f"SHA256: {sha}")
    return True


def main():
    MODEL_REPO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Export Production Model
    prod_ckpt = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_sweetspot_best" / "best_model.pth"
    prod_out = MODEL_REPO_DIR / "ecrformer_sweetspot_ema.pt"
    prod_ok = export_checkpoint(prod_ckpt, "ema_state_dict", prod_out)

    # 2. Export Baseline Model
    base_ckpt = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_baseline" / "best_model.pth"
    base_out = MODEL_REPO_DIR / "ecrformer_baseline.pt"
    base_ok = export_checkpoint(base_ckpt, "ema_state_dict", base_out)

    # 3. Copy model_metadata.json files if available
    prod_meta = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_sweetspot_best" / "model_metadata.json"
    if prod_meta.exists():
        shutil.copy2(prod_meta, MODEL_REPO_DIR / "production_model_metadata.json")

    base_meta = REPO_ROOT / "backend" / "checkpoints" / "ecrformer_baseline" / "model_metadata.json"
    if base_meta.exists():
        shutil.copy2(base_meta, MODEL_REPO_DIR / "baseline_model_metadata.json")

    # 4. Write config.json
    config = {
        "production": {
            "file": "ecrformer_sweetspot_ema.pt",
            "class_name": "ECRformerAdaptedModel",
            "constructor_args": MODEL_ARGS,
            "sha256": compute_sha256(prod_out) if prod_ok else None,
            "size_bytes": prod_out.stat().st_size if prod_ok else 0,
        },
        "baseline": {
            "file": "ecrformer_baseline.pt",
            "class_name": "ECRformerAdaptedModel",
            "constructor_args": MODEL_ARGS,
            "sha256": compute_sha256(base_out) if base_ok else None,
            "size_bytes": base_out.stat().st_size if base_ok else 0,
        } if base_ok else None,
        "input_spec": {
            "s2_cloudy": {
                "bands": ["B04", "B03", "B02", "B08"],
                "channels": 4,
                "shape": [1, 4, 256, 256],
                "dtype": "float32",
                "range": [0.0, 1.0],
                "description": "Optical Red, Green, Blue, NIR in [0, 1]",
            },
            "s1": {
                "bands": ["VV", "VH"],
                "channels": 2,
                "shape": [1, 2, 256, 256],
                "dtype": "float32",
                "normalization": "paper_exact",
                "ranges": {
                    "VV": "[-25.0, 0.0] dB -> [0, 1]",
                    "VH": "[-32.5, 0.0] dB -> [0, 1]",
                },
            },
            "mask": {
                "channels": 1,
                "shape": [1, 1, 256, 256],
                "dtype": "float32",
                "refinement": "9x9 avg pool > 0.5, 5x5 max pool dilation, 11x11 gaussian blur sigma 2.0, clamp [0, 1]",
            },
        },
    }

    config_path = MODEL_REPO_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"\nWritten {config_path.name}")


if __name__ == "__main__":
    main()

