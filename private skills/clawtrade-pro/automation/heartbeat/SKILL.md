# Heartbeat Monitor

> ClawTrade Pro 系統心跳監控

## 功能

- 系統健康檢查
- 各模塊狀態監控
- 自動故障檢測
- 異常通知

## 監控項目

| 項目 | 檢查內容 | 頻率 |
|------|----------|------|
| Futu API | 連接狀態 | 每分鐘 |
| 數據流 | 價格更新時間 | 每分鐘 |
| 持倉風險 | 止損止盈檢查 | 每分鐘 |
| 賬戶狀態 | 資金、保證金 | 每5分鐘 |
| 系統資源 | CPU、內存 | 每5分鐘 |

## 使用方法

```python
from heartbeat import HeartbeatMonitor

monitor = HeartbeatMonitor()
status = monitor.check_all()
```

## CLI 命令

```bash
# 運行單次檢查
python -m heartbeat --action check

# 持續監控
python -m heartbeat --action monitor --interval 60
```
