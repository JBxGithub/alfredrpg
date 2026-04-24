# Survival Trader Runner
# 啟動 survival_trader.py 並監控

Write-Host "========================================" -ForegroundColor Green
Write-Host "[生存挑戰] 啟動 Survival Trader" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 檢查 OpenD
Write-Host "`n[1/3] 檢查 Futu OpenD 狀態..." -ForegroundColor Yellow
$connection = Test-NetConnection -ComputerName 127.0.0.1 -Port 11111 -WarningAction SilentlyContinue
if ($connection.TcpTestSucceeded) {
    Write-Host "[結果] OpenD 正在運行 ✓" -ForegroundColor Green
} else {
    Write-Host "[結果] OpenD 未運行 ✗" -ForegroundColor Red
    Write-Host "[錯誤] 請先啟動 Futu OpenD" -ForegroundColor Red
    exit 1
}

# 切換目錄
Write-Host "`n[2/3] 切換到交易目錄..." -ForegroundColor Yellow
$traderPath = "C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot"
Set-Location $traderPath
Write-Host "[結果] 當前目錄: $(Get-Location)" -ForegroundColor Green

# 啟動交易程序
Write-Host "`n[3/3] 啟動 survival_trader.py..." -ForegroundColor Yellow
Write-Host "[監控] 每30秒報告狀態" -ForegroundColor Cyan
Write-Host "[提示] 按 Ctrl+C 停止`n" -ForegroundColor Gray

& "C:\Python314\python.exe" "survival_trader.py"

Write-Host "`n[結束] 交易程序已停止" -ForegroundColor Yellow
