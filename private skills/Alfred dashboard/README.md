# Alfred 統一安全儀表板

## 快速連結

- 🌐 **線上儀表板**: https://jbxgithub.github.io/alfredrpg/dashboard.html
- 📁 **GitHub Repo**: https://github.com/JBxGithub/alfredrpg

## 檔案結構

```
Alfred dashboard/
├── dashboard.html              # 主儀表板 (33KB)
├── sync-dashboard.js           # 同步腳本 (v2.2 安全加固版)
├── SKILL.md                    # 技能文檔
├── README.md                   # 本文件
└── cron/                       # Cron Job 配置
    ├── alfred-daily-briefing.ps1         # PowerShell 執行腳本
    ├── alfred-daily-briefing.yaml        # 配置文件
    └── alfred-daily-briefing-agent-turn.md   # ACP Agent Turn
```

## 功能特性

- 📊 **5個標籤頁面**: 總覽、安全檢查、系統監控、Cron Jobs、組件狀態
- 🔄 **每日自動同步**: 每日 08:00 自動更新
- 🛡️ **安全加固**: 修復 10 個安全漏洞
- 📱 **WhatsApp 通知**: 同步完成後發送報告

## 使用方法

### 手動執行同步

```powershell
cd "C:\Users\BurtClaw\openclaw_workspace\private skills\Alfred dashboard"
node sync-dashboard.js
```

### 檢查儀表板狀態

```powershell
cd "C:\Users\BurtClaw\openclaw_workspace\private skills\Alfred dashboard\cron"
.\alfred-daily-briefing.ps1 -TestMode
```

## 系統要求

- Node.js v18+
- PowerShell v5.1+
- GITHUB_TOKEN 環境變數

## 版本資訊

- **版本**: v3.0.0
- **發布日期**: 2026-04-18
- **作者**: Alfred (for Burt only)
