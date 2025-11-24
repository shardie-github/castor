-- AI Features Schema Migration
-- Adds support for AI-powered insights, predictions, and recommendations

-- 1. AI Insights Table
CREATE TABLE IF NOT EXISTS ai_insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(episode_id) ON DELETE SET NULL,
    insight_type VARCHAR(50) NOT NULL,
    content TEXT,
    summary TEXT,
    sentiment_score DECIMAL(3, 2),
    topics JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    confidence_score DECIMAL(3, 2),
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_insight_type CHECK (insight_type IN ('content_analysis', 'performance_prediction', 'optimization_recommendation', 'anomaly_detection'))
);

CREATE INDEX IF NOT EXISTS idx_ai_insights_tenant_id ON ai_insights(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_insights_campaign_id ON ai_insights(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ai_insights_episode_id ON ai_insights(episode_id);
CREATE INDEX IF NOT EXISTS idx_ai_insights_type ON ai_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_ai_insights_created_at ON ai_insights(created_at DESC);

-- 2. Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    prediction_type VARCHAR(50) NOT NULL,
    predicted_value DECIMAL(10, 2),
    confidence_interval_lower DECIMAL(10, 2),
    confidence_interval_upper DECIMAL(10, 2),
    actual_value DECIMAL(10, 2),
    accuracy_score DECIMAL(5, 4),
    model_version VARCHAR(50),
    input_features JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_prediction_type CHECK (prediction_type IN ('campaign_performance', 'roi', 'conversions', 'churn', 'revenue'))
);

CREATE INDEX IF NOT EXISTS idx_predictions_tenant_id ON predictions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_predictions_campaign_id ON predictions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);

-- 3. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    action_items JSONB DEFAULT '[]',
    expected_impact VARCHAR(50),
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    accepted_at TIMESTAMP WITH TIME ZONE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_recommendation_type CHECK (recommendation_type IN ('campaign_optimization', 'content_improvement', 'timing_optimization', 'pricing_adjustment', 'feature_adoption')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'accepted', 'rejected', 'implemented'))
);

CREATE INDEX IF NOT EXISTS idx_recommendations_tenant_id ON recommendations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_campaign_id ON recommendations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON recommendations(priority);

-- Add RLS policies
ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_ai_insights ON ai_insights
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_predictions ON predictions
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_recommendations ON recommendations
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
