---
name: alfred-browser
version: "2.1.0"
description: 呀鬼瀏覽器助手 - 你話想點，我識做
author: Alfred (for Burt only)
private: true
---

# 呀鬼瀏覽器助手 v2.1

> 「靚仔，你想做咩，講句就得」

**呢個係瀏覽器助手，唔係儀表板。儀表板功能喺 `Alfred dashboard/`。**

---

## 🚀 快速開始

### 直接講你想做咩

```
你：幫我開個網頁睇下天氣
呀鬼：(自動開瀏覽器，去天氣網站)

你：幫我睇下 X 有咩新消息
呀鬼：(自動開 Chrome，入 X，俾你睇 feed)

你：幫我搵下 iPhone 16 幾錢
呀鬼：(自動搜尋，比較價錢)
```

### Python 用法

```python
from skills.alfred_browser import 呀鬼

# 你想做咩，講句就得
呀鬼.幫我開個網頁("youtube.com")
呀鬼.幫我搜尋("iPhone 16 價錢")
呀鬼.幫我睇下_X_有咩新消息()
```

---

## 🛠️ 高級用法：連接已登入的 Chrome

### 使用場景

- 需要訪問已登入的網站（如 Kimi API Platform、Gmail 等）
- 需要獲取登入後的頁面信息
- 需要截圖或操作已登入的網頁

### 步驟 1: 關閉現有 Chrome

```powershell
# 關閉所有 Chrome 進程
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 步驟 2: 用調試模式啟動 Chrome

```powershell
# 創建臨時 user-data-dir 並複製登入憑證
$tempDir = "C:\temp\chrome-debug-profile"
New-Item -ItemType Directory -Path "$tempDir\Default" -Force | Out-Null

# 複製 Cookies 和 Login Data（保留登入狀態）
$sourceProfile = "C:\Users\BurtClaw\AppData\Local\Google\Chrome\User Data\Default"
Copy-Item "$sourceProfile\Cookies" "$tempDir\Default\" -Force -ErrorAction SilentlyContinue
Copy-Item "$sourceProfile\Login Data" "$tempDir\Default\" -Force -ErrorAction SilentlyContinue
Copy-Item "$sourceProfile\Local Storage" "$tempDir\Default\" -Recurse -Force -ErrorAction SilentlyContinue

# 啟動 Chrome 並開啟遠程調試
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --remote-allow-origins=* `
  --user-data-dir=$tempDir `
  https://platform.kimi.ai/console/account
```

### 步驟 3: 創建 DevToolsActivePort 文件

```powershell
# 創建 DevToolsActivePort 文件（讓 OpenClaw 找到 Chrome）
$devToolsPortPath = "C:\temp\chrome-debug-profile\DevToolsActivePort"
"9222`nws://127.0.0.1:9222/devtools/browser/<browser-id>" | Out-File -FilePath $devToolsPortPath -Encoding ASCII
```

### 步驟 4: 使用 browser 工具連接

```javascript
// 導航到目標網頁
browser open --url "https://platform.kimi.ai/console/account" --profile user

// 獲取頁面快照
browser snapshot --target-id <target-id>

// 點擊元素
browser act --kind click --ref <ref>

// 截圖
browser screenshot --target-id <target-id> --full-page
```

---

## 📋 完整示例：獲取 Kimi API Platform 信息

### 1. 啟動 Chrome（PowerShell）

```powershell
# 關閉 Chrome
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 準備臨時 profile
$tempDir = "C:\temp\chrome-debug-profile"
New-Item -ItemType Directory -Path "$tempDir\Default" -Force | Out-Null
$sourceProfile = "C:\Users\BurtClaw\AppData\Local\Google\Chrome\User Data\Default"
Copy-Item "$sourceProfile\Cookies" "$tempDir\Default\" -Force -ErrorAction SilentlyContinue
Copy-Item "$sourceProfile\Login Data" "$tempDir\Default\" -Force -ErrorAction SilentlyContinue
Copy-Item "$sourceProfile\Local Storage" "$tempDir\Default\" -Recurse -Force -ErrorAction SilentlyContinue

