# Migration Pack 20251113T114706Z
**RUN-ID:** 20251113T114706Z  
**Additive-only, idempotent. No drops/renames beyond guarded rollback.**

## Overview

This migration pack verifies existing objects and adds only missing pieces:
- Verifies `matches` table exists (creates minimal version if missing)
- Verifies `io_bookings.promo_code` and `io_bookings.vanity_url` columns exist
- Creates unique index `ux_metrics_daily_day_ep_source` on `metrics_daily` if missing
- Adds RLS policies if RLS is enabled in the project

## Files

1. `01_detect_and_add.sql` - Main migration (idempotent)
2. `02_policies.sql` - RLS policies (only if RLS is used)
3. `99_rollback.sql` - Rollback script (guarded)

## Usage

### Run Migration

```bash
PGURL="postgresql://user:pass@host:5432/db?sslmode=require" ./scripts/db_migrate.sh migrations/20251113T114706Z
```

### Dry Run

```bash
PGURL="..." ./scripts/db_migrate.sh migrations/20251113T114706Z --dry-run
```

### Rollback

```bash
PGURL="..." ./scripts/db_rollback.sh migrations/20251113T114706Z
```

## Notes

- If your project does not use RLS, `02_policies.sql` will safely skip policy creation
- All migrations are idempotent (safe to run multiple times)
- Rollback script uses `IF EXISTS` guards for safety
- This migration pack does NOT drop existing tables/columns (additive only)

## What This Migration Does

### Creates/Verifies:
- `matches` table (if missing)
- `io_bookings.promo_code` column (if missing)
- `io_bookings.vanity_url` column (if missing)
- `ux_metrics_daily_day_ep_source` unique index (if missing)
- RLS policies on `matches` (if RLS is enabled)

### Does NOT:
- Drop any existing tables
- Rename any columns
- Modify existing data
- Break existing functionality

## Verification

After running migration, verify with:

```bash
PGURL="..." psql -f scripts/verify_run.sql
```
