# Skill Security Audit Script for Windows
# Scans all installed skills for malicious patterns

$skillDir = "$env:USERPROFILE\openclaw_workspace\skills"
$patternsFile = "$skillDir\skill-security-auditor\patterns\malicious-patterns.json"
$patterns = Get-Content $patternsFile | ConvertFrom-Json

$results = @()
$skills = Get-ChildItem -Path $skillDir -Directory | Where-Object { $_.Name -notin @('_staging', 'skill-security-auditor') }

foreach ($skill in $skills) {
    $skillName = $skill.Name
    $skillPath = $skill.FullName
    $skillMdPath = "$skillPath\SKILL.md"
    
    if (-not (Test-Path $skillMdPath)) {
        continue
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Scanning: $skillName" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
    $content = Get-Content $skillMdPath -Raw
    $score = 0
    $findings = @()
    
    # Check Critical Patterns
    foreach ($pattern in $patterns.patterns.critical) {
        if ($content -match $pattern.pattern) {
            $score += $pattern.score_impact
            $findings += "[CRITICAL] $($pattern.id): $($pattern.name) - $($pattern.description)"
            Write-Host "  ❌ CRITICAL: $($pattern.name)" -ForegroundColor Red
        }
    }
    
    # Check High Patterns
    foreach ($pattern in $patterns.patterns.high) {
        if ($content -match $pattern.pattern) {
            $score += $pattern.score_impact
            $findings += "[HIGH] $($pattern.id): $($pattern.name) - $($pattern.description)"
            Write-Host "  ⚠️  HIGH: $($pattern.name)" -ForegroundColor DarkYellow
        }
    }
    
    # Check Medium Patterns
    foreach ($pattern in $patterns.patterns.medium) {
        if ($content -match $pattern.pattern) {
            $score += $pattern.score_impact
            $findings += "[MEDIUM] $($pattern.id): $($pattern.name)"
        }
    }
    
    # Determine Risk Level
    $riskLevel = "SAFE"
    $riskColor = "Green"
    if ($score -ge 80) { $riskLevel = "CRITICAL"; $riskColor = "DarkRed" }
    elseif ($score -ge 60) { $riskLevel = "HIGH RISK"; $riskColor = "Red" }
    elseif ($score -ge 40) { $riskLevel = "MEDIUM RISK"; $riskColor = "DarkYellow" }
    elseif ($score -ge 20) { $riskLevel = "LOW RISK"; $riskColor = "Yellow" }
    
    Write-Host "`n  Risk Score: $score/100 - $riskLevel" -ForegroundColor $riskColor
    
    if ($findings.Count -eq 0) {
        Write-Host "  ✅ No malicious patterns detected" -ForegroundColor Green
    }
    
    $results += [PSCustomObject]@{
        Skill = $skillName
        Score = $score
        RiskLevel = $riskLevel
        Findings = $findings
    }
}

# Summary Report
Write-Host "`n`n========================================" -ForegroundColor Cyan
Write-Host "         SECURITY AUDIT SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$safe = ($results | Where-Object { $_.RiskLevel -eq "SAFE" }).Count
$low = ($results | Where-Object { $_.RiskLevel -eq "LOW RISK" }).Count
$medium = ($results | Where-Object { $_.RiskLevel -eq "MEDIUM RISK" }).Count
$high = ($results | Where-Object { $_.RiskLevel -eq "HIGH RISK" }).Count
$critical = ($results | Where-Object { $_.RiskLevel -eq "CRITICAL" }).Count

Write-Host "`nTotal Skills Scanned: $($results.Count)" -ForegroundColor White
Write-Host "  ✅ SAFE: $safe" -ForegroundColor Green
Write-Host "  ⚠️  LOW RISK: $low" -ForegroundColor Yellow
Write-Host "  🟡 MEDIUM RISK: $medium" -ForegroundColor DarkYellow
Write-Host "  🔴 HIGH RISK: $high" -ForegroundColor Red
Write-Host "  ☠️  CRITICAL: $critical" -ForegroundColor DarkRed

if ($critical -gt 0 -or $high -gt 0) {
    Write-Host "`n⚠️  WARNING: High-risk skills detected! Review findings above." -ForegroundColor Red
}

# Export results
$results | ConvertTo-Json -Depth 3 | Out-File "$env:USERPROFILE\openclaw_workspace\skill-security-audit-results.json"
Write-Host "`n📄 Full results saved to: skill-security-audit-results.json" -ForegroundColor Gray
