# 反向 Whisper 研究：TTS + WhatsApp 語音發送

> 日期: 2026-04-11  
> 研究: 呀鬼 (Alfred)

---

## 🎯 問題定義

**目標**: 讓 AI 能夠透過 WhatsApp 發送語音訊息給用戶

**現狀**:
- ✅ 用戶發語音 → AI 接收 (Whisper STT)
- ❌ AI 生成語音 → 用戶接收 (缺失)

---

## 🔍 方案分析

### 方案 1: 直接使用 OpenClaw 發送語音

**可行性**: ❌ 暫不支持

OpenClaw 目前支持：
- 發送文字訊息
- 發送圖片
- ❌ 發送語音訊息

**難度**: 需要修改 OpenClaw 核心代碼

---

### 方案 2: 使用 WhatsApp Business API

**可行性**: ⚠️ 複雜但可行

**所需組件**:
1. Meta Business 賬戶
2. WhatsApp Business API 認證
3. 電話號碼驗證
4. 雲端伺服器（接收 webhook）

**流程**:
```
AI 生成語音 (TTS)
    ↓
保存為 OGG/MP3
    ↓
調用 WhatsApp Business API
    ↓
發送語音訊息
```

**缺點**:
- 需要商業認證
- 有發送限制
- 成本問題

---

### 方案 3: 使用 whatsapp-web.js (推薦)

**可行性**: ✅ 可行

**原理**:
- 使用 Puppeteer 控制 WhatsApp Web
- 模擬人類操作發送語音

**代碼示例**:
```javascript
const { Client, MessageMedia } = require('whatsapp-web.js');
const client = new Client();

// 發送語音
const media = MessageMedia.fromFilePath('./voice.ogg');
client.sendMessage(chatId, media, { sendAudioAsVoice: true });
```

**優點**:
- 開源免費
- 無需商業認證
- 直接使用現有 WhatsApp 賬戶

**缺點**:
- 需要保持 WhatsApp Web 登入
- 可能被封號風險

---

### 方案 4: 使用第三方 TTS 服務 + 短鏈接

**可行性**: ✅ 簡單

**流程**:
```
AI 生成語音
    ↓
上傳到雲端（如 AWS S3）
    ↓
生成短鏈接
    ↓
發送文字訊息："點擊收聽語音回覆: [鏈接]"
```

**優點**:
- 實現簡單
- 無需修改 WhatsApp

**缺點**:
- 用戶體驗差（需要點擊）
- 需要雲存儲

---

## 📊 方案比較

| 方案 | 難度 | 成本 | 用戶體驗 | 風險 | 推薦度 |
|------|------|------|----------|------|--------|
| 1. OpenClaw 原生 | ⭐⭐⭐⭐⭐ | 低 | 最好 | 低 | ❌ |
| 2. Business API | ⭐⭐⭐⭐ | 高 | 好 | 中 | ⚠️ |
| 3. whatsapp-web.js | ⭐⭐⭐ | 低 | 好 | 中 | ✅ |
| 4. 短鏈接方案 | ⭐⭐ | 中 | 差 | 低 | ⚠️ |

---

## 🚀 推薦方案: whatsapp-web.js

### 實現步驟

1. **安裝依賴**
```bash
npm install whatsapp-web.js qrcode-terminal
```

2. **創建 TTS 發送服務**
```javascript
// tts-service.js
const { Client, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client();

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('TTS Service Ready!');
});

// 接收來自 Python 的請求
const express = require('express');
const app = express();

app.post('/send-voice', async (req, res) => {
    const { chatId, audioPath } = req.body;
    const media = MessageMedia.fromFilePath(audioPath);
    await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
    res.json({ success: true });
});

app.listen(3000);
client.initialize();
```

3. **Python 調用**
```python
import requests

def send_voice_to_whatsapp(chat_id, audio_path):
    requests.post('http://localhost:3000/send-voice', json={
        'chatId': chat_id,
        'audioPath': audio_path
    })
```

---

## ⏱️ 工作量評估

| 任務 | 時間 | 難度 |
|------|------|------|
| 設置 Node.js 環境 | 30 分鐘 | ⭐ |
| 安裝 whatsapp-web.js | 15 分鐘 | ⭐ |
| 開發 TTS 發送服務 | 2-3 小時 | ⭐⭐⭐ |
| 整合到 OpenClaw | 1-2 小時 | ⭐⭐⭐ |
| 測試與調試 | 1 小時 | ⭐⭐ |
| **總計** | **5-7 小時** | **中等** |

---

## 🎯 結論

**建議**: 使用 **whatsapp-web.js** 方案

**原因**:
1. 開源免費
2. 直接使用現有 WhatsApp 賬戶
3. 無需商業認證
4. 工作量合理（5-7 小時）

**風險**:
- WhatsApp 可能檢測自動化（但風險可控）
- 需要保持 WhatsApp Web 登入

**下一步**:
如靚仔同意，我可以開始開發此功能。

---

*研究完成*  
*日期: 2026-04-11*
