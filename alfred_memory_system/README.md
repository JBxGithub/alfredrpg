# Alfred Memory System (AMS) v2.0

> **Windows 版自適應學習機制長期記憶架構**
> 
> 整合版本 v2.0.0 | 整合日期: 2026-04-08

## 🎯 系統概述

Alfred Memory System (AMS) 是一個為呀鬼打造的持續學習、自我改進的長期記憶系統。

### 整合內容

| 組件 | 來源 | 狀態 |
|------|------|------|
| Context Monitor | 現有 AMS | ✅ 已整合 |
| Memory Manager | hermes-memory-system | ✅ 已整合 |
| Skill Manager | hermes-memory-system | ✅ 已整合 |
| Learning Engine | hermes-memory-system | ✅ 已整合 |
| Summarizer | memory-system-plugin | ✅ 已整合 (可選) |
| OpenClaw Hook | 新增 | ✅ 已整合 |
| Memory Sync | 新增 | ✅ 已整合 |
| Project Tracker | 新增 | ✅ 已整合 |

---

## 📦 核心組件

### 1. Context Monitor (`core/context_monitor.py`)
實時監控對話 Context 使用情況
- 中英文混合 token 估算
- 多級閾值監控（70% 警告 / 85% 壓縮 / 95% 緊急）
- 使用趨勢分析與預測

### 2. Memory Manager (`core/memory_manager.py`)
雙層記憶架構管理器（從 hermes 整合）
- MEMORY.md 管理 (2200 chars)
- USER.md 管理 (1375 chars)
- 自動壓縮與存檔
- 全文搜索

### 3. Skill Manager (`core/skill_manager.py`)
技能管理器（從 hermes 整合）
- SKILL.md 格式管理
- 漸進式披露 (Progressive Disclosure)
- 版本控制與使用追蹤
- 自動創建與改進建議

### 4. Learning Engine (`core/learning_engine.py`)
自適應學習引擎（從 hermes 整合）
- 任務複雜度分析
- 自動技能創建
- 錯誤記錄與改進建議
- 定期提醒 (Nudges)

### 5. Summarizer (`core/summarizer.py`)
摘要生成器（從 plugin 整合，可選）
- 自動生成對話摘要
- 提取決策、行動項目、思考過程
- **注意：默認關閉，不依賴 ChromaDB**

---

## 🔌 整合模組

### OpenClaw Hook (`integration/openclaw_hook.py`)
OpenClaw 整合鉤子
- 每次對話後自動檢查 Context
- 超過 70% 時發出警告
- **默認關閉，需要手動啟用**

### Memory Sync (`integration/memory_sync.py`)
記憶同步模組
- 自動讀取 memory/ 目錄
- 同步到數據庫和 MEMORY.md / USER.md
- 保持與現有文件兼容

### Project Tracker (`integration/project_tracker.py`)
專案追蹤模組
- 讀取 project-states/ 目錄
- 追蹤專案狀態變化
- 與數據庫同步

---

## 🚀 快速開始

### 初始化系統
```powershell
cd ~/openclaw_workspace
python -m alfred_memory_system.cli init
```

### 查看系統狀態
```powershell
python -m alfred_memory_system.cli status
```

### 在 Python 中使用
```python
from alfred_memory_system import AMS

# 初始化
ams = AMS()
ams.initialize()

# 檢查 Context
messages = [...]  # 當前對話消息
status = ams.context_monitor.check_context(messages)
print(status)

# 添加記憶
ams.memory_manager.add("用戶偏好使用深色主題", category="preference")

# 分析任務並可能創建技能
analysis = ams.learning_engine.analyze_task(
    task_description="部署 TradingBot",
    steps=["步驟1", "步驟2", "步驟3"],
    duration_minutes=15,
    tool_calls_count=8
)
if analysis.should_create_skill:
    ams.learning_engine.auto_create_skill(analysis)
```

---

## 🛠️ CLI 命令

### 基礎命令
```powershell
ams init                          # 初始化 AMS
ams status                        # 顯示系統狀態
ams context                       # 顯示 Context 報告
ams reset                         # 重置系統（刪除所有數據）
```

### 記憶管理
```powershell
ams memory list                   # 列出所有記憶
ams memory list --category preference  # 按分類過濾
ams memory add "內容" --category general  # 添加記憶
ams memory search "關鍵詞"        # 搜索記憶
```

### 技能管理
```powershell
ams skill list                    # 列出所有技能
ams skill list --auto-only        # 只顯示自動創建的技能
```

### 學習記錄管理
```powershell
ams learning list                 # 列出學習記錄
ams learning list --type error    # 按類型過濾
ams learning add "內容" --type improvement  # 添加學習記錄
```

### 專案管理
```powershell
ams project list                  # 列出專案
ams project list --status active  # 按狀態過濾
ams project add "名稱" --description "描述"  # 添加專案
```

