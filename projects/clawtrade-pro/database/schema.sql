-- ClawTrade Pro Database Schema
-- 數據庫初始化腳本

-- 價格數據表
CREATE TABLE IF NOT EXISTS price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    volume INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT DEFAULT 'futu',
    INDEX idx_symbol_time (symbol, timestamp)
);

-- K線數據表
CREATE TABLE IF NOT EXISTS kline_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    period TEXT NOT NULL,  -- 1MIN, 5MIN, 15MIN, 30MIN, 60MIN, DAY, WEEK, MONTH
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    UNIQUE(symbol, period, timestamp),
    INDEX idx_kline (symbol, period, timestamp)
);

-- 交易記錄表
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,  -- BUY, SELL
    quantity INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME,
    pnl REAL,
    pnl_pct REAL,
    exit_reason TEXT,
    strategy TEXT DEFAULT 'TQQQ_Momentum',
    status TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED
    INDEX idx_symbol_time (symbol, entry_time)
);

-- 持倉表
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,  -- LONG, SHORT
    quantity INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    unrealized_pnl REAL,
    entry_time DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED
    INDEX idx_symbol (symbol)
);

-- 賬戶歷史表
CREATE TABLE IF NOT EXISTS account_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_assets REAL NOT NULL,
    cash REAL NOT NULL,
    market_value REAL NOT NULL,
    buying_power REAL NOT NULL,
    daily_pnl REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_time (timestamp)
);

-- 風險事件表
CREATE TABLE IF NOT EXISTS risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    symbol TEXT,
    message TEXT NOT NULL,
    level TEXT NOT NULL,  -- LOW, MEDIUM, HIGH, CRITICAL
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_time (timestamp)
);

-- 止損止盈設置表
CREATE TABLE IF NOT EXISTS stop_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER,
    symbol TEXT NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    trailing_stop REAL,
    time_stop DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

-- 交易信號表
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- BUY, SELL, HOLD, CLOSE
    price REAL NOT NULL,
    z_score REAL,
    rsi REAL,
    volume_ratio REAL,
    reason TEXT,
    executed BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_time (symbol, timestamp)
);

-- 系統日誌表
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,  -- DEBUG, INFO, WARNING, ERROR
    component TEXT,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_time (timestamp)
);

-- 回測結果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital REAL NOT NULL,
    final_equity REAL NOT NULL,
    total_return REAL NOT NULL,
    total_trades INTEGER,
    win_rate REAL,
    profit_factor REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    config TEXT,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 創建視圖：持倉摘要
CREATE VIEW IF NOT EXISTS position_summary AS
SELECT 
    symbol,
    side,
    SUM(quantity) as total_quantity,
    AVG(avg_price) as avg_entry_price,
    SUM(market_value) as total_market_value,
    SUM(unrealized_pnl) as total_unrealized_pnl,
    COUNT(*) as position_count
FROM positions
WHERE status = 'OPEN'
GROUP BY symbol, side;

-- 創建視圖：每日交易統計
CREATE VIEW IF NOT EXISTS daily_trading_stats AS
SELECT 
    DATE(entry_time) as date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_profit,
    AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
FROM trades
WHERE status = 'CLOSED'
GROUP BY DATE(entry_time);
