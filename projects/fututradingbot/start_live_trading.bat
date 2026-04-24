@echo off
chcp 65001 >nul
title FutuTradingBot - 實盤交易啟動器

:: ============================================
:: FutuTradingBot 一鍵實盤交易啟動腳本
:: ============================================

echo.
echo  ╔═══════════════════════════════════════════════════════════════╗
echo  ║                                                               ║
echo  ║           FutuTradingBot - 自動化交易系統啟動器               ║
echo  ║                                                               ║
echo  ╚═══════════════════════════════════════════════════════════════╝
echo.

:: 設定路徑
set PROJECT_DIR=%~dp0
set PYTHON=python
set CONFIG_FILE=%PROJECT_DIR%config\live_trading_config.json

:: 檢查 Python
echo [1/6] 檢查 Python 環境...
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 找不到 Python，請確保 Python 已安裝並加入 PATH
    pause
    exit /b 1
)
echo ✅ Python 已就緒

:: 檢查必要檔案
echo.
echo [2/6] 檢查專案檔案...
if not exist "%PROJECT_DIR%src" (
    echo ❌ 錯誤: 找不到 src 目錄
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%config" (
    echo ⚠️  警告: config 目錄不存在，正在建立...
    mkdir "%PROJECT_DIR%config"
)
echo ✅ 專案檔案檢查通過

:: 顯示模式選擇
echo.
echo [3/6] 選擇交易模式:
echo.
echo     [1] 模擬交易 (Paper Trading) - 推薦先用此模式測試
echo     [2] 實盤交易 (Live Trading)  - ⚠️  真實資金交易
echo.
set /p MODE="請選擇 (1 或 2): "

if "%MODE%"=="1" (
    set TRADING_MODE=paper
    set MODE_NAME=模擬交易
) else if "%MODE%"=="2" (
    set TRADING_MODE=live
    set MODE_NAME=實盤交易
) else (
    echo ❌ 無效選擇，預設使用模擬交易
    set TRADING_MODE=paper
    set MODE_NAME=模擬交易
)

echo.
echo ✅ 已選擇: %MODE_NAME%

:: 風險確認
echo.
echo [4/6] 風險確認:
echo.
if "%TRADING_MODE%"=="live" (
    echo ⚠️  ⚠️  ⚠️  警告: 您即將啟動實盤交易！⚠️  ⚠️  ⚠️
    echo.
    echo     這將使用真實資金進行交易！
    echo     請確認:
    echo       1. 您已充分了解策略風險
    echo       2. 已設置適當的止損限制
    echo       3. 帳戶資金在可承受範圍內
    echo.
    set /p CONFIRM="輸入 'YES' 確認啟動實盤交易: "
    if not "!CONFIRM!"=="YES" (
        echo ❌ 未確認，取消啟動
        pause
        exit /b 1
    )
) else (
    echo ℹ️  模擬交易模式 - 不會使用真實資金
)

:: 啟動前檢查清單
echo.
echo [5/6] 執行啟動前檢查:
echo.

:: 檢查 1: API 配置
echo   □ 檢查 API 配置...
if exist "%PROJECT_DIR%config\api_config.json" (
    echo     ✅ API 配置檔案存在
) else (
    echo     ⚠️  API 配置檔案不存在，將使用預設配置
)

:: 檢查 2: 策略配置
echo   □ 檢查策略配置...
if exist "%PROJECT_DIR%config\strategy_config.json" (
    echo     ✅ 策略配置檔案存在
) else (
    echo     ⚠️  策略配置檔案不存在，將使用預設策略
)

:: 檢查 3: 日誌目錄
echo   □ 檢查日誌目錄...
if not exist "%PROJECT_DIR%logs" (
    mkdir "%PROJECT_DIR%logs"
    echo     ✅ 已建立日誌目錄
) else (
    echo     ✅ 日誌目錄已存在
)

:: 建立啟動配置
echo.
echo [6/6] 建立啟動配置...
(
echo {
echo   "trading_mode": "%TRADING_MODE%",
echo   "start_time": "%date% %time%",
echo   "auto_stop_loss": true,
echo   "auto_take_profit": true,
echo   "enable_monitoring": true,
echo   "max_daily_loss": 0.05,
echo   "max_drawdown": 0.10
}
) > "%CONFIG_FILE%"
echo ✅ 配置已儲存: %CONFIG_FILE%

:: 啟動系統
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║  正在啟動 %MODE_NAME% 系統...                                  ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: 啟動 Realtime Bridge (背景)
echo 📡 啟動 Realtime Bridge...
start "Realtime Bridge" cmd /k "cd /d %PROJECT_DIR% && %PYTHON% -m src.realtime_bridge.bridge"
timeout /t 2 /nobreak >nul

:: 啟動 Dashboard
echo 📊 啟動 Dashboard...
start "Trading Dashboard" cmd /k "cd /d %PROJECT_DIR% && %PYTHON% -m src.dashboard.app"
timeout /t 2 /nobreak >nul

:: 啟動主交易引擎
echo 🤖 啟動交易引擎...
cd /d %PROJECT_DIR%
%PYTHON% -c "
import asyncio
import sys
sys.path.insert(0, '%PROJECT_DIR%')

from src.automation import UnifiedTradingSystem, UnifiedConfig

async def main():
    print('╔═══════════════════════════════════════════════════════════════╗')
    print('║  FutuTradingBot 自動化交易系統                               ║')
    print('╚═══════════════════════════════════════════════════════════════╝')
    print()
    
    config = UnifiedConfig(
        strategy_name='TQQQ_Momentum',
        symbols=['TQQQ'],
        initial_capital=100000,
        paper_trading=%TRADING_MODE%=='paper',
        auto_adjust_params=True,
        auto_stop_loss=True,
        auto_take_profit=True
    )
    
    system = UnifiedTradingSystem()
    
    print(f'📊 交易模式: {config.paper_trading and \"模擬\" or \"實盤\"}')
    print(f'🎯 策略: {config.strategy_name}')
    print(f'💰 初始資金: ${config.initial_capital:,}')
    print()
    
    if await system.start(config):
        print('✅ 系統啟動成功！')
        print()
        print('按 Ctrl+C 停止系統')
        print()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print()
            print('🛑 正在停止系統...')
            await system.stop()
    else:
        print('❌ 系統啟動失敗')
        sys.exit(1)

asyncio.run(main())
"

:: 清理
echo.
echo 系統已停止
pause
