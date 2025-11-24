-- Advanced Attribution Schema Migration
-- Adds support for multiple attribution models and validation

-- 1. Attribution Models Table
CREATE TABLE IF NOT EXISTS attribution_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    model_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_model_type CHECK (model_type IN ('first_touch', 'last_touch', 'linear', 'time_decay', 'position_based', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_attribution_models_tenant_id ON attribution_models(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_models_campaign_id ON attribution_models(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_models_type ON attribution_models(model_type);

-- 2. Attribution Paths Table (for multi-touch attribution)
CREATE TABLE IF NOT EXISTS attribution_paths (
    path_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    device_id VARCHAR(255),
    conversion_id UUID,
    touchpoints JSONB NOT NULL DEFAULT '[]',
    conversion_value DECIMAL(10, 2),
    conversion_type VARCHAR(50),
    first_touch_at TIMESTAMP WITH TIME ZONE,
    last_touch_at TIMESTAMP WITH TIME ZONE,
    conversion_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_attribution_paths_tenant_id ON attribution_paths(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_campaign_id ON attribution_paths(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_user_id ON attribution_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_session_id ON attribution_paths(session_id);
CREATE INDEX IF NOT EXISTS idx_attribution_paths_conversion_at ON attribution_paths(conversion_at);

-- 3. Attribution Validations Table
CREATE TABLE IF NOT EXISTS attribution_validations (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    model_id UUID REFERENCES attribution_models(model_id) ON DELETE CASCADE,
    validation_type VARCHAR(50) NOT NULL,
    ground_truth_value DECIMAL(10, 2),
    predicted_value DECIMAL(10, 2),
    accuracy_score DECIMAL(5, 4),
    confidence_interval_lower DECIMAL(10, 2),
    confidence_interval_upper DECIMAL(10, 2),
    validation_status VARCHAR(50) DEFAULT 'pending',
    validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_validation_type CHECK (validation_type IN ('ground_truth', 'statistical', 'cross_validation', 'manual')),
    CONSTRAINT valid_validation_status CHECK (validation_status IN ('pending', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_attribution_validations_tenant_id ON attribution_validations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_validations_campaign_id ON attribution_validations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_validations_model_id ON attribution_validations(model_id);
CREATE INDEX IF NOT EXISTS idx_attribution_validations_status ON attribution_validations(validation_status);

-- 4. Attribution Analytics Table (pre-computed analytics)
CREATE TABLE IF NOT EXISTS attribution_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    model_id UUID REFERENCES attribution_models(model_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2) NOT NULL,
    breakdown JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('attributed_conversions', 'attributed_revenue', 'attribution_accuracy', 'touchpoint_count', 'path_length'))
);

CREATE INDEX IF NOT EXISTS idx_attribution_analytics_tenant_id ON attribution_analytics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_analytics_campaign_id ON attribution_analytics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_analytics_date ON attribution_analytics(date);
CREATE INDEX IF NOT EXISTS idx_attribution_analytics_metric_type ON attribution_analytics(metric_type);

-- Add RLS policies
ALTER TABLE attribution_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE attribution_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE attribution_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE attribution_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_attribution_models ON attribution_models
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_attribution_paths ON attribution_paths
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_attribution_validations ON attribution_validations
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_attribution_analytics ON attribution_analytics
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
