@echo off
chcp 65001 >nul
echo ==========================================
echo   六循環系統 V9.4 - 快速設置
echo ==========================================
echo.
echo 請以管理員身份運行此腳本
echo.

REM 設置變量
set PROJECT_PATH=C:\Users\BurtClaw\openclaw_workspace\projects\six-loop-system
set PYTHON_PATH=python

echo [1/4] 創建每日監控任務...
schtasks /create /tn "SixLoop-Daily-Monitor" /tr "%PYTHON_PATH% %PROJECT_PATH%\run_adaptive_learning.py --mode daily" /sc daily /st 08:00 /f /rl HIGHEST

echo [2/4] 創建每週回顧任務...
schtasks /create /tn "SixLoop-Weekly-Review" /tr "%PYTHON_PATH% %PROJECT_PATH%\run_adaptive_learning.py --mode weekly" /sc weekly /d MON /st 09:00 /f /rl HIGHEST

echo [3/4] 創建每月調整任務...
schtasks /create /tn "SixLoop-Monthly-Adjustment" /tr "%PYTHON_PATH% %PROJECT_PATH%\run_adaptive_learning.py --mode monthly" /sc monthly /mo 1 /st 10:00 /f /rl HIGHEST

echo [4/4] 創建持續監控任務 (登入時啟動)...
schtasks /create /tn "SixLoop-Continuous-Monitor" /tr "%PYTHON_PATH% %PROJECT_PATH%\run_adaptive_learning.py --mode continuous" /sc onlogon /f /rl HIGHEST

echo.
echo ==========================================
echo   設置完成！
echo ==========================================
echo.
echo 任務列表:
echo   - SixLoop-Daily-Monitor      (每天 08:00)
echo   - SixLoop-Weekly-Review      (每週一 09:00)
echo   - SixLoop-Monthly-Adjustment (每月1日 10:00)
echo   - SixLoop-Continuous-Monitor (登入時啟動)
echo.
echo 查看任務: taskschd.msc
echo.
pause
