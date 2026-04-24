# Futu Trading Bot - Python Virtual Environment Setup Script
# For Windows PowerShell

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$VenvPath = Join-Path $ProjectRoot ".venv"
$RequirementsPath = Join-Path $ProjectRoot "requirements.txt"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Futu Trading Bot - Venv Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $PythonVersion = python --version 2>&1
    Write-Host "Found: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment if not exists
if (Test-Path $VenvPath) {
    Write-Host "Virtual environment already exists at: $VenvPath" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "Using existing virtual environment." -ForegroundColor Green
    }
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment at: $VenvPath" -ForegroundColor Yellow
    python -m venv $VenvPath
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Host "Error: Activate script not found at $ActivateScript" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
if (Test-Path $RequirementsPath) {
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    pip install -r $RequirementsPath
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: requirements.txt not found at $RequirementsPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate the virtual environment manually, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\activate-venv.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate, run:" -ForegroundColor Cyan
Write-Host "  deactivate" -ForegroundColor White
