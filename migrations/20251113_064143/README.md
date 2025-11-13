# Migration Pack: 20251113_064143

**RUN-ID**: `20251113_064143`  
**Created**: 2025-11-13T06:41:43Z

## Overview

This migration pack adds the following **additive-only** changes:

1. **ETL Imports Table** - Track CSV/Google Sheets imports
2. **Ad Units Table** - Define ad unit types (pre/mid/post-roll)
3. **IO Bookings Table** - Insertion orders with flight dates, promo codes, vanity URLs
4. **Matches Table** - Advertiser-podcast matchmaking scores
5. **Campaigns Extension** - Add `stage` and `stage_changed_at` columns for deal pipeline

## Preconditions

- PostgreSQL 15+ with TimescaleDB extension
- UUID extension enabled (`uuid-ossp`)
- `tenants` table exists (from migration 003)
- `campaigns`, `podcasts`, `episodes`, `sponsors` tables exist (from migration 001)

## Run Steps

### 1. Backup Database
```bash
pg_dump -U postgres -d podcast_analytics > backup_before_20251113_064143.sql
```

### 2. Run Migrations in Order

```bash
# Connect to database
psql -U postgres -d podcast_analytics

# Run migrations
\i migrations/20251113_064143/01_detect_and_add.sql
\i migrations/20251113_064143/02_policies.sql
```

Or via Python:
```python
import asyncpg
import asyncio

async def run_migrations():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        database='podcast_analytics'
    )
    
    with open('migrations/20251113_064143/01_detect_and_add.sql', 'r') as f:
        await conn.execute(f.read())
    
    with open('migrations/20251113_064143/02_policies.sql', 'r') as f:
        await conn.execute(f.read())
    
    await conn.close()

asyncio.run(run_migrations())
```

### 3. Verify Migration

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('etl_imports', 'ad_units', 'io_bookings', 'matches');

-- Check campaigns.stage column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'campaigns' AND column_name IN ('stage', 'stage_changed_at');

-- Check RLS policies
SELECT tablename, policyname FROM pg_policies 
WHERE tablename IN ('etl_imports', 'ad_units', 'io_bookings', 'matches');
```

## Rollback

### Rollback Script

```sql
BEGIN;

-- Drop RLS policies
DROP POLICY IF EXISTS tenant_isolation_matches ON matches;
DROP POLICY IF EXISTS tenant_isolation_io_bookings ON io_bookings;
DROP POLICY IF EXISTS tenant_isolation_ad_units ON ad_units;
DROP POLICY IF EXISTS tenant_isolation_etl_imports ON etl_imports;

-- Drop tables (in reverse order due to FKs)
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS io_bookings;
DROP TABLE IF EXISTS ad_units;
DROP TABLE IF EXISTS etl_imports;

-- Remove columns from campaigns (if added)
ALTER TABLE campaigns DROP COLUMN IF EXISTS stage_changed_at;
ALTER TABLE campaigns DROP COLUMN IF EXISTS stage;

-- Drop constraints
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS valid_stage;

-- Drop indexes
DROP INDEX IF EXISTS idx_campaigns_stage;
DROP INDEX IF EXISTS idx_matches_score;
DROP INDEX IF EXISTS idx_matches_podcast_id;
DROP INDEX IF EXISTS idx_matches_advertiser_id;
DROP INDEX IF EXISTS idx_matches_tenant_id;
DROP INDEX IF EXISTS idx_io_bookings_status;
DROP INDEX IF EXISTS idx_io_bookings_flight;
DROP INDEX IF EXISTS idx_io_bookings_episode_id;
DROP INDEX IF EXISTS idx_io_bookings_campaign_id;
DROP INDEX IF EXISTS idx_io_bookings_tenant_id;
DROP INDEX IF EXISTS idx_ad_units_podcast_id;
DROP INDEX IF EXISTS idx_ad_units_tenant_id;
DROP INDEX IF EXISTS idx_etl_imports_started_at;
DROP INDEX IF EXISTS idx_etl_imports_status;
DROP INDEX IF EXISTS idx_etl_imports_tenant_id;

COMMIT;
```

### Rollback via Backup

```bash
# Restore from backup
psql -U postgres -d podcast_analytics < backup_before_20251113_064143.sql
```

## Idempotency

All migrations are **idempotent**:
- `CREATE TABLE IF NOT EXISTS` - Safe to run multiple times
- `ADD COLUMN IF NOT EXISTS` - Safe to run multiple times
- Index creation checks existence before creating
- Policy creation checks existence before creating

## Feature Flags

These migrations support features behind flags:
- `ENABLE_ETL_CSV_UPLOAD` - Controls ETL import functionality
- `ENABLE_DEAL_PIPELINE` - Controls deal pipeline stages
- `ENABLE_IO_BOOKINGS` - Controls IO booking functionality
- `ENABLE_MATCHMAKING` - Controls matchmaking functionality

## Notes

- All new tables include `tenant_id` for multi-tenant isolation
- All new tables have RLS enabled with tenant isolation policies
- All foreign keys use `ON DELETE CASCADE` or `ON DELETE SET NULL` as appropriate
- All timestamps use `TIMESTAMP WITH TIME ZONE`
- All tables include `metadata JSONB` for extensibility

## Schema Changes Summary

### New Tables
- `etl_imports` - 1 table
- `ad_units` - 1 table
- `io_bookings` - 1 table
- `matches` - 1 table
- **Total**: 4 new tables

### Modified Tables
- `campaigns` - Added 2 columns (`stage`, `stage_changed_at`)

### New Indexes
- 15 new indexes across new tables

### New Policies
- 4 new RLS policies
