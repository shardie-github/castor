-- Automation and Self-Service Schema Migration
-- Adds task scheduling and self-service onboarding tables

-- 1. Scheduled Tasks Table
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    schedule_cron VARCHAR(100),
    schedule_interval_seconds INTEGER,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'running', 'completed', 'failed', 'cancelled')),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_type ON scheduled_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at) WHERE status IN ('scheduled', 'pending');
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_priority ON scheduled_tasks(priority DESC);

-- 2. Onboarding Progress Table
CREATE TABLE IF NOT EXISTS onboarding_progress (
    onboarding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    current_step VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'abandoned')),
    completed_steps JSONB DEFAULT '[]',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_onboarding_progress_tenant_id ON onboarding_progress(tenant_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_status ON onboarding_progress(status);

-- Add RLS policies
ALTER TABLE onboarding_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY onboarding_progress_tenant_isolation ON onboarding_progress
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);
