-- NQ100 Trading System - PostgreSQL Database Schema
-- Created: 2026-04-19
-- Database: nq100_trading

-- Create database (run manually: CREATE DATABASE nq100_trading;)

-- 1. NQ100 Price Data (時間序列)
CREATE TABLE IF NOT EXISTS nq100_price (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nq100_price_timestamp ON nq100_price(timestamp);

-- 2. NQ100 Components (成份股權重)
CREATE TABLE IF NOT EXISTS nq100_components (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100),
    weight DECIMAL(5, 4), -- 權重百分比 (0-1)
    sector VARCHAR(50),
    market_cap BIGINT,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_components_symbol ON nq100_components(symbol);
CREATE INDEX idx_components_date ON nq100_components(date);

-- 3. Component Events (成份股事件)
CREATE TABLE IF NOT EXISTS component_events (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    event_type VARCHAR(50), -- earnings, news, dividend, etc.
    event_date DATE,
    description TEXT,
    impact_score INTEGER CHECK (impact_score >= 0 AND impact_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_symbol ON component_events(symbol);
CREATE INDEX idx_events_date ON component_events(event_date);

-- 4. Technical Indicators (技術指標)
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ma_50 DECIMAL(10, 2),
    ma_200 DECIMAL(10, 2),
    ema_20_weekly DECIMAL(10, 2),
    ema_50_weekly DECIMAL(10, 2),
    rsi_14 DECIMAL(5, 2),
    atr_14 DECIMAL(10, 2),
    macd DECIMAL(10, 2),
    macd_signal DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indicators_timestamp ON technical_indicators(timestamp);

-- 5. Absolute Reference Scores (計算結果)
CREATE TABLE IF NOT EXISTS absolute_reference_scores (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- Absolute (趨勢判定)
    score_vs_ma200 DECIMAL(5, 2), -- 40% 權重
    score_vs_ma50 DECIMAL(5, 2),  -- 35% 權重
    score_weekly_ema DECIMAL(5, 2), -- 25% 權重
    absolute_total DECIMAL(5, 2), -- 加權總分
    absolute_signal VARCHAR(20), -- bull, bear, neutral
    
    -- Reference (綜合評分)
    component_breadth DECIMAL(5, 2), -- 30% 前20漲跌比例
    event_risk DECIMAL(5, 2),        -- 30% 事件風險
    rsi_score DECIMAL(5, 2),         -- 20% RSI
    volatility_score DECIMAL(5, 2),  -- 20% ATR
    reference_total DECIMAL(5, 2),   -- 0-100 分數
    
    -- 最終決策
    final_signal VARCHAR(20), -- long, short, neutral
    confidence DECIMAL(5, 2), -- 置信度
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scores_timestamp ON absolute_reference_scores(timestamp);

-- 6. Trading Decisions (交易決策記錄)
CREATE TABLE IF NOT EXISTS trading_decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    signal VARCHAR(20), -- long, short, neutral
    absolute_score DECIMAL(5, 2),
    reference_score DECIMAL(5, 2),
    position_size DECIMAL(5, 2), -- 倉位百分比
    stop_loss DECIMAL(10, 2),
    take_profit DECIMAL(10, 2),
    executed BOOLEAN DEFAULT FALSE,
    result VARCHAR(20), -- win, loss, pending
    pnl DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_timestamp ON trading_decisions(timestamp);

-- 7. Error Protection Log (錯誤保護記錄)
CREATE TABLE IF NOT EXISTS error_protection_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    error_type VARCHAR(50),
    description TEXT,
    action_taken VARCHAR(100), -- e.g., "paused_for_1_day"
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Views for easy querying
CREATE OR REPLACE VIEW latest_scores AS
SELECT * FROM absolute_reference_scores
ORDER BY timestamp DESC
LIMIT 1;

CREATE OR REPLACE VIEW daily_summary AS
SELECT 
    DATE(timestamp) as date,
    AVG(close) as avg_close,
    MAX(high) as day_high,
    MIN(low) as day_low,
    SUM(volume) as total_volume
FROM nq100_price
GROUP BY DATE(timestamp)
ORDER BY date DESC;
