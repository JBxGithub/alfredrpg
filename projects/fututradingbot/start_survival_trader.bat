@echo off
chcp 65001 >nul
echo ==========================================
echo SURVIVAL TRADER - LIVE TRADING SYSTEM
echo ==========================================
echo.
echo Account: 6896 (REAL)
echo Daily Target: $50+
echo Daily Max Loss: $100
echo Trading Hours: 21:30 - 04:00
echo.
echo ⚠️  WARNING: THIS IS REAL MONEY! ⚠️
echo ==========================================
echo.

set PROJECT_DIR=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
set PYTHONPATH=%PROJECT_DIR%

cd /d %PROJECT_DIR%

echo [1/3] Checking Futu OpenD...
echo.

echo [2/3] Starting Survival Trader...
echo.
python src\survival_trader.py

echo.
echo ==========================================
echo Survival Trader stopped.
echo ==========================================
pause
