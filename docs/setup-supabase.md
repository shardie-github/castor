# Supabase Setup Guide

**Last Updated:** 2024  
**Purpose:** Complete guide for setting up Supabase for database hosting

---

## Quick Setup

### 1. Create Supabase Account

1. Go to: https://supabase.com/dashboard/sign-up
2. Sign up with GitHub (recommended)
3. Complete account setup

### 2. Create Project

1. Go to: https://supabase.com/dashboard
2. Click "New Project"
3. Fill in details:
   - **Name:** `podcast-analytics` (or your preferred name)
   - **Database Password:** Generate strong password (save it!)
   - **Region:** Choose closest to your users
   - **Pricing Plan:** Pro ($25/month) recommended for production
4. Click "Create new project"
5. Wait for project to be provisioned (2-3 minutes)

---

## Get Connection Details

### Database Connection String

1. Go to: Project Settings → Database
2. Scroll to "Connection string"
3. Select "URI" tab
4. Copy connection string
5. Replace `[YOUR-PASSWORD]` with your database password

**Format:**
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Use as:** `DATABASE_URL` in environment variables

### API Credentials

1. Go to: Project Settings → API
2. Copy:
   - **Project URL:** `https://[PROJECT-REF].supabase.co`
   - **anon/public key:** (for frontend)
   - **service_role key:** (for backend, keep secret!)

**Use as:**
- `SUPABASE_URL` = Project URL
- `SUPABASE_ANON_KEY` = anon/public key
- `SUPABASE_SERVICE_ROLE_KEY` = service_role key

---

## Enable TimescaleDB Extension

### Check Availability

**Important:** This project requires TimescaleDB extension for time-series data.

1. Go to: Project Settings → Database → Extensions
2. Search for "TimescaleDB"
3. Check if available

### If Available

1. Click "Enable" next to TimescaleDB
2. Wait for activation (may take a few minutes)

### If Not Available

**Option 1: Request Support**
1. Contact Supabase support
2. Request TimescaleDB extension enablement
3. Provide use case (time-series analytics)

**Option 2: Use Alternative**
- Use DigitalOcean Managed Postgres with TimescaleDB ($15/month)
- Use AWS RDS with TimescaleDB extension
- See `docs/backend-strategy.md` for alternatives

---

## Apply Migrations

### Option 1: Via Supabase SQL Editor

1. Go to: SQL Editor → New Query
2. Open `db/migrations/99999999999999_master_schema.sql`
3. Copy entire contents
4. Paste into SQL Editor
5. Click "Run"
6. Wait for completion (may take a few minutes)

### Option 2: Via CI/CD

**Recommended:** Use GitHub Actions workflow

1. Set `PRODUCTION_DATABASE_URL` in GitHub Secrets
2. Push to `main` branch
3. Migration runs automatically via `.github/workflows/db-migrate.yml`

### Option 3: Via Local Script

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Run migration
./scripts/db-migrate-hosted.sh
```

---

## Verify Setup

### Check Tables

1. Go to: Table Editor
2. Verify tables exist:
   - `tenants`
   - `users`
   - `podcasts`
   - `episodes`
   - `campaigns`
   - `listener_events`
   - `attribution_events`

### Check TimescaleDB Hypertables

Run in SQL Editor:

```sql
SELECT * FROM timescaledb_information.hypertables;
```

Should show:
- `listener_events`
- `attribution_events`
- `listener_metrics`

### Check RLS Policies

Run in SQL Editor:

```sql
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND rowsecurity = true;
```

Should show tables with Row-Level Security enabled.

---

## Configure Environment Variables

### Backend (GitHub Secrets / Hosting Platform)

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[SERVICE-ROLE-KEY]
```

### Frontend (Vercel Environment Variables)

```
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT-REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[ANON-KEY]
```

---

## Security Configuration

### Row-Level Security (RLS)

**Status:** Already configured in migrations

**Verify:**
1. Go to: Authentication → Policies
2. Check policies exist for:
   - `tenants` table
   - `users` table
   - Other tenant-scoped tables

### API Keys

**anon/public key:**
- Safe for frontend/client-side
- Limited by RLS policies
- Can be exposed in code

