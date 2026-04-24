@echo off
chcp 65001 >nul
echo ==========================================
echo FutuTradingBot - BREAKTHROUGH MODE
echo Account: 6896 | Survival Challenge
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
set PYTHONPATH=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

echo [BREAKTHROUGH] Initializing survival trader...
echo [BREAKTHROUGH] Target: $50+ daily profit
echo [BREAKTHROUGH] Risk limit: $100 daily loss
echo.

:START
echo [%date% %time%] Starting trader...
python.exe -u survival_trader.py > logs\survival_output.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] Trader crashed, restarting in 10 seconds...
    timeout /t 10 /nobreak >nul
    goto START
)

echo [%date% %time%] Trader stopped.
pause
