# Phase 3 — Safe DB Migration Pack
**RUN-ID:** 20251113T114706Z  
**Timestamp:** 2025-11-13T11:47:06Z UTC

## Migration Pack Created

### Location
`migrations/20251113T114706Z/`

### Files Created
1. `01_detect_and_add.sql` - Main migration (idempotent)
2. `02_policies.sql` - RLS policies (conditional)
3. `99_rollback.sql` - Rollback script
4. `README.md` - Migration documentation

### Helper Scripts Created
1. `scripts/db_migrate.sh` - Migration execution script
2. `scripts/db_rollback.sh` - Rollback execution script
3. `scripts/verify_run.sql` - Verification SQL

## What This Migration Does

### Additive Changes Only
1. **Matches Table:** Verifies exists, creates minimal version if missing
2. **IO Bookings Columns:** Verifies `promo_code` and `vanity_url` exist
3. **Metrics Daily Index:** Creates unique index `ux_metrics_daily_day_ep_source` if missing
4. **RLS Policies:** Adds policies on `matches` if RLS is enabled

### Safety Features
- All operations use `IF NOT EXISTS` / `DO $$ BEGIN ... END $$` patterns
- Idempotent (safe to run multiple times)
- Rollback script uses `IF EXISTS` guards
- No DROP/RENAME operations

## Schema Diff Summary

### Tables Verified/Created
- `matches` - Advertiser-podcast matchmaking scores

### Columns Verified/Added
- `io_bookings.promo_code` - Promo code for tracking
- `io_bookings.vanity_url` - Vanity URL for tracking

### Indexes Created
- `ux_metrics_daily_day_ep_source` - Unique index on `metrics_daily(day, episode_id, source)` (may include tenant_id)

### Policies Added (if RLS enabled)
- `org_select_matches` - SELECT policy
- `org_insert_matches` - INSERT policy
- `org_update_matches` - UPDATE policy
- `org_delete_matches` - DELETE policy

## Dry-Run Validation

Migration scripts parse correctly:
- ✅ SQL syntax validated
- ✅ Idempotent patterns confirmed
- ✅ Rollback guards in place

## Gate Status

✅ **PASS** - Migration pack is additive-only and idempotent.

**Next Steps:**
- Phase 4: Implement code deltas (sample files, event emission, etc.)
