# OpenClaw Gateway Auto-Start Script with Windows Update Detection
# Location: ~/openclaw_workspace/scripts/gateway-auto-start.ps1

param(
    [switch]$TestMode = $false
)

$LogFile = "$env:USERPROFILE\.openclaw\logs\gateway-auto-start.log"
$FlagFile = "$env:USERPROFILE\.openclaw\logs\last-boot.flag"
$Workspace = "C:\Users\BurtClaw\openclaw_workspace"

# Ensure log directory exists
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

# Get system boot info
$BootTime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$BootTimeStr = $BootTime.ToString("yyyy-MM-dd HH:mm:ss")
Write-Log "========================================"
Write-Log "System boot detection - Boot Time: $BootTimeStr"

# Check if reboot was caused by Windows Update
$IsWindowsUpdateReboot = $false
$RebootReason = "Normal boot"

try {
    # Method 1: Check event logs
    $UpdateEvents = Get-WinEvent -FilterHashtable @{
        LogName = 'System'
        ID = 1074, 6006, 6008
        StartTime = $BootTime.AddHours(-1)
    } -MaxEvents 5 -ErrorAction SilentlyContinue

    foreach ($Event in $UpdateEvents) {
        $Message = $Event.Message
        if ($Message -match "Windows Update" -or 
            $Message -match "Update" -or
            $Message -match "planned restart" -or
            $Message -match "reboot") {
            $IsWindowsUpdateReboot = $true
            $RebootReason = "Windows Update reboot (Event ID: $($Event.Id))"
            break
        }
    }

    # Method 2: Check for pending update sessions
    if (!$IsWindowsUpdateReboot) {
        try {
            $UpdateSession = New-Object -ComObject Microsoft.Update.Session
            $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
            $HistoryCount = $UpdateSearcher.GetTotalHistoryCount()
            
            if ($HistoryCount -gt 0) {
                $UpdateHistory = $UpdateSearcher.QueryHistory(0, [Math]::Min($HistoryCount, 10))
                $RecentUpdates = $UpdateHistory | Where-Object { 
                    $_.Date -gt $BootTime.AddHours(-2) -and 
                    $_.ResultCode -eq 2
                }
                if ($RecentUpdates) {
                    $IsWindowsUpdateReboot = $true
                    $RebootReason = "Windows Update installation completed"
                }
            }
        }
        catch {
            Write-Log "Windows Update check skipped: $($_.Exception.Message)"
        }
    }
}
catch {
    Write-Log "Error detecting reboot reason: $($_.Exception.Message)"
}

Write-Log "Reboot reason: $RebootReason"

# Update flag file
$BootTime.ToString("o") | Out-File $FlagFile -Force

# Check if Gateway is already running
try {
    $Response = Invoke-RestMethod -Uri "http://127.0.0.1:18789/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($Response) {
        Write-Log "Gateway is already running"
        
        # Send notification if Windows Update reboot or test mode
        if ($IsWindowsUpdateReboot -or $TestMode) {
            $NotifyMessage = "Windows Update reboot detected`n`nGateway is already running (recovered after reboot)`n`nReboot time: $BootTimeStr"
            & "$Workspace\scripts\send-whatsapp.ps1" -Message $NotifyMessage
        }
        exit 0
    }
}
catch {
    Write-Log "Gateway not running, preparing to start..."
}

# Start Gateway
Write-Log "Starting OpenClaw Gateway..."

try {
    # Start Gateway in foreground (visible window)
    $StartInfo = @{
        FilePath = "openclaw"
        ArgumentList = "gateway", "start"
        WorkingDirectory = $Workspace
        WindowStyle = "Normal"
        PassThru = $true
    }
    
    $Process = Start-Process @StartInfo
    Write-Log "Gateway starting (PID: $($Process.Id))"
    
    # Wait for Gateway to initialize
    Start-Sleep -Seconds 5
    
    # Verify Gateway started successfully
    $MaxRetries = 6
    $RetryCount = 0
    $GatewayRunning = $false
    
    while ($RetryCount -lt $MaxRetries) {
        try {
            $Health = Invoke-RestMethod -Uri "http://127.0.0.1:18789/health" -Method GET -TimeoutSec 3
            if ($Health) {
                $GatewayRunning = $true
                Write-Log "Gateway started successfully"
                break
            }
        }
        catch {
            $RetryCount++
            Write-Log "Waiting for Gateway ready... ($RetryCount/$MaxRetries)"
            Start-Sleep -Seconds 5
        }
    }
    
    # Send WhatsApp notification
    if ($IsWindowsUpdateReboot -or $TestMode) {
        if ($GatewayRunning) {
            $StatusEmoji = "OK"
            $StatusText = "Started successfully"
        } else {
            $StatusEmoji = "WARNING"
            $StatusText = "Start failed, please check"
        }
        
        $NotifyMessage = @"
Windows Update reboot detection

$StatusEmoji Gateway $StatusText
Reboot time: $BootTimeStr
Reason: $RebootReason
PID: $($Process.Id)

Auto-start script executed.
"@
        
        & "$Workspace\scripts\send-whatsapp.ps1" -Message $NotifyMessage
        Write-Log "WhatsApp notification sent"
    }
    else {
        Write-Log "Normal boot, skipping notification"
    }
}
catch {
    $ErrorMsg = $_.Exception.Message
    Write-Log "Error starting Gateway: $ErrorMsg"
    
    # Send error notification
    if ($IsWindowsUpdateReboot -or $TestMode) {
        $ErrorMessage = @"
Gateway auto-start failed

Reboot time: $BootTimeStr
Error: $ErrorMsg

Please check system manually.
"@
        & "$Workspace\scripts\send-whatsapp.ps1" -Message $ErrorMessage
    }
}

Write-Log "Script execution completed"
Write-Log "========================================"
