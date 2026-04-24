-- ============================================================
-- Six-Loop-System: Score Tables Creation
-- Version: 1.0.0
-- Created: 2026-04-20
-- Description: Create absolute_scores, reference_scores, and system_config tables
-- ============================================================

-- Check if database exists, create if not
SELECT 'CREATE DATABASE trading_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_db')\gexec

\c trading_db;

-- ============================================================
-- Table 1: absolute_scores
-- Stores NQ100 absolute trend scores
-- ============================================================

CREATE TABLE IF NOT EXISTS absolute_scores (
    id SERIAL PRIMARY KEY,
    nq200ma_score INTEGER CHECK (nq200ma_score BETWEEN 0 AND 100),
    nq50ma_score INTEGER CHECK (nq50ma_score BETWEEN 0 AND 100),
    nq20ema50ema_score INTEGER CHECK (nq20ema50ema_score BETWEEN 0 AND 100),
    mtf_score INTEGER CHECK (mtf_score BETWEEN 0 AND 100),
    market_phase_score INTEGER CHECK (market_phase_score BETWEEN 0 AND 100),
    final_absolute_score INTEGER CHECK (final_absolute_score BETWEEN 0 AND 100),
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('strong_bull', 'bull', 'weak', 'bear', 'strong_bear', 'sideways')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_absolute_scores_timestamp 
ON absolute_scores(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_absolute_scores_final 
ON absolute_scores(final_absolute_score DESC);

COMMENT ON TABLE absolute_scores IS 'Absolute trend scores for NQ100 - measures price vs moving averages';
COMMENT ON COLUMN absolute_scores.nq200ma_score IS 'Score based on price vs 200-day moving average (30% weight)';
COMMENT ON COLUMN absolute_scores.nq50ma_score IS 'Score based on price vs 50-day moving average (30% weight)';
COMMENT ON COLUMN absolute_scores.nq20ema50ema_score IS 'Score based on 20EMA vs 50EMA crossover (20% weight)';
COMMENT ON COLUMN absolute_scores.mtf_score IS 'Multi-timeframe trend direction consensus (10% weight)';
COMMENT ON COLUMN absolute_scores.market_phase_score IS 'Market phase score: accumulation/markup/distribution/markdown (10% weight)';

-- ============================================================
-- Table 2: reference_scores
-- Stores NQ100 comprehensive reference scores
-- ============================================================

CREATE TABLE IF NOT EXISTS reference_scores (
    id SERIAL PRIMARY KEY,
    components_breadth_score INTEGER CHECK (components_breadth_score BETWEEN 0 AND 100),
    components_risk_score INTEGER CHECK (components_risk_score BETWEEN 0 AND 100),
    technical_rsi_score INTEGER CHECK (technical_rsi_score BETWEEN 0 AND 100),
    technical_atr_score INTEGER CHECK (technical_atr_score BETWEEN 0 AND 100),
    technical_zscore_score INTEGER CHECK (technical_zscore_score BETWEEN 0 AND 100),
    technical_macd_score INTEGER CHECK (technical_macd_score BETWEEN 0 AND 100),
    technical_divergence_score INTEGER CHECK (technical_divergence_score BETWEEN 0 AND 100),
    money_flow_futures_score INTEGER CHECK (money_flow_futures_score BETWEEN 0 AND 100),
    money_flow_etf_score INTEGER CHECK (money_flow_etf_score BETWEEN 0 AND 100),
    final_reference_score INTEGER CHECK (final_reference_score BETWEEN 0 AND 100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reference_scores_timestamp 
ON reference_scores(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_reference_scores_final 
ON reference_scores(final_reference_score DESC);

COMMENT ON TABLE reference_scores IS 'Comprehensive reference scores for NQ100 - components, technical, and money flow';
COMMENT ON COLUMN reference_scores.components_breadth_score IS 'Percentage of top stocks above MA (20% weight)';
COMMENT ON COLUMN reference_scores.components_risk_score IS 'Event risk score from news/sentiment (10% weight)';
COMMENT ON COLUMN reference_scores.technical_rsi_score IS 'RSI overbought/oversold indicator (15% weight)';
COMMENT ON COLUMN reference_scores.technical_atr_score IS 'ATR volatility normalizer (10% weight)';
COMMENT ON COLUMN reference_scores.technical_zscore_score IS 'Z-score deviation from mean (10% weight)';
COMMENT ON COLUMN reference_scores.technical_macd_score IS 'MACD histogram direction (5% weight)';
COMMENT ON COLUMN reference_scores.technical_divergence_score IS 'Price vs indicator divergence (5% weight)';
COMMENT ON COLUMN reference_scores.money_flow_futures_score IS 'NQ futures open interest change (15% weight)';
COMMENT ON COLUMN reference_scores.money_flow_etf_score IS 'TQQQ/QQQ ETF inflow (10% weight)';

-- ============================================================
-- Table 3: system_config
-- Stores system weights and configuration
-- ============================================================

CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_config_name 
ON system_config(config_name);

COMMENT ON TABLE system_config IS 'System configuration storage for weights and parameters';

-- ============================================================
-- Insert Default Configurations
-- ============================================================

-- Absolute Weights Configuration
INSERT INTO system_config (config_name, config_value, description) 
VALUES (
    'absolute_weights',
    '{
        "nq200ma": 30,
        "nq50ma": 30,
        "nq20ema50ema": 20,
        "mtf": 10,
        "market_phase": 10
    }'::jsonb,
    'Absolute score weight configuration - must sum to 100'
) ON CONFLICT (config_name) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Reference Weights Configuration
INSERT INTO system_config (config_name, config_value, description) 
VALUES (
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
    }'::jsonb,
    'Reference score weight configuration - must sum to 100'
) ON CONFLICT (config_name) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Trading Parameters Configuration
INSERT INTO system_config (config_name, config_value, description) 
VALUES (
    'trading_parameters',
    '{
        "max_position_size": 0.33,
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.05,
        "max_daily_loss": 0.02,
        "max_total_risk": 0.04,
        "max_positions": 3,
        "min_score_to_buy": 70,
        "max_score_to_sell": 30
    }'::jsonb,
    'Trading risk parameters'
) ON CONFLICT (config_name) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================
-- Verification Queries
-- ============================================================

-- Verify tables created
SELECT 'Tables created:' AS status;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('absolute_scores', 'reference_scores', 'system_config');

-- Verify weights sum to 100
SELECT 
    config_name,
    (config_value->>'nq200ma')::int + (config_value->>'nq50ma')::int + 
    (config_value->>'nq20ema50ema')::int + (config_value->>'mtf')::int + 
    (config_value->>'market_phase')::int AS total_weight
FROM system_config 
WHERE config_name = 'absolute_weights';

SELECT 
    config_name,
    (config_value->>'components_breadth')::int + (config_value->>'components_risk')::int + 
    (config_value->>'technical_rsi')::int + (config_value->>'technical_atr')::int + 
    (config_value->>'technical_zscore')::int + (config_value->>'technical_macd')::int + 
    (config_value->>'technical_divergence')::int + (config_value->>'money_flow_futures')::int + 
    (config_value->>'money_flow_etf')::int AS total_weight
FROM system_config 
WHERE config_name = 'reference_weights';

-- ============================================================
-- End of Script
-- ============================================================