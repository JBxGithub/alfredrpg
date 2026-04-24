# 技能發現協議 v2.0

> 每次啟動自動重建技能地圖，確保「肌肉記憶」不遺失
> 最後更新：2026-04-09

---

## 📊 技能總覽（96個技能）

### 分類統計
| 類別 | 數量 | 核心技能 |
|------|------|---------|
| 開發工具 | 15+ | coding-agent, claude-code-cli, opencode-controller |
| 數據分析 | 10+ | Data Analysis, stock-monitor, clawtrade-pro |
| 自動化/控制 | 12+ | desktop-control, browser, Agent Browser |
| 通訊/通知 | 8+ | whatsapp-notifier, xurl, agenthub |
| 文件處理 | 8+ | PDF全家桶, Excel/XLSX, Spreadsheet |
| 記憶/知識 | 5+ | alfred-memory-system, obsidian, session-logs |
| 多代理 | 3+ | multi-agent-orchestrator, multi-agent-chat |
| 金融/交易 | 5+ | clawtrade-pro, polymarket-analysis |
| 監控/通知 | 6+ | pushover-notify, universal-notify, live-task-pulse |
| 其他 | 30+ | 各種專用工具 |

---

## 🎯 核心技能分類與使用規則

### 1️⃣ 寫程式/開發類

| 技能 | 觸發詞 | 使用方法 | 注意事項 |
|------|--------|----------|----------|
| **coding-agent** | 複雜coding、review PR、refactor | `sessions_spawn` with `runtime:"acp"` | 簡單修改直接用 edit，唔好 spawn |
| **claude-code-cli** | 寫code、大型refactor | `claude-code-cli --print --permission-mode bypassPermissions` | 複雜任務先用，簡單任務自己搞 |
| **opencode-controller** | 用Opencode寫程式 | 直接調用技能 | 同 claude-code-cli 二選一 |
| **github-ops** | 創建repo、push code、管理Release | 直接調用技能 | 全自動，無需干預 |
| **github-cli** | GitHub操作參考 | 查詢用，非執行 | 用於查詢gh命令語法 |
| **github-contribution** | 開源貢獻流程 | 直接調用技能 | fork到PR完整流程 |
| **github-issue-resolver** | 自動修復GitHub issues | 直接調用技能 | 有guardrails保護 |
| **git-workflows** | 高級git操作 | 直接調用技能 | rebase/bisect/worktrees等 |
| **github-actions-generator** | 生成CI/CD workflow | 直接調用技能 | 支持多種場景 |

**使用規則：**
1. 簡單修改（<10行）→ 直接用 `edit` 工具
2. 中等任務（10-100行）→ 自己讀寫，必要時用 `coding-agent`
3. 複雜任務（>100行/多文件）→ `claude-code-cli` 或 `opencode-controller`
4. GitHub相關 → `github-*` 系列技能

---

### 2️⃣ 搜尋/研究類

| 技能 | 觸發詞 | 使用方法 | 優先級 |
|------|--------|----------|--------|
| **web-content-fetcher** | 獲取網頁、bypass Cloudflare | `web-content-fetcher --url <url>` | ⭐⭐⭐ 第一選擇 |
| **web_fetch** | 已知URL抓取 | `web_fetch` 工具 | ⭐⭐⭐ 簡單直接 |
| **tavily-search** | 深度搜尋、研究 | `tavily-search` 工具 | ⭐⭐ 第二選擇 |
| **parallel** | 高精度研究 | `parallel` 工具 | ⭐⭐ 深度研究 |
| **github-research** | 搜尋開源項目 | 直接調用技能 | ⭐⭐⭐ GitHub專用 |
| **github-trending-cn** | GitHub趨勢 | 直接調用技能 | 監控熱門項目 |
| **blogwatcher** | 監控RSS/博客 | `blogwatcher` CLI | 自動追蹤更新 |
| **last30days** | 近30天趨勢研究 | 直接調用技能 | 社交媒體+新聞 |

**使用規則：**
1. 已知URL → `web_fetch` 或 `web-content-fetcher`
2. 關鍵詞搜尋 → `tavily-search`（第一層）→ `parallel`（第二層）
3. GitHub項目 → `github-research`
4. 趨勢/熱門 → `github-trending-cn` 或 `last30days`

---

### 3️⃣ 自動化/控制類

| 技能 | 觸發詞 | 使用方法 | 平台 |
|------|--------|----------|------|
| **desktop-control-win** | 控制Windows應用 | PowerShell scripts | Windows |
| **desktop_control** | 高級桌面自動化 | 直接調用技能 | Windows |
| **browser** | 瀏覽器自動化 | `browser` 工具 | 跨平台 |
| **Agent Browser** | 高級瀏覽器（Rust） | 直接調用技能 | 跨平台 |
| **windows-ui-automation** | Windows GUI自動化 | PowerShell | Windows |
| **tmux** | 遠程控制tmux | `tmux` 技能 | Linux/Mac |
| **mcporter** | MCP服務器管理 | `mcporter` CLI | 跨平台 |

