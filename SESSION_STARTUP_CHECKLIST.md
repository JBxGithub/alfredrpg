# Session Startup Checklist

> **用途**: 每次session啟動時的強制讀取清單  
> **版本**: v1.0  
> **更新日期**: 2026-03-26

---

## 強制讀取順序

| 順序 | 檔案 | 用途 | 狀態 |
|------|------|------|------|
| 1 | `SOUL.md` | 身份確認（呀鬼/Alfred） | ⬜ |
| 2 | `USER.md` | 主人偏好（Burt/靚仔） | ⬜ |
| 3 | `MEMORY.md` | 核心準則與重要記憶 | ⬜ |
| 4 | `FutuTradingBot-STATUS.md` | 專案狀態（如存在） | ⬜ |
| 5 | `memory/YYYY-MM-DD.md` | 今日對話記錄 | ⬜ |
| 6 | `SKILL_PROTOCOL.md` | 技能調用協議 | ⬜ |

---

## 啟動後回報模板

```
🧐 啟動完成。已讀取：
✅ SOUL.md
✅ USER.md
✅ MEMORY.md
✅ FutuTradingBot-STATUS.md (或檔案不存在)
✅ memory/YYYY-MM-DD.md
✅ SKILL_PROTOCOL.md

請指示下一步行動。
```

---

## 重要準則

### 絕對禁止
- ❌ 自行重啟session（必須得到主人明確指令）
- ❌ 跳過任何讀取項目
- ❌ 未回報即開始工作

### 必須執行
- ✅ 完整讀取所有6項檔案
- ✅ 向主人回報讀取狀態
- ✅ 等待指示後才行動

---

## Context監控

- **閾值**: 70%
- **行動**: 達到時立即通知主人
- **通知內容**: "Context已達70%，請指示如何操作（繼續/總結/存檔）"

---

*此清單確保每次啟動都有完整記憶連貫性。*
