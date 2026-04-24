-- Create achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    trade_date DATE UNIQUE,
    total_pnl DECIMAL(10,2),
    win_rate DECIMAL(5,2),
    max_drawdown DECIMAL(5,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    badges_earned JSONB,
    posted_to_alfredrpg BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_achievements_date ON achievements(trade_date);
CREATE INDEX IF NOT EXISTS idx_achievements_posted ON achievements(posted_to_alfredrpg);

COMMENT ON TABLE achievements IS 'Daily trading performance and achievements';
COMMENT ON COLUMN achievements.badges_earned IS 'JSON array of earned badges';