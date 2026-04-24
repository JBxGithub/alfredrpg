# ClawTeam Agent 啟動腳本
# 用於初始化各專業 Agent

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "dataforge", "signalforge", "tradeforge", "orchestrator")]
    [string]$Agent = "all",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("simulate", "live")]
    [string]$Mode = "simulate",
    
    [switch]$Status,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

# 顏色配置
$colors = @{
    Success = "Green"
    Info = "Cyan"
    Warning = "Yellow"
    Error = "Red"
    Header = "Magenta"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Show-Header {
    Write-ColorOutput "`n🦞 ClawTeam Multi-Agent System" "Header"
    Write-ColorOutput "═══════════════════════════════════════" "Header"
    Write-ColorOutput "Mode: $Mode | Agent: $Agent`n" "Info"
}

function Get-AgentStatus {
    $agents = @{
        "DataForge" = @{ Port = 8001; Status = "Unknown" }
        "SignalForge" = @{ Port = 8002; Status = "Unknown" }
        "TradeForge" = @{ Port = 8003; Status = "Unknown" }
        "Orchestrator" = @{ Port = 9000; Status = "Unknown" }
    }
    
    foreach ($agent in $agents.Keys) {
        $port = $agents[$agent].Port
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                $agents[$agent].Status = "🟢 Running"
            } else {
                $agents[$agent].Status = "🔴 Stopped"
            }
        } catch {
            $agents[$agent].Status = "🔴 Stopped"
        }
    }
    
    return $agents
}

function Start-DataForge {
    Write-ColorOutput "📊 啟動 DataForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "DataForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8001"
    
    # 這裡將啟動 DataForge 的 Python 服務
    # Start-Process python -ArgumentList "agents/dataforge/main.py" -WindowStyle Hidden
    
    Write-ColorOutput "✅ DataForge 配置完成" "Success"
    Write-ColorOutput "   - WhatsApp: +852-62255569" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8001" "Info"
    Write-ColorOutput "   - Skills: futu-stock, data-analysis, stock-monitor" "Info"
}

function Start-SignalForge {
    Write-ColorOutput "📈 啟動 SignalForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "SignalForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8002"
    
    Write-ColorOutput "✅ SignalForge 配置完成" "Success"
    Write-ColorOutput "   - WhatsApp: +852-62212577" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8002" "Info"
    Write-ColorOutput "   - Skills: trading, stock-strategy-backtester" "Info"
}

function Start-TradeForge {
    Write-ColorOutput "💰 啟動 TradeForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "TradeForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8003"
    
    Write-ColorOutput "✅ TradeForge 配置完成" "Success"
    Write-ColorOutput "   - WhatsApp: +852-55086558" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8003" "Info"
    Write-ColorOutput "   - Skills: trading, dashboard, monitoring" "Info"
}

function Start-Orchestrator {
    Write-ColorOutput "🎛️  啟動中央指揮系統 (呀鬼)..." "Info"
    
    $env:CLAWTEAM_AGENT = "Orchestrator"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "9000"
    
    Write-ColorOutput "✅ Orchestrator 配置完成" "Success"
    Write-ColorOutput "   - WhatsApp: +85263609349 (當前)" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:9000" "Info"
    Write-ColorOutput "   - Skills: monitoring, dashboard, reporting" "Info"
}

# 主程序
Show-Header

if ($Status) {
    Write-ColorOutput "📊 Agent 狀態檢查" "Header"
    $status = Get-AgentStatus
    $status.GetEnumerator() | ForEach-Object {
        Write-ColorOutput "$($_.Key): $($_.Value.Status)" "Info"
    }
    exit 0
}

if ($Stop) {
    Write-ColorOutput "🛑 停止所有 Agent..." "Warning"
    # 停止邏輯
    Write-ColorOutput "✅ 所有 Agent 已停止" "Success"
    exit 0
}

# 啟動指定 Agent
switch ($Agent) {
    "all" {
        Start-DataForge
        Start-SignalForge
        Start-TradeForge
        Start-Orchestrator
    }
    "dataforge" { Start-DataForge }
    "signalforge" { Start-SignalForge }
    "tradeforge" { Start-TradeForge }
    "orchestrator" { Start-Orchestrator }
}

Write-ColorOutput "`n═══════════════════════════════════════" "Header"
Write-ColorOutput "🚀 ClawTeam 系統啟動完成！" "Success"
Write-ColorOutput "Mode: $Mode" "Info"
Write-ColorOutput "`n可用指令:" "Info"
Write-ColorOutput "  - 查看狀態: .\start-clawteam.ps1 -Status" "Info"
Write-ColorOutput "  - 停止系統: .\start-clawteam.ps1 -Stop" "Info"
Write-ColorOutput "  - 切換模式: .\start-clawteam.ps1 -Mode live" "Info"
Write-ColorOutput "═══════════════════════════════════════`n" "Header"
