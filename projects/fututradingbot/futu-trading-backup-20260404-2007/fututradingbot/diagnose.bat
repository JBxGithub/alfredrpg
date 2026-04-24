@echo off
echo ==========================================
echo FutuTradingBot - 診斷腳本
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

echo [1/4] 檢查 Python...
python --version
echo.

echo [2/4] 檢查文件...
if exist src\realtime_bridge.py echo ✅ realtime_bridge.py 存在
if exist src\dashboard\app.py echo ✅ app.py 存在
if exist templates\dashboard.html echo ✅ dashboard.html 存在
if exist start_dashboard_simple.py echo ✅ start_dashboard_simple.py 存在
echo.

echo [3/4] 清理進程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo ✅ 清理完成
echo.

echo [4/4] 測試啟動 Bridge...
start "Bridge測試" cmd /k "python src/realtime_bridge.py"
echo ⏳ 等待 5 秒...
timeout /t 5 /nobreak >nul

echo 檢查端口 8765...
netstat -an | findstr ":8765" | findstr "LISTENING"
if errorlevel 1 (
    echo ❌ Bridge 未在 8765 監聽
) else (
    echo ✅ Bridge 運行正常
)
echo.

echo 按任意鍵關閉所有測試窗口...
pause
taskkill /F /IM python.exe 2>nul
