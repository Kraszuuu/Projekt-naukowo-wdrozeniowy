<#
.SYNOPSIS
  Creates a Python virtual environment (.venv) and installs dependencies from requirements.txt.
#>

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Write-Host "=== Creating virtual environment: .venv ===" -ForegroundColor Cyan

# 1. Find a suitable Python interpreter (prefer 3.11, then 3.12, then 3.10).
$pythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($ver in @("3.11", "3.12", "3.10")) {
        & py "-$ver" --version *> $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = (& py "-$ver" -c "import sys; print(sys.executable)").Trim()
            break
        }
    }
}
if (-not $pythonExe) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $pythonExe = $cmd.Source }
}
if (-not $pythonExe) {
    Write-Error "Python not found. Install Python 3.11 (or 3.10/3.12) and try again."
    exit 1
}
Write-Host "Using Python: $pythonExe" -ForegroundColor DarkGray

# 2. Create the venv.
& $pythonExe -m venv $venvPath

# 3. Upgrade pip and install dependencies.
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r "$projectRoot\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Dependency installation failed."
    exit 1
}

# 4. Freeze versions.
& $venvPython -m pip freeze > "$projectRoot\requirements-locked.txt"

Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Frozen versions saved to requirements-locked.txt"
