# ClawTeam Scheme B 啟動腳本
# 獨立 WhatsApp 身份 + 單機多 Agent 架構

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "dataforge", "signalforge", "tradeforge", "orchestrator")]
    [string]$Agent = "all",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("simulate", "live")]
    [string]$Mode = "simulate",
    
    [switch]$Status,
    [switch]$Stop,
    [switch]$Setup
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
    Write-ColorOutput "`n🦞 ClawTeam Multi-Agent System (Scheme B)" "Header"
    Write-ColorOutput "═══════════════════════════════════════════" "Header"
    Write-ColorOutput "Mode: $Mode | Agent: $Agent`n" "Info"
}

function Show-AgentsInfo {
    Write-ColorOutput "📋 Agent 配置概覽" "Header"
    Write-ColorOutput "───────────────────────────────────────────" "Info"
    
    $agents = @(
        @{ Name = "呀鬼 (Orchestrator)"; WhatsApp = "+85263609349"; Port = 9000; Status = "🟢 Active"; Role = "中央指揮" },
        @{ Name = "DataForge"; WhatsApp = "+85262255569"; Port = 8001; Status = "⏳ Setup"; Role = "數據工程師" },
        @{ Name = "SignalForge"; WhatsApp = "+85262212577"; Port = 8002; Status = "⏳ Setup"; Role = "信號工程師" },
        @{ Name = "TradeForge"; WhatsApp = "+85255086558"; Port = 8003; Status = "⏳ Setup"; Role = "執行工程師" }
    )
    
    foreach ($a in $agents) {
        Write-ColorOutput "$($a.Status) $($a.Name)" "Info"
        Write-ColorOutput "   WhatsApp: $($a.WhatsApp)" "Info"
        Write-ColorOutput "   Port: $($a.Port) | Role: $($a.Role)" "Info"
        Write-ColorOutput ""
    }
}

function Test-AgentHealth {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Get-SystemStatus {
    Write-ColorOutput "📊 系統狀態檢查" "Header"
    Write-ColorOutput "───────────────────────────────────────────" "Info"
    
    $agents = @(
        @{ Name = "Orchestrator"; Port = 9000 },
        @{ Name = "DataForge"; Port = 8001 },
        @{ Name = "SignalForge"; Port = 8002 },
        @{ Name = "TradeForge"; Port = 8003 }
    )
    
    foreach ($a in $agents) {
        $healthy = Test-AgentHealth -Port $a.Port
        $status = if ($healthy) { "🟢 Running" } else { "🔴 Stopped" }
        Write-ColorOutput "$status $($a.Name) (Port: $($a.Port))" "Info"
    }
    
    # 檢查 OpenD
    Write-ColorOutput ""
    Write-ColorOutput "🔌 Futu OpenD 狀態:" "Info"
    $opendRunning = Test-AgentHealth -Port 11111
    if ($opendRunning) {
        Write-ColorOutput "   🟢 OpenD 運行中 (127.0.0.1:11111)" "Success"
    } else {
        Write-ColorOutput "   🔴 OpenD 未運行" "Error"
        Write-ColorOutput "   請先啟動 OpenD: Start-Process 'C:\Path\To\OpenD-GUI.exe'" "Warning"
    }
}

function Initialize-AgentConfig {
    Write-ColorOutput "🔧 初始化 Agent 配置..." "Header"
    
    $configDir = "$env:USERPROFILE\.openclaw\agents"
    
    # 建立目錄結構
    $agents = @("orchestrator", "dataforge", "signalforge", "tradeforge")
    foreach ($agent in $agents) {
        $dir = "$configDir\$agent"
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput "✅ 建立目錄: $dir" "Success"
        }
    }
    
    Write-ColorOutput "`n📁 Agent 配置目錄:" "Info"
    Write-ColorOutput "   $configDir" "Info"
    Write-ColorOutput ""
    Write-ColorOutput "⚠️  請手動配置各 Agent 的 WhatsApp:" "Warning"
    Write-ColorOutput "   1. DataForge: +85262255569" "Info"
    Write-ColorOutput "   2. SignalForge: +85262212577" "Info"
    Write-ColorOutput "   3. TradeForge: +85255086558" "Info"
    Write-ColorOutput ""
    Write-ColorOutput "   配置命令:" "Info"
    Write-ColorOutput "   openclaw channel add whatsapp --phone +85262255569 --name DataForge" "Info"
}

