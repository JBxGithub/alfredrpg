# DeFi Intelligence Dashboard

> 一個 AI 驅動的 DeFi 情報儀表板，實時聚合多鏈數據，提供智能洞察與預警。

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![React](https://img.shields.io/badge/React-18-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6)

## 🚀 快速開始

### 系統要求
- Python 3.11+
- Node.js 18+
- PostgreSQL (可選，默認使用 SQLite)

### 一鍵啟動

```bash
# 1. 克隆專案
git clone <repository-url>
cd defi-intelligence-dashboard

# 2. 啟動後端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. 啟動前端 (新終端)
cd frontend
npm install
npm run dev

# 4. 訪問
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API 文檔: http://localhost:8000/docs
```

## 🏗️ 技術架構

### 後端 (Backend)
- **框架**: FastAPI + Python 3.11+
- **數據庫**: SQLAlchemy + asyncpg (PostgreSQL) / aiosqlite (SQLite)
- **數據源**: DeFiLlama API
- **任務隊列**: Celery + Redis
- **文檔**: 自動生成 OpenAPI/Swagger

### 前端 (Frontend)
- **框架**: React 18 + TypeScript
- **構建**: Vite
- **樣式**: TailwindCSS
- **圖表**: Recharts
- **數據獲取**: React Query + Axios
- **圖標**: Lucide React

## 📊 功能特性

### 核心功能
- ✅ 實時 TVL 追蹤 (Total Value Locked)
- ✅ 多鏈支持 (Ethereum, Arbitrum, Base, Solana 等)
- ✅ 協議監控 (Protocols)
- ✅ 收益率比較 (Yield Farming)
- ✅ 歷史數據圖表
- ✅ 智能預警系統

### 頁面
1. **Dashboard** - 主頁概覽，統計卡片 + 圖表
2. **Chains** - 鏈列表，TVL 排名
3. **Protocols** - 協議列表，分類篩選
4. **Yields** - 收益率比較，APY 排序
5. **TVL History** - 歷史 TVL 走勢圖

## 🔌 API 端點

### Chains
```
GET /api/v1/chains              # 所有鏈列表
GET /api/v1/chains/{chain_id}   # 特定鏈詳情
```

### Protocols
```
GET /api/v1/protocols              # 所有協議列表
GET /api/v1/protocols/{protocol_id} # 特定協議詳情
```

### TVL
```
GET /api/v1/tvl/history  # TVL 歷史數據
```

### Yields
```
GET /api/v1/yields       # 收益率數據
GET /api/v1/yields/top   # 最高收益率池
```

完整 API 文檔請訪問: http://localhost:8000/docs

## 🎨 設計風格

- **主題**: 深色模式
- **強調色**: 金色 (#FFD700) / 綠色 (#00C853)
- **字體**: Inter / system-ui
- **響應式**: 支持桌面 + 移動端

## 📁 專案結構

```
defi-intelligence-dashboard/
├── backend/                    # FastAPI 後端
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 路由
│   │   ├── core/              # 配置
│   │   ├── crud/              # 數據庫操作
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # DeFiLlama 客戶端
│   │   └── tasks/             # Celery 任務
│   └── main.py                # FastAPI 入口
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # UI 組件
│   │   ├── hooks/             # React Query hooks
│   │   ├── pages/             # 頁面
│   │   ├── services/          # API 客戶端
│   │   └── types/             # TypeScript 類型
│   └── package.json
│
└── README.md                   # 本文件
```

## 🛠️ 開發

### 後端開發
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 前端開發
```bash
cd frontend
npm run dev
```

### 數據庫遷移
```bash
cd backend
alembic revision --autogenerate -m "migration name"
alembic upgrade head
```

## 📝 環境變量

創建 `.env` 文件:

```env
# 應用配置
APP_NAME=DeFi Intelligence Dashboard
APP_VERSION=1.0.0
DEBUG=false

# 數據庫
DATABASE_URL=sqlite+aiosqlite:///./defi_dashboard.db
# 或 PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/defi_dashboard

# DeFiLlama API
DEFILAMA_API_BASE=https://api.llama.fi
DEFILAMA_API_TIMEOUT=30

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

MIT License

---

Built with ❤️ by ClawTeam
