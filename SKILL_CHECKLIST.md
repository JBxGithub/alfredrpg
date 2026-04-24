# 技能調用前綴檢查表

> 每次使用技能前，強制執行以下檢查

## 檢查流程（必須依序執行）

### Step 1: 技能存在檢查
```
問：我要用嘅技能係咪存在？
→ 執行：openclaw skills list | findstr <skill-name>
→ 如不存在：通知用戶技能未安裝
```

### Step 2: 技能路徑確認
```
問：我知唔知道呢個技能嘅正確路徑？
→ 檢查：SKILL_PROTOCOL.md 或 AGENTS.md
→ 如唔確定：執行 openclaw skills list 搵路徑
```

### Step 3: 依賴檢查
```
問：呢個技能需要咩依賴？
→ 檢查：skill/SKILL.md 入面嘅 Prerequisites
→ 如缺依賴：先安裝依賴
```

### Step 4: 執行模板確認
```
問：我有正確嘅執行命令嗎？
→ 檢查：SKILL_PROTOCOL.md 入面嘅「常用執行模板」
→ 如唔確定：讀取 skill/SKILL.md
```

---

## 常見技能快速檢查

### 桌面控制 (desktop-control-win)
- [ ] 路徑：`~/openclaw_workspace/skills/desktop-control-win/`
- [ ] 腳本位置：`scripts/app-control.ps1`, `input-sim.ps1`
- [ ] 執行方式：`powershell -ExecutionPolicy Bypass -File "..."`

### 瀏覽器控制 (browser-automation)
- [ ] Chrome Relay 狀態：`browser status --profile chrome-relay`
- [ ] 開啟 URL：`browser open <url> --profile chrome-relay`
- [ ] 執行 JS：`browser act --profile chrome-relay --kind evaluate --fn "..."`

### 網絡搜尋
- [ ] 第一層：Grok → Agent Browser → web_fetch
- [ ] 第二層：Tavily Search → Parallel.ai
- [ ] API Key：檢查 `openclaw config get skills.entries.<skill>.apiKey`

---

## 錯誤處理流程

### 如果技能路徑錯誤：
1. 執行 `openclaw skills list` 搵正確路徑
2. 更新 `SKILL_PROTOCOL.md`
3. 記錄於 `memory/YYYY-MM-DD.md`
4. 重新執行

### 如果 Browser Relay 未連接：
1. 通知用戶啟動 Chrome
2. 點擊 OpenClaw Browser Relay 擴充功能
3. 等待連接後再試

### 如果 API Key 無效：
1. 檢查 `openclaw config get skills.entries.<skill>.apiKey`
2. 如缺失：通知用戶設定 API Key
3. 或使用其他替代工具

---

## 強制執行聲明

**我承諾：**
每次使用技能前，必定執行以上檢查流程。
如跳過檢查導致錯誤，立即記錄並修正。

簽署：呀鬼 (Alfred)
日期：2026-03-23
