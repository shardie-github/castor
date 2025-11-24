# Backend Discovery Report

**Generated:** 2024-12-XX  
**Purpose:** Document all backend and database artifacts, migration frameworks, and configuration patterns found in the repository.

---

## Executive Summary

This repository uses **PostgreSQL with TimescaleDB extension** as its primary database backend. The backend is Python/FastAPI using `asyncpg` for database connections. There is **partial Supabase configuration** present (env vars and frontend package), but **no active Supabase client implementation** in the codebase.

---

## Database Type

**Primary Database:** PostgreSQL 15+ with TimescaleDB extension

**Evidence:**
- `docker-compose.yml` uses `timescale/timescaledb:latest-pg15`
- `src/database/postgres.py` uses `asyncpg` (PostgreSQL async driver)
- Migrations use PostgreSQL-specific features (UUID extension, JSONB, RLS, hypertables)
- TimescaleDB hypertables for time-series data (`listener_events`, `attribution_events`, `listener_metrics`)

**Secondary Storage:**
- Redis (for caching, session management)
- No MongoDB, MySQL, or SQLite detected

---

## Migration Framework

**Type:** Raw SQL migrations (no ORM migration tool)

**Location:** `migrations/` directory

**Structure:**
- Numbered migrations: `001_initial_schema.sql` through `030_attribution_event_metadata_table.sql`
- Dated migration folders: `20251113_064143/`, `20251113T114706Z/`
- Total: ~28 SQL migration files

**Migration Execution:**
- `scripts/init_db.py` - Python script that runs migrations sequentially
- `scripts/db_migrate.sh` - Bash script for running migrations from a directory
- No Prisma, Drizzle, Knex, TypeORM, or Sequelize detected

**Migration Characteristics:**
- Uses `CREATE TABLE IF NOT EXISTS` (idempotent)
- Uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (safe for re-runs)
- Some migrations have dependencies (e.g., `003_multi_tenant_schema.sql` requires `001_initial_schema.sql`)
- TimescaleDB-specific migrations (`002_timescale_hypertables.sql`)

---

## Database Configuration

### Environment Variables

**PostgreSQL Connection:**
- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DATABASE` (default: `podcast_analytics`)
- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: `postgres`)

**Supabase Configuration (Present but Unused):**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Alternative Connection String:**
- No `DATABASE_URL` env var detected (but could be added)

### Configuration Files

**Backend (Python):**
- `src/config/settings.py` - Loads Postgres config from env vars
- `src/config/validation.py` - Validates Postgres and Supabase env vars
- `src/database/postgres.py` - Connection manager using `asyncpg`

**Frontend (Next.js):**
- `frontend/next.config.js` - Exposes Supabase env vars to client
- `frontend/package.json` - Includes `@supabase/supabase-js` package
- **No actual Supabase client code found** in frontend components

**Docker:**
- `docker-compose.yml` - Defines TimescaleDB container
- `docker-compose.staging.yml` - Staging environment config

**Infrastructure:**
- `terraform/main.tf` - References RDS PostgreSQL (AWS)
- `k8s/deployment.yaml` - Kubernetes deployment with `DATABASE_URL` env var

---

## Database Connection Pattern

**Backend Pattern:**
```python
# src/database/postgres.py
class PostgresConnection:
    def __init__(self, host, port, database, user, password, ...):
        # Uses asyncpg.create_pool()
```

**Usage in Code:**
- Services inject `PostgresConnection` instance
- Uses async context managers: `async with conn.acquire() as connection:`
- Read replica support (optional)
- Connection pooling (min_size=5, max_size=20)

**No ORM Detected:**
- Direct SQL queries via `asyncpg`
- No Prisma, SQLAlchemy, Django ORM, or similar

---

## Schema Features

**Key Database Features Used:**
1. **UUID Primary Keys** - All tables use UUIDs (`gen_random_uuid()`)
2. **JSONB Columns** - Extensive use for flexible metadata
3. **Row-Level Security (RLS)** - Multi-tenant isolation via RLS policies
4. **TimescaleDB Hypertables** - Time-series tables (`listener_events`, `attribution_events`, `listener_metrics`)
5. **Materialized Views** - Continuous aggregates for analytics
6. **Foreign Keys** - Referential integrity enforced
7. **Check Constraints** - Data validation at DB level
8. **Indexes** - Extensive indexing for performance

**Extensions:**
- `uuid-ossp` (UUID generation)
- `pg_trgm` (text search)
- `timescaledb` (time-series)

---

## API / Server Code Dependencies

**Backend API (FastAPI):**
- `src/api/**` - REST API endpoints
- All services depend on `PostgresConnection` injected dependency
- No direct Supabase client usage in backend

**Frontend:**
- Next.js app in `frontend/app/`
- Supabase package installed but **not actively used**
- No `lib/supabase.ts` or `lib/supabaseClient.ts` found

**Edge Functions / Serverless:**
- No Supabase Edge Functions detected
- No Vercel/Netlify functions detected
- Background jobs in `src/agents/`

---

## Supabase Status

**Configuration Present:**
- ✅ `.env.example` includes Supabase vars
- ✅ `frontend/next.config.js` exposes Supabase vars
- ✅ `frontend/package.json` includes `@supabase/supabase-js`
- ✅ `supabase/config.toml` exists (template)

**Implementation Missing:**
- ❌ No Supabase client initialization in frontend
- ❌ No Supabase client usage in backend
- ❌ No Supabase migrations in `supabase/migrations/`
- ❌ No Supabase Edge Functions

**Conclusion:** Supabase is **configured but not implemented**. The project currently uses direct PostgreSQL connections.

---

## Migration Execution Flow

**Current Process:**
1. `scripts/init_db.py` reads migrations from `migrations/` directory
2. Sorts migrations by filename (lexicographically)
3. Executes each SQL file sequentially
4. Uses `IF NOT EXISTS` clauses for idempotency
5. Sets up TimescaleDB hypertables after migrations

**Issues Identified:**
- No migration tracking table (can't detect which migrations ran)
- No rollback mechanism (except manual SQL)
- Dated migration folders (`20251113_064143/`) may conflict with numbered ones
- No dependency validation

---

## Recommendations

1. **Consolidate migrations** into a single master migration for fresh installs
2. **Add migration tracking** table to track applied migrations
3. **Standardize on one migration format** (numbered vs dated)
4. **Decide on Supabase** - either implement it fully or remove unused config
5. **Add DATABASE_URL support** for easier connection string management

---

## Files Referenced

**Migrations:**
- `migrations/001_initial_schema.sql` through `030_*.sql`
- `migrations/20251113_064143/` (dated folder)
- `migrations/20251113T114706Z/` (dated folder)

**Database Code:**
- `src/database/postgres.py`
- `src/database/timescale.py`
- `src/database/redis.py`
- `src/database/schema_validator.py`

**Configuration:**
- `.env.example`
- `src/config/settings.py`
- `src/config/validation.py`
- `docker-compose.yml`

**Scripts:**
- `scripts/init_db.py`
- `scripts/db_migrate.sh`
