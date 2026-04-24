# FutuTradingBot 系統架構總覽

> **最後更新**: 2026-04-07 21:30
> **版本**: 2.0.0 - MTF整合版
> **實盤交易密碼**: 011087 + Enter

---

## 📁 完整系統結構

```
fututradingbot/
│
├── 📄 核心檔案
│   ├── emergency_close.py          # 緊急平倉
│   ├── launcher.py                 # 系統啟動器
│   ├── main.py                     # 主入口
│   ├── test_mtf_v2_integration.py  # MTF測試
│   └── test_strategies_integration.py # 策略測試
│
├── 📁 archived/                    # 歸檔檔案
│   ├── root_scripts/               # 過期腳本
│   ├── strategies/                 # 舊策略
│   ├── tests/                      # 過期測試
│   └── backtest/                   # 舊回測
│
├── 📁 src/                         # 源代碼
│   │
│   ├── 📁 analysis/                # 分析模組 (5個)
│   │   ├── divergence_detector.py      # 背離檢測 ✅
│   │   ├── market_regime.py            # 市場狀態 ✅
│   │   ├── market_sentiment.py         # 情緒分析 ✅
│   │   ├── mtf_analyzer.py             # MTF分析器 ✅
│   │   └── stock_analysis.py           # 股票分析 ✅
│   │
│   ├── 📁 api/                     # API模組 (1個)
│   │   └── futu_client.py              # Futu API ✅
│   │
│   ├── 📁 backtest/                # 回測模組 (5個)
│   │   ├── analyze_2022.py             # 2022分析 ✅
│   │   ├── check_signals.py            # 信號檢查 ✅
│   │   ├── enhanced_backtest.py        # 增強回測 ✅
│   │   ├── quick_simulation.py         # 快速模擬 ✅
│   │   └── archived/                   # 舊回測 (35+檔案)
│   │
│   ├── 📁 config/                  # 配置模組 (1個)
│   │   └── settings.py                 # 系統配置 ✅
│   │
│   ├── 📁 core/                    # 核心引擎 (2個)
│   │   ├── bot.py                      # 交易機器人 ✅
│   │   └── risk_aware_engine.py        # 風險引擎 ✅
│   │
│   ├── 📁 dashboard/               # 儀表板 (2個)
│   │   ├── app.py                      # 主應用 ✅
│   │   └── app_stable.py               # 穩定版 ✅
│   │
│   ├── 📁 data/                    # 數據模組 (1個)
│   │   └── market_data.py              # 市場數據 ✅
│   │
│   ├── 📁 indicators/              # 指標模組 (3個)
│   │   ├── candlestick_patterns.py     # K線形態 ✅
│   │   ├── macd_v.py                   # MACD-V ✅
│   │   └── technical.py                # 技術指標 ✅
│   │
│   ├── 📁 ml/                      # 機器學習 (3個)
│   │   ├── feature_engineering.py      # 特徵工程 ✅
│   │   ├── model_trainer.py            # 模型訓練 ✅
│   │   └── signal_enhancer.py          # 信號增強 ✅
│   │
│   ├── 📁 monitoring/              # 監控模組 (1個)
│   │   └── monitor.py                  # 系統監控 ✅
│   │
│   ├── 📁 optimization/            # 優化模組 (1個)
│   │   └── strategy_optimizer.py       # 策略優化 ✅
│   │
│   ├── 📁 recorder/                # 記錄模組 (1個)
│   │   └── trade_recorder.py           # 交易記錄 ✅
│   │
│   ├── 📁 risk/                    # 風險模組 (3個)
│   │   ├── __init__.py
│   │   ├── risk_management.py          # 風險管理 ✅
│   │   └── risk_manager.py             # 風險管理器 ✅
│   │
│   ├── 📁 strategies/              # 策略模組 (12個)
│   │   ├── __init__.py
│   │   ├── backtest.py                 # 回測引擎 ✅
│   │   ├── base.py                     # 策略基類 ✅
│   │   ├── breakout.py                 # 突破策略 ✅
│   │   ├── enhanced_strategy.py        # 增強策略 ✅
│   │   ├── entry_generator.py          # 入場生成器 ✅
│   │   ├── flexible_arbitrage.py       # 套利策略 ✅
│   │   ├── momentum.py                 # 動量策略 ✅
│   │   ├── strategy_config.py          # 策略配置 ✅
│   │   ├── strategy_registry.py        # 策略註冊 ✅
│   │   ├── tqqq_long_short.py          # TQQQ策略 ✅
│   │   ├── trend_strategy.py           # 趨勢策略 ✅
│   │   └── zscore_strategy.py          # ZScore策略 ✅
│   │
│   └── 📁 utils/                   # 工具模組 (4個)
│       ├── error_handler.py            # 錯誤處理 ✅
│       ├── logger_config.py            # 日誌配置 ✅
│       ├── logger.py                   # 日誌工具 ✅
│       └── performance.py              # 性能工具 ✅
│
├── 📁 examples/                    # 示例 (4個)
│   ├── partial_profit_example.py
│   ├── risk_monitor_demo.py
│   ├── stock_analysis_example.py
│   └── strategy_examples.py
│
├── 📁 scripts/                     # 腳本 (2個)
│   ├── validate_strategy.py
│   └── validate_strategy_v2.py
│
├── 📁 simulation/                  # 模擬 (5個)
│   ├── backtest_2025.py
│   ├── paper_dashboard.py
│   ├── paper_dashboard_stable.py
│   ├── paper_trading_bridge.py
│   └── start_paper_dashboard.py
│
└── 📁 tests/                       # 測試 (11個)
    ├── test_basic.py
    ├── test_candlestick_patterns.py
    ├── test_config.py
    ├── test_connection.py
    ├── test_enhanced_strategy.py
    ├── test_indicators.py
    ├── test_phase4.py
    ├── test_risk_monitor.py
    ├── test_stock_analysis.py
    ├── test_strategy_engine.py
    └── test_zscore.py
```

