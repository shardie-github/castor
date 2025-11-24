-- Post-Launch Optimization Schema Migration
-- Adds support for A/B testing, churn analysis, and onboarding optimization

-- 1. Experiments Table (A/B Testing)
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    experiment_name VARCHAR(255) NOT NULL,
    experiment_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    hypothesis TEXT,
    variants JSONB NOT NULL DEFAULT '[]',
    traffic_allocation DECIMAL(5, 2) DEFAULT 100.0,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    winner_variant VARCHAR(100),
    statistical_significance DECIMAL(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_experiment_type CHECK (experiment_type IN ('onboarding', 'feature', 'ui', 'pricing', 'content', 'campaign')),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'running', 'paused', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_experiments_tenant_id ON experiments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_type ON experiments(experiment_type);
CREATE INDEX IF NOT EXISTS idx_experiments_dates ON experiments(start_date, end_date);

-- 2. Experiment Assignments Table
CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    experiment_id UUID NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    variant VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(tenant_id, experiment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_experiment_assignments_tenant_id ON experiment_assignments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment_id ON experiment_assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_user_id ON experiment_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_variant ON experiment_assignments(variant);

-- 3. Experiment Events Table
CREATE TABLE IF NOT EXISTS experiment_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    experiment_id UUID NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES experiment_assignments(assignment_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_value DECIMAL(10, 2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_event_type CHECK (event_type IN ('conversion', 'engagement', 'completion', 'dropoff', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_experiment_events_tenant_id ON experiment_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_experiment_events_experiment_id ON experiment_events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_events_assignment_id ON experiment_events(assignment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_events_type ON experiment_events(event_type);
CREATE INDEX IF NOT EXISTS idx_experiment_events_timestamp ON experiment_events(timestamp);

-- 4. Churn Events Table
CREATE TABLE IF NOT EXISTS churn_events (
    churn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    churn_type VARCHAR(50) NOT NULL,
    churn_date DATE NOT NULL,
    churn_reason VARCHAR(255),
    predicted_probability DECIMAL(5, 4),
    predicted_at TIMESTAMP WITH TIME ZONE,
    intervention_applied BOOLEAN DEFAULT FALSE,
    intervention_type VARCHAR(100),
    intervention_result VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_churn_type CHECK (churn_type IN ('subscription_cancelled', 'account_deleted', 'inactive', 'downgrade')),
    CONSTRAINT valid_intervention_result CHECK (intervention_result IS NULL OR intervention_result IN ('success', 'failed', 'pending'))
);

CREATE INDEX IF NOT EXISTS idx_churn_events_tenant_id ON churn_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_churn_events_user_id ON churn_events(user_id);
CREATE INDEX IF NOT EXISTS idx_churn_events_churn_date ON churn_events(churn_date);
CREATE INDEX IF NOT EXISTS idx_churn_events_type ON churn_events(churn_type);
CREATE INDEX IF NOT EXISTS idx_churn_events_predicted ON churn_events(predicted_probability) WHERE predicted_probability IS NOT NULL;

-- 5. Onboarding Steps Table
CREATE TABLE IF NOT EXISTS onboarding_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_order INTEGER NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    required BOOLEAN DEFAULT TRUE,
    completion_criteria JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_step_type CHECK (step_type IN ('tutorial', 'setup', 'configuration', 'verification', 'custom')),
    UNIQUE(tenant_id, step_order)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_steps_tenant_id ON onboarding_steps(tenant_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_steps_order ON onboarding_steps(tenant_id, step_order);

-- 6. Onboarding Progress Table
CREATE TABLE IF NOT EXISTS onboarding_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    step_id UUID NOT NULL REFERENCES onboarding_steps(step_id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INTEGER,
    dropoff_reason TEXT,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped', 'dropped')),
    UNIQUE(tenant_id, user_id, step_id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_progress_tenant_id ON onboarding_progress(tenant_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_user_id ON onboarding_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_step_id ON onboarding_progress(step_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_status ON onboarding_progress(status);

-- Add RLS policies
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE churn_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_experiments ON experiments
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_experiment_assignments ON experiment_assignments
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_experiment_events ON experiment_events
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_churn_events ON churn_events
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_onboarding_steps ON onboarding_steps
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);

CREATE POLICY tenant_isolation_onboarding_progress ON onboarding_progress
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
