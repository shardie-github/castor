-- Migration: Add user_metrics table for TTFV and other user-level metrics
-- Created: 2024-12-XX
-- Purpose: Store calculated metrics per user (TTFV, completion rates, etc.)

CREATE TABLE IF NOT EXISTS user_metrics (
    user_id UUID NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, metric_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_metrics_user_id ON user_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_metrics_metric_name ON user_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_user_metrics_recorded_at ON user_metrics(recorded_at);

-- Add comment
COMMENT ON TABLE user_metrics IS 'Stores calculated metrics per user (TTFV, completion rates, etc.)';
COMMENT ON COLUMN user_metrics.metric_name IS 'Name of the metric (e.g., ttfv_seconds, completion_rate)';
COMMENT ON COLUMN user_metrics.metric_value IS 'Value of the metric';
