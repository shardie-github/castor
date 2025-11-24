-- DELTA:20251113_064143 Metrics Daily View
-- Creates a materialized view for daily aggregated metrics

BEGIN;

-- Create metrics_daily materialized view (or table if preferred)
-- This aggregates listener_metrics and attribution_events into daily summaries

CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily AS
SELECT 
    DATE(timestamp) as day,
    episode_id,
    podcast_id,
    tenant_id,
    platform as source,
    COUNT(*) FILTER (WHERE metric_type = 'download') as downloads,
    COUNT(DISTINCT session_id) FILTER (WHERE metric_type = 'download') as listeners,
    AVG(metadata->>'completion_rate')::numeric as completion_rate,
    AVG(metadata->>'ctr')::numeric as ctr,
    COUNT(*) FILTER (WHERE metadata->>'conversions' IS NOT NULL) as conversions,
    SUM((metadata->>'revenue_cents')::numeric) FILTER (WHERE metadata->>'revenue_cents' IS NOT NULL) as revenue_cents,
    MAX(timestamp) as last_updated
FROM listener_metrics
WHERE timestamp >= NOW() - INTERVAL '90 days'
GROUP BY DATE(timestamp), episode_id, podcast_id, tenant_id, platform;

-- Create unique index for upsert logic
CREATE UNIQUE INDEX IF NOT EXISTS idx_metrics_daily_unique 
ON metrics_daily(day, episode_id, source, tenant_id);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_metrics_daily_day ON metrics_daily(day DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_daily_episode ON metrics_daily(episode_id);
CREATE INDEX IF NOT EXISTS idx_metrics_daily_podcast ON metrics_daily(podcast_id);
CREATE INDEX IF NOT EXISTS idx_metrics_daily_tenant ON metrics_daily(tenant_id);

-- Create refresh function
CREATE OR REPLACE FUNCTION refresh_metrics_daily()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY metrics_daily;
END;
$$ LANGUAGE plpgsql;

-- Note: In production, schedule this refresh via cron or scheduled_tasks table
-- Example: SELECT refresh_metrics_daily(); should run daily at 2 AM UTC

COMMIT;
