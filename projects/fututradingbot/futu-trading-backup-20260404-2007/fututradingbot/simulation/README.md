# FutuTradingBot 模擬交易系統
# 獨立於實盤系統，用於策略實測
# 創建時間: 2026-03-28
# 用途: 周一實測 Z-Score 策略

## 系統架構

```
simulation/
├── paper_trading_dashboard.py    # 模擬交易 Dashboard (Port 8081)
├── paper_trading_bridge.py       # 模擬交易 Bridge (WebSocket 8766)
├── paper_strategy.py             # 模擬策略 (獨立參數)
├── paper_recorder.py             # 模擬交易記錄器
└── data/
    ├── paper_trades.csv          # 模擬交易記錄
    ├── paper_positions.json      # 模擬持倉
    └── paper_performance.json    # 模擬績效
```

## 與實盤系統的區別

| 項目 | 實盤系統 | 模擬系統 |
|------|---------|---------|
| Dashboard Port | 8080 | 8081 |
| WebSocket Port | 8765 | 8766 |
| 交易執行 | 真實下單 | 模擬記錄 |
| 資金 | 真實資金 | 虛擬 $100,000 |
| 記錄位置 | `logs/trades.csv` | `simulation/data/paper_trades.csv` |
| 策略參數 | 可調整 | 固定測試參數 |

## 啟動指令

```bash
# 1. 啟動模擬 Bridge
python simulation/paper_trading_bridge.py

# 2. 啟動模擬 Dashboard
python simulation/paper_trading_dashboard.py

# 3. 訪問模擬 Dashboard
http://127.0.0.1:8081
密碼: paper2024
```

## 周一實測流程

1. **20:30** - 啟動 Futu OpenD
2. **20:35** - 啟動實盤 Bridge (Port 8765) - 僅觀察
3. **20:35** - 啟動模擬 Bridge (Port 8766) - 實測交易
4. **20:40** - 啟動實盤 Dashboard (Port 8080) - 監控
5. **20:40** - 啟動模擬 Dashboard (Port 8081) - 實測
6. **比較結果** - 每日收盤後比較實盤 vs 模擬表現

## 測試目標

- 驗證 Z-Score 策略在實時市場的表現
- 比較模擬與實盤的差異
- 收集數據優化策略參數
