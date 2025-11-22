-- Migration: Add attribution_event_metadata table for storing pixel event metadata
-- Created: 2024-12-XX
-- Purpose: Store additional metadata from attribution pixel events

CREATE TABLE IF NOT EXISTS attribution_event_metadata (
    event_id UUID NOT NULL PRIMARY KEY,
    page_url TEXT,
    referrer TEXT,
    user_agent TEXT,
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_content VARCHAR(255),
    utm_term VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (event_id) REFERENCES attribution_events(event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attribution_event_metadata_event_id ON attribution_event_metadata(event_id);
CREATE INDEX IF NOT EXISTS idx_attribution_event_metadata_utm_campaign ON attribution_event_metadata(utm_campaign);
CREATE INDEX IF NOT EXISTS idx_attribution_event_metadata_created_at ON attribution_event_metadata(created_at);

-- Add comment
COMMENT ON TABLE attribution_event_metadata IS 'Stores additional metadata from attribution pixel events';