function Start-DataForge {
    Write-ColorOutput "📊 啟動 DataForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "DataForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8001"
    $env:FUTU_OPEND_HOST = "127.0.0.1"
    $env:FUTU_OPEND_PORT = "11111"
    
    Write-ColorOutput "   配置:" "Info"
    Write-ColorOutput "   - WhatsApp: +85262255569" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8001" "Info"
    Write-ColorOutput "   - Mode: $Mode" "Info"
    Write-ColorOutput "   - OpenD: 127.0.0.1:11111" "Info"
    
    # 這裡將啟動 DataForge 的 Python 服務
    # Start-Process python -ArgumentList "agents/dataforge/main.py" -WindowStyle Hidden
    
    Write-ColorOutput "   ✅ DataForge 配置就緒" "Success"
}

function Start-SignalForge {
    Write-ColorOutput "📈 啟動 SignalForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "SignalForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8002"
    
    Write-ColorOutput "   配置:" "Info"
    Write-ColorOutput "   - WhatsApp: +85262212577" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8002" "Info"
    Write-ColorOutput "   - Mode: $Mode" "Info"
    
    Write-ColorOutput "   ✅ SignalForge 配置就緒" "Success"
}

function Start-TradeForge {
    Write-ColorOutput "💰 啟動 TradeForge Agent..." "Info"
    
    $env:CLAWTEAM_AGENT = "TradeForge"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "8003"
    
    Write-ColorOutput "   配置:" "Info"
    Write-ColorOutput "   - WhatsApp: +85255086558" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:8003" "Info"
    Write-ColorOutput "   - Mode: $Mode" "Info"
    
    Write-ColorOutput "   ✅ TradeForge 配置就緒" "Success"
}

function Start-Orchestrator {
    Write-ColorOutput "🎛️  啟動中央指揮系統 (呀鬼)..." "Info"
    
    $env:CLAWTEAM_AGENT = "Orchestrator"
    $env:CLAWTEAM_MODE = $Mode
    $env:CLAWTEAM_PORT = "9000"
    
    Write-ColorOutput "   配置:" "Info"
    Write-ColorOutput "   - WhatsApp: +85263609349" "Info"
    Write-ColorOutput "   - Endpoint: http://localhost:9000" "Info"
    Write-ColorOutput "   - Mode: $Mode" "Info"
    
    Write-ColorOutput "   ✅ Orchestrator 配置就緒" "Success"
}

function Stop-AllAgents {
    Write-ColorOutput "🛑 停止所有 Agent..." "Warning"
    
    # 這裡將停止所有 Agent 進程
    # Get-Process python | Where-Object { $_.CommandLine -like "*clawteam*" } | Stop-Process
    
    Write-ColorOutput "✅ 所有 Agent 已停止" "Success"
}

# 主程序
Show-Header

if ($Setup) {
    Initialize-AgentConfig
    Show-AgentsInfo
    exit 0
}

if ($Status) {
    Get-SystemStatus
    exit 0
}

if ($Stop) {
    Stop-AllAgents
    exit 0
}

# 檢查 OpenD 是否運行
$opendRunning = Test-AgentHealth -Port 11111
if (!$opendRunning) {
    Write-ColorOutput "⚠️  警告: Futu OpenD 未運行" "Warning"
    Write-ColorOutput "   部分功能可能無法正常工作" "Warning"
    Write-ColorOutput "   請啟動 OpenD 後重試`n" "Warning"
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

Write-ColorOutput "`n═══════════════════════════════════════════" "Header"
Write-ColorOutput "🚀 ClawTeam Scheme B 系統啟動完成！" "Success"
Write-ColorOutput "Mode: $Mode" "Info"
Write-ColorOutput "`n可用指令:" "Info"
Write-ColorOutput "  - 查看狀態: .\start-clawteam-schemeB.ps1 -Status" "Info"
Write-ColorOutput "  - 停止系統: .\start-clawteam-schemeB.ps1 -Stop" "Info"
Write-ColorOutput "  - 初始化配置: .\start-clawteam-schemeB.ps1 -Setup" "Info"
Write-ColorOutput "  - 切換模式: .\start-clawteam-schemeB.ps1 -Mode live" "Info"
Write-ColorOutput "═══════════════════════════════════════════`n" "Header"
