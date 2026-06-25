<#
.SYNOPSIS
  Tworzy środowisko Conda ecg-trust i instaluje zależności.
#>

$envName = "ecg-trust"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== Tworzenie środowiska Conda: $envName ===" -ForegroundColor Cyan

# 1. Sprawdź czy Conda jest dostępna
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Error "Conda nie jest zainstalowana. Zainstaluj Miniconda/Anaconda i spróbuj ponownie."
    exit 1
}

# 2. Utwórz środowisko z environment.yml
conda env create -f "$projectRoot\environment.yml" --name $envName

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Środowisko już istnieje – aktualizuję..."
    conda env update -f "$projectRoot\environment.yml" --name $envName
}

# 3. Zamroź wersje
& conda run -n $envName pip freeze > "$projectRoot\requirements-locked.txt"

Write-Host "=== Gotowe ===" -ForegroundColor Green
Write-Host "Aktywuj: conda activate $envName"
Write-Host "Zamrożone wersje zapisane w requirements-locked.txt"
