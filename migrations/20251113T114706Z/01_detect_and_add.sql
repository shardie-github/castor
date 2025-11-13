-- DELTA:20251113T114706Z Safe DB Migration Pack - Additive Only
-- Verifies existing objects and adds only missing pieces

BEGIN;

-- Enable extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- 1. MATCHES TABLE (verify exists, create if missing)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.matches(
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  advertiser_id uuid NOT NULL,
  podcast_id uuid NOT NULL,
  score numeric NOT NULL,
  rationale text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Note: If matches table already exists from previous migration with different structure,
-- we preserve existing structure. This is a fallback for minimal matches table.

-- Check if matches table has tenant_id (from previous migration)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='tenant_id'
  ) THEN
    -- Add tenant_id if missing (for multi-tenant support)
    ALTER TABLE public.matches ADD COLUMN tenant_id uuid;
  END IF;
  
  -- Add advertiser_id if missing (may be named differently)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='advertiser_id'
  ) THEN
    -- Check if it's named sponsor_id instead
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='matches' AND column_name='sponsor_id'
    ) THEN
      -- Rename sponsor_id to advertiser_id (if safe)
      -- Actually, we'll keep both for compatibility - no rename
      NULL;
    ELSE
      ALTER TABLE public.matches ADD COLUMN advertiser_id uuid;
    END IF;
  END IF;
  
  -- Add score if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='score'
  ) THEN
    ALTER TABLE public.matches ADD COLUMN score numeric;
  END IF;
  
  -- Add rationale if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='rationale'
  ) THEN
    ALTER TABLE public.matches ADD COLUMN rationale text;
  END IF;
  
  -- Add signals if missing (from previous migration)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='signals'
  ) THEN
    ALTER TABLE public.matches ADD COLUMN signals jsonb DEFAULT '{}';
  END IF;
  
  -- Add updated_at if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='matches' AND column_name='updated_at'
  ) THEN
    ALTER TABLE public.matches ADD COLUMN updated_at timestamptz DEFAULT now();
  END IF;
END$$;

-- ============================================================================
-- 2. IO_BOOKINGS COLUMNS (verify promo_code and vanity_url exist)
-- ============================================================================

-- promo_code column on io_bookings (if missing)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='io_bookings' AND column_name='promo_code'
  ) THEN
    ALTER TABLE public.io_bookings ADD COLUMN promo_code text;
  END IF;
END$$;

-- vanity_url column on io_bookings (if missing)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='io_bookings' AND column_name='vanity_url'
  ) THEN
    ALTER TABLE public.io_bookings ADD COLUMN vanity_url text;
  END IF;
END$$;

-- ============================================================================
-- 3. METRICS_DAILY UNIQUE INDEX (verify/create)
-- ============================================================================

-- Check if metrics_daily is a table or view
DO $$
DECLARE
  v_table_type text;
BEGIN
  SELECT CASE 
    WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname='metrics_daily' AND relkind='m') THEN 'materialized_view'
    WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname='metrics_daily' AND relkind='r') THEN 'table'
    ELSE 'not_found'
  END INTO v_table_type;
  
  -- If it's a materialized view, create unique index if missing
  IF v_table_type = 'materialized_view' THEN
    -- Check if unique index exists
    IF NOT EXISTS (
      SELECT 1
      FROM   pg_class c
      JOIN   pg_namespace n ON n.oid = c.relnamespace
      WHERE  c.relkind='i'
      AND    c.relname='ux_metrics_daily_day_ep_source'
      AND    n.nspname='public'
    ) THEN
      -- Check if tenant_id column exists (for multi-tenant)
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='metrics_daily' AND column_name='tenant_id'
      ) THEN
        CREATE UNIQUE INDEX ux_metrics_daily_day_ep_source
        ON public.metrics_daily(day, episode_id, source, tenant_id);
      ELSE
        CREATE UNIQUE INDEX ux_metrics_daily_day_ep_source
        ON public.metrics_daily(day, episode_id, source);
      END IF;
    END IF;
  END IF;
  
  -- If it's a table (not view), also create index
  IF v_table_type = 'table' THEN
    IF NOT EXISTS (
      SELECT 1
      FROM   pg_class c
      JOIN   pg_namespace n ON n.oid = c.relnamespace
      WHERE  c.relkind='i'
      AND    c.relname='ux_metrics_daily_day_ep_source'
      AND    n.nspname='public'
    ) THEN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='metrics_daily' AND column_name='tenant_id'
      ) THEN
        CREATE UNIQUE INDEX ux_metrics_daily_day_ep_source
        ON public.metrics_daily(day, episode_id, source, tenant_id);
      ELSE
        CREATE UNIQUE INDEX ux_metrics_daily_day_ep_source
        ON public.metrics_daily(day, episode_id, source);
      END IF;
    END IF;
  END IF;
END$$;

COMMIT;
