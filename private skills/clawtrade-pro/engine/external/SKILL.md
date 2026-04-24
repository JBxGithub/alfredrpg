# Strategy Engine

> 通用策略引擎 — 支持多種交易策略的模塊化框架

## 功能

- 策略動態加載
- 統一策略接口
- 多策略並行運行
- 策略參數管理
- 股票-策略映射

## 架構

```
strategy-engine/
├── engine.py          # 策略引擎核心
├── base_strategy.py   # 策略基類
└── loader.py          # 策略加載器

strategies/
├── momentum.py        # 動量策略
├── mean_reversion.py  # 均值回歸策略
├── breakout.py        # 突破策略
└── macd_crossover.py  # MACD交叉策略
```

## 使用方法

```python
from strategy_engine import StrategyEngine

# 創建引擎
engine = StrategyEngine()

# 加載配置
engine.load_config('config/strategies.yaml')

# 獲取某股票的交易信號
signal = engine.generate_signal('TQQQ', price_data)

# 獲取所有活躍信號
all_signals = engine.scan_all_stocks()
```

## 配置示例

```yaml
strategies:
  TQQQ:
    type: momentum
    enabled: true
    params:
      rsi_period: 14
      rsi_overbought: 70
      rsi_oversold: 30
      ma_short: 20
      ma_long: 50
      
  AAPL:
    type: mean_reversion
    enabled: true
    params:
      lookback: 20
      z_threshold: 2.0
      take_profit: 0.05
      stop_loss: 0.03
      
  NVDA:
    type: breakout
    enabled: true
    params:
      lookback: 20
      volume_threshold: 1.5
      confirmation_bars: 2
```

## CLI 命令

```bash
# 列出所有策略
python -m strategy_engine --action list

# 測試策略
python -m strategy_engine --action test --symbol TQQQ --strategy momentum

# 掃描所有股票
python -m strategy_engine --action scan
```
