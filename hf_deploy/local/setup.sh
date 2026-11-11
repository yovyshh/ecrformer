#!/usr/bin/env bash
set -e

FORCE_CPU=0
FORCE_GPU=0
TORCH_INDEX_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cpu)
      FORCE_CPU=1
      shift
      ;;
    --gpu|-g)
      FORCE_GPU=1
      shift
      ;;
    --torch-index-url)
      TORCH_INDEX_URL="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VENV_PATH="${VENV_DIR:-$REPO_ROOT/hf_deploy/.venv}"
echo "Target venv: $VENV_PATH"

# G1: Python selection (python3.12, python3.11, then python3/python if 3.11 or 3.12)
SELECTED_PY=""
SELECTED_VER=""

check_python() {
  local cmd="$1"
  if command -v "$cmd" &>/dev/null; then
    local ver
    ver="$("$cmd" -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>/dev/null || true)"
    if [ -n "$ver" ]; then
      echo "$ver"
    fi
  fi
}

for cand in python3.12 python3.11; do
  ver="$(check_python "$cand")"
  if [ -n "$ver" ]; then
    SELECTED_PY="$cand"
    SELECTED_VER="$ver"
    break
  fi
done

if [ -z "$SELECTED_PY" ]; then
  for cand in python3 python; do
    ver="$(check_python "$cand")"
    if [ "$ver" = "3.11" ] || [ "$ver" = "3.12" ]; then
      SELECTED_PY="$cand"
      SELECTED_VER="$ver"
      break
    elif [ -n "$ver" ]; then
      major="$(echo "$ver" | cut -d. -f1)"
      minor="$(echo "$ver" | cut -d. -f2)"
      if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 13 ]); then
        echo "Error: Python $ver detected. Python 3.13+ is not supported. Please install Python 3.12 (e.g. winget install Python.Python.3.12, brew install python@3.12, or apt install python3.12)." >&2
        exit 1
      fi
    fi
  done
fi

if [ -z "$SELECTED_PY" ]; then
  echo "Error: No compatible Python 3.11 or 3.12 found. Python 3.13+ is not supported. Please install Python 3.12." >&2
  exit 1
fi

echo "Selected Python: $SELECTED_PY (version $SELECTED_VER)"

# Check existing venv version and recreate if needed
if [ -d "$VENV_PATH" ]; then
  EXISTING_PY=""
  if [ -f "$VENV_PATH/bin/python" ]; then
    EXISTING_PY="$VENV_PATH/bin/python"
  elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
    EXISTING_PY="$VENV_PATH/Scripts/python.exe"
  fi
  EXISTING_VER=""
  if [ -n "$EXISTING_PY" ]; then
    EXISTING_VER="$("$EXISTING_PY" -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>/dev/null || true)"
  fi
  if [ "$EXISTING_VER" != "$SELECTED_VER" ]; then
    echo "Existing venv was built with Python '$EXISTING_VER' (selected is '$SELECTED_VER'). Deleting and recreating..."
    rm -rf "$VENV_PATH"
  else
    echo "Virtual environment already exists at $VENV_PATH with Python $EXISTING_VER."
  fi
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment at $VENV_PATH..."
  "$SELECTED_PY" -m venv "$VENV_PATH"
fi

if [ -f "$VENV_PATH/bin/python" ]; then
  VENV_PY="$VENV_PATH/bin/python"
elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
  VENV_PY="$VENV_PATH/Scripts/python.exe"
else
  echo "Error: Python binary not found in $VENV_PATH"
  exit 1
fi

echo "Upgrading pip..."
"$VENV_PY" -m pip install --upgrade pip

# G2: GPU setup logic
OS_TYPE="$(uname -s)"
INSTALL_GPU=0
DRIVER_CUDA_VER="0.0"

if [ "$FORCE_CPU" -eq 1 ]; then
  echo "Force CPU requested (--cpu)."
  INSTALL_GPU=0
