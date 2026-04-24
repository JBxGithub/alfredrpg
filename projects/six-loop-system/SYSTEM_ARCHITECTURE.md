# 新循環系統 - 融合自動化引擎

> **系統版本**: v1.1.0  
> **設計日期**: 2026-04-20  
> **最後更新**: 2026-04-23 23:10  
> **設計者**: Alfred (呀鬼) via Opencode ACP  
> **循環流程**: 感知 → 處理 → 決策 → 執行 → 成就 → 學習 → 循環

---

## 🎯 系統概述

### 核心原則
- **分析標的**: NQ 100 (Nasdaq 100 Index)
  - *Futu 數據源*: 使用 US.QQQ 作為代理 (QQQ 追蹤 NQ 100)
  - *其他數據源*: 直接使用 NQ 100 指數
- **交易標的**: TQQQ (ProShares UltraPro QQQ)
- **數據源優先級**: Futu OpenD (QQQ) > investing.com (NQ 100) > tradingview.com > jin10.com
- **錯誤保護**: 錯誤即暫停一天，重新判斷

### 重要說明: 分析標的 vs 交易標的
```
分析標的: NQ 100 (Nasdaq 100 Index)
    ↓ 技術分析、信號生成
交易標的: TQQQ (3x 槓桿 QQQ ETF)

為什麼這樣設計?
- NQ 100 是基礎指數，代表納斯達克100家大公司
- QQQ 是追蹤 NQ 100 的 ETF (1:1 追蹤)
- TQQQ 是 QQQ 的 3x 槓桿版本 (適合短期交易)
- Futu 中無法直接獲取 NDX 指數，使用 QQQ 作為最佳代理
```

### 六系統架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         新循環系統 - 融合自動化引擎                        │
│                    「感知 → 處理 → 決策 → 執行 → 成就 → 學習 → 循環」      │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   系統 1    │     │   系統 2    │     │   系統 3    │     │   系統 4    │
    │   感知層   │────►│  數據處理   │────►│   決策層   │────►│   執行層   │
    │  Node-RED  │     │  Node-RED  │     │Opencode ACP │     │FutuTrading  │
    │ +PostgreSQL│     │ +PostgreSQL│     │             │     │    Bot     │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │                   │
           ▼                   ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │•Futu OpenD  │     │•Absolute   │     │•信號生成    │     │•模擬/實盤   │
    │•investing   │     │ 計算(權重)  │     │•風險檢查    │     │ 交易       │
    │•tradingview │     │•Reference  │     │•錯誤保護    │     │•止損止盈    │
    │•jin10.com   │     │ 計算(權重)  │     │•決策輸出    │     │•每日報告    │
    │•DeFiLlama   │     │•綜合評分   │     │             │     │            │
    │•ACLED/USGS  │     │ (0-100)    │     │             │     │            │
    └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                       │
                                                                       ▼
                                                              ┌─────────────┐
                                                              │   系統 5    │
                                                              │  成就激勵   │
                                                              │ Alfredrpg  │
                                                              │             │
                                                              │•交易結果    │
                                                              │ 記錄       │
                                                              │•每日更新    │
                                                              │ alfredrpg  │
                                                              │ .net       │
                                                              └──────┬──────┘
                                                                     │
                                                                     ▼
                                                              ┌─────────────┐
                                                              │   系統 6    │
                                                              │   學習層   │
                                                              │Self-Improving│
                                                              │             │
                                                              │•每週回顧    │
                                                              │•參數優化    │
                                                              │•反饋至系統2 │
                                                              │ (權重調整)  │
                                                              └─────────────┘
