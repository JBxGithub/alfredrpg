@echo off
chcp 65001 >nul
echo ==========================================
echo FutuTradingBot - SURVIVAL MODE
echo Account: 6896 | Target: $50+/day
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
set PYTHONPATH=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

echo [SURVIVAL] Starting Survival Trader...
echo [SURVIVAL] Time: %date% %time%
echo.

python survival_trader.py

echo.
echo [SURVIVAL] Trader stopped.
echo [SURVIVAL] Time: %date% %time%
pause
