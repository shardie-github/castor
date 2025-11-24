# Backend Discovery Report

## Summary

This document summarizes the database and backend infrastructure discovered in the repository.

## Database Technology

**Primary Database**: PostgreSQL 15 with TimescaleDB extension

The project uses:
- **PostgreSQL** as the relational database
- **TimescaleDB** extension for time-series data (listener events, attribution events, metrics)
- **Redis** for caching and session management

## Migration Framework

**Migration System**: Raw SQL migrations

- Migrations are stored as numbered SQL files in `migrations/` directory
- Migrations are applied using `psql` (PostgreSQL command-line client) or via Python scripts using `asyncpg`
- No ORM migration framework detected (no Prisma, Drizzle, Alembic, etc.)
- Migrations use idempotent patterns (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`)

## Database Connection

**Connection Library**: `asyncpg` (async PostgreSQL driver for Python)

The application uses:
- `asyncpg` for all database operations
- Connection pooling via `asyncpg.create_pool()`
- Read replica support for query routing
- Custom connection managers in `src/database/postgres.py` and `src/database/timescale.py`

## Configuration

**Environment Variables** (from `.env.example`):

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=podcast_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

**Configuration Files**:
- `src/config/settings.py` - Pydantic settings model for database configuration
- `src/config/validation.py` - Database settings validation
- `docker-compose.yml` - Local development database setup

## Database Features Used

1. **Multi-Tenancy**: Row-Level Security (RLS) with tenant isolation
2. **Time-Series Data**: TimescaleDB hypertables for events and metrics
3. **Continuous Aggregates**: Materialized views with automatic refresh policies
4. **Extensions**: 
   - `uuid-ossp` - UUID generation
   - `pg_trgm` - Trigram matching for text search
   - `pgcrypto` - Cryptographic functions
   - `timescaledb` - Time-series database extension
5. **Custom Functions**: 
   - `set_tenant_context()` - Sets tenant context for RLS
   - `refresh_metrics_daily()` - Refreshes materialized views

## API/Server Code

**Backend Framework**: FastAPI (Python)

- API routes in `src/api/`
- Services in `src/services/`, `src/business/`, `src/campaigns/`, etc.
- Database connections injected via dependency injection
- All database operations use raw SQL queries with `asyncpg`

## Frontend Database Access

**Frontend**: Next.js

- Uses `@supabase/supabase-js` package (detected in `frontend/`)
- However, no active Supabase client implementation found
- Frontend likely communicates with backend API rather than directly accessing database

## Infrastructure

**Local Development**: Docker Compose
- `docker-compose.yml` defines PostgreSQL (TimescaleDB) and Redis services
- Uses `timescale/timescaledb:latest-pg15` image

**Production Deployment**: 
- Kubernetes configuration in `k8s/deployment.yaml`
- Terraform configuration in `terraform/main.tf` (mentions AWS RDS PostgreSQL)

## Migration Files Location

- **Original migrations**: `migrations/` (now archived in `migrations_archive/`)
- **Master migration**: `db/migrations/99999999999999_master_schema.sql`

## Key Findings

1. **No ORM**: The project uses raw SQL with `asyncpg`, providing full control but requiring manual schema management
2. **TimescaleDB Required**: The schema heavily relies on TimescaleDB features (hypertables, continuous aggregates)
3. **Multi-Tenant Architecture**: RLS policies enforce tenant isolation at the database level
4. **Supabase Configuration Present**: `.env.example` includes Supabase variables, but backend code doesn't use Supabase client libraries
5. **Migration Strategy**: Migrations are consolidated into a single master migration file for fresh database setups

## Recommendations

1. **Standardize Database URL**: Consider using `DATABASE_URL` environment variable (PostgreSQL connection string format) for easier switching between providers
2. **Migration Tooling**: Consider adding a migration runner script that handles idempotent execution
3. **Supabase Integration**: If Supabase is chosen, update backend code to use Supabase client libraries or ensure direct PostgreSQL connection works with Supabase's managed Postgres
