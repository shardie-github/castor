# Comprehensive Database Schema & Data Lineage

## Overview

This document defines the complete database schema and data lineage for the podcast analytics and sponsorship platform, supporting multi-platform ingestion, attribution tracking, ROI calculations, and reporting.

## Schema Architecture

### Database Strategy

- **PostgreSQL (Primary)**: Relational data (users, podcasts, campaigns, sponsors, reports)
- **TimescaleDB/InfluxDB**: Time-series data (listener events, metrics, attribution events)
- **Redis**: Caching and session management
- **Data Warehouse (BigQuery/Redshift)**: Historical analytics and BI queries

---

## Core Entity Schemas

### 1. Users

**Table:** `users`

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user', -- admin, user, viewer
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free', -- free, starter, professional, enterprise
    persona_segment VARCHAR(100), -- solo_podcaster, producer, agency, enterprise
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer')),
    CONSTRAINT valid_tier CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_persona_segment ON users(persona_segment);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
```

**Data Lineage:**
- **Source:** User registration, OAuth providers
- **Transforms:** Password hashing, persona classification
- **Dependencies:** None
- **Downstream:** Campaigns, podcasts, reports, billing

---

### 2. Podcasts

**Table:** `podcasts`

```sql
CREATE TABLE podcasts (
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
    platform_configs JSONB DEFAULT '{}', -- Platform-specific settings
    ingestion_status VARCHAR(50) DEFAULT 'active', -- active, paused, error
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_ingestion_status CHECK (ingestion_status IN ('active', 'paused', 'error'))
);

