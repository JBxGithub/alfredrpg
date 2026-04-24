# 🚨 緊急啟動指令

## 立即執行步驟

### 步驟 1: 檢查 OpenD 狀態
打開 PowerShell 或 CMD，執行：
```powershell
netstat -an | findstr "11111"
```
如果看到 `LISTENING`，表示 OpenD 正在運行。

### 步驟 2: 啟動 Survival Trader
打開 PowerShell，執行：
```powershell
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
C:\Python314\python.exe survival_trader.py
```

### 步驟 3: 監控輸出
程序啟動後會顯示：
- 連接狀態
- 帳戶資金
- 交易信號
- 每30秒心跳

## 快速啟動檔案

已創建以下檔案供手動執行：

1. **start_survival_trader.bat** - 雙擊啟動
   - 路徑: `C:\Users\BurtClaw\openclaw_workspace\start_survival_trader.bat`

2. **survival_launcher.py** - 智能啟動器
   - 路徑: `C:\Users\BurtClaw\openclaw_workspace\survival_launcher.py`
   - 命令: `C:\Python314\python.exe survival_launcher.py`

3. **check_opend.bat** - 檢查 OpenD
   - 路徑: `C:\Users\BurtClaw\openclaw_workspace\check_opend.bat`

## 交易策略配置

```
帳戶: 6896 (閒置帳戶)
每日目標: $50+ 盈利
每日止損: $100 最大虧損
倉位: 30% (保守)
交易時間: 美股市場 21:30-04:00
```

## 注意事項

- 確保 Futu OpenD 已啟動並登入
- 確保帳戶 6896 有足夠資金
- 監控輸出確保正常運行

---
**創建時間**: 2026-04-11 12:25 GMT+8
**任務**: 生存挑戰 - 啟動實盤交易
