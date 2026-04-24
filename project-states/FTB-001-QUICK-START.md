# FTB-001 快速重啟指南

> **適用場景**: 未來重啟 Future Trading Bot 專案時  
> **預計時間**: 30分鐘內恢復開發狀態  
> **最後更新**: 2026-03-29  
> **策略版本**: Z-Score Mean Reversion Final

---

## ⚡ 5分鐘快速檢查清單

### 1. 市場條件確認 (1分鐘)
```
□ VIX < 20 (檢查 https://www.cboe.com/tradable_products/vix/)
□ 美伊戰爭是否停火
□ 特朗普政策是否連續2週穩定
□ 結論: 是否適合重啟?
```

### 2. 檔案完整性檢查 (2分鐘)
```powershell
cd C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot
ls -la
# 確認以下目錄存在:
# - src/
# - tests/
# - config/
# - strategies/
# - backtest/
# - data/
# - logs/
# - risk/
```

### 3. 環境驗證 (2分鐘)
```powershell
# 檢查 Python
python --version  # 應為 3.8+

# 檢查依賴
pip list | findstr futu-api
pip list | findstr scikit-learn
pip list | findstr pandas

# 檢查 OpenD
# 確認 OpenD 已啟動並登入
# 訪問 http://localhost:11111 (或配置的端口)
```

---

## 🔄 重啟步驟

### Step 1: 讀取封存狀態 (5分鐘)
1. 閱讀 `project-states/archived/project-ftb-001-suspended.md`
2. 確認暫停原因是否已解除
3. 檢查「重啟條件」是否滿足

### Step 2: 代碼驗證 (10分鐘)
```powershell
# 運行完整測試套件
cd C:/Users/BurtClaw/openclaw_workspace/projects/future-trading-bot
python -m pytest tests/ -v

# 預期結果: 197/197 測試通過
```

### Step 3: 模擬測試 (10分鐘)
```powershell
# 啟動模擬模式
python src/main.py --mode simulate

# 檢查:
# - OpenD 連接成功
# - 行情數據接收正常
# - 策略信號生成正常
# - 風控系統運作正常
```

### Step 4: 訂閱與實盤準備 (5分鐘)
1. 訂閱 Nasdaq Basic (~HK$468/月)
2. 確認模擬賬戶資金充足
3. 設置交易參數 (建議初始: 1-10股)
4. 啟動 Dashboard (localhost:8080)

---

## 📋 關鍵配置

### 配置文件位置
```
config/config.yaml
```

### 關鍵設定
```yaml
trading:
  default_trd_env: "SIMULATE"  # 重啟時必須為 SIMULATE
  # default_trd_env: "REAL"    # 驗證後才切換

futu:
  host: "127.0.0.1"
  port: 11111

# Z-Score Mean Reversion 策略參數（2026-03-29 最終版）
strategy:
  zscore:
    entry_threshold: 1.65      # 進場閾值
    exit_threshold: 0.5        # 出場閾值
    stop_loss_threshold: 3.5   # 止損閾值
    lookback_period: 60        # 回望期（日）
  rsi:
    period: 14
    overbought: 70             # 超買閾值
    oversold: 30               # 超賣閾值
  risk:
    take_profit_pct: 0.05      # 止盈 5%
    stop_loss_pct: 0.03        # 止損 3%
    time_stop_days: 7          # 時間止損 7天
  position:
    base_capital: 100000       # 基礎資金 $100,000
    position_pct: 0.50         # 單筆倉位 50%
```

---

## 🐛 已知問題 (重啟時需修復)

| 問題 | 嚴重程度 | 修復方法 |
|------|----------|----------|
| 行情數據需先訂閱 | 中 | 調整順序: 先 `subscribe()` 再 `get_stock_quote()` |
| 撤單 Series 類型 | 低 | 使用 `.iloc[0]` 提取具體值 |

---

## 📞 緊急聯繫

如遇問題:
1. 檢查 `logs/` 目錄最新日誌
2. 閱讀 `PROJECT_TRACKER.md` 歷史記錄
3. 參考富途 API 文檔: https://www.futunn.com/OpenAPI

---

## ✅ 重啟成功標準

- [ ] 104項測試全部通過
- [ ] OpenD 連接成功
- [ ] 模擬交易正常執行
- [ ] Dashboard 可正常訪問
- [ ] 風控系統無警報

---

*重啟完成後，請更新本檔案並繼續開發日誌。*
