# 核心技能強制載入清單

> **用途**: 這些 Skills 每次啟動必須讀取，不可遺忘
> **更新日期**: 2026-04-06
> **版本**: v1.0

---

## 第一層：系統級（必須載入）

| 技能名稱 | 路徑 | 用途 | 狀態 |
|---------|------|------|------|
| desktop-control-win | `~/openclaw_workspace/skills/desktop-control-win/` | Windows桌面控制 | 必載 |
| browser-automation | `~/openclaw_workspace/skills/browser-automation/` | 瀏覽器自動化 | 必載 |
| web-content-fetcher | `~/openclaw_workspace/skills/web-content-fetcher/` | 繞過Cloudflare | 必載 |
| novel-completion-checker | `~/openclaw_workspace/skills/novel-completion-checker/` | 完本檢測 | 必載 |

## 第二層：常用（按需載入）

| 技能名稱 | 路徑 | 用途 | 觸發詞 |
|---------|------|------|--------|
| excel-xlsx | `~/openclaw_workspace/skills/excel-xlsx/` | Excel處理 | 「Excel」「表格」「xlsx」|
| pdf | `~/openclaw_workspace/skills/pdf/` | PDF處理 | 「PDF」「發票」「帳單」|
| liang-tavily-search | `~/openclaw_workspace/skills/liang-tavily-search/` | Tavily搜尋 | 「搜尋」「查詢」「研究」|
| parallel | `~/openclaw_workspace/skills/parallel/` | Parallel.ai深度研究 | 「深度研究」「詳細分析」|
| github-research | `~/openclaw_workspace/skills/github-research/` | GitHub專案搜尋 | 「GitHub」「開源」「repo」|

## 載入驗證流程

啟動後必須報告：
```
🧐 啟動完成。已讀取：
✅ SOUL.md
✅ USER.md
✅ MEMORY.md
✅ MEMORY_SYNC_PROTOCOL.md
✅ FutuTradingBot-STATUS.md
✅ memory/YYYY-MM-DD.md (過去14天)
✅ SKILL_PROTOCOL.md
✅ CORE_SKILLS.md

**核心技能驗證:**
✅ desktop-control-win
✅ browser-automation
✅ web-content-fetcher
✅ novel-completion-checker

**記憶同步驗證:**
- 檢查 memory/YYYY-MM-DD.md 時間戳: [顯示時間]
- 讀取範圍: [今天] → [14天前]
- 狀態: [同步/需更新]

請指示下一步行動。
```

## 缺失處理

| 情況 | 處理方式 |
|------|---------|
| 核心技能路徑不存在 | 立即報告，標記為 🔴 缺失 |
| 常用技能路徑不存在 | 記錄警告，標記為 ⚠️ 可選缺失 |
| 新增技能未列入 | 更新本清單，記錄於 memory/YYYY-MM-DD.md |

## 更新日誌

| 日期 | 更新內容 |
|------|---------|
| 2026-04-06 | 初始版本，建立核心技能強制載入機制 |
