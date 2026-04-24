---
name: alfred-memory-system
description: "Alfred Memory System (AMS) - 統一記憶管理、Context監控、自動學習"
version: 2.0.0
metadata:
  openclaw:
    tags: [memory, context, learning, monitoring]
    category: system
    auto_load: true
---

# Alfred Memory System (AMS) Skill

統一的記憶管理系統，整合 Context 監控、記憶同步、技能管理和自動學習。

## 功能

- **Context Monitor**: 實時監控對話長度，70%/85%/95% 三級閾值預警
- **Memory Manager**: 自動同步 MEMORY.md / USER.md
- **Skill Manager**: 追蹤 Skills 使用情況
- **Learning Engine**: 自動提取對話中的重要信息
- **Project Tracker**: 追蹤專案狀態

## 使用方式

### 在對話中自動運行

安裝後，AMS 會在每次對話後自動：
1. 檢查 Context 使用率
2. 超過 70% 時發出警告
3. 自動同步記憶到 MEMORY.md

### 手動使用

```python
# 檢查 Context
ams context

# 查看記憶
ams memory list

# 查看狀態
ams status

# 搜索記憶
ams memory search "關鍵詞"
```

## 配置

```yaml
# ~/.ams/config.yaml
context_monitor:
  enabled: true
  warning_threshold: 70
  
memory_manager:
  auto_sync: true
  
learning_engine:
  enabled: false  # 默認關閉
```

## 依賴

- Python 3.8+
- SQLite3
- PyYAML

## 安裝

```bash
# 複製到 OpenClaw skills 目錄
cp -r alfred-memory-system ~/.openclaw/skills/

# 初始化
python -m alfred_memory_system init
```
