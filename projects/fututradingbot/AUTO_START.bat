@echo off
chcp 65001 >nul
echo ==========================================
echo FutuTradingBot - AUTO START
echo Survival Mode - Account 6896
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
set PYTHONPATH=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

echo [AUTO] Checking Futu OpenD...
timeout /t 2 /nobreak >nul

echo [AUTO] Starting Survival Trader...
echo [AUTO] Time: %date% %time%
echo.

python.exe survival_trader.py

echo.
echo [AUTO] Trader stopped.
echo [AUTO] Time: %date% %time%
echo.
echo Press any key to exit...
pause >nul
