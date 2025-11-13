-- Cost Tracking Schema Migration
-- Adds support for cost tracking, monitoring, and budget management

-- 1. Cost Allocations Table
CREATE TABLE IF NOT EXISTS cost_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    cost_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    amount DECIMAL(10, 4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    unit VARCHAR(50),
    quantity DECIMAL(10, 4),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_cost_type CHECK (cost_type IN ('compute', 'storage', 'network', 'api_calls', 'database', 'cache', 'other'))
);

CREATE INDEX IF NOT EXISTS idx_cost_allocations_tenant_id ON cost_allocations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cost_allocations_date ON cost_allocations(date);
CREATE INDEX IF NOT EXISTS idx_cost_allocations_cost_type ON cost_allocations(cost_type);
CREATE INDEX IF NOT EXISTS idx_cost_allocations_service_name ON cost_allocations(service_name);
CREATE INDEX IF NOT EXISTS idx_cost_allocations_tenant_date ON cost_allocations(tenant_id, date);

-- 2. Resource Usage Table
CREATE TABLE IF NOT EXISTS resource_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10, 4) NOT NULL,
    unit VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resource_usage_tenant_id ON resource_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_timestamp ON resource_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_resource_usage_resource_type ON resource_usage(resource_type);
CREATE INDEX IF NOT EXISTS idx_resource_usage_metric_name ON resource_usage(metric_name);

-- 3. Cost Alerts Table
CREATE TABLE IF NOT EXISTS cost_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    threshold_percentage DECIMAL(5, 2),
    threshold_amount DECIMAL(10, 2),
    current_amount DECIMAL(10, 2),
    budget_period VARCHAR(50) DEFAULT 'monthly',
    status VARCHAR(50) DEFAULT 'active',
    triggered_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_alert_type CHECK (alert_type IN ('budget_threshold', 'anomaly', 'quota_exceeded')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'triggered', 'acknowledged', 'resolved'))
);

CREATE INDEX IF NOT EXISTS idx_cost_alerts_tenant_id ON cost_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cost_alerts_status ON cost_alerts(status);
CREATE INDEX IF NOT EXISTS idx_cost_alerts_triggered_at ON cost_alerts(triggered_at);

-- Add RLS policies
ALTER TABLE cost_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_cost_allocations ON cost_allocations
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_resource_usage ON resource_usage
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_cost_alerts ON cost_alerts
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
