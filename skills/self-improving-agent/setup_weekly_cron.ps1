# Self-Improving Skills Weekly Review - Cron Job

$jobName = "SelfImproving-Weekly-Review"
$scriptPath = "$env:USERPROFILE\openclaw_workspace\skills\self-improving-agent\weekly_review.py"
$pythonPath = "python"

# 檢查是否已存在
$existingJob = Get-ScheduledTask -TaskName $jobName -ErrorAction SilentlyContinue

if ($existingJob) {
    Write-Host "Job already exists: $jobName"
    Write-Host "Updating..."
    Unregister-ScheduledTask -TaskName $jobName -Confirm:$false
}

# 創建動作 (比 AMS 晚 30 分鐘執行)
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath

# 創建觸發器 (每週一上午 9:30)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:30"

# 創建設置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# 註冊任務
Register-ScheduledTask -TaskName $jobName -Action $action -Trigger $trigger -Settings $settings -Description "Self-Improving Skills 每週回顧 - 分析 .learnings/ 記錄"

Write-Host "✅ Cron job created: $jobName"
Write-Host "   Schedule: Every Monday at 09:30"
Write-Host "   Script: $scriptPath"

Get-ScheduledTask -TaskName $jobName | Select-Object TaskName, State, NextRunTime | Format-Table -AutoSize
