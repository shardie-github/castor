-- DELTA: 20251113_064143
-- Safe DB Migration Pack - Additive Only
-- Creates new tables and columns for ETL, Deal Pipeline, IO Bookings, and Matchmaking

BEGIN;

-- ============================================================================
-- 1. ETL IMPORTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS etl_imports (
    import_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    source VARCHAR(100) NOT NULL, -- 'csv', 'google_sheets', etc.
    file_name VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Add indexes if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_etl_imports_tenant_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_etl_imports_tenant_id ON etl_imports(tenant_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_etl_imports_status' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_etl_imports_status ON etl_imports(status);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_etl_imports_started_at' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_etl_imports_started_at ON etl_imports(started_at DESC);
    END IF;
END$$;

-- ============================================================================
-- 2. AD UNITS TABLE (if needed for IO bookings)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ad_units (
    ad_unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    duration_seconds INTEGER,
    position VARCHAR(50) NOT NULL, -- 'pre', 'mid', 'post'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_position CHECK (position IN ('pre', 'mid', 'post'))
);

-- Add indexes if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_ad_units_tenant_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_ad_units_tenant_id ON ad_units(tenant_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_ad_units_podcast_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_ad_units_podcast_id ON ad_units(podcast_id);
    END IF;
END$$;

-- ============================================================================
-- 3. IO BOOKINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS io_bookings (
    io_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    ad_unit_id UUID REFERENCES ad_units(ad_unit_id) ON DELETE SET NULL,
    episode_id UUID REFERENCES episodes(episode_id) ON DELETE SET NULL,
    flight_start TIMESTAMP WITH TIME ZONE NOT NULL,
    flight_end TIMESTAMP WITH TIME ZONE NOT NULL,
    booked_impressions INTEGER,
    booked_cpm_cents INTEGER,
    promo_code TEXT,
    vanity_url TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled', 'makegood')),
    CONSTRAINT valid_flight_range CHECK (flight_end > flight_start)
);

-- Add indexes if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_io_bookings_tenant_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_io_bookings_tenant_id ON io_bookings(tenant_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_io_bookings_campaign_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_io_bookings_campaign_id ON io_bookings(campaign_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_io_bookings_episode_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_io_bookings_episode_id ON io_bookings(episode_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_io_bookings_flight' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_io_bookings_flight ON io_bookings(flight_start, flight_end);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_io_bookings_status' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_io_bookings_status ON io_bookings(status);
    END IF;
END$$;

-- ============================================================================
-- 4. MATCHES TABLE (for matchmaking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    advertiser_id UUID REFERENCES sponsors(sponsor_id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    score NUMERIC(5, 2) NOT NULL CHECK (score >= 0 AND score <= 100),
    rationale TEXT,
    signals JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_match UNIQUE(tenant_id, advertiser_id, podcast_id)
);

-- Add indexes if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_matches_tenant_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_matches_tenant_id ON matches(tenant_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_matches_advertiser_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_matches_advertiser_id ON matches(advertiser_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_matches_podcast_id' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_matches_podcast_id ON matches(podcast_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_matches_score' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_matches_score ON matches(score DESC);
    END IF;
END$$;

-- ============================================================================
-- 5. EXTEND CAMPAIGNS TABLE WITH DEAL PIPELINE STAGES
-- ============================================================================

-- Add stage column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'campaigns' AND column_name = 'stage'
    ) THEN
        ALTER TABLE campaigns ADD COLUMN stage VARCHAR(50) DEFAULT 'lead';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'campaigns' AND column_name = 'stage_changed_at'
    ) THEN
        ALTER TABLE campaigns ADD COLUMN stage_changed_at TIMESTAMP WITH TIME ZONE;
    END IF;
END$$;

-- Add check constraint if not exists (PostgreSQL doesn't support IF NOT EXISTS for constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'valid_stage' AND conrelid = 'campaigns'::regclass
    ) THEN
        ALTER TABLE campaigns ADD CONSTRAINT valid_stage 
            CHECK (stage IN ('lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost'));
    END IF;
END$$;

-- Add index on stage if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = 'idx_campaigns_stage' AND n.nspname = 'public'
    ) THEN
        CREATE INDEX idx_campaigns_stage ON campaigns(stage);
    END IF;
END$$;

COMMIT;