**service_role key:**
- ⚠️ **NEVER expose to frontend**
- Has admin access
- Bypasses RLS policies
- Store in backend secrets only

---

## Backup Configuration

### Automatic Backups

**Pro Tier:**
- Daily backups
- 7-day retention
- Point-in-time recovery

**Team Tier:**
- Hourly backups
- Longer retention
- Point-in-time recovery

### Manual Backup

1. Go to: Database → Backups
2. Click "Create backup"
3. Download backup file

### Restore Backup

1. Go to: Database → Backups
2. Select backup
3. Click "Restore"

---

## Monitoring & Performance

### Database Usage

1. Go to: Project Settings → Usage
2. Monitor:
   - Database size
   - Bandwidth usage
   - API requests

### Query Performance

1. Go to: Database → Query Performance
2. View slow queries
3. Optimize as needed

### Connection Pooling

**Recommended:** Use Supabase connection pooling

**Connection String (Pooled):**
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

**Benefits:**
- Better connection management
- Reduced connection overhead
- Improved performance

---

## Troubleshooting

### Connection Issues

**Issue:** Cannot connect to database

**Solutions:**
1. Verify connection string is correct
2. Check database password is correct
3. Verify IP is not blocked (check IP restrictions)
4. Check project is not paused

### Migration Failures

**Issue:** Migration fails with errors

**Solutions:**
1. Check TimescaleDB extension is enabled
2. Verify PostgreSQL version (should be 15+)
3. Check for existing tables (migration is idempotent)
4. Review error messages in SQL Editor

### TimescaleDB Not Available

**Issue:** TimescaleDB extension not found

**Solutions:**
1. Contact Supabase support to enable
2. Use alternative database provider (DigitalOcean, AWS RDS)
3. See `docs/backend-strategy.md` for alternatives

### Performance Issues

**Issue:** Slow queries or high latency

**Solutions:**
1. Use connection pooling
2. Add database indexes
3. Optimize queries
4. Upgrade to Team tier for better performance
5. Use read replicas (if available)

---

## Cost Management

### Free Tier Limits

- 500 MB database storage
- 2 GB bandwidth/month
- ❌ No TimescaleDB extension
- ❌ Limited for production

### Pro Tier ($25/month)

- 8 GB database storage
- 50 GB bandwidth/month
- ✅ TimescaleDB extension (may need to request)
- ✅ Daily backups
- ✅ Point-in-time recovery

### Team Tier ($599/month)

- 32 GB database storage
- 250 GB bandwidth/month
- ✅ TimescaleDB extension
- ✅ Hourly backups
- ✅ Better performance

**Recommendation:** Start with Pro tier for production.

---

## Alternative Setup (If Not Using Supabase)

### DigitalOcean Managed Postgres

1. Create database: https://cloud.digitalocean.com/databases
2. Enable TimescaleDB extension
3. Get connection string
4. Use as `DATABASE_URL`

**Cost:** $15/month (1 GB RAM, 10 GB storage)

### AWS RDS PostgreSQL

1. Create RDS instance: AWS Console → RDS
2. Enable TimescaleDB via parameter groups
3. Get connection string
4. Use as `DATABASE_URL`

**Cost:** $15-30/month (db.t3.micro)

See `docs/backend-strategy.md` for detailed comparison.

---

## Quick Reference

### Connection Strings

**Direct Connection:**
```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Pooled Connection (Recommended):**
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

### Dashboard URLs

- **Projects:** https://supabase.com/dashboard
- **Project Settings:** https://supabase.com/dashboard/project/[PROJECT-REF]/settings
- **SQL Editor:** https://supabase.com/dashboard/project/[PROJECT-REF]/sql
- **Table Editor:** https://supabase.com/dashboard/project/[PROJECT-REF]/editor

### CLI Commands

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref [PROJECT-REF]

# Run migrations
supabase db push
```

---

## Next Steps

1. ✅ Create Supabase account
2. ✅ Create project (Pro tier recommended)
3. ✅ Get connection string and API keys
4. ✅ Enable TimescaleDB extension (if available)
5. ✅ Apply migrations
6. ✅ Verify tables and hypertables
7. ✅ Configure environment variables
8. ✅ Set up backups
9. ✅ Monitor usage

For detailed backend strategy, see: `docs/backend-strategy.md`
