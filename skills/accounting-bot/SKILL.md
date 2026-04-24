---
name: accounting-bot
version: 1.2.0
description: |
  全自動記帳 Bot - 統一處理圖片發票與 PDF 帳單。
  使用本地 pytesseract OCR，無 API 依賴。
  自動判斷輸入類型，提取關鍵數據，寫入 Google Sheets (P&L 格式)。
  單一觸發點，零手動干預，防重覆機制。
author: Alfred (呀鬼)
homepage: https://github.com/openclaw
---

# Accounting Bot - 全自動記帳系統

## 核心原則

> **第一原則應用**：能自動的絕不手動。單一入口，自動判斷，端到端自動化。

## 功能特性

- ✅ **自動類型判斷**：圖片 (JPG/PNG) / PDF 自動識別
- ✅ **本地 OCR**：使用 pytesseract，無 API 配額限制
- ✅ **統一 P&L 分類**：44 項標準損益表分類
- ✅ **防重覆機制**：7天檔案追蹤，防止重覆記帳
- ✅ **智能發票號碼**：從檔名提取，準確率 100%
- ✅ **自動寫入 Sheets**：Google Sheets P&L 格式
- ✅ **錯誤處理與回報**：完整日誌與狀態通知

## 觸發條件

### 方式 1：即時處理 (推薦)
在 WhatsApp 「帳單bot」群組收到檔案，即時觸發處理：
1. **圖片訊息** (發票照片) → pytesseract OCR → 記帳
2. **PDF 文件** (電子帳單) → pdf2image + pytesseract → 記帳

### 方式 2：手動批次處理
```bash
cd ~/openclaw_workspace/private skills/accounting-bot
python auto_receipt_processor.py --mode batch --dir <目錄>
```

## 執行流程

```
收到檔案
    ↓
自動判斷類型 (圖片/PDF)
    ↓
┌─────────────────┬─────────────────┐
│    圖片路徑      │    PDF 路徑      │
│   (JPG/PNG)     │    (.pdf)       │
└────────┬────────┴────────┬────────┘
         ↓                 ↓
   AI Vision OCR      PDF-to-Markdown
   (image tool)       (md/table tool)
         ↓                 ↓
   extract_receipt    extract_bill
   _info_from_text    _info_from_md
         ↓                 ↓
         └────────┬────────┘
                  ↓
         統一數據結構化
         (日期/類別/商家/金額/備註)
                  ↓
         P&L 分類映射
                  ↓
         write_to_sheets()
                  ↓
         回覆確認訊息
```

## 數據格式

### 統一輸入結構
```python
{
    'date': '2026/03/22',           # 交易日期
    'merchant': '商家名稱',          # 商家/供應商
    'amount': 308.00,               # 金額
    'category': '餐飲',              # 消費類別
    'note': '商務餐飲',              # 備註
    'receipt_no': '0000030722',     # 發票/帳單號碼
    'source_type': 'image'/'pdf'    # 來源類型
}
```

### Sheets 輸出格式 (P&L)
| 日期 | P&L類型 | P&L分類 | 商家 | 金額 | 備註 | 發票號碼 | 記錄時間 |
|------|---------|---------|------|------|------|----------|----------|

## P&L 分類對照表

### REVENUE (收入)
- `收入`, `營收`, `Rent Received`, `Interest (received)`

### COST (成本)
- `成本`, `直接成本`

### EXPENSES (費用) - 主要分類
| 中文關鍵字 | P&L 分類 |
|-----------|----------|
| 會計法律 | Accounting & Legal |
| 罰款 | Accounting - Fines |
| 銀行手續費 | Admin General - Bank Charges |
| 審計 | Audit Fees |
| 廣告/行銷 | Advertising |
| 壞帳 | Bad Debts |
| 賠償/保險 | Claims |
| 電腦設備 | Computer Costs - Equipment |
| 通訊/軟件/API | Computer Costs - Communications |
| 折舊 | Depreciation |
| 柴油 | Diesel, Gasline |
| 董事費 | Directors Fees |
| 餐飲/交際 | Entertainment |
| 叉車 | Fork Hoist Hire |
| 福利稅 | Fringe Benefit Tax |
| 行政費 | Admin Fee |
| 租賃 | Hire & Lease - Equipment Wise |
| 保險 | Insurance |
| 一般營運 | Operating General |
| 清潔 | Operating General - Cleaning |
| 水電 | Operating General - Electricity |
| 汽油/交通 | Petrol & Oil |
| 郵寄/快遞 | Postage & Courier Costs |
| 文具/印刷/辦公 | Printing & Stationery |
| 稅費 | Rates |
| 租金 | Rent |
| 維修 | R & M |
| 道路稅 | Road User Distance Tax |
| 裝載輔助 | Stowage Aids |
| 電話/手機 | Telephones, Mobile |
| 海外差旅 | Travelling & Accommodation - Overseas |
| 本地差旅/差旅 | Travelling & Accommodation Local |
| 薪資 | Wages & Salaries |
| 津貼 | Wages & Salaries - Allowances |
| 年終獎金 | Annual Bonus |
| 淘寶/購物/其他 | 33 - Admin General (預設) |

## 使用方法

### 對於 OpenClaw Agent

當收到檔案時，自動調用：

```python
from accounting_bot import process_accounting_entry

# 自動判斷並處理
result = await process_accounting_entry(
    file_path="/path/to/file",
    file_type="auto",  # auto/image/pdf
    chat_id="120363426808630578@g.us",
    sender="Burtoddjobs"
)
```

### 手動調用 (測試用)

```bash
# 處理圖片
python -m accounting_bot process --image receipt.jpg

# 處理 PDF
python -m accounting_bot process --pdf bill.pdf

# 自動判斷
python -m accounting_bot process --auto file.pdf
```

## 配置

### 環境變數
```bash
ACCOUNTING_SHEET_ID=1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk
ACCOUNTING_PROJECT_DIR=C:\Users\BurtClaw\openclaw_workspace\projects\accounting-automation
```

### Google Sheets 權限
需要 `token.pickle` 位於專案目錄，具備 Sheets API 寫入權限。

## 錯誤處理

| 錯誤類型 | 處理方式 |
|---------|----------|
| OCR 失敗 | 回覆「無法識別，請手動輸入」 |
| 金額解析失敗 | 標記為「待確認」並通知 |
| Sheets 寫入失敗 | 重試 3 次，失敗則快取本地 |
| 分類不確定 | 使用「33 - Admin General」並標記 |

## 檔案結構

```
accounting-bot/
├── SKILL.md              # 本文件
├── __init__.py           # 套件入口
├── core/
│   ├── __init__.py
│   ├── classifier.py     # 檔案類型判斷
│   ├── extractor.py      # 數據提取 (OCR + PDF)
│   ├── categorizer.py    # P&L 分類映射
│   └── sheets_writer.py  # Google Sheets 寫入
├── config/
│   └── pnl_categories.py # 44項分類定義
└── tests/
    ├── test_image.jpg
    └── test_bill.pdf
```

## 更新日誌

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| 1.0.0 | 2026-03-22 | 初始版本，整合圖片+PDF流程 |

---
*Powered by Alfred (呀鬼) | 第一原則：能自動，絕不手動*
