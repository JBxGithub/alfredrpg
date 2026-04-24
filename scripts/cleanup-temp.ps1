# OpenClaw Safe Temp Cleanup Script
# 每月自動清理 Temp 檔案，排除 OpenClaw 相關檔案
# 執行時間：每月 1 號 03:00

param(
    [switch]$Verbose = $false
)

$LogFile = "C:\Users\BurtClaw\openclaw_workspace\logs\cleanup-temp.log"
$StartTime = Get-Date

# 確保 log 目錄存在
$LogDir = Split-Path -Parent $LogFile
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $LogEntry
    if ($Verbose) { Write-Host $LogEntry }
}

Write-Log "=== Temp Cleanup Started ==="
Write-Log "執行時間: $StartTime"

# 統計變數
$TotalSize = 0
$FilesDeleted = 0
$FilesSkipped = 0
$Errors = @()

# 1. 清理用戶 Temp 目錄
Write-Log "清理用戶 Temp 目錄: $env:TEMP"
try {
    $UserTempFiles = Get-ChildItem -Path $env:TEMP -Recurse -Force -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.Name -notmatch 'openclaw|memory|dreaming|clawhub|alfred' -and
            $_.FullName -notmatch 'openclaw|memory|dreaming|clawhub|alfred'
        }
    
    foreach ($File in $UserTempFiles) {
        try {
            if ($File.PSIsContainer) {
                # 資料夾
                $Size = (Get-ChildItem $File.FullName -Recurse -Force -ErrorAction SilentlyContinue | 
                    Measure-Object -Property Length -Sum).Sum
                Remove-Item -Path $File.FullName -Recurse -Force -ErrorAction Stop
            } else {
                # 檔案
                $Size = $File.Length
                Remove-Item -Path $File.FullName -Force -ErrorAction Stop
            }
            $TotalSize += $Size
            $FilesDeleted++
            Write-Log "已刪除: $($File.FullName) ($( [math]::Round($Size / 1MB, 2) ) MB)"
        }
        catch {
            $FilesSkipped++
            Write-Log "跳過 (使用中): $($File.FullName)"
        }
    }
}
catch {
    $Errors += "用戶 Temp 清理錯誤: $_"
    Write-Log "錯誤: $_"
}

# 2. 清理 Windows 系統 Temp
Write-Log "清理 Windows 系統 Temp: C:\Windows\Temp"
try {
    $SystemTempFiles = Get-ChildItem -Path "C:\Windows\Temp" -Recurse -Force -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.Name -notmatch 'openclaw|memory|dreaming|clawhub|alfred' -and
            $_.FullName -notmatch 'openclaw|memory|dreaming|clawhub|alfred'
        }
    
    foreach ($File in $SystemTempFiles) {
        try {
            if ($File.PSIsContainer) {
                $Size = (Get-ChildItem $File.FullName -Recurse -Force -ErrorAction SilentlyContinue | 
                    Measure-Object -Property Length -Sum).Sum
                Remove-Item -Path $File.FullName -Recurse -Force -ErrorAction Stop
            } else {
                $Size = $File.Length
                Remove-Item -Path $File.FullName -Force -ErrorAction Stop
            }
            $TotalSize += $Size
            $FilesDeleted++
            Write-Log "已刪除: $($File.FullName) ($( [math]::Round($Size / 1MB, 2) ) MB)"
        }
        catch {
            $FilesSkipped++
            Write-Log "跳過 (使用中): $($File.FullName)"
        }
    }
}
catch {
    $Errors += "系統 Temp 清理錯誤: $_"
    Write-Log "錯誤: $_"
}

# 注意：Chrome 瀏覽器暫存已排除（靚仔要求）
# 如需清理 Chrome 暫存，請手動在 Chrome 設定中執行
Write-Log "Chrome 瀏覽器暫存已排除（根據設定要求）"

# 總結
$EndTime = Get-Date
$Duration = $EndTime - $StartTime
Write-Log "=== Temp Cleanup Completed ==="
Write-Log "執行時間: $( [math]::Round($Duration.TotalSeconds, 2) ) 秒"
Write-Log "刪除檔案數: $FilesDeleted"
Write-Log "跳過檔案數: $FilesSkipped"
Write-Log "釋放空間: $( [math]::Round($TotalSize / 1MB, 2) ) MB"

if ($Errors.Count -gt 0) {
    Write-Log "錯誤摘要:"
    foreach ($Error in $Errors) {
        Write-Log "  - $Error"
    }
}

Write-Log "下次清理: 下月 1 號 03:00"
Write-Log ""

# 輸出簡要結果
@{
    Status = "Completed"
    FilesDeleted = $FilesDeleted
    FilesSkipped = $FilesSkipped
    SpaceFreedMB = [math]::Round($TotalSize / 1MB, 2)
    DurationSeconds = [math]::Round($Duration.TotalSeconds, 2)
    Timestamp = $EndTime.ToString("yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json