# Backend & Database Strategy

**Last Updated:** 2024  
**Status:** Canonical backend strategy for the podcast analytics platform

---

## Executive Summary

**Canonical Backend:** FastAPI (Python 3.11) + PostgreSQL 15 with TimescaleDB + Redis

**Database Hosting Recommendation:** **Supabase Pro** ($25/month) for production, with fallback to self-hosted Postgres for development.

**Rationale:** The platform requires PostgreSQL with TimescaleDB extension, multi-tenant RLS, and real-time capabilities. Supabase provides managed Postgres with these features, reducing operational overhead significantly.

---

## Current Backend Architecture

### Backend Stack
- **Framework:** FastAPI 0.104.1
- **Language:** Python 3.11
- **ASGI Server:** Uvicorn (4 workers in production)
- **Database:** PostgreSQL 15 with TimescaleDB extension
- **Cache:** Redis 7
- **ORM:** SQLAlchemy 2.0 with asyncpg driver

### Database Requirements

#### Core Requirements
1. **PostgreSQL 15+** with extensions:
   - `uuid-ossp` - UUID generation
   - `pg_trgm` - Text search
   - `pgcrypto` - Encryption
   - `timescaledb` - Time-series data (critical)

2. **TimescaleDB Features Used:**
   - Hypertables: `listener_events`, `attribution_events`, `listener_metrics`
   - Continuous aggregates for analytics
   - Time-based partitioning and retention policies

3. **Row-Level Security (RLS):**
   - Multi-tenant isolation via RLS policies
   - Tenant context functions (`set_tenant_context`)
   - Critical for data security

4. **JSONB Support:**
   - Extensive use of JSONB columns (`event_data`, `configuration`, `metadata`, `signals`)

### Current Database Hosting Status

**Status:** Flexible - supports both Supabase-hosted and self-hosted Postgres

**Evidence:**
- Connection string format: `DATABASE_URL` or individual `POSTGRES_*` variables
- Migrations: SQL-based (not Supabase-native migrations)
- Code: Uses standard asyncpg/SQLAlchemy (no Supabase-specific code)
- Frontend: Has `@supabase/supabase-js` but unclear if actively used for auth/storage

**Supabase Integration:**
- Optional environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`
- Frontend has Supabase client installed
- No Supabase migrations directory (`supabase/migrations/` doesn't exist)
- Supabase config file exists but minimal (`supabase/config.toml`)

---

## Recommended Backend Strategy

### Production: Supabase Pro ($25/month)

**Why Supabase:**
1. **Managed PostgreSQL with TimescaleDB Support**
   - Supabase uses standard PostgreSQL and supports TimescaleDB extension
   - Automatic backups, point-in-time recovery
   - Managed updates and patches
   - High availability options

2. **Built-in RLS Support**
   - Native PostgreSQL RLS (already used in schema)
   - Supabase provides UI for managing RLS policies
   - Aligns perfectly with existing multi-tenant architecture

3. **Real-time Capabilities**
   - PostgreSQL logical replication for real-time updates
   - Useful for dashboard updates and event streaming
   - No additional infrastructure needed

4. **Developer Experience**
   - Web UI for database management
   - SQL editor with query history
   - Database backups UI
   - Monitoring and performance insights

5. **Cost-Effective**
   - Free tier for development/testing
   - Pro tier ($25/month) includes 8 GB database, 50 GB bandwidth, daily backups
   - Clear upgrade path to Team tier ($599/month) for higher scale

**Migration Path:**
1. Use Supabase-hosted Postgres for production
2. Apply master migration (`db/migrations/99999999999999_master_schema.sql`) via Supabase SQL editor or CI
3. Update `DATABASE_URL` to Supabase connection string
4. Verify TimescaleDB extension is enabled (may need to contact Supabase support)

### Development: Self-Hosted Postgres (Docker Compose)

**Why Self-Hosted for Dev:**
- Free (no cost)
- Full control over extensions
- Fast iteration (no network latency)
- Matches production TimescaleDB setup

**Setup:**
- Use `docker-compose.yml` with TimescaleDB image
- Run migrations via `scripts/db-migrate-local.sh`
- No Supabase account needed for local development

### Alternative: Generic Managed Postgres

**If Supabase is not suitable:**
- **DigitalOcean Managed Databases:** $15/month (1 GB RAM, 10 GB storage, TimescaleDB support)
- **AWS RDS PostgreSQL:** $15-30/month (db.t3.micro, TimescaleDB via extensions)
- **TimescaleDB Cloud:** $29/month (1 GB RAM, 25 GB storage, TimescaleDB native)

**Trade-offs:**
- Lower cost but higher operational overhead
- Must configure backups, monitoring, security updates manually
- No built-in real-time subscriptions (would need external solution)

---

## Database Migration Strategy

### Current Migration Approach

**Format:** SQL-based migrations (not Prisma, not Supabase migrations)

**Master Schema:** `db/migrations/99999999999999_master_schema.sql`
- Single idempotent migration file
- Consolidates all schema changes
- Safe to run multiple times (uses `CREATE TABLE IF NOT EXISTS`, etc.)

**Legacy Migrations:** Archived in `migrations_archive/` (001-030, plus dated folders)

### Migration Scripts

1. **Local Development:**
   ```bash
   ./scripts/db-migrate-local.sh
   ```
   - Uses `psql` to apply master schema
   - Connects to local Postgres (default: `postgresql://postgres:postgres@localhost:5432/podcast_analytics`)
   - Verifies TimescaleDB extension

