# ClawTeam 設定指南
# 為各 Agent 配置 WhatsApp 身份與權限

## 🎯 設定流程概述

由於 OpenClaw 目前只綁定了一個 WhatsApp 號碼 (+85263609349)，要實現真正的多 Agent 架構，有以下幾種方案：

---

## 方案 A: 虛擬 Agent 身份 (推薦 - 現階段)

**概念**: 所有 Agent 共享同一個 WhatsApp 號碼，但通過消息前綴區分身份

### 實現方式

1. **消息格式標準化**:
```
[DataForge] 📊 TQQQ 數據更新: $52.34, Z-Score: -1.65
[SignalForge] 📈 生成 BUY 信號 (信心度: 85%)
[TradeForge] 💰 執行買入 100股 @ $52.34
```

2. **指令識別**:
```
@DataForge 獲取 TQQQ 數據
@SignalForge 分析市場狀態
@TradeForge 查詢持倉
```

3. **優點**:
   - 無需額外 WhatsApp 號碼
   - 立即可用
   - 成本低

4. **缺點**:
   - 所有消息來自同一號碼
   - 需要手動標記身份

---

## 方案 B: 多 WhatsApp 號碼 (完整實現)

**概念**: 為每個 Agent 配置獨立 WhatsApp 號碼

### 需要的資源

| Agent | 建議號碼類型 | 成本估算 |
|-------|-------------|---------|
| DataForge | +852-62255569 | 現有 |
| SignalForge | +852-62212577 | 現有 |
| TradeForge | +852-55086558 | 現有 |

### 設定步驟

1. **準備設備**:
   - 每個 WhatsApp 號碼需要獨立設備或虛擬機
   - 或使用 WhatsApp Business API (需 Meta 批准)

2. **OpenClaw 多賬號配置**:
```json
{
  "channels": {
    "whatsapp": {
      "accounts": [
        {
          "id": "default",
          "phone": "+85263609349",
          "role": "orchestrator"
        },
        {
          "id": "dataforge",
          "phone": "+85262255569",
          "role": "data"
        },
        {
          "id": "signalforge",
          "phone": "+85262212577",
          "role": "signal"
        },
        {
          "id": "tradeforge",
          "phone": "+85255086558",
          "role": "trade"
        }
      ]
    }
  }
}
```

3. **啟動多 Gateway 實例**:
   - 每個 Agent 需要獨立的 OpenClaw Gateway
   - 或使用單一 Gateway 的多賬號支持

---

## 方案 C: Webhook 為主，WhatsApp 為輔 (技術優先)

**概念**: Agent 間主要通過 Webhook/HTTP 通訊，WhatsApp 僅用於人工監督

### 架構

```
┌─────────────────────────────────────────────────────────────┐
│                     ClawTeam 網絡                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  DataForge   │  │ SignalForge  │  │  TradeForge  │       │
│  │  :8001       │◄─┤  :8002       │◄─┤  :8003       │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ▼                                 │
│                  ┌────────────────┐                         │
│                  │  Orchestrator  │                         │
│                  │  :9000         │                         │
│                  └───────┬────────┘                         │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  WhatsApp (監督層)    │
              │  +85263609349        │
              └──────────────────────┘
```

### 通訊流程

1. **Agent 間**: HTTP/WebSocket (實時、自動化)
2. **人工監督**: WhatsApp (重要事件通知)

### 優點
- 技術上最簡潔
- Agent 間通訊延遲低
- 易於擴展

---

## 🚀 推薦實施路線

### Phase 1 (現在): 方案 A + C 混合
- 使用虛擬 Agent 身份標記
- Agent 間通過本地 HTTP 通訊
- WhatsApp 僅用於重要通知

### Phase 2 (未來): 方案 B
- 為每個 Agent 配置獨立 WhatsApp
- 實現真正的分佈式架構

---

## 📋 立即執行項目

### 1. 建立虛擬 Agent 識別系統

在 `clawteam_protocol.py` 中添加：

```python
class AgentIdentity:
    """Agent 身份管理"""
    
    IDENTITIES = {
        "dataforge": {
            "name": "DataForge",
            "emoji": "📊",
            "color": "\033[94m",  # Blue
            "whatsapp": "+85262255569"
        },
        "signalforge": {
            "name": "SignalForge", 
            "emoji": "📈",
            "color": "\033[92m",  # Green
            "whatsapp": "+85262212577"
        },
        "tradeforge": {
            "name": "TradeForge",
            "emoji": "💰",
            "color": "\033[93m",  # Yellow
            "whatsapp": "+85255086558"
        },
        "orchestrator": {
            "name": "Alfred",
            "emoji": "🎛️",
            "color": "\033[95m",  # Magenta
            "whatsapp": "+85263609349"
        }
    }
    
    @classmethod
    def format_message(cls, agent_id: str, message: str) -> str:
        identity = cls.IDENTITIES.get(agent_id, {})
        emoji = identity.get("emoji", "🤖")
        name = identity.get("name", agent_id)
        return f"[{emoji} {name}] {message}"
```

### 2. 配置 Webhook 接收器

```python
# webhook_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/clawteam', methods=['POST'])
def handle_clawteam_webhook():
    data = request.json
    agent_id = data.get('agent')
    message = data.get('message')
    
    # 轉發到 WhatsApp
    send_whatsapp_message(f"[{agent_id}] {message}")
    
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(port=5000)
```

### 3. 測試通訊

```powershell
# 發送測試消息
curl -X POST http://localhost:5000/webhook/clawteam `
  -H "Content-Type: application/json" `
  -d '{"agent": "DataForge", "message": "TQQQ 數據更新: $52.34"}'
```

---

## ❓ 需要主人決定的事項

1. **WhatsApp 號碼**:
   - +852-62255569, +852-62212577, +852-55086558 是否可用於 Agent？
   - 是否需要購買新的虛擬號碼？

2. **運行模式**:
   - 先使用虛擬身份 (方案 A)？
   - 還是直接配置多號碼 (方案 B)？

3. **部署環境**:
   - 所有 Agent 在同一台機器運行？
   - 還是分散到不同設備？

---

*等待主人指示後繼續配置*
