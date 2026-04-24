# AGENTS.md - ClawTeam Agent Registry

## Team Overview
**ClawTeam** - Multi-Agent Trading System for TQQQ Z-Score Mean Reversion Strategy

## Agent Registry

### 1. Orchestrator - Alfred (呀鬼)
```yaml
id: main
name: Alfred
role: Central Orchestrator
phone: +852-63609349
parent: null
children:
  - dataforge
  - signalseorge
  - tradeforge
skills:
  - self-improving-agent
  - parallel
  - capability-evolver
  - webhook
  - monitoring
  - logging-observability
  - dashboard
  - reporting
```

### 2. DataForge - Robin
```yaml
id: dataforge
name: Robin DataForge
role: Data Acquisition & Processing
phone: +852-62255569
parent: main
upstream: []
downstream:
  - signalseorge
skills:
  - futu
  - data-analysis
  - stock-monitor
  - stock-study
  - spreadsheet
  - microsoft-excel
  - excel-xlsx
```

### 3. SignalForge - BatGirl
```yaml
id: signalseorge
name: BatGirl SignalForge
role: Signal Generation & Strategy
phone: +852-62212577
parent: main
upstream:
  - dataforge
downstream:
  - tradeforge
skills:
  - trading
  - stock-strategy-backtester
  - stock-study
  - super-search
  - last30days-official
```

### 4. TradeForge - Catwoman
```yaml
id: tradeforge
name: Catwoman TradeForge
role: Trade Execution & Risk Management
phone: +852-55086558
parent: main
upstream:
  - signalseorge
downstream: []
skills:
  - trading
  - dashboard
  - monitoring
  - reporting
  - webhook
  - safe-exec
  - logging-observability
  - red-alert
```

## Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Alfred (Orchestrator)                     │
│                      +852-63609349                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Command & Control
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  DataForge   │ │ SignalForge  │ │  TradeForge  │
│   (Data)     │ │  (Signal)    │ │  (Execute)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │  DATA_UPDATE   │ SIGNAL_GENERATED│
       └───────────────▶│───────────────▶│
                        │                │
                        │   TRADE_EXEC   │
                        └───────────────▶│
```

## Message Types

### 1. DATA_UPDATE
```json
{
  "type": "DATA_UPDATE",
  "from": "dataforge",
  "to": ["signalseorge", "orchestrator"],
  "payload": {
    "symbol": "TQQQ",
    "price": 52.34,
    "zscore": 1.82,
    "rsi": 68.5,
    "timestamp": "2026-04-04T10:30:00+08:00"
  }
}
```

### 2. SIGNAL_GENERATED
```json
{
  "type": "SIGNAL_GENERATED",
  "from": "signalseorge",
  "to": ["tradeforge", "orchestrator"],
  "payload": {
    "signal_id": "SIG-20260404-001",
    "symbol": "TQQQ",
    "signal_type": "LONG",
    "strength": "STRONG",
    "zscore": -1.85,
    "rsi": 28.5
  }
}
```

### 3. TRADE_EXECUTED
```json
{
  "type": "TRADE_EXECUTED",
  "from": "tradeforge",
  "to": ["orchestrator"],
  "payload": {
    "trade_id": "TRD-20260404-001",
    "symbol": "TQQQ",
    "action": "BUY",
    "qty": 100,
    "price": 52.34,
    "status": "FILLED"
  }
}
```

### 4. SYSTEM_ALERT
```json
{
  "type": "SYSTEM_ALERT",
  "from": "any",
  "to": ["orchestrator"],
  "payload": {
    "level": "WARN|ERROR|CRITICAL",
    "message": "Alert description",
    "agent": "agent_id"
  }
}
```

## Startup Sequence

1. **Orchestrator** (呀鬼) - 首先啟動
2. **DataForge** - 啟動數據服務
3. **SignalForge** - 等待 DataForge 就緒後啟動
4. **TradeForge** - 等待 SignalForge 就緒後啟動

## Health Check

```bash
# Check all agents
openclaw subagents list

# Check specific agent
openclaw subagents status dataforge
```
