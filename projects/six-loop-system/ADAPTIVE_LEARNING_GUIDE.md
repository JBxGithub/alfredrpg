# 自適應學習系統使用指南

> **系統名稱**: Adaptive Learning System  
> **版本**: v1.0.0  
> **更新日期**: 2026-04-23  
> **目的**: 持續監控、自動優化交易參數

---

## 🎯 系統概述

### 為什麼需要自適應學習？

即使回測數據完美，市場環境也會變化：
- 📈 牛市/熊市週期轉換
- 📊 波動率變化
- 🔄 策略有效性衰減
- ⚠️ 黑天鵝事件

**自適應學習系統** 就是為了應對這些變化，持續優化策略參數。

---

## 🏗️ 系統架構

```
自適應學習系統
├── 每日監控 (Daily Monitoring)
│   ├── 檢查昨日表現
│   ├── 異常檢測
│   └── 自動保護措施
│
├── 每週回顧 (Weekly Review)
│   ├── 分析4週趨勢
│   ├── 盈利減倉效率分析
│   ├── 回撤控制評估
│   └── 生成優化建議
│
└── 每月調整 (Monthly Adjustment)
    ├── 長期趨勢分析
    ├── 策略漂移檢測
    └── 自動參數調整 (可選)
```

---

## 🚀 快速開始

### 1. 單次運行

```bash
# 每日監控
python run_adaptive_learning.py --mode daily

# 每週回顧
python run_adaptive_learning.py --mode weekly

# 每月調整
python run_adaptive_learning.py --mode monthly
```

### 2. 持續運行 (推薦)

```bash
# 啟用自動參數調整 (危險！)
python run_adaptive_learning.py --mode continuous --auto-adjust

# 僅監控和建議 (安全)
python run_adaptive_learning.py --mode continuous
```

### 3. 設置為系統服務

#### Windows (使用 Task Scheduler)
```powershell
# 創建每日監控任務
schtasks /create /tn "SixLoop-Daily-Monitor" `
  /tr "python C:\path\to\run_adaptive_learning.py --mode daily" `
  /sc daily /st 08:00

# 創建每週回顧任務
schtasks /create /tn "SixLoop-Weekly-Review" `
  /tr "python C:\path\to\run_adaptive_learning.py --mode weekly" `
  /sc weekly /d MON /st 09:00
```

#### Linux/Mac (使用 cron)
```bash
# 編輯 crontab
crontab -e

# 添加以下行
# 每日 08:00 執行監控
0 8 * * * cd /path/to/six-loop-system && python run_adaptive_learning.py --mode daily

# 每週一 09:00 執行回顧
0 9 * * 1 cd /path/to/six-loop-system && python run_adaptive_learning.py --mode weekly

# 每月1日 10:00 執行調整
0 10 1 * * cd /path/to/six-loop-system && python run_adaptive_learning.py --mode monthly
```

---

## ⚙️ 配置說明

### 重要配置項

#### 1. 自動調整模式
```yaml
mode:
  auto_adjust: false  # ⚠️ 建議先設為 false 觀察
  confirm_before_adjust: true  # 調整前發送確認
```

**建議**: 先運行 1-2 個月觀察建議質量，再考慮啟用 `auto_adjust`。

#### 2. 自動保護措施
```yaml
auto_protection:
  reduce_position_after_consecutive_losses:
    enabled: true
    days: 3
    reduction: 50  # 連續3天虧損 -> 減倉50%
  
  pause_after_large_drawdown:
    enabled: true
    threshold: -15  # 單日回撤 > 15% -> 暫停24小時
```

#### 3. 調整閾值
```yaml
weekly_review:
  suggestion_thresholds:
    high_drawdown:
      threshold: -70  # 回撤超過 -70% 建議減倉
```

---

## 📊 輸出說明

### 每日監控輸出

```json
{
  "date": "2026-04-23",
  "alerts": [
    {
      "level": "warning",
      "metric": "daily_pnl",
      "message": "昨日虧損過大: $-2500",
      "suggested_action": "檢查市場狀況"
    }
  ],
  "daily_stats": {
    "pnl": -2500,
    "win_rate": 45,
    "max_drawdown": -8.5
  }
}
```

### 每週回顧輸出

```json
{
  "summary": {
    "avg_weekly_pnl": 1500,
    "avg_win_rate": 72,
    "worst_drawdown": -58
  },
  "suggestions": [
    {
      "param": "max_position_pct",
      "current": 90,
      "suggested": 92,
      "reason": "表現優秀，可適度提高倉位"
    }
  ]
}
```

---

## 🛡️ 安全機制

### 1. 分層調整策略

| 層級 | 調整內容 | 需確認？ |
|------|----------|----------|
 每日監控 | 自動保護 (減倉/暫停) | 否 |
| 每週回顧 | 生成建議 | 否 |
| 每月調整 | 參數調整 | 是 (建議) |

### 2. 保護參數

以下參數調整需手動確認：
- `long_stop` / `short_stop` (止損參數)
- `max_position_pct` 超過 5% 的調整

### 3. 回滾機制

```bash
# 查看調整歷史
python -c "from adaptive_learning_system import AdaptiveLearningSystem; \
  s = AdaptiveLearningSystem(); \
  print(s.adjustment_history)"

# 手動回滾 (需實現)
# 可通過修改 config/v9_4_config.yaml 手動回復
```

---

## 📈 最佳實踐

### 第一個月 (觀察期)

1. **設置 `auto_adjust: false`**
2. **每日檢查監控報告**
3. **每週審閱建議質量**
4. **手動測試建議效果**

### 第二個月 (測試期)

1. **啟用 `confirm_before_adjust: true`**
2. **對每個建議進行回測驗證**
3. **記錄建議準確率**

### 第三個月+ (自動期)

1. **考慮啟用 `auto_adjust: true`**
2. **持續監控自動調整效果**
3. **定期回顧長期趨勢**

---

## ⚠️ 注意事項

### 不要過度優化

- 市場有隨機性，不要對短期波動過度反應
- 建議至少觀察 2-4 週再進行調整
- 保持核心邏輯穩定 (V9.4 的 90%倉位 + 盈利減倉)

### 黑天鵝保護

- 系統無法預測黑天鵝事件
- 建議設置最大倉位上限 (如 95%)
- 保留部分現金應對極端情況

---

## 🔧 故障排除

### 常見問題

**Q: 系統沒有生成建議？**
A: 檢查是否有足夠的歷史數據 (至少 1 週)。

**Q: 建議質量不高？**
A: 調整配置中的閾值，或延長觀察期。

**Q: 如何停用自動調整？**
A: 修改 `config/adaptive_learning_config.yaml`:
```yaml
mode:
  auto_adjust: false
```

---

## 📞 支援

如有問題，請檢查：
1. 日誌文件: `logs/adaptive_learning.log`
2. 數據庫連接是否正常
3. 配置文件語法是否正確

---

**記住**: 自適應學習是長期過程，耐心和紀律是關鍵！ 🎯
