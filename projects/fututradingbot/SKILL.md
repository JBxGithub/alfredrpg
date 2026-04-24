---
name: futu-trading-bot
description: 完整股票交易系統，包含MTF分析、機器學習、增強回測、Web儀表板
metadata:
  openclaw:
    version: "2.1.0"
    author: "ClawTeam"
    category: "trading"
    location: "projects/fututradingbot"
---

# FutuTradingBot - 完整交易系統 v2.1

> 位置: `projects/fututradingbot/`
> 
> 整合版本: 合併 ClawTrade Pro 優點（文檔、數據、研究）

---

## 🎯 系統概述

**目標**: 建立自動化股票交易系統，實現「人在度假，系統在運轉」的被動收入

**核心願景**: 將呀鬼訓練成優秀的投資人，長期做正確的交易決定

**當前狀態**: ✅ 系統整合完成，等待實盤部署

---

## 📁 完整結構

```
projects/fututradingbot/
│
├── 📄 核心程序
│   ├── main.py                      # 主入口
│   ├── launcher.py                  # 系統啟動器
│   └── emergency_close.py           # 緊急平倉
│
├── 📁 src/                          # 源代碼（97個Python檔案）
│   ├── analysis/                    # 分析模組（MTF、市場狀態、情緒）
│   ├── api/                         # Futu API 封裝
│   ├── backtest/                    # 增強回測引擎（42個腳本）
│   ├── core/                        # 交易引擎
│   ├── dashboard/                   # Web儀表板
│   ├── indicators/                  # 技術指標（MACD-V、K線形態）
│   ├── ml/                          # 機器學習（52+特徵）
│   ├── risk/                        # 風險管理
│   ├── strategies/                  # 策略系統（13個策略）
│   └── utils/                       # 工具函數
│
├── 📁 docs/                         # 文檔（整合自CTP）
│   ├── research/                    # 研究報告
│   │   ├── TQQQ_Research_Report.md
│   │   └── TQQQ_ZScore_Strategy_Optimization_Report.md
│   ├── architecture/                # 系統設計
│   │   ├── CLAWTRADE_ARCHITECTURE.md
│   │   └── qqq_tqqq_arbitrage_system_design.md
│   └── *.md                         # 其他技術文檔
│
├── 📁 data/                         # 數據
│   └── historical/                  # 歷史數據（整合自CTP）
│       ├── qqq_history.csv
│       ├── tqqq_history.csv
│       └── ...
│
├── 📁 scripts/                      # 工具腳本（整合自CTP）
│   ├── analyze_qqq_tqqq.py
│   ├── check_futu_account.py
│   ├── get_qqq_tqqq_data.py
│   └── ...
│
├── 📁 tests/                        # 測試（34個測試檔案）
├── 📁 config/                       # 配置檔案
└── 📁 archived/                     # 歸檔檔案
```

---

## 🚀 快速開始

### 1. 環境準備

```bash
cd projects/fututradingbot

# 安裝依賴
pip install -r requirements.txt

# 配置機密信息
cp config/secrets.yaml.example config/secrets.yaml
# 編輯 config/secrets.yaml 填入API密鑰
```

### 2. 運行Dashboard

```bash
python src/dashboard/app.py
# 訪問 http://localhost:5000
```

### 3. 執行回測

```bash
python src/backtest/enhanced_backtest.py --symbol TQQQ
```

### 4. 啟動實盤（謹慎！）

```bash
python main.py --mode live
```

---

## 🎛️ 核心功能

### MTF多時間框架分析
```python
from src.analysis.mtf_analyzer import MTFAnalyzer

mtf = MTFAnalyzer()
trend = mtf.analyze_trend(symbol='TQQQ', timeframes=['1d', '4h', '1h'])
```

### 機器學習信號增強
```python
from src.ml.signal_enhancer import SignalEnhancer

enhancer = SignalEnhancer()
ml_signal = enhancer.enhance(raw_signal, features=52)
```

### TQQQ策略（Z-Score均值回歸）
```python
from src.strategies.tqqq_long_short import TQQQLongShortStrategy

strategy = TQQQLongShortStrategy(config={
    'entry_zscore': 1.65,
    'rsi_overbought': 70,
    'rsi_oversold': 30
})
```

---

## 📊 與 ClawTrade Pro 的關係

| 特性 | FutuTradingBot | ClawTrade Pro | 整合結果 |
|------|---------------|---------------|---------|
| **功能完整性** | ⭐⭐⭐ 完整 | ⭐⭐ 基礎 | ✅ 保留FTB完整功能 |
| **文檔豐富度** | ⭐⭐ 一般 | ⭐⭐⭐ 豐富 | ✅ 合併CTP文檔 |
| **數據現成度** | ⭐⭐ 需下載 | ⭐⭐⭐ 現成 | ✅ 合併CTP數據 |
| **代碼複雜度** | ⭐⭐⭐ 複雜 | ⭐⭐ 簡單 | ✅ 保留FTB專業性 |
| **測試覆蓋** | ⭐⭐⭐ 完整 | ⭐ 無 | ✅ 保留FTB測試 |

**結論**: FutuTradingBot 為主系統，吸收 CTP 的文檔、數據、研究優點

---

## 🔧 常用命令

| 命令 | 功能 |
|------|------|
| `python main.py --mode backtest --symbol TQQQ` | 回測模式 |
| `python main.py --mode live` | 實盤模式（謹慎） |
| `python src/backtest/quick_simulation.py` | 快速模擬 |
| `python scripts/check_futu_account.py` | 檢查賬戶 |

---

## ⚠️ 風險提示

- 實盤交易前必須完成紙上交易測試
- 確保風險參數設置正確
- 保留緊急平倉能力
- 實盤密碼: `011087 + Enter`

---

## 📚 相關文檔

- 系統架構: `docs/architecture/CLAWTRADE_ARCHITECTURE.md`
- TQQQ研究: `docs/research/TQQQ_Research_Report.md`
- 風險指南: `docs/RISK_MONITOR_GUIDE.md`
- 策略引擎: `docs/strategy_engine.md`

---

## 📝 更新記錄

| 版本 | 日期 | 更新內容 |
|------|------|---------|
| 2.1.0 | 2026-04-09 | 整合 ClawTrade Pro 文檔、數據、研究報告 |
| 2.0.0 | 2026-04-07 | MTF整合版，全系統測試通過 |
| 1.0.0 | 2026-03-27 | 初始版本 |

---

## 🏆 成就

- ✅ 全系統測試通過（104/104）
- ✅ 策略優化完成（勝率目標65%+）
- ✅ ML模組整合（52+特徵）
- ✅ Dashboard部署就緒
- ✅ 等待實盤驗證
