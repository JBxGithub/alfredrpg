@echo off
chcp 65001 >nul
echo 🔄 Alfred 安全儀表板同步服務
echo ========================================
echo.

:: 檢查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 未安裝 Node.js
    exit /b 1
)

:: 設置環境變數（從 .env 文件讀取）
if exist "%~dp0.env" (
    for /f "tokens=*" %%a in (%~dp0.env) do (
        set %%a
    )
)

:: 檢查 GITHUB_TOKEN
if "%GITHUB_TOKEN%"=="" (
    echo ❌ 錯誤: 未設置 GITHUB_TOKEN
    echo 請設置環境變數 GITHUB_TOKEN 或創建 .env 文件
    exit /b 1
)

echo ✅ 環境檢查通過
echo 📡 開始同步...
echo.

:: 運行同步腳本
node "%~dp0sync-dashboard.js"

if errorlevel 1 (
    echo.
    echo ❌ 同步失敗
    exit /b 1
) else (
    echo.
    echo ✅ 同步成功！
    echo 🌐 儀表板: https://alfredrpg.net/dashboard.html
)
