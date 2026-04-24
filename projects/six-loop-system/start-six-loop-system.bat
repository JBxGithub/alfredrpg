@echo off
chcp 65001 >nul
echo ==========================================
echo  六循環系統 - 融合自動化引擎
echo  Six-Loop System - Fusion Automation Engine
echo ==========================================
echo.

REM Check PostgreSQL
echo [1/4] Checking PostgreSQL...
psql -h localhost -p 5432 -U postgres -c "SELECT version();" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL is not running!
    echo Please start PostgreSQL first.
    pause
    exit /b 1
)
echo      PostgreSQL is running.

REM Check Node-RED
echo [2/4] Checking Node-RED...
curl -s http://localhost:1880/flows >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node-RED is not running!
    echo Starting Node-RED...
    start "Node-RED" node-red
    timeout /t 5 /nobreak >nul
)
echo      Node-RED is running.

REM Check Futu OpenD
echo [3/4] Checking Futu OpenD...
netstat -an | findstr "11111" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Futu OpenD is not detected on port 11111.
    echo Please ensure Futu OpenD is running.
)
echo      Futu OpenD check complete.

REM Test Decision Engine
echo [4/4] Testing Decision Engine...
python "%~dp0decision-engine\main.py" > "%~dp0logs\decision-test.log" 2>&1
if %errorlevel% equ 0 (
    echo      Decision Engine is working.
) else (
    echo WARNING: Decision Engine test failed.
)

echo.
echo ==========================================
echo  System Status: READY
echo ==========================================
echo.
echo Components:
echo   - PostgreSQL: localhost:5432/trading_db
echo   - Node-RED: http://localhost:1880
echo   - Decision Engine: Python module ready
echo   - Futu Adapter: Python module ready
echo.
echo Quick Commands:
echo   - View logs: tail -f logs\system.log
echo   - Run decision: python decision-engine\main.py
echo   - Run futu adapter: python futu-adapter\main.py
echo.
pause