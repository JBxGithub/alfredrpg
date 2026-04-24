@echo off
chcp 65001 >nul
echo ==========================================
echo Futu Trading Bot - Dashboard + Bridge
echo ==========================================
echo.

set PROJECT_DIR=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
set PYTHONPATH=%PROJECT_DIR%
set DASHBOARD_PORT=8080

cd /d %PROJECT_DIR%

echo [1/2] Starting Realtime Bridge...
echo     Connecting to Futu API...
start "Realtime Bridge" cmd /k "cd /d %PROJECT_DIR% && set PYTHONPATH=%PROJECT_DIR% && python src/realtime_bridge.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Dashboard Server...
echo     http://127.0.0.1:%DASHBOARD_PORT%
echo.
start "Dashboard Server" cmd /k "cd /d %PROJECT_DIR% && set PYTHONPATH=%PROJECT_DIR% && set DASHBOARD_PORT=%DASHBOARD_PORT% && python src/dashboard/app.py"

timeout /t 2 /nobreak >nul

echo ==========================================
echo Both services started!
echo.
echo Dashboard: http://127.0.0.1:%DASHBOARD_PORT%
echo Bridge: ws://127.0.0.1:8765
echo.
echo Close this window to keep services running.
echo Use the service windows to stop them.
echo ==========================================
pause
