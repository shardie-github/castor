# Changelog

## [20251113T114706Z] - 2025-11-13

### Added

#### Database Schema
- **Migration Pack:** `migrations/20251113T114706Z/`
  - `01_detect_and_add.sql` - Verifies existing objects, adds missing pieces
  - `02_policies.sql` - RLS policies (conditional)
  - `99_rollback.sql` - Rollback script
  - `README.md` - Migration documentation

#### Tables/Columns
- Verified `matches` table exists (creates minimal version if missing)
- Verified `io_bookings.promo_code` column exists (adds if missing)
- Verified `io_bookings.vanity_url` column exists (adds if missing)

#### Indexes
- `ux_metrics_daily_day_ep_source` - Unique index on `metrics_daily(day, episode_id, source)` (may include tenant_id)

#### API Endpoints
- `PATCH /api/v1/io/{io_id}/status` - Update IO booking status
  - Emits `io.delivered` event when status changes to 'completed'
  - Emits `io.status_changed` event for other status changes

#### Events
- `io.delivered` - Emitted when IO status changes to 'completed'
- `io.status_changed` - Emitted when IO status changes (generic)

#### Scripts
- `scripts/db_migrate.sh` - Migration execution script
- `scripts/db_rollback.sh` - Rollback execution script
- `scripts/verify_run.sql` - Verification SQL script

#### Sample Files
- `samples/metrics_daily.csv` - Sample metrics data
- `samples/io_bookings.csv` - Sample IO booking data

#### Documentation
- `docs/sheets/push_metrics_daily.gs` - Google Sheets Apps Script for sync
- `docs/run-logs/20251113T114706Z_*.md` - Run logs for this extension

#### Environment Variables
- `ENABLE_ETL_CSV_UPLOAD` - Enable CSV upload feature
- `ENABLE_MATCHMAKING` - Enable matchmaking feature (existing)
- `ENABLE_IO_BOOKINGS` - Enable IO bookings feature
- `ENABLE_DEAL_PIPELINE` - Enable deal pipeline feature
- `ENABLE_NEW_DASHBOARD_CARDS` - Enable new dashboard cards
- `MATCHMAKING_ENABLED` - Alias for matchmaking (documented, existing flag is `ENABLE_MATCHMAKING`)

### Changed

#### Files Modified
- `src/api/io.py` - Added status update endpoint with event emission
- `.env.example` - Added feature flags section

### Notes

- All changes are **additive-only** (no destructive operations)
- Migrations are **idempotent** (safe to run multiple times)
- Feature flags default to `false` (opt-in)
- Existing functionality remains unchanged
