---
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
