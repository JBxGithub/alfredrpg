# 六循環系統 - 自學習排程設置腳本 (PowerShell)
# 創建 Windows 定時任務

$ProjectPath = "C:\Users\BurtClaw\openclaw_workspace\projects\six-loop-system"
$PythonPath = "python"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  六循環系統 V9.4 - 排程設置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查管理員權限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  需要管理員權限運行此腳本" -ForegroundColor Yellow
    Write-Host "   請以管理員身份運行 PowerShell" -ForegroundColor Yellow
    exit 1
}

# 1. 每日監控任務 (08:00)
Write-Host "📅 創建每日監控任務..." -ForegroundColor Green
$Action1 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\run_adaptive_learning.py --mode daily" -WorkingDirectory $ProjectPath
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00"
$Settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal1 = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "SixLoop-Daily-Monitor" `
    -Action $Action1 `
    -Trigger $Trigger1 `
    -Settings $Settings1 `
    -Principal $Principal1 `
    -Description "六循環系統 - 每日監控 (檢查異常、自動保護)" `
    -Force

Write-Host "   ✅ 每日監控: 每天 08:00" -ForegroundColor Green

# 2. 每週回顧任務 (週一 09:00)
Write-Host "📅 創建每週回顧任務..." -ForegroundColor Green
$Action2 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\run_adaptive_learning.py --mode weekly" -WorkingDirectory $ProjectPath
$Trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
$Settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "SixLoop-Weekly-Review" `
    -Action $Action2 `
    -Trigger $Trigger2 `
    -Settings $Settings2 `
    -Principal $Principal1 `
    -Description "六循環系統 - 每週回顧 (趨勢分析、生成建議)" `
    -Force

Write-Host "   ✅ 每週回顧: 每週一 09:00" -ForegroundColor Green

# 3. 每月調整任務 (每月1日 10:00)
Write-Host "📅 創建每月調整任務..." -ForegroundColor Green
$Action3 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\run_adaptive_learning.py --mode monthly" -WorkingDirectory $ProjectPath
# 每月1日的觸發器需要特殊處理
$Trigger3 = New-ScheduledTaskTrigger -Once -At "2026-05-01T10:00:00" -RepetitionInterval (New-TimeSpan -Days 30)
$Settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "SixLoop-Monthly-Adjustment" `
    -Action $Action3 `
    -Trigger $Trigger3 `
    -Settings $Settings3 `
    -Principal $Principal1 `
    -Description "六循環系統 - 每月調整 (長期分析、參數優化)" `
    -Force

Write-Host "   ✅ 每月調整: 每月1日 10:00" -ForegroundColor Green

# 4. 持續監控服務 (背景運行)
Write-Host "📅 創建持續監控服務..." -ForegroundColor Green
$Action4 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\run_adaptive_learning.py --mode continuous" -WorkingDirectory $ProjectPath
$Trigger4 = New-ScheduledTaskTrigger -AtLogon
$Settings4 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "SixLoop-Continuous-Monitor" `
    -Action $Action4 `
    -Trigger $Trigger4 `
    -Settings $Settings4 `
    -Principal $Principal1 `
    -Description "六循環系統 - 持續監控 (用戶登入時啟動)" `
    -Force

Write-Host "   ✅ 持續監控: 登入時啟動" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  排程設置完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "創建的任務:" -ForegroundColor Yellow
Write-Host "  1. SixLoop-Daily-Monitor      - 每天 08:00" -ForegroundColor White
Write-Host "  2. SixLoop-Weekly-Review      - 每週一 09:00" -ForegroundColor White
Write-Host "  3. SixLoop-Monthly-Adjustment - 每月1日 10:00" -ForegroundColor White
Write-Host "  4. SixLoop-Continuous-Monitor - 登入時啟動" -ForegroundColor White
Write-Host ""
Write-Host "管理命令:" -ForegroundColor Yellow
Write-Host "  查看所有任務: Get-ScheduledTask | Where-Object {`$_.TaskName -like 'SixLoop-*'}" -ForegroundColor Gray
Write-Host "  啟動任務: Start-ScheduledTask -TaskName 'SixLoop-Daily-Monitor'" -ForegroundColor Gray
Write-Host "  停止任務: Stop-ScheduledTask -TaskName 'SixLoop-Daily-Monitor'" -ForegroundColor Gray
Write-Host "  刪除任務: Unregister-ScheduledTask -TaskName 'SixLoop-Daily-Monitor' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "任務計劃程序 GUI: taskschd.msc" -ForegroundColor Gray
Write-Host ""