2. **Hosted/Production:**
   ```bash
   DATABASE_URL=postgresql://... ./scripts/db-migrate-hosted.sh
   ```
   - Includes safety confirmations
   - Verifies TimescaleDB extension
   - Checks for existing tables before applying

### CI Migration Workflow

**Current State:** Deploy workflows reference `scripts/init_db.py` but this script may have outdated imports.

**Recommended:** Use SQL-based migrations via `psql` in CI (simpler, more reliable).

**Workflow:**
1. PR: Validate migration SQL syntax (no actual DB changes)
2. Main branch: Apply migrations to staging/production via CI
3. Use GitHub Secrets for `DATABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

---

## Backend Deployment Strategy

### Current State

**Container:** Docker (Dockerfile, Dockerfile.prod)
- Multi-stage build for production
- Non-root user
- Health checks
- Entrypoint script for validation

**Orchestration:** Kubernetes configs exist (`k8s/deployment.yaml`)

**Deployment Target:** **TBD** (deploy workflows have placeholder steps)

### Recommended Deployment Options

#### Option 1: Render (Recommended for Simplicity)

**Pros:**
- Simple Docker deployment
- Automatic HTTPS
- Built-in health checks
- Free tier available
- Easy environment variable management

**Setup:**
1. Connect GitHub repo to Render
2. Create Web Service from Dockerfile
3. Set environment variables (DATABASE_URL, REDIS_URL, etc.)
4. Deploy automatically on push to main

**Cost:** Free tier (limited) or $7/month for basic plan

#### Option 2: Fly.io

**Pros:**
- Global edge deployment
- Docker-based
- Good for low-latency requirements
- Free tier available

**Setup:**
1. Install Fly CLI
2. Run `fly launch` (creates `fly.toml`)
3. Set secrets: `fly secrets set DATABASE_URL=...`
4. Deploy: `fly deploy`

**Cost:** Free tier (limited) or pay-as-you-go

#### Option 3: AWS ECS / GCP Cloud Run

**Pros:**
- Enterprise-grade
- Auto-scaling
- Integration with cloud services

**Cons:**
- More complex setup
- Higher cost
- Requires cloud expertise

**Recommendation:** Start with Render or Fly.io, migrate to AWS/GCP if needed.

---

## Redis Strategy

### Current Setup
- **Version:** Redis 7 (Alpine)
- **Usage:** Caching, session storage, rate limiting

### Hosting Options

#### Development
- **Docker Compose:** Local Redis container
- **No cost**

#### Production

**Option 1: Supabase (if using Supabase for Postgres)**
- Supabase doesn't provide Redis
- Need separate Redis hosting

**Option 2: Upstash Redis (Recommended)**
- Serverless Redis
- Free tier: 10K commands/day
- Paid: $0.20/100K commands
- Global edge caching

**Option 3: Redis Cloud**
- Managed Redis
- Free tier: 30 MB
- Paid: $5/month for 100 MB

**Option 4: Self-Hosted**
- VPS: $5-10/month
- Higher operational overhead

**Recommendation:** Use Upstash Redis for production (serverless, cost-effective, global).

---

## Backend API Strategy

### Current API Structure
- **Framework:** FastAPI
- **Routes:** Organized in `src/api/` (via `route_registration.py`)
- **Documentation:** Auto-generated OpenAPI at `/api/docs`
- **Health Check:** `/health` endpoint
- **Metrics:** `/metrics` endpoint (Prometheus)

### API Hosting

**Current:** Backend runs as standalone FastAPI server

**Options:**
1. **Standalone Deployment** (Current)
   - Deploy FastAPI server as Docker container
   - Expose port 8000
   - Use reverse proxy (nginx, Caddy) for HTTPS

2. **Serverless Functions** (Future)
   - Could migrate to Vercel Serverless Functions or AWS Lambda
   - Requires refactoring (FastAPI → serverless handlers)
   - Not recommended initially (adds complexity)

**Recommendation:** Keep standalone FastAPI deployment for now. Migrate to serverless only if cost/scale requires it.

---

## Environment Variables Strategy

### Database Connection

**Primary:** `DATABASE_URL` (PostgreSQL connection string)
```
postgresql://user:password@host:port/database
```

**Fallback:** Individual variables (for backward compatibility)
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DATABASE`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### Supabase (Optional)

If using Supabase-hosted Postgres:
- `SUPABASE_URL` - Project URL (for Supabase features like auth/storage)
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (for admin operations)
- `SUPABASE_ANON_KEY` - Anonymous key (for client-side, if using Supabase client)

