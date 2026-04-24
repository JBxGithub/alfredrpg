# Emergency Launch - Survival Mode
# Account: 6896 | Target: $50+ daily

$ProjectDir = "C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot"
$LogFile = "$ProjectDir\logs\emergency_launch.log"

function Write-Log($Message) {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "=========================================="
Write-Log "EMERGENCY LAUNCH - Survival Mode"
Write-Log "Account: 6896 | Target: $50+ daily"
Write-Log "=========================================="

Set-Location $ProjectDir
$env:PYTHONPATH = $ProjectDir

Write-Log "Checking OpenD connection..."
# Test connection
$TestConnection = Test-NetConnection -ComputerName 127.0.0.1 -Port 11111 -WarningAction SilentlyContinue
if ($TestConnection.TcpTestSucceeded) {
    Write-Log "OpenD is running on port 11111"
} else {
    Write-Log "WARNING: OpenD may not be running"
}

Write-Log "Starting survival trader..."
while ($true) {
    try {
        python.exe -u survival_trader.py
        $ExitCode = $LASTEXITCODE
        if ($ExitCode -eq 0) {
            Write-Log "Trader stopped normally"
            break
        } else {
            Write-Log "Trader crashed with exit code $ExitCode, restarting..."
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Log "ERROR: $_"
        Start-Sleep -Seconds 10
    }
}

Write-Log "Emergency launch ended"
