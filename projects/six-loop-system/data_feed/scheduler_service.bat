@echo off
REM NQ100 自動更新服務 (Windows)
REM 使用方法: scheduler_service.bat

cd /d %~dp0..

echo [NQ100] 啟動排程服務...
echo 執行時間: 09:30, 14:00, 21:00
echo.

python data_feed\scheduler.py

pause