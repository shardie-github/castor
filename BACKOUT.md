# Backout Plan
**RUN-ID:** 20251113T114706Z

## Overview

This document provides exact rollback snippets for every delta added in this extension. All rollback operations use `IF EXISTS` guards and are safe to run multiple times.

---

## Rollback Order (Safe Order)

### 1. Drop RLS Policies (if added)

```sql
BEGIN;

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

COMMIT;
```

### 2. Drop Index

```sql
BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE c.relkind='i' AND c.relname='ux_metrics_daily_day_ep_source' AND n.nspname='public'
  ) THEN
    DROP INDEX public.ux_metrics_daily_day_ep_source;
  END IF;
END$$;

COMMIT;
```

### 3. Drop Columns (ONLY if added by this migration)

**⚠️ WARNING:** Do NOT drop columns if they existed before this migration. This migration only adds columns if missing.

```sql
-- Only run if you're certain these columns were added by this migration
BEGIN;

DO $$
BEGIN
  -- Check if columns exist and were added by this migration
  -- Since we can't track this automatically, manual verification required
  
  -- If you're certain, uncomment:
  -- IF EXISTS (
  --   SELECT 1 FROM information_schema.columns
  --   WHERE table_schema='public' AND table_name='io_bookings' AND column_name='vanity_url'
  -- ) THEN
  --   ALTER TABLE public.io_bookings DROP COLUMN IF EXISTS vanity_url;
  -- END IF;
  
  -- IF EXISTS (
  --   SELECT 1 FROM information_schema.columns
  --   WHERE table_schema='public' AND table_name='io_bookings' AND column_name='promo_code'
  -- ) THEN
  --   ALTER TABLE public.io_bookings DROP COLUMN IF EXISTS promo_code;
  -- END IF;
END$$;

COMMIT;
```

**Recommendation:** Skip column drops unless you're certain they were added by this migration.

### 4. Drop Table (ONLY if created by this migration)

**⚠️ WARNING:** Do NOT drop `matches` table if it existed before this migration. This migration only creates a minimal version if missing.

```sql
-- Only run if you're certain the matches table was created by this migration
-- Since matches table likely existed before, DO NOT run this

-- BEGIN;
-- DROP TABLE IF EXISTS public.matches;
-- COMMIT;
```

**Recommendation:** Skip table drop. The `matches` table likely existed before this migration.

---

## Complete Rollback Script

The complete rollback script is available at:
- `migrations/20251113T114706Z/99_rollback.sql`

To execute:
```bash
PGURL="postgresql://..." ./scripts/db_rollback.sh migrations/20251113T114706Z
```

---

## Code Changes Rollback

### Remove IO Status Endpoint

If you need to remove the new `PATCH /api/v1/io/{io_id}/status` endpoint:

1. **Remove endpoint from `src/api/io.py`:**
   - Delete `UpdateIOStatusRequest` class
   - Delete `update_io_status` function

2. **Restart API server**

### Remove Feature Flags

If you need to remove feature flags from `.env.example`:

1. **Remove from `.env.example`:**
   ```bash
   # Remove these lines:
   ENABLE_ETL_CSV_UPLOAD=false
   ENABLE_MATCHMAKING=false
   ENABLE_IO_BOOKINGS=false
   ENABLE_DEAL_PIPELINE=false
   ENABLE_NEW_DASHBOARD_CARDS=false
   MATCHMAKING_ENABLED=false
   ```

2. **Unset environment variables** (if set)

---

## Verification After Rollback

After rollback, verify:

```sql
-- Check index dropped
SELECT 1 FROM pg_class WHERE relname='ux_metrics_daily_day_ep_source';
-- Should return 0 rows

-- Check policies dropped
SELECT 1 FROM pg_policies WHERE tablename='matches' AND policyname LIKE 'org_%';
-- Should return 0 rows (if policies were added)

-- Check columns still exist (if they existed before)
SELECT column_name FROM information_schema.columns 
WHERE table_name='io_bookings' AND column_name IN ('promo_code', 'vanity_url');
-- Should return rows if columns existed before migration
```

---

## Full Database Restore

If rollback fails or you need to restore entire database:

```bash
# Restore from backup taken before migration
psql "$PGURL" < backup_before_20251113T114706Z.sql
```

---

## Notes

- All rollback operations are **idempotent** (safe to run multiple times)
- Rollback uses `IF EXISTS` guards to prevent errors
- **Do NOT** drop tables/columns that existed before this migration
- When in doubt, restore from backup instead of dropping objects
