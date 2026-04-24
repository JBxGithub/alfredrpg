# Alfred Memory System (AMS) - 版本比較與整合計劃

> **日期**: 2026-04-08
> **比較對象**: 
> - hermes-memory-system (2026-04-07 子代理完成)
> - alfred_memory_system (2026-04-08 呀鬼完成 Phase 1)

---

## 📊 兩個版本比較

### Version A: hermes-memory-system (projects/)
**完成時間**: 2026-04-07 (子代理)
**位置**: `~/openclaw_workspace/projects/hermes-memory-system/`

| 組件 | 狀態 | 說明 |
|------|------|------|
| MemoryManager | ✅ | MEMORY.md + USER.md 雙層記憶 |
| SessionStore | ✅ | SQLite + FTS5 |
| SkillManager | ✅ | SKILL.md 漸進式披露 |
| LearningEngine | ✅ | 自動技能創建 + Nudges |
| WindowsScheduler | ✅ | Task Scheduler 整合 |
| CLI | ✅ | PowerShell 工具 |
| **Context Monitor** | ❌ | **缺失** |
| **測試驗證** | ❓ | 未知 |

### Version B: alfred_memory_system (workspace/)
**完成時間**: 2026-04-08 (呀鬼)
**位置**: `~/openclaw_workspace/alfred_memory_system/`

| 組件 | 狀態 | 說明 |
|------|------|------|
| **Context Monitor** | ✅ | 70%/85%/95% 三級閾值 |
| **Token 估算** | ✅ | 中英文混合估算 |
| DatabaseManager | ✅ | SQLite + FTS5 |
| CLI | ✅ | 完整命令集 |
| MemoryManager | 🟡 | 基礎框架 |
| SkillManager | 🟡 | 基礎框架 |
| LearningEngine | ❌ | 待開發 |
| **測試驗證** | ✅ | 已驗證運作 |

---

## 🎯 功能對比分析

### hermes-memory-system 有但 AMS 沒有的：
1. **Gemini Flash 摘要整合** - 會話自動摘要
2. **Windows Task Scheduler 整合** - Nudge 系統
3. **完整的 LearningEngine** - 自動技能創建邏輯
4. **漸進式 Skill 披露** - Level 0/1/2 加載

### AMS 有但 hermes-memory-system 沒有的：
1. **Context Monitor** - 實時監控對話長度 ⚡
2. **Token 估算** - 中英文混合估算
3. **使用趨勢分析** - 預測 Context 用盡時間
4. **已驗證運作** - 測試通過

---

## 💡 建議方案

### 方案 1: 整合兩者優點 (推薦)
**做法**: 將 hermes-memory-system 的完整功能整合到 AMS，並加入 Context Monitor

**步驟**:
1. 驗證 hermes-memory-system 是否正常運作
2. 將 Context Monitor 移植過去
3. 統一使用 AMS 的 DatabaseManager (更完整)
4. 測試整合後的系統

**優點**: 功能最完整
**缺點**: 需要額外整合時間 (1-2 天)

### 方案 2: 擴展 AMS (快速)
**做法**: 在現有 AMS 基礎上，添加缺失的功能

**步驟**:
1. 參考 hermes-memory-system 實現 LearningEngine
2. 添加 Windows Task Scheduler 支援
3. 完善 MemoryManager 和 SkillManager

**優點**: 基於已驗證的代碼
**缺點**: 需要重新實現部分功能

### 方案 3: 直接使用 hermes-memory-system
**做法**: 驗證並修復 hermes-memory-system，添加 Context Monitor

**步驟**:
1. 測試 hermes-memory-system 是否可運行
2. 修復任何問題
3. 添加 Context Monitor 模組

**優點**: 功能已完整
**缺點**: 需要調試未知問題

---

## 🚀 靚仔請選擇

| 方案 | 時間 | 風險 | 功能完整度 |
|------|------|------|-----------|
| 1. 整合兩者 | 1-2 天 | 中 | ⭐⭐⭐⭐⭐ |
| 2. 擴展 AMS | 2-3 天 | 低 | ⭐⭐⭐⭐⭐ |
| 3. 使用 hermes | 0.5-1 天 | 高 | ⭐⭐⭐⭐⭐ (如無問題) |

**我的建議**: 方案 1 (整合兩者)
- AMS 的 Context Monitor 和 DatabaseManager 已驗證
- hermes 的功能更完整
- 整合後可得到最佳系統

---

## 📝 遺漏檢查 (根據 2026-04-07 計劃)

根據之前的計劃，以下功能需要確認：

| 功能 | hermes | AMS | 狀態 |
|------|--------|-----|------|
| 自動監控 Context | ❌ | ✅ | AMS 已完成 |
| 自動生成摘要 | ✅ | ❌ | 需整合 |
| 向量數據庫存儲 | ❌ | ❌ | 兩者都未實現 |
| 語義記憶檢索 | ❌ | ❌ | 兩者都未實現 |
| 記憶自動注入 | ✅ | ❌ | 需整合 |

**結論**: 
- ✅ Context 監控 - AMS 已完成
- 🟡 自動摘要 - hermes 有，需整合
- ❌ 向量數據庫 - 兩者都未實現 (可選功能)
- ❌ 語義檢索 - 兩者都未實現 (可選功能)

---

*等待靚仔決定下一步行動*
