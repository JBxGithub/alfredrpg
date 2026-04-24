# 技能調用代理 v1.0

> 自動攔截技能調用請求，強制執行檢查流程

## 使用流程

### 當用戶提出需求時：

**Step 1: 需求分析**
```
用戶說：「幫我搜尋...」
→ 識別為「搜尋需求」
→ 觸發搜尋工具鏈
```

**Step 2: 工具選擇（自動執行）**
```
根據 SKILL_PROTOCOL.md 優先級：
1. 檢查 Browser Relay 狀態
2. 如可用 → 使用 browser 工具
3. 如不可用 → 使用 web_fetch / Tavily Search
```

**Step 3: 執行前檢查**
```
- [ ] 確認工具可用
- [ ] 確認路徑/配置正確
- [ ] 確認 API Key（如需要）
```

**Step 4: 執行並記錄**
```
- 執行工具調用
- 記錄結果
- 如失敗 → 嘗試替代方案
```

---

## 常見需求 → 工具映射

| 用戶需求關鍵詞 | 自動選擇工具 | 檢查項目 |
|--------------|------------|---------|
| 「搜尋」「查詢」「搵」 | 1. browser (Grok)<br>2. web_fetch<br>3. tavily-search | Browser Relay 狀態 |
| 「控制電腦」「點擊」「輸入」 | desktop-control-win | PowerShell 執行權限 |
| 「截圖」「影相」 | screen-info.ps1 | 輸出路徑權限 |
| 「問Grok」「問鬼王」 | browser (Grok) | Chrome Relay 連接 |
| 「研究」「深度分析」 | Parallel.ai / Tavily | API Key 有效性 |

---

## 自動修復機制

### 如果 Browser Relay 未連接：
```
1. 通知用戶：「請啟動 Chrome 並點擊 OpenClaw Browser Relay」
2. 等待 10 秒後重試
3. 如仍失敗 → 切換到替代工具（web_fetch / Tavily）
```

### 如果技能路徑錯誤：
```
1. 執行 openclaw skills list 搵正確路徑
2. 更新 SKILL_PROTOCOL.md
3. 重新執行
```

### 如果 API Key 無效：
```
1. 通知用戶 API Key 問題
2. 切換到免費替代工具
3. 記錄於 memory/YYYY-MM-DD.md
```

---

## 執行模板

### 模板 1: 搜尋任務
```
用戶：「幫我搜尋 AI Agent 商業化」

執行：
1. browser status --profile chrome-relay
2. 如 running: browser open "https://grok.com" --profile chrome-relay
3. 如 not running: 
   → 通知用戶啟動 Chrome Relay
   → 或使用 tavily-search "AI Agent 商業化"
```

### 模板 2: 桌面控制任務
```
用戶：「幫我 focus Chrome」

執行：
1. 確認路徑: ~/openclaw_workspace/skills/desktop-control-win/
2. 執行: app-control.ps1 -Action focus -Target "Chrome"
3. 如失敗: 檢查 PowerShell 執行權限
```

### 模板 3: 網頁內容提取
```
用戶：「讀取呢個網址 https://...」

執行：
1. 嘗試 web_fetch <url>
2. 如失敗（Cloudflare）: 使用 web-content-fetcher
3. 如仍失敗: 使用 browser snapshot
```

---

## 記錄要求

每次技能調用後，記錄於 memory/YYYY-MM-DD.md：
```markdown
## 技能調用記錄
- **時間**: 2026-03-23 10:30
- **需求**: 搜尋 AI Agent 商業化
- **使用工具**: browser (Grok)
- **結果**: 成功 / 失敗
- **備註**: Browser Relay 正常 / 需啟動 Chrome
```
