# FutuTradingBot 系統狀態存檔

**存檔時間**: 2026-03-28 (週六)  
**狀態**: 美股休市，系統待命  
**Z-Score 閾值**: 1.6 (已設定)

---

## 📁 核心檔案

| 檔案 | 用途 | 狀態 |
|------|------|------|
| `src/strategies/zscore_strategy.py` | Z-Score 策略 | ✅ 閾值 1.6 |
| `src/indicators/technical.py` | 技術指標 | ✅ 含 Z-Score |
| `src/data/market_data.py` | 數據獲取 | ✅ 含 Z-Score 實時 |
| `src/dashboard/app.py` | Dashboard API | ✅ 含 Z-Score 端點 |
| `templates/dashboard.html` | 前端界面 | ✅ 含 Z-Score 面板 |

---

## 🚀 週一開市前檢查清單

- [ ] 啟動 Futu OpenD (20:30)
- [ ] 啟動 Realtime Bridge (20:35)
- [ ] 啟動 Dashboard (20:40)
- [ ] 驗證 TQQQ 價格更新
- [ ] 啟動 Z-Score 策略
- [ ] 監察首筆交易

---

## 📝 模擬交易系統

**位置**: `src/simulation/zscore_paper_trading.py` (將創建)

**功能**:
- 模擬交易執行（不真實下單）
- 記錄模擬交易結果
- 與實盤系統獨立運行

---

*存檔完成，等待週一開市*
