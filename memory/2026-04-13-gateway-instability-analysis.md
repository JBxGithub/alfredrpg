# Gateway 不穩定性分析報告

**日期**: 2026-04-13  
**調查者**: 呀鬼 (Alfred)  
**嚴重程度**: 🔴 高

---

## 問題描述

用戶報告：「最近只要似有關群組或者 Gateway 既事你都會自動關機」

## 調查發現

### 1. creds.json 頻繁損壞

從系統日誌 (`openclaw-2026-04-12.log`) 發現極其嚴重的問題：

- **4月12日單日損壞次數**: 20 次
- **平均損壞間隔**: 30-45 分鐘
- **備份恢復機制**: 運作正常，但頻繁觸發

### 損壞時間線（4月12日）

```
07:55:06 → 08:25:10 → 08:55:14 → 09:25:18 → 09:55:22
10:25:26 → 10:55:31 → 11:31:36 → 11:35:32 → 11:51:55
12:10:43 → 12:16:29 → 12:52:12 → 12:53:22 → 13:30:47
14:00:52 → 14:54:56 → 15:25:00 → 23:37:44 → 23:39:09
```

### 2. Gateway 重啟模式

日誌顯示頻繁的 Gateway 重啟序列：

```
1. Gateway failed to start: gateway already running (pid XXXXX)
2. Port 18789 is already in use
3. 再次嘗試啟動 → 成功
4. WebSocket handshake → 超時 (23-25秒)
5. WhatsApp creds.json → 損壞 → 從備份恢復
```

### 3. WebSocket Handshake Timeout

```
handshake: failed
durationMs: 23820
lastFrameMethod: connect
```

---

## 根本原因分析

### 直接原因
1. **Gateway 進程管理問題** — 舊進程未正確終止，新進程無法啟動
2. **WebSocket 連接超時** — 23秒 handshake timeout 過短
3. **WhatsApp 連接不穩定** — 頻繁重連導致 creds 損壞

### 間接原因
1. **channelMaxRestartsPerHour** 設置過高（默認10次）
2. **channelStaleEventThresholdMinutes** 設置過短（默認30分鐘）
3. 可能與群組消息處理有關（用戶報告群組相關時出問題）

---

## 已採取的修復措施

### 2026-04-13 00:31

調整 Gateway 配置 (`~/.openclaw/openclaw.json`)：

```json
{
  "gateway": {
    "channelStaleEventThresholdMinutes": 60,
    "channelMaxRestartsPerHour": 5
  }
}
```

**變更說明**:
- 將 stale event 閾值從 30 分鐘增加至 60 分鐘
- 將每小時最大重啟次數從 10 次降低至 5 次

---

## 風險評估

| 風險 | 等級 | 說明 |
|------|------|------|
| WhatsApp 帳號被標記 | 🔴 高 | 頻繁重連可能觸發 WhatsApp 反垃圾機制 |
| 群組消息丟失 | 🔴 高 | Gateway 不穩定期間可能錯過消息 |
| 用戶體驗下降 | 🟠 中 | 頻繁「自動關機」影響信任度 |
| 數據不一致 | 🟡 低 | creds 恢復可能導致 session 狀態丟失 |

---

## 後續監控建議

1. **監控 creds.json 損壞頻率** — 檢查是否仍頻繁發生
2. **觀察 Gateway 重啟次數** — 確認每小時不超過 5 次
3. **測試群組消息穩定性** — 驗證群組相關操作是否正常
4. **檢查 WhatsApp 連接狀態** — 確認無頻繁斷線

---

## 待決定事項

1. 是否需要完全重啟 Gateway 以應用新配置？
2. 是否需要更新 OpenClaw 至 2026.4.11？
3. 是否需要檢查 WhatsApp 帳號健康狀態？

---

**報告狀態**: ✅ 已記錄，配置已調整，待觀察效果
