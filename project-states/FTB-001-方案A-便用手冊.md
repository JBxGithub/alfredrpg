# FTB-001 方案A：便用手冊

> **版本**: v2.0 (Z-Score Mean Reversion Final)  
> **日期**: 2026-03-29  
> **狀態**: 已整合至FutuTradingBot  
> **測試**: 197/197 通過 (整合後總計)  
> **回測結果**: 3年 +1,918.29%，夏普比率 2.45

---

## 快速開始（5分鐘上手）

### 1. 環境檢查
```python
# 確認Python版本
python --version  # 需 3.8+

# 確認依賴安裝
pip list | findstr futu-api
pip list | findstr pandas
pip list | findstr numpy
```

### 2. Z-Score Mean Reversion 策略（最終版 2026-03-29）

```python
from src.strategies.tqqq_long_short import TQQQLongShortStrategy, TQQQStrategyConfig

# 創建策略實例（使用最終版參數）
config = TQQQStrategyConfig(
    entry_zscore=1.65,      # 進場閾值
    exit_zscore=0.5,        # 出場閾值
    rsi_overbought=70.0,    # RSI超買
    rsi_oversold=30.0,      # RSI超賣
    take_profit_pct=0.05,   # 止盈5%
    stop_loss_pct=0.03,     # 止損3%
    time_stop_days=7        # 時間止損7天
)

strategy = TQQQLongShortStrategy(config)

# 生成交易信號
signal = strategy.generate_signal(data)
print(f"信號: {signal.signal_type}")
print(f"信心度: {signal.confidence}")
print(f"原因: {signal.reason}")
```

### 3. 策略參數（最終版）
| 參數 | 做多 | 做空 |
|------|------|------|
| Z-Score | < -1.65 | > +1.65 |
| RSI | < 30 | > 70 |
| 成交量 | > 20日均量×50% | > 20日均量×50% |
| 止盈 | 5% | 5% |
| 止損 | 3% | 3% |
| 時間止損 | 7天 | 7天 |
```

---

## 核心概念

### 6大市場狀態

| 狀態 | 定義 | 策略 | 倉位 |
|------|------|------|------|
| **牛市平靜** | 價格>200MA, VIX<20 | 趨勢跟蹤 | 100% |
| **牛市波動** | 價格>200MA, VIX≥20 | 動量突破 | 70% |
| **熊市平靜** | 價格<200MA, VIX<20 | 防禦減倉 | 30% |
| **熊市波動** | 價格<200MA, VIX≥20 | 暫停交易 | 0% |
| **橫盤平靜** | 價格≈200MA, VIX<20 | 均值回歸 | 50% |
| **橫盤波動** | 價格≈200MA, VIX≥20 | 暫停交易 | 0% |

### 狀態判別邏輯

```
價格 vs 200日均線
    │
    ├─ > +3% → 牛市
    ├─ < -3% → 熊市
    └─ ±3%內 → 橫盤
    
VIX值
    │
    ├─ < 20 → 平靜
    └─ ≥ 20 → 波動
```

---

## 詳細API參考

### MarketRegimeClassifier

#### 初始化
```python
from market_regime_simple import MarketRegimeClassifier

classifier = MarketRegimeClassifier(
    sideways_threshold_pct=3.0,    # 橫盤閾值 (%)
    vix_quiet_threshold=20.0,      # VIX平靜閾值
    min_history_days=200           # 最小歷史天數
)
```

#### 更新價格歷史
```python
classifier.update_price_history(prices)  # prices: List[float]
```

#### 分類市場
```python
result = classifier.classify(
    price=450.0,
    vix=18.5,
    atr=2.3
)
```

#### 檢測狀態轉換
```python
transition = classifier.get_state_transition(result)
if transition:
    prev_state, new_state = transition
    is_significant = classifier.is_significant_transition(transition)
```

### StateStrategyMapper

#### 獲取策略配置
```python
from state_strategy_mapper import StateStrategyMapper

mapper = StateStrategyMapper()
mapping = mapper.map_regime(regime_result)

