# Cron Jobs Scheduler

> ClawTrade Pro 定時任務調度器

## 定時任務

| 任務 | 時間 | 描述 |
|------|------|------|
| market_open | 09:25 | 開盤前檢查 |
| pre_market_scan | 09:28 | 盤前掃描 |
| market_data_sync | 每 1 分鐘 | 同步市場數據 |
| signal_check | 每 5 分鐘 | 檢查交易信號 |
| risk_monitor | 每 1 分鐘 | 風險監控 |
| heartbeat | 每 5 分鐘 | 系統心跳 |
| daily_report | 16:30 | 日終報告 |
| market_close | 16:05 | 收盤處理 |

## 使用方法

```python
from cron_jobs import Scheduler

scheduler = Scheduler()
scheduler.start()
```

## CLI 命令

```bash
# 啟動調度器
python -m cron_jobs --action start

# 列出所有任務
python -m cron_jobs --action list

# 運行單個任務
python -m cron_jobs --action run --task signal_check
```
