---
name: opencode-integration
description: OpenClaw Oh-My-Opencode Integration System - 整合 IntentGate、Hash-Anchored Edit、Todo Enforcer、Plan 文件驅動四大機制
version: 1.0.0
author: ClawTeam
private: true
---

# Opencode Integration Skill

> 將 Oh-My-Opencode 核心機制整合到 OpenClaw + ClawTeam 生態

## 概述

本 Skill 實現四個核心機制：

1. **IntentGate** - 意圖分類與智能路由，將用戶查詢分類到 ClawTeam 7人角色
2. **Hash-Anchored Edit** - 哈希驗證編輯系統，防止文件編輯衝突
3. **Todo Enforcer** - 任務強制執行機制，與 AMS 深度整合
4. **Plan 文件驅動** - 專案計劃管理系統

## 安裝

```bash
# 安裝依賴
pip install -r requirements.txt
```

## 使用方法

### 1. IntentGate - 意圖分類

```python
from opencode_integration import IntentGate

# 初始化
gate = IntentGate()

# 處理用戶查詢
classification, routing = gate.process("幫我監控股票價格")

print(f"意圖: {classification.intent.value}")
print(f"分類: {classification.category.value}")
print(f"目標代理: {routing.target_agent}")
```

### 2. Hash-Anchored Edit - 安全編輯

```python
from opencode_integration import HashAnchoredEditor

# 初始化
editor = HashAnchoredEditor()

# 讀取文件帶哈希
version = editor.read_file("example.py")
print(editor.get_file_with_hashes())

# 編輯行（基於哈希驗證）
result = editor.edit_line(
    "example.py",
    line_number=5,
    expected_hash="a3f",
    new_content="print('hello')"
)
```

### 3. Todo Enforcer - 任務強制

```python
from opencode_integration import TodoEnforcer

# 初始化
enforcer = TodoEnforcer()

# 創建任務
task = enforcer.create_task(
    title="完成報告",
    description="撰寫月度報告",
    priority="high"
)
task.start()

# 檢查進度
report = enforcer.get_report()
print(f"進度: {report.progress_percent}%")
```

### 4. Plan 文件驅動 - 計劃管理

```python
from opencode_integration import PlanManager

# 初始化
manager = PlanManager()

# 創建計劃
plan = manager.create_plan(
    name="系統重構",
    description="重構核心模組",
    priority="high"
)

# 添加任務
from opencode_integration import Task
task = Task(
    id="task-001",
    title="設計新架構",
    assignee="技術官"
)
plan.add_task(task)

# 保存計劃
plan.save(Path("plans/system-refactor.md"))
```

## 整合使用

```python
from opencode_integration import OpenClawIntegration

# 初始化整合系統
integration = OpenClawIntegration()

# 處理用戶查詢（完整流程）
result = integration.process_user_query("幫我寫一個股票監控程式")

# 編輯文件
edit_result = integration.edit_file(
    "stock_monitor.py",
    line_number=10,
    expected_hash="a3f",
    new_content="# 新增功能"
)

# 創建計劃
plan_info = integration.create_plan(
    name="股票監控系統",
    description="開發自動化股票監控"
)

# 獲取系統狀態
status = integration.get_system_status()
```

## CLI 使用

```bash
# 查看系統狀態
python main.py --command status

# 處理查詢
python main.py --command query --query "幫我分析財務報表"

# 查看任務報告
python main.py --command report

# 交互模式
python main.py
```

## 配置

編輯 `config/integration.yaml`：

```yaml
intentgate:
  enabled: true
  high_confidence: 0.85
  medium_confidence: 0.70

hash_anchored_edit:
  enabled: true
  strict_mode: true
  hash_length: 3

todo_enforcer:
  enabled: true
  check_interval: 30
  timeout_threshold: 30

plan_driven:
  enabled: true
  plans_dir: "~/openclaw_workspace/plans"
```

## 架構

```
opencode-integration/
├── main.py                      # 主入口
├── config/
│   └── integration.yaml         # 配置
├── modules/
│   ├── intentgate/              # 意圖分類
│   │   └── engine.py
│   ├── hash_anchored_edit/      # 哈希編輯
│   │   └── editor.py
│   ├── todo_enforcer/           # 任務強制
│   │   └── enforcer.py
│   └── plan_driven/             # 計劃管理
│       └── manager.py
└── requirements.txt
```

## 與 ClawTeam 整合

| 機制 | ClawTeam 角色 | 應用場景 |
|------|--------------|---------|
| IntentGate | 隊長（路由） | 分派任務到合適角色 |
| Hash-Anchored | 技術官 | 安全編輯代碼 |
| Todo Enforcer | 全員 | 確保任務完成 |
| Plan 驅動 | 隊長 | 專案管理 |

## 與 AMS 整合

- Todo Enforcer 自動同步任務狀態到 AMS
- Plan 文件自動記錄到 memory/
- Context Monitor 監察任務進度

## 注意事項

1. **Private Skill** - 此為私人 Skill，不公開分享
2. **依賴 Opencode** - 複雜編程任務會調用 Opencode ACP
3. **整合測試** - 建議先測試各模組再正式使用

## 更新日誌

| 版本 | 日期 | 更新內容 |
|------|------|---------|
| 1.0.0 | 2026-04-13 | 初始版本，整合四大機制 |

## 參考

- Oh-My-OpenAgent: https://github.com/code-yeongyu/oh-my-openagent
- Opencode: https://opencode.ai
- OpenClaw Docs: https://docs.openclaw.ai
