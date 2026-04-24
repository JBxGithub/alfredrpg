# Hermes Memory System - Windows Edition

A Windows-optimized adaptive learning memory architecture inspired by Hermes Agent's dual-layer memory system.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hermes Memory System                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Memory Layer │  │ Session Layer│  │    Skill Layer       │  │
│  │              │  │              │  │                      │  │
│  │ MEMORY.md    │  │ SQLite+FTS5  │  │  SKILL.md files      │  │
│  │ (2200 chars) │  │  + Gemini    │  │  Progressive         │  │
│  │              │  │  Summaries   │  │  Disclosure          │  │
│  │ USER.md      │  │              │  │                      │  │
│  │ (1375 chars) │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Learning Engine                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Auto-Skill   │  │ Self-Improve │  │   Nudge System       │  │
│  │ Creation     │  │              │  │  (Task Scheduler)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
hermes-memory-system/
├── config/
│   └── hermes_config.yaml          # 主配置文件
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── memory_manager.py       # 記憶管理器 (MEMORY.md + USER.md)
│   │   ├── session_store.py        # 會話存儲 (SQLite+FTS5)
│   │   ├── skill_manager.py        # 技能管理器 (SKILL.md)
│   │   └── learning_engine.py      # 自適應學習引擎
│   ├── utils/
│   │   ├── __init__.py
│   │   └── windows_scheduler.py    # Windows Task Scheduler 整合
│   └── cli/
│       ├── __init__.py
│       └── hermes_cli.py           # PowerShell CLI 工具
├── data/
│   ├── memory/                     # 記憶文件存儲
│   ├── sessions/                   # SQLite 數據庫
│   └── skills/                     # 技能文件存儲
├── tests/
│   └── test_memory_system.py
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. 安裝依賴

```powershell
cd ~/openclaw_workspace/projects/hermes-memory-system
pip install -r requirements.txt
```

### 2. 初始化系統

```powershell
python -m src.cli.hermes_cli memory stats
```

### 3. 添加記憶

```powershell
python -m src.cli.hermes_cli memory add "用戶偏好使用 Python 進行數據分析" --category preference
```

### 4. 搜索會話

```powershell
python -m src.cli.hermes_cli session search "數據庫優化"
```

### 5. 創建技能

```powershell
python -m src.cli.hermes_cli skill create --name "數據清洗" --description "數據清洗流程" --category data-processing
```

### 6. 設置定期提醒

```powershell
python -m src.cli.hermes_cli nudge setup --time "09:00" --frequency daily
```

## 📊 Core Components

### 1. MemoryManager
- 管理 MEMORY.md (Agent 記憶, 2200 chars)
- 管理 USER.md (用戶畫像, 1375 chars)
- 提供 add/replace/remove 操作
- 字符限制管理與自動壓縮

### 2. SessionStore
- SQLite 數據庫持久化所有對話
- FTS5 全文搜索
- 會話標籤與分類

### 3. SkillManager
- SKILL.md 格式管理
- 漸進式披露 (Progressive Disclosure)
- 技能版本控制
- 技能發現與加載

### 4. LearningEngine
- 複雜任務後自動創建技能
- 技能使用頻率追蹤
- 技能改進建議
- 定期自我提醒 (Nudges)

## 🪟 Windows 特定優化

### PowerShell 整合
- 完整的 PowerShell CLI 工具
- 管道支持
- 自動補全

### Windows Task Scheduler
- 替代 Linux cron
- 自動設置定期提醒任務
- 系統啟動時自動運行

### Windows 路徑處理
- 正確處理 Windows 路徑分隔符
- 支持長路徑 (\\?\ 前綴)
- 環境變量擴展

## 📝 CLI Reference

### Memory 命令
```powershell
# 添加記憶
hermes memory add "內容" --category general --target memory

# 搜索記憶
hermes memory search "關鍵詞" --target both

# 查看統計
hermes memory stats

# 移除記憶
hermes memory remove "模式" --target memory
```

### Session 命令
```powershell
# 搜索會話
hermes session search "查詢" --limit 10

# 列出會話
hermes session list --limit 10

# 會話統計
hermes session stats
```

### Skill 命令
```powershell
# 列出技能
hermes skill list --category data-processing

# 創建技能
hermes skill create --name "技能名" --description "描述" --content "內容"

# 搜索技能
hermes skill search "關鍵詞"
```

### Nudge 命令
```powershell
# 設置提醒
hermes nudge setup --time "09:00" --frequency daily

# 列出任務
hermes nudge list

# 立即生成提醒
hermes nudge now
```

### Stats 命令
```powershell
# 顯示所有統計
hermes stats
```

## ⚙️ Configuration

配置文件位於 `config/hermes_config.yaml`：

```yaml
# 記憶限制
memory_limits:
  memory_max_chars: 2200
  user_max_chars: 1375
  compression_threshold: 0.9
  keep_recent_memories: 10

# 自適應學習
learning:
  auto_creation:
    enabled: true
    complexity_threshold: 5
    duration_threshold: 15
  
  nudges:
    enabled: true
    frequency: daily
    time: "09:00"
```

## 📚 SKILL.md Format

```markdown
---
name: my-skill
description: Brief description
version: 1.0.0
category: devops
tags: [python, automation]
metadata:
  usage_count: 5
  last_used: 2026-04-07T10:00:00
  created_at: 2026-04-01T09:00:00
---

# Skill Title

## When to Use
Trigger conditions for this skill.

## Procedure
1. Step one
2. Step two

## Pitfalls
- Known failure modes and fixes

## Verification
How to confirm it worked.
```

## 🔧 Integration with OpenClaw

此系統設計為與 OpenClaw 無縫整合：

1. **記憶文件**: 直接使用現有的 `MEMORY.md` 和 `USER.md`
2. **技能目錄**: 與 OpenClaw skills 目錄兼容
3. **工作空間**: 使用相同的 `~/openclaw_workspace` 路徑

## 📈 Future Enhancements

- [ ] Gemini Flash 摘要整合
- [ ] 向量數據庫支持 (可選)
- [ ] 圖形界面 (GUI)
- [ ] 多代理協作記憶
- [ ] 雲端同步

## 📄 License

MIT
