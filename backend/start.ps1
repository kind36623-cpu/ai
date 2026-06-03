# ============================================================
# Seed AGI - One-click startup script (Windows PowerShell)
# Run this from the backend folder: .\start.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$BackendDir = $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   SEED AGI - Backend Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
$pyVersion = python --version
Write-Host "[OK] $pyVersion detected" -ForegroundColor Green

# Step 2: Create virtual environment if missing
$VenvPath = Join-Path $BackendDir "venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate venv
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not activate venv automatically" -ForegroundColor Yellow
}

# Step 4: Install / upgrade dependencies
Write-Host "[INFO] Installing dependencies (this may take a minute first time)..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "[OK] Dependencies ready" -ForegroundColor Green

# Step 5: Check .env exists
$EnvFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "[ERROR] .env file not found! Copy .env.example to .env and add your API keys." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] .env found" -ForegroundColor Green

# Step 6: Launch the Brain
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Starting Seed AGI Backend on port 8001" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8001/docs" -ForegroundColor Gray
Write-Host "   Stop with Ctrl+C" -ForegroundColor DarkGray
Write-Host "==========================================" -ForegroundColor Blue

& python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