**使用規則：**
1. Windows應用控制 → `desktop-control-win`
2. 網頁操作 → `browser`（簡單）→ `Agent Browser`（複雜）
3. 需要先開Chrome並啟動 Browser Relay

**Browser Relay 啟動流程：**
```
1. 檢查狀態: browser status --profile chrome-relay
2. 如未運行: 通知用戶啟動 Chrome 並點擊 OpenClaw Browser Relay
3. 連接後: browser open <url> --profile chrome-relay
4. 操作: browser act --profile chrome-relay --kind evaluate --fn "..."
```

---

### 4️⃣ 通訊/通知類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **whatsapp-notifier** | WhatsApp通知 | 直接調用技能 | 交易信號、風險警報 |
| **xurl** | Twitter/X操作 | `xurl` 工具 | 發推、回覆、DM |
| **agenthub** | Agent間通訊 | 直接調用技能 | AI代理互相聯繫 |
| **agentmail-integration** | Agent郵件 | 直接調用技能 | 專用郵箱 |
| **pushover-notify** | 手機推送 | `pushover-notify` | 緊急通知 |
| **universal-notify** | 多通道通知 | `universal-notify` | 統一通知接口 |
| **gog** | Google Workspace | 直接調用技能 | Gmail/Calendar/Drive |
| **outlook** | Outlook郵件 | 直接調用技能 | Microsoft郵件 |

**使用規則：**
1. WhatsApp → `whatsapp-notifier`（已配置）
2. 緊急通知 → `pushover-notify`
3. 郵件 → `gog`（Gmail）或 `outlook`

---

### 5️⃣ 文件處理類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **pdf** | PDF操作 | 直接調用技能 | 創建/合併/分割 |
| **pypdf** | PDF文本提取 | `pypdf` 工具 | 讀取PDF內容 |
| **pymupdf** | 高級PDF處理 | 直接調用技能 | 渲染/註解/提取圖片 |
| **PDF to Markdown** | PDF轉Markdown | 直接調用技能 | 保留表格 |
| **pdf-ocr** | 掃描PDF轉Word | 直接調用技能 | 中文OCR |
| **pdf-to-long-image** | PDF轉長圖 | 直接調用技能 | 多頁合併 |
| **nano-pdf** | 自然語言PDF編輯 | 直接調用技能 | 語音指令 |
| **Excel / XLSX** | Excel操作 | 直接調用技能 | 公式/格式 |
| **microsoft-excel** | Excel API | 直接調用技能 | OneDrive Excel |
| **Spreadsheet** | 表格數據 | 直接調用技能 | 通用表格 |

**使用規則：**
1. 讀取PDF → `pypdf`（簡單）或 `PDF to Markdown`（複雜）
2. 掃描件 → `pdf-ocr`
3. Excel → `Excel / XLSX`（本地）或 `microsoft-excel`（雲端）

---

### 6️⃣ 記憶/知識類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **alfred-memory-system** | 統一記憶管理 | Python import | AMS核心 |
| **obsidian** | Obsidian筆記 | 直接調用技能 | 知識庫 |
| **session-logs** | Session日誌搜索 | `session-logs` | 歷史對話 |
| **memory-setup** | 記憶配置 | 直接調用技能 | 設置指南 |
| **capability-evolver** | 自進化引擎 | 直接調用技能 | 自動改進 |

**使用規則：**
1. 每次啟動自動初始化 AMS
2. 重要資訊寫入 `memory/YYYY-MM-DD.md`
3. 長期記憶更新 `MEMORY.md`

---

### 7️⃣ 多代理類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **multi-agent-orchestrator** | 多代理團隊 | 直接調用技能 | 設計代理團隊 |
| **multi-agent-chat** | 多代理對話 | 直接調用技能 | Discord群聊 |
| **subagent-dashboard** | 子代理監控 | Web dashboard | 監控進度 |
| **live-task-pulse** | 任務進度追蹤 | 自動啟用 | 實時通知 |

**使用規則：**
1. 複雜任務 → 分拆給子代理
2. 監控進度 → `live-task-pulse` + `subagent-dashboard`

---

### 8️⃣ 金融/交易類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **clawtrade-pro** | 股票交易框架 | 直接調用技能 | 通用交易 |
| **stock-monitor** | 股票監控 | 直接調用技能 | 實時監控 |
| **stock-watcher** | 股票觀察列表 | 直接調用技能 | 自選股 |
| **stock_study** | 股票研究 | 直接調用技能 | 深度分析 |
| **stock-strategy-backtester** | 策略回測 | 直接調用技能 | 驗證策略 |
| **polymarket-analysis** | 預測市場分析 | 直接調用技能 | Polymarket |
| **data-anomaly-detector** | 異常檢測 | 直接調用技能 | 數據異常 |

