# ClawTeam Communication Protocol

## Overview
This document defines the communication protocol between ClawTeam agents.

## Communication Methods

### 1. Sessions Send (Primary)
Direct message passing between agents using OpenClaw's `sessions_send` tool.

```python
# Example: DataForge sending data to SignalForge
sessions_send(
    sessionKey="agent:signalseorge",
    message=json.dumps({
        "type": "DATA_UPDATE",
        "payload": data
    })
)
```

### 2. Shared Memory (Secondary)
File-based shared state for persistent data.

**Directory Structure:**
```
~/openclaw_workspace/agents/shared/
├── data/
│   ├── tqqq_price.json
│   ├── indicators.json
│   └── market_state.json
├── signals/
│   ├── latest_signal.json
│   └── signal_history.json
├── trades/
│   ├── open_positions.json
│   └── trade_history.json
└── system/
    ├── agent_health.json
    └── system_status.json
```

### 3. Webhook (Alerts)
For critical alerts and external notifications.

## Message Format

### Standard Message Structure
```json
{
  "header": {
    "version": "1.0",
    "timestamp": "2026-04-04T10:30:00+08:00",
    "message_id": "uuid",
    "correlation_id": "uuid"
  },
  "metadata": {
    "from": "agent_id",
    "to": ["agent_id"],
    "type": "MESSAGE_TYPE",
    "priority": "HIGH|MEDIUM|LOW"
  },
  "payload": {
    // Message-specific data
  }
}
```

## Message Types

### DATA_UPDATE
Sent by: DataForge
Received by: SignalForge, Orchestrator

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "dataforge", "to": ["signalseorge"], "type": "DATA_UPDATE" },
  "payload": {
    "symbol": "TQQQ",
    "price": 52.34,
    "change": 1.23,
    "change_percent": 2.41,
    "volume": 12345678,
    "indicators": {
      "zscore": 1.82,
      "rsi": 68.5,
      "macd": 0.45,
      "volume_ma20": 15000000
    },
    "timestamp": "2026-04-04T10:30:00+08:00"
  }
}
```

### SIGNAL_GENERATED
Sent by: SignalForge
Received by: TradeForge, Orchestrator

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "signalseorge", "to": ["tradeforge"], "type": "SIGNAL_GENERATED" },
  "payload": {
    "signal_id": "SIG-20260404-001",
    "symbol": "TQQQ",
    "signal_type": "LONG",
    "strength": "STRONG",
    "entry_price": 52.34,
    "indicators": {
      "zscore": -1.85,
      "rsi": 28.5,
      "confirmation": {
        "trend_filter": "PASS",
        "volatility": "NORMAL",
        "volume": "ADEQUATE"
      }
    },
    "strategy": "ZScore Mean Reversion",
    "timestamp": "2026-04-04T10:30:00+08:00"
  }
}
```

### TRADE_EXECUTED
Sent by: TradeForge
Received by: Orchestrator

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "tradeforge", "to": ["orchestrator"], "type": "TRADE_EXECUTED" },
  "payload": {
    "trade_id": "TRD-20260404-001",
    "signal_id": "SIG-20260404-001",
    "symbol": "TQQQ",
    "action": "BUY",
    "qty": 100,
    "price": 52.34,
    "total_value": 5234.00,
    "fees": 5.23,
    "status": "FILLED",
    "pnl": null,
    "timestamp": "2026-04-04T10:30:05+08:00"
  }
}
```

### POSITION_UPDATED
Sent by: TradeForge
Received by: Orchestrator

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "tradeforge", "to": ["orchestrator"], "type": "POSITION_UPDATED" },
  "payload": {
    "position_id": "POS-20260404-001",
    "symbol": "TQQQ",
    "side": "LONG",
    "qty": 100,
    "avg_price": 52.34,
    "current_price": 53.00,
    "unrealized_pnl": 66.00,
    "unrealized_pnl_percent": 1.26,
    "entry_time": "2026-04-04T10:30:05+08:00",
    "exit_conditions": {
      "take_profit": 54.96,
      "stop_loss": 50.77,
      "time_stop": "2026-04-07T10:30:05+08:00"
    }
  }
}
```

### SYSTEM_ALERT
Sent by: Any Agent
Received by: Orchestrator

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "agent_id", "to": ["orchestrator"], "type": "SYSTEM_ALERT", "priority": "HIGH" },
  "payload": {
    "level": "INFO|WARN|ERROR|CRITICAL",
    "category": "DATA|STRATEGY|EXECUTION|SYSTEM",
    "message": "Alert description",
    "details": {},
    "suggested_action": "Action to take"
  }
}
```

### COMMAND
Sent by: Orchestrator
Received by: Any Agent

```json
{
  "header": { "version": "1.0", "timestamp": "...", "message_id": "..." },
  "metadata": { "from": "orchestrator", "to": ["agent_id"], "type": "COMMAND" },
  "payload": {
    "command": "START|STOP|PAUSE|RESUME|STATUS|CONFIG",
    "parameters": {},
    "timeout_seconds": 30
  }
}
```

## Communication Flow

### 1. Data Collection Flow
```
DataForge → Shared Memory → SignalForge
         ↓
    Orchestrator (monitor)
```

### 2. Signal Generation Flow
```
SignalForge → Shared Memory → TradeForge
           ↓
      Orchestrator (approval)
```

### 3. Trade Execution Flow
```
TradeForge → Shared Memory → Orchestrator
          ↓
     Dashboard Update
```

### 4. Alert Flow
```
Any Agent → Webhook/Sessions → Orchestrator
         ↓
    WhatsApp Group (if critical)
```

## Error Handling

### Retry Policy
- **Max Retries**: 3
- **Backoff**: Exponential (1s, 2s, 4s)
- **Timeout**: 30 seconds per attempt

### Dead Letter Queue
Failed messages are stored in:
`~/openclaw_workspace/agents/shared/system/dead_letter.json`

## Health Monitoring

### Heartbeat
Each agent sends heartbeat every 60 seconds:
```json
{
  "type": "HEARTBEAT",
  "agent": "agent_id",
  "status": "HEALTHY|DEGRADED|UNHEALTHY",
  "timestamp": "..."
}
```

### Health Check Response
```json
{
  "type": "HEALTH_CHECK_RESPONSE",
  "agent": "agent_id",
  "status": "HEALTHY",
  "metrics": {
    "cpu_percent": 15.2,
    "memory_mb": 256,
    "uptime_seconds": 3600,
    "messages_processed": 150
  }
}
```