```

---

## 📊 系統 1：感知層 (Node-RED + PostgreSQL)

### 功能描述
負責從多個數據源收集原始數據，並寫入 PostgreSQL 數據庫。

### 數據源配置

| 數據源 | 類型 | 頻率 | 數據內容 | 備註 |
|--------|------|------|----------|------|
| **Futu OpenD** | 主要 | 實時 | NQ 100 價格、成交量、技術指標 | 優先使用 |
| **investing.com** | 備份 | 每分鐘 | 全球指數、期貨數據 | 驗證用 |
| **tradingview.com** | 技術分析 | 每5分鐘 | 圖表、技術指標 | 圖表確認 |
| **jin10.com** | 新聞 | 實時 | 財經快訊、事件 | 事件驅動 |
| **DeFiLlama** | DeFi | 每5分鐘 | TVL、APY、協議數據 | 現有系統 |
| **ACLED** | 衝突 | 每小時 | 全球衝突事件 | 現有系統 |
| **USGS** | 災害 | 每小時 | 地震等自然災害 | 現有系統 |

### Node-RED Flows 設計

#### Flow 1: Futu OpenD 數據收集
```json
{
  "flow_name": "futu-data-collection",
  "nodes": [
    {
      "type": "inject",
      "repeat": 5,
      "units": "seconds"
    },
    {
      "type": "function",
      "name": "Connect Futu OpenD",
      "func": "// Connect to Futu OpenD WebSocket\n// Subscribe to NQ 100, TQQQ data"
    },
    {
      "type": "postgresql",
      "server": "localhost:5432",
      "database": "trading_db",
      "table": "raw_market_data"
    }
  ]
}
```

#### Flow 2: investing.com 爬蟲
```json
{
  "flow_name": "investing-scraper",
  "nodes": [
    {
      "type": "inject",
      "repeat": 1,
      "units": "minutes"
    },
    {
      "type": "http request",
      "url": "https://www.investing.com/indices/nq-100",
      "method": "GET"
    },
    {
      "type": "function",
      "name": "Parse Data",
      "func": "// Extract price, change, volume"
    },
    {
      "type": "postgresql",
      "table": "raw_market_data"
    }
  ]
}
```

#### Flow 3-6: 其他數據源
- Flow 3: tradingview.com 技術指標提取
- Flow 4: jin10.com 新聞監控
- Flow 5: DeFiLlama 數據更新
- Flow 6: World Monitor (ACLED/USGS)

---

## 🧮 系統 2：數據處理/存儲 (Node-RED + PostgreSQL)

### 功能描述
處理原始數據，計算 Absolute 和 Reference 評分，輸出綜合評分。

### Absolute 計算 (NQ 100 趨勢判定)

| 指標 | 來源 | 權重 | 計算邏輯 |
|------|------|------|----------|
| **NQ100 vs 200MA (日線)** | Futu OpenD | 30% | 價格 > 200MA = 100分，否則線性計算 |
| **NQ100 vs 50MA (日線)** | Futu OpenD | 30% | 同上 |
| **NQ100 20EMA vs 50EMA (週線)** | Futu OpenD | 20% | 20EMA > 50EMA = 100分 |
| **MTF Trend Direction** | mtf_analyzer.py | 10% | 多時間框架共識分數 |
| **Market Phase** | market_sentiment.py | 10% | 積累/上升/派發/下降評分 |

**趨勢判定**:
- 4-5 個 align (>=80分): 強趨勢
- 3 個 align (60-79分): 中等趨勢
- 2 個 align (40-59分): 弱趨勢
- 0-1 個 align (0-39分): 震盪

### Reference 計算 (NQ 100 綜合)

| 類別 | 指標 | 來源 | 權重 |
|------|------|------|------|
| **成份股層面** | 前20權重股漲跌比例 | Futu OpenD | 20% |
| | 前50隻事件風險評分 | jin10.com | 10% |
| **技術層面** | NQ100 RSI | Futu OpenD | 15% |
| | NQ100 波動率 (ATR) | Futu OpenD | 10% |
| | Z-Score | tqqq_long_short.py | 10% |
| | MACD-V | MTF | 5% |
| | Divergence | MTF | 5% |
| **資金層面** | NQ 期貨持倉變化 | investing.com | 15% |
| | TQQQ/QQQ 資金流入 | Futu OpenD | 10% |

**輸出**: 0-100 分數

### Node-RED Flows 設計

#### Flow 7: Absolute 計算
```json
{
  "flow_name": "absolute-calculation",
  "nodes": [
    {
      "type": "inject",
      "repeat": 1,
      "units": "minutes"
    },
    {
      "type": "postgresql",
      "query": "SELECT * FROM raw_market_data WHERE timestamp > NOW() - INTERVAL '5 minutes'"
    },
    {
      "type": "function",
      "name": "Calculate Absolute Score",
      "func": "// Calculate weighted absolute score\n// Output: 0-100"
    },
    {
      "type": "postgresql",
      "table": "absolute_scores"
    }
  ]
}
```

#### Flow 8: Reference 計算
```json
{
  "flow_name": "reference-calculation",
  "nodes": [
    {
      "type": "inject",
      "repeat": 1,
      "units": "minutes"
    },
    {
      "type": "postgresql",
      "query": "SELECT * FROM raw_market_data WHERE timestamp > NOW() - INTERVAL '5 minutes'"
    },
    {
      "type": "function",
      "name": "Calculate Reference Score",
      "func": "// Calculate weighted reference score\n// Components: 成份股, 技術, 資金\n// Output: 0-100"
    },
    {
      "type": "postgresql",
      "table": "reference_scores"
    }
  ]
}
```

---

## 🧠 系統 3：決策層 (Opencode ACP)

### 功能描述
基於 Absolute 和 Reference 評分生成交易信號，進行風險檢查，輸出最終決策。

### 決策邏輯

```python
def generate_signal(absolute_score, reference_score, risk_params):
    """
    決策邏輯
    """
    # 綜合評分計算
    final_score = (absolute_score * 0.6) + (reference_score * 0.4)
    
    # 信號生成
    if final_score >= 70:
        signal = "BUY"
    elif final_score <= 30:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    # 風險檢查
    if not risk_check_passed(risk_params):
        signal = "HOLD"
        error_flag = True
    
    return {
        "signal": signal,
        "final_score": final_score,
        "absolute_score": absolute_score,
        "reference_score": reference_score,
        "risk_check_passed": not error_flag,
        "error_flag": error_flag
    }
