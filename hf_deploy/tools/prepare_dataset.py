"""Prepare demo samples into Hugging Face dataset repo structure."""

import os
import sys
import re
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPACE_DIR = REPO_ROOT / "hf_deploy" / "space"
sys.path.insert(0, str(SPACE_DIR))

import preprocess
import render

ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def natural_sort_key(s: str):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def get_dir_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def prepare_dataset(src_dir: Path, out_dir: Path, limit: int = None, force: bool = False, exclude: str = "sparse_1pct"):
    print(f"Preparing dataset from {src_dir} -> {out_dir}")
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_dir}")

    samples_dir = out_dir / "samples"
    previews_dir = out_dir / "previews"
    index_file = out_dir / "index.json"

    if (samples_dir.exists() or index_file.exists()) and not force:
        raise FileExistsError(f"Destination {out_dir} already contains data. Use --force to overwrite.")

    if force:
        if samples_dir.exists():
            for f in samples_dir.glob("*.npz"):
                f.unlink()
        if previews_dir.exists():
            for f in previews_dir.glob("*.png"):
                f.unlink()

    samples_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)

    excluded_stems = {x.strip() for x in (exclude or "").split(",") if x.strip()}
    print(f"Excluded sample stems: {excluded_stems}")

    npz_files = sorted([f for f in src_dir.glob("*.npz")], key=lambda p: natural_sort_key(p.name))
    if limit is not None:
        npz_files = npz_files[:limit]

    print(f"Found {len(npz_files)} .npz files.")

    seen_ids = set()
    index_records = []
    skipped_files = []

    for fpath in npz_files:
        stem = fpath.stem
        if stem in excluded_stems:
            skipped_files.append((fpath.name, "Excluded via --exclude"))
            continue

        # Validate or sanitize ID
        if ID_RE.match(stem):
            sample_id = stem
        else:
            sample_id = re.sub(r"[^A-Za-z0-9_-]", "_", stem)
            print(f"Sanitized ID: '{stem}' -> '{sample_id}'")

        if sample_id in seen_ids:
            skipped_files.append((fpath.name, f"Duplicate sample ID: {sample_id}"))
            continue

        # Validate with preprocess module
        try:
            sample_tensors = preprocess.load_sample_npz(fpath)
        except Exception as e:
            skipped_files.append((fpath.name, f"Preprocess validation failed: {e}"))
            continue

        # Load raw data untouched for copying
        raw_data = np.load(fpath)
        raw_dict = {k: raw_data[k] for k in raw_data.files}

        # Calculate integer cloudCoverage percentage
        cf = float(sample_tensors["cf"])
        if cf <= 1.0:
            cloud_cov = int(round(cf * 100.0))
        else:
            cloud_cov = int(round(cf))
        cloud_cov = max(0, min(100, cloud_cov))

        # 1. Save untouched raw sample to samples/{id}.npz
        dst_sample_path = samples_dir / f"{sample_id}.npz"
        np.savez_compressed(dst_sample_path, **raw_dict)

        # 2. Render previews
        cloudy_preview_path = previews_dir / f"{sample_id}_cloudy.png"
        sar_preview_path = previews_dir / f"{sample_id}_sar.png"
        mask_preview_path = previews_dir / f"{sample_id}_mask.png"

        # Cloudy RGB
        cloudy_rgb = render.to_rgb_image(sample_tensors["s2_cloudy"])
        Image.fromarray(cloudy_rgb).save(cloudy_preview_path)

        # SAR Preview (paper_exact VV)
        sar_bytes = render.sar_preview(sample_tensors["s1"])
        sar_preview_path.write_bytes(sar_bytes)

        # Refined Mask Preview
        mask_bytes = render.mask_preview(sample_tensors["mask"])
        mask_preview_path.write_bytes(mask_bytes)

        seen_ids.add(sample_id)
        index_records.append({
            "id": sample_id,
            "filename": stem,
            "cloudCoverage": cloud_cov,
            "previews": {
                "cloudy": f"previews/{sample_id}_cloudy.png",
                "sar": f"previews/{sample_id}_sar.png",
                "mask": f"previews/{sample_id}_mask.png",
            },
        })

    # Write index.json
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_records, f, indent=2)

    # Write dataset README.md
    readme_path = out_dir / "README.md"
    readme_content = """---
license: apache-2.0
task_categories:
- image-to-image
tags:
- remote-sensing
- earth-observation
- cloud-removal
- sentinel-1
- sentinel-2
pretty_name: ECRformer Demo Dataset
size_categories:
- n<1K
---

# ECRformer Cloud Removal Demo Dataset

This dataset contains co-registered multimodal Sentinel-1 SAR and Sentinel-2 optical image pairs for evaluating the ECRformer cloud-removal pipeline.

## Structure
- `index.json`: Scene metadata and relative preview paths.
- `samples/<id>.npz`: Compressed raw tensors containing `s2_cloudy`, `s1`, `mask`, `s2_clear`, `cf`.
- `previews/<id>_<kind>.png`: Pre-rendered 256x256 preview thumbnails.
"""
    readme_path.write_text(readme_content, encoding="utf-8")

    total_bytes = get_dir_size(out_dir)
    print("\n=== Dataset Preparation Summary ===")
    print(f"Total processed samples: {len(index_records)}")
    print(f"Skipped files: {len(skipped_files)}")
    for name, reason in skipped_files:
        print(f"  - {name}: {reason}")
    print(f"Total dataset_repo size: {total_bytes:,} bytes ({total_bytes / (1024 * 1024):.2f} MB)")
    if index_records:
        print("\nFirst 5 entries in index.json:")
        for r in index_records[:5]:
            print(f"  id='{r['id']}', filename='{r['filename']}', cloudCoverage={r['cloudCoverage']}%")


def main():
    parser = argparse.ArgumentParser(description="Prepare dataset repo for ECRformer Space")
    parser.add_argument("--src", type=Path, default=REPO_ROOT / "demo_samples", help="Source folder of .npz files")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "hf_deploy" / "dataset_repo", help="Output dataset repo folder")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of samples processed")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output directory")
    parser.add_argument("--exclude", type=str, default="sparse_1pct", help="Comma-separated sample stems to exclude")
    args = parser.parse_args()

    prepare_dataset(args.src, args.out, limit=args.limit, force=args.force, exclude=args.exclude)


if __name__ == "__main__":
    main()