**Note:** `DATABASE_URL` is still required even with Supabase (it's the Postgres connection string).

### Redis

**Primary:** `REDIS_URL` (Redis connection string)
```
redis://:password@host:port
```

**Fallback:** Individual variables
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`

---

## Scaling Considerations

### Database Scaling

**Current Scale:** Suitable for 10-1,000 tenants

**Scaling Path:**
1. **Early Stage (10-100 tenants):**
   - Supabase Pro ($25/month) or DigitalOcean Managed ($15/month)
   - 8 GB database storage
   - Single region

2. **Growth Stage (100-1,000 tenants):**
   - Supabase Team ($599/month) or AWS RDS larger instance
   - 32 GB+ database storage
   - Read replicas for analytics queries

3. **Mature (1,000+ tenants):**
   - Multi-region setup
   - Read replicas in multiple regions
   - TimescaleDB Cloud for dedicated time-series storage
   - Consider separating time-series data from relational data

### Backend Scaling

**Current:** Single FastAPI instance (4 workers)

**Scaling Path:**
1. **Horizontal Scaling:**
   - Deploy multiple FastAPI instances
   - Use load balancer (nginx, Cloudflare, AWS ALB)
   - Stateless design (sessions in Redis)

2. **Auto-scaling:**
   - Use Kubernetes HPA or cloud provider auto-scaling
   - Scale based on CPU/memory/request rate

3. **Caching:**
   - Increase Redis usage for frequently accessed data
   - Use CDN for static assets (if any)

---

## Cost Summary

| Component | Development | Production (Early) | Production (Growth) |
|-----------|------------|-------------------|---------------------|
| **Database** | Free (Docker) | Supabase Pro ($25/mo) | Supabase Team ($599/mo) |
| **Redis** | Free (Docker) | Upstash Free/Paid ($0-5/mo) | Upstash Paid ($20-50/mo) |
| **Backend Hosting** | Free (Local) | Render ($7/mo) or Fly.io (Free) | AWS ECS ($50-200/mo) |
| **Frontend Hosting** | Free (Local) | Vercel (Free) | Vercel Pro ($20/mo) |
| **Total** | **$0** | **$32-57/mo** | **$669-869/mo** |

**Note:** Costs are approximate and vary by usage. Free tiers are suitable for development and early production.

---

## Migration Checklist

### To Supabase (Production)

- [ ] Create Supabase project
- [ ] Verify TimescaleDB extension availability (contact support if needed)
- [ ] Get connection string from Supabase dashboard
- [ ] Set `DATABASE_URL` in GitHub Secrets and hosting platform
- [ ] Apply master migration via Supabase SQL editor or CI
- [ ] Verify RLS policies are active
- [ ] Test tenant isolation
- [ ] Verify TimescaleDB hypertables created
- [ ] Update frontend `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (if using Supabase features)

### To Generic Managed Postgres (Alternative)

- [ ] Create managed Postgres instance (DigitalOcean, AWS RDS, etc.)
- [ ] Enable TimescaleDB extension
- [ ] Get connection string
- [ ] Set `DATABASE_URL` in GitHub Secrets and hosting platform
- [ ] Apply master migration via CI or `psql`
- [ ] Configure backups (daily recommended)
- [ ] Set up monitoring and alerts
- [ ] Test tenant isolation and RLS policies

---

## Future Considerations

### If We Need to Scale Beyond Supabase Team Tier

1. **Hybrid Approach:**
   - Keep relational data in Supabase
   - Move time-series data to TimescaleDB Cloud
   - Use read replicas for analytics

2. **Self-Hosted:**
   - Migrate to self-hosted Postgres on AWS/GCP
   - Requires DevOps expertise
   - Higher operational overhead

3. **Database Sharding:**
   - Partition tenants across multiple databases
   - Requires application-level routing
   - Significant refactoring

### If We Need Real-time Features

- **Supabase:** Built-in PostgreSQL subscriptions (already available)
- **Generic Postgres:** Use Supabase Realtime or Pusher/Ably for real-time updates
- **WebSockets:** Add WebSocket support to FastAPI for custom real-time features

---

## Summary

**Canonical Backend:**
- FastAPI (Python 3.11) + PostgreSQL 15 + TimescaleDB + Redis

**Database Hosting:**
- **Production:** Supabase Pro ($25/month) - recommended
- **Development:** Self-hosted Postgres (Docker Compose) - free
- **Alternative:** DigitalOcean Managed Postgres ($15/month) if budget is tight

**Backend Deployment:**
- **Recommended:** Render or Fly.io (simple, Docker-based, free tier available)
- **Future:** AWS ECS / GCP Cloud Run if enterprise features needed

**Redis:**
- **Development:** Docker Compose (free)
- **Production:** Upstash Redis (serverless, cost-effective)

**Migration Strategy:**
- SQL-based migrations (master schema approach)
- CI-first migration workflow
- Idempotent migrations (safe to run multiple times)

This strategy balances cost, simplicity, and scalability while minimizing operational overhead.