```

### 風險檢查項目

| 檢查項 | 閾值 | 失敗處理 |
|--------|------|----------|
| 單筆最大風險 | <= 1% | 拒絕交易 |
| 每日最大虧損 | <= 2% | 暫停交易 |
| 總持倉風險 | <= 4% | 減倉 |
| 最大持倉數 | <= 3筆 | 拒絕新倉 |
| 錯誤保護 | 任何錯誤 | 暫停一天 |

### API 接口

```
POST /api/v1/decision
Request:
{
    "absolute_score": 75,
    "reference_score": 65,
    "current_positions": [...],
    "account_balance": 100000
}

Response:
{
    "signal": "BUY",
    "final_score": 71,
    "risk_check_passed": true,
    "recommended_position_size": 0.33,
    "timestamp": "2026-04-20T08:00:00Z"
}
```

---

## ⚡ 系統 4：執行層 (FutuTradingBot)

### 功能描述
執行交易決策，管理倉位，設置止損止盈，生成每日報告。

### 現有 Cron Job
- **Trading System Heartbeat**: 美股時段自動啟動

### 交易執行流程

```
1. 接收決策層信號 (BUY/SELL/HOLD)
2. 檢查當前倉位
3. 計算倉位大小 (基於風險參數)
4. 執行交易 (模擬/實盤)
5. 設置止損止盈
6. 記錄交易到 PostgreSQL
7. 發送通知
```

### 修改項目

| 項目 | 原設計 | 新設計 |
|------|--------|--------|
| 分析標的 | TQQQ | NQ 100 |
| RSI 閾值 | TQQQ RSI 30/70 | NQ 100 RSI 30/70 |
| Z-Score | TQQQ Z-Score | NQ 100 Z-Score |
| 交易策略 | 基於 TQQQ | 基於 NQ 100，交易 TQQQ |

---

## 🏆 系統 5：成就激勵系統 (Alfredrpg)

### 功能描述
記錄交易結果，計算績效統計，更新 Alfredrpg 網站。

### 每日收盤任務

```python
def daily_close_tasks():
    """
    每日收盤時執行
    """
    # 1. 計算當日績效
    daily_pnl = calculate_daily_pnl()
    win_rate = calculate_win_rate()
    max_drawdown = calculate_max_drawdown()
    
    # 2. 檢查成就解鎖
    badges = check_achievements(daily_pnl, win_rate)
    
    # 3. 更新數據庫
    save_to_achievements_table(daily_pnl, win_rate, max_drawdown, badges)
    
    # 4. 更新 Alfredrpg 網站
    update_alfredrpg_website({
        "date": today,
        "pnl": daily_pnl,
        "win_rate": win_rate,
        "badges": badges
    })
    
    # 5. 發送通知
    send_notification(f"今日盈虧: {daily_pnl}, 勝率: {win_rate}%")
