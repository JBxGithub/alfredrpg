# Alfred Daily Briefing + Dashboard Sync (整合版)
# Agent Turn Message for OpenCode ACP
# 執行時間: 每日 08:00 (Asia/Hong_Kong)

---

## 🎯 任務指令

執行 **Alfred Daily Briefing + Dashboard Sync (整合版)** Cron Job，將原本的兩個 Cron Job 整合為一個。

---

## 📋 執行步驟

### 步驟 1: Dashboard Daily Sync

1. **檢查儀表板狀態**
   - 檢查 https://jbxgithub.github.io/alfredrpg/dashboard.html
   - 檢查 http://127.0.0.1:8080 (FutuTradingBot)
   - 檢查 http://127.0.0.1:8000/docs (DeFi Dashboard API)
   - 記錄每個儀表板的狀態和響應時間

2. **更新系統監控數據**
   - 收集 CPU 使用率
   - 收集記憶體使用率
   - 收集磁碟使用率
   - 記錄系統運行時間

3. **同步安全檢查結果**
   - 執行快速安全掃描
   - 檢查是否有新的安全警告
   - 更新安全評分

4. **檢查組件健康狀況**
   - Gateway: 檢查網關狀態
   - WhatsApp: 檢查 WhatsApp 連接
   - Hooks: 檢查 Webhooks
   - Dashboard: 檢查儀表板
   - FutuTradingBot: 檢查交易機器人
   - DeFi Dashboard: 檢查 DeFi 儀表板

### 步驟 2: Daily Briefing

1. **讀取記憶文件**
   - 讀取 memory/YYYY-MM-DD.md (今日日誌)
   - 讀取 memory/YYYY-MM-DD-1.md (昨日日誌)
   - 讀取 MEMORY.md (長期記憶)
   - 讀取 project-states/FutuTradingBot-STATUS.md
   - 讀取 HEARTBEAT.md

2. **生成每日摘要報告**
   - 提取昨日重要事件
   - 提取今日待辦事項
   - 檢查專案狀態更新
   - 檢查系統健康狀況

3. **整理報告內容**
   - 系統狀態摘要
   - 專案進度更新
   - 待辦事項列表
   - 異常警告 (如有)
   - Cron Job 執行狀態

### 步驟 3: 發送報告

1. **格式化報告**
   - 使用繁體中文
   - 包含表情符號
   - 結構化顯示

2. **發送 WhatsApp 通知**
   - 收件人: +85263931048
   - 發送完整報告

---

## 📝 報告模板

```
🤖 **Alfred Daily Briefing + Dashboard Sync**
📅 {DATE} ({DAY_OF_WEEK}) | ⏰ {TIME} | 📍 Asia/Hong_Kong

---

### 📊 系統狀態

🎮 **AlfredRPG 網站**
- 狀態: {STATUS}
- 網址: https://jbxgithub.github.io/alfredrpg/dashboard.html
- 安全評分: {SCORE}/100

📈 **FutuTradingBot**
- 狀態: {STATUS}
- 下一步: {NEXT_ACTION}
- Realtime Bridge: ws://127.0.0.1:8765

🌐 **DeFi Dashboard**
- 狀態: {STATUS}
- 後端: localhost:8000
- 前端: localhost:3001

🛠️ **系統工具**
- AAT v2.0: {STATUS}
- AMS v2.1: {STATUS}
- 呀鬼瀏覽器: {STATUS}

---

### 📈 系統監控

- 💻 CPU: {CPU_USAGE}%
- 🧠 記憶體: {MEMORY_USAGE}%
- 💾 磁碟: {DISK_USAGE}%
- ⏱️ 運行時間: {UPTIME}

---

### 📅 昨日重點 ({YESTERDAY})

{YESTERDAY_EVENTS}

---

### 🎯 今日待辦

**🔴 P1 (高優先級)**:
- [ ] {TODO_1}
- [ ] {TODO_2}
- [ ] {TODO_3}

**🟡 P2 (中優先級)**:
- [ ] {TODO_4}
- [ ] {TODO_5}
- [ ] {TODO_6}

**🟢 P3 (低優先級)**:
- [ ] {TODO_7}
- [ ] {TODO_8}

---

### ⚠️ 異常警告

{WARNINGS}

---

### 🔧 組件狀態

- Gateway: {STATUS}
- WhatsApp: {STATUS}
- Hooks: {STATUS}
- Dashboard: {STATUS}
- FutuTradingBot: {STATUS}
- DeFi Dashboard: {STATUS}

---

### ⏰ Cron Job 狀態

| Job | 排程 | 狀態 |
|-----|------|------|
| Alfred Daily Briefing + Sync | 每日 08:00 | ✅ 正常 |

---

*報告由 Alfred 整合版 Cron Job 生成*
*版本: 2.0.0 | 執行時間: {EXECUTION_TIME}*
*下次執行: 明日 08:00*
```

---

## 🔧 技術細節

- **執行時間**: 每日 08:00 (Asia/Hong_Kong)
- **執行方式**: OpenCode ACP (agentId: opencode)
- **通知方式**: WhatsApp (+85263931048)
- **報告語言**: 繁體中文
- **版本**: 2.0.0 (整合版)

---

## 📁 相關檔案

- 配置檔案: `cron/alfred-daily-briefing.yaml`
- 執行腳本: `cron/alfred-daily-briefing.ps1`
- Agent Turn: `cron/alfred-daily-briefing-agent-turn.md`
- 報告輸出: `reports/daily-briefing-YYYY-MM-DD.md`

---

## 🚀 執行指令

```json
{
  "agentId": "opencode",
  "message": "執行 Alfred Daily Briefing + Dashboard Sync (整合版) Cron Job。請按照 cron/alfred-daily-briefing-agent-turn.md 的步驟執行，完成後發送報告到 WhatsApp +85263931048。",
  "priority": "high"
}
```
