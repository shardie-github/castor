# Database Migrations & Schema Documentation

**Last Updated:** 2024-12  
**Purpose:** Complete guide to database migrations, schema management, and validation

---

## Overview

This repository uses **SQL-based migrations** with a **master schema approach**. All migrations are consolidated into a single, idempotent migration file that can bootstrap a fresh database from zero to the complete schema.

---

## Migration Strategy

### Approach: Master Schema Migration

- **File:** `db/migrations/99999999999999_master_schema.sql`
- **Type:** Idempotent SQL migration
- **Philosophy:** Single source of truth for database schema
- **Safety:** All operations use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, etc.

### Why This Approach?

1. **Simplicity:** One file to rule them all
2. **Idempotency:** Safe to run multiple times
3. **Fresh Installs:** Easy to bootstrap new databases
4. **No Migration History:** No need to track migration versions

### Trade-offs

**Pros:**
- ✅ Simple to understand and maintain
- ✅ Easy to bootstrap fresh databases
- ✅ No migration version conflicts
- ✅ Easy to review entire schema

**Cons:**
- ⚠️ Harder to track incremental changes
- ⚠️ No rollback to specific versions
- ⚠️ Requires manual schema diffing for changes

---

## Migration Files

### Active Migration

**File:** `db/migrations/99999999999999_master_schema.sql`

**Contents:**
- All table definitions
- All indexes
- All constraints
- All TimescaleDB hypertables
- All extensions (uuid-ossp, pg_trgm, pgcrypto, timescaledb)

**Size:** ~1400+ lines

**Key Tables:**
- `tenants` - Multi-tenancy foundation
- `users` - User accounts
- `podcasts` - Podcast metadata
- `episodes` - Episode metadata
- `campaigns` - Campaign tracking
- `listener_events` - Time-series listener data (TimescaleDB hypertable)
- `attribution_events` - Attribution tracking (TimescaleDB hypertable)
- `sponsors` - Sponsor information
- `deals` - Deal pipeline (if enabled)
- And many more...

### Archived Migrations

**Directory:** `migrations_archive/`

**Contents:**
- Historical migration files (001-030)
- Dated migration folders (20251113_064143, 20251113T114706Z)
- Legacy schema changes

**Status:** Archived for reference only, not used in production

---

## Migration Scripts

### Production/Hosted Migration

**Script:** `scripts/db-migrate-hosted.sh`

**Usage:**
```bash
# Using DATABASE_URL
DATABASE_URL=postgresql://user:pass@host:5432/db ./scripts/db-migrate-hosted.sh

# Using individual variables
POSTGRES_HOST=host POSTGRES_USER=user POSTGRES_PASSWORD=pass POSTGRES_DATABASE=db ./scripts/db-migrate-hosted.sh
```

**Features:**
- ✅ Connection string validation
- ✅ PostgreSQL version check
- ✅ TimescaleDB extension check
- ✅ Safety confirmations (can be skipped with `SKIP_CONFIRMATION=true`)
- ✅ Migration verification
- ✅ Key table validation

**CI Integration:** Used in `.github/workflows/db-migrate.yml`

### Local Development Migration

**Script:** `scripts/db-migrate-local.sh`

**Usage:**
```bash
./scripts/db-migrate-local.sh
```

**Features:**
- Uses Docker Compose database
- Simplified for local development
- Less safety checks (assumes local dev)

---

## Schema Structure

### Core Tables

#### Multi-Tenancy
- `tenants` - Tenant/organization records
- `tenant_settings` - Tenant-specific settings (JSONB)
- `tenant_quotas` - Tenant resource limits

#### Users & Authentication
- `users` - User accounts
- `user_email_preferences` - Email preferences
- `user_metrics` - User-level metrics

#### Content
- `podcasts` - Podcast metadata
- `episodes` - Episode metadata
- `sponsors` - Sponsor information

#### Campaigns & Attribution
- `campaigns` - Campaign tracking
- `attribution_events` - Attribution events (TimescaleDB hypertable)
- `listener_events` - Listener behavior events (TimescaleDB hypertable)

#### Business Logic
- `deals` - Deal pipeline (feature-flagged)
- `partnerships` - Partnership records
- `referrals` - Referral program data

### TimescaleDB Hypertables

**Extension:** TimescaleDB (PostgreSQL extension for time-series data)

**Hypertables:**
- `listener_events` - Listener behavior tracking
- `attribution_events` - Attribution event tracking
- `metrics_daily` - Daily aggregated metrics (continuous aggregate)

**Benefits:**
- ✅ Automatic partitioning by time
- ✅ Optimized queries for time-series data
- ✅ Continuous aggregates for fast analytics
- ✅ Automatic data retention policies

**Requirements:**
- TimescaleDB extension must be enabled on database
- For Supabase: Contact support to enable TimescaleDB
- For AWS RDS: Enable via parameter groups

### Indexes

**Strategy:** Indexes created for:
- Foreign keys
- Frequently queried columns
- Time-series queries (TimescaleDB automatic indexes)
- Full-text search (pg_trgm extension)

**Key Indexes:**
- `idx_users_tenant_id` - Tenant isolation
- `idx_users_email` - Email lookups
- `idx_listener_events_timestamp` - Time-series queries
- `idx_attribution_events_campaign_id` - Campaign attribution

---

## Schema Validation

### Validation Scripts

**Script:** `scripts/check_schema_health.py`

**Purpose:** Validates database schema matches expectations

**Checks:**
- ✅ Core tables exist
- ✅ Required columns present
- ✅ Indexes exist
- ✅ Foreign keys valid
- ✅ TimescaleDB hypertables configured

