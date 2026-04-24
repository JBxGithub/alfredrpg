# FutuTradingBot 策略引擎文檔

## 概述

策略引擎是 FutuTradingBot 的核心組件，提供完整的趨勢跟蹤交易策略實現，整合技術指標與9步分析法。

## 架構

```
src/strategies/
├── __init__.py           # 模組導出
├── base.py               # 策略基類和接口
├── trend_strategy.py     # 趨勢策略實現
├── strategy_config.py    # 策略配置管理
└── backtest.py           # 回測框架
```

## 核心組件

### 1. TrendStrategy (趨勢策略)

基於多時間框架的趨勢跟蹤策略，整合多種技術指標。

#### 主要功能

- **趨勢判斷**: 多時間框架分析 (日線/小時線/15分鐘)
- **進場條件**: 9步分析法評分 + 技術指標共振 + 成交量確認
- **出場條件**: 止盈/止損/趨勢反轉
- **倉位管理**: 固定比例法 + 凱利公式

#### 配置參數

```yaml
# 趨勢判斷參數
ema_fast: 12              # EMA快線週期
ema_slow: 26              # EMA慢線週期
macd_fast: 12             # MACD快線
macd_slow: 26             # MACD慢線
boll_period: 20           # 布林帶週期

# 進場條件
min_analysis_score: 70.0  # 9步分析法最低評分
min_indicator_resonance: 3  # 最少共振指標數
volume_threshold: 1.5     # 成交量倍數閾值
rsi_lower: 30.0           # RSI下限
rsi_upper: 70.0           # RSI上限

# 出場條件
take_profit_pct: 0.05     # 止盈比例 5%
stop_loss_pct: 0.03       # 止損比例 3%
use_atr_stop: false       # 是否使用ATR止損

# 倉位管理
fixed_position_pct: 0.02  # 固定倉位比例 2%
max_positions: 10         # 最大持倉數量
use_kelly: false          # 是否使用凱利公式
```

#### 使用示例

```python
from src.strategies import TrendStrategy

# 創建策略實例
config = {
    'min_analysis_score': 70,
    'take_profit_pct': 0.05,
    'stop_loss_pct': 0.03
}
strategy = TrendStrategy(config=config)
strategy.initialize()

# 處理數據
signal = strategy.on_data({
    'code': '00700.HK',
    'df': kline_data,
    'analysis_score': 75
})

if signal:
    print(f"信號: {signal.signal.value}, 價格: {signal.price}")
```

### 2. BacktestEngine (回測引擎)

提供完整的策略回測功能，包括績效分析和風險指標計算。

#### 主要功能

- 歷史數據回測
- 績效分析 (收益率、勝率、盈虧比)
- 風險指標 (最大回撤、夏普比率、索提諾比率)
- 資金曲線記錄

#### 使用示例

```python
from src.strategies import BacktestEngine, TrendStrategy

# 創建策略和回測引擎
strategy = TrendStrategy()
engine = BacktestEngine(
    strategy=strategy,
    initial_capital=1000000,
    commission_rate=0.001,
    slippage=0.001
)

# 運行回測
result = engine.run(data_dict)

# 查看結果
result.print_summary()
print(f"總收益率: {result.total_return_pct:.2f}%")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
```

### 3. StrategyConfigManager (配置管理器)

管理策略配置，支持 YAML/JSON 格式的配置加載和保存。

#### 使用示例

```python
from src.strategies import StrategyConfigManager

# 創建配置管理器
config_manager = StrategyConfigManager('config/strategy_config.yaml')

# 獲取配置
trend_config = config_manager.get_trend_strategy_config()
risk_config = config_manager.get_risk_config()

# 更新配置
config_manager.update_trend_config(take_profit_pct=0.06)

# 驗證配置
is_valid, errors = config_manager.validate_config()
```

## 策略邏輯詳解

### 趨勢判斷邏輯

1. **EMA交叉判斷**
   - EMA5 > EMA20: 看多信號
   - EMA5 < EMA20: 看空信號

2. **MACD確認**
   - DIF > DEA 且 MACD柱 > 0: 動能向上
   - DIF < DEA 且 MACD柱 < 0: 動能向下

3. **布林帶位置**
   - 價格 > 中軌: 相對強勢
   - 價格 < 中軌: 相對弱勢

4. **多時間框架確認**
   - 所有時間框架趨勢一致時才進場
   - 主時間框架為 1小時線

### 進場條件

必須同時滿足:
1. 9步分析法評分 ≥ 70分
2. 技術指標共振 ≥ 3個指標
3. 成交量 > 1.5倍均量
4. RSI 在 30-70 範圍內

### 出場條件

滿足任一條件即出場:
1. 盈利達到 +5% (止盈)
2. 虧損達到 -3% (止損)
3. 趨勢反轉信號

### 倉位管理

**固定比例法** (默認):
```
倉位金額 = 賬戶總值 × 2%
股數 = 倉位金額 / 當前價格
```

**凱利公式** (可選):
```
f* = (p×b - q) / b
倉位比例 = f* × 0.25  (1/4凱利，保守策略)
```
其中:
- p = 勝率
- q = 敗率 = 1-p
- b = 賠率 (止盈/止損)

## 回測結果指標

| 指標 | 說明 |
|------|------|
| 總收益率 | 策略整體收益百分比 |
| 勝率 | 盈利交易次數 / 總交易次數 |
| 盈虧比 | 平均盈利 / 平均虧損 |
| 最大回撤 | 從高點到低點的最大虧損 |
| 夏普比率 | 風險調整後收益指標 |
| 索提諾比率 | 下行風險調整後收益 |
| 卡瑪比率 | 年化收益 / 最大回撤 |

## 配置文件示例

```yaml
# config/strategy_config.yaml
trend_strategy:
  ema_fast: 12
  ema_slow: 26
  macd_fast: 12
  macd_slow: 26
  
  min_analysis_score: 70.0
  min_indicator_resonance: 3
  volume_threshold: 1.5
  
  take_profit_pct: 0.05
  stop_loss_pct: 0.03
  
  fixed_position_pct: 0.02
  max_positions: 10

risk_management:
  max_daily_loss: 50000
  max_drawdown_percent: 10.0

backtest:
  start_date: "2023-01-01"
  end_date: "2024-01-01"
  initial_capital: 1000000
```

## 運行示例

```bash
# 運行策略示例
python examples/strategy_examples.py

# 運行測試
python -m pytest tests/test_strategy_engine.py -v
```

## 擴展開發

### 自定義策略

繼承 `BaseStrategy` 基類:

```python
from src.strategies import BaseStrategy, TradeSignal, SignalType

class MyStrategy(BaseStrategy):
    def on_data(self, data):
        # 實現策略邏輯
        if self.should_buy(data):
            return TradeSignal(
                code=data['code'],
                signal=SignalType.BUY,
                price=current_price,
                qty=quantity,
                reason="自定義邏輯"
            )
        return None
```

## 注意事項

1. **風險控制**: 始終設置止損，控制單筆交易風險
2. **參數優化**: 使用 Walk-Forward 分析避免過度擬合
3. **滑點考慮**: 實盤交易需考慮滑點影響
4. **資金管理**: 不要超過最大持倉限制
