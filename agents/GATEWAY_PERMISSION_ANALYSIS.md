# Gateway 權限問題分析報告

> **日期**: 2026-04-05
> **問題**: `missing scope: operator.read`
> **狀態**: 已診斷，提供解決方案

---

## 問題診斷

### 現象
```
Gateway: local · ws://127.0.0.1:18789 · unreachable (missing scope: operator.read)
```

### 根本原因

從日誌分析發現：

1. **設備配對列表**顯示有 3 個配對設備：
   - 設備 1: 有 `operator.admin, operator.approvals, operator.pairing` ❌ (缺少 read)
   - 設備 2: 有 `operator.admin, operator.approvals, operator.pairing` ❌ (缺少 read)
   - 設備 3: 有 `operator.read, operator.admin, operator.write, operator.approvals, operator.pairing` ✅

2. **CLI 連接**使用 token 認證，但該 token 關聯的設備缺少 `operator.read` scope

3. **影響範圍**:
   - ❌ `openclaw status` 無法讀取 Gateway 狀態
   - ❌ `openclaw subagents` 無法管理 SubAgents
   - ✅ WhatsApp 消息收發正常
   - ✅ ClawTeam Shared Memory 運作正常

---

## 解決方案

### 方案 1: 重新配對 CLI (推薦)

需要重新運行完整配置嚮導，讓 CLI 獲得正確的權限：

```powershell
# 1. 停止 Gateway
openclaw gateway stop

# 2. 刪除現有設備配對 (可選)
# 手動編輯 ~/.openclaw/openclaw.json 移除 gateway.auth

# 3. 重新配置
openclaw configure

# 4. 選擇 Local mode，完成配對
```

### 方案 2: 手動修復 Token

從有 `operator.read` 的設備複製 token：

```powershell
# 查看設備列表
openclaw devices list

# 找到有 operator.read 的設備 (35fba4e2...)
# 手動更新 config 中的 token
```

### 方案 3: 暫時忽略 (ClawTeam 不受影響)

由於：
- ✅ WhatsApp 正常運作
- ✅ ClawTeam Shared Memory 機制正常
- ✅ Agent 間通訊不受影響

可以暫時忽略此問題，專注於 ClawTeam 功能開發。

---

## 當前狀態

| 組件 | 狀態 | 備註 |
|------|------|------|
| Gateway Service | 🟢 Running | pid 4368 |
| WhatsApp Channel | 🟢 OK | 已連接 |
| ClawTeam Shared Memory | 🟢 Working | 數據流正常 |
| CLI Status Command | 🔴 Error | missing scope |
| SubAgent Management | 🔴 Error | missing scope |

---

## 建議行動

**立即**: 暫時忽略，ClawTeam 功能不受影響

**稍後**: 運行 `openclaw configure` 重新配對 CLI

**注意**: 重新配對可能需要重新掃描 QR code 或輸入配對碼

---

*報告生成時間: 2026-04-05*
