# Database Migrations Workflow

This document describes how to manage database migrations for this project.

## Migration Strategy

This project uses a **single master migration** approach:

- **Master Migration**: `db/migrations/99999999999999_master_schema.sql`
  - Consolidates all schema changes into one idempotent file
  - Safe to run multiple times (uses `IF NOT EXISTS` clauses)
  - Bootstraps a fresh database from zero to complete schema

- **Legacy Migrations**: Archived in `migrations_archive/`
  - Preserved for historical reference
  - **Do not apply these directly** to fresh databases
  - Use the master migration instead

## Prerequisites

### Required Tools

1. **PostgreSQL Client** (`psql`)
   - macOS: `brew install postgresql`
   - Ubuntu/Debian: `sudo apt-get install postgresql-client`
   - Windows: Download from [PostgreSQL website](https://www.postgresql.org/download/)

2. **PostgreSQL Database**
   - Local: Use Docker Compose (`docker-compose up postgres`)
   - Hosted: Supabase, AWS RDS, DigitalOcean, etc.

3. **TimescaleDB Extension** (Recommended)
   - Required for time-series features (hypertables, continuous aggregates)
   - Local: Included in `timescale/timescaledb` Docker image
   - Hosted: Verify provider support (Supabase may require request)

## Local Development Workflow

### 1. Start Local Database

```bash
# Start PostgreSQL with TimescaleDB using Docker Compose
docker-compose up -d postgres

# Wait for database to be ready (usually 10-30 seconds)
docker-compose ps postgres
```

### 2. Apply Migration

```bash
# Option 1: Use the migration script (recommended)
./scripts/db-migrate-local.sh

# Option 2: Use DATABASE_URL environment variable
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics \
  ./scripts/db-migrate-local.sh

# Option 3: Manual psql command
psql postgresql://postgres:postgres@localhost:5432/podcast_analytics \
  -f db/migrations/99999999999999_master_schema.sql
```

### 3. Verify Migration

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/podcast_analytics

# Check tables
\dt

# Check for key tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tenants', 'users', 'podcasts', 'episodes', 'campaigns');

# Check TimescaleDB hypertables (if extension is enabled)
SELECT hypertable_name FROM timescaledb_information.hypertables;
```

### 4. Reset Database (if needed)

```bash
# Drop and recreate database
psql postgresql://postgres:postgres@localhost:5432/postgres -c \
  "DROP DATABASE IF EXISTS podcast_analytics;"
psql postgresql://postgres:postgres@localhost:5432/postgres -c \
  "CREATE DATABASE podcast_analytics;"

# Reapply migration
./scripts/db-migrate-local.sh
```

## Hosted/Production Workflow

### 1. Prepare Database Connection

Set up your database connection string:

```bash
# Option 1: Use DATABASE_URL (recommended)
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Option 2: Use individual variables
export POSTGRES_HOST="your-host.com"
export POSTGRES_USER="your-user"
export POSTGRES_PASSWORD="your-password"
export POSTGRES_DATABASE="your-database"
export POSTGRES_PORT="5432"
```

### 2. Create Backup

**Always create a backup before applying migrations to production:**

```bash
# Using pg_dump
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use your provider's backup feature:
# - Supabase: Dashboard → Database → Backups
# - AWS RDS: Automated backups or manual snapshot
# - DigitalOcean: Create snapshot from dashboard
```

### 3. Apply Migration

```bash
# Use the hosted migration script (includes safety checks)
./scripts/db-migrate-hosted.sh

# Skip confirmation prompts (for CI/CD)
SKIP_CONFIRMATION=true ./scripts/db-migrate-hosted.sh
```

### 4. Verify Migration

```bash
# Connect to database
psql "$DATABASE_URL"

# Verify tables and schema
\dt
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

# Test tenant isolation (if RLS is enabled)
SELECT set_tenant_context('00000000-0000-0000-0000-000000000000'::UUID);
SELECT * FROM users LIMIT 1;
```

## Supabase-Specific Workflow

### 1. Get Connection String

1. Go to Supabase Dashboard → Project Settings → Database
2. Copy the connection string (use "Connection pooling" for serverless, "Direct connection" for migrations)
3. Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

### 2. Enable TimescaleDB Extension

**Important**: Supabase may require enabling TimescaleDB extension manually.

1. Go to Supabase Dashboard → Database → Extensions
2. Search for "timescaledb"
3. Enable the extension
4. Or run: `CREATE EXTENSION IF NOT EXISTS timescaledb;`

### 3. Apply Migration

```bash
# Set connection string
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Apply migration
./scripts/db-migrate-hosted.sh
```

### 4. Verify in Supabase Dashboard

1. Go to Database → Tables
2. Verify all tables are created
3. Check Database → Extensions for TimescaleDB
4. Test queries in SQL Editor

## AWS RDS Workflow

### 1. Enable TimescaleDB Extension

1. Go to RDS Console → Parameter Groups
2. Create or modify parameter group
3. Set `shared_preload_libraries` to include `timescaledb`
4. Apply parameter group to RDS instance
5. Restart RDS instance

### 2. Apply Migration

```bash
# Set connection string
export DATABASE_URL="postgresql://user:password@your-rds-endpoint:5432/database"

# Apply migration
./scripts/db-migrate-hosted.sh
```

## Troubleshooting

### Error: "extension timescaledb does not exist"

**Solution**: Enable TimescaleDB extension manually:

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

If extension is not available, contact your database provider to enable it.

### Error: "relation already exists"

**Solution**: This is normal - the migration is idempotent. The `IF NOT EXISTS` clauses prevent errors. If you see this error, it means the table already exists and was skipped.

### Error: "permission denied"

**Solution**: Ensure your database user has sufficient permissions:

```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO your_user;
```

### Error: "cannot connect to database"

**Solution**: Check your connection string and network access:

1. Verify `DATABASE_URL` or `POSTGRES_*` environment variables
2. Check firewall rules (hosted databases)
3. Verify database is running (local)
4. Test connection: `psql "$DATABASE_URL" -c "SELECT 1;"`

### Migration Takes Too Long

**Solution**: Large migrations may take time. Monitor progress:

```bash
# In another terminal, monitor database activity
psql "$DATABASE_URL" -c "SELECT pid, state, query FROM pg_stat_activity WHERE query LIKE '%CREATE%';"
```

### Rollback

**Note**: The master migration is designed for fresh databases. For rollbacks:

1. Restore from backup (recommended)
2. Or manually drop tables/columns if needed
3. Reapply migration after fixing issues

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Database Migration

on:
  push:
    branches: [main]
    paths:
      - 'db/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install PostgreSQL client
        run: |
          sudo apt-get update
          sudo apt-get install -y postgresql-client
      
      - name: Run migration
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          SKIP_CONFIRMATION=true ./scripts/db-migrate-hosted.sh
```

### Environment Variables

Set these in your CI/CD platform:

- `DATABASE_URL`: Full PostgreSQL connection string (recommended)
- Or individual variables: `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE`, `POSTGRES_PORT`

## Best Practices

1. **Always Backup**: Create backups before applying migrations to production
2. **Test Locally First**: Test migrations on local/staging before production
3. **Idempotent Migrations**: The master migration is idempotent - safe to run multiple times
4. **Monitor**: Watch migration progress and verify results
5. **Document Changes**: If modifying the master migration, document what changed and why
6. **Version Control**: Keep migration files in version control
7. **Review**: Have another developer review migration changes before production

## Modifying the Schema

If you need to modify the database schema:

1. **Edit the master migration**: `db/migrations/99999999999999_master_schema.sql`
2. **Keep it idempotent**: Use `IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, etc.
3. **Test locally**: Apply to local database and verify
4. **Update documentation**: Update `docs/data-model-overview.md` if needed
5. **Apply to production**: Follow hosted workflow above

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Supabase Database Guide](https://supabase.com/docs/guides/database)
- [AWS RDS PostgreSQL Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
