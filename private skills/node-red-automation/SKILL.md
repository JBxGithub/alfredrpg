---
name: node-red-automation
description: Node-RED Workflow Automation - HTTP API client, flow management, event monitoring, webhook handling
version: 1.0.1
author: 呀鬼 (Alfred)
private: true
---

# Node-RED Automation Skill

> Node-RED Workflow 自動化技能 for OpenClaw
> 創建時間: 2026-04-19
> 最後更新: 2026-04-19
> 負責人: 呀鬼 (Alfred)
> 狀態: ✅ 已驗證可用

---

## 概述

本 Skill 提供 Node-RED 完整自動化能力：
1. **HTTP API Client** - Node-RED Admin API 包裝器
2. **Flow Manager** - Flow 導入/導出/部署/版本控制
3. **Event Monitor** - 事件監控和 webhook 處理
4. **Integration** - 與 OpenClaw 生態整合

---

## ⚡ 快速開始 (已驗證)

### 1. 確保 Node-RED 運行中
```bash
# 檢查是否運行
curl http://localhost:1880/flows

# 如未運行，啟動它
node-red
```

### 2. 基本使用
```python
import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/node-red-automation')
from client import NodeREDClient

# 連接 Node-RED
client = NodeREDClient('localhost', 1880)

# 檢查狀態
print(f"運行中: {client.is_running()}")  # True

# 獲取 flows
flows = client.get_flows()
print(f"Flows 數量: {len(flows)}")

# 獲取節點
nodes = client.get_nodes()
print(f"節點數量: {len(nodes)}")

# 獲取設置
settings = client.get_settings()
print(f"版本: {settings.get('version')}")
```

### 3. 可用 API 路徑 (已測試)
| 路徑 | 狀態 | 用途 |
|------|------|------|
| `/` | ✅ | 主頁 |
| `/flows` | ✅ | 獲取/設置所有 flows |
| `/nodes` | ✅ | 獲取已安裝節點 |
| `/settings` | ✅ | 獲取運行時設置 |
| `/flow/{id}` | ✅ | 獲取/設置特定 flow |

### 4. 不可用路徑
| 路徑 | 狀態 | 備註 |
|------|------|------|
| `/info` | ❌ | 使用 `/settings` 替代 |
| `/status` | ❌ | 使用 `/flows` 替代 |
| `/debug` | ❌ | 未啟用 |
| `/auth/*` | ❌ | 未設置認證 |
| `/library/*` | ❌ | 未啟用 |

## 安裝

### Node-RED 安裝

```bash
# via npm
npm install -g node-red

# or via npx
npx node-red
```

### Python 依賴

```bash
pip install requests
```

### 啟動 Node-RED

```bash
node-red
# 訪問 http://localhost:1880
```

## 使用方法

### 1. Node-RED Client - API 調用

```python
from node_red_automation import get_client

# 初始化客戶端
client = get_client(host="localhost", port=1880)

# 檢查運行狀態
print(f"Node-RED 運行中: {client.is_running()}")

# 獲取所有 flows
flows = client.get_flows()
print(f"Flows 數量: {len(flows)}")

# 獲取節點信息
info = client.get_info()
print(f"版本: {info.get('version')}")

# 獲取所有已安裝節點
nodes = client.get_nodes()
```

### 2. Flow Manager - Flow 管理

```python
from node_red_automation import get_flow_manager

# 初始化 flow 管理器
fm = get_flow_manager(host="localhost", port=1880)

# 導出所有 flows 到文件
path = fm.export_to_file("my_flows.json")
print(f"導出到: {path}")

# 導出自定義文件
fm.import_from_file("template.json")

# 創建備份
backup_path = fm.backup(tag="before-change")

# 列出所有備份
backups = fm.list_backups()
for b in backups:
    print(f"{b['created']}: {b['name']}")

# 從備份恢復
fm.restore("backup_20260419_120000.json")

# 驗證 flows
validation = fm.validate_flows()
print(f"Valid: {validation['valid']}")

# 獲取 flows 使用的節點類型
node_types = fm.get_node_types()
print(f"節點類型: {node_types}")
```

### 3. Event Monitor - 事件監控

```python
from node_red_automation import EventMonitor

# 初始化事件監控
monitor = EventMonitor(host="localhost", port=1880)

# 註冊事件處理器
def handle_debug(msg):
    print(f"Debug: {msg}")

def handle_error(msg):
    print(f"Error: {msg}")

monitor.on("message", handle_debug)
monitor.on("error", handle_error)

# 開始監控
monitor.start_monitoring()

# 獲取事件
event = monitor.get_event(timeout=5)
print(event)

# 停止監控
monitor.stop_monitoring()

# 列出最近事件
events = monitor.list_events(limit=20)
print(f"最近事件: {len(events)}")

# 獲取事件摘要
summary = monitor.get_event_summary()
print(f"類型統計: {summary['types']}")
```

