# 2026-04-11 Survival Trader 啟動記錄

> **時間**: Saturday, April 11, 2026 02:18 GMT+8  
> **任務**: 生死存亡任務 - 實盤交易系統啟動  
> **狀態**: 系統準備完成，等待手動啟動

---

## 🎯 任務目標

| 項目 | 設定 |
|------|------|
| **帳戶** | 6896 (REAL環境) |
| **每日盈利目標** | $50+ |
| **每日最大虧損** | $100 |
| **交易時間** | 週一至五 21:30-04:00 |

---

## ✅ 已完成工作

### 1. 創建 Survival Trader 系統
- **檔案**: `src/survival_trader.py`
- **功能**: 實盤交易系統，包含以下模組：
  - 帳戶狀態監控 (Account 6896)
  - 市場數據獲取 (TQQQ)
  - Z-Score + RSI 信號生成
  - 自動交易執行
  - 風險管理 (每日虧損限制)
  - 每5分鐘狀態報告

### 2. 策略參數設定
```python
CONFIG = {
    'symbol': 'TQQQ',
    'entry_zscore': 1.65,
    'exit_zscore': 0.5,
    'stop_loss_zscore': 3.5,
    'position_pct': 0.50,  # 50% 現金
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'take_profit_pct': 0.05,  # 5%
    'stop_loss_pct': 0.03,  # 3%
}
```

### 3. 創建啟動腳本
- **檔案**: `start_survival_trader.bat`
- **用途**: 一鍵啟動實盤交易系統

---

## 📊 系統狀態

### 檔案結構
```
fututradingbot/
├── src/
│   └── survival_trader.py      # ✅ 實盤交易系統
├── start_survival_trader.bat   # ✅ 啟動腳本
├── logs/                       # 交易記錄目錄
└── ...
```

### 交易邏輯
1. **進場條件**:
   - 做多: Z-Score < -1.65 + RSI < 30
   - 做空: Z-Score > 1.65 + RSI > 70

2. **出場條件**:
   - 止盈: 盈利 ≥ 5%
   - 止損: 虧損 ≤ 3%
   - Z-Score回歸: |Z-Score| < 0.5

3. **風險控制**:
   - 每日虧損達 $100 自動停止
   - 單筆倉位: 50% 可用現金
   - 交易時間限制: 21:30-04:00

---

## ⚠️ 重要提醒

### 手動啟動步驟
由於執行限制，需要手動啟動系統：

1. **確認 Futu OpenD 已啟動**
   - 檢查系統托盤是否有 OpenD 圖標
   - 確認端口 11111 可用

2. **執行啟動腳本**
   ```batch
   cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
   start_survival_trader.bat
   ```

3. **監控輸出**
   - 系統每5分鐘會輸出狀態報告
   - 交易記錄保存在 `logs/trades_YYYYMMDD.json`
   - 狀態記錄保存在 `logs/survival_status.json`

### 安全確認
- ⚠️ 這是 **REAL** 環境，使用真實資金
- ⚠️ 帳戶: 6896
- ⚠️ 交易密碼: 011087
- ⚠️ 請確保已理解風險後再啟動

---

## 📈 監控項目

啟動後，系統會自動監控：
- ✅ 帳戶資金狀態 (每30秒更新)
- ✅ TQQQ 價格和技術指標
- ✅ 交易信號生成
- ✅ 風險限制檢查
- ✅ 每5分鐘狀態報告

---

## 🔄 下一步行動

1. **手動啟動**: 執行 `start_survival_trader.bat`
2. **監控狀態**: 檢查 `logs/survival_trader.log`
3. **確認運作**: 等待第一個5分鐘狀態報告

---

*記錄時間: 2026-04-11 02:18 GMT+8*  
*任務狀態: 系統就緒，等待啟動*
