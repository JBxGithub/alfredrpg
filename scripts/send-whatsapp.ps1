# Send WhatsApp Notification via OpenClaw CLI
# Location: ~/openclaw_workspace/scripts/send-whatsapp.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$Message,
    
    [string]$Target = "+85263931048"
)

$LogFile = "$env:USERPROFILE\.openclaw\logs\whatsapp-notify.log"

function Write-Log {
    param([string]$Text)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Text" | Tee-Object -FilePath $LogFile -Append
}

try {
    Write-Log "Sending notification to $Target"
    
    # Create temp file with message
    $TempFile = [System.IO.Path]::GetTempFileName()
    $Message | Out-File $TempFile -Encoding UTF8
    
    # Use openclaw CLI to send message
    $result = & openclaw message send --target $Target --file $TempFile 2>&1
    $exitCode = $LASTEXITCODE
    
    Remove-Item $TempFile -Force
    
    if ($exitCode -eq 0) {
        Write-Log "Notification sent successfully"
    } else {
        Write-Log "CLI send failed with exit code $exitCode`: $result"
        
        # Fallback: try with message parameter directly
        $result2 = & openclaw message send --target $Target --message $Message 2>&1
        $exitCode2 = $LASTEXITCODE
        
        if ($exitCode2 -eq 0) {
            Write-Log "Fallback notification sent successfully"
        } else {
            Write-Log "Fallback also failed: $result2"
        }
    }
}
catch {
    Write-Log "Send failed: $($_.Exception.Message)"
}
