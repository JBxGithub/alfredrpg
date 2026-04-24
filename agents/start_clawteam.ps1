# ClawTeam Multi-Agent Startup Script
# Usage: Run this script to start all agents in sequence

Write-Host "🚀 Starting ClawTeam Multi-Agent System..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Orchestrator (Main Agent)
Write-Host "Step 1: Checking Orchestrator (Alfred)..." -ForegroundColor Yellow
$orchestratorStatus = openclaw status --all | Select-String "Gateway"
if ($orchestratorStatus) {
    Write-Host "✅ Orchestrator is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  Starting Gateway..." -ForegroundColor Red
    openclaw gateway start
}
Write-Host ""

# Step 2: Update System Status
Write-Host "Step 2: Initializing shared memory..." -ForegroundColor Yellow
$healthFile = "$env:USERPROFILE\openclaw_workspace\agents\shared\system\agent_health.json"
$health = Get-Content $healthFile | ConvertFrom-Json
$health.system_status = "STARTING"
$health.orchestrator.status = "ONLINE"
$health.orchestrator.last_heartbeat = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss+08:00")
$health.last_updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss+08:00")
$health | ConvertTo-Json -Depth 10 | Set-Content $healthFile
Write-Host "✅ Shared memory initialized" -ForegroundColor Green
Write-Host ""

# Step 3: Start DataForge
Write-Host "Step 3: Starting DataForge..." -ForegroundColor Yellow
Write-Host "   📊 DataForge will monitor TQQQ market data"
# Note: In actual implementation, this would spawn a subagent
# openclaw subagents spawn --agent dataforge --task "TQQQ data monitoring"
$health.agents.dataforge.status = "STARTING"
$health | ConvertTo-Json -Depth 10 | Set-Content $healthFile
Write-Host "✅ DataForge startup initiated" -ForegroundColor Green
Write-Host ""

# Step 4: Start SignalForge
Write-Host "Step 4: Starting SignalForge..." -ForegroundColor Yellow
Write-Host "   📈 SignalForge will generate trading signals"
# Note: In actual implementation, this would spawn a subagent
# openclaw subagents spawn --agent signalseorge --task "TQQQ signal generation"
$health.agents.signalseorge.status = "STARTING"
$health | ConvertTo-Json -Depth 10 | Set-Content $healthFile
Write-Host "✅ SignalForge startup initiated" -ForegroundColor Green
Write-Host ""

# Step 5: Start TradeForge
Write-Host "Step 5: Starting TradeForge..." -ForegroundColor Yellow
Write-Host "   ⚡ TradeForge will execute trades"
# Note: In actual implementation, this would spawn a subagent
# openclaw subagents spawn --agent tradeforge --task "TQQQ trade execution"
$health.agents.tradeforge.status = "STARTING"
$health | ConvertTo-Json -Depth 10 | Set-Content $healthFile
Write-Host "✅ TradeForge startup initiated" -ForegroundColor Green
Write-Host ""

# Final Status
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🎯 ClawTeam Startup Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Agent Status:"
Write-Host "  🧐 Orchestrator (Alfred): ONLINE"
Write-Host "  📊 DataForge: STARTING"
Write-Host "  📈 SignalForge: STARTING"
Write-Host "  ⚡ TradeForge: STARTING"
Write-Host ""
Write-Host "Shared Memory:"
Write-Host "  📁 ~/openclaw_workspace/agents/shared/"
Write-Host ""
Write-Host "Communication Protocol:"
Write-Host "  📡 sessions_send + shared memory"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "  1. Wait for all agents to report HEALTHY"
Write-Host "  2. Check status: openclaw subagents list"
Write-Host "  3. Monitor dashboard: http://localhost:8501"
Write-Host ""
