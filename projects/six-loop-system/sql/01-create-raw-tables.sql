-- Six Loop System - Raw Data Tables
-- Database: trading_db
-- Created: 2026-04-20

-- Drop tables if exist (for fresh setup)
DROP TABLE IF EXISTS raw_market_data CASCADE;
DROP TABLE IF EXISTS raw_market_data_backup CASCADE;

-- Main raw market data table
CREATE TABLE raw_market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(12,4),
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    volume BIGINT,
    turnover DECIMAL(20,2),
    open_interest BIGINT,
    bid_price DECIMAL(12,4),
    ask_price DECIMAL(12,4),
    bid_volume BIGINT,
    ask_volume BIGINT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) DEFAULT 'tick',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX idx_raw_market_data_symbol_timestamp
ON raw_market_data(symbol, timestamp DESC);

CREATE INDEX idx_raw_market_data_source_timestamp
ON raw_market_data(source, timestamp DESC);

-- Backup table for investing.com data (verification)
CREATE TABLE raw_market_data_backup (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(12,4),
    change_value DECIMAL(12,4),
    change_percent DECIMAL(8,4),
    volume BIGINT,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_backup_symbol_timestamp
ON raw_market_data_backup(symbol, timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE raw_market_data IS 'Real-time market data from Futu OpenD';
COMMENT ON TABLE raw_market_data_backup IS 'Backup data from investing.com for verification';
COMMENT ON COLUMN raw_market_data.source IS 'Data source: futu_opend, investing, tradingview, jin10';
COMMENT ON COLUMN raw_market_data.symbol IS 'Trading symbol: MNQ (NQ 100 Mini), TQQQ';
