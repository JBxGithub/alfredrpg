@echo off
echo ==========================================
echo FutuTradingBot - 完整啟動腳本
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

:: 清理現有進程
echo [1/6] 清理現有進程...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul
echo ✅ 清理完成
echo.

:: 創建日志目錄
if not exist logs mkdir logs

:: 啟動實盤 Bridge
echo [2/6] 啟動實盤 Bridge (Port 8765)...
start "實盤Bridge-8765" cmd /k "echo 實盤 Bridge 啟動中... && python src/realtime_bridge.py && pause"
echo ⏳ 等待 Bridge 啟動...
timeout /t 5 /nobreak >nul
echo ✅ 實盤 Bridge 已啟動
echo.

:: 檢查 Bridge 是否成功啟動
echo [3/6] 檢查 Bridge 狀態...
netstat -an | findstr ":8765" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo ❌ Bridge 啟動失敗，請檢查錯誤訊息
    pause
    exit /b 1
)
echo ✅ Bridge 運行正常
echo.

:: 啟動實盤 Dashboard
echo [4/6] 啟動實盤 Dashboard (Port 8080)...
start "實盤Dashboard-8080" cmd /k "echo 實盤 Dashboard 啟動中... && python start_dashboard_simple.py && pause"
timeout /t 5 /nobreak >nul
echo ✅ 實盤 Dashboard 已啟動
echo.

:: 啟動模擬 Bridge
echo [5/6] 啟動模擬 Bridge (Port 8766)...
start "模擬Bridge-8766" cmd /k "echo 模擬 Bridge 啟動中... && python simulation/paper_trading_bridge.py && pause"
timeout /t 5 /nobreak >nul
echo ✅ 模擬 Bridge 已啟動
echo.

:: 啟動模擬 Dashboard
echo [6/6] 啟動模擬 Dashboard (Port 8081)...
start "模擬Dashboard-8081" cmd /k "echo 模擬 Dashboard 啟動中... && python simulation/start_paper_dashboard.py && pause"
timeout /t 5 /nobreak >nul
echo ✅ 模擬 Dashboard 已啟動
echo.

echo ==========================================
echo ✅ 所有系統啟動完成！
echo ==========================================
echo.
echo 請檢查以下窗口是否正常運行：
echo   1. 實盤Bridge-8765
echo   2. 實盤Dashboard-8080
echo   3. 模擬Bridge-8766
echo   4. 模擬Dashboard-8081
echo.
echo 訪問地址：
echo   實盤: http://127.0.0.1:8080
echo   模擬: http://127.0.0.1:8081
echo.
pause