```

### 成就系統

| 成就 | 條件 | 徽章 |
|------|------|------|
| 首勝 | 第一筆盈利交易 | 🥉 |
| 連勝 | 連續5筆盈利 | 🥈 |
| 大師 | 連續10筆盈利 | 🥇 |
| 穩健 | 最大回撤 < 2% | 🛡️ |
| 勇士 | 單日盈利 > 5% | ⚔️ |

---

## 📚 系統 6：學習層 (Self-Improving)

### 功能描述
每週回顧交易結果，優化參數，調整系統 2 的權重。

### 每週任務 (週一 09:30)

參考現有系統:
- SelfImproving-Weekly-Review
- AMS-Weekly-Learning-Review

```python
def weekly_learning_review():
    """
    每週學習回顧
    """
    # 1. 讀取上週交易數據
    last_week_trades = get_last_week_trades()
    
    # 2. 分析表現
    performance_analysis = analyze_performance(last_week_trades)
    
    # 3. 識別模式
    patterns = identify_patterns(last_week_trades)
    
    # 4. 生成優化建議
    recommendations = generate_recommendations(performance_analysis, patterns)
    
    # 5. 調整系統 2 權重 (小改進自動執行)
    if recommendations['confidence'] > 0.8:
        adjust_system2_weights(recommendations['weight_adjustments'])
    
    # 6. 生成報告
    generate_weekly_report(performance_analysis, recommendations)
    
    # 7. 保存學習記錄
    save_learning_log(performance_analysis, recommendations)
```

### 反饋至系統 2

```python
def adjust_system2_weights(recommendations):
    """
    根據學習結果調整系統 2 的權重
    """
    # 讀取當前權重
    current_weights = get_current_weights()
    
    # 應用調整
    new_weights = {
        'nq200ma': current_weights['nq200ma'] + recommendations['nq200ma_delta'],
        'nq50ma': current_weights['nq50ma'] + recommendations['nq50ma_delta'],
        # ... 其他權重
    }
    
    # 驗證權重總和為 100%
    assert sum(new_weights.values()) == 100
    
    # 保存新權重
    save_weights(new_weights)
```

---

## 🗄️ PostgreSQL 數據庫設計

### 連接配置
```
Host: localhost
Port: 5432
Database: trading_db
Username: postgres
Password: PostgresqL
```

### 數據表結構

```sql
-- 系統 1: 原始數據表
CREATE TABLE raw_market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10,2),
    volume BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_market_data_symbol_timestamp 
ON raw_market_data(symbol, timestamp);