CREATE INDEX idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX idx_podcasts_feed_url ON podcasts(feed_url);
CREATE INDEX idx_podcasts_ingestion_status ON podcasts(ingestion_status);
CREATE INDEX idx_podcasts_created_at ON podcasts(created_at);
```

**Data Lineage:**
- **Source:** RSS feeds, platform APIs (Apple Podcasts, Spotify, Google Podcasts)
- **Transforms:** Feed parsing, metadata normalization, deduplication
- **Dependencies:** Users
- **Downstream:** Episodes, campaigns, listener events, reports

**Platform Configurations:**
```json
{
  "apple_podcasts": {
    "connect_api_key": "encrypted",
    "podcast_id": "1234567890",
    "last_sync": "2024-01-15T10:00:00Z"
  },
  "spotify": {
    "api_key": "encrypted",
    "show_id": "abc123",
    "last_sync": "2024-01-15T10:00:00Z"
  },
  "google_podcasts": {
    "api_key": "encrypted",
    "feed_id": "xyz789",
    "last_sync": "2024-01-15T10:00:00Z"
  }
}
```

---

### 3. Episodes

**Table:** `episodes`

```sql
CREATE TABLE episodes (
    episode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    guid VARCHAR(500) NOT NULL, -- Unique identifier from RSS feed
    title VARCHAR(500) NOT NULL,
    description TEXT,
    audio_url VARCHAR(1000) NOT NULL,
    duration_seconds INTEGER,
    publish_date TIMESTAMP WITH TIME ZONE NOT NULL,
    link VARCHAR(1000),
    author VARCHAR(255),
    categories TEXT[],
    explicit BOOLEAN DEFAULT FALSE,
    transcript_url VARCHAR(1000), -- Link to transcript storage
    transcript_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    ad_slots JSONB DEFAULT '[]', -- Detected ad slot timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT unique_episode_guid UNIQUE (podcast_id, guid),
    CONSTRAINT valid_transcript_status CHECK (transcript_status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX idx_episodes_publish_date ON episodes(publish_date);
CREATE INDEX idx_episodes_guid ON episodes(guid);
CREATE INDEX idx_episodes_transcript_status ON episodes(transcript_status) WHERE transcript_status != 'completed';
```

**Data Lineage:**
- **Source:** RSS feed parsing, platform APIs
- **Transforms:** Metadata extraction, ad slot detection, transcript generation
- **Dependencies:** Podcasts
- **Downstream:** Listener events, campaigns, attribution events, reports

**Ad Slots Structure:**
```json
[
  {
    "start_time_seconds": 120,
    "end_time_seconds": 180,
    "campaign_id": "uuid",
    "detection_method": "manual|automated|transcript",
    "confidence": 0.95
  }
]
```

---

### 4. Sponsors

**Table:** `sponsors`

```sql
CREATE TABLE sponsors (
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

CREATE INDEX idx_sponsors_user_id ON sponsors(user_id);
CREATE INDEX idx_sponsors_name ON sponsors(name);
```

**Data Lineage:**
- **Source:** User input, CRM imports
- **Transforms:** Data normalization, enrichment
- **Dependencies:** Users
- **Downstream:** Campaigns, reports

---

### 5. Campaigns

**Table:** `campaigns`

```sql
CREATE TABLE campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    sponsor_id UUID NOT NULL REFERENCES sponsors(sponsor_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, scheduled, active, paused, completed, cancelled
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_value DECIMAL(10, 2) NOT NULL, -- Sponsorship fee
    episode_ids UUID[] DEFAULT '{}', -- Array of episode IDs
    attribution_config JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'scheduled', 'active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT valid_date_range CHECK (end_date > start_date)
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_podcast_id ON campaigns(podcast_id);
CREATE INDEX idx_campaigns_sponsor_id ON campaigns(sponsor_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_date_range ON campaigns(start_date, end_date);
CREATE INDEX idx_campaigns_episode_ids ON campaigns USING GIN(episode_ids);
```

**Attribution Config Structure:**
```json
{
  "method": "promo_code|pixel|utm|custom",
  "promo_code": "PODCAST2024",
  "pixel_url": "https://example.com/track",
  "utm_source": "podcast",
  "utm_medium": "audio",
  "utm_campaign": "campaign_name",
  "custom_tracking_id": "custom_123",
  "conversion_endpoint": "https://api.example.com/conversions"
}
```

**Data Lineage:**
- **Source:** User creation, campaign management UI
- **Transforms:** Status transitions, attribution setup
- **Dependencies:** Users, Podcasts, Sponsors, Episodes
- **Downstream:** Attribution events, listener events, reports, ROI calculations

---

### 6. Listener Events (Time-Series)

**Table:** `listener_events` (TimescaleDB hypertable)

```sql
-- Create hypertable for time-series data
CREATE TABLE listener_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    podcast_id UUID NOT NULL,
    episode_id UUID,
    campaign_id UUID, -- Optional: if event is associated with a campaign
    event_type VARCHAR(50) NOT NULL, -- download, stream, listen_start, listen_complete, skip
    platform VARCHAR(100), -- apple_podcasts, spotify, google_podcasts, etc.
    country_code VARCHAR(2),
    device_type VARCHAR(50), -- mobile, desktop, smart_speaker, etc.
    device_os VARCHAR(50),
    listen_duration_seconds INTEGER,
    completion_rate DECIMAL(5, 4), -- 0.0000 to 1.0000
    user_agent TEXT,
    ip_address INET,
    session_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_event_type CHECK (event_type IN ('download', 'stream', 'listen_start', 'listen_complete', 'skip', 'ad_start', 'ad_complete', 'ad_skip'))
);

-- Convert to hypertable
SELECT create_hypertable('listener_events', 'timestamp');

CREATE INDEX idx_listener_events_podcast_id ON listener_events(podcast_id, timestamp DESC);
CREATE INDEX idx_listener_events_episode_id ON listener_events(episode_id, timestamp DESC);
CREATE INDEX idx_listener_events_campaign_id ON listener_events(campaign_id, timestamp DESC) WHERE campaign_id IS NOT NULL;
CREATE INDEX idx_listener_events_platform ON listener_events(platform, timestamp DESC);
CREATE INDEX idx_listener_events_event_type ON listener_events(event_type, timestamp DESC);
```

**Data Lineage:**
- **Source:** Platform APIs (Apple Podcasts Connect, Spotify for Podcasters, Google Podcasts Manager), webhook receivers
- **Transforms:** Event normalization, deduplication, aggregation
- **Dependencies:** Podcasts, Episodes, Campaigns
- **Downstream:** Attribution matching, ROI calculations, reports, analytics dashboards

**Retention Policy:**
- Raw events: 90 days
- Aggregated hourly: 1 year
- Aggregated daily: 7 years

---

### 7. Attribution Events

**Table:** `attribution_events` (TimescaleDB hypertable)

```sql
CREATE TABLE attribution_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    podcast_id UUID NOT NULL REFERENCES podcasts(podcast_id),
    episode_id UUID REFERENCES episodes(episode_id),
    attribution_method VARCHAR(50) NOT NULL, -- promo_code, pixel, utm, direct
    attribution_data JSONB NOT NULL DEFAULT '{}',
    conversion_data JSONB DEFAULT '{}',
    listener_event_id UUID, -- Link to listener event if matched
    user_id VARCHAR(255), -- External user ID from conversion
    session_id VARCHAR(255),
    device_id VARCHAR(255),
    cross_device_match_id UUID, -- For cross-device matching
    demographic_lift JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_attribution_method CHECK (attribution_method IN ('promo_code', 'pixel', 'utm', 'direct', 'custom'))
);

SELECT create_hypertable('attribution_events', 'timestamp');

CREATE INDEX idx_attribution_events_campaign_id ON attribution_events(campaign_id, timestamp DESC);
CREATE INDEX idx_attribution_events_podcast_id ON attribution_events(podcast_id, timestamp DESC);
CREATE INDEX idx_attribution_events_method ON attribution_events(attribution_method, timestamp DESC);
CREATE INDEX idx_attribution_events_user_id ON attribution_events(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_attribution_events_cross_device ON attribution_events(cross_device_match_id) WHERE cross_device_match_id IS NOT NULL;
```

**Attribution Data Structure:**
```json
{
  "promo_code": "PODCAST2024",
  "utm_source": "podcast",
  "utm_medium": "audio",
  "utm_campaign": "campaign_name",
  "pixel_id": "pixel_123",
  "referrer": "https://example.com"
}
```

**Conversion Data Structure:**
```json
{
  "conversion_type": "purchase|signup|download|trial",
  "conversion_value": 99.99,
  "currency": "USD",
  "order_id": "order_123",
  "product_id": "product_456"
}
```

**Demographic Lift Structure:**
```json
{
  "age_group": "25-34",
  "gender": "male",
  "location": "US-CA",
  "device_type": "mobile",
  "baseline_conversion_rate": 0.02,
  "campaign_conversion_rate": 0.05,
  "lift": 0.03
}
```

**Data Lineage:**
- **Source:** Conversion tracking pixels, promo code redemptions, UTM parameter tracking, direct API calls
- **Transforms:** Cross-device matching, demographic enrichment, lift calculation
- **Dependencies:** Campaigns, Listener Events
- **Downstream:** ROI calculations, reports, sponsor exports

---

### 8. Transcripts

**Table:** `transcripts`

```sql
CREATE TABLE transcripts (
    transcript_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    source VARCHAR(50) NOT NULL DEFAULT 'automated', -- automated, manual, uploaded
    language VARCHAR(10) DEFAULT 'en',
    transcript_text TEXT,
    transcript_json JSONB, -- Structured transcript with timestamps
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

CREATE INDEX idx_transcripts_episode_id ON transcripts(episode_id);
CREATE INDEX idx_transcripts_status ON transcripts(status) WHERE status != 'completed';
CREATE INDEX idx_transcripts_language ON transcripts(language);
```

**Transcript JSON Structure:**
```json
{
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 5.2,
      "text": "Welcome to the podcast...",
      "speaker": "host",
      "confidence": 0.95
    }
  ],
  "speakers": [
    {
      "id": "host",
      "name": "John Doe"
    }
  ],
  "ad_segments": [
    {
      "start_time": 120.0,
      "end_time": 180.0,
      "sponsor": "Example Sponsor",
      "detected": true
    }
  ]
}
```

**Data Lineage:**
- **Source:** Audio transcription services (Whisper, Google Speech-to-Text, manual uploads)
- **Transforms:** Text extraction, speaker diarization, ad slot detection
- **Dependencies:** Episodes
- **Downstream:** Ad slot detection, search indexing, reports

---

### 9. Reports

**Table:** `reports`

```sql
CREATE TABLE reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    template_id VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- sponsor_report, performance_summary, roi_report, custom
    format VARCHAR(50) NOT NULL, -- pdf, csv, excel, json
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

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_campaign_id ON reports(campaign_id);
CREATE INDEX idx_reports_generated_at ON reports(generated_at DESC);
CREATE INDEX idx_reports_type ON reports(report_type);
```

**Data Lineage:**
- **Source:** Campaign performance data, attribution events, listener events, ROI calculations
- **Transforms:** Data aggregation, visualization generation, PDF/CSV/Excel export
- **Dependencies:** Users, Campaigns, Attribution Events, Listener Events
- **Downstream:** Sponsor exports, email delivery, user downloads

---

## Data Lineage Map

### Ingestion Flow

```
External Sources (RSS, APIs, Webhooks)
    ↓
Ingestion Layer (rss_ingest.py, platform integrations)
    ↓
Normalization & Validation
    ↓
PostgreSQL (podcasts, episodes)
    ↓
TimescaleDB (listener_events)
```

### Attribution Flow

```
Conversion Sources (Pixels, Promo Codes, UTM)
    ↓
Attribution Engine (attribution matching)
    ↓
Cross-Device Matching
    ↓
Demographic Enrichment
    ↓
TimescaleDB (attribution_events)
    ↓
ROI Calculations
```

### Reporting Flow

```
Campaigns + Listener Events + Attribution Events
    ↓
Analytics Aggregation
    ↓
ROI Calculations
    ↓
Report Generation
    ↓
Storage (reports table)
    ↓
Sponsor Export / Email Delivery
```

---

## Data Quality & Validation

### Completeness Requirements

- **Podcasts:** 100% must have feed_url, title, user_id
- **Episodes:** 100% must have guid, title, audio_url, publish_date
- **Campaigns:** 100% must have campaign_id, podcast_id, sponsor_id, start_date, end_date
- **Attribution Events:** 95%+ must have valid attribution_method and campaign_id
- **Listener Events:** 90%+ must have platform, event_type, timestamp

### Accuracy Requirements

- **Attribution Accuracy:** 95%+ validated accuracy (test campaigns)
- **ROI Calculation Accuracy:** 98%+ validated accuracy (manual verification)
- **Metric Accuracy:** 99%+ accuracy vs. source platforms (cross-validation)

### Freshness Requirements

- **Real-time Data:** <1 hour latency from event to availability
- **Daily Aggregates:** Available by 2 AM UTC next day
- **Historical Data:** Available within 24 hours of request

---

## Multi-Platform Ingestion Support

### Platform-Specific Schemas

**Apple Podcasts:**
- Uses Apple Podcasts Connect API
- Metrics: downloads, streams, completion rates
- Demographics: country, device type, age groups

**Spotify:**
- Uses Spotify for Podcasters API
- Metrics: streams, starts, completion rates
- Demographics: country, age, gender

**Google Podcasts:**
- Uses Google Podcasts Manager API
- Metrics: plays, completions
- Demographics: country, device

**Generic RSS:**
- Polls RSS feeds every 15 minutes
- Extracts episode metadata
- No listener metrics (requires platform APIs)

---

## Data Retention Policies

- **Raw Listener Events:** 90 days
- **Aggregated Hourly Metrics:** 1 year
- **Aggregated Daily Metrics:** 7 years
- **Attribution Events:** 2 years
- **Reports:** 5 years
- **Transcripts:** Indefinite (for search/indexing)
- **Campaigns:** Indefinite (historical records)

---

## Indexing Strategy

### High-Frequency Queries

1. **Campaign Performance:** `campaign_id + timestamp`
2. **Episode Metrics:** `episode_id + timestamp`
3. **User Reports:** `user_id + generated_at`
4. **Attribution Matching:** `campaign_id + attribution_method + timestamp`

### Composite Indexes

- `(podcast_id, timestamp DESC)` for time-series queries
- `(campaign_id, status, start_date)` for campaign management
- `(user_id, subscription_tier)` for monetization queries

---

*Last Updated: [Current Date]*
*Version: 1.0*
