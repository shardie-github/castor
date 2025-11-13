-- TimescaleDB Hypertables Migration
-- Converts time-series tables to hypertables and sets up retention policies

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert listener_events to hypertable
SELECT create_hypertable('listener_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes on listener_events
CREATE INDEX IF NOT EXISTS idx_listener_events_podcast_id ON listener_events(podcast_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_listener_events_episode_id ON listener_events(episode_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_listener_events_campaign_id ON listener_events(campaign_id, timestamp DESC) WHERE campaign_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_listener_events_platform ON listener_events(platform, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_listener_events_event_type ON listener_events(event_type, timestamp DESC);

-- Convert attribution_events to hypertable
SELECT create_hypertable('attribution_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes on attribution_events
CREATE INDEX IF NOT EXISTS idx_attribution_events_campaign_id ON attribution_events(campaign_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attribution_events_podcast_id ON attribution_events(podcast_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attribution_events_method ON attribution_events(attribution_method, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attribution_events_user_id ON attribution_events(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_attribution_events_cross_device ON attribution_events(cross_device_match_id) WHERE cross_device_match_id IS NOT NULL;

-- Convert listener_metrics to hypertable
SELECT create_hypertable('listener_metrics', 'timestamp', if_not_exists => TRUE);

-- Create indexes on listener_metrics
CREATE INDEX IF NOT EXISTS idx_listener_metrics_podcast_id ON listener_metrics(podcast_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_listener_metrics_episode_id ON listener_metrics(episode_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_listener_metrics_metric_type ON listener_metrics(metric_type, timestamp DESC);

-- Add retention policies (90 days for raw events)
SELECT add_retention_policy('listener_events', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('attribution_events', INTERVAL '2 years', if_not_exists => TRUE);
SELECT add_retention_policy('listener_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Create continuous aggregates for hourly aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS listener_events_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    podcast_id,
    episode_id,
    campaign_id,
    event_type,
    platform,
    country_code,
    COUNT(*) AS event_count,
    AVG(listen_duration_seconds) AS avg_duration,
    AVG(completion_rate) AS avg_completion_rate
FROM listener_events
GROUP BY bucket, podcast_id, episode_id, campaign_id, event_type, platform, country_code;

-- Add refresh policy for hourly aggregate
SELECT add_continuous_aggregate_policy('listener_events_hourly',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Create continuous aggregates for daily aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS listener_events_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    podcast_id,
    episode_id,
    campaign_id,
    event_type,
    platform,
    country_code,
    COUNT(*) AS event_count,
    AVG(listen_duration_seconds) AS avg_duration,
    AVG(completion_rate) AS avg_completion_rate
FROM listener_events
GROUP BY bucket, podcast_id, episode_id, campaign_id, event_type, platform, country_code;

-- Add refresh policy for daily aggregate
SELECT add_continuous_aggregate_policy('listener_events_daily',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);