### 4. Webhook 處理

```python
from node_red_automation import WebhookServer

# 創建 webhook 服務器
server = WebhookServer(port=1881)

# 註冊 webhook 路由
@server.route("/webhook/github", method="POST")
def handle_github(data):
    event = data.get("event")
    print(f"GitHub event: {event}")
    return {"status": "ok"}

# 處理請求
result = server.handle("POST", "/webhook/github", {"event": "push"})
```

## CLI 使用

```bash
# 查看 Node-RED 狀態
python -m node_red_automation status

# 導出 flows
python -m node_red_automation export -o my_flows.json

# 導入 flows
python -m node_red_automation import -f template.json

# 創建備份
python -m node_red_automation backup

# 查看事件
python -m node_red_automation events --last 20
```

## 配置文件

創建 `config/node_red.yaml`:

```yaml
node_red:
  host: localhost
  port: 1880
  username: null  # 如果設置了認證
  password: null
  timeout: 30

flow_manager:
  storage_dir: ./flows_storage

event_monitor:
  storage_dir: ./events_storage
```

## 架構

```
node-red-automation/
├── __init__.py              # 主入口，導出公共接口
├── client.py                # Node-RED HTTP API 客戶端
├── flow_manager.py          # Flow 管理器
├── event_monitor.py         # 事件監控器
├── config/
│   └── node_red.yaml         # 配置
├── templates/              # Flow 模板
│   ├── weather.json
│   ├── webhook.json
│   ├── scheduler.json
│   └── api_gateway.json
├── examples/               # 示例 flows
│   └── notify.json
├── scripts/                # 輔助腳本
│   ├── backup.py
│   └── monitor.py
└── SKILL.md                # 本文檔
```

## Flow Templates

### 1. 天氣查詢 Flow

```json
[
    {"id": "inject_weather", "type": "inject", "name": "定時獲取天氣", "repeat": "300", ...},
    {"id": "http_weather", "type": "http request", "method": "GET", "url": "https://wttr.in/Hong+Kong?format=j1", ...},
    {"id": "parse_weather", "type": "function", "func": "...", ...},
    {"id": "debug_weather", "type": "debug", ...}
]
```

### 2. Webhook 接收 Flow

```json
[
    {"id": "http_in", "type": "http in", "url": "/webhook", ...},
    {"id": "parse_json", "type": "json", ...},
    {"id": "switch_event", "type": "switch", ...},
    {"id": "debug_webhook", "type": "debug", ...}
]
```

### 3. 定時任務 Flow

```json
[
    {"id": "cron_daily", "type": "inject", "name": "每日執行", "crontab": "0 9 * * *", ...},
    {"id": "http_task", "type": "http request", ...},
    {"id": "log_result", "type": "debug", ...}
]
```

### 4. API 網關 Flow

```json
[
    {"id": "http_api", "type": "http in", "url": "/api/*", "method": "GET", ...},
    {"id": "switch_path", "type": "switch", "property": "url", ...},
    {"id": "function_handler", "type": "function", ...},
    {"id": "http_response", "type": "http response", ...}
]
```

## 與 OpenClaw 生態整合

### 與AMS 整合

```python
from node_red_automation import get_flow_manager
from ams_simple import AMS

# 自動記錄 flow 變更到 AMS
fm = get_flow_manager()

# 導出並記錄
path = fm.export_to_file()
ams = AMS()
ams.log(f"Node-RED flows 已導出: {path}")
```

### 與 AgentHub 整合

```python
from node_red_automation import EventMonitor

# 監控 Node-RED 事件，觸發 AgentHub 任務
monitor = EventMonitor()

def on_node_error(event):
    # 通知 AgentHub
    print(f"Node 錯誤: {event}")
    # 調用 AgentHub 處理

monitor.on("error", on_node_error)
```

### 與 Alfred Browser 整合

```python
import webbrowser
from node_red_automation import get_client

# 打開 Node-RED Editor
client = get_client()
webbrowser.open(f"http://{client.host}:{client.port}")
```

## 常見問題

### Q: Node-RED 無法連接

```bash
# 確保 Node-RED 正在運行
node-red

# 檢查端口
netstat -an | grep 1880
```

### Q: 認證失敗

```bash
# 設置 Node-RED 管理員
# 編輯 ~/.node-red/settings.js
adminAuth: {
    type: "credentials",
    users: [{
        username: "admin",
        password: "password-hash",
        permissions: "*"
    }]
}
```

### Q: Flow 部署失敗

```python
# 驗證 flow 結構
fm = get_flow_manager()
result = fm.validate_flows()
print(result['errors'])
```

