-- Initial Database Schema Migration
-- Creates all tables, indexes, and constraints

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    persona_segment VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer')),
    CONSTRAINT valid_tier CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_persona_segment ON users(persona_segment);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- 2. Podcasts Table
CREATE TABLE IF NOT EXISTS podcasts (
    podcast_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    image_url VARCHAR(1000),
    feed_url VARCHAR(1000) NOT NULL,
    website_url VARCHAR(1000),
    language VARCHAR(10) DEFAULT 'en',
    category VARCHAR(100),
    explicit BOOLEAN DEFAULT FALSE,
    platform_configs JSONB DEFAULT '{}',
    ingestion_status VARCHAR(50) DEFAULT 'active',
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_ingestion_status CHECK (ingestion_status IN ('active', 'paused', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX IF NOT EXISTS idx_podcasts_feed_url ON podcasts(feed_url);
CREATE INDEX IF NOT EXISTS idx_podcasts_ingestion_status ON podcasts(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_podcasts_created_at ON podcasts(created_at);

-- 3. Episodes Table
CREATE TABLE IF NOT EXISTS episodes (
    episode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    guid VARCHAR(500) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    audio_url VARCHAR(1000) NOT NULL,
    duration_seconds INTEGER,
    publish_date TIMESTAMP WITH TIME ZONE NOT NULL,
    link VARCHAR(1000),
    author VARCHAR(255),
    categories TEXT[],
    explicit BOOLEAN DEFAULT FALSE,
    transcript_url VARCHAR(1000),
    transcript_status VARCHAR(50) DEFAULT 'pending',
    ad_slots JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT unique_episode_guid UNIQUE (podcast_id, guid),
    CONSTRAINT valid_transcript_status CHECK (transcript_status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX IF NOT EXISTS idx_episodes_publish_date ON episodes(publish_date);
CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid);
CREATE INDEX IF NOT EXISTS idx_episodes_transcript_status ON episodes(transcript_status) WHERE transcript_status != 'completed';

-- 4. Sponsors Table
CREATE TABLE IF NOT EXISTS sponsors (
    sponsor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    email VARCHAR(255),
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(1000),
    logo_url VARCHAR(1000),
    industry VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sponsors_user_id ON sponsors(user_id);
CREATE INDEX IF NOT EXISTS idx_sponsors_name ON sponsors(name);

-- 5. Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    sponsor_id UUID NOT NULL REFERENCES sponsors(sponsor_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_value DECIMAL(10, 2) NOT NULL,
    episode_ids UUID[] DEFAULT '{}',
    attribution_config JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'scheduled', 'active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT valid_date_range CHECK (end_date > start_date)
);

CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_podcast_id ON campaigns(podcast_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_sponsor_id ON campaigns(sponsor_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_date_range ON campaigns(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_campaigns_episode_ids ON campaigns USING GIN(episode_ids);

-- 6. Listener Events Table (will be converted to hypertable)
CREATE TABLE IF NOT EXISTS listener_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    podcast_id UUID NOT NULL,
    episode_id UUID,
    campaign_id UUID,
    event_type VARCHAR(50) NOT NULL,
    platform VARCHAR(100),
    country_code VARCHAR(2),
    device_type VARCHAR(50),
    device_os VARCHAR(50),
    listen_duration_seconds INTEGER,
    completion_rate DECIMAL(5, 4),
    user_agent TEXT,
    ip_address INET,
    session_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_event_type CHECK (event_type IN ('download', 'stream', 'listen_start', 'listen_complete', 'skip', 'ad_start', 'ad_complete', 'ad_skip'))
);

-- 7. Attribution Events Table (will be converted to hypertable)
CREATE TABLE IF NOT EXISTS attribution_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id),
    episode_id UUID REFERENCES episodes(episode_id),
    attribution_method VARCHAR(50) NOT NULL,
    attribution_data JSONB NOT NULL DEFAULT '{}',
    conversion_data JSONB DEFAULT '{}',
    listener_event_id UUID,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    device_id VARCHAR(255),
    cross_device_match_id UUID,
    demographic_lift JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_attribution_method CHECK (attribution_method IN ('promo_code', 'pixel', 'utm', 'direct', 'custom'))
);

-- 8. Transcripts Table
CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    source VARCHAR(50) NOT NULL DEFAULT 'automated',
    language VARCHAR(10) DEFAULT 'en',
    transcript_text TEXT,
    transcript_json JSONB,
    word_count INTEGER,
    duration_seconds INTEGER,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_source CHECK (source IN ('automated', 'manual', 'uploaded'))
);

CREATE INDEX IF NOT EXISTS idx_transcripts_episode_id ON transcripts(episode_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_status ON transcripts(status) WHERE status != 'completed';
CREATE INDEX IF NOT EXISTS idx_transcripts_language ON transcripts(language);

-- 9. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    template_id VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(50) NOT NULL,
    file_url VARCHAR(1000),
    file_size_bytes BIGINT,
    includes_roi BOOLEAN DEFAULT FALSE,
    includes_attribution BOOLEAN DEFAULT FALSE,
    includes_benchmarks BOOLEAN DEFAULT FALSE,
    date_range_start TIMESTAMP WITH TIME ZONE,
    date_range_end TIMESTAMP WITH TIME ZONE,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_report_type CHECK (report_type IN ('sponsor_report', 'performance_summary', 'roi_report', 'custom')),
    CONSTRAINT valid_format CHECK (format IN ('pdf', 'csv', 'excel', 'json'))
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_campaign_id ON reports(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);

-- 10. Listener Metrics Table (for analytics store - TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS listener_metrics (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    podcast_id UUID NOT NULL,
    episode_id UUID,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    platform VARCHAR(100),
    country VARCHAR(100),
    device VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);
