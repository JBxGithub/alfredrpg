# ClawTeam WhatsApp 配置指南
# 為 DataForge, SignalForge, TradeForge 配置獨立 WhatsApp 身份

## 🎯 目標

為以下 Agent 配置獨立 WhatsApp 號碼，使其能夠：
1. 接收和發送消息
2. 在群組中獨立識別
3. 與中央指揮系統 (呀鬼) 協作

## 📱 需要配置的號碼

| Agent | WhatsApp 號碼 | 狀態 |
|-------|--------------|------|
| DataForge | +85262255569 | ⏳ 待配置 |
| SignalForge | +85262212577 | ⏳ 待配置 |
| TradeForge | +85255086558 | ⏳ 待配置 |
| 呀鬼 (Orchestrator) | +85263609349 | ✅ 已配置 |

---

## 🔧 配置方法

### 方法 1: OpenClaw 多賬號配置 (推薦)

OpenClaw 支持配置多個 WhatsApp 賬號，每個 Agent 可以有自己的身份。

#### 步驟 1: 檢查當前配置

```powershell
# 查看當前 OpenClaw 配置
openclaw config get

# 查看當前 WhatsApp 配置
openclaw status --all
```

#### 步驟 2: 添加新 WhatsApp 賬號

```powershell
# 添加 DataForge WhatsApp
openclaw channel add whatsapp --phone +85262255569 --name DataForge

# 添加 SignalForge WhatsApp
openclaw channel add whatsapp --phone +85262212577 --name SignalForge

# 添加 TradeForge WhatsApp
openclaw channel add whatsapp --phone +85255086558 --name TradeForge
```

#### 步驟 3: 配對流程

每個號碼需要單獨配對：

1. **DataForge (+85262255569)**:
   ```powershell
   openclaw channel pair whatsapp --phone +85262255569
   ```
   - 掃描 QR Code
   - 等待配對完成

2. **SignalForge (+85262212577)**:
   ```powershell
   openclaw channel pair whatsapp --phone +85262212577
   ```
   - 掃描 QR Code
   - 等待配對完成

3. **TradeForge (+85255086558)**:
   ```powershell
   openclaw channel pair whatsapp --phone +85255086558
   ```
   - 掃描 QR Code
   - 等待配對完成

#### 步驟 4: 驗證配置

```powershell
# 查看所有 WhatsApp 賬號狀態
openclaw channel list whatsapp

# 測試發送消息
openclaw message send --channel whatsapp --to "+85263931048" --text "[DataForge] 測試消息" --account DataForge
```

---

### 方法 2: 使用 WhatsApp Business API (進階)

如果需要更穩定的商業級解決方案，可以考慮 WhatsApp Business API：

#### 要求
- Meta 商業賬號
- 每個號碼需要單獨申請
- 需要服務器託管

#### 優點
- 更穩定
- 支持自動化
- 無需手機在線

#### 缺點
- 需要 Meta 批准
- 有消息費用
- 配置複雜

---

### 方法 3: 虛擬手機/模擬器 (替代方案)

如果無法使用真實手機號碼：

#### 選項 A: Android 模擬器
- 使用 BlueStacks 或 Nox
- 每個模擬器安裝一個 WhatsApp
- 使用虛擬號碼服務 (如 TextNow)

#### 選項 B: 樹莓派 + 舊手機
- 使用舊 Android 手機
- 長期連接電源
- 安裝 WhatsApp Web 配套應用

---

## 📋 配置檢查清單

### DataForge (+85262255569)
- [ ] 號碼可以接收 SMS
- [ ] 已安裝 WhatsApp
- [ ] 可以掃描 QR Code
- [ ] OpenClaw 配對成功
- [ ] 可以發送測試消息
- [ ] 已加入 TradingBotGroup

### SignalForge (+85262212577)
- [ ] 號碼可以接收 SMS
- [ ] 已安裝 WhatsApp
- [ ] 可以掃描 QR Code
- [ ] OpenClaw 配對成功
- [ ] 可以發送測試消息
- [ ] 已加入 TradingBotGroup

### TradeForge (+85255086558)
- [ ] 號碼可以接收 SMS
- [ ] 已安裝 WhatsApp
- [ ] 可以掃描 QR Code
- [ ] OpenClaw 配對成功
- [ ] 可以發送測試消息
- [ ] 已加入 TradingBotGroup

---

## 🧪 測試流程

### 測試 1: 單獨消息
```powershell
# 從各 Agent 發送測試消息
openclaw message send --channel whatsapp --to "+85263931048" --text "[DataForge] 測試消息" --account DataForge
openclaw message send --channel whatsapp --to "+85263931048" --text "[SignalForge] 測試消息" --account SignalForge
openclaw message send --channel whatsapp --to "+85263931048" --text "[TradeForge] 測試消息" --account TradeForge
```

### 測試 2: 群組消息
```powershell
# 在 TradingBotGroup 發送消息
openclaw message send --channel whatsapp --to "120363423690498535@g.us" --text "[DataForge] 群組測試" --account DataForge
```

### 測試 3: 接收消息
- 從其他號碼發送消息給各 Agent
- 確認 Agent 可以接收並處理

---

## 🔐 安全注意事項

1. **號碼保護**:
   - 不要公開分享 Agent WhatsApp 號碼
   - 限制誰可以發送消息給 Agent

2. **消息驗證**:
   - 實現發送者驗證
   - 只處理來自授權號碼的指令

3. **日誌記錄**:
   - 記錄所有 WhatsApp 通訊
   - 定期審查

---

## 🚨 常見問題

### Q: WhatsApp 號碼被封鎖？
A: 
- 避免發送過多消息
- 不要發送垃圾信息
- 遵守 WhatsApp 使用條款

### Q: 無法配對？
A:
- 確保手機有網絡連接
- 重新啟動 WhatsApp
- 清除緩存後重試

### Q: 消息發送失敗？
A:
- 檢查號碼是否正確
- 確認對方已添加為聯繫人
- 檢查網絡連接

---

## 📞 號碼狀態確認

請確認以下號碼的當前狀態：

| 號碼 | 擁有者 | 狀態 | 備註 |
|------|--------|------|------|
| +85262255569 | ? | ? | DataForge |
| +85262212577 | ? | ? | SignalForge |
| +85255086558 | ? | ? | TradeForge |

**需要主人提供的信息**:
1. 這些號碼是否已經是 WhatsApp 賬號？
2. 這些號碼是否可用於 OpenClaw 配置？
3. 是否需要購買新的虛擬號碼？

---

## 🚀 下一步

1. 確認號碼狀態
2. 選擇配置方法
3. 執行配對流程
4. 測試通訊
5. 啟動 ClawTeam 系統

---

*等待主人確認號碼狀態後繼續配置*
