# Stack Discovery & Architecture Analysis

**Generated:** 2024-12-XX  
**Status:** Complete Repository Diagnostic

## Executive Summary

This is a **Podcast Analytics & Sponsorship Platform** - a full-stack SaaS application built with:
- **Frontend:** Next.js 14 (React 18) with TypeScript
- **Backend:** FastAPI (Python 3.11+) with async/await
- **Database:** PostgreSQL 15+ with TimescaleDB extension
- **Cache:** Redis 7
- **Hosting:** Vercel (frontend), Multiple options for backend (Fly.io, Kubernetes, Render)
- **Monitoring:** Prometheus + Grafana
- **CI/CD:** GitHub Actions

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js/Vercel)                   │
│  - App Router (Next.js 14)                                   │
│  - React 18 + TypeScript                                     │
│  - TailwindCSS + HeadlessUI                                  │
│  - TanStack Query (React Query)                              │
│  - Zustand (State Management)                                │
│  - Supabase Client (Auth/Storage)                            │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/REST API
┌───────────────────────▼─────────────────────────────────────┐
│              Backend API (FastAPI/Python)                     │
│  - FastAPI 0.104+                                             │
│  - AsyncPG (PostgreSQL async driver)                         │
│  - Redis (Caching/Sessions)                                  │
│  - Pydantic (Validation)                                       │
│  - OpenTelemetry (Tracing)                                    │
│  - Prometheus (Metrics)                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  PostgreSQL  │ │  TimescaleDB│ │    Redis    │
│  (Relational)│ │ (Time-Series)│ │   (Cache)  │
│              │ │              │ │            │
│  - Multi-    │ │  - Listener  │ │  - Session │
│    tenant    │ │    events    │ │  - Cache   │
│  - Users     │ │  - Metrics   │ │  - Rate    │
│  - Campaigns │ │  - Analytics │ │    limiting│
│  - Episodes  │ │              │ │            │
└──────────────┘ └──────────────┘ └────────────┘
```

## Technology Stack Details

### Frontend Stack

**Framework & Core:**
- Next.js 14.0+ (App Router)
- React 18.2+
- TypeScript 5.2+
- Node.js 20+

**UI & Styling:**
- TailwindCSS 3.3+
- HeadlessUI 1.7+
- Heroicons 2.0+
- Recharts 2.10+ (Charts)

**State & Data:**
- TanStack Query 5.0+ (Server state)
- Zustand 4.4+ (Client state)
- Axios 1.6+ (HTTP client)
- Supabase JS 2.39+ (Auth/Storage)

**Testing:**
- Jest 29.7+
- React Testing Library 14.0+
- Playwright 1.40+ (E2E)

### Backend Stack

**Framework & Core:**
- FastAPI 0.104+
- Python 3.11+
- Uvicorn 0.24+ (ASGI server)
- Pydantic 2.5+ (Validation)

**Database & Storage:**
- AsyncPG 0.29+ (PostgreSQL async driver)
- SQLAlchemy 2.0+ (ORM - if used)
- Redis 5.0+ (Cache/Sessions)
- TimescaleDB (Time-series extension)

**Security & Auth:**
- PyJWT 2.8+ (JWT tokens)
- Passlib 1.7+ (Password hashing)
- OAuth2 (Custom provider)

**External Services:**
- Stripe 7.0+ (Payments)
- SendGrid 6.11+ (Email)
- OpenAI/Anthropic (AI features)

**Monitoring & Observability:**
- Prometheus Client 0.19+
- OpenTelemetry 1.21+ (Tracing)
- Python JSON Logger 2.0+

**Testing:**
- Pytest 7.4+
- Pytest-asyncio 0.21+
- Pytest-cov 4.1+

**Code Quality:**
- Ruff 0.1+ (Linting/Formatting)
- MyPy 1.7+ (Type checking)

### Infrastructure

**Hosting:**
- **Frontend:** Vercel (Serverless)
- **Backend Options:**
  - Fly.io (Docker containers)
  - Kubernetes (k8s/)
  - Render (render.yaml)
  - Docker Compose (Local dev)

**CI/CD:**
- GitHub Actions
- Multiple workflows:
  - `ci.yml` - Lint, test, build
  - `frontend-ci-deploy.yml` - Frontend deploy to Vercel
  - `deploy-backend-*.yml` - Backend deployment options
  - `db-migrate.yml` - Database migrations
  - `e2e-tests.yml` - End-to-end tests
  - `smoke-tests.yml` - Smoke tests
  - `security-scan.yml` - Security scanning

**Monitoring:**
- Prometheus (Metrics)
- Grafana (Dashboards)
- Health check endpoints (`/health`, `/metrics`)

**Database:**
- PostgreSQL 15+ (Primary)
- TimescaleDB extension (Time-series)
- Redis 7+ (Cache)

## Data Flow Architecture

### Request Flow

1. **User Request** → Next.js Frontend (Vercel)
2. **API Call** → FastAPI Backend (via `NEXT_PUBLIC_API_URL`)
3. **Authentication** → JWT validation, tenant isolation
4. **Database Query** → PostgreSQL (relational) or TimescaleDB (time-series)
5. **Cache Check** → Redis (if applicable)
6. **Response** → JSON back to frontend
7. **UI Update** → React Query cache update

### Multi-Tenancy Flow

1. Every request includes `tenant_id` (from JWT or context)
2. All database queries filtered by `tenant_id`
3. Tenant isolation enforced at:
   - Database level (WHERE clauses)
   - Application level (middleware)
   - API level (route handlers)

### Time-Series Data Flow

1. **Listener Events** → `listener_events` hypertable (TimescaleDB)
2. **Metrics Aggregation** → Continuous aggregates (TimescaleDB)
3. **Analytics Queries** → Optimized time-series queries
4. **Dashboard Display** → Aggregated metrics via API

## Environment Variables

### Required (Production)

**Database:**
- `DATABASE_URL` (PostgreSQL connection string) OR
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

**Redis:**
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` (optional)

