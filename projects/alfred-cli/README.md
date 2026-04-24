# Alfred CLI v2.0

> Alfred AI Toolkit 統一入口  
> 版本: 2.0.0  
> 更新日期: 2026-04-11  
> 狀態: ✅ 全部功能驗證通過

---

## 🚀 快速開始

### 進入項目目錄
```bash
cd ~/openclaw_workspace/projects/alfred-cli
```

### 基本使用
```bash
python alfred_v2.py <command> [options]
```

---

## 📚 完整命令列表

### 1. 技能分析 (Skill Analyzer)

分析 OpenClaw 技能生態，生成報告。

```bash
python alfred_v2.py analyze skills
```

**輸出**:
- 總技能數
- 分類統計
- 重複檢測
- 報告文件（Markdown + JSON）

**報告位置**: `~/openclaw_workspace/reports/skill-analysis-YYYYMMDD.md`

---

### 2. 智能路由 (Smart Router)

根據查詢推薦最適合的技能。

```bash
# 基本使用
python alfred_v2.py route "check trading status"

# 指定返回數量
python alfred_v2.py route "desktop control" --top 5
```

**示例輸出**:
```
🧭 路由查詢: desktop control

✅ 找到 1 個推薦技能:

  1. desktop-control-win (匹配度: 9)
     分類: system
     描述: Windows desktop control
```

---

### 3. 績效儀表板 (Performance Dashboard)

顯示 AI 助理績效報告。

```bash
# 默認顯示本週報告
python alfred_v2.py dashboard show

# 指定時間範圍
python alfred_v2.py dashboard show --period day
python alfred_v2.py dashboard show --period week
python alfred_v2.py dashboard show --period month
```

**示例輸出**:
```
📊 生成績效報告...

📈 week 報告:
  任務完成: 42
  成功率: 95.0%
  平均響應時間: 1.23s
```

---

### 4. 代碼片段 (Snippets Pro)

搜索代碼片段。

```bash
# 搜索關鍵字
python alfred_v2.py snippet search "error handling"
python alfred_v2.py snippet search "python"
python alfred_v2.py snippet search "api"
```

**注意**: 需要先添加片段到數據庫才能搜索。

---

### 5. 工作流 (Workflow Designer)

管理和執行工作流。

```bash
# 列出所有工作流
python alfred_v2.py workflow list

# 執行工作流
python alfred_v2.py workflow run test-workflow
python alfred_v2.py workflow run morning-routine
```

**示例輸出**:
```
📋 工作流列表:
  - morning-routine
  - system-health-check
  - trading-monitor
  - test-workflow

🚀 執行工作流: test-workflow
📋 描述: 測試工作流

  Step 1: check_status (check_status)
    ✅ 完成
  Step 2: send_notification (send_notification)
    ✅ 完成
  Step 3: collect_metrics (collect_metrics)
    ✅ 完成

✅ 工作流執行完成: 3/3 步驟
```

---

### 6. 開發助手 (Skill Dev Assistant)

創建新技能模板。

```bash
# 基本創建
python alfred_v2.py dev create my-skill

# 指定分類
python alfred_v2.py dev create my-skill --category automation
python alfred_v2.py dev create my-skill --category data
```

**創建的文件**:
- `SKILL.md` - 技能說明文件
- `src/__init__.py` - 包入口

**輸出位置**: `~/openclaw_workspace/skills/{skill-name}/`

---

## 🛠️ 故障排除

### 問題 1: ModuleNotFoundError

**錯誤**: `No module named 'xxx'`

**解決**: 確保在 `alfred-cli` 目錄運行命令：
```bash
cd ~/openclaw_workspace/projects/alfred-cli
python alfred_v2.py ...
```

### 問題 2: 數據庫不存在

**現象**: 首次運行時某些命令報錯

**解決**: 首次運行會自動創建數據庫，無需手動處理。

### 問題 3: 工作流 YAML 錯誤

**現象**: `yaml.parser.ParserError`

**解決**: 使用簡化版工作流格式，避免在 YAML 中嵌入複雜 Python 代碼。

---

## 📁 項目結構

```
alfred-cli/
├── alfred_v2.py          # 主程序（推薦使用）
├── alfred.py             # 原始版本（有導入問題）
├── test_simple.py        # 簡化測試
├── test_aat.ps1          # PowerShell 測試腳本
└── README.md             # 本文檔
```

---

## 🔗 相關項目

| 項目 | 路徑 | 功能 |
|------|------|------|
| skill-analyzer | `../skill-analyzer/` | 技能分析 |
| smart-router | `../smart-router/` | 智能路由 |
| performance-dashboard | `../performance-dashboard/` | 績效儀表板 |
| snippets-pro | `../snippets-pro/` | 代碼片段 |
| workflow-designer | `../workflow-designer/` | 工作流 |
| skill-dev-assistant | `../skill-dev-assistant/` | 開發助手 |

---

## 📝 更新日誌

### v2.0.0 (2026-04-11)
- ✅ 全部 7 個命令驗證通過
- ✅ 修復所有導入問題
- ✅ 創建兼容版本模塊
- ✅ 實現 Smart Router 和 Workflow Executor

### v1.0.0 (2026-04-11)
- 初始版本
- 基本 CLI 框架

---

*由 呀鬼 (Alfred) 開發*  
*最後更新: 2026-04-11*
