# Self-Learning 整合方案

> AMS Weekly Learning Review + Self-Improving Weekly Review 協同運作設計

**日期**: 2026-04-19  
**版本**: 1.0  
**狀態**: 設計完成，待實施

---

## 🎯 整合目標

1. **避免重複** - 兩個系統分工明確，互補不足
2. **自動化學習** - 錯誤和經驗自動歸檔
3. **持續改進** - 每週回顧生成可執行的改進建議

---

## 📊 系統分工

| 系統 | 主要職責 | 數據來源 | 輸出 |
|------|---------|---------|------|
| **AMS Weekly** | 對話分析、決策提取、模式識別 | SQLite 數據庫 (sessions, messages) | 週報 + 學習建議 |
| **Self-Improving** | 錯誤追蹤、糾正措施、經驗累積 | `.learnings/ERRORS.md`, `LEARNINGS.md` | 改進報告 + 行動項目 |

---

## 🔄 整合工作流程

### 日常運作 (自動)

```
每次對話/任務
       │
       ▼
┌─────────────────────┐
│   AMS Skill Hook    │ ◀── 自動觸發
│                     │
│ • 記錄對話到數據庫   │
│ • Context 監控      │
│ • 複雜任務檢測      │
└──────────┬──────────┘
           │
    複雜任務完成?
           │
     ┌─────┴─────┐
     │           │
    是          否
     │           │
     ▼           ▼
┌──────────┐  ┌──────────┐
│ 自動分析  │  │ 繼續監控  │
│ 學習點   │  │          │
└────┬─────┘  └──────────┘
     │
     ▼
是否需要記錄?
     │
┌────┴────┐
│         │
錯誤      經驗
│         │
▼         ▼
ERRORS.md LEARNINGS.md
```

### 每週回顧 (週一 09:00 & 09:30)

```
週一 09:00
    │
    ▼
┌─────────────────────────────┐
│  AMS Weekly Learning Review │
│                             │
│  1. 讀取本週所有對話         │
│  2. 提取關鍵決策            │
│  3. 識別重複模式            │
│  4. 生成學習建議            │
└──────────────┬──────────────┘
               │
               ▼
    輸出: memory/weekly-learning-review-YYYY-MM-DD.md
               │
               ▼
週一 09:30
    │
    ▼
┌─────────────────────────────┐
│  Self-Improving Weekly      │
│  Review                     │
│                             │
│  1. 讀取 ERRORS.md          │
│  2. 讀取 LEARNINGS.md       │
│  3. 讀取 AMS 週報           │ ◀── 整合點
│  4. 分析錯誤模式            │
│  5. 生成改進計劃            │
└──────────────┬──────────────┘
               │
               ▼
    輸出: memory/self-improving-weekly-YYYY-MM-DD.md
               │
               ▼
           通知用戶
```

---

## 📝 具體實施方案

### Phase 1: 建立自動記錄機制 (立即)

建立新 Skill: **學習歸檔器 (learning-archiver)**

```python
# 功能:
# 1. 監聽對話結束事件
# 2. 檢測是否有錯誤發生
# 3. 自動歸檔到 ERRORS.md 或 LEARNINGS.md

觸發條件:
- 用戶糾正指令
- 工具調用失敗
- 用戶明確表示「記住」
- 複雜任務完成 (>5 tool calls)
```

### Phase 2: 修改 Self-Improving Weekly Review (本週)

更新現有 Cron Job，加入 AMS 數據讀取：

```yaml
# 現有任務修改
name: SelfImproving-Weekly-Review
schedule: 30 9 * * 1  # 週一 09:30

# 新增步驟:
# 1. 讀取 AMS 週報 (memory/weekly-learning-review-YYYY-MM-DD.md)
# 2. 整合 AMS 發現的模式
# 3. 避免重複建議
```

### Phase 3: 建立回饋循環 (下週)

```
Self-Improving 發現問題
         │
         ▼
┌─────────────────┐
│  生成改進建議    │
│  (Action Items) │
└────────┬────────┘
         │
         ▼
是否需要 Skill?
         │
    ┌────┴────┐
    │         │
   是         否
    │         │
    ▼         ▼
┌────────┐  ┌────────┐
│創建    │  │更新    │
│Skill   │  │LEARNINGS│
└────────┘  └────────┘
```

---

## 🗂️ 檔案結構更新

```
~/.openclaw/skills/self-improving/
│
├── .learnings/
│   ├── ERRORS.md              # 錯誤記錄 (手動 + 自動)
│   ├── LEARNINGS.md           # 經驗記錄 (手動 + 自動)
│   └── action-items.md        # 待執行改進項目 (新增)
│
└── integrations/
    └── ams_connector.py       # AMS 數據讀取接口 (新增)

~/openclaw_workspace/memory/
│
├── weekly-learning-review-YYYY-MM-DD.md      # AMS 輸出
├── self-improving-weekly-YYYY-MM-DD.md       # Self-Improving 輸出
└── action-items-tracker.md                   # 改進項目追蹤 (新增)
```

---

## 📋 本週行動項目

1. **建立 learning-archiver skill** - 自動記錄錯誤和經驗
2. **更新 Self-Improving Weekly Review** - 整合 AMS 週報讀取
3. **建立 action-items.md** - 追蹤待執行改進
4. **測試整合流程** - 下週一驗證

---

## 🎯 預期效果

| 指標 | 現狀 | 目標 |
|------|------|------|
| 錯誤記錄 | 手動 | 自動 |
| 經驗累積 | 被動 | 主動 |
| 改進建議 | 每週生成 | 每週生成 + 追蹤執行 |
| 重複錯誤 | 可能重複 | 顯著減少 |

---

*設計完成，等待靚仔指示實施*
