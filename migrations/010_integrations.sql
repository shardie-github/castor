-- Integrations Schema Migration
-- Adds support for integration management, OAuth tokens, and webhooks

-- 1. Integrations Table
CREATE TABLE IF NOT EXISTS integrations (
    integration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    integration_name VARCHAR(100) NOT NULL,
    integration_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    configuration JSONB DEFAULT '{}',
    last_synced_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_integration_type CHECK (integration_type IN ('hosting', 'ecommerce', 'marketing', 'communication', 'automation')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error', 'configuring')),
    UNIQUE(tenant_id, integration_name)
);

CREATE INDEX IF NOT EXISTS idx_integrations_tenant_id ON integrations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_integrations_name ON integrations(integration_name);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);

-- 2. Integration Tokens Table (OAuth tokens)
CREATE TABLE IF NOT EXISTS integration_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    integration_name VARCHAR(100) NOT NULL,
    token_value TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE,
    scopes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(tenant_id, integration_name)
);

CREATE INDEX IF NOT EXISTS idx_integration_tokens_tenant_id ON integration_tokens(tenant_id);
CREATE INDEX IF NOT EXISTS idx_integration_tokens_integration_name ON integration_tokens(integration_name);
CREATE INDEX IF NOT EXISTS idx_integration_tokens_expires_at ON integration_tokens(expires_at) WHERE expires_at IS NOT NULL;

-- 3. Webhooks Table
CREATE TABLE IF NOT EXISTS webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    integration_name VARCHAR(100) NOT NULL,
    webhook_url VARCHAR(1000) NOT NULL,
    webhook_secret VARCHAR(255),
    events TEXT[] NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant_id ON webhooks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_integration_name ON webhooks(integration_name);
CREATE INDEX IF NOT EXISTS idx_webhooks_status ON webhooks(status);

-- 4. Integration Sync Logs Table
CREATE TABLE IF NOT EXISTS integration_sync_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    integration_name VARCHAR(100) NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_synced INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_sync_type CHECK (sync_type IN ('full', 'incremental', 'manual')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_tenant_id ON integration_sync_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_integration_name ON integration_sync_logs(integration_name);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_status ON integration_sync_logs(status);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_started_at ON integration_sync_logs(started_at DESC);

-- Add RLS policies
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_sync_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_integrations ON integrations
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_integration_tokens ON integration_tokens
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_webhooks ON webhooks
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_integration_sync_logs ON integration_sync_logs
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