**Usage:**
```bash
python scripts/check_schema_health.py --database-url $DATABASE_URL
```

### CI Integration

**Workflow:** `.github/workflows/db-migrate.yml`

**Steps:**
1. Validate migration files (`validate-migrations` job)
2. Apply migrations (`migrate-staging` or `migrate-production` job)
3. Verify migration (`verify migration` step)

**Verification Query:**
```sql
SELECT 
  COUNT(*) as table_count,
  COUNT(CASE WHEN table_name IN ('tenants', 'users', 'podcasts', 'episodes', 'campaigns', 'listener_events') THEN 1 END) as key_tables
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

---

## Making Schema Changes

### Process

1. **Edit Master Schema:**
   - Open `db/migrations/99999999999999_master_schema.sql`
   - Add/modify table definitions (use `IF NOT EXISTS` for safety)
   - Test locally with `scripts/db-migrate-local.sh`

2. **Test Migration:**
   - Run migration against test database
   - Verify schema changes
   - Run validation script

3. **Commit Changes:**
   - Commit updated migration file
   - PR will trigger migration validation workflow

4. **Deploy:**
   - Merge PR triggers staging migration
   - Manual production migration via workflow dispatch

### Best Practices

1. **Always Use IF NOT EXISTS:**
   ```sql
   CREATE TABLE IF NOT EXISTS new_table (...);
   CREATE INDEX IF NOT EXISTS idx_new_table_column ON new_table(column);
   ```

2. **Test Locally First:**
   ```bash
   # Start local database
   docker-compose up -d postgres
   
   # Run migration
   ./scripts/db-migrate-local.sh
   
   # Verify
   psql postgresql://postgres:postgres@localhost:5432/podcast_analytics -c "\dt"
   ```

3. **Document Changes:**
   - Add comments in migration file
   - Update this documentation
   - Document breaking changes

4. **Backup Before Production:**
   - Always backup production database before migrations
   - Test migration on staging first
   - Have rollback plan ready

---

## Migration Workflow

### Development

1. Make schema changes in `db/migrations/99999999999999_master_schema.sql`
2. Test locally: `./scripts/db-migrate-local.sh`
3. Commit and push

### CI/CD

1. **PR Created:**
   - Migration validation workflow runs (`test-migrations.yml`)
   - Validates migration syntax

2. **PR Merged to Main:**
   - `db-migrate.yml` workflow triggers
   - Applies migrations to staging database
   - Verifies migration success

3. **Production Deployment:**
   - Manual trigger via workflow dispatch
   - Applies migrations to production database
   - Verifies migration success

### Rollback Strategy

**Current Approach:** No automatic rollback (master schema is additive)

**Manual Rollback:**
1. Restore from backup
2. Or manually drop/modify tables
3. Document rollback steps

**Future Improvement:** Consider adding rollback scripts for critical changes

---

## Database Connection

### Connection Configuration

**Backend:** `src/database/postgres.py`

**Connection Pool:**
- Primary pool: Read/write operations
- Read replica pool: Read-only operations (optional)

**Configuration:**
- `DATABASE_URL` (recommended) or individual `POSTGRES_*` variables
- Connection pooling: min_size=5, max_size=20
- Read replica support (optional)

### Environment Variables

**Required:**
- `DATABASE_URL` OR (`POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE`)

**Optional:**
- `POSTGRES_READ_REPLICA_HOST` - Read replica host
- `POSTGRES_READ_REPLICA_PORT` - Read replica port

---

## Troubleshooting

### Migration Fails

**Symptoms:** Migration script exits with error

**Solutions:**
1. Check database connection: `psql $DATABASE_URL -c "SELECT 1;"`
2. Check PostgreSQL version: Must be 15+ for TimescaleDB
3. Check TimescaleDB extension: `SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';`
4. Review migration log: `/tmp/migration_output.log`
5. Check for existing tables: May conflict with `IF NOT EXISTS`

### TimescaleDB Not Available

**Symptoms:** Warning about TimescaleDB extension

**Solutions:**
- **Supabase:** Contact support to enable TimescaleDB extension
- **AWS RDS:** Enable via parameter groups
- **Self-hosted:** Install TimescaleDB extension

### Schema Drift

**Symptoms:** Database schema doesn't match code expectations

**Solutions:**
1. Run validation script: `python scripts/check_schema_health.py`
2. Compare schema: Use `pg_dump` to export schema
3. Re-run migration: Migration is idempotent, safe to re-run

---

## Future Improvements

### Potential Enhancements

1. **Migration Versioning:**
   - Track migration versions in database
   - Enable rollback to specific versions
   - Track migration history

2. **Incremental Migrations:**
   - Create incremental migration files
   - Merge into master schema periodically
   - Better change tracking

3. **Automated Testing:**
   - Test migrations against multiple PostgreSQL versions
   - Test rollback procedures
   - Test migration performance

4. **Schema Diff Tool:**
   - Compare database schema to migration file
   - Detect schema drift automatically
   - Generate migration files from schema changes

---

## Resources

### Documentation
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Scripts
- `scripts/db-migrate-hosted.sh` - Production migrations
- `scripts/db-migrate-local.sh` - Local development migrations
- `scripts/check_schema_health.py` - Schema validation
- `scripts/check_schema_drift.py` - Schema drift detection

### CI/CD
- `.github/workflows/db-migrate.yml` - Migration workflow
- `.github/workflows/test-migrations.yml` - Migration testing

---

**Documentation Generated By:** Unified Background Agent  
**Last Updated:** 2024-12