**使用規則：**
1. 監控 → `stock-monitor`
2. 研究 → `stock_study`
3. 回測 → `stock-strategy-backtester`
4. 交易 → `clawtrade-pro`

---

### 9️⃣ 數據分析類

| 技能 | 觸發詞 | 使用方法 | 用途 |
|------|--------|----------|------|
| **Data Analysis** | 數據分析 | 直接調用技能 | 分析+可視化 |
| **data-analyst** | 數據分析任務 | 直接調用技能 | 專業分析 |
| **Dashboard** | 儀表板 | 直接調用技能 | 自定義儀表板 |
| **computer-vision-expert** | 電腦視覺 | 直接調用技能 | YOLO/SAM |
| **summarize** | 內容摘要 | `summarize` CLI | 網頁/PDF/影片 |
| **video-frames** | 影片幀提取 | `video-frames` | ffmpeg操作 |
| **FFmpeg** | 影音處理 | `FFmpeg` 技能 | 專業處理 |

---

### 🔟 其他重要技能

| 技能 | 觸發詞 | 使用方法 |
|------|--------|----------|
| **clawhub** | 安裝/更新技能 | `npx clawhub` |
| **skill-creator** | 創建技能 | 直接調用技能 |
| **find-skills** | 搜索技能 | 直接調用技能 |
| **healthcheck** | 安全檢查 | 直接調用技能 |
| **cron** | 定時任務 | `cron` 工具 |
| **proactive-agent** | 主動代理 | 直接調用技能 |
| **self-improvement** | 自我改進 | 自動觸發 |
| **humanizer** | 去除AI痕跡 | 直接調用技能 |
| **weather** | 天氣查詢 | `weather` 工具 |
| **Markdown** | Markdown生成 | 直接調用技能 |
| **logging-observability** | 日誌監控 | 直接調用技能 |
| **Monitoring** | 系統監控 | 直接調用技能 |
| **openclaw-dashboard** | OpenClaw儀表板 | Web UI |
| **Webhook** | Webhook處理 | 直接調用技能 |
| **webhook-send** | 發送Webhook | `webhook-send` |
| **safe-exec** | 安全執行 | 直接調用技能 |
| **Screenshot** | 截圖 | `Screenshot` 技能 |
| **skill-sandbox** | 技能沙盒 | 自動使用 |
| **skill-vetting** | 技能審查 | 直接調用技能 |
| **document-skills** | 技能文檔 | 直接調用技能 |
| **burt-youtube-analyzer** | YouTube分析 | 直接調用技能 |
| **accounting-bot** | 自動記帳 | 直接調用技能 |
| **creditclaw-*** | CreditClaw系統 | 直接調用技能 |
| **red-alert** | 紅色警報 | 直接調用技能 |
| **polymarket-analysis** | Polymarket分析 | 直接調用技能 |

---

## ⚡ 技能選擇決策樹

```
任務類型？
├── 寫程式
│   ├── 簡單修改 (<10行) → edit工具
│   ├── 中等任務 → coding-agent
│   └── 複雜項目 → claude-code-cli / opencode-controller
├── 搜尋/研究
│   ├── 已知URL → web_fetch / web-content-fetcher
│   ├── 關鍵詞 → tavily-search → parallel
│   └── GitHub → github-research
├── 自動化
│   ├── Windows應用 → desktop-control-win
│   ├── 網頁操作 → browser → Agent Browser
│   └── 多步驟流程 → 組合使用
├── 通訊
│   ├── WhatsApp → whatsapp-notifier
│   ├── 郵件 → gog / outlook
│   └── 通知 → pushover-notify / universal-notify
├── 文件
│   ├── PDF讀取 → pypdf / PDF to Markdown
│   ├── PDF編輯 → nano-pdf / pymupdf
│   └── Excel → Excel / XLSX
├── 金融
│   ├── 監控 → stock-monitor
│   ├── 研究 → stock_study
│   └── 交易 → clawtrade-pro
└── 其他 → 查詢本協議
```

---

## 📝 技能使用日誌模板

記錄於：`memory/skill-usage-log.md`

```markdown
| 時間 | 技能 | 任務 | 效果 | 備註 |
|------|------|------|------|------|
| HH:MM | 技能名 | 做咩 | ✅/❌ | 特別注意 |
```

---

## 🔄 更新記錄

| 日期 | 更新內容 |
|------|---------|
| 2026-03-23 | 初始版本，建立技能發現協議 |
| 2026-04-09 | v2.0 - 完整分類96個技能，加入使用規則同決策樹 |
