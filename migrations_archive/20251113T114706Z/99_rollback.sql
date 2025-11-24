-- DELTA:20251113T114706Z Rollback Script
-- Safe rollback with IF EXISTS guards

BEGIN;

-- Drop policies if present
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='matches' AND policyname='org_select_matches') THEN
    DROP POLICY org_select_matches ON public.matches;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='matches' AND policyname='org_insert_matches') THEN
    DROP POLICY org_insert_matches ON public.matches;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='matches' AND policyname='org_update_matches') THEN
    DROP POLICY org_update_matches ON public.matches;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='matches' AND policyname='org_delete_matches') THEN
    DROP POLICY org_delete_matches ON public.matches;
  END IF;
END$$;

-- Drop index if exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE c.relkind='i' AND c.relname='ux_metrics_daily_day_ep_source' AND n.nspname='public'
  ) THEN
    DROP INDEX public.ux_metrics_daily_day_ep_source;
  END IF;
END$$;

-- Drop added columns if exist (only if they were added by this migration)
-- Note: We don't drop columns that existed before, only ones we added
-- Since we can't track which columns we added vs existed, we'll skip column drops
-- to avoid breaking existing functionality

-- Drop matches table ONLY if it was created by this migration
-- Since matches may have existed before, we'll skip table drop for safety
-- If you need to drop matches table, do it manually after verifying it's safe

COMMIT;
