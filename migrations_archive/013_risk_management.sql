-- Risk Management Schema Migration
-- Adds risk tracking, monitoring, and mitigation tables

-- 1. Risks Table
CREATE TABLE IF NOT EXISTS risks (
    risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    impact INTEGER NOT NULL CHECK (impact >= 1 AND impact <= 5),
    probability INTEGER NOT NULL CHECK (probability >= 1 AND probability <= 5),
    risk_score INTEGER NOT NULL GENERATED ALWAYS AS (impact * probability) STORED,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'mitigated', 'accepted', 'closed', 'archived')),
    owner VARCHAR(255) NOT NULL,
    mitigation_strategies JSONB DEFAULT '[]',
    next_review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_risks_tenant_id ON risks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_risks_category ON risks(category);
CREATE INDEX IF NOT EXISTS idx_risks_severity ON risks(severity);
CREATE INDEX IF NOT EXISTS idx_risks_status ON risks(status);
CREATE INDEX IF NOT EXISTS idx_risks_risk_score ON risks(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_risks_next_review ON risks(next_review_date) WHERE status = 'active';

-- 2. Risk Mitigations Table
CREATE TABLE IF NOT EXISTS risk_mitigations (
    mitigation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID NOT NULL REFERENCES risks(risk_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    mitigation_type VARCHAR(50) NOT NULL DEFAULT 'action',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMP WITH TIME ZONE,
    owner VARCHAR(255),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_risk_mitigations_risk_id ON risk_mitigations(risk_id);
CREATE INDEX IF NOT EXISTS idx_risk_mitigations_status ON risk_mitigations(status);
CREATE INDEX IF NOT EXISTS idx_risk_mitigations_due_date ON risk_mitigations(due_date) WHERE status IN ('pending', 'in_progress');

-- 3. Risk Reviews Table
CREATE TABLE IF NOT EXISTS risk_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID NOT NULL REFERENCES risks(risk_id) ON DELETE CASCADE,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reviewer VARCHAR(255) NOT NULL,
    review_notes TEXT,
    impact_updated INTEGER CHECK (impact_updated >= 1 AND impact_updated <= 5),
    probability_updated INTEGER CHECK (probability_updated >= 1 AND probability_updated <= 5),
    status_updated VARCHAR(20) CHECK (status_updated IN ('active', 'mitigated', 'accepted', 'closed', 'archived')),
    next_review_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_reviews_risk_id ON risk_reviews(risk_id);
CREATE INDEX IF NOT EXISTS idx_risk_reviews_review_date ON risk_reviews(review_date DESC);

-- Add RLS policies for multi-tenancy
ALTER TABLE risks ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_mitigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_reviews ENABLE ROW LEVEL SECURITY;

-- RLS policies (assuming tenant_id context function exists)
CREATE POLICY risks_tenant_isolation ON risks
    FOR ALL
    USING (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE POLICY risk_mitigations_tenant_isolation ON risk_mitigations
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM risks
            WHERE risks.risk_id = risk_mitigations.risk_id
            AND (risks.tenant_id IS NULL OR risks.tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID)
        )
    );

CREATE POLICY risk_reviews_tenant_isolation ON risk_reviews
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM risks
            WHERE risks.risk_id = risk_reviews.risk_id
            AND (risks.tenant_id IS NULL OR risks.tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID)
        )
    );
