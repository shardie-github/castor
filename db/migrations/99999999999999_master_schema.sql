-- Master Schema Migration
-- This file consolidates all database migrations into a single, idempotent migration
-- that can bootstrap a fresh database from zero to the complete schema.
-- 
-- Usage: Apply this migration to a fresh PostgreSQL database with TimescaleDB extension.
-- All operations are idempotent and safe to run multiple times.

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Tenants table (multi-tenancy foundation)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

-- Tenant settings
CREATE TABLE IF NOT EXISTS tenant_settings (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tenant quotas
CREATE TABLE IF NOT EXISTS tenant_quotas (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    max_users INTEGER DEFAULT 10,
    max_podcasts INTEGER DEFAULT 5,
    max_campaigns INTEGER DEFAULT 20,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User email preferences
CREATE TABLE IF NOT EXISTS user_email_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    marketing_emails BOOLEAN DEFAULT TRUE,
    product_updates BOOLEAN DEFAULT TRUE,
    security_alerts BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User metrics
CREATE TABLE IF NOT EXISTS user_metrics (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC,
    metric_data JSONB DEFAULT '{}'::JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_user_metrics_user_id ON user_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_metrics_recorded_at ON user_metrics(recorded_at);

-- Podcasts table
CREATE TABLE IF NOT EXISTS podcasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rss_feed_url VARCHAR(500),
    website_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_podcasts_tenant_id ON podcasts(tenant_id);

-- Episodes table
CREATE TABLE IF NOT EXISTS episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    episode_number INTEGER,
    published_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    audio_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX IF NOT EXISTS idx_episodes_published_at ON episodes(published_at);

-- Sponsors table
CREATE TABLE IF NOT EXISTS sponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sponsors_tenant_id ON sponsors(tenant_id);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    sponsor_id UUID REFERENCES sponsors(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    stage VARCHAR(50) DEFAULT 'draft',
    stage_changed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_stage CHECK (stage IN ('draft', 'active', 'paused', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_campaigns_tenant_id ON campaigns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_sponsor_id ON campaigns(sponsor_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_stage ON campaigns(stage);

-- ============================================================================
-- EVENT TABLES (TimescaleDB Hypertables)
-- ============================================================================

-- Listener events (converted to hypertable)
CREATE TABLE IF NOT EXISTS listener_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    listener_id VARCHAR(255),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_listener_events_tenant_id ON listener_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_listener_events_episode_id ON listener_events(episode_id);
CREATE INDEX IF NOT EXISTS idx_listener_events_occurred_at ON listener_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_listener_events_event_type ON listener_events(event_type);

-- Convert to hypertable if TimescaleDB is available
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE hypertable_name = 'listener_events'
    ) THEN
        PERFORM create_hypertable('listener_events', 'occurred_at', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Set retention policy (optional, adjust as needed)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM timescaledb_information.jobs 
        WHERE proc_name = 'policy_retention' 
        AND hypertable_name = 'listener_events'
    ) THEN
        -- Policy already exists
        NULL;
    ELSE
        -- Add retention policy: keep data for 2 years
        PERFORM add_retention_policy('listener_events', INTERVAL '2 years', if_not_exists => TRUE);
    END IF;
END $$;

-- Attribution events (converted to hypertable)
CREATE TABLE IF NOT EXISTS attribution_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    listener_id VARCHAR(255),
    attribution_type VARCHAR(50) NOT NULL,
    attribution_data JSONB DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attribution_events_tenant_id ON attribution_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_events_campaign_id ON attribution_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_events_episode_id ON attribution_events(episode_id);
CREATE INDEX IF NOT EXISTS idx_attribution_events_occurred_at ON attribution_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_attribution_events_attribution_type ON attribution_events(attribution_type);

-- Convert to hypertable
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE hypertable_name = 'attribution_events'
    ) THEN
        PERFORM create_hypertable('attribution_events', 'occurred_at',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Attribution event metadata
CREATE TABLE IF NOT EXISTS attribution_event_metadata (
    event_id UUID PRIMARY KEY REFERENCES attribution_events(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Listener metrics (converted to hypertable)
CREATE TABLE IF NOT EXISTS listener_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_data JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_listener_metrics_tenant_id ON listener_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_listener_metrics_episode_id ON listener_metrics(episode_id);
CREATE INDEX IF NOT EXISTS idx_listener_metrics_metric_date ON listener_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_listener_metrics_metric_name ON listener_metrics(metric_name);

-- Convert to hypertable
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE hypertable_name = 'listener_metrics'
    ) THEN
        PERFORM create_hypertable('listener_metrics', 'metric_date',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- ============================================================================
-- CONTINUOUS AGGREGATES (TimescaleDB Materialized Views)
-- ============================================================================

-- Listener events hourly aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS listener_events_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', occurred_at) AS hour,
    tenant_id,
    episode_id,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT listener_id) AS unique_listeners
FROM listener_events
GROUP BY hour, tenant_id, episode_id, event_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_listener_events_hourly_unique 
    ON listener_events_hourly (hour, tenant_id, episode_id, event_type);

-- Add refresh policy for hourly aggregate
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.continuous_aggregates 
        WHERE view_name = 'listener_events_hourly'
    ) THEN
        PERFORM add_continuous_aggregate_policy('listener_events_hourly',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Listener events daily aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS listener_events_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', occurred_at) AS day,
    tenant_id,
    episode_id,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT listener_id) AS unique_listeners
FROM listener_events
GROUP BY day, tenant_id, episode_id, event_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_listener_events_daily_unique 
    ON listener_events_daily (day, tenant_id, episode_id, event_type);

-- Add refresh policy for daily aggregate
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.continuous_aggregates 
        WHERE view_name = 'listener_events_daily'
    ) THEN
        PERFORM add_continuous_aggregate_policy('listener_events_daily',
            start_offset => INTERVAL '3 days',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Metrics daily view (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily AS
SELECT
    lm.metric_date AS day,
    lm.tenant_id,
    lm.episode_id,
    lm.metric_name,
    SUM(lm.metric_value) AS total_value,
    AVG(lm.metric_value) AS avg_value,
    COUNT(*) AS record_count
FROM listener_metrics lm
GROUP BY lm.metric_date, lm.tenant_id, lm.episode_id, lm.metric_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_metrics_daily_unique 
    ON metrics_daily (day, tenant_id, episode_id, metric_name);

CREATE INDEX IF NOT EXISTS idx_metrics_daily_day ON metrics_daily(day);
CREATE INDEX IF NOT EXISTS idx_metrics_daily_tenant_id ON metrics_daily(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metrics_daily_episode_id ON metrics_daily(episode_id);

-- Unique index for tenant_id adaptation (if tenant_id exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'metrics_daily' AND column_name = 'tenant_id'
    ) THEN
        CREATE UNIQUE INDEX IF NOT EXISTS ux_metrics_daily_day_ep_source 
            ON metrics_daily(day, tenant_id, episode_id, metric_name);
    END IF;
END $$;

-- ============================================================================
-- AUTHENTICATION TABLES
-- ============================================================================

-- Email verification tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires_at ON email_verification_tokens(expires_at);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- Refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- ============================================================================
-- AUTHORIZATION TABLES (RBAC/ABAC)
-- ============================================================================

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource_type VARCHAR(100),
    action VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_permissions_resource_type ON permissions(resource_type);

-- User roles (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);

-- Role permissions (many-to-many)
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Resource ownership (ABAC)
CREATE TABLE IF NOT EXISTS resource_ownership (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(resource_type, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_resource_ownership_tenant_id ON resource_ownership(tenant_id);
CREATE INDEX IF NOT EXISTS idx_resource_ownership_resource ON resource_ownership(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_ownership_owner_id ON resource_ownership(owner_id);

-- Access control policies (ABAC)
CREATE TABLE IF NOT EXISTS access_control_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_definition JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_control_policies_tenant_id ON access_control_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_access_control_policies_enabled ON access_control_policies(enabled);

-- Access logs
CREATE TABLE IF NOT EXISTS access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    action VARCHAR(100),
    allowed BOOLEAN NOT NULL,
    reason TEXT,
    ip_address INET,
    user_agent TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_tenant_id ON access_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_resource ON access_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_occurred_at ON access_logs(occurred_at);

-- ============================================================================
-- ADVANCED ATTRIBUTION TABLES
-- ============================================================================

-- Attribution models
CREATE TABLE IF NOT EXISTS attribution_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    configuration JSONB DEFAULT '{}'::JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attribution_models_tenant_id ON attribution_models(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_models_model_type ON attribution_models(model_type);

-- Attribution paths
CREATE TABLE IF NOT EXISTS attribution_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    listener_id VARCHAR(255) NOT NULL,
    touchpoints JSONB NOT NULL,
    conversion_event_id UUID REFERENCES attribution_events(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attribution_paths_tenant_id ON attribution_paths(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_campaign_id ON attribution_paths(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_listener_id ON attribution_paths(listener_id);

-- Attribution validations
CREATE TABLE IF NOT EXISTS attribution_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    attribution_event_id UUID REFERENCES attribution_events(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL,
    passed BOOLEAN NOT NULL,
    details JSONB DEFAULT '{}'::JSONB,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attribution_validations_tenant_id ON attribution_validations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_validations_event_id ON attribution_validations(attribution_event_id);

-- Attribution analytics
CREATE TABLE IF NOT EXISTS attribution_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, campaign_id, analysis_date)
);

CREATE INDEX IF NOT EXISTS idx_attribution_analytics_tenant_id ON attribution_analytics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_analytics_campaign_id ON attribution_analytics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_analytics_analysis_date ON attribution_analytics(analysis_date);

-- ============================================================================
-- SECURITY & COMPLIANCE TABLES
-- ============================================================================

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    changes JSONB DEFAULT '{}'::JSONB,
    ip_address INET,
    user_agent TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_occurred_at ON audit_logs(occurred_at);

-- Security events
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}'::JSONB,
    ip_address INET,
    user_agent TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_events_tenant_id ON security_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_occurred_at ON security_events(occurred_at);

-- GDPR requests
CREATE TABLE IF NOT EXISTS gdpr_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_gdpr_requests_tenant_id ON gdpr_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_requests_user_id ON gdpr_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_requests_status ON gdpr_requests(status);

-- API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    scopes TEXT[],
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);

-- ============================================================================
-- INTEGRATIONS TABLES
-- ============================================================================

-- Integrations
CREATE TABLE IF NOT EXISTS integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    integration_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    configuration JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_integrations_tenant_id ON integrations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);

-- Integration tokens
CREATE TABLE IF NOT EXISTS integration_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL,
    token_value_encrypted TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_integration_tokens_integration_id ON integration_tokens(integration_id);

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    event_types TEXT[] NOT NULL,
    secret VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant_id ON webhooks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_integration_id ON webhooks(integration_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_enabled ON webhooks(enabled);

-- Integration sync logs
CREATE TABLE IF NOT EXISTS integration_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_integration_id ON integration_sync_logs(integration_id);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_status ON integration_sync_logs(status);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_started_at ON integration_sync_logs(started_at);

-- ============================================================================
-- MONETIZATION TABLES
-- ============================================================================

-- Agencies
CREATE TABLE IF NOT EXISTS agencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    commission_rate NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agencies_tenant_id ON agencies(tenant_id);

-- Affiliates
CREATE TABLE IF NOT EXISTS affiliates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    commission_rate NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_affiliates_tenant_id ON affiliates(tenant_id);

-- Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    referrer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    referred_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrals_tenant_id ON referrals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);

-- Referral commissions
CREATE TABLE IF NOT EXISTS referral_commissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referral_id UUID REFERENCES referrals(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referral_commissions_referral_id ON referral_commissions(referral_id);
CREATE INDEX IF NOT EXISTS idx_referral_commissions_status ON referral_commissions(status);

-- AI token usage
CREATE TABLE IF NOT EXISTS ai_token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    token_count INTEGER NOT NULL,
    usage_type VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_token_usage_tenant_id ON ai_token_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_usage_user_id ON ai_token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_usage_created_at ON ai_token_usage(created_at);

-- AI token balances
CREATE TABLE IF NOT EXISTS ai_token_balances (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    balance INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_token_balances_user_id ON ai_token_balances(user_id);

-- API usage
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_tenant_id ON api_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_api_key_id ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_occurred_at ON api_usage(occurred_at);

-- White label settings
CREATE TABLE IF NOT EXISTS white_label_settings (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    brand_name VARCHAR(255),
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),
    custom_domain VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subscription tiers
CREATE TABLE IF NOT EXISTS subscription_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    price_monthly NUMERIC(10,2),
    price_yearly NUMERIC(10,2),
    features JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Billing transactions
CREATE TABLE IF NOT EXISTS billing_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    subscription_tier_id UUID REFERENCES subscription_tiers(id) ON DELETE SET NULL,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL,
    stripe_transaction_id VARCHAR(255),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_transactions_tenant_id ON billing_transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_user_id ON billing_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_status ON billing_transactions(status);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_occurred_at ON billing_transactions(occurred_at);

-- ============================================================================
-- OPTIMIZATION TABLES
-- ============================================================================

-- Experiments
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experiments_tenant_id ON experiments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);

-- Experiment assignments
CREATE TABLE IF NOT EXISTS experiment_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    variant VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (experiment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment_id ON experiment_assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_user_id ON experiment_assignments(user_id);

-- Experiment events
CREATE TABLE IF NOT EXISTS experiment_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experiment_events_experiment_id ON experiment_events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_events_user_id ON experiment_events(user_id);
CREATE INDEX IF NOT EXISTS idx_experiment_events_occurred_at ON experiment_events(occurred_at);

-- Churn events
CREATE TABLE IF NOT EXISTS churn_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    churn_reason VARCHAR(255),
    churn_data JSONB DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_churn_events_tenant_id ON churn_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_churn_events_user_id ON churn_events(user_id);
CREATE INDEX IF NOT EXISTS idx_churn_events_occurred_at ON churn_events(occurred_at);

-- Onboarding steps
CREATE TABLE IF NOT EXISTS onboarding_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_key VARCHAR(100) UNIQUE NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_onboarding_steps_order_index ON onboarding_steps(order_index);

-- Onboarding progress
CREATE TABLE IF NOT EXISTS onboarding_progress (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    step_id UUID REFERENCES onboarding_steps(id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ,
    skipped_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, step_id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_progress_user_id ON onboarding_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_step_id ON onboarding_progress(step_id);

-- ============================================================================
-- ETL & BUSINESS DOMAIN TABLES
-- ============================================================================

-- ETL imports
CREATE TABLE IF NOT EXISTS etl_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    import_type VARCHAR(100) NOT NULL,
    source VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    records_imported INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_etl_imports_tenant_id ON etl_imports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_etl_imports_status ON etl_imports(status);
CREATE INDEX IF NOT EXISTS idx_etl_imports_started_at ON etl_imports(started_at);

-- Ad units
CREATE TABLE IF NOT EXISTS ad_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    unit_type VARCHAR(100) NOT NULL,
    position_seconds INTEGER,
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_units_tenant_id ON ad_units(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ad_units_campaign_id ON ad_units(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ad_units_episode_id ON ad_units(episode_id);

-- IO bookings
CREATE TABLE IF NOT EXISTS io_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    sponsor_id UUID REFERENCES sponsors(id) ON DELETE SET NULL,
    booking_date DATE NOT NULL,
    promo_code VARCHAR(100),
    vanity_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_io_bookings_tenant_id ON io_bookings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_io_bookings_campaign_id ON io_bookings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_io_bookings_sponsor_id ON io_bookings(sponsor_id);
CREATE INDEX IF NOT EXISTS idx_io_bookings_booking_date ON io_bookings(booking_date);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    advertiser_id UUID,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    score NUMERIC(5,2),
    rationale TEXT,
    signals JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_matches_tenant_id ON matches(tenant_id);
CREATE INDEX IF NOT EXISTS idx_matches_advertiser_id ON matches(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_matches_campaign_id ON matches(campaign_id);
CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(score);

-- ============================================================================
-- PARTNERSHIPS TABLES
-- ============================================================================

-- Partners
CREATE TABLE IF NOT EXISTS partners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    partner_type VARCHAR(100),
    contact_email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partners_tenant_id ON partners(tenant_id);

-- Partner integrations
CREATE TABLE IF NOT EXISTS partner_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    integration_type VARCHAR(100) NOT NULL,
    configuration JSONB DEFAULT '{}'::JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partner_integrations_partner_id ON partner_integrations(partner_id);

-- Marketplace listings
CREATE TABLE IF NOT EXISTS marketplace_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    listing_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    pricing JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_marketplace_listings_tenant_id ON marketplace_listings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_podcast_id ON marketplace_listings(podcast_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_status ON marketplace_listings(status);

-- Marketplace revenue
CREATE TABLE IF NOT EXISTS marketplace_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES marketplace_listings(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_tenant_id ON marketplace_revenue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_listing_id ON marketplace_revenue(listing_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_transaction_date ON marketplace_revenue(transaction_date);

-- ============================================================================
-- DISASTER RECOVERY TABLES
-- ============================================================================

-- Backup records
CREATE TABLE IF NOT EXISTS backup_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    backup_type VARCHAR(100) NOT NULL,
    backup_location VARCHAR(500),
    size_bytes BIGINT,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_backup_records_tenant_id ON backup_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(status);
CREATE INDEX IF NOT EXISTS idx_backup_records_started_at ON backup_records(started_at);

-- Replication status
CREATE TABLE IF NOT EXISTS replication_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    replica_name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    lag_seconds INTEGER,
    last_sync_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_replication_status_status ON replication_status(status);

-- Failover events
CREATE TABLE IF NOT EXISTS failover_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    source_node VARCHAR(255),
    target_node VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_failover_events_status ON failover_events(status);
CREATE INDEX IF NOT EXISTS idx_failover_events_occurred_at ON failover_events(occurred_at);

-- Recovery procedures
CREATE TABLE IF NOT EXISTS recovery_procedures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procedure_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    last_tested_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- REPORTS TABLES
-- ============================================================================

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    report_type VARCHAR(100) NOT NULL,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_tenant_id ON reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reports_report_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports(generated_at);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    confidence_score NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcripts_episode_id ON transcripts(episode_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to set tenant context for RLS
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_uuid::TEXT, FALSE);
    PERFORM set_config('app.current_tenant_id', tenant_uuid::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to refresh metrics daily view
CREATE OR REPLACE FUNCTION refresh_metrics_daily()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY metrics_daily;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tenant-scoped tables
DO $$
DECLARE
    rls_table RECORD;
    rls_tables TEXT[] := ARRAY[
        'tenants', 'tenant_settings', 'tenant_quotas',
        'users', 'user_email_preferences', 'user_metrics',
        'podcasts', 'episodes', 'sponsors', 'campaigns',
        'listener_events', 'attribution_events', 'attribution_event_metadata', 'listener_metrics',
        'email_verification_tokens', 'password_reset_tokens', 'refresh_tokens',
        'roles', 'user_roles', 'permissions', 'role_permissions',
        'resource_ownership', 'access_control_policies', 'access_logs',
        'attribution_models', 'attribution_paths', 'attribution_validations', 'attribution_analytics',
        'audit_logs', 'security_events', 'gdpr_requests', 'api_keys',
        'integrations', 'integration_tokens', 'webhooks', 'integration_sync_logs',
        'agencies', 'affiliates', 'referrals', 'referral_commissions',
        'ai_token_usage', 'ai_token_balances', 'api_usage', 'white_label_settings',
        'subscription_tiers', 'billing_transactions',
        'experiments', 'experiment_assignments', 'experiment_events', 'churn_events',
        'onboarding_steps', 'onboarding_progress',
        'etl_imports', 'ad_units', 'io_bookings', 'matches',
        'partners', 'partner_integrations', 'marketplace_listings', 'marketplace_revenue',
        'backup_records', 'reports', 'transcripts'
    ];
BEGIN
    FOR rls_table IN 
        SELECT unnest(rls_tables) AS table_name
    LOOP
        -- Enable RLS if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = rls_table.table_name
        ) THEN
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', rls_table.table_name);
        END IF;
    END LOOP;
END $$;

-- Create tenant isolation policies
DO $$
DECLARE
    policy_table RECORD;
    policy_tables TEXT[] := ARRAY[
        'users', 'podcasts', 'campaigns', 'sponsors', 'reports',
        'listener_events', 'attribution_events', 'listener_metrics',
        'roles', 'user_roles', 'permissions', 'role_permissions',
        'resource_ownership', 'access_control_policies', 'access_logs',
        'attribution_models', 'attribution_paths', 'attribution_validations', 'attribution_analytics',
        'audit_logs', 'security_events', 'gdpr_requests', 'api_keys',
        'integrations', 'integration_tokens', 'webhooks', 'integration_sync_logs',
        'agencies', 'affiliates', 'referrals', 'ai_token_usage', 'ai_token_balances',
        'api_usage', 'white_label_settings', 'billing_transactions',
        'experiments', 'experiment_assignments', 'experiment_events', 'churn_events',
        'onboarding_progress', 'etl_imports', 'ad_units', 'io_bookings',
        'partners', 'partner_integrations', 'marketplace_listings', 'marketplace_revenue',
        'backup_records', 'reports'
    ];
    tenant_col TEXT;
BEGIN
    FOR policy_table IN 
        SELECT unnest(policy_tables) AS table_name
    LOOP
        -- Check if table exists and has tenant_id column
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = policy_table.table_name 
            AND column_name = 'tenant_id'
        ) THEN
            -- Determine tenant column name (some tables use different names)
            tenant_col := 'tenant_id';
            
            -- Drop existing policy if it exists
            EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', policy_table.table_name);
            
            -- Create tenant isolation policy
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I FOR ALL USING (%I = current_setting(''app.current_tenant'', TRUE)::UUID)',
                policy_table.table_name, tenant_col
            );
        END IF;
    END LOOP;
END $$;

-- Special RLS policies for referrals and marketplace_revenue (using app.current_tenant_id)
DO $$
BEGIN
    -- Referrals table
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'referrals'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'referrals' AND column_name = 'tenant_id'
    ) THEN
        EXECUTE 'DROP POLICY IF EXISTS tenant_isolation ON referrals';
        EXECUTE 'CREATE POLICY tenant_isolation ON referrals FOR ALL USING (tenant_id = current_setting(''app.current_tenant_id'', TRUE)::UUID)';
    END IF;
    
    -- Marketplace revenue table
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'marketplace_revenue'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'marketplace_revenue' AND column_name = 'tenant_id'
    ) THEN
        EXECUTE 'DROP POLICY IF EXISTS tenant_isolation ON marketplace_revenue';
        EXECUTE 'CREATE POLICY tenant_isolation ON marketplace_revenue FOR ALL USING (tenant_id = current_setting(''app.current_tenant_id'', TRUE)::UUID)';
    END IF;
END $$;

-- RLS policies for matches table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'matches'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'matches' AND column_name = 'tenant_id'
    ) THEN
        -- Enable RLS
        EXECUTE 'ALTER TABLE matches ENABLE ROW LEVEL SECURITY';
        
        -- Drop existing policies if they exist
        EXECUTE 'DROP POLICY IF EXISTS org_select_matches ON matches';
        EXECUTE 'DROP POLICY IF EXISTS org_insert_matches ON matches';
        EXECUTE 'DROP POLICY IF EXISTS org_update_matches ON matches';
        EXECUTE 'DROP POLICY IF EXISTS org_delete_matches ON matches';
        
        -- Create policies
        EXECUTE 'CREATE POLICY org_select_matches ON matches FOR SELECT USING (tenant_id = current_setting(''app.current_tenant'', TRUE)::UUID)';
        EXECUTE 'CREATE POLICY org_insert_matches ON matches FOR INSERT WITH CHECK (tenant_id = current_setting(''app.current_tenant'', TRUE)::UUID)';
        EXECUTE 'CREATE POLICY org_update_matches ON matches FOR UPDATE USING (tenant_id = current_setting(''app.current_tenant'', TRUE)::UUID)';
        EXECUTE 'CREATE POLICY org_delete_matches ON matches FOR DELETE USING (tenant_id = current_setting(''app.current_tenant'', TRUE)::UUID)';
    END IF;
END $$;

-- System-level policies for replication_status and failover_events (no tenant_id)
DO $$
BEGIN
    -- Replication status (system-level, no tenant isolation)
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'replication_status'
    ) THEN
        EXECUTE 'ALTER TABLE replication_status ENABLE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS system_access ON replication_status';
        EXECUTE 'CREATE POLICY system_access ON replication_status FOR ALL USING (true)';
    END IF;
    
    -- Failover events (system-level, no tenant isolation)
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'failover_events'
    ) THEN
        EXECUTE 'ALTER TABLE failover_events ENABLE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS system_access ON failover_events';
        EXECUTE 'CREATE POLICY system_access ON failover_events FOR ALL USING (true)';
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenants IS 'Multi-tenant organization table';
COMMENT ON TABLE users IS 'User accounts with tenant association';
COMMENT ON TABLE podcasts IS 'Podcast entities owned by tenants';
COMMENT ON TABLE episodes IS 'Individual podcast episodes';
COMMENT ON TABLE campaigns IS 'Marketing campaigns with stage tracking';
COMMENT ON TABLE listener_events IS 'Time-series events from podcast listeners (TimescaleDB hypertable)';
COMMENT ON TABLE attribution_events IS 'Attribution events for campaign tracking (TimescaleDB hypertable)';
COMMENT ON TABLE listener_metrics IS 'Aggregated listener metrics (TimescaleDB hypertable)';
