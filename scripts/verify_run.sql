-- DELTA:20251113T114706Z Verification Script
-- Checks that all required objects exist after migration

-- 1. Verify matches table exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='matches'
  ) THEN
    RAISE EXCEPTION 'matches table does not exist';
  END IF;
END$$;

-- 2. Verify io_bookings.promo_code column exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='io_bookings' AND column_name='promo_code'
  ) THEN
    RAISE EXCEPTION 'io_bookings.promo_code column does not exist';
  END IF;
END$$;

-- 3. Verify io_bookings.vanity_url column exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='io_bookings' AND column_name='vanity_url'
  ) THEN
    RAISE EXCEPTION 'io_bookings.vanity_url column does not exist';
  END IF;
END$$;

-- 4. Verify ux_metrics_daily_day_ep_source index exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM   pg_class c
    JOIN   pg_namespace n ON n.oid = c.relnamespace
    WHERE  c.relkind='i'
    AND    c.relname='ux_metrics_daily_day_ep_source'
    AND    n.nspname='public'
  ) THEN
    RAISE EXCEPTION 'ux_metrics_daily_day_ep_source index does not exist';
  END IF;
END$$;

-- 5. Verify metrics_daily exists (table or materialized view)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class
    WHERE relname='metrics_daily'
    AND relkind IN ('r', 'm')  -- 'r' = table, 'm' = materialized view
  ) THEN
    RAISE EXCEPTION 'metrics_daily table/view does not exist';
  END IF;
END$$;

-- Success message
SELECT 'All verification checks passed!' as status;
