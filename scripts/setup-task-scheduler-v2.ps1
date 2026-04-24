# setup-task-scheduler-v2.ps1 - 設定健康檢查自動執行（修正版）
# 用途: 建立 Windows Task Scheduler 任務
# 執行方式: 以系統管理員身份執行此腳本

$ScriptDir = "C:\Users\BurtClaw\openclaw_workspace\scripts"
$UserName = $env:USERNAME

Write-Host "設定健康檢查自動執行..." -ForegroundColor Cyan
Write-Host "腳本位置: $ScriptDir" -ForegroundColor Gray
Write-Host "使用者: $UserName" -ForegroundColor Gray

# 確保腳本存在
$HealthMonitor = Join-Path $ScriptDir "health-monitor.ps1"
$HealthCheck = Join-Path $ScriptDir "health-check.ps1"

if (!(Test-Path $HealthMonitor)) {
    Write-Error "找不到 health-monitor.ps1"
    exit 1
}
if (!(Test-Path $HealthCheck)) {
    Write-Error "找不到 health-check.ps1"
    exit 1
}

# ============================================
# 任務 1: health-monitor.ps1 (每12小時)
# ============================================
Write-Host "`n建立任務: Health Monitor (每12小時)..." -ForegroundColor Yellow

$TaskName1 = "OpenClaw-Health-Monitor"

# 使用 XML 定義任務以支援重複間隔
$Xml1 = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>OpenClaw 健康監控 - 每12小時執行一次</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$(Get-Date -Format "yyyy-MM-dd")T00:00:00</StartBoundary>
      <Repetition>
        <Interval>PT12H</Interval>
        <Duration>P3650D</Duration>
      </Repetition>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -WindowStyle Hidden -File "$HealthMonitor"</Arguments>
    </Exec>
  </Actions>
</Task>
"@

$XmlPath1 = "$env:TEMP\task1.xml"
$Xml1 | Out-File -FilePath $XmlPath1 -Encoding Unicode

try {
    schtasks /Create /TN $TaskName1 /XML $XmlPath1 /F 2>&1 | Out-Null
    Write-Host "✅ 任務已建立: $TaskName1 (每12小時)" -ForegroundColor Green
    Remove-Item $XmlPath1 -ErrorAction SilentlyContinue
} catch {
    Write-Error "無法建立任務 ${TaskName1}: $_"
}

# ============================================
# 任務 2: health-check.ps1 (每2日)
# ============================================
Write-Host "`n建立任務: Health Check (每2日)..." -ForegroundColor Yellow

$TaskName2 = "OpenClaw-Health-Check-Full"

$Xml2 = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>OpenClaw 詳細健康檢查 - 每2日執行一次</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$(Get-Date -Format "yyyy-MM-dd")T06:00:00</StartBoundary>
      <Repetition>
        <Interval>P2D</Interval>
        <Duration>P3650D</Duration>
      </Repetition>
      <ScheduleByDay>
        <DaysInterval>2</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -WindowStyle Hidden -File "$HealthCheck"</Arguments>
    </Exec>
  </Actions>
</Task>
"@

$XmlPath2 = "$env:TEMP\task2.xml"
$Xml2 | Out-File -FilePath $XmlPath2 -Encoding Unicode

try {
    schtasks /Create /TN $TaskName2 /XML $XmlPath2 /F 2>&1 | Out-Null
    Write-Host "✅ 任務已建立: $TaskName2 (每2日)" -ForegroundColor Green
    Remove-Item $XmlPath2 -ErrorAction SilentlyContinue
} catch {
    Write-Error "無法建立任務 ${TaskName2}: $_"
}

# ============================================
# 任務 3: 開機時執行
# ============================================
Write-Host "`n建立任務: Startup Health Check..." -ForegroundColor Yellow

$TaskName3 = "OpenClaw-Health-Startup"

$Xml3 = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>OpenClaw 開機健康檢查</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -WindowStyle Hidden -File "$HealthMonitor"</Arguments>
    </Exec>
  </Actions>
</Task>
"@

$XmlPath3 = "$env:TEMP\task3.xml"
$Xml3 | Out-File -FilePath $XmlPath3 -Encoding Unicode

try {
    schtasks /Create /TN $TaskName3 /XML $XmlPath3 /F 2>&1 | Out-Null
    Write-Host "✅ 任務已建立: $TaskName3 (開機時)" -ForegroundColor Green
    Remove-Item $XmlPath3 -ErrorAction SilentlyContinue
} catch {
    Write-Warning "無法建立開機任務（需要管理員權限）: $_"
    Write-Host "   提示: 以系統管理員身份執行此腳本以建立開機任務" -ForegroundColor Yellow
}

Write-Host "`n========== 設定完成 ==========" -ForegroundColor Cyan
Write-Host "已建立以下排程任務:" -ForegroundColor Gray
Write-Host "  1. OpenClaw-Health-Monitor    - 每12小時執行健康監控" -ForegroundColor Green
Write-Host "  2. OpenClaw-Health-Check-Full - 每2日執行詳細檢查" -ForegroundColor Green
Write-Host "  3. OpenClaw-Health-Startup    - 開機時執行快速檢查" -ForegroundColor Green
Write-Host "`n查看任務: 開啟 Task Scheduler (taskschd.msc)" -ForegroundColor Yellow
Write-Host "或執行: schtasks /Query /TN OpenClaw-* /FO LIST" -ForegroundColor Gray
Write-Host "日誌位置: C:\Users\BurtClaw\openclaw_workspace\memory\health-logs\`n" -ForegroundColor Gray
