# ClawTrade Pro - 完整交易系統

> **專案代號**: CTP-001  
> **版本**: v1.0.0  
> **最後更新**: 2026-04-04  
> **狀態**: 🟢 **開發中**

---

## 🎯 專案概述

ClawTrade Pro 是一個全自動化交易系統，整合 Futu API、Investing.com 數據、風險管理、WhatsApp 通知和定時任務。

### 核心模塊

| 模塊 | 描述 | 狀態 |
|------|------|------|
| trading-core | Futu API + Investing.com 數據獲取 | 🔄 開發中 |
| tqqq-momentum | TQQQ 動量策略 + 回測引擎 | 🔄 開發中 |
| risk-manager | 風險監控 + 止損止盈 | 🔄 開發中 |
| whatsapp-notifier | WhatsApp 通知系統 | ✅ 已存在 |
| heartbeat | 系統心跳監控 | 🔄 開發中 |
| cron-jobs | 定時交易任務 | 🔄 開發中 |
| database | SQLite 數據存儲 | 🔄 開發中 |

---

## 📁 專案結構

```
clawtrade-pro/
├── skills/
│   ├── trading-core/
│   │   ├── SKILL.md
│   │   ├── futu_client.py
│   │   ├── investing_client.py
│   │   └── data_sync.py
│   ├── tqqq-momentum/
│   │   ├── SKILL.md
│   │   ├── strategy.py
│   │   ├── backtest.py
│   │   └── signals.py
│   ├── risk-manager/
│   │   ├── SKILL.md
│   │   ├── risk_check.py
│   │   ├── position_manager.py
│   │   └── stop_loss.py
│   ├── whatsapp-notifier/
│   │   └── (已存在)
│   ├── heartbeat/
│   │   ├── SKILL.md
│   │   └── heartbeat.py
│   └── cron-jobs/
│       ├── SKILL.md
│       └── scheduler.py
├── database/
│   ├── schema.sql
│   └── db_manager.py
├── config/
│   ├── trading.yaml
│   └── secrets.yaml
├── tests/
│   └── test_suite.py
└── README.md
```

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置環境

```bash
cp config/secrets.yaml.example config/secrets.yaml
# 編輯 secrets.yaml 填入你的 API 密鑰
```

### 3. 初始化數據庫

```bash
python database/db_manager.py --init
```

### 4. 啟動系統

```bash
python main.py
```

---

## 📊 開發進度

| 日期 | 進度 |
|------|------|
| 2026-04-04 | 專案啟動，開始統籌開發 |

---

*此檔案為 ClawTrade Pro (CTP-001) 的統一狀態記錄。*
