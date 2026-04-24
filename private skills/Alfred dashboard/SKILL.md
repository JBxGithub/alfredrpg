---
name: alfred-dashboard
version: "3.0.0"
description: Alfred 統一安全儀表板 - 整合所有安全檢查和系統監控功能
author: Alfred (for Burt only)
private: true
---

# Alfred 統一安全儀表板 v3.0

> 「靚仔，你想睇咩數據，一個儀表板搞掂」

## 📊 功能概覽

Alfred 統一安全儀表板整合所有安全檢查和系統監控功能到單一界面。

### 5個標籤頁面

| 標籤 | 功能 |
|------|------|
| 📊 **總覽** | 安全評分、運行時間、Cron Jobs、快速連結 |
| 🔒 **安全檢查** | Repository、Secrets、部署、API 狀態 |
| 🖥️ **系統監控** | CPU/記憶體/磁碟、實時圖表 |
| ⏰ **Cron Jobs** | 6個 Cron Job 詳細資訊 |
| 🔧 **組件狀態** | 6個系統組件狀態 |

## 🚀 快速開始

### 網址
- **GitHub Pages**: https://jbxgithub.github.io/alfredrpg/dashboard.html

### 本地檔案結構
```
private skills/Alfred dashboard/
├── dashboard.html                    # 35 KB - 主儀表板
├── sync-dashboard.js                 # 5 KB - 同步腳本 (v3.0)
├── SKILL.md                          # 本文件
├── README.md                         # 讀我檔案
├── .env.example                      # 環境變數範例
├── start-sync.bat                    # 快速啟動腳本
├── cron/                             # Cron Job 配置
│   ├── alfred-daily-briefing.ps1          # PowerShell 腳本
│   ├── alfred-daily-briefing.yaml         # 配置文件
│   └── alfred-daily-briefing-agent-turn.md # ACP Agent Turn
├── logs/                             # 日誌目錄
├── backups/                          # 備份目錄
└── reports/                          # 報告目錄
    └── daily-briefing-YYYY-MM-DD.md  # 每日報告
```

## 🔄 每日同步流程

```
每日 08:00 (Asia/Hong_Kong)
    ↓
Cron Job 觸發 (ID: 5386f659-1310-41f6-8092-6f294bb7895f)
    ↓
OpenCode ACP 執行
    ↓
1. Dashboard Daily Sync
   - 檢查儀表板狀態
   - 更新系統監控數據
   - 同步安全檢查結果
   - 檢查組件健康狀況
    ↓
2. 安全儀表板數據同步
   - 執行 sync-dashboard.js
   - 讀取本地 dashboard.html
   - 上傳到 GitHub Pages
    ↓
3. Daily Briefing
   - 讀取記憶文件
   - 生成每日摘要
   - 發送 WhatsApp 報告 (+85263931048)
```

## 🛠️ 使用方法

### 手動執行同步

```powershell
# 方法1: 使用批次腳本
cd "C:\Users\BurtClaw\openclaw_workspace\private skills\Alfred dashboard"
.\start-sync.bat

# 方法2: 直接使用 Node.js
node sync-dashboard.js

# 方法3: 執行完整 Daily Briefing (測試模式)
powershell -ExecutionPolicy Bypass -File "cron\alfred-daily-briefing.ps1" -TestMode
```

### 環境變數設置

創建 `.env` 文件:
```
GITHUB_TOKEN=your_github_token_here
```

或設置系統環境變數:
```powershell
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your_token", "User")
```

## 📋 Cron Jobs (6個)

| # | 名稱 | 排程 | 功能 |
|---|------|------|------|
| 1 | 📝 每日日誌建立 | 每日 00:00 | 建立日誌 + 知識圖譜更新 |
| 2 | 🧠 Memory Dreaming | 每日 01:00 | 記憶同步 |
| 3 | 🎯 **Alfred Daily Briefing + Dashboard Sync** | 每日 08:00 | **整合版儀表板同步** |
| 4 | 📚 AMS Weekly Review | 每週一 09:00 | 每週學習回顧 |
| 5 | 🔧 Self-Improving Review | 每週一 09:30 | 自我改進回顧 |
| 6 | 💭 Monthly Vision | 每月 1日 09:00 | 每月願景提醒 |

## 🛡️ 安全特性

### sync-dashboard.js v3.0 功能
- ✅ **重試機制**: 最多 3 次嘗試
- ✅ **錯誤處理**: 完整的錯誤捕獲和日誌
- ✅ **Token 驗證**: 執行前檢查 GITHUB_TOKEN
- ✅ **超時控制**: HTTP 請求 10-30 秒超時
- ✅ **狀態報告**: 詳細的執行日誌

### PowerShell 腳本 v2.1 功能
- ✅ **系統監控**: CPU、記憶體、運行時間
- ✅ **健康檢查**: 驗證 GitHub Pages 狀態
- ✅ **報告生成**: Markdown 格式每日報告
- ✅ **WhatsApp 通知**: 自動發送到 +85263931048

## 🔧 系統要求

| 項目 | 要求 |
|------|------|
| **Node.js** | v18+ |
| **PowerShell** | v5.1+ |
| **環境變數** | `GITHUB_TOKEN` (GitHub Personal Access Token) |
| **時區** | Asia/Hong_Kong |
| **網絡** | 可訪問 GitHub API |

## 📝 更新日誌

### v3.0.0 (2026-04-18) - 當前版本
- 🎉 **統一安全儀表板正式發布**
- 📁 整理到 `private skills/Alfred dashboard/`
- 🔄 簡化 sync-dashboard.js (v3.0, 5KB)
- ✅ 測試通過：Dashboard Sync + Daily Briefing
- 📝 更新 Cron Job 路徑
- 🔧 修正 PowerShell 語法錯誤

### v2.2.0 (2026-04-18)
- 🔒 安全加固版
- 📝 添加詳細日誌記錄
- 💾 添加自動備份機制
- 🔍 添加健康檢查端點

### v2.1.0 (2026-04-18)
- 🐛 漏洞修復版本
- 🔄 添加錯誤重試機制
- 📊 添加數據驗證

### v2.0.0 (2026-04-18)
- ⏰ Cron Job 整合版
- 📱 WhatsApp 通知
- 📊 每日報告生成

## 🔗 相關連結

| 名稱 | 網址 |
|------|------|
| 🌐 線上儀表板 | https://jbxgithub.github.io/alfredrpg/dashboard.html |
| 📁 GitHub Repo | https://github.com/JBxGithub/alfredrpg |
| 📊 FutuTradingBot | http://127.0.0.1:8080 |
| 🌐 DeFi Dashboard | http://127.0.0.1:8000/docs |

## 📞 支援

如有問題，請檢查:
1. `logs/sync-YYYY-MM-DD.log` - 同步日誌
2. `reports/daily-briefing-YYYY-MM-DD.md` - 每日報告
3. 確保 `GITHUB_TOKEN` 已正確設置

---

*「靚仔，你想點，講句就得」- 呀鬼*  
*最後更新: 2026-04-18*
