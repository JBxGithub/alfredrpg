@echo off
echo ==========================================
echo FutuTradingBot - 啟動腳本
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

:: 檢查並清理現有進程
echo [1/5] 檢查並清理現有進程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo ✅ 清理完成
echo.

:: 創建日志目錄
if not exist logs mkdir logs

:: 啟動實盤 Bridge
echo [2/5] 啟動實盤 Bridge (Port 8765)...
start cmd /k "python src/realtime_bridge.py"
timeout /t 3 /nobreak >nul
echo ✅ 實盤 Bridge 啟動中...
echo.

:: 啟動實盤 Dashboard
echo [3/5] 啟動實盤 Dashboard (Port 8080)...
start cmd /k "python start_dashboard_simple.py"
timeout /t 3 /nobreak >nul
echo ✅ 實盤 Dashboard 啟動中...
echo.

:: 啟動模擬 Bridge
echo [4/5] 啟動模擬 Bridge (Port 8766)...
start cmd /k "python simulation/paper_trading_bridge.py"
timeout /t 3 /nobreak >nul
echo ✅ 模擬 Bridge 啟動中...
echo.

:: 啟動模擬 Dashboard
echo [5/5] 啟動模擬 Dashboard (Port 8081)...
start cmd /k "python simulation/start_paper_dashboard.py"
timeout /t 3 /nobreak >nul
echo ✅ 模擬 Dashboard 啟動中...
echo.

echo ==========================================
echo 所有系統啟動中...
echo ==========================================
echo.
echo 請等待 10 秒後檢查：
echo   實盤 Dashboard: http://127.0.0.1:8080
echo   模擬 Dashboard: http://127.0.0.1:8081
echo.
pause
