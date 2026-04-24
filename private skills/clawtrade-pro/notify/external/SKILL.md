---
name: whatsapp-notifier
description: WhatsApp 通知系統，發送交易信號、風險警報和日報
metadata:
  openclaw:
    triggers:
      - event: signal_generated
      - event: order_executed
      - event: stop_loss_triggered
      - event: daily_report
---

# WhatsApp Notifier Skill

通過 WhatsApp 發送實時交易通知。

## 通知類型

### 1. 交易信號
```
🚨 TQQQ 交易信號

信號: BUY (強)
當前價: $52.35
RSI: 28.5 (超賣)
建議: 買入 100 股

回覆 /confirm 執行
```

### 2. 訂單執行
```
✅ 訂單已執行

標的: TQQQ
方向: BUY
數量: 100
價格: $52.35
時間: 09:45:32 ET

持倉更新: 100 股 @ $52.35
```

### 3. 風險警報
```
⚠️ 風險警報

日虧損: -$450
限制: $500
剩餘: $50

建議: 暫停新交易
```

### 4. 日報
```
📊 每日交易報告

日期: 2026-04-04

交易統計:
- 交易次數: 3
- 盈利次數: 2
- 虧損次數: 1
- 總盈虧: +$125

持倉:
- TQQQ: 100 股 @ $52.35
- QQQ: 10 股 @ $485.20

賬戶總值: $19,361 (+0.65%)
```

## 配置

```yaml
# notifier_config.yaml
whatsapp:
  enabled: true
  target_number: "+85263931048"
  
notifications:
  signal: true
  order: true
  risk_alert: true
  daily_report: true
  report_time: "16:30"  # 收盤後
```

## 使用方式

### 測試通知
```bash
/notify test
```

### 設置通知偏好
```bash
/notify set signal on
/notify set order off
```

## 依賴

- OpenClaw WhatsApp 通道