# 啟動 Chrome
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --remote-allow-origins=* `
  --user-data-dir=$tempDir `
  https://platform.kimi.ai/console/account
```

### 2. 創建 DevToolsActivePort

```powershell
$devToolsPortPath = "C:\temp\chrome-debug-profile\DevToolsActivePort"
"9222`nws://127.0.0.1:9222/devtools/browser/09985573-8f61-4c36-86f0-54640664f788" | Out-File -FilePath $devToolsPortPath -Encoding ASCII
```

### 3. 使用 browser 工具操作

```javascript
// 打開網頁
browser open --url "https://platform.kimi.ai/console/account" --profile user

// 獲取頁面信息
browser snapshot --target-id "2"

// 點擊 API Keys 菜單
browser act --kind click --ref "1_25"

// 等待頁面加載
Start-Sleep -Seconds 2

// 獲取 API Keys 信息
browser snapshot --target-id "2"

// 點擊 Usage Limits
browser act --kind click --ref "1_27"

// 截圖保存
browser screenshot --target-id "2" --full-page
```

---

## 🎯 功能一覽

| 你想做咩 | 點講 |
|---------|------|
| 開網頁 | `呀鬼.幫我開個網頁("youtube.com")` |
| 搜尋 | `呀鬼.幫我搜尋("天氣預報")` |
| 睇 X/Twitter | `呀鬼.幫我睇下_X_有咩新消息()` |
| 發推 | `呀鬼.幫我發推("Hello")` |
| 填表 | `呀鬼.幫我填表({"姓名": "Burt"})` |
| 截圖 | `呀鬼.影張相("截圖.png")` |
| 撳按鈕 | `呀鬼.撳呢個("登入")` |
| 打字 | `呀鬼.打呢句("Hello")` |
| 讀網頁 | `呀鬼.幫我睇下呢個網頁講咩()` |
| 比價 | `呀鬼.幫我比較下價錢("iPhone 16")` |
| 監察網頁 | `呀鬼.幫我監察個網頁(url)` |

---

## 🔧 智能模式

呀鬼會自動揀最適合嘅方式：

1. **你有開 Chrome？** → 用 Chrome 控制（保留登入）
2. **冇開 Chrome？** → 用背景瀏覽器（自動開）
3. **要自然語言？** → 用 Stagehand（講句就得）

---

## 📸 實際例子

### 例 1：獲取已登入網站信息

```powershell
# 1. 啟動 Chrome（見上文步驟）
# 2. 使用 browser 工具
browser open --url "https://platform.kimi.ai/console/account" --profile user
browser snapshot --target-id "2"
```

### 例 2：自動填表

```python
呀鬼.幫我填表({
    "姓名": "Burt",
    "電話": "91234567",
    "電郵": "burt@example.com"
})
```

### 例 3：睇 X

```python
呀鬼.幫我睇下_X_有咩新消息()
```

### 例 4：發推文

```python
呀鬼.幫我發推("今日天氣真好！")
```

---

## ❓ 常見問題

**Q: 點解有時慢？**  
A: 如果用 Chrome，要等佢載入。用背景瀏覽器會快啲。

**Q: 點解有時要登入？**  
A: 如果用背景瀏覽器，係新 session。用 Chrome 就會保留你嘅登入。

**Q: 點解連接 Chrome 時話搵唔到 DevToolsActivePort？**  
A: 需要手動創建呢個文件，見上文「步驟 3」。

**Q: Chrome 話 "DevTools remote debugging requires a non-default data directory"？**  
A: 必須使用 `--user-data-dir` 指定非默認的 user data 目錄。

**Q: 呢個係咩 skill？**  
A: 呢個係「呀鬼瀏覽器助手」。儀表板功能已經整合到 `Alfred dashboard/` 目錄。

---

## 📝 更新日誌

- **v2.1.0** (2026-04-19): 新增 Chrome 遠程調試連接方法，詳細步驟說明
- **v2.0.0** (2026-04-18): 清理完成，分離儀表板功能
- **v2.0.0** (2026-04-17): 人性化設計，講句就得

---

*「靚仔，你想點，講句就得」- 呀鬼*
