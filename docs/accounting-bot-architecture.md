# 呀鬼記帳 Bot - 系統架構與規則

## 📊 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    使用者 (WhatsApp)                         │
│                   發送發票圖片 + 指令                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw Gateway (Port 18789)                   │
│         - 接收 WhatsApp 訊息                                 │
│         - 觸發自動化流程                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   核心處理引擎                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Cron Job   │  │  AI Vision  │  │  P&L 分類引擎       │ │
│  │ (30秒檢查)  │  │  (OCR解析)  │  │ (自動/手動分類)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Sheets (P&L 格式)                        │
│  欄位: 日期 | P&L類型 | P&L分類 | 商家 | 金額 | 備註 | 發票號 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 控制指令

| 指令 | 功能 | 狀態 |
|------|------|------|
| `開啟自動記帳` | 啟用 Cron Job 自動處理 | ⏳ 待實施 |
| `關閉自動記帳` | 停用 Cron Job | ⏳ 待實施 |
| `@呀鬼 + 圖片` | 手動觸發處理 | ✅ 可用 |

---

## 📋 P&L 分類規則

### 三層結構
```
REVENUE (收入)
    └── Rent Received
    └── Interest (received)
    └── ...

COST (成本)
    └── 不適用 EXPENSES 的項目

EXPENSES (費用) - 主要分類
    ├── Accounting & Legal
    ├── Accounting - Fines
    ├── Admin General - Bank Charges
    ├── Audit Fees
    ├── Advertising
    ├── Bad Debts
    ├── Claims
    ├── Computer Costs - Equipment
    ├── Computer Costs - Communications, Subscription, API cost
    ├── Depreciation
    ├── Diesel, Gasolines
    ├── Directors Fees
    ├── Entertainment
    ├── Fork Hoist Hire
    ├── Fringe Benefit Tax
    ├── Admin Fee
    ├── Hire & Lease - Equipment Wise
    ├── Insurance
    ├── Operating General
    ├── Operating General - Cleaning
    ├── Operating General - Electricity, Water Supply
    ├── Petrol & Oil
    ├── Postage & Courier Costs
    ├── Printing & Stationery
    ├── Rates
    ├── Rent
    ├── R & M
    ├── Road User Distance Tax
    ├── Stowage Aids
    ├── Telephones, Mobile
    ├── Travelling & Accommodation - Overseas
    ├── Travelling & Accommodation Local
    ├── Wages & Salaries
    ├── Wages & Salaries - Allowances
    └── Annual Bonus
```

---

## 🔄 運作流程

### 自動模式 (Cron)
```
每 30 秒檢查群組
    ↓
發現新圖片？
    ├── 是 → AI Vision OCR → 提取資訊 → 詢問分類 → 寫入 Sheets
    └── 否 → 靜音 (不干擾)
```

### 手動模式 (@)
```
@呀鬼 + 發送圖片
    ↓
立即觸發 OCR
    ↓
提取資訊
    ↓
詢問分類 (如有疑問)
    ↓
寫入 Sheets
    ↓
回覆確認
```

---

## 📝 資料格式規範

### Google Sheets 欄位
| 欄位 | 格式 | 範例 |
|------|------|------|
| 日期 | `'YYYY/MM/DD` | `'2026/03/19` |
| P&L類型 | TEXT | EXPENSES |
| P&L分類 | TEXT | Operating General - Cleaning |
| 商家 | TEXT | 淘寶 |
| 金額 | NUMBER | 66.14 |
| 備註 | TEXT | 全林除濕盒 |
| 發票號碼 | TEXT | 2701752998070116791 |
| 記錄時間 | TIMESTAMP | 2026-03-21 23:45:00 |

### 日期格式處理
- 加前導符號 `'` 避免 Excel 轉換為序列號
- 統一格式：`YYYY/MM/DD`

### 商家名稱簡化
- 淘寶訂單 → 統一顯示「淘寶」
- 其他商家 → 保留前 30 字元

---

## ⚠️ 規則與限制

### 分類確認機制
1. **明確分類** → 自動歸類
2. **模糊分類** → 詢問用戶
3. **未知項目** → 建議分類並確認

### Token 節省策略
- Cron Job 預設靜音（無新圖片不通知）
- 只在發現新圖片或處理完成時通知
- 用戶可隨時開關自動模式

### 錯誤處理
- OCR 失敗 → 通知用戶手動輸入
- Sheets 寫入失敗 → 重試 3 次後通知
- 分類疑問 → 立即詢問，不猜測

---

## 🔧 技術堆疊

| 組件 | 技術 |
|------|------|
| 訊息接收 | OpenClaw Gateway |
| OCR 解析 | Kimi Vision AI |
| 資料儲存 | Google Sheets API |
| 自動排程 | OpenClaw Cron |
| 程式語言 | Python 3.11 |

---

## 📊 狀態監控

- **Cron Job ID**: `92883bd4-5721-40d3-89f7-bdb58609b163`
- **檢查頻率**: 每 30 秒
- **Sheets ID**: `1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk`
- **支援幣別**: HKD, CNY, USD (自動識別)

---

*最後更新: 2026-03-21*  
*版本: P&L Format v1.0*
