-- Disaster Recovery Schema Migration
-- Adds support for backups, replication, and failover

-- 1. Backup Records Table
CREATE TABLE IF NOT EXISTS backup_records (
    backup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    backup_type VARCHAR(50) NOT NULL,
    backup_source VARCHAR(100) NOT NULL,
    backup_location VARCHAR(1000) NOT NULL,
    backup_size_bytes BIGINT,
    backup_format VARCHAR(50) DEFAULT 'sql',
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_status VARCHAR(50),
    retention_until TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_backup_type CHECK (backup_type IN ('full', 'incremental', 'differential', 'point_in_time')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'expired')),
    CONSTRAINT valid_verification_status CHECK (verification_status IS NULL OR verification_status IN ('passed', 'failed', 'pending'))
);

CREATE INDEX IF NOT EXISTS idx_backup_records_tenant_id ON backup_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backup_records_type ON backup_records(backup_type);
CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(status);
CREATE INDEX IF NOT EXISTS idx_backup_records_created_at ON backup_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backup_records_retention ON backup_records(retention_until) WHERE retention_until > NOW();

-- 2. Replication Status Table
CREATE TABLE IF NOT EXISTS replication_status (
    replication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_region VARCHAR(50) NOT NULL,
    target_region VARCHAR(50) NOT NULL,
    replication_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    lag_seconds INTEGER,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    last_verified_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_replication_type CHECK (replication_type IN ('database', 'cache', 'storage', 'full')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'failed', 'syncing'))
);

CREATE INDEX IF NOT EXISTS idx_replication_status_source_region ON replication_status(source_region);
CREATE INDEX IF NOT EXISTS idx_replication_status_target_region ON replication_status(target_region);
CREATE INDEX IF NOT EXISTS idx_replication_status_status ON replication_status(status);

-- 3. Failover Events Table
CREATE TABLE IF NOT EXISTS failover_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    failover_type VARCHAR(50) NOT NULL,
    source_region VARCHAR(50) NOT NULL,
    target_region VARCHAR(50) NOT NULL,
    trigger_reason VARCHAR(100),
    status VARCHAR(50) DEFAULT 'initiated',
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE,
    rollback_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    affected_tenants UUID[],
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_failover_type CHECK (failover_type IN ('automatic', 'manual', 'drill', 'planned')),
    CONSTRAINT valid_status CHECK (status IN ('initiated', 'in_progress', 'completed', 'failed', 'rolled_back'))
);

CREATE INDEX IF NOT EXISTS idx_failover_events_type ON failover_events(failover_type);
CREATE INDEX IF NOT EXISTS idx_failover_events_status ON failover_events(status);
CREATE INDEX IF NOT EXISTS idx_failover_events_initiated_at ON failover_events(initiated_at DESC);

-- 4. Recovery Procedures Table
CREATE TABLE IF NOT EXISTS recovery_procedures (
    procedure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    procedure_name VARCHAR(255) NOT NULL,
    procedure_type VARCHAR(50) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL DEFAULT '[]',
    estimated_rto_minutes INTEGER,
    estimated_rpo_minutes INTEGER,
    last_tested_at TIMESTAMP WITH TIME ZONE,
    test_status VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_procedure_type CHECK (procedure_type IN ('backup_restore', 'failover', 'database_recovery', 'full_disaster')),
    CONSTRAINT valid_test_status CHECK (test_status IS NULL OR test_status IN ('passed', 'failed', 'not_tested'))
);

CREATE INDEX IF NOT EXISTS idx_recovery_procedures_type ON recovery_procedures(procedure_type);
CREATE INDEX IF NOT EXISTS idx_recovery_procedures_name ON recovery_procedures(procedure_name);

-- Add RLS policies
ALTER TABLE backup_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE replication_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE failover_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_backup_records ON backup_records
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID OR tenant_id IS NULL);

-- Replication and failover are system-level, no tenant isolation needed
CREATE POLICY system_only_replication_status ON replication_status
    USING (TRUE);

CREATE POLICY system_only_failover_events ON failover_events
    USING (TRUE);
