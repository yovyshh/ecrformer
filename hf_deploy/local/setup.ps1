[CmdletBinding()]
param(
    [switch]$Cpu,
    [switch]$Gpu,
    [string]$TorchIndexUrl = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path

if ($env:VENV_DIR) {
    $VenvPath = $env:VENV_DIR
} else {
    $VenvPath = Join-Path $RepoRoot "hf_deploy\.venv"
}

Write-Host "Target venv: $VenvPath"

# G1: Python selection
function Get-PyCandidateVersion($cmdName, $extraArg) {
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $cmdName
        $argPrefix = if ($extraArg) { "$extraArg " } else { "" }
        $psi.Arguments = $argPrefix + '-c "import sys; print(sys.version_info.major, sys.version_info.minor)"'
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $p = [System.Diagnostics.Process]::Start($psi)
        $p.WaitForExit()
        if ($p.ExitCode -eq 0) {
            $raw = $p.StandardOutput.ReadToEnd().Trim()
            $parts = $raw -split '\s+'
            if ($parts.Count -ge 2) {
                return "$($parts[0]).$($parts[1])"
            }
        }
    } catch {}
    return $null
}

$SelectedPyCmd = @()
$SelectedPyVer = ""

if (Get-Command "py" -ErrorAction SilentlyContinue) {
    $ver = Get-PyCandidateVersion "py" "-3.12"
    if ($ver -eq "3.12") {
        $SelectedPyCmd = @("py", "-3.12")
        $SelectedPyVer = "3.12"
    } else {
        $ver = Get-PyCandidateVersion "py" "-3.11"
        if ($ver -eq "3.11") {
            $SelectedPyCmd = @("py", "-3.11")
            $SelectedPyVer = "3.11"
        }
    }
}

if (-not $SelectedPyVer -and (Get-Command "python" -ErrorAction SilentlyContinue)) {
    $ver = Get-PyCandidateVersion "python" ""
    if ($ver -in @("3.11", "3.12")) {
        $SelectedPyCmd = @("python")
        $SelectedPyVer = $ver
    } elseif ($ver) {
        $parts = $ver.Split('.')
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 13)) {
            Write-Error "Python $ver detected. Python 3.13+ is not supported. Please install Python 3.12: winget install Python.Python.3.12"
            exit 1
        }
    }
}

if (-not $SelectedPyVer) {
    Write-Error "No compatible Python 3.11 or 3.12 found. Python 3.13+ is not supported. Please install Python 3.12: winget install Python.Python.3.12"
    exit 1
}

Write-Host "Selected Python: $($SelectedPyCmd -join ' ') (version $SelectedPyVer)"

# Recreate venv if built with a different Python version
if (Test-Path $VenvPath) {
    $existingPy = Join-Path $VenvPath "Scripts\python.exe"
    if (-not (Test-Path $existingPy)) {
        $existingPy = Join-Path $VenvPath "bin\python"
    }
    $existingVer = ""
    if (Test-Path $existingPy) {
        $existingVer = Get-PyCandidateVersion $existingPy ""
    }
    if ($existingVer -ne $SelectedPyVer) {
        Write-Host "Existing venv was built with Python '$existingVer' (selected is '$SelectedPyVer'). Deleting and recreating..."
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "Virtual environment already exists at $VenvPath with Python $existingVer."
    }
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment at $VenvPath..."
    if ($SelectedPyCmd.Length -gt 1) {
        & $SelectedPyCmd[0] $SelectedPyCmd[1..($SelectedPyCmd.Length - 1)] -m venv "$VenvPath"
    } else {
        & $SelectedPyCmd[0] -m venv "$VenvPath"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = Join-Path $VenvPath "bin\python"
}
if (-not (Test-Path $PythonExe)) {
    throw "Python binary not found in $VenvPath"
}

Write-Host "Upgrading pip..."
& $PythonExe -m pip install --upgrade pip

# G2: GPU setup logic
$installGpu = $false
$DriverCudaVersion = 0.0

if ($Cpu) {
    Write-Host "Force CPU requested (-Cpu)."
    $installGpu = $false
} elseif ($Gpu) {
    Write-Host "Force GPU requested (-Gpu)."
    $installGpu = $true
} else {
    # Auto-detect via nvidia-smi
    $smiCmd = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
    if ($smiCmd) {
        $smiOut = & nvidia-smi 2>$null
        $smiText = ($smiOut -join "`n")
        if ($smiText -match "CUDA Version:\s*([0-9]+\.[0-9]+)") {
            $DriverCudaVersion = [double]$Matches[1]
            Write-Host "Detected NVIDIA GPU with Driver CUDA Version: $DriverCudaVersion"
            $installGpu = $true
        } else {
            Write-Host "nvidia-smi found but could not parse CUDA version. Defaulting to CPU."
            $installGpu = $false
        }
    } else {
        Write-Host "nvidia-smi not found. Defaulting to CPU build."
        $installGpu = $false
    }
}

$torchInstalled = $false

if ($installGpu) {
    $candidateIndexes = @()
    if ($TorchIndexUrl) {
        $candidateIndexes += @{ Name="Custom"; Url=$TorchIndexUrl }
    } else {
        $allIndexes = @(
            @{ Name="cu126"; Version=12.6; Url="https://download.pytorch.org/whl/cu126" },
            @{ Name="cu124"; Version=12.4; Url="https://download.pytorch.org/whl/cu124" },
            @{ Name="cu121"; Version=12.1; Url="https://download.pytorch.org/whl/cu121" },
            @{ Name="cu118"; Version=11.8; Url="https://download.pytorch.org/whl/cu118" }
        )
        foreach ($cand in $allIndexes) {
            if ($DriverCudaVersion -eq 0.0 -or $cand.Version -le $DriverCudaVersion) {
                $candidateIndexes += $cand
            }
        }
    }

    foreach ($cand in $candidateIndexes) {
        $idxUrl = $cand.Url
        Write-Host "Attempting PyTorch installation with $($cand.Name) index ($idxUrl)..."
        & $PythonExe -m pip install torch torchvision --index-url $idxUrl
        if ($LASTEXITCODE -eq 0) {
            $torchInstalled = $true
            Write-Host "PyTorch successfully installed from $idxUrl"
            break
        } else {
            Write-Warning "Installation failed using $idxUrl. Trying next candidate..."
        }
    }

    if (-not $torchInstalled) {
        Write-Warning "`n[WARNING] Failed to install CUDA PyTorch with all candidate wheel indexes! Falling back to CPU build.`nPick the right CUDA build command from https://pytorch.org and specify -TorchIndexUrl if needed.`n"
    }
}

if (-not $torchInstalled) {
    $isMac = ($PSVersionTable.OS -like "*Darwin*")
    if ($isMac) {
        Write-Host "Installing CPU PyTorch from PyPI (macOS)..."
        & $PythonExe -m pip install torch torchvision
    } else {
        Write-Host "Installing CPU PyTorch from https://download.pytorch.org/whl/cpu..."
        & $PythonExe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install CPU PyTorch"
    }
}

$ReqPath = Join-Path $ScriptDir "requirements.txt"
Write-Host "Installing dependencies from $ReqPath..."
& $PythonExe -m pip install -r "$ReqPath"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install requirements.txt"
}

Write-Host "`n=== PyTorch Verification ==="
& $PythonExe -c "
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
