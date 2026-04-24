@echo off
chcp 65001 >nul
echo ==========================================
echo FutuTradingBot - 一鍵啟動腳本 (修復版)
echo ==========================================
echo.

set WORKSPACE=C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
cd /d %WORKSPACE%

:: 創建日志目錄
if not exist logs mkdir logs

:: 檢查端口
echo [檢查] 檢查端口狀態...
netstat -an | findstr ":8765 " | findstr "LISTENING" >nul && (
    echo ⚠️  Port 8765 已被佔用
    goto :error
)
netstat -an | findstr ":8080 " | findstr "LISTENING" >nul && (
    echo ⚠️  Port 8080 已被佔用
    goto :error
)
netstat -an | findstr ":8766 " | findstr "LISTENING" >nul && (
    echo ⚠️  Port 8766 已被佔用
    goto :error
)
netstat -an | findstr ":8081 " | findstr "LISTENING" >nul && (
    echo ⚠️  Port 8081 已被佔用
    goto :error
)
echo ✅ 端口檢查通過
echo.

:: 獲取時間戳
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

:: 啟動實盤 Bridge
echo [1/4] 啟動實盤 Bridge (Port 8765)...
start "實盤 Bridge" cmd /k "cd /d %WORKSPACE% && python src/realtime_bridge.py"
timeout /t 5 /nobreak >nul
echo ✅ 實盤 Bridge 已啟動
echo.

:: 啟動實盤 Dashboard
echo [2/4] 啟動實盤 Dashboard (Port 8080)...
start "實盤 Dashboard" cmd /k "cd /d %WORKSPACE% && python start_dashboard_simple.py"
timeout /t 5 /nobreak >nul
echo ✅ 實盤 Dashboard 已啟動
echo.

:: 啟動模擬 Bridge
echo [3/4] 啟動模擬 Bridge (Port 8766)...
start "模擬 Bridge" cmd /k "cd /d %WORKSPACE% && python simulation/paper_trading_bridge.py"
timeout /t 5 /nobreak >nul
echo ✅ 模擬 Bridge 已啟動
echo.

:: 啟動模擬 Dashboard
echo [4/4] 啟動模擬 Dashboard (Port 8081)...
start "模擬 Dashboard" cmd /k "cd /d %WORKSPACE% && python simulation/start_paper_dashboard.py"
timeout /t 5 /nobreak >nul
echo ✅ 模擬 Dashboard 已啟動
echo.

echo ==========================================
echo ✅ 所有系統啟動完成！
echo ==========================================
echo.
echo 訪問地址:
echo   實盤 Dashboard: http://127.0.0.1:8080 (密碼: futu2024)
echo   模擬 Dashboard: http://127.0.0.1:8081 (密碼: paper2024)
echo.
echo 按任意鍵關閉此窗口（系統將在背景繼續運行）
pause >nul
goto :end

:error
echo.
echo ❌ 啟動失敗：端口被佔用
echo 請先關閉現有進程，然後重試
echo.
pause
exit /b 1

:end
