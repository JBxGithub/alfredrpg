# 三套系統及腳本存放位置總覽

> **最後更新**: 2026-04-14  
> **用途**: 快速定位所有系統及腳本

---

## 📁 系統總覽

### 1️⃣ FutuTradingBot (傳統金融交易系統)

**主目錄**: `C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\`

```
projects/fututradingbot/
├── src/                                    # 核心源碼
│   ├── main.py                            # 主入口
│   ├── realtime_bridge.py                 # 實時數據橋接
│   ├── dashboard_real.py                  # Dashboard 實時版
│   ├── dashboard_reporter.py              # 報告生成器
│   ├── simulation_bridge.py               # 模擬交易橋接
│   ├── survival_trader.py                 # 生存交易模式
│   │
│   ├── analysis/                          # 分析模組
│   │   ├── mtf_analyzer.py               # 多時間框架分析
│   │   ├── market_sentiment.py           # 市場情緒分析
│   │   ├── market_regime.py              # 市場狀態判斷
│   │   ├── divergence_detector.py        # 背離檢測
│   │   └── stock_analysis.py             # 股票分析
│   │
│   ├── api/                               # API 接口
│   │   └── futu_client.py                # 富途API客戶端
│   │
│   ├── backtest/                          # 回測模組
│   │   ├── enhanced_backtest.py          # 增強回測引擎
│   │   ├── quick_simulation.py           # 快速模擬
│   │   ├── analyze_2022.py               # 2022數據分析
│   │   └── archived/                     # 封存腳本
│   │
│   ├── dashboard/                         # Web Dashboard
│   │   └── app.py                        # Flask/FastAPI應用
│   │
│   ├── indicators/                        # 技術指標
│   │   ├── technical_indicators.py       # 技術指標計算
│   │   ├── candlestick_patterns.py       # K線形態識別
│   │   └── vwap.py                       # VWAP計算
│   │
│   ├── ml/                                # 機器學習
│   │   ├── feature_engineering.py        # 特徵工程
│   │   ├── model_trainer.py              # 模型訓練
│   │   └── signal_enhancer.py            # 信號增強
│   │
│   ├── strategies/                        # 交易策略
│   │   ├── base_strategy.py              # 策略基類
│   │   ├── trend_strategy.py             # 趨勢策略
│   │   ├── breakout_strategy.py          # 突破策略
│   │   ├── momentum_strategy.py          # 動量策略
│   │   └── tqqq_long_short.py            # TQQQ多空策略
│   │
│   ├── risk/                              # 風險管理
│   │   ├── risk_manager.py               # 風險管理器
│   │   ├── position_sizer.py             # 倉位計算
│   │   └── stop_loss.py                  # 止損模組
│   │
│   └── optimization/                      # 策略優化
│       ├── strategy_optimizer.py         # 策略優化器
│       └── walk_forward.py               # Walk-forward分析
│
├── templates/                             # HTML模板
│   └── dashboard.html                    # Dashboard模板
│
├── reports/                               # 報告輸出
├── logs/                                  # 日誌文件
├── start_dashboard.bat                    # 啟動腳本
└── STATUS.md                              # 狀態文件
```

**核心腳本**:
- `src/main.py` - 主程序入口
- `src/realtime_bridge.py` - 實時數據連接
- `src/analysis/market_sentiment.py` - 市場情緒分析 (供融合引擎使用)
- `src/strategies/tqqq_long_short.py` - TQQQ交易策略

---

### 2️⃣ DeFi Intelligence Dashboard (加密金融監控系統)

**主目錄**: `C:\Users\BurtClaw\openclaw_workspace\projects\defi-intelligence-dashboard\`

```
projects/defi-intelligence-dashboard/
├── backend/                               # FastAPI後端
│   ├── app/
│   │   ├── main.py                       # FastAPI入口
│   │   │
│   │   ├── api/v1/                       # API路由
│   │   │   ├── api.py                    # 路由聚合
│   │   │   └── endpoints/
│   │   │       ├── chains.py             # 鏈API
│   │   │       ├── protocols.py          # 協議API
│   │   │       ├── tvl.py                # TVL API
│   │   │       ├── yields.py             # 收益率API
│   │   │       └── world.py              # World Monitor API
│   │   │
│   │   ├── core/                         # 核心模組
│   │   │   ├── config.py                 # 配置管理
│   │   │   └── fusion_engine.py          # ⭐ 信號融合引擎
│   │   │
│   │   ├── crud/                         # 數據庫操作
│   │   │   ├── chain.py                  # 鏈CRUD
│   │   │   ├── protocol.py               # 協議CRUD
│   │   │   ├── tvl.py                    # TVL CRUD
│   │   │   └── yield.py                  # 收益CRUD
│   │   │
│   │   ├── models/                       # 數據模型
│   │   │   ├── base.py                   # SQLAlchemy基礎
│   │   │   ├── entities.py               # 實體模型
│   │   │   ├── fusion.py                 # 融合模型
│   │   │   └── worldmonitor.py           # World Monitor模型
│   │   │
│   │   ├── schemas/                      # Pydantic模型
│   │   │   ├── __init__.py
│   │   │   └── response.py               # 響應模型
│   │   │
│   │   ├── services/                     # 服務層
│   │   │   ├── defillama_client.py       # ⭐ DeFiLlama API客戶端
│   │   │   └── worldmonitor_client.py    # ⭐ World Monitor客戶端
│   │   │
│   │   └── tasks/                        # Celery任務
│   │       └── celery_config.py          # 任務隊列配置
│   │
│   ├── requirements.txt                   # Python依賴
│   ├── requirements-simple.txt            # 簡化依賴
│   └── venv/                              # 虛擬環境
│
├── frontend/                              # React前端
│   ├── src/
│   │   ├── main.tsx                      # React入口
│   │   ├── App.tsx                       # 主應用組件
│   │   ├── index.css                     # 全局樣式
│   │   │
│   │   ├── components/                   # UI組件
│   │   │   ├── Layout.tsx                # 布局組件
│   │   │   ├── DataTable.tsx             # 數據表格
│   │   │   ├── ChartCard.tsx             # 圖表卡片
│   │   │   ├── StatCard.tsx              # 統計卡片
│   │   │   ├── LoadingSpinner.tsx        # 加載動畫
│   │   │   ├── ErrorBoundary.tsx         # 錯誤邊界
│   │   │   └── index.ts                  # 組件導出
│   │   │
│   │   ├── pages/                        # 頁面組件
│   │   │   ├── Dashboard.tsx             # 主頁儀表板
│   │   │   ├── Chains.tsx                # 鏈列表頁
│   │   │   ├── Protocols.tsx             # 協議列表頁
│   │   │   ├── Yields.tsx                # 收益率頁
│   │   │   └── TVL.tsx                   # TVL歷史頁
│   │   │
│   │   ├── hooks/                        # 自定義Hooks
│   │   │   └── useApi.ts                 # API調用Hook
│   │   │
│   │   ├── services/                     # API服務
│   │   │   └── api.ts                    # Axios客戶端
│   │   │
│   │   └── types/                        # TypeScript類型
│   │       └── index.ts                  # 類型定義
│   │
│   ├── package.json                       # npm依賴
│   ├── vite.config.ts                     # Vite配置
│   ├── tsconfig.json                      # TypeScript配置
│   └── tailwind.config.js                 # Tailwind配置
│
└── README.md                              # 專案文檔
```

**核心腳本**:
- `backend/app/main.py` - FastAPI主入口
- `backend/app/core/fusion_engine.py` - ⭐ 信號融合引擎
- `backend/app/services/defillama_client.py` - DeFi數據獲取
- `backend/app/services/worldmonitor_client.py` - 宏觀數據獲取
- `frontend/src/App.tsx` - React主應用

---

### 3️⃣ World Monitor (全球宏觀監控系統)

**注意**: World Monitor 已整合到 DeFi Intelligence Dashboard 中

**整合位置**: `projects/defi-intelligence-dashboard/backend/app/services/worldmonitor_client.py`

**數據源**:
- **ACLED API** - 衝突事件數據 (https://api.acleddata.com)
- **USGS API** - 地震數據 (https://earthquake.usgs.gov)
- **GDELT** - 全球事件數據 (可選)

**相關文件**:
- `backend/app/services/worldmonitor_client.py` - 客戶端
- `backend/app/models/worldmonitor.py` - 數據模型
- `backend/app/api/v1/endpoints/world.py` - API端點

---

## 📊 三系統關係圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        呀鬼 (Alfred)                            │
│                      中央指揮協調                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│FutuTradingBot │ │  DeFi Intel   │ │World Monitor  │
│  (獨立系統)    │ │  (獨立系統)    │ │  (整合子系統)  │
├───────────────┤ ├───────────────┤ ├───────────────┤
│projects/      │ │projects/      │ │projects/      │
│fututradingbot/│ │defi-intelligen│ │defi-intelligen│
│               │ │ce-dashboard/  │ │ce-dashboard/  │
│               │ │               │ │backend/app/   │
│               │ │               │ │services/      │
│               │ │               │ │worldmonitor_  │
│               │ │               │ │client.py      │
└───────┬───────┘ └───────┬───────┘ └───────────────┘
        │                 │
        └─────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   信號融合引擎         │
              │   (fusion_engine.py)   │
              └───────────────────────┘
```

---

## 🚀 快速訪問

### FutuTradingBot
```bash
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
python src\main.py
```

### DeFi Intelligence Dashboard
```bash
# 後端
cd C:\Users\BurtClaw\openclaw_workspace\projects\defi-intelligence-dashboard\backend
venv\Scripts\python -m uvicorn app.main:app --reload

# 前端
cd C:\Users\BurtClaw\openclaw_workspace\projects\defi-intelligence-dashboard\frontend
npm run dev
```

---

## 📝 相關文檔

| 文檔 | 位置 |
|------|------|
| 本文件 | `SYSTEMS_LOCATION.md` |
| FutuTradingBot 狀態 | `project-states/FutuTradingBot-STATUS.md` |
| DeFi Dashboard 狀態 | `project-states/DeFi-Intelligence-Dashboard-STATUS.md` |
| 工作日誌 | `memory/2026-04-14-complete.md` |
| 長期記憶 | `MEMORY.md` |

---

*建立時間: 2026-04-14 10:26*  
*建立人: 呀鬼 (Alfred)*
