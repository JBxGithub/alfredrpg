# Futu Trading Bot - Activate Virtual Environment
# For Windows PowerShell

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$VenvPath = Join-Path $ProjectRoot ".venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $ActivateScript) {
    Write-Host "Activating Futu Trading Bot virtual environment..." -ForegroundColor Green
    & $ActivateScript
    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host "Python: $(python --version)" -ForegroundColor Cyan
    Write-Host "Pip: $(pip --version)" -ForegroundColor Cyan
} else {
    Write-Host "Error: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Please run setup-venv.ps1 first." -ForegroundColor Yellow
}
