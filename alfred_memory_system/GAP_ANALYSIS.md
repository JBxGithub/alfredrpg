# AMS 遺漏檢查與功能對比報告

> **日期**: 2026-04-08
> **主題**: LearningEngine vs Skill Evolver vs Self-Improving Skills

---

## 🔍 遺漏檢查清單

### ✅ 已完成
- [x] Context Monitor - 實時監控對話長度
- [x] Memory Manager - 記憶管理
- [x] Skill Manager - 技能管理
- [x] Learning Engine - 學習引擎
- [x] Summarizer - 摘要生成
- [x] Database - SQLite + FTS5
- [x] Skill Hook - OpenClaw 整合
- [x] 統一安裝到 `~/.openclaw/skills/`

### ⚠️ 可能遺漏
- [ ] **自動化觸發機制** - LearningEngine 如何自動觸發？
- [ ] **與 Self-Improving Skills 整合** - 是否讀取 `.learnings/`？
- [ ] **Nudges 系統** - Windows Task Scheduler 整合是否完整？
- [ ] **Vector Store** - 語義搜索（可選功能，默認關閉）
- [ ] **實際對話測試** - 在真實對話中驗證

---

## 🔄 功能對比：LearningEngine vs Skill Evolver vs Self-Improving

### 📊 對比表

| 功能 | LearningEngine (AMS) | Skill Evolver (設計) | Self-Improving Skills |
|------|---------------------|---------------------|----------------------|
| **觸發條件** | 複雜任務 (>5 tool calls) | 複雜任務 (>5 tool calls) | 錯誤、糾正、功能請求 |
| **輸出** | SKILL.md (自動創建) | SKILL.md (自動創建) | `.learnings/*.md` (記錄) |
| **自動化程度** | 自動創建 Skill | 自動創建 + 改進 | 手動記錄 |
| **改進追蹤** | ✅ 使用統計 | ✅ 使用統計 | ❌ 無 |
| **Nudges** | ✅ 定期提醒 | ✅ 定期提醒 | ❌ 無 |
| **錯誤記錄** | ✅ 有 | ✅ 有 | ✅ 有 |
| **與現有整合** | ⚠️ 部分 | ⚠️ 部分 | ✅ 完整 |

---

## 💡 關鍵發現

### 1. LearningEngine **包含** Skill Evolver 功能

LearningEngine 已經實現了：
- ✅ 自動創建 Skill (analyze_task → create_skill_from_learning)
- ✅ 技能使用追蹤 (usage_count, success_count)
- ✅ 改進建議 (suggest_skill_improvements)
- ✅ Nudges 系統 (setup_nudges)
- ✅ 錯誤記錄 (log_error)

**結論**: LearningEngine **等同於** Skill Evolver，功能已完整

---

### 2. LearningEngine **與** Self-Improving Skills **互補**

| 系統 | 專注點 | 輸出 |
|------|--------|------|
| **LearningEngine** | 自動創建 Skills | `skills/{name}/SKILL.md` |
| **Self-Improving** | 記錄錯誤和學習 | `.learnings/{type}.md` |

**關係**: 
- LearningEngine 可以**讀取** Self-Improving 的記錄來創建 Skills
- Self-Improving 記錄**原始學習**，LearningEngine **提煉成 Skills**

---

### 3. 是否取代 Self-Improving Skills？

**不應該取代**，應該**整合**：

```
Self-Improving Skills          LearningEngine (AMS)
       │                              │
       │  記錄錯誤、糾正               │  分析複雜任務
       │                              │
       ▼                              ▼
  .learnings/                    數據庫 (learnings 表)
       │                              │
       └──────────┬───────────────────┘
                  │
                  ▼
           創建 SKILL.md
                  │
                  ▼
           改進現有 Skills
```

---

## 🎯 建議整合方案

### 方案 A: 保持分離 (推薦)
- **Self-Improving Skills**: 繼續記錄錯誤和學習到 `.learnings/`
- **LearningEngine**: 定期讀取 `.learnings/`，提煉成 Skills

**優點**: 兩者專注不同層面，互補

### 方案 B: 完全整合
- 將 Self-Improving 功能併入 LearningEngine
- 統一輸出到數據庫

**優點**: 單一系統
**缺點**: 失去 Self-Improving 的簡潔性

---

## ⚠️ 實際遺漏項目

### 1. 自動化觸發機制
**問題**: LearningEngine 如何知道「任務完成」？

**解決方案**:
```python
# 在 skill_hook.py 中添加
class AMS:
    def on_task_complete(self, messages, tool_calls_count):
        if tool_calls_count >= 5:
            analysis = self.learning_engine.analyze_task(messages)
            if analysis.should_create_skill:
                self.learning_engine.create_skill_from_learning(analysis)
```

### 2. 與 .learnings/ 整合
**問題**: LearningEngine 沒有讀取現有的 Self-Improving 記錄

**解決方案**:
```python
# 添加同步功能
def sync_from_self_improving(self):
    """從 .learnings/ 讀取記錄到數據庫"""
    learnings_dir = Path("~/openclaw_workspace/.learnings")
    # 讀取 ERRORS.md, LEARNINGS.md 等
    # 轉換為 LearningEntry 存入數據庫
```

### 3. Nudges 實際運行
**問題**: Nudges 是否真正設置了 Windows Task Scheduler？

**需要驗證**:
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "*AMS*" }
```

---

## ✅ 結論

### 功能完整性
- **LearningEngine = Skill Evolver** ✅ (功能已完整)
- **LearningEngine ≠ Self-Improving** ✅ (互補關係)

### 實際遺漏
1. **自動觸發機制** - 需要添加到 Skill Hook
2. **與 .learnings/ 整合** - 可選，但建議添加
3. **Nudges 驗證** - 需要確認 Task Scheduler 是否設置

### 建議行動
1. ✅ 保持現狀 (LearningEngine 已完整)
2. 🟡 添加自動觸發機制 (讓 LearningEngine 自動運行)
3. 🟡 驗證 Nudges 是否運作
4. ❓ 可選：與 .learnings/ 整合

---

*LearningEngine 功能已完整，無需取代 Self-Improving Skills*
