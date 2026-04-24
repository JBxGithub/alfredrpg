# Risk Manager

> 風險監控 + 止損止盈管理

## 功能

- 實時風險監控
- 倉位管理
- 止損止盈自動執行
- 風險限額檢查
- 保證金監控

## 風險規則

### 倉位限制

| 規則 | 限額 | 動作 |
|------|------|------|
| 單筆倉位 | ≤ 50% 資金 | 拒絕超額訂單 |
| 總倉位 | ≤ 100% 資金 | 拒絕新訂單 |
| 單一標的 | ≤ 50% 資金 | 分散風險 |
| 日內虧損 | ≤ 3% 總資金 | 暫停交易 |
| 連續虧損 | ≥ 3 筆 | 冷卻 30 分鐘 |

### 止損止盈

- **固定止損**: 虧損達 3% 自動平倉
- **移動止損**: 盈利後回撤 50% 平倉
- **時間止損**: 持倉 7 天強制平倉
- **止盈**: 盈利 5% 自動平倉

## 使用方法

```python
from risk_manager import RiskManager

# 創建風險管理器
risk = RiskManager()

# 檢查訂單
result = risk.check_order(order)

# 檢查持倉風險
alerts = risk.check_positions(positions)

# 更新止損止盈
risk.update_stops(position)
```

## CLI 命令

```bash
# 檢查當前風險狀態
python -m risk_manager --action status

# 檢查訂單風險
python -m risk_manager --action check --symbol TQQQ --quantity 100

# 運行風險監控
python -m risk_manager --action monitor
```
