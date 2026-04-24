# ClawTeam Multi-Agent Test Script
# Usage: Test communication between agents

Write-Host "🧪 Testing ClawTeam Multi-Agent System..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Check File Structure
Write-Host "Test 1: Checking Agent File Structure..." -ForegroundColor Yellow
$agents = @("dataforge", "signalseorge", "tradeforge", "orchestrator")
$allFilesExist = $true

foreach ($agent in $agents) {
    $soulPath = "$env:USERPROFILE\openclaw_workspace\agents\$agent\SOUL.md"
    $identityPath = "$env:USERPROFILE\openclaw_workspace\agents\$agent\IDENTITY.md"
    
    if ($agent -eq "orchestrator") {
        $soulPath = "$env:USERPROFILE\openclaw_workspace\agents\CLAWTEAM.md"
    }
    
    $soulExists = Test-Path $soulPath
    $identityExists = Test-Path $identityPath
    
    if ($soulExists -and $identityExists) {
        Write-Host "  ✅ $agent : SOUL.md + IDENTITY.md" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $agent : Missing files" -ForegroundColor Red
        $allFilesExist = $false
    }
}
Write-Host ""

# Test 2: Check Config Files
Write-Host "Test 2: Checking Config Files..." -ForegroundColor Yellow
$configAgents = @("dataforge", "signalseorge", "tradeforge")
$allConfigsExist = $true

foreach ($agent in $configAgents) {
    $configPath = "$env:USERPROFILE\openclaw_workspace\agents\$agent\config.json"
    if (Test-Path $configPath) {
        Write-Host "  ✅ $agent : config.json" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $agent : Missing config.json" -ForegroundColor Red
        $allConfigsExist = $false
    }
}
Write-Host ""

# Test 3: Check Shared Memory
Write-Host "Test 3: Checking Shared Memory Structure..." -ForegroundColor Yellow
$sharedDirs = @("data", "signals", "trades", "system")
$allDirsExist = $true

foreach ($dir in $sharedDirs) {
    $dirPath = "$env:USERPROFILE\openclaw_workspace\agents\shared\$dir"
    if (Test-Path $dirPath) {
        Write-Host "  ✅ shared/$dir : Directory exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ shared/$dir : Directory missing" -ForegroundColor Red
        $allDirsExist = $false
    }
}
Write-Host ""

# Test 4: Check Shared Files
Write-Host "Test 4: Checking Shared State Files..." -ForegroundColor Yellow
$sharedFiles = @{
    "data/tqqq_price.json" = "TQQQ Price Data"
    "signals/signal_state.json" = "Signal State"
    "trades/portfolio.json" = "Portfolio State"
    "system/agent_health.json" = "Agent Health"
}

$allFilesValid = $true
foreach ($file in $sharedFiles.Keys) {
    $filePath = "$env:USERPROFILE\openclaw_workspace\agents\shared\$file"
    if (Test-Path $filePath) {
        try {
            $content = Get-Content $filePath | ConvertFrom-Json
            Write-Host "  ✅ $file : Valid JSON" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $file : Invalid JSON" -ForegroundColor Red
            $allFilesValid = $false
        }
    } else {
        Write-Host "  ❌ $file : File missing" -ForegroundColor Red
        $allFilesValid = $false
    }
}
Write-Host ""

# Test 5: Simulate Agent Communication
Write-Host "Test 5: Simulating Agent Communication..." -ForegroundColor Yellow

# Simulate DataForge sending data
Write-Host "  📊 DataForge → SignalForge (DATA_UPDATE)" -ForegroundColor Cyan
$dataUpdate = @{
    header = @{
        version = "1.0"
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss+08:00")
        message_id = [guid]::NewGuid().ToString()
    }
    metadata = @{
        from = "dataforge"
        to = @("signalseorge")
        type = "DATA_UPDATE"
    }
    payload = @{
        symbol = "TQQQ"
        price = 52.34
        zscore = 1.82
        rsi = 68.5
    }
} | ConvertTo-Json -Depth 10

$dataFile = "$env:USERPROFILE\openclaw_workspace\agents\shared\data\test_message.json"
$dataUpdate | Set-Content $dataFile
Write-Host "    ✅ Message written to shared memory" -ForegroundColor Green

# Simulate SignalForge sending signal
Write-Host "  📈 SignalForge → TradeForge (SIGNAL_GENERATED)" -ForegroundColor Cyan
$signal = @{
    header = @{
        version = "1.0"
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss+08:00")
        message_id = [guid]::NewGuid().ToString()
    }
    metadata = @{
        from = "signalseorge"
        to = @("tradeforge")
        type = "SIGNAL_GENERATED"
    }
    payload = @{
        signal_id = "SIG-TEST-001"
        symbol = "TQQQ"
        signal_type = "LONG"
        strength = "STRONG"
        zscore = -1.85
    }
} | ConvertTo-Json -Depth 10

$signalFile = "$env:USERPROFILE\openclaw_workspace\agents\shared\signals\test_message.json"
$signal | Set-Content $signalFile
Write-Host "    ✅ Signal written to shared memory" -ForegroundColor Green

# Simulate TradeForge sending trade
Write-Host "  ⚡ TradeForge → Orchestrator (TRADE_EXECUTED)" -ForegroundColor Cyan
$trade = @{
    header = @{
        version = "1.0"
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss+08:00")
        message_id = [guid]::NewGuid().ToString()
    }
    metadata = @{
        from = "tradeforge"
        to = @("orchestrator")
        type = "TRADE_EXECUTED"
    }
    payload = @{
        trade_id = "TRD-TEST-001"
        symbol = "TQQQ"
        action = "BUY"
        qty = 100
        price = 52.34
        status = "FILLED"
    }
} | ConvertTo-Json -Depth 10

$tradeFile = "$env:USERPROFILE\openclaw_workspace\agents\shared\trades\test_message.json"
$trade | Set-Content $tradeFile
Write-Host "    ✅ Trade written to shared memory" -ForegroundColor Green
Write-Host ""

# Test Summary
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🎯 Test Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$allTestsPassed = $allFilesExist -and $allConfigsExist -and $allDirsExist -and $allFilesValid

if ($allTestsPassed) {
    Write-Host "✅ ALL TESTS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "ClawTeam Multi-Agent System is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Run: .\agents\start_clawteam.ps1" -ForegroundColor White
    Write-Host "  2. Monitor: openclaw subagents list" -ForegroundColor White
    Write-Host "  3. Test: Send messages between agents" -ForegroundColor White
} else {
    Write-Host "❌ SOME TESTS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the errors above and fix them." -ForegroundColor Red
}
Write-Host ""

# Cleanup test files
Remove-Item $dataFile -ErrorAction SilentlyContinue
Remove-Item $signalFile -ErrorAction SilentlyContinue
Remove-Item $tradeFile -ErrorAction SilentlyContinue
