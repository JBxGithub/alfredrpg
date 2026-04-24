# Accounting Automation Bot

Telegram Bot for automated receipt OCR and accounting.

## 功能

- 📸 拍照記帳：發送相片自動辨識
- 🤖 AI 解析：提取金額、日期、商家、類別
- 💾 自動儲存：同步到 Google Sheets
- 📊 即時統計：查看每日/每月報表

## 安裝

### 1. 安裝依賴

```bash
cd src
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入你的 API Keys
```

### 3. 設定 Google Sheets

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立 Service Account
3. 下載 credentials.json 放到專案根目錄
4. 建立 Google Sheet 並分享給 Service Account email
5. 複製 Spreadsheet ID 到 .env

### 4. 啟動 Bot

```bash
python src/bot.py
```

## 使用方式

1. 在 Telegram 搜尋 `@Ghost_Mode_Claw_bot`
2. 發送 `/start` 開始使用
3. 直接發送發票相片
4. 確認 AI 解析結果
5. 自動記帳完成！

## 指令

- `/start` - 啟動機器人
- `/help` - 顯示說明
- `/status` - 查看今日統計
- `/export` - 匯出報表

## 專案結構

```
.
├── src/
│   ├── bot.py              # 主程式
│   ├── vision_parser.py    # OCR 解析 (Phase 2)
│   ├── sheets_sync.py      # Google Sheets 同步 (Phase 2)
│   └── dashboard.py        # 儀表板 (Phase 3)
├── data/
│   └── receipts.json       # 本地資料儲存
├── logs/
│   └── bot.log            # 執行日誌
├── .env                   # 環境變數 (勿提交)
└── credentials.json       # Google Service Account (勿提交)
```

## Phase 開發計畫

### Phase 1: MVP (現在)
- ✅ Telegram Bot 基礎架構
- ✅ 相片接收與儲存
- ⏳ 整合 Vision AI (Claude/OpenAI)
- ⏳ Google Sheets API 整合

### Phase 2: 優化
- 自動分類邏輯
- 批次處理
- 錯誤修正介面

### Phase 3: Dashboard
- 視覺化報表
- 趨勢分析
- 稅務彙整

## 注意事項

- `.env` 和 `credentials.json` 包含敏感資訊，請勿提交到 Git
- 發票相片會儲存在本地 `data/` 目錄
- 建議定期備份 `data/receipts.json`
