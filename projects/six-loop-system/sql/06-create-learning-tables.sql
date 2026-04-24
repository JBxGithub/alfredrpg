-- Create learning_logs table
CREATE TABLE IF NOT EXISTS learning_logs (
    id SERIAL PRIMARY KEY,
    week_start DATE,
    week_end DATE,
    performance_summary JSONB,
    parameter_changes JSONB,
    weight_adjustments JSONB,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_logs_week ON learning_logs(week_start);

COMMENT ON TABLE learning_logs IS 'Weekly learning and optimization logs';