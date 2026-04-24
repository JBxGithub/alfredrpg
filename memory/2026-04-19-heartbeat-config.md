# Heartbeat 配置更新記錄

**日期**: 2026-04-19  
**時間**: 13:26 GMT+8  
**操作者**: 靚仔 (Burt)  
**執行者**: 呀鬼 (Alfred)

---

## 更新內容

### 1. 正常 Heartbeat (已修改)
| 項目 | 舊設定 | 新設定 |
|------|--------|--------|
| **頻率** | 30 分鐘 | **240 分鐘 (4小時)** |
| **運作時間** | 08:00-23:00 | **08:00-20:00** |
| **時區** | Asia/Hong_Kong | Asia/Hong_Kong (不變) |
| **目標** | last (發送到最後活躍對話) | **none (不發送)** |

**原因**: 靚仔常不在電腦前，減少頻密 heartbeat 干擾

### 2. Trading System Heartbeat (新增)
| 項目 | 設定 |
|------|------|
| **頻率** | 每 15 分鐘 |
| **運作時間** | Mon-Fri 20:15-04:30 (Asia/Hong_Kong) |
| **對應美股時間** | Mon-Fri 盤前+正常+盤後交易時段 |
| **觸發方式** | Cron Job (systemEvent) |
| **檢查內容** | 交易信號、風險限制、止損止盈、TQQQ動量 |
| **通知方式** | 只在有警報時通知 |

**Cron Expression**: `*/15 20-23,0-4 * * 1-5`

---

## 技術細節

### 配置檔案修改
- **檔案**: `~/.openclaw/openclaw.json`
- **路徑**: `agents.defaults.heartbeat`
- **新增欄位**:
  - `every`: "240m"
  - `activeHours.start`: "08:00"
  - `activeHours.end`: "20:00"
  - `target`: "none"
  - `includeSystemPromptSection`: true

### Cron Job 新增
- **Job ID**: `b62ad571-3a4f-4c92-8d62-4bccbc9248f4`
- **名稱**: Trading System Heartbeat
- **類型**: systemEvent (輕量級)
- **下次執行**: 2026-04-19 20:15

---

## 運作邏輯

```
時間軸 (Asia/Hong_Kong):

08:00 ────────────────── 20:00 ───── 20:15 ─────── 04:30 ─── 08:00
    [正常 Heartbeat 每4小時]        [Trading Heartbeat 每15分鐘]
         (08:00, 12:00, 16:00, 20:00)    (只在 Mon-Fri)
```

---

## 注意事項

1. **正常 Heartbeat** 現在只會喺 08:00-20:00 之間每 4 小時觸發一次
2. **Trading Heartbeat** 只會喺美股交易時段 (Mon-Fri 20:15-04:30) 運作
3. 兩個 heartbeat 都會讀取 HEARTBEAT.md，但 Trading Heartbeat 會專注於交易相關檢查
4. 如果冇特別事情，兩者都會回覆 `HEARTBEAT_OK`

---

## 驗證

- [x] Gateway 配置已更新
- [x] Gateway 已重啟
- [x] Trading System Heartbeat Cron Job 已創建
- [x] 下次執行時間已確認

---

*記錄由呀鬼自動生成*