### 同步
```powershell
ams sync --memory --projects      # 同步所有
ams sync --memory --dry-run       # 預覽記憶同步
ams sync --projects --dry-run     # 預覽專案同步
```

### 任務分析
```powershell
ams analyze "任務描述" --steps "步驟1,步驟2,步驟3" --duration 15 --tool-calls 8
```

---

## ⚙️ 配置

配置文件位置：`~/.ams/config.yaml`

```yaml
version: "2.0.0"
debug: false

context:
  enabled: true
  warning_threshold: 0.70
  compress_threshold: 0.85
  critical_threshold: 0.95
  model_context_length: 128000
  check_interval: 5

memory:
  enabled: true
  auto_extract: true
  max_memory_entries: 100

skill:
  enabled: true
  auto_create: true
  min_tool_calls: 5

# 可選功能（默認關閉）
summarizer_enabled: false
```

---

## 🔗 與 OpenClaw 整合

### 在 AGENTS.md 中添加

```python
# 在啟動序列中初始化 AMS Hook（可選，默認關閉）
try:
    from alfred_memory_system.integration.openclaw_hook import init_ams_hook
    ams_hook = init_ams_hook(enabled=False)  # 設為 True 啟用
except ImportError:
    ams_hook = None

# 每次對話後檢查 Context
def after_message_processing(messages, session_id):
    if ams_hook and ams_hook.enabled:
        try:
            status = ams_hook.check_context(messages, session_id)
            if status and status['usage_percent'] > 70:
                # Context 警告已在 Hook 中打印
                pass
        except Exception as e:
            print(f"[AMS] Context check failed: {e}")
```

---

## 📊 數據庫 Schema

### 現有表
- `sessions` - 會話記錄
- `messages` - 消息記錄（FTS5 全文搜索）
- `memories` - 記憶（FTS5 全文搜索）
- `skills` - 技能
- `context_usage` - Context 使用記錄

### 新增表（v2.0）
- `learnings` - 學習記錄（錯誤、改進建議）
- `learnings_fts` - 學習記錄全文搜索
- `projects` - 專案狀態追蹤
- `project_sessions` - 專案與 Session 關聯

---

## 🧪 測試

運行整合測試：
```powershell
cd ~/openclaw_workspace/alfred_memory_system
python test_integration.py
```

測試內容：
1. 數據庫 Schema 更新
2. Memory Manager 功能
3. Skill Manager 功能
4. Learning Engine 功能
5. Summarizer 功能
6. OpenClaw Hook 功能
7. Memory Sync 功能
8. Project Tracker 功能

---

## 📁 檔案結構

```
alfred_memory_system/
├── __init__.py                 # 主 AMS 類 v2.0
├── config.py                   # 配置管理
├── README.md                   # 本文檔
├── test_integration.py         # 整合測試
│
├── core/                       # 核心組件
│   ├── __init__.py
│   ├── context_monitor.py      # Context 監控
│   ├── memory_manager.py       # 記憶管理（從 hermes 整合）
│   ├── skill_manager.py        # 技能管理（從 hermes 整合）
│   ├── learning_engine.py      # 學習引擎（從 hermes 整合）
│   └── summarizer.py           # 摘要生成器（從 plugin 整合，可選）
│
├── storage/                    # 存儲層
│   └── __init__.py             # 數據庫管理（含 learnings, projects 表）
│
├── integration/                # 整合模組
│   ├── __init__.py
│   ├── openclaw_hook.py        # OpenClaw 整合鉤子
│   ├── memory_sync.py          # 記憶同步
│   └── project_tracker.py      # 專案追蹤
│
├── cli/                        # 命令行工具
│   └── __main__.py             # CLI 入口
│
└── data/                       # 數據目錄
    └── alfred_memory.db        # SQLite 數據庫
```

---

## ⚠️ 重要提醒

1. **不要修改 OpenClaw 核心** - 所有整合都是非侵入式的
2. **不要刪除現有功能** - 保持向後兼容
3. **所有新功能默認關閉** - 需要手動啟用
4. **代碼需有完整註釋** - 便於維護

---

## 📝 更新日誌

### v2.0.0 (2026-04-08)
- ✅ 整合 Memory Manager（從 hermes-memory-system）
- ✅ 整合 Skill Manager（從 hermes-memory-system）
- ✅ 整合 Learning Engine（從 hermes-memory-system）
- ✅ 整合 Summarizer（從 memory-system-plugin，可選）
- ✅ 添加 learnings 和 projects 數據庫表
- ✅ 創建 OpenClaw 整合模組
- ✅ 創建記憶同步模組
- ✅ 創建專案追蹤模組
- ✅ 更新 CLI 添加新命令
- ✅ 提供整合測試腳本

---

*整合完成時間: 2026-04-08*
*版本: v2.0.0*
