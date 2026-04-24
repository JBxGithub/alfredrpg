# 免費 OCR 供應商比較（非中國）

## 🏆 推薦方案

### 1. OCR.space ⭐ 最佳免費選擇
- **價格**: 完全免費，無需註冊
- **額度**: 無限制（但請合理使用）
- **支援**: JPG, PNG, GIF, PDF
- **語言**: 支援中文、英文
- **優點**: 簡單易用、無需 API Key
- **缺點**: 準確度中等
- **官網**: https://ocr.space/

### 2. Google Cloud Vision API
- **價格**: 每月 1000 次免費
- **額度**: 1000 requests/month
- **支援**: 圖片、PDF
- **語言**: 200+ 語言，中文優秀
- **優點**: 準確度極高、Google 技術
- **缺點**: 需要信用卡設定帳單
- **官網**: https://cloud.google.com/vision

### 3. Tesseract OCR (本地運行)
- **價格**: 完全免費開源
- **額度**: 無限制
- **支援**: 圖片
- **語言**: 100+ 語言
- **優點**: 離線運行、無網路依賴、資料不上傳
- **缺點**: 準確度依賴訓練資料、需要本地安裝
- **安裝**: `pip install pytesseract`

### 4. Microsoft Azure Computer Vision
- **價格**: 每月 5000 次免費
- **額度**: 5000 requests/month
- **支援**: 圖片、PDF
- **語言**: 100+ 語言
- **優點**: Microsoft 技術、準確度高
- **缺點**: 需要 Azure 帳號
- **官網**: https://azure.microsoft.com/services/cognitive-services/computer-vision/

---

## 建議

### 方案 A：OCR.space（最簡單）
- 無需註冊、無需 API Key
- 立即使用
- 適合快速測試和個人使用

### 方案 B：Google Vision（最準確）
- 每月 1000 次免費對個人足夠
- 準確度最高
- 需要設定 Google Cloud 帳號

### 方案 C：Tesseract（最私密）
- 完全離線
- 資料不上傳雲端
- 需要安裝和設定

---

## 實作建議

我建議採用 **多層備援架構**：

```
1. 主要: OCR.space (免費、快速)
2. 備援: Google Vision (準確度高)
3. 離線: Tesseract (完全私密)
```

這樣即使某個服務失效，系統仍能運作。
