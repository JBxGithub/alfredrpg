# TQQQ Momentum Strategy

> TQQQ 動量交易策略 + 回測引擎

## 策略概述

基於 Z-Score Mean Reversion 的 TQQQ 單邊多空策略。

### 核心參數

| 參數 | 數值 | 說明 |
|------|------|------|
| Z-Score 進場閾值 | ±1.65 | 極端偏離時進場 |
| Z-Score 出場閾值 | ±0.5 | 回歸均值時出場 |
| Z-Score 止損閾值 | ±3.5 | 策略失效時止損 |
| 回望期 | 60日 | 計算均值和標準差 |
| RSI 超買 | 70 | 做空信號確認 |
| RSI 超賣 | 30 | 做多信號確認 |
| 止盈 | 5% | 達標即出場 |
| 止損 | 3% | 嚴格風控 |
| 時間止損 | 7天 | 防止長期套牢 |
| 單筆倉位 | 50% | 固定基礎 $50,000 |

### 進場條件

- **做多**: Z-Score < -1.65 + RSI < 30 + 成交量 > 20日均量 × 50%
- **做空**: Z-Score > 1.65 + RSI > 70 + 成交量 > 20日均量 × 50%

### 出場條件

- **止盈**: 盈利 ≥ 5%
- **止損**: 虧損 ≤ -3%
- **Z-Score回歸**: |Z-Score| < 0.5
- **Z-Score止損**: |Z-Score| > 3.5
- **時間止損**: 持倉 ≥ 7天

## 使用方法

```python
from tqqq_momentum import TQQQStrategy, BacktestEngine

# 創建策略
strategy = TQQQStrategy()

# 獲取交易信號
signal = strategy.generate_signal(price_data)

# 回測
backtest = BacktestEngine(strategy)
results = backtest.run(historical_data)
```

## CLI 命令

```bash
# 生成當前信號
python -m tqqq_momentum --action signal

# 運行回測
python -m tqqq_momentum --action backtest --start 2023-01-01 --end 2025-12-31

# 優化參數
python -m tqqq_momentum --action optimize
```