# 訪問配置
config = mapping.config
print(config.strategy_type)           # 策略類型
print(config.position_size_multiplier) # 倉位倍數
print(config.rsi_overbought)          # RSI超買閾值
print(config.rsi_oversold)            # RSI超賣閾值
```

#### 動態倉位計算
```python
base_size = 100  # 基礎倉位
adjusted_size = mapper.get_position_size(base_size, regime_result)
```

#### 檢查交易許可
```python
can_trade = mapper.should_allow_new_entries(regime_result)
is_paused = mapper.is_trading_paused(regime_result)
```

### RiskManager

#### 初始化
```python
from risk_manager import RiskManager, RiskLimits

limits = RiskLimits(
    max_position_size=100000,      # 單筆最大倉位
    max_total_exposure=500000,     # 總曝險上限
    max_positions=5,               # 最大持倉數
    max_drawdown_pct=10.0,         # 最大回撤
    daily_loss_limit=50000         # 日虧損限制
)

risk_manager = RiskManager(limits=limits)
```

#### 註冊回調函數
```python
def on_reduce_positions(reduction_pct):
    print(f"減倉 {reduction_pct}%")

def on_pause_trading():
    print("暫停交易")

def on_state_change(prev_state, new_state):
    print(f"狀態變更: {prev_state.value} -> {new_state.value}")

risk_manager.register_callbacks(
    on_reduce_positions=on_reduce_positions,
    on_pause_trading=on_pause_trading,
    on_state_change=on_state_change
)
```

#### 更新市場狀態
```python
alerts = risk_manager.update_market_regime(regime_result)
for alert in alerts:
    print(f"[{alert.level.value}] {alert.message}")
```

#### 倉位管理
```python
# 計算動態倉位
size = risk_manager.calculate_position_size(
    base_size=100,
    symbol="AAPL",
    price=150.0
)

# 檢查是否可開倉
allowed, reason = risk_manager.can_open_position(
    symbol="AAPL",
    size=100,
    price=150.0
)
```

---

## 配置參數

### config.yaml

```yaml
# 市場狀態檢測配置
market_regime:
  sideways_threshold_pct: 3.0      # 橫盤閾值 (%)
  vix_quiet_threshold: 20.0        # VIX平靜閾值
  min_history_days: 200            # 最小歷史天數

# 狀態-策略映射
state_strategy_mapping:
  bull_quiet:
    strategy_type: "trend_following"
    position_size_multiplier: 1.0
    rsi_overbought: 75
    rsi_oversold: 40
    
  bull_volatile:
    strategy_type: "momentum_breakout"
    position_size_multiplier: 0.8
    rsi_overbought: 75
    rsi_oversold: 35
    
  bear_quiet:
    strategy_type: "defensive_reduce"
    position_size_multiplier: 0.5
    rsi_overbought: 60
    rsi_oversold: 25
    
  bear_volatile:
    strategy_type: "pause_trading"
    position_size_multiplier: 0.0
    
  sideways_quiet:
    strategy_type: "mean_reversion"
    position_size_multiplier: 0.7
    rsi_overbought: 65
    rsi_oversold: 35
    
  sideways_volatile:
    strategy_type: "pause_trading"
    position_size_multiplier: 0.0

# 風險管理
risk_management:
  max_position_size: 100000
  max_total_exposure: 500000
  max_positions: 5
  max_drawdown_pct: 10.0
  daily_loss_limit: 50000
  
  # 狀態感知減倉
  volatile_state_reduction_pct: 50.0
  bear_state_reduction_pct: 50.0
  emergency_reduction_pct: 90.0
```

---

## 使用示例

### 示例1：日度市場檢查
```python
import yfinance as yf
from market_regime_simple import classify_market

# 獲取數據
spy = yf.Ticker("SPY")
hist = spy.history(period="1y")
prices = hist['Close'].tolist()

# 獲取VIX（需額外數據源）
vix = 18.5  # 從外部API獲取

# 分類
result = classify_market(
    price=prices[-1],
    vix=vix,
    atr=2.5,
    price_history=prices
)

