# Skillflows - 自動化工作流程

> **建立日期**: 2026-03-17  
> **用途**: 定義可重用的自動化流程

---

## 📁 目錄結構

```
skillflows/
├── README.md              # 本說明文件
├── health-check.yaml      # 每日健康檢查
├── skill-install.yaml     # 技能安裝流程
├── daily-routine.yaml     # 每日例行流程
└── templates/             # 通知模板
    └── health-alert.txt
```

---

## 🚀 使用方法

### 1. 定義流程
創建 `.yaml` 檔案，定義觸發條件和執行步驟。

### 2. 註冊到系統
更新 `cron` 或手動執行：
```bash
openclaw skillflow run health-check
```

### 3. 監控執行
結果記錄到 `memory/health-logs/skillflow.log`

---

## 📋 現有流程

| 流程名稱 | 觸發方式 | 用途 |
|---------|---------|------|
| health-check | cron (08:00) | 系統健康檢查 |
| skill-install | manual | 安全安裝技能 |
| daily-routine | cron (09:00) | 每日例行任務 |

---

## 🛠️ YAML 格式規範

```yaml
name: 流程名稱
description: 流程描述
trigger:
  type: cron | manual | event
  schedule: "cron 表達式"  # 僅 cron 類型需要
steps:
  step-id:
    action: exec | condition | message | append
    # 根據 action 類型定義參數
```

---

*Skillflow 系統已就緒*
