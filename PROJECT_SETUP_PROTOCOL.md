# 新專案建立協議

> **用途**: 確保所有新專案遵循統一配置標準，避免 port 衝突  
> **版本**: 1.0  
> **最後更新**: 2026-04-14

---

## 🎯 核心原則

**所有新專案必須：**
1. ✅ 使用 `.env` 配置系統
2. ✅ 從 `PORT_ALLOCATION.md` 分配 port
3. ✅ 建立 `.env.example` 模板
4. ✅ 更新 `PORT_ALLOCATION.md` 記錄

---

## 📋 建立新專案檢查清單

### Step 1: Port 分配 (必做)
- [ ] 查閱 `PORT_ALLOCATION.md`
- [ ] 確認可用 port range
- [ ] 分配專屬 port (每個專案預留 100 個 port)
- [ ] 更新 `PORT_ALLOCATION.md`

### Step 2: 建立 .env 配置 (必做)
```bash
# 專案根目錄
touch .env
touch .env.example
echo ".env" >> .gitignore
```

#### Backend .env.example 模板：
```env
# Server
SERVER_PORT=8XXX
HOST=0.0.0.0

# Database
DATABASE_URL=sqlite:///./app.db

# API Keys (optional)
# API_KEY=your_key_here
```

#### Frontend .env.example 模板：
```env
# API
VITE_API_BASE_URL=http://localhost:8XXX/api

# Feature Flags
VITE_DEBUG=false
```

### Step 3: 配置讀取代碼 (必做)

#### Python/FastAPI:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_PORT: int = 8000  # 預設值
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings():
    return Settings()
```

#### Node.js/React:
```javascript
// .env
VITE_API_BASE_URL=http://localhost:8XXX/api

// api.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
```

### Step 4: 啟動腳本更新 (必做)
所有 `.bat` / `.sh` 腳本必須：
- [ ] 檢查 `.env` 文件存在
- [ ] 顯示正在使用嘅 port
- [ ] 檢查 port 是否已被佔用

```batch
@echo off
:: 檢查 .env
if not exist .env (
    echo ❌ .env 文件不存在，請複製 .env.example
    pause
    exit /b 1
)

:: 顯示配置
echo [配置] 讀取 .env...
for /f "tokens=2 delims==" %%a in ('findstr "SERVER_PORT" .env') do set PORT=%%a
echo [配置] 使用 port: %PORT%

:: 檢查 port 是否被佔用
netstat -an | findstr ":%PORT% " | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo ❌ Port %PORT% 已被佔用
    pause
    exit /b 1
)
```

### Step 5: 文檔更新 (必做)
- [ ] 更新專案 `README.md`
- [ ] 記錄 port 使用說明
- [ ] 更新 `PORT_ALLOCATION.md`

---

## 🚫 禁止行為

| 禁止 | 原因 | 正確做法 |
|------|------|---------|
| 硬編碼 port | 容易衝突 | 用 `.env` |
| 用常見 port (8000, 8080, 3000) | 容易衝突 | 分配專屬 range |
| 唔更新 `PORT_ALLOCATION.md` | 無法追蹤 | 立即更新 |
| 唔建立 `.env.example` | 其他人無法配置 | 必須建立 |

---

## 📊 Port Range 分配表

```
8000-8099: FutuTradingBot (已分配)
8100-8199: DeFi Intelligence Dashboard (已分配)
8200-8299: Accounting Bot (預留)
8300-8399: YouTube Analyzer (預留)
8400-8499: World Monitor (預留)
8500-8599: 可用
8600-8699: 可用
...
```

**新專案請用下一個可用 range！**

---

## 🔧 自動檢查腳本

### check_port.bat (放喺專案根目錄)
```batch
@echo off
echo ==========================================
echo Port 檢查工具
echo ==========================================
echo.

:: 讀取 .env 嘅 port
for /f "tokens=2 delims==" %%a in ('findstr "SERVER_PORT" .env') do set PORT=%%a
set PORT=%PORT: =%

echo [檢查] 目標 Port: %PORT%
echo.

:: 檢查是否被佔用
netstat -an | findstr ":%PORT% " | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo ❌ Port %PORT% 已被佔用！
    echo.
    echo [建議]:
    echo   1. 檢查 PORT_ALLOCATION.md 分配新 port
    echo   2. 修改 .env 文件
    echo   3. 重新啟動
    pause
    exit /b 1
) else (
    echo ✅ Port %PORT% 可用
)

echo.
pause
```

---

## 🎯 呀鬼提醒

**每次建立新專案前，必須：**
1. 讀 `PROJECT_SETUP_PROTOCOL.md` ✅
2. 讀 `PORT_ALLOCATION.md` ✅
3. 執行檢查清單 ✅
4. 更新文檔 ✅

**違反協議嘅後果：**
- Port 衝突
- 系統無法同時運行
- 浪費時間 debug

---

## 📝 更新日誌

| 日期 | 更新內容 |
|------|---------|
| 2026-04-14 | 初版建立，解決 DeFi Dashboard port 衝突 |

---

*建立人: 呀鬼 (Alfred)*  
*建立時間: 2026-04-14 13:04*
