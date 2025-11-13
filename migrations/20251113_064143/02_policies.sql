-- DELTA: 20251113_064143
-- RLS Policies for new tables
-- Only creates policies if RLS is already enabled (mirrors existing pattern)

BEGIN;

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY ON NEW TABLES
-- ============================================================================

ALTER TABLE etl_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE io_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- CREATE RLS POLICIES (mirror existing tenant isolation pattern)
-- ============================================================================

-- ETL Imports Policy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' 
        AND tablename = 'etl_imports' 
        AND policyname = 'tenant_isolation_etl_imports'
    ) THEN
        CREATE POLICY tenant_isolation_etl_imports ON etl_imports
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END$$;

-- Ad Units Policy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' 
        AND tablename = 'ad_units' 
        AND policyname = 'tenant_isolation_ad_units'
    ) THEN
        CREATE POLICY tenant_isolation_ad_units ON ad_units
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END$$;

-- IO Bookings Policy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' 
        AND tablename = 'io_bookings' 
        AND policyname = 'tenant_isolation_io_bookings'
    ) THEN
        CREATE POLICY tenant_isolation_io_bookings ON io_bookings
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END$$;

-- Matches Policy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' 
        AND tablename = 'matches' 
        AND policyname = 'tenant_isolation_matches'
    ) THEN
        CREATE POLICY tenant_isolation_matches ON matches
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END$$;

COMMIT;
