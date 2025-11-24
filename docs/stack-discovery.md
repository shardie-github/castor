# Stack Discovery Report

**Generated:** 2024  
**Purpose:** Complete inventory of the technology stack, infrastructure, and deployment patterns

---

## Executive Summary

This is a **podcast analytics and sponsorship platform** with:
- **Frontend:** Next.js 14 (React 18, TypeScript)
- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15 with TimescaleDB extension
- **Cache:** Redis 7
- **Frontend Hosting:** Vercel
- **Backend Hosting:** Docker/Kubernetes (deployment target TBD)
- **CI/CD:** GitHub Actions

The architecture supports multi-tenancy, real-time analytics, attribution tracking, and AI-powered features.

---

## Frontend Stack

### Framework & Build
- **Framework:** Next.js 14.0.0 (App Router)
- **React:** 18.2.0
- **TypeScript:** 5.2.0
- **Build Tool:** Next.js built-in (Webpack)
- **Package Manager:** npm (package-lock.json present)

### Key Dependencies
- `@tanstack/react-query` - Data fetching & caching
- `zustand` - State management
- `recharts` - Data visualization
- `tailwindcss` - Styling
- `@supabase/supabase-js` - Supabase client (optional, for auth/storage)

### Testing
- Jest with React Testing Library
- Playwright for E2E (configured but not actively used in CI)

### Configuration
- `next.config.js` - Next.js configuration
- `vercel.json` - Vercel deployment configuration
- Environment variables prefixed with `NEXT_PUBLIC_*` for client-side access

---

## Backend Stack

### Framework & Runtime
- **Framework:** FastAPI 0.104.1
- **Python:** 3.11
- **ASGI Server:** Uvicorn
- **Package Manager:** pip (requirements.txt)

### Key Dependencies
- `pydantic` / `pydantic-settings` - Configuration & validation
- `sqlalchemy` / `asyncpg` - Database ORM & async driver
- `redis` - Caching
- `stripe` - Payment processing
- `sendgrid` - Email
- `prometheus-client` - Metrics
- `opentelemetry-*` - Observability

### Testing
- pytest with pytest-asyncio
- Coverage target: 50% minimum

### Code Quality
- `ruff` - Linting & formatting (replaces flake8, black, isort)
- `mypy` - Type checking

---

## Database & Persistence

### Primary Database
- **Type:** PostgreSQL 15
- **Extension:** TimescaleDB (for time-series data)
- **Connection:** SQLAlchemy with asyncpg driver
- **Schema:** Multi-tenant architecture with comprehensive tables for:
  - Tenants, users, podcasts, episodes
  - Campaigns, attribution events, listener events
  - AI features, cost tracking, security, compliance

### Migration Strategy
- **Approach:** SQL-based migrations (not Prisma, not Supabase migrations)
- **Master Schema:** `db/migrations/99999999999999_master_schema.sql`
  - Single idempotent migration file
  - Consolidates all schema changes
  - Safe to run multiple times
- **Legacy Migrations:** Archived in `migrations_archive/` (001-030, plus dated folders)
- **Scripts:**
  - `scripts/db-migrate-local.sh` - Local development
  - `scripts/db-migrate-hosted.sh` - Production/hosted databases

### Supabase Integration
- **Status:** Optional/Partial
- **Usage:** Can use Supabase-hosted Postgres OR self-hosted Postgres
- **Config:** `supabase/config.toml` exists but minimal
- **Client:** Frontend has `@supabase/supabase-js` installed
- **Note:** Supabase is mentioned in README as recommended option, but migrations are SQL-based (not Supabase migration format)

### Cache
- **Redis:** Version 7 (Alpine)
- **Usage:** Caching, session storage, rate limiting

---

## Infrastructure & Hosting

### Frontend Hosting
- **Primary:** Vercel
- **Config:** `vercel.json` present
- **Deployment:** Via GitHub Actions (deploy.yml) or Vercel CLI
- **Environment:** Preview deployments for PRs, production for main branch

### Backend Hosting
- **Container:** Docker (Dockerfile, Dockerfile.prod)
- **Orchestration:** Kubernetes configs present (`k8s/deployment.yaml`)
- **Registry:** Configurable (secrets: `CONTAINER_REGISTRY`, `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`)
- **Deployment Target:** TBD (Render, Fly.io, AWS ECS, GCP Cloud Run, etc.)

### Local Development
- **Docker Compose:** `docker-compose.yml` includes:
  - PostgreSQL (TimescaleDB)
  - Redis
  - Prometheus
  - Grafana
- **Scripts:** `scripts/dev.sh` for starting/stopping services

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### Active Workflows
1. **`.github/workflows/ci.yml`**
   - Triggers: PRs and pushes to main/develop
   - Jobs:
     - `lint-backend` - Ruff + mypy
     - `lint-frontend` - ESLint + TypeScript check
     - `test-backend` - pytest with coverage
     - `test-frontend` - Jest
     - `build-backend` - Docker build verification
     - `build-frontend` - Next.js build