-- 系統 2: Absolute 評分
CREATE TABLE absolute_scores (
    id SERIAL PRIMARY KEY,
    nq200ma_score INT CHECK (nq200ma_score BETWEEN 0 AND 100),
    nq50ma_score INT CHECK (nq50ma_score BETWEEN 0 AND 100),
    nq20ema50ema_score INT CHECK (nq20ema50ema_score BETWEEN 0 AND 100),
    mtf_score INT CHECK (mtf_score BETWEEN 0 AND 100),
    market_phase_score INT CHECK (market_phase_score BETWEEN 0 AND 100),
    final_absolute_score INT CHECK (final_absolute_score BETWEEN 0 AND 100),
    trend_direction VARCHAR(20), -- bull/bear/sideways
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統 2: Reference 評分
CREATE TABLE reference_scores (
    id SERIAL PRIMARY KEY,
    components_breadth_score INT CHECK (components_breadth_score BETWEEN 0 AND 100),
    technical_score INT CHECK (technical_score BETWEEN 0 AND 100),
    money_flow_score INT CHECK (money_flow_score BETWEEN 0 AND 100),
    final_reference_score INT CHECK (final_reference_score BETWEEN 0 AND 100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統 3: 決策記錄
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    absolute_score INT,
    reference_score INT,
    final_score INT,
    signal VARCHAR(10) CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    risk_check_passed BOOLEAN,
    error_flag BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統 4: 交易執行
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    decision_id INT REFERENCES decisions(id),
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) CHECK (action IN ('BUY', 'SELL')),
    quantity INT,
    price DECIMAL(10,2),
    total_value DECIMAL(12,2),
    pnl DECIMAL(10,2),
    status VARCHAR(20), -- pending/filled/cancelled
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統 5: 成就記錄
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    trade_date DATE UNIQUE,
    total_pnl DECIMAL(10,2),
    win_rate DECIMAL(5,2),
    max_drawdown DECIMAL(5,2),
    total_trades INT,
    winning_trades INT,
    badges_earned JSONB,
    posted_to_alfredrpg BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統 6: 學習記錄
CREATE TABLE learning_logs (
    id SERIAL PRIMARY KEY,
    week_start DATE,
    week_end DATE,
    performance_summary JSONB,
    parameter_changes JSONB,
    weight_adjustments JSONB,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統配置表 (存儲權重等配置)
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(50) UNIQUE,
    config_value JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默認權重配置
INSERT INTO system_config (config_name, config_value) VALUES (
    'absolute_weights',
    '{
        "nq200ma": 30,
        "nq50ma": 30,
        "nq20ema50ema": 20,
        "mtf": 10,
        "market_phase": 10
    }'::jsonb
);

INSERT INTO system_config (config_name, config_value) VALUES (
    'reference_weights',
    '{
        "components_breadth": 20,
        "components_risk": 10,
        "technical_rsi": 15,
        "technical_atr": 10,
        "technical_zscore": 10,
        "technical_macd": 5,
        "technical_divergence": 5,
        "money_flow_futures": 15,
        "money_flow_etf": 10
    }'::jsonb
);
```

---

## 🔌 API 接口設計

### 系統 2 → 系統 3 接口

```
GET /api/v1/scores/latest
Response:
{
    "absolute": {
        "score": 75,
        "trend": "bull",
        "components": {
            "nq200ma": 80,
            "nq50ma": 75,
            "nq20ema50ema": 70,
            "mtf": 80,
            "market_phase": 70
        }
    },
    "reference": {
        "score": 65,
        "components": {
            "components_breadth": 70,
            "components_risk": 60,
            "technical": 65,
            "money_flow": 65
        }
    },
    "timestamp": "2026-04-20T08:00:00Z"
}
```

### 系統 3 → 系統 4 接口

```
POST /api/v1/execute
Request:
{
    "signal": "BUY",
    "position_size": 0.33,
    "stop_loss": 0.03,
    "take_profit": 0.05
}

Response:
{
    "trade_id": 12345,
    "status": "filled",
    "filled_price": 45.20,
    "timestamp": "2026-04-20T08:00:05Z"
}
```

### 系統 4 → 系統 5 接口

```
POST /api/v1/achievement/update
Request:
{
    "date": "2026-04-20",
    "pnl": 1250.50,
    "trades": 3,
    "wins": 2
}
```

---

## 📋 實施計劃

### Phase 1: 基礎建設
- [ ] 安裝 PostgreSQL
- [ ] 創建數據庫和表
- [ ] 配置 Node-RED
- [ ] 建立 Futu OpenD 連接

### Phase 2: 感知層 (系統 1)
- [ ] Flow 1: Futu OpenD 數據收集
- [ ] Flow 2: investing.com 爬蟲
- [ ] Flow 3: tradingview.com 指標
- [ ] Flow 4: jin10.com 新聞
- [ ] Flow 5-6: DeFi + World Monitor

### Phase 3: 數據處理 (系統 2)
- [ ] Flow 7: Absolute 計算
- [ ] Flow 8: Reference 計算
- [ ] 權重配置系統

### Phase 4: 決策層 (系統 3)
- [ ] Opencode ACP 決策邏輯
- [ ] 風險檢查模組
- [ ] 錯誤保護機制

### Phase 5: 執行層 (系統 4)
- [ ] 修改 FutuTradingBot
- [ ] NQ 100 分析核心
- [ ] TQQQ 交易執行

### Phase 6: 成就系統 (系統 5)
- [ ] Alfredrpg 網站整合
- [ ] 每日更新自動化

### Phase 7: 學習層 (系統 6)
- [ ] 每週回顧自動化
- [ ] 參數優化系統
- [ ] 反饋至系統 2

---

*文檔版本: v1.0.0*  
*最後更新: 2026-04-22 09:32*  
*設計者: Alfred (呀鬼)*
