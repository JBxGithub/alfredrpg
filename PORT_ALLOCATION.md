# Port 分配管理文件

> **用途**: 統一管理所有專案的 localhost:port，避免衝突  
> **最後更新**: 2026-04-18  
> **負責人**: 呀鬼 (Alfred)

---

## 🎯 Port 分配原則

1. **每個專案獨立 port range** - 避免重疊
2. **文檔化所有 port** - 方便查詢
3. **預留擴展空間** - 每個專案預留 10 個 port
4. **啟動前檢查** - 檢查 port 是否已被佔用

---

## 📊 Port 分配表

### 系統服務 (1000-1999)
| Port | 用途 | 狀態 |
|------|------|------|
| 11111 | Futu OpenD 網關 | 🟢 固定 |
| 8765 | FutuTradingBot Realtime Bridge | 🟢 使用中 |
| 8766 | FutuTradingBot Paper Trading Bridge | 🟢 使用中 |

### FutuTradingBot (8000-8099)
| Port | 用途 | 狀態 |
|------|------|------|
| 8000 | Dashboard (實盤) | 🟢 使用中 |
| 8081 | Dashboard (模擬) | 🟢 使用中 |

### FutuTradingBot Strategy Panel (8200-8299)
| Port | 用途 | 狀態 |
|------|------|------|
| 8200 | Strategy Panel Backend | 🟢 已配置 (.env) |
| 3000 | Strategy Panel Frontend | 🟢 已配置 |

### DeFi Intelligence Dashboard (3000-3099)
| Port | 用途 | 狀態 |
|------|------|------|
| 3000 | Frontend (Vite dev server) | 🟢 使用中 |
| 3001 | Frontend (備用) | 🟢 使用中 |
| 8000 | Backend (FastAPI) | 🔴 **衝突！** |

### Windmill Workflow (8500-8599)
| Port | 用途 | 狀態 |
|------|------|------|
| 8500 | Windmill Server | 🟢 已配置 |

### 其他專案
| Port | 用途 | 狀態 |
|------|------|------|
| 5000 | Flask 預設 | 🟡 可能衝突 |
| 8080 | HTTP 預設 | 🟡 可能衝突 |

---

## ✅ 已解決嘅衝突

### ~~衝突 1: Port 8000~~ ✅ 已修復
| 專案 | 原 Port | 新 Port | 狀態 |
|------|---------|---------|------|
| FutuTradingBot | 8000 | 8000 | 🟢 保持 |
| DeFi Dashboard | 8000 | **8100** | ✅ 已修復 |

### ~~衝突 2: Port 8080~~ 🟡 需關注
| 專案 | 用途 | 狀態 |
|------|------|------|
| accounting-automation | OAuth (臨時) | 🟡 需改為動態分配 |

---

## ✅ 建議修復

### 方案 A: 重新分配 Port (推薦)

為每個專案定義專屬 port range：

```
FutuTradingBot:     8000-8099
DeFi Dashboard:     8100-8199  (Backend)
                    3000-3099  (Frontend)
Accounting Bot:     8200-8299
YouTube Analyzer:   8300-8399
World Monitor:      8400-8499
Windmill:           8500-8599
```

### 方案 B: 使用環境變數
每個專案從 `.env` 文件讀取 port：
```bash
# .env
PORT=8000
# 或
BACKEND_PORT=8100
FRONTEND_PORT=3000
```

### 方案 C: 動態 Port 分配
啟動時自動找可用 port：
```python
import socket
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
```

---

## 📝 需要立即修復

### 高優先級
- [ ] DeFi Dashboard Backend: 8000 → 8100
- [ ] 更新所有 `.bat` 啟動腳本
- [ ] 更新 frontend proxy 設定
- [ ] 更新文檔

### 中優先級
- [ ] 為所有專案建立 `.env` 文件
- [ ] 建立 port 檢查腳本
- [ ] 更新 README

---

## 🔧 快速修復命令

### 檢查 port 是否被佔用
```bash
# Windows
netstat -an | findstr ":8000"

# 或 PowerShell
Get-NetTCPConnection -LocalPort 8000
```

### 查找可用 port
```bash
# 查找 8100-8199 範圍內可用 port
for ($port = 8100; $port -le 8199; $port++) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if (-not $connection) {
        Write-Host "Port $port is available"
        break
    }
}
```

---

## 📋 專案 Port 配置檢查清單

建立新專案時：
- [ ] 查閱本文件，分配未使用 port
- [ ] 在 `.env` 文件中定義 PORT
- [ ] 在啟動腳本中使用環境變數
- [ ] 更新本文件，記錄新 port 分配
- [ ] 測試啟動，確認無衝突

---

## 🎯 總結

**當前問題**:
- Port 8000: FutuTradingBot vs DeFi Dashboard 衝突
- Port 8080: 多個服務可能衝突
- 缺乏統一管理

**解決方案**:
1. 立即修復 DeFi Dashboard Backend port (8000 → 8100)
2. 建立 `.env` 配置系統
3. 更新所有啟動腳本
4. 建立 port 檢查機制

---

*建立時間: 2026-04-14 12:53*  
*建立人: 呀鬼 (Alfred)*
