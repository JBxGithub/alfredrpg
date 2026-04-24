# Novel Completion Checker ⚠️ 已棄用

> **狀態**: ⚠️ **測試用 / 已棄用 (DEPRECATED)**  
> **用途**: ~~小說完本檢測~~（原為測試 AGENTS.md 啟動協議）  
> **版本**: v1.0-test  
> **建立日期**: 2026-04-06  
> **棄用日期**: 2026-04-11  
> **原因**: 僅為測試新啟動協議而創建，無實際功能實現

---

## ⚠️ 重要提示

此 Skill **僅為測試用途**，**不建議使用**。

- ❌ 無實際功能代碼
- ❌ 無腳本實現
- ❌ 不再維護

如需小說完本檢測功能，請重新開發或尋找其他解決方案。

---

## 原始概念（僅供參考）

---

## 功能概述

本 Skill 用於檢測小說的完本狀態，確保：
- 情節連貫性
- 人物一致性
- 時間線合理性
- 伏筆回收完整性
- 字數與節奏分析

## 使用方式

### 基本檢測
```python
# 檢測單一小說檔案
python scripts/check-completion.py --file novel.md

# 檢測目錄下所有章節
python scripts/check-completion.py --dir chapters/ --output report.md
```

### 特定檢查項目
```python
# 只檢查人物一致性
python scripts/check-characters.py --file novel.md

# 只檢查時間線
python scripts/check-timeline.py --file novel.md

# 只檢查伏筆回收
python scripts/check-foreshadowing.py --file novel.md
```

## 檢測項目

### 1. 連貫性檢查 (Continuity)
- [ ] 情節邏輯無矛盾
- [ ] 場景轉換合理
- [ ] 對話與行為一致

### 2. 人物一致性 (Character Consistency)
- [ ] 人名拼寫統一
- [ ] 性格特徵一致
- [ ] 能力/背景無矛盾
- [ ] 關係網絡正確

### 3. 時間線驗證 (Timeline)
- [ ] 日期順序正確
- [ ] 時間跨度合理
- [ ] 季節/節日對應正確

### 4. 伏筆回收 (Foreshadowing)
- [ ] 前期伏筆有回收
- [ ] 回收方式合理
- [ ] 無遺漏重要伏筆

### 5. 字數與節奏 (Pacing)
- [ ] 總字數達標
- [ ] 章節長度均衡
- [ ] 高潮位置合理

## 輸出格式

檢測報告生成於 `memory/novel-check-YYYY-MM-DD.md`：

```markdown
# 完本檢測報告 - [小說名稱]
**檢測日期**: 2026-04-06
**總字數**: 150,000
**章節數**: 50

## 摘要
- ✅ 通過項目: 4/5
- ⚠️ 警告項目: 1/5
- 🔴 錯誤項目: 0/5

## 詳細結果
...
```

## 與記憶系統整合

```
檢測結果 → memory/novel-check-YYYY-MM-DD.md
        → summary/novel-completion-status.md (更新)
        → tacit_knowledge.md (寫作經驗累積)
```

## 依賴

- Python 3.8+
- 無外部 API 依賴（純本地分析）

## 觸發詞

當用戶提及以下詞彙時，自動調用本 Skill：
- 「完本檢測」
- 「小說檢查」
- 「情節漏洞」
- 「人物一致性」
- 「伏筆回收」