print(f"今日市場狀態: {result.state.value}")
```

### 示例2：實時風控
```python
from risk_manager import RiskManager, Position

# 初始化
risk_mgr = RiskManager()

# 添加持倉
position = Position(
    symbol="AAPL",
    size=100,
    entry_price=150.0,
    current_price=155.0,
    side="long"
)
risk_mgr.add_position(position)

# 更新市場狀態
alerts = risk_mgr.update_market_regime(regime_result)

# 檢查是否需要行動
for alert in alerts:
    if alert.level == "critical":
        print(f"🚨 緊急警報: {alert.message}")
```

### 示例3：策略選擇
```python
from state_strategy_mapper import StateStrategyMapper

mapper = StateStrategyMapper()
mapping = mapper.map_regime(regime_result)

# 根據狀態選擇策略
if mapping.config.strategy_type == "trend_following":
    print("執行趨勢跟蹤策略")
    # ...
elif mapping.config.strategy_type == "mean_reversion":
    print("執行均值回歸策略")
    # ...
elif mapping.config.strategy_type == "pause_trading":
    print("⚠️ 暫停交易，保護本金")
```

---

## 常見問題

### Q1: 為什麼狀態顯示為"sideways"？
**A**: 當價格在200日均線±3%範圍內時，系統判定為橫盤。這是正常的震盪整理階段。

### Q2: VIX數據從哪裡獲取？
**A**: 可以從以下來源獲取：
- Yahoo Finance: `^VIX`
- CBOE官網
- 富途API（如已訂閱）

### Q3: 如何自定義狀態閾值？
**A**: 
```python
classifier = MarketRegimeClassifier(
    sideways_threshold_pct=5.0,    # 改為5%
    vix_quiet_threshold=25.0       # 改為25
)
```

### Q4: 狀態轉換時會自動減倉嗎？
**A**: 是的。RiskManager會根據配置自動觸發：
- `bear_volatile` → 緊急減倉90%
- `sideways_volatile` → 暫停交易
- `bear_quiet` → 減倉50%

### Q5: 如何測試系統？
**A**: 
```bash
# 運行所有測試
python -m pytest tests/ -v

# 運行特定測試
python -m pytest tests/test_market_regime_simple.py -v
```

---

## 故障排除

| 問題 | 原因 | 解決方案 |
|------|------|----------|
| `Insufficient price history` | 歷史數據不足200天 | 提供更長的價格歷史 |
| `No mapping found for state` | 狀態映射缺失 | 檢查config.yaml配置 |
| `Trading paused` | 高風險狀態觸發 | 等待市場穩定或手動覆蓋 |
| `Max positions reached` | 持倉數達上限 | 平倉後再開新倉 |

---

## 進階用法

### 自定義策略映射
```python
from state_strategy_mapper import StrategyConfig, StrategyType, RiskAction

# 自定義映射
custom_mapping = {
    MarketState.BULL_QUIET: StrategyConfig(
        strategy_type=StrategyType.TREND_FOLLOWING,
        risk_action=RiskAction.NONE,
        position_size_multiplier=1.2,  # 加大倉位
        rsi_overbought=80,              # 更寬鬆的RSI
        rsi_oversold=35
    )
}

mapper = StateStrategyMapper(custom_mapping)
```

### 多時間框架分析
```python
# 日線狀態
daily_result = classifier.classify(daily_price, daily_vix, daily_atr)

# 週線狀態
weekly_result = classifier.classify(weekly_price, weekly_vix, weekly_atr)

# 綜合判斷
if daily_result.is_bull and weekly_result.is_bull:
    print("多時間框架確認牛市")
```

---

## 更新日誌

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| v1.0 | 2026-03-26 | 初始版本，78項測試通過 |

---

## 支援與反饋

如有問題，請檢查：
1. 測試報告: `tests/reports/`
2. 日誌檔案: `logs/`
3. 封存狀態: `project-states/archived/`

---

*本手冊確保FTB-001方案A可在未來無縫使用。*
