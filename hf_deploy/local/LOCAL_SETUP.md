# Local Setup Guide: ECRformer Cloud Removal

This guide provides exact copy-paste steps to run the ECRformer local backend and frontend on Windows, macOS, or Linux. The application runs locally without Docker, Hugging Face hosting, or cloud dependencies.

---

## Prerequisites

1. **Python 3.12 or 3.11** (64-bit)
   - On Windows: `winget install Python.Python.3.12`
   - On macOS: `brew install python@3.12`
   - On Linux: `sudo apt install python3.12 python3.12-venv`
   - Verify: `py -3.12 --version` or `python --version`
2. **Node.js 20+ & npm**
   - Verify: `node -v` and `npm -v`
3. **Git**
   - Verify: `git --version`
4. **NVIDIA GPU (Optional, for CUDA acceleration)**
   - Verify: `nvidia-smi`
   - Ensure up-to-date NVIDIA drivers are installed if running GPU inference.

---

## 1. Backend Setup & Run

The backend is a FastAPI server located under `hf_deploy/space` that serves the ECRformer models and sample datasets locally.

### Windows (PowerShell)

#### Step 1: Install Dependencies & Setup Venv
Open PowerShell and navigate to the repository root:
```powershell
# Auto-detects GPU via nvidia-smi and installs CUDA PyTorch if available (default):
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\setup.ps1

# Force CPU inference (even if an NVIDIA GPU is present):
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\setup.ps1 -Cpu
```
*Note: If your CUDA version requires a custom wheel index, pass `-TorchIndexUrl`, e.g.:*
```powershell
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\setup.ps1 -Gpu -TorchIndexUrl "https://download.pytorch.org/whl/cu124"
```

#### Step 2: Run Backend
```powershell
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\run_backend.ps1
```
To explicitly select device or adjust LRU result cache:
```powershell
# Auto detect (default):
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\run_backend.ps1 -Device auto

# Force CPU:
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\run_backend.ps1 -Device cpu

# Force CUDA:
powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\run_backend.ps1 -Device cuda
```
*Environment variable `RESULT_CACHE_SIZE` controls the LRU result cache (default `64`). Set `RESULT_CACHE_SIZE=0` to disable caching.*

---

### macOS / Linux (Bash)

#### Step 1: Install Dependencies & Setup Venv
Open a terminal and navigate to the repository root:
```bash
# Auto-detects GPU (Linux) or defaults to CPU (macOS):
bash hf_deploy/local/setup.sh

# Force CPU inference:
bash hf_deploy/local/setup.sh --cpu
```
*(macOS with Apple Silicon uses PyPI CPU/MPS builds by default.)*

#### Step 2: Run Backend
```bash
bash hf_deploy/local/run_backend.sh
```
To explicitly select device:
```bash
DEVICE=cpu bash hf_deploy/local/run_backend.sh
# or
DEVICE=cuda bash hf_deploy/local/run_backend.sh
```

---

## 2. Verify Backend Health

Once running, verify the backend status:

```bash
curl http://127.0.0.1:7860/health
```

Expected response format (CUDA mode):
```json
{
  "status": "ok",
  "modelLoaded": true,
  "baseline": "loaded",
  "sampleCount": 44,
  "device": "cuda:0 (NVIDIA GeForce RTX 3050 Laptop GPU)",
  "torchVersion": "2.14.1+cu126",
  "cudaVersion": "12.6"
}
```
*(On CPU mode, `"device"` reports `"cpu"` and `"cudaVersion"` reports `null`.)*

---

## 3. Frontend Setup & Run

The Next.js frontend connects to the local FastAPI backend.

```bash
# 1. Navigate to the frontend directory
cd frontend-v2

# 2. Install dependencies
npm install

# 3. Configure environment variables
# Copy template or create .env.local:
# (If .env.example exists, copy it: cp .env.example .env.local)
echo "BACKEND_URL=http://127.0.0.1:7860" > .env.local
echo "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:7860" >> .env.local

# 4. Start Next.js development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Adding New Samples

To prepare and add new evaluation samples:
1. Place `.npz` files into the `demo_samples/` folder at the repository root.
2. Run the dataset preparation script using the virtual environment:
   - **Windows**:
     ```powershell
     .\hf_deploy\.venv\Scripts\python.exe hf_deploy\tools\prepare_dataset.py --force
     ```
   - **macOS/Linux**:
     ```bash
     hf_deploy/.venv/bin/python hf_deploy/tools/prepare_dataset.py --force
     ```
3. The script extracts metadata, creates pre-rendered PNG previews in `hf_deploy/dataset_repo/previews/`, and rebuilds `hf_deploy/dataset_repo/index.json`.

---

## 5. Troubleshooting

- **Port 7860 in use**:
  Another instance of uvicorn or another service is listening on port 7860.
  - Windows: Run `netstat -ano | findstr :7860` to find the PID, then `Stop-Process -Id <PID> -Force` or kill in Task Manager.
  - macOS/Linux: Run `lsof -i :7860` and `kill -9 <PID>`.

- **Execution Policy Error (`PSSecurityException`)**:
  If Windows blocks running PowerShell scripts (`running scripts is disabled on this system`), use the bypass flag:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\hf_deploy\local\run_backend.ps1
  ```
  Or change your local user policy once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

- **`"device": "cpu"` on a GPU Machine**:
  - Check that an NVIDIA GPU is detected: run `nvidia-smi`.
  - Check whether CUDA-enabled PyTorch is installed in the venv:
    ```powershell
    .\hf_deploy\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
    ```
  - If `False`, re-run `setup.ps1 -Gpu` (or `setup.sh --gpu`). Check `https://pytorch.org` for the exact CUDA version wheel command compatible with your installed CUDA driver.

- **Backend Unreachable from Frontend**:
  - Verify that the backend is running and listening: `curl http://127.0.0.1:7860/health`.
  - Ensure `.env.local` in `frontend-v2/` defines `BACKEND_URL=http://127.0.0.1:7860`.
  - Restart the Next.js dev server after editing `.env.local`.

- **First Request Slow**:
  The first request on a sample performs dynamic initialization and JIT memory allocation. Subsequent requests on cached samples take under 10 ms.

