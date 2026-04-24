# PROJECT_STATE.md - 專案狀態持久化系統

> **最後更新**: 2026-03-29  
> **用途**: 記錄進行中專案的完整狀態，確保重啟後無縫恢復  
> **當前專案**: FutuTradingBot (FTB-001) - Z-Score Mean Reversion 策略

---

## 🎯 設計目標

1. **零摩擦恢復** - 重啟後自動讀取，無需重新解釋上下文
2. **結構化存儲** - 機器可讀格式，支援自動化處理
3. **版本控制** - 追蹤專案演變歷程
4. **多專案支援** - 同時管理多個進行中專案

---

## 📁 檔案結構

```
project-states/
├── index.json              # 專案索引，快速查找
├── templates/
│   └── project-template.md # 新專案模板
├── active/                 # 進行中專案
│   ├── project-{id}.md
│   └── project-{id}.json   # 機器可讀格式
├── archived/               # 已完成/暫停專案
│   └── project-{id}.md
└── snapshots/              # 定期快照備份
    └── {project-id}/
        └── YYYY-MM-DD-HHMMSS.json
```

---

## 🔄 自動化機制

### 1. 啟動時自動恢復

在 `AGENTS.md` 加入：

```markdown
## Project State Recovery

每次啟動時：
1. 讀取 `project-states/index.json`
2. 檢查 `active/` 目錄中的專案
3. 如有進行中專案，自動加載到上下文
4. 顯示專案摘要給用戶
```

### 2. 定期自動保存

使用 cron job 每 30 分鐘保存一次：

```json
{
  "name": "project-state-snapshot",
  "schedule": { "kind": "every", "everyMs": 1800000 },
  "payload": {
    "kind": "systemEvent",
    "text": "Save current project state snapshot"
  }
}
```

### 3. 關鍵操作觸發保存

- 完成重要任務後
- 做出關鍵決策後
- 用戶說「記住這個」時

---

## 📝 專案狀態格式

### 人類可讀格式 (Markdown)

```markdown
# 專案: {名稱}

## 元數據
- **ID**: {uuid}
- **創建時間**: 2026-03-26
- **最後更新**: 2026-03-26 09:15:00
- **狀態**: active | paused | completed | archived
- **優先級**: 🔴 High | 🟡 Medium | 🟢 Low

## 專案概述
{簡短描述專案目標和背景}

## 當前進度
- [x] 已完成的任務
- [ ] 進行中的任務
- [ ] 待處理的任務

## 關鍵決策記錄
| 時間 | 決策 | 原因 | 決策者 |
|------|------|------|--------|
| 09:15 | 採用方案A | 成本較低 | Burt |

## 上下文信息
- **相關檔案**: 
- **相關技能**:
- **外部資源**:

## 待解決問題
1. 
2. 

## 下一步行動
1. 
2. 

## 對話歷史摘要
- 09:00 - 啟動專案，討論目標
- 09:15 - 確定技術方案
```

### 機器可讀格式 (JSON)

```json
{
  "id": "uuid-v4",
  "name": "專案名稱",
  "status": "active",
  "priority": "high",
  "created_at": "2026-03-26T09:00:00+08:00",
  "updated_at": "2026-03-26T09:15:00+08:00",
  "description": "專案描述",
  "progress": {
    "completed": ["task-1", "task-2"],
    "in_progress": ["task-3"],
    "pending": ["task-4", "task-5"]
  },
  "decisions": [
    {
      "timestamp": "2026-03-26T09:15:00+08:00",
      "decision": "採用方案A",
      "reason": "成本較低",
      "by": "Burt"
    }
  ],
  "context": {
    "files": [],
    "skills": [],
    "urls": []
  },
  "issues": [],
  "next_actions": [],
  "conversation_summary": [
    {
      "time": "09:00",
      "summary": "啟動專案，討論目標"
    }
  ]
}
```

---

## 🚀 使用方法

### 創建新專案

```bash
# 自動創建
openclaw project create "專案名稱" --priority high

# 或手動複製模板
cp project-states/templates/project-template.md project-states/active/project-{uuid}.md
```

### 保存當前狀態

```bash
# 手動保存
openclaw project save

# 或自動保存（每30分鐘）
```

### 恢復專案

```bash
# 列出進行中專案
openclaw project list

# 恢復特定專案
openclaw project resume {project-id}
```

### 完成/暫停專案

```bash
openclaw project complete {project-id}
openclaw project pause {project-id}
```

---

## 💡 與現有系統整合

### 與三層記憶系統的關係

| 層級 | 用途 | 內容 |
|------|------|------|
| **Project State** | 專案級上下文 | 進行中專案的完整狀態 |
| **MEMORY.md** | 長期記憶 | 重要決策、方法論、偏好 |
| **memory/YYYY-MM-DD.md** | 每日流水帳 | 原始對話記錄 |
| **memory/context.md** | 運行時上下文 | 當前會話的臨時狀態 |

### 啟動流程整合

```
1. 讀取 SOUL.md (身份)
2. 讀取 USER.md (用戶偏好)
3. 讀取 MEMORY.md (長期記憶)
4. 讀取 SKILL_PROTOCOL.md (技能地圖)
5. 【新增】讀取 project-states/index.json
6. 【新增】如有進行中專案，加載到上下文
7. 讀取 memory/YYYY-MM-DD.md (今日/昨日)
```

---

## 📊 實施計劃

### Phase 1: 基礎設施 (今天)
- [ ] 創建 `project-states/` 目錄結構
- [ ] 建立專案模板
- [ ] 創建示例專案

### Phase 2: 自動化腳本 (本週)
- [ ] 編寫 `project-manager.py` CLI 工具
- [ ] 整合到啟動流程
- [ ] 設置自動保存 cron job

### Phase 3: 進階功能 (下週)
- [ ] 專案間依賴關係
- [ ] 狀態差異比較
- [ ] 自動生成進度報告

---

## 🔐 安全注意事項

1. **敏感信息** - 專案狀態中如有敏感信息，使用 `secrets.md` 引用而非直接存儲
2. **訪問控制** - 專案狀態僅在 main session 中加載
3. **備份** - 定期備份 `project-states/` 目錄

---

## 📝 更新日誌

| 日期 | 更新內容 |
|------|---------|
| 2026-03-26 | 初始設計，建立框架 |
