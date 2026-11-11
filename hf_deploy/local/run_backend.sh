#!/usr/bin/env bash
set -e

DEVICE_ARG="${1:-${DEVICE:-auto}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HF_DEPLOY_DIR="$REPO_ROOT/hf_deploy"
SPACE_DIR="$HF_DEPLOY_DIR/space"
MODEL_DIR="$HF_DEPLOY_DIR/model_repo"
DATASET_DIR="$HF_DEPLOY_DIR/dataset_repo"

VENV_PATH="${VENV_DIR:-$HF_DEPLOY_DIR/.venv}"

# 1. Check venv
if [ -f "$VENV_PATH/bin/python" ]; then
  VENV_PY="$VENV_PATH/bin/python"
elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
  VENV_PY="$VENV_PATH/Scripts/python.exe"
else
  echo "[Error] Virtual environment not found at $VENV_PATH. Run setup.sh first."
  exit 1
fi

# 2. Check weights
if [ ! -f "$MODEL_DIR/ecrformer_sweetspot_ema.pt" ]; then
  echo "[Error] Model weights not found at $MODEL_DIR/ecrformer_sweetspot_ema.pt"
  exit 1
fi

# 3. Check samples
SAMPLE_COUNT=$(find "$DATASET_DIR/samples" -name "*.npz" 2>/dev/null | wc -l)
if [ "$SAMPLE_COUNT" -eq 0 ]; then
  echo "[Error] Dataset samples not found in $DATASET_DIR/samples. Run prepare_dataset.py first."
  exit 1
fi

export LOCAL_MODEL_DIR="$MODEL_DIR"
export LOCAL_DATASET_DIR="$DATASET_DIR"
export ALLOWED_ORIGINS="*"
export DEVICE="$DEVICE_ARG"

echo "=========================================================="
echo "Starting ECRformer Local Backend Server"
echo "Venv:        $VENV_PATH"
echo "Device:      $DEVICE"
echo "Models:      $LOCAL_MODEL_DIR"
echo "Dataset:     $LOCAL_DATASET_DIR"
echo "Server URL:  http://127.0.0.1:7860"
echo "Health:      http://127.0.0.1:7860/health"
echo "Reminder: Open http://127.0.0.1:7860/health to verify service status."
echo "=========================================================="

cd "$SPACE_DIR"
exec "$VENV_PY" -m uvicorn app:app --host 127.0.0.1 --port 7860