2. **`.github/workflows/deploy.yml`**
   - Triggers: Push to main, workflow_dispatch
   - Environment: production
   - Steps:
     - Run migrations (Supabase/hosted)
     - Build & push Docker image
     - Deploy frontend to Vercel
     - Deploy backend (placeholder)
     - Smoke tests (placeholder)

3. **`.github/workflows/deploy-staging.yml`**
   - Triggers: Push to develop, workflow_dispatch
   - Environment: staging
   - Similar to production but for staging

4. **`.github/workflows/test-migrations.yml`**
   - Triggers: PRs affecting migrations, workflow_dispatch
   - Tests migration files against a test database

#### Other Workflows (Status Unclear)
- `aurora-doctor.yml` - Health check automation
- `e2e-tests.yml` - End-to-end tests (not actively used)
- `nightly.yml` / `nightly.yml.new` - Nightly builds (may be obsolete)

### CI Environment
- **Python:** 3.11
- **Node:** 20
- **OS:** ubuntu-latest
- **Services:** PostgreSQL 15, Redis 7 (for test-backend job)

---

## Environment Variables & Secrets

### Configuration Files
- `.env.example` - Comprehensive template with all variables
- `.env.staging` - Staging-specific overrides (if needed)

### Categories
1. **Database:** `DATABASE_URL` or individual `POSTGRES_*` vars
2. **Redis:** `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
3. **Security:** `JWT_SECRET`, `ENCRYPTION_KEY`
4. **Supabase:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`
5. **Frontend:** `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, etc.
6. **External Services:** Stripe, SendGrid, AWS, etc.
7. **Feature Flags:** `ENABLE_*` variables for toggling features

### Secrets Management
- **GitHub Secrets:** Used in CI workflows
- **Vercel:** Environment variables set in dashboard
- **Backend Hosting:** TBD (will need secrets for DB, Redis, etc.)

---

## Notable Gaps & Red Flags

### 🔴 Critical Issues
1. **Migration Workflow:** 
   - Migrations are SQL-based but deploy workflows reference `scripts/init_db.py` which may not exist
   - No clear CI path for validating migrations before deploy
   - Master schema approach is good but needs better orchestration

2. **Backend Deployment:**
   - Deploy workflows have placeholder steps ("Add actual deployment commands")
   - No clear production backend hosting target

3. **Supabase Integration:**
   - Supabase is mentioned but migrations aren't Supabase-native
   - Frontend has Supabase client but unclear if auth/storage are used
   - Need to decide: Supabase-hosted Postgres OR self-hosted Postgres

### ⚠️ Medium Priority
4. **Package Manager Lock:**
   - Frontend uses npm (package-lock.json)
   - Backend uses pip (requirements.txt, no Pipfile.lock)
   - Should pin Node version in package.json engines

5. **Test Coverage:**
   - Backend coverage target is 50% (reasonable but could be higher)
   - Frontend tests exist but coverage not enforced in CI

6. **Obsolete Workflows:**
   - `nightly.yml.new`, `ci.yml.new` suggest incomplete migrations
   - `e2e-tests.yml` exists but not integrated into PR checks

### ✅ Good Practices Found
- Comprehensive `.env.example`
- Docker Compose for local dev
- Health check endpoints (`/health`, `/metrics`)
- Multi-stage Dockerfile for production
- Idempotent migrations
- CI runs lint, test, build on PRs

---

## Business Intent

### Primary Use Case
**Podcast Analytics & Sponsorship Platform**

### User Flows
1. **Podcasters:** Track listener behavior, prove ROI to sponsors, automate reporting
2. **Podcast Networks:** Manage multiple shows, match advertisers, unified reporting
3. **Agencies:** Onboard clients, demonstrate ROI, scale operations
4. **Advertisers:** Find matching podcasts, track campaign performance

### App Type
- **Dashboard-heavy:** Analytics, campaign management, attribution tracking
- **API-first:** FastAPI backend with comprehensive REST APIs
- **Multi-tenant:** Isolated data per organization
- **Real-time:** Time-series data with TimescaleDB

---

## Recommendations

1. **Choose Backend Hosting:** Decide on Render, Fly.io, AWS, or other and complete deployment workflows
2. **Clarify Supabase:** Either commit to Supabase-hosted Postgres OR remove Supabase references
3. **Normalize Migrations:** Create a CI workflow that validates migrations before deploy
4. **Complete Deployment:** Replace placeholder steps in deploy workflows
5. **Add Smoke Tests:** Implement actual smoke tests for production deployments
6. **Clean Up Workflows:** Remove or complete obsolete workflows (`nightly.yml.new`, etc.)

---

**Next Steps:** See `docs/backend-strategy.md` and `docs/frontend-hosting-strategy.md` for detailed recommendations.
