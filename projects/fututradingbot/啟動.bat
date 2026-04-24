@echo off
echo ==========================================
echo FutuTradingBot - 一鍵啟動
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

:: 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 找不到 Python，請確保 Python 已安裝
    pause
    exit /b 1
)

echo ✅ Python 檢查通過
echo.

:: 啟動統一啟動器
echo 啟動系統...
python launcher.py

echo.
echo 系統已停止
echo.
pause
