# 六循環系統部署指南

> **系統名稱**: 新循環系統 - 融合自動化引擎  
> **版本**: v1.1.0  
> **部署日期**: 2026-04-20
> **最後更新**: 2026-04-23 23:10  
> **狀態**: ✅ V9.4 最終版 - 所有組件已更新

---

## 🎯 系統概述

### 六系統循環架構

```
感知層 → 數據處理層 → 決策層 → 執行層 → 成就系統 → 學習層 → (循環)
```

| 系統 | 技術 | 狀態 |
|------|------|------|
| 感知層 | Node-RED + PostgreSQL | ✅ 運行中 |
| 數據處理層 | Node-RED + PostgreSQL | ✅ 運行中 |
| 決策層 | Python + PostgreSQL | ✅ 已測試 |
| 執行層 | Python + Futu API | ✅ 已創建 |
| 成就系統 | Python + Alfredrpg | ✅ 已創建 |
| 學習層 | Python + Self-Improving | ✅ 已創建 |

---

## 📋 部署狀態

### ✅ 已完成

#### 1. PostgreSQL 數據庫
- **主機**: localhost
- **端口**: 5432
- **數據庫**: trading_db
- **用戶**: postgres
- **密碼**: PostgresqL

**已創建表**:
- `raw_market_data` - 原始市場數據
- `raw_market_data_backup` - 備份數據
- `absolute_scores` - Absolute 評分
- `reference_scores` - Reference 評分
- `system_config` - 系統配置（含權重）
- `decisions` - 決策記錄

#### 2. Node-RED Flows
- **URL**: http://localhost:1880
- **Flows**: 4 個已部署並運行

| Flow | 功能 | 頻率 |
|------|------|------|
| Flow 1 | Futu OpenD 數據收集 | 每 5 秒 |
| Flow 2 | investing.com 爬蟲 | 每分鐘 |
| Flow 7 | Absolute 計算 | 每分鐘 |
| Flow 8 | Reference 計算 | 每分鐘 |

#### 3. Python 組件
- **決策引擎**: `decision-engine/main.py`
- **風險管理**: `decision-engine/risk_manager.py`
- **Futu 適配器**: `futu-adapter/main.py`
- **NQ 100 分析器**: `futu-adapter/nq100_analyzer.py`
- **TQQQ 執行器**: `futu-adapter/tqqq_executor.py`
- **每日收盤**: `achievement-system/daily_close.py`
- **成就徽章**: `achievement-system/badges.py`
- **每週回顧**: `learning-system/weekly_review.py`

---

## 🚀 快速開始

### 1. 檢查系統狀態

```bash
# 檢查 PostgreSQL
psql -h localhost -p 5432 -U postgres -d trading_db -c "SELECT version();"

# 檢查 Node-RED
curl http://localhost:1880/flows

# 檢查數據表
psql -h localhost -p 5432 -U postgres -d trading_db -c "\dt"
```

### 2. 手動運行決策引擎

```bash
python projects/six-loop-system/decision-engine/main.py
```

### 3. 手動運行 Futu 適配器

```bash
python projects/six-loop-system/futu-adapter/main.py
```

---

## ⚙️ 配置說明

### Absolute 權重配置

```sql
SELECT * FROM system_config WHERE config_name = 'absolute_weights';
-- nq200ma: 30%
-- nq50ma: 30%
-- nq20ema50ema: 20%
-- mtf: 10%
-- market_phase: 10%
```

### Reference 權重配置

```sql
SELECT * FROM system_config WHERE config_name = 'reference_weights';
-- components_breadth: 20%
-- components_risk: 10%
-- technical_rsi: 15%
-- technical_atr: 10%
-- technical_zscore: 10%
-- technical_macd: 5%
-- technical_divergence: 5%
-- money_flow_futures: 15%
-- money_flow_etf: 10%
```

---

## 📊 決策邏輯

### 信號生成

```python
final_score = (absolute_score * 0.6) + (reference_score * 0.4)

if final_score >= 70:
    signal = "BUY"
elif final_score <= 30:
    signal = "SELL"
else:
    signal = "HOLD"
```

### 風險檢查

| 檢查項 | 閾值 | 失敗處理 |
|--------|------|----------|
| 單筆最大風險 | <= 1% | 拒絕交易 |
| 每日最大虧損 | <= 2% | 暫停交易 |
| 總持倉風險 | <= 4% | 減倉 |
| 最大持倉數 | <= 3筆 | 拒絕新倉 |
| 錯誤保護 | 任何錯誤 | 暫停一天 |

---

## 🔧 故障排除

### PostgreSQL 連接失敗

```bash
# 檢查服務狀態
sc query postgresql-x64-18

# 啟動服務
net start postgresql-x64-18
```

### Node-RED 未運行

```bash
# 啟動 Node-RED
node-red

# 或
npx node-red
```

### Python 依賴缺失

```bash
pip install psycopg2-binary asyncpg pandas python-dotenv
```

---

## 📁 文件結構

```
projects/six-loop-system/
├── SYSTEM_ARCHITECTURE.md      # 系統架構文檔
├── DEPLOYMENT_GUIDE.md         # 本文件
├── flows/                      # Node-RED Flows
│   ├── flow1-futu-opend.json
│   ├── flow2-investing.json
│   ├── flow7-absolute-calc.json
│   └── flow8-reference-calc.json
├── sql/                        # SQL 腳本
│   ├── 01-create-raw-tables.sql
│   └── 02-create-score-tables.sql
├── decision-engine/            # 決策層
│   ├── main.py
│   └── risk_manager.py
├── futu-adapter/               # 執行層
│   ├── main.py
│   ├── nq100_analyzer.py
│   └── tqqq_executor.py
├── achievement-system/         # 成就系統
│   ├── daily_close.py
│   └── badges.py
└── learning-system/            # 學習層
    ├── weekly_review.py
    └── parameter_optimizer.py
```

---

## 🔄 系統工作流程

### 正常運行流程

1. **感知層** (每 5 秒/每分鐘)
   - Futu OpenD 收集 NQ 100 數據
   - investing.com 備份數據
   - 寫入 PostgreSQL

2. **數據處理層** (每分鐘)
   - 讀取 raw_market_data
   - 計算 Absolute Score (5 指標加權)
   - 計算 Reference Score (9 指標加權)
   - 寫入評分表

3. **決策層** (按需運行)
   - 讀取 absolute_scores 和 reference_scores
   - 計算 final_score
   - 生成 BUY/SELL/HOLD 信號
   - 風險檢查
   - 寫入 decisions 表

4. **執行層** (根據信號)
   - 讀取 decisions 表
   - NQ 100 分析確認
   - 執行 TQQQ 交易
   - 寫入 trades 表

5. **成就系統** (每日收盤)
   - 計算當日績效
   - 檢查成就解鎖
   - 更新 alfredrpg.net

6. **學習層** (每週一 09:30)
   - 分析上週交易
   - 優化參數
   - 調整權重
   - 反饋至系統 2

---

## 📝 更新日誌

| 日期 | 版本 | 更新內容 |
|------|------|----------|
| 2026-04-20 | v1.0.0 | 初始部署，六系統完整實現 |
| 2026-04-22 | v1.0.1 | 更新時間戳，系統狀態維持正常 |
| 2026-04-22 | v1.0.2 | 更新時間戳，完成 Node-RED Flows 建立 |

---

*部署完成時間: 2026-04-20 08:25*  
*最後更新: 2026-04-22 09:32*  
*部署者: Alfred (呀鬼)*