**Security:**
- `JWT_SECRET` (min 32 chars)
- `ENCRYPTION_KEY` (min 32 chars)

### Optional (Feature Flags)

- `ENABLE_ETL_CSV_UPLOAD`
- `ENABLE_MATCHMAKING`
- `ENABLE_IO_BOOKINGS`
- `ENABLE_DEAL_PIPELINE`
- `ENABLE_NEW_DASHBOARD_CARDS`
- `ENABLE_ORCHESTRATION`
- `ENABLE_MONETIZATION`
- `ENABLE_AUTOMATION_JOBS`

### Frontend

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SITE_URL`

## API Endpoints Structure

### Core APIs (Always Available)

- `/api/v1/auth/*` - Authentication
- `/api/v1/billing/*` - Billing/Stripe
- `/api/v1/campaigns/*` - Campaign management
- `/api/v1/podcasts/*` - Podcast CRUD
- `/api/v1/episodes/*` - Episode management
- `/api/v1/sponsors/*` - Sponsor management
- `/api/v1/reports/*` - Report generation
- `/api/v1/analytics/*` - Analytics queries
- `/api/v1/users/*` - User management
- `/api/v1/tenants/*` - Tenant management
- `/api/v1/attribution/*` - Attribution tracking
- `/api/v1/ai/*` - AI features
- `/api/v1/cost/*` - Cost tracking
- `/api/v1/security/*` - Security features
- `/api/v1/backup/*` - Backup/restore
- `/api/v1/optimization/*` - A/B testing, churn
- `/api/v1/monitoring/*` - Health/metrics
- `/api/v1/features/*` - Feature flags

### Feature-Flagged APIs

- `/api/v1/etl/*` - CSV upload (if `ENABLE_ETL_CSV_UPLOAD=true`)
- `/api/v1/match/*` - Matchmaking (if `ENABLE_MATCHMAKING=true`)
- `/api/v1/io/*` - IO bookings (if `ENABLE_IO_BOOKINGS=true`)
- `/api/v1/deals/*` - Deal pipeline (if `ENABLE_DEAL_PIPELINE=true`)
- `/api/v1/dashboard/*` - New dashboard (if `ENABLE_NEW_DASHBOARD_CARDS=true`)
- `/api/v1/automation/*` - Automation jobs (if `ENABLE_AUTOMATION_JOBS=true`)
- `/api/v1/monetization/*` - Monetization (if `ENABLE_MONETIZATION=true`)
- `/api/v1/orchestration/*` - Orchestration (if `ENABLE_ORCHESTRATION=true`)

## Database Schema Overview

### Core Tables

- `tenants` - Multi-tenant foundation
- `users` - User accounts (tenant-scoped)
- `podcasts` - Podcast definitions
- `episodes` - Episode metadata
- `sponsors` - Sponsor/advertiser info
- `campaigns` - Campaign definitions
- `tenant_settings` - Tenant configuration (JSONB)
- `tenant_quotas` - Tenant limits

### Time-Series Tables (TimescaleDB Hypertables)

- `listener_events` - Raw listener events
- `attribution_events` - Attribution tracking events
- `metrics_daily` - Daily aggregated metrics

### Feature Tables

- `io_bookings` - Insertion order bookings
- `deals` - Deal pipeline
- `matches` - Sponsor-podcast matches
- `workflows` - Workflow definitions
- `feature_flags` - Feature flag configuration

## Dependency Hotspots

### High-Gravity Modules (Most Imported)

**Backend:**
1. `src.config.settings` - Configuration (used everywhere)
2. `src.database.postgres` - Database connection
3. `src.telemetry.metrics` - Metrics collection
4. `src.telemetry.events` - Event logging
5. `src.tenants.tenant_manager` - Tenant isolation

**Frontend:**
1. `components/ui/*` - UI primitives
2. `app/layout.tsx` - Root layout
3. API client utilities

### Circular Dependencies

**Potential Issues:**
- Check for circular imports between:
  - `src.api.*` modules
  - `src.services.*` modules
  - `src.tenants.*` and `src.users.*`

## Security Posture

### Implemented

✅ JWT-based authentication  
✅ Multi-factor authentication (MFA)  
✅ Role-based access control (RBAC)  
✅ Attribute-based access control (ABAC)  
✅ API key management  
✅ Rate limiting  
✅ CORS configuration  
✅ Security headers middleware  
✅ WAF middleware  
✅ CSRF protection  
✅ Password hashing (bcrypt)  
✅ Tenant isolation  
✅ Audit logging  

### Areas for Enhancement

⚠️ Input sanitization (verify all endpoints)  
⚠️ SQL injection protection (verify parameterized queries)  
⚠️ File upload validation (if applicable)  
⚠️ Secrets scanning in CI  
⚠️ Dependency vulnerability scanning  

## Performance Considerations

### Optimizations Implemented

✅ Connection pooling (PostgreSQL, Redis)  
✅ Read replicas support (PostgreSQL)  
✅ Redis caching layer  
✅ TimescaleDB for time-series (chunking, compression)  
✅ Code splitting (Next.js webpack config)  
✅ Image optimization (Next.js)  
✅ Prometheus metrics collection  

### Potential Bottlenecks

⚠️ Database query optimization (need query analysis)  
⚠️ N+1 query patterns (verify with tests)  
⚠️ Frontend bundle size (analyze with webpack-bundle-analyzer)  
⚠️ API response times (add latency monitoring)  
⚠️ Cache hit rates (monitor Redis)  

## CI/CD Pipeline

### Workflows

1. **ci.yml** - Main CI pipeline
   - Lint backend (ruff, mypy)
   - Lint frontend (ESLint, TypeScript)
   - Test backend (pytest with coverage)
   - Test frontend (Jest)
   - Build backend (Docker)
   - Build frontend (Next.js)

2. **frontend-ci-deploy.yml** - Frontend deployment
   - Build and test
   - Deploy preview (PR)
   - Deploy production (main branch)

3. **db-migrate.yml** - Database migrations
   - Validate migrations
   - Test migrations

4. **e2e-tests.yml** - End-to-end tests
   - Playwright tests

5. **smoke-tests.yml** - Smoke tests
   - Health checks
   - Critical path validation

6. **security-scan.yml** - Security scanning
   - Dependency vulnerabilities
   - Code security issues

### Deployment Strategies

- **Frontend:** Vercel (automatic on push to main)
- **Backend:** Multiple options:
  - Fly.io (Docker)
  - Kubernetes (k8s/)
  - Render (render.yaml)

## Risk Heatmap

### 🔴 Critical Risks

1. **Database Migration Safety**
   - Single master migration file (`99999999999999_master_schema.sql`)
   - Need incremental migration strategy for production
   - Risk: Schema drift between environments

2. **Environment Variable Drift**
   - Many optional variables
   - Risk: Missing configs in production
   - Solution: Env validation script needed

3. **Feature Flag Management**
   - Flags control critical features
   - Risk: Misconfiguration could disable core features
   - Solution: Feature flag validation

### 🟡 Medium Risks

1. **Multi-Environment Parity**
   - DEV/STAGING/PROD alignment
   - Risk: Environment-specific bugs
   - Solution: Environment parity checker

2. **Test Coverage**
   - Backend: 50% minimum (CI enforced)
   - Frontend: Coverage check exists but not enforced
   - Risk: Regression bugs
   - Solution: Increase coverage thresholds

3. **Dependency Updates**
   - Many dependencies
   - Risk: Security vulnerabilities
   - Solution: Automated dependency updates

### 🟢 Low Risks

1. **Documentation Sync**
   - Extensive docs exist
   - Risk: Docs drift from code
   - Solution: Auto-sync scripts

2. **Code Quality**
   - Linting and type checking enforced
   - Risk: Technical debt accumulation
   - Solution: Regular refactoring

## Misalignments & Issues Found

### 1. Database Connection String Handling

**Issue:** Code supports both `DATABASE_URL` and individual `POSTGRES_*` vars, but validation may not handle both paths consistently.

**Impact:** Medium - Could cause deployment issues

**Fix:** Ensure `src/config/validation.py` handles `DATABASE_URL` parsing correctly.

### 2. Frontend API URL Configuration

**Issue:** `NEXT_PUBLIC_API_URL` hardcoded in some places, should use env var consistently.

**Impact:** Low - Works but not flexible

**Fix:** Audit all API calls to use env var.

### 3. Migration Strategy

**Issue:** Single master migration file is good for greenfield, but needs incremental strategy for production.

**Impact:** High - Production migrations risky

**Fix:** Create incremental migration system.

### 4. Feature Flag Defaults

**Issue:** Many features disabled by default, but some may be needed for core functionality.

**Impact:** Medium - Could block core features

**Fix:** Review feature flags, enable core features by default.

### 5. Test Environment Setup

**Issue:** Tests require full database setup, may be slow.

**Impact:** Low - Works but could be faster

**Fix:** Consider test database fixtures or mocks.

## Safe Fixes to Apply

1. ✅ **Environment Variable Validation Script**
   - Create `scripts/env-doctor.ts` to validate env vars

2. ✅ **Schema Validator Script**
   - Create `scripts/db-validate-schema.ts` to validate DB schema

3. ✅ **API Documentation Generator**
   - Generate OpenAPI spec from FastAPI
   - Create `docs/api.md` from OpenAPI

4. ✅ **Dependency Health Check**
   - Audit dependencies for vulnerabilities
   - Update outdated packages

5. ✅ **CI/CD Improvements**
   - Ensure all workflows run correctly
   - Add missing checks

## Next Steps

1. Generate complete API documentation (Mode 4)
2. Create environment variable doctor script (Mode 5)
3. Optimize database queries and indexes (Mode 6)
4. Harden deployment workflows (Mode 7)
5. Enhance test coverage (Mode 13)
6. Add observability instrumentation (Mode 14)
7. Security audit (Mode 15)
8. Performance optimization (Mode 16)
9. Developer experience improvements (Mode 17)
10. Documentation automation (Mode 18)

---

**Last Updated:** 2024-12-XX  
**Status:** ✅ Diagnostic Complete - Proceeding with Mode 2-30
