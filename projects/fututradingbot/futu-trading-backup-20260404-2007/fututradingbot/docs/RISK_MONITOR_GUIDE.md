# FutuTradingBot 風控與監控系統

## 系統概述

本系統提供全方位的交易風險控制和實時監控機制，確保交易機器人在安全範圍內運行。

## 模組結構

```
src/
├── risk/
│   ├── __init__.py
│   └── risk_manager.py      # 風險管理核心
├── monitoring/
│   ├── __init__.py
│   └── monitor.py           # 監控系統核心
└── core/
    └── risk_aware_engine.py # 整合引擎

config/
└── risk_config.json         # 風控配置文件
```

## 風控系統 (RiskManager)

### 1. 倉位風控

| 限制類型 | 配置項 | 默認值 | 說明 |
|---------|-------|-------|------|
| 單一股票最大倉位價值 | `max_single_position_value` | 100,000 | 單一股票持倉上限 |
| 單一股票最大佔比 | `max_single_position_percent` | 20% | 佔總資金比例 |
| 總倉位上限 | `max_total_position_value` | 500,000 | 所有持倉總值上限 |
| 總倉位佔比上限 | `max_total_position_percent` | 80% | 總倉位佔資金比例 |
| 行業集中度上限 | `max_sector_concentration_percent` | 40% | 單一行業佔比 |

### 2. 交易風控

| 限制類型 | 配置項 | 默認值 | 說明 |
|---------|-------|-------|------|
| 每日最大交易次數 | `max_daily_trades` | 20 | 日內交易次數上限 |
| 單筆最大金額 | `max_order_value` | 50,000 | 單筆訂單金額上限 |
| 單筆最大股數 | `max_order_quantity` | 1,000 | 單筆訂單股數上限 |
| 價格波動閾值 | `price_volatility_threshold` | 5% | 波動率異常檢測 |
| 價格暴漲暴跌閾值 | `price_spike_threshold` | 10% | 價格異常波動檢測 |

### 3. 資金風控

| 限制類型 | 配置項 | 默認值 | 說明 |
|---------|-------|-------|------|
| 每日最大虧損 | `max_daily_loss` | 50,000 | 日內虧損上限 |
| 回撤警告 | `max_drawdown_percent` | 10% | 觸發警告 |
| 強制停止回撤 | `max_drawdown_percent_hard` | 15% | 自動停止交易 |
| 保證金警告 | `margin_warning_percent` | 80% | 保證金使用率警告 |
| 保證金危險 | `margin_critical_percent` | 90% | 保證金危險水平 |

## 監控系統 (Monitor)

### 1. 實時監控面板

- **當日盈虧**: 實時顯示日內盈虧狀況
- **持倉風險度**: 顯示當前持倉風險指標
- **策略運行狀態**: 各策略的運行狀態
- **風控指標**: 各項風控指標的當前值

### 2. 警報機制

| 警報類型 | 級別 | 說明 |
|---------|------|------|
| RISK_WARNING | warning | 風險警告 |
| RISK_CRITICAL | critical | 嚴重風險 |
| TRADE_ANOMALY | error | 異常交易 |
| SYSTEM_ERROR | critical | 系統錯誤 |
| CONNECTION_LOST | error | 連接斷開 |
| MARGIN_CALL | critical | 保證金不足 |

### 3. 日誌與審計

- **操作記錄**: 所有交易操作的詳細記錄
- **風控事件追蹤**: 風險事件的完整追蹤
- **性能指標統計**: CPU、內存等性能指標

## 使用方法

### 基本使用

```python
from src.risk.risk_manager import RiskManager, Position
from src.monitoring.monitor import Monitor

# 初始化
risk_manager = RiskManager("./config/risk_config.json")
monitor = Monitor()

# 設置資金
risk_manager.update_capital(
    total_capital=1000000,
    margin_used=100000,
    margin_available=400000
)

# 更新持倉
positions = [
    Position(symbol="00700", quantity=100, avg_price=400.0, market_price=420.0, sector="科技")
]
risk_manager.update_positions(positions)

# 檢查交易風險
can_trade, event = risk_manager.check_trade_risk("00700", 100, 420.0, "BUY")
if not can_trade:
    print(f"交易被拒絕: {event.message}")

# 啟動監控
monitor.start()

# 發送警報
monitor.send_risk_alert("POSITION_LIMIT", "倉位超過限制", "warning")

# 獲取監控數據
dashboard = monitor.get_dashboard_data()
```

### 整合引擎使用

```python
from src.core.risk_aware_engine import RiskAwareTradingEngine
from src.config.settings import Settings

# 初始化
settings = Settings()
engine = RiskAwareTradingEngine(settings)
engine.start()

# 更新賬戶信息
engine.update_account_info(1000000, 0, 500000)

# 檢查交易
can_trade, reason = engine.check_trade("00700", 100, 420.0, "BUY")
if can_trade:
    # 執行交易...
    engine.record_trade("00700", 100, 420.0, "BUY", "ORD123", "success", 1000.0)

# 獲取狀態
status = engine.get_status()
```

## 配置文件

### risk_config.json

```json
{
  "max_single_position_value": 100000,
  "max_single_position_percent": 20.0,
  "max_total_position_value": 500000,
  "max_total_position_percent": 80.0,
  "max_sector_concentration_percent": 40.0,
  "max_daily_trades": 20,
  "max_order_value": 50000,
  "max_order_quantity": 1000,
  "price_volatility_threshold": 5.0,
  "price_spike_threshold": 10.0,
  "max_daily_loss": 50000,
  "max_drawdown_percent": 10.0,
  "max_drawdown_percent_hard": 15.0,
  "margin_warning_percent": 80.0,
  "margin_critical_percent": 90.0,
  "enable_position_risk": true,
  "enable_trade_risk": true,
  "enable_capital_risk": true,
  "auto_stop_on_critical": true
}
```

## 測試

```bash
# 運行測試
python tests/test_risk_monitor.py

# 運行演示
python examples/risk_monitor_demo.py
```

## 風險事件處理流程

1. **檢測**: 系統持續監控各項風險指標
2. **評估**: 根據風險等級分類 (LOW/MEDIUM/HIGH/CRITICAL)
3. **警報**: 通過多種渠道發送警報通知
4. **處置**: 根據配置自動或手動處理
5. **記錄**: 完整記錄風險事件到審計日誌

## 注意事項

1. **auto_stop_on_critical**: 當設為 true 時，嚴重風險會自動停止交易
2. **價格異常檢測**: 基於歷史價格數據，需要一定數據量才能生效
3. **警報去重**: 相同警報在5分鐘內不會重複發送
4. **日誌保留**: 審計日誌默認保留90天