## 注意事項

1. **Port 1880** - Node-RED 默認使用 1880
2. **Admin API** - 默認無認證，建議在生產環境配置
3. **Flow 存儲** - flows 保存在 `~/.node-red/flows.json`
4. **安全** - 不要在公開網絡暴露 Node-RED API
5. **版本控制** - 定期備份 flows
6. **n8n 轉換** - 並非所有 n8n 節點都有 Node-RED 對應，需評估可行性

## 更新日誌

| 版本 | 日期 | 更新內容 |
|------|------|---------|
| 1.0.1 | 2026-04-19 | 驗證可用性，修復 API 路徑，添加 n8n 模板參考庫 |
| 1.0.0 | 2026-04-19 | 初始版本，實現 client/flow_manager/event_monitor |

---

## 📚 n8n Workflow 模板參考數據庫

> 當靚仔提出自動化需求時，首先查看以下模板庫，分析是否可轉換為 Node-RED flow

### 🌟 主要模板庫

#### 1. enescingoz/awesome-n8n-templates ⭐ 推薦
- **數量**: 280+ 個免費模板
- **內容**: Gmail、Telegram、Slack、Discord、WhatsApp、Google Drive、Notion、OpenAI
- **特色**: AI agents、RAG chatbots、email 自動化、社交媒體、DevOps、文檔處理
- **鏈接**: https://github.com/enescingoz/awesome-n8n-templates
- **備註**: GitHub 上最知名的 n8n 模板集合之一

#### 2. Zie619/n8n-workflows
- **數量**: 4000+ 個（包含從 n8n 官網爬取）
- **特色**: 按類別組織、有搜索界面、大量生產級 workflow
- **鏈接**: https://github.com/zie619/n8n-workflows
- **適合**: 想一次性拿到超多模板的用戶

#### 3. Danitilahun/n8n-workflow-templates
- **數量**: 2053 個
- **特色**: 組織非常專業，有快速搜索、分析和瀏覽系統
- **鏈接**: https://github.com/Danitilahun/n8n-workflow-templates

#### 4. wassupjay/n8n-free-templates
- **數量**: 200+ 個
- **特色**: 偏向 AI 棧（Vector DB、Embeddings、LLM），結合經典自動化
- **鏈接**: https://github.com/wassupjay/n8n-free-templates

#### 5. ritik-prog/n8n-automation-templates-5000
- **數量**: 5000+ 個真實世界模板
- **特色**: AI、CRM、財務、電商、營銷、RAG 等生產級場景
- **鏈接**: https://github.com/ritik-prog/n8n-automation-templates-5000

#### 6. zengfr/n8n-workflow-all-templates ⭐ 最全面
- **數量**: 8615+ 個（最全面之一）
- **特色**: 定期同步更新
- **鏈接**: https://github.com/zengfr/n8n-workflow-all-templates

---

## 🔄 n8n → Node-RED 轉換指南

### 概念對照

| n8n 概念 | Node-RED 概念 | 備註 |
|---------|--------------|------|
| Workflow | Flow | 相同概念 |
| Node | Node | 相同概念 |
| Trigger | Inject/HTTP In | 觸發節點 |
| HTTP Request | http request | HTTP 請求 |
| Function | function | 代碼節點 |
| IF/Switch | switch | 條件分支 |
| Wait | delay | 延遲 |
| Webhook | http in | Webhook 接收 |
| Schedule | inject (repeat) | 定時任務 |

### 轉換流程

當靚仔提出自動化需求：

1. **分析需求** - 理解觸發條件、處理邏輯、輸出動作
2. **搜索模板** - 在上述 6 個庫中搜索相似 workflow
3. **評估可行性** - 檢查 Node-RED 是否有對應節點
4. **設計 Flow** - 將 n8n 邏輯轉換為 Node-RED 節點
5. **實現測試** - 使用本 skill 部署並測試

### 常用節點對照

| 功能 | n8n | Node-RED |
|------|-----|----------|
| HTTP API | HTTP Request | http request |
| Webhook | Webhook | http in |
| Email | Email (IMAP/SMTP) | email |
| Database | Postgres/MySQL | node-red-contrib-postgres |
| AI/LLM | OpenAI | node-red-contrib-openai |
| Telegram | Telegram | node-red-contrib-telegrambot |
| Discord | Discord | node-red-contrib-discord |
| Slack | Slack | node-red-contrib-slack |
| Scheduler | Schedule | inject (repeat/cron) |
| JSON 處理 | Set/Function | function/json |

---

## 參考

- Node-RED: https://nodered.org/
- Node-RED Admin API: https://nodered.org/docs/api/admin/
- Node-RED Nodes: https://flows.nodered.org/
- n8n Workflow 庫: https://n8n.io/workflows/