---

## 🔧 核心功能模組

### 1. 三維分析框架
```
MTFAnalyzer (多時間框架)
├── 月線分析 (40%權重)
├── 週線分析 (35%權重)
├── 日線分析 (25%權重)
├── MACD-V整合
└── 背離檢測
```

### 2. 策略引擎
```
TradingBot
├── 策略管理 (8個活躍策略)
├── 風險檢查
├── 訂單執行
├── 持倉監控
└── 數據持久化
```

### 3. 風險管理
```
RiskAwareEngine
├── 資金風險檢查
├── 持倉風險檢查
├── 交易風險檢查
├── 部分獲利機制
└── 實時監控警報
```

### 4. ML增強
```
SignalEnhancer
├── 特徵工程 (52+特徵)
├── 模型預測
├── 信號融合
└── 動態權重調整
```

---

## 📊 活躍策略清單 (8個)

| 策略 | 類型 | MTF整合 | 狀態 |
|------|------|---------|------|
| TrendStrategy | 趨勢跟隨 | ✅ | 活躍 |
| TQQQLongShortStrategy | Z-Score多空 | ✅ | 活躍 |
| ZScoreStrategy | 均值回歸 | ✅ | 活躍 |
| BreakoutStrategy | 突破策略 | ✅ | 活躍 |
| FlexibleArbitrageStrategy | 靈活套利 | ✅ | 活躍 |
| MomentumStrategy | 動量策略 | ✅ | 活躍 |
| EnhancedStrategy | 多因子 | - | 活躍 |
| EntryGenerator | 入場生成 | - | 活躍 |

---

## 🔐 重要配置

### 實盤交易
- **密碼**: 011087
- **確認**: Enter鍵
- **環境**: REAL
- **市場**: US (NASDAQ)

### MTF參數
- 月線權重: 40%
- 週線權重: 35%
- 日線權重: 25%
- 最低評分: 60分

### 風險限制
- 單筆最大風險: 1%
- 每日最大虧損: 2%
- 總持倉風險: ≤4%
- 最大持倉數: 3筆

---

## 📈 系統統計

| 類別 | 數量 |
|------|------|
| 總檔案數 | 120+ |
| Python檔案 | 100+ |
| 活躍策略 | 8個 |
| 分析模組 | 5個 |
| ML模組 | 3個 |
| 測試檔案 | 11個 |
| 已歸檔 | 40+ |

---

## ✅ 系統狀態

- **健康度**: 100% ✅
- **MTF整合**: 7/8策略 ✅
- **測試覆蓋**: 核心功能 ✅
- **文檔完整**: 已更新 ✅

---

*系統已就緒，等待實盤部署*
