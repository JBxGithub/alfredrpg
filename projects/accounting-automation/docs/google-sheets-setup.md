# Google Sheets 設定指南

## 步驟 1: 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 點擊左上角的專案選擇器，建立新專案
3. 輸入專案名稱（例如：Accounting Bot）
4. 點擊「建立」

## 步驟 2: 啟用 Google Sheets API

1. 在導覽選單中選擇「API 和服務」>「程式庫」
2. 搜尋 "Google Sheets API"
3. 點擊「啟用」

## 步驟 3: 建立 Service Account

1. 前往「API 和服務」>「憑證」
2. 點擊「建立憑證」>「Service Account"
3. 輸入 Service Account 名稱（例如：accounting-bot）
4. 點擊「建立並繼續」
5. 角色選擇「編輯者」(Editor)
6. 點擊「完成」

## 步驟 4: 下載憑證檔案

1. 在 Service Account 列表中找到剛建立的帳號
2. 點擊進入詳細頁面
3. 選擇「金鑰」分頁
4. 點擊「新增金鑰」>「建立新的金鑰」
5. 選擇 JSON 格式
6. 點擊「建立」，檔案會自動下載

## 步驟 5: 設定專案

1. 將下載的 JSON 檔案重新命名為 `credentials.json`
2. 移動到專案目錄：
   ```
   ~/openclaw_workspace/projects/accounting-automation/credentials.json
   ```

## 步驟 6: 分享試算表

1. 開啟你的 Google Sheet：https://docs.google.com/spreadsheets/d/1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk/edit
2. 點擊右上角的「分享」
3. 加入 Service Account 的 email（在 credentials.json 中的 `client_email` 欄位）
4. 權限設為「編輯者」
5. 點擊「傳送」

## 步驟 7: 測試

執行測試指令：
```bash
cd ~/openclaw_workspace/projects/accounting-automation
python src/sheets_sync.py
```

如果看到「✅ 測試資料已儲存到 Google Sheets」，表示設定成功！

## 常見問題

### Q: 出現 "Permission denied" 錯誤
A: 確認已將 Service Account email 加入試算表的分享名單

### Q: 出現 "API not enabled" 錯誤
A: 確認已在 Google Cloud Console 啟用 Google Sheets API

### Q: 找不到 Service Account email
A: 開啟 credentials.json，尋找 `client_email` 欄位
