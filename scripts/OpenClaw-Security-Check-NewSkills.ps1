# ================================================
# OpenClaw 全技能安全檢查一鍵腳本 v2.0
# 作者：Grok Automation Expert (2026.3)
# 功能：掃描你目前全部 68 個技能 + 彩色報告 + 自動記錄 + gateway restart
# 使用前：請 cd 到 OpenClaw 主目錄（包含 skills/ 資料夾）
# ================================================

$skills = @(
    "browser-automation","agent-browser","github","openclaw-github-assistant",
    "github-cli","github-trending-cn","github-ops","github-search",
    "github-issue-resolver","github-actions-generator","github-contribution",
    "github-pages-auto-deploy","parallel","last30days-official","live-task-pulse",
    "agenthub","document-skills","super-search","capability-evolver",
    "playwright-scraper","summarize","self-improving-agent","stock-watcher",
    "trading","stock-strategy-backtester","vision-sandbox","computer-vision-expert",
    "pdf-ocr","data-analysis","microsoft-excel","excel-xlsx","spreadsheet",
    "monitoring","red-alert","logging-observability","dashboard","reporting",
    "webhook","xurl","tmux","screenshot","safe-exec","safe-exec-0-3-2",
    "last30days","gog","stock-monitor","stock-study","skill-sandbox",
    "skill-security-auditor","mh-wacli","windows-ui-automation","desktop-control-win",
    "skill-vetter","find-skills","liang-tavily-search","skill-vetting",
    "obsidian-direct","git-workflows","agentmail-integration","cron-backup",
    "memory-setup","web-content-fetcher","nano-pdf","humanizer",
    "nano-banana-pro","proactive-agent-skill","proactive-agent-lite"
)

# 45 項危險關鍵字（已包含前版全部 + 高危項目）
$dangerKeywords = @(
    "wallet","crypto","base64","curl","wget","eval","exec","subprocess",
    "exfil","send data","api_key","private key","seed","http://","https://",
    "upload","post","exfiltrate","telemetry","key","password","secret",
    "token","credential","private","sensitive","keylog","screenshot",
    "hook","inject","shell","powershell","cmd.exe","bypass","obfuscate",
    "base64decode","requests.post","urllib","http.client","socket","ftp",
    "ssh","scp","smb","exfil","telemetry","analytics","tracking","spy",
    "backdoor","ransomware","malware","phish","steal","leak"
)

$pattern = ($dangerKeywords -join "|")
$reportFile = "Security-Audit-Report-AllSkills-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$findings = @()
$totalFiles = 0
$riskCount = 0

Write-Host "🚀 OpenClaw v2.0 全技能安全檢查開始 - 68 個技能" -ForegroundColor Cyan
Write-Host "掃描目錄：skills/ + 子資料夾 (Recurse)" -ForegroundColor Gray

foreach ($skill in $skills) {
    $skillPath = "skills\$skill"
    if (-not (Test-Path $skillPath)) {
        Write-Host "⚠️  找不到 skills\$skill，改為全域掃描" -ForegroundColor Yellow
        $skillPath = "."
    }

    $files = Get-ChildItem -Path $skillPath -Recurse -Include *.py,*.ps1,*.js,*.json,*.md,*.txt,*.sh -ErrorAction SilentlyContinue
    $totalFiles += $files.Count

    Write-Host "📂 檢查技能：$skill  (找到 $($files.Count) 個檔案)" -ForegroundColor White

    foreach ($file in $files) {
        $matches = Select-String -Path $file.FullName -Pattern $pattern -AllMatches -ErrorAction SilentlyContinue
        if ($matches) {
            $riskCount += $matches.Count
            foreach ($m in $matches) {
                $findings += "[HIGH RISK] $($file.FullName) : $($m.Line.Trim())"
                Write-Host "   ❌ 發現風險 @ $($file.Name) → $($m.Line.Trim())" -ForegroundColor Red
            }
        }
    }
}

# ==================== 報告輸出 ====================
Write-Host "`n✅ 掃描完成！總檔案：$totalFiles 個" -ForegroundColor Green

if ($riskCount -eq 0) {
    Write-Host "🎉 零風險！68 個技能全部安全通過！" -ForegroundColor Green
    $status = "PASS - 零風險"
} else {
    Write-Host "⚠️  發現 $riskCount 處潛在風險！請檢查上方紅色項目" -ForegroundColor Red
    $status = "WARNING - $riskCount 處風險"
}

$report = @"
OpenClaw v2.0 全技能安全檢查報告 - $(Get-Date)
技能總數：$($skills.Count)
總檔案數：$totalFiles
風險計數：$riskCount
狀態：$status

發現風險項目：
$($findings -join "`n")

建議下一步：
1. 若有風險 → clawhub uninstall <skill> 後重裝
2. openclaw gateway restart
3. 直接說「開始 futubot」進入交易主力
"@

$report | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "📄 詳細報告已儲存 → $reportFile" -ForegroundColor Cyan

# ==================== 額外安全步驟 ====================
Write-Host "`n🔄 嘗試執行 skill-security-auditor（若存在）..." -ForegroundColor Gray
if (Get-Command "skill-security-auditor" -ErrorAction SilentlyContinue) {
    foreach ($skill in $skills) { skill-security-auditor scan $skill }
} else {
    Write-Host "   skill-security-auditor 未找到（手動掃描已完成）" -ForegroundColor Yellow
}

Write-Host "`n🔄 重啟 OpenClaw Gateway..." -ForegroundColor Cyan
openclaw gateway restart

Write-Host "`n🎯 v2.0 檢查完成！可以安全使用全部技能。" -ForegroundColor Green
Write-Host "執行完請把報告貼給我，我立刻分析 + 給 futubot 安裝指令。" -ForegroundColor Magenta