elif [ "$FORCE_GPU" -eq 1 ]; then
  echo "Force GPU requested (--gpu)."
  INSTALL_GPU=1
elif [ "$OS_TYPE" = "Darwin" ]; then
  echo "macOS detected. Defaulting to CPU."
  INSTALL_GPU=0
elif command -v nvidia-smi &>/dev/null; then
  SMI_OUT="$(nvidia-smi 2>/dev/null || true)"
  CUDA_VER_MATCH="$(echo "$SMI_OUT" | grep -oE "CUDA Version: [0-9]+\.[0-9]+" | head -n1 | awk '{print $3}' || true)"
  if [ -n "$CUDA_VER_MATCH" ]; then
    DRIVER_CUDA_VER="$CUDA_VER_MATCH"
    echo "Detected NVIDIA GPU with Driver CUDA Version: $DRIVER_CUDA_VER"
    INSTALL_GPU=1
  else
    echo "nvidia-smi found but could not parse CUDA version. Defaulting to CPU."
    INSTALL_GPU=0
  fi
else
  echo "nvidia-smi not found. Defaulting to CPU build."
  INSTALL_GPU=0
fi

TORCH_INSTALLED=0

if [ "$INSTALL_GPU" -eq 1 ]; then
  if [ -n "$TORCH_INDEX_URL" ]; then
    CANDIDATES=("$TORCH_INDEX_URL")
  else
    # Descending PyTorch CUDA wheels
    CANDIDATES=()
    # Check driver cuda version vs candidate version
    # using awk for float comparison
    for item in "12.6 https://download.pytorch.org/whl/cu126" \
                "12.4 https://download.pytorch.org/whl/cu124" \
                "12.1 https://download.pytorch.org/whl/cu121" \
                "11.8 https://download.pytorch.org/whl/cu118"; do
      cver="$(echo "$item" | awk '{print $1}')"
      curl_val="$(echo "$item" | awk '{print $2}')"
      if [ "$DRIVER_CUDA_VER" = "0.0" ] || awk "BEGIN {exit !($cver <= $DRIVER_CUDA_VER)}"; then
        CANDIDATES+=("$curl_val")
      fi
    done
  fi

  for idx_url in "${CANDIDATES[@]}"; do
    echo "Attempting PyTorch installation with index: $idx_url..."
    if "$VENV_PY" -m pip install torch torchvision --index-url "$idx_url"; then
      TORCH_INSTALLED=1
      echo "PyTorch successfully installed from $idx_url"
      break
    else
      echo "Warning: Installation failed using $idx_url. Trying next candidate..."
    fi
  done

  if [ "$TORCH_INSTALLED" -eq 0 ]; then
    echo ""
    echo "[WARNING] Failed to install CUDA PyTorch with candidate wheel indexes! Falling back to CPU build."
    echo "Pick the right CUDA build command from https://pytorch.org and specify --torch-index-url if needed."
    echo ""
  fi
fi

if [ "$TORCH_INSTALLED" -eq 0 ]; then
  if [ "$OS_TYPE" = "Darwin" ]; then
    echo "Installing CPU PyTorch from default PyPI (macOS)..."
    "$VENV_PY" -m pip install torch torchvision
  else
    echo "Installing CPU PyTorch from https://download.pytorch.org/whl/cpu..."
    "$VENV_PY" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  fi
fi

echo "Installing dependencies from $SCRIPT_DIR/requirements.txt..."
"$VENV_PY" -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== PyTorch Verification ==="
"$VENV_PY" -c "
import torch
print('Torch version:      ', torch.__version__)
print('Torch CUDA version: ', torch.version.cuda)
print('CUDA available:     ', torch.cuda.is_available())
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'
print('GPU Name:           ', gpu_name)
if torch.cuda.is_available():
    x = torch.randn(10, 10, device='cuda')
    y = torch.matmul(x, x)
    print('CUDA matmul test:    SUCCESS (norm={:.4f})'.format(y.norm().item()))
else:
    print('CUDA matmul test:    SKIPPED (CPU mode)')
"
