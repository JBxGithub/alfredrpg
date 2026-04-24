# TQQQ Momentum Strategy

基於 RSI、移動平均線和 MACD 的 TQQQ 動量交易策略。

## 功能特性

- ✅ 技術指標計算 (RSI, MA, MACD)
- ✅ 交易信號生成 (BUY/SELL/HOLD)
- ✅ 策略回測功能
- ✅ 風險管理
- ✅ 自動通知集成
- ✅ CLI 命令行工具

## 策略邏輯

### 買入信號（滿足 2/3 條件）
1. RSI < 30（超賣）
2. 短期 MA > 長期 MA（金叉）
3. MACD > MACD Signal

### 賣出信號（滿足 2/3 條件）
1. RSI > 70（超買）
2. 短期 MA < 長期 MA（死叉）
3. MACD < MACD Signal

## 文件結構

```
tqqq-momentum/
├── SKILL.md                 # 技能說明文檔
├── strategy.py              # 核心策略實現
├── cli.py                   # 命令行接口
├── integration.py           # 系統集成模塊
├── strategy_config.yaml     # 策略配置
├── cron_config.json         # Cron 作業配置
├── HEARTBEAT.md            # 心跳檢查配置
├── backtest_report.md       # 回測報告
└── __init__.py             # 包初始化
```

## 安裝依賴

```bash
pip install pandas numpy pyyaml
# 可選：用於獲取真實數據
pip install yfinance
```

## 使用方法

### 1. 檢查當前信號

```bash
python cli.py check
```

### 2. 運行回測

```bash
python cli.py backtest --capital 100000 --period 2y
```

### 3. 查看技術指標

```bash
python cli.py indicators
```

### 4. 測試通知

```bash
python cli.py notify
```

### 5. Python API

```python
from strategy import TQQQMomentumStrategy, StrategyConfig

# 初始化策略
config = StrategyConfig()
strategy = TQQQMomentumStrategy(config)

# 加載數據
data = load_historical_data('TQQQ')

# 計算指標
strategy.calculate_indicators(data)

# 生成信號
signal = strategy.generate_signal(account_value=100000)
print(f"信號: {signal.signal.value}")

# 運行回測
result = strategy.backtest(initial_capital=100000)
print(f"總回報: {result['total_return_pct']:.2f}%")
```

## 配置說明

編輯 `strategy_config.yaml` 調整策略參數：

```yaml
indicators:
  rsi:
    period: 14
    oversold: 30
    overbought: 70
  moving_averages:
    short: 20
    long: 50
  macd:
    fast: 12
    slow: 26
    signal: 9

risk_limits:
  max_position_size: 0.25
  stop_loss_pct: 0.05
  take_profit_pct: 0.10
```

## 自動觸發

### HEARTBEAT 配置

在 `HEARTBEAT.md` 中配置自動檢查邏輯：

```markdown
During market hours (09:30-16:00 ET):
1. Check TQQQ momentum signals every 5 minutes
2. If signal generated, check risk limits
3. If risk check passed, notify user
```

### Cron 作業

```json
{
  "name": "tqqq-signal-check",
  "schedule": "*/5 9-16 * * 1-5",
  "timezone": "America/New_York"
}
```

## 回測結果

基於 2 年歷史數據的回測結果：

| 指標 | 數值 |
|------|------|
| 總回報 | 0.77% |
| 交易次數 | 10 |
| 勝率 | 50.0% |
| 最大回撤 | -9.16% |
| 夏普比率 | 0.09 |

詳見 `backtest_report.md`

## 注意事項

⚠️ **風險提示**: 本策略僅供參考，不構成投資建議。過去表現不代表未來收益。

## 更新日誌

### v1.0 (2026-04-04)
- 初始版本發布
- 實現 RSI/MA/MACD 策略
- 添加回測功能
- 集成通知系統
