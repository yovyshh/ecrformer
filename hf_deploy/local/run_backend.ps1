[CmdletBinding()]
param(
    [string]$Device = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$HfDeployDir = Join-Path $RepoRoot "hf_deploy"
$SpaceDir = Join-Path $HfDeployDir "space"
$ModelDir = Join-Path $HfDeployDir "model_repo"
$DatasetDir = Join-Path $HfDeployDir "dataset_repo"

if ($env:VENV_DIR) {
    $VenvPath = $env:VENV_DIR
} else {
    $VenvPath = Join-Path $HfDeployDir ".venv"
}

# 1. Check venv
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = Join-Path $VenvPath "bin\python"
}
if (-not (Test-Path $PythonExe)) {
    Write-Error "[Error] Virtual environment not found at $VenvPath. Run setup.ps1 first."
    exit 1
}

# 2. Check weights
$WeightFile = Join-Path $ModelDir "ecrformer_sweetspot_ema.pt"
if (-not (Test-Path $WeightFile)) {
    Write-Error "[Error] Model weights not found at $WeightFile."
    exit 1
}

# 3. Check samples
$SampleDir = Join-Path $DatasetDir "samples"
$Samples = Get-ChildItem -Path $SampleDir -Filter "*.npz" -ErrorAction SilentlyContinue
if (-not $Samples -or $Samples.Count -eq 0) {
    Write-Error "[Error] Dataset samples not found in $SampleDir. Run prepare_dataset.py first."
    exit 1
}

# Set environment
$env:LOCAL_MODEL_DIR = $ModelDir
$env:LOCAL_DATASET_DIR = $DatasetDir
$env:ALLOWED_ORIGINS = "*"

if ($Device) {
    $env:DEVICE = $Device
} elseif (-not $env:DEVICE) {
    $env:DEVICE = "auto"
}

Write-Host "=========================================================="
Write-Host "Starting ECRformer Local Backend Server"
Write-Host "Venv:        $VenvPath"
Write-Host "Device:      $env:DEVICE"
Write-Host "Models:      $env:LOCAL_MODEL_DIR"
Write-Host "Dataset:     $env:LOCAL_DATASET_DIR"
Write-Host "Server URL:  http://127.0.0.1:7860"
Write-Host "Health:      http://127.0.0.1:7860/health"
Write-Host "Reminder: Open http://127.0.0.1:7860/health to verify service status."
Write-Host "=========================================================="

Push-Location -Path $SpaceDir
try {
    & $PythonExe -m uvicorn app:app --host 127.0.0.1 --port 7860
} finally {
    Pop-Location
}

