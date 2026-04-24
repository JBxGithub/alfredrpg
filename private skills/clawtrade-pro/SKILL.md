---
name: clawtrade-pro
description: 通用股票交易框架，支持任意股票和多種策略，包含完整的研究、回測、交易執行流程
metadata:
  openclaw:
    version: "2.0.0"
    author: "ClawTeam"
    category: "trading"
    location: "private skills/clawtrade-pro"
---

# ClawTrade Pro - 通用股票交易框架 v2.0

## 概述

ClawTrade Pro 是一個完整的股票交易生態系統，包含研究、策略開發、回測驗證、風險管理、自動交易執行全流程。

## 系統架構（更新後）

```
private skills/clawtrade-pro/
│
├── 核心模組（運行時必需）
│   ├── core/                    # Futu API 封裝、數據源管理
│   ├── strategies/              # 策略基類 + 具體策略
│   │   ├── base.py              # BaseStrategy 基類
│   │   ├── momentum.py          # 通用動量策略
│   │   ├── tqqq_momentum/       # TQQQ 專用動量策略
│   │   └── external/            # 外部策略擴展
│   ├── engine/                  # 策略引擎
│   ├── risk/                    # 風險管理
│   ├── notify/                  # 通知系統（WhatsAppNotifier）
│   ├── automation/              # 自動化
│   │   ├── cron_jobs/           # 定時任務（Scheduler, ScheduledTask）
│   │   └── heartbeat/           # 心跳監控
│   ├── trading-core/            # 交易核心
│   ├── config/                  # 配置檔案
│   └── modules/                 # 其他模組
│
├── 研究開發（策略研發使用）
│   ├── research/                # 研究報告
│   │   ├── TQQQ_Research_Report.md
│   │   └── TQQQ_ZScore_Strategy_Optimization_Report.md
│   ├── docs/                    # 系統設計文檔
│   │   ├── CLAWTRADE_ARCHITECTURE.md
│   │   └── qqq_tqqq_arbitrage_system_design.md
│   ├── backtests/               # 回測腳本
│   │   ├── tqqq_tmh_backtest.py
│   │   └── tqqq_tmh_backtest_v2.py
│   ├── scripts/                 # 分析工具
│   │   ├── analyze_qqq_tqqq.py
│   │   ├── check_futu_account.py
│   │   ├── directional_strategy_analysis.py
│   │   ├── get_qqq_tqqq_data.py
│   │   └── tqqq_statistical_analysis.py
│   └── data/                    # 歷史數據（CSV）
│       ├── qqq_history.csv
│       ├── tqqq_history.csv
│       └── ...
│
└── main.py                      # 主程序入口
```

## 正確使用方法

### 1. 匯入核心模組（優先順序）

```python
import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/clawtrade-pro')

# 核心交易模組
from core.trading_core import FutuTradingCore
from strategies.base import BaseStrategy
from engine.strategy_engine import StrategyEngine
from risk.risk_manager import RiskManager
from notify.notifier import WhatsAppNotifier

# 具體策略
from strategies.tqqq_momentum import TQQQMomentumStrategy

# 自動化
from automation.cron_jobs.cron_jobs import Scheduler, ScheduledTask
```

### 2. 使用策略

```python
# 創建策略實例
strategy = TQQQMomentumStrategy(config={
    'zscore_threshold': 1.65,
    'rsi_overbought': 70,
    'rsi_oversold': 30
})

# 生成信號
signal = strategy.generate_signal(data)
```

### 3. 執行回測

```python
# 使用 backtests/ 目錄下的腳本
# 或者：
python private skills/clawtrade-pro/backtests/tqqq_tmh_backtest.py
```

### 4. 運行主程序

```bash
cd "private skills/clawtrade-pro"
python main.py --mode live    # 實盤交易
python main.py --mode backtest --symbol TQQQ  # 回測
```

## 關鍵類別名稱（必須記住）

| 模組 | 正確類別名 | 常見錯誤 |
|------|-----------|---------|
| core.trading_core | FutuTradingCore | TradingCore |
| strategies.base | BaseStrategy | StrategyBase |
| engine.strategy_engine | StrategyEngine | - |
| risk.risk_manager | RiskManager | - |
| notify.notifier | WhatsAppNotifier | Notifier |
| strategies.tqqq_momentum | TQQQMomentumStrategy | - |
| automation.cron_jobs | Scheduler, ScheduledTask | trading_cron |

## 檔案位置規則

| 類型 | 位置 | 說明 |
|------|------|------|
| 研究報告 | research/ | Markdown 格式 |
| 系統設計 | docs/ | 架構文檔 |
| 回測腳本 | backtests/ | Python 腳本 |
| 分析工具 | scripts/ | 獨立運行工具 |
| 歷史數據 | data/ | CSV 格式 |
| 核心模組 | core/, strategies/, engine/ 等 | 運行時匯入 |

## 依賴安裝

```bash
pip install schedule  # cron_jobs 必需
pip install futu-api  # 富途 API
pip install pandas numpy ta-lib  # 數據分析
```

## 常見錯誤

1. **ImportError: cannot import name 'TradingCore'**
   - 正確：`from core.trading_core import FutuTradingCore`
   - 錯誤：`from core.trading_core import TradingCore`

2. **ModuleNotFoundError: No module named 'strategies.tqqq_momentum'**
   - 確保使用 `from strategies.tqqq_momentum import TQQQMomentumStrategy`
   - 目錄名是 `tqqq_momentum`（下劃線），不是 `tqqq-momentum`

3. **ModuleNotFoundError: No module named 'automation.cron_jobs'**
   - 確保目錄名是 `cron_jobs`（下劃線），不是 `cron-jobs`

## 更新記錄

| 版本 | 日期 | 更新內容 |
|------|------|---------|
| 2.0.0 | 2026-04-09 | 重構結構，新增 research/docs/backtests/scripts/data 目錄，整合所有交易相關檔案 |
| 1.0.0 | 2026-04-04 | 初始版本 |

## 授權

Apache 2.0
