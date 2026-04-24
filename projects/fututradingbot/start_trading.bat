@echo off
echo [啟動] Survival Trader
echo [時間] %date% %time%
echo [帳戶] 6896
echo ============================
cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
python survival_trader.py
echo.
echo [結束] Survival Trader 已停止
echo [時間] %date% %time%
pause
