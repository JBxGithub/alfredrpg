-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER REFERENCES decisions(id),
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) CHECK (action IN ('BUY', 'SELL')),
    quantity INTEGER,
    price DECIMAL(10,2),
    total_value DECIMAL(12,2),
    pnl DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending', -- pending/filled/cancelled
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_decision_id ON trades(decision_id);

COMMENT ON TABLE trades IS 'Trade executions';
COMMENT ON COLUMN trades.status IS 'Trade status: pending, filled, or cancelled';