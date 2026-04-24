# 防失憶機制 - 連續性優先協議

> **生效日期**: 2026-04-07  
> **核心原則**: 連續性 > 效率 > 深度

---

## 🛡️ 機制一：關鍵對話保護

### 觸發條件
當以下情況出現，立即建立 Checkpoint：
- 重要決策進行到一半
- 複雜分析未完成
- 用戶明確表示「繼續」

### Checkpoint 內容
```
checkpoints/
├── YYYY-MM-DD-HH-MM-context.md  (對話上下文)
├── YYYY-MM-DD-HH-MM-tasks.md    (進行中任務)
└── YYYY-MM-DD-HH-MM-decisions.md (已做決定)
```

---

## 🛡️ 機制二：Context 預警系統

| Context 使用率 | 行動 |
|---------------|------|
| 50% | 提醒用戶，詢問是否存檔 |
| 70% | 強制建立 Checkpoint |
| 80% | 建議開新對話，但保留恢復路徑 |

---

## 🛡️ 機制三：簡化啟動流程

### 原流程 (10-15秒)
1. 讀 SOUL.md
2. 讀 USER.md
3. 讀 MEMORY.md
4. 讀 MEMORY_SYNC_PROTOCOL.md
5. 讀 FutuTradingBot-STATUS.md
6. 讀 memory/YYYY-MM-DD.md
7. 讀 SKILL_PROTOCOL.md

### 新流程 (1-2秒)
1. **只讀 SESSION_RESUME.md** ← 濃縮所有關鍵信息
2. 如需詳情，再讀專項檔案

---

## 🛡️ 機制四：Session 重啟恢復

當被迫開新 Session 時：
1. 自動讀取 `SESSION_RESUME.md`
2. 報告：「已從 [時間點] 恢復」
3. 詢問：「繼續進行中任務，定開始新任務？」

---

## 📋 執行清單

- [x] 建立 SESSION_RESUME.md
- [x] 建立 CONTINUITY_PROTOCOL.md (本檔案)
- [ ] 建立 checkpoints/ 文件夾
- [ ] 測試新啟動流程
- [ ] 驗證恢復機制

---

*此協議由 Alfred 主動建立，回應靚仔對連續性的需求*
