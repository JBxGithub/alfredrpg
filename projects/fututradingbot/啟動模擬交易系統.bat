@echo off
echo ==========================================
echo FutuTradingBot - 模擬交易系統（周一測試版）
echo ==========================================
echo.

cd /d C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

:: 檢查時間（周一晚上）
echo [檢查] 當前時間: %date% %time%
echo.

:: 清理現有進程
echo [1/4] 清理現有進程...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul
echo ✅ 清理完成
echo.

:: 創建日志目錄
if not exist logs mkdir logs
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

:: 啟動模擬 Bridge
echo [2/4] 啟動模擬 Bridge (Port 8766)...
start "模擬Bridge-8766" cmd /k "echo 模擬 Bridge 啟動中... && python simulation/paper_trading_bridge.py 2^>^&1 | tee logs/paper_bridge_%TIMESTAMP%.log"
echo ⏳ 等待 Bridge 啟動...
timeout /t 5 /nobreak >nul

:: 檢查 Bridge 是否成功啟動
netstat -an | findstr ":8766" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo ❌ Bridge 啟動失敗
    pause
    exit /b 1
)
echo ✅ 模擬 Bridge 已啟動
echo.

:: 啟動模擬 Dashboard
echo [3/4] 啟動模擬 Dashboard (Port 8081)...
start "模擬Dashboard-8081" cmd /k "echo 模擬 Dashboard 啟動中... && python simulation/paper_dashboard_stable.py 2^>^&1 | tee logs/paper_dashboard_%TIMESTAMP%.log"
timeout /t 5 /nobreak >nul
echo ✅ 模擬 Dashboard 已啟動
echo.

:: 檢查 Dashboard 是否成功啟動
netstat -an | findstr ":8081" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo ❌ Dashboard 啟動失敗
    pause
    exit /b 1
)
echo ✅ 模擬 Dashboard 已啟動
echo.

:: 顯示訪問資訊
echo ==========================================
echo ✅ 模擬交易系統啟動完成！
echo ==========================================
echo.
echo 訪問地址:
echo   模擬 Dashboard: http://127.0.0.1:8081
echo   密碼: paper2024
echo.
echo 日志檔案:
echo   logs/paper_bridge_%TIMESTAMP%.log
echo   logs/paper_dashboard_%TIMESTAMP%.log
echo.
echo 測試項目:
echo   1. Z-Score 策略（閾值 1.6）
echo   2. 模擬交易執行
necho   3. 交易記錄和績效追蹤
echo.
echo 按任意鍵關閉此窗口（系統將在背景繼續運行）
pause >nul
