-- Cross-Platform Attribution Schema Migration
-- Adds support for web, mobile, and offline conversion tracking

-- 1. Conversion Events Table (unified conversion tracking)
CREATE TABLE IF NOT EXISTS conversion_events (
    conversion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    conversion_type VARCHAR(50) NOT NULL,
    conversion_value DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    device_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    referrer_url VARCHAR(1000),
    landing_page_url VARCHAR(1000),
    conversion_data JSONB DEFAULT '{}',
    attribution_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_platform CHECK (platform IN ('web', 'mobile_ios', 'mobile_android', 'offline', 'in_store', 'phone', 'email')),
    CONSTRAINT valid_conversion_type CHECK (conversion_type IN ('purchase', 'signup', 'download', 'trial_start', 'subscription', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_conversion_events_tenant_id ON conversion_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_campaign_id ON conversion_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_timestamp ON conversion_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversion_events_platform ON conversion_events(platform);
CREATE INDEX IF NOT EXISTS idx_conversion_events_user_id ON conversion_events(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_session_id ON conversion_events(session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_device_id ON conversion_events(device_id);

-- 2. User Journey Table (cross-device tracking)
CREATE TABLE IF NOT EXISTS user_journeys (
    journey_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    unified_user_id UUID,
    first_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    devices JSONB DEFAULT '[]',
    sessions JSONB DEFAULT '[]',
    touchpoints JSONB DEFAULT '[]',
    conversions JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_journeys_tenant_id ON user_journeys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_journeys_user_id ON user_journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_journeys_unified_user_id ON user_journeys(unified_user_id);
CREATE INDEX IF NOT EXISTS idx_user_journeys_first_seen ON user_journeys(first_seen_at);

-- 3. Device Fingerprints Table (for cross-device matching)
CREATE TABLE IF NOT EXISTS device_fingerprints (
    fingerprint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    fingerprint_hash VARCHAR(255) NOT NULL,
    device_type VARCHAR(50),
    device_os VARCHAR(50),
    browser VARCHAR(100),
    screen_resolution VARCHAR(50),
    timezone VARCHAR(50),
    language VARCHAR(10),
    ip_address INET,
    user_agent TEXT,
    unified_user_id UUID,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(tenant_id, fingerprint_hash)
);

CREATE INDEX IF NOT EXISTS idx_device_fingerprints_tenant_id ON device_fingerprints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_device_fingerprints_device_id ON device_fingerprints(device_id);
CREATE INDEX IF NOT EXISTS idx_device_fingerprints_unified_user_id ON device_fingerprints(unified_user_id);
CREATE INDEX IF NOT EXISTS idx_device_fingerprints_hash ON device_fingerprints(fingerprint_hash);

-- 4. Offline Conversions Table (for imported conversions)
CREATE TABLE IF NOT EXISTS offline_conversions (
    offline_conversion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    conversion_date DATE NOT NULL,
    conversion_time TIME,
    conversion_type VARCHAR(50) NOT NULL,
    conversion_value DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    customer_id VARCHAR(255),
    order_id VARCHAR(255),
    store_location VARCHAR(255),
    import_source VARCHAR(100),
    import_batch_id UUID,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    matched_to_attribution BOOLEAN DEFAULT FALSE,
    matched_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_conversion_type CHECK (conversion_type IN ('purchase', 'return', 'refund', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_offline_conversions_tenant_id ON offline_conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_offline_conversions_campaign_id ON offline_conversions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_offline_conversions_date ON offline_conversions(conversion_date);
CREATE INDEX IF NOT EXISTS idx_offline_conversions_customer_id ON offline_conversions(customer_id);
CREATE INDEX IF NOT EXISTS idx_offline_conversions_matched ON offline_conversions(matched_to_attribution) WHERE matched_to_attribution = FALSE;

-- Add RLS policies
ALTER TABLE conversion_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_journeys ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_fingerprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE offline_conversions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_conversion_events ON conversion_events
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_user_journeys ON user_journeys
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_device_fingerprints ON device_fingerprints
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_offline_conversions ON offline_conversions
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
