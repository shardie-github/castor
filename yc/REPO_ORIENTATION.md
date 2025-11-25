# Repo Orientation: Podcast Analytics & Sponsorship Platform

**Generated:** 2024  
**Purpose:** Quick orientation for YC partners, investors, and technical reviewers

---

## What Is This Product?

**Podcast Analytics & Sponsorship Platform** - A SaaS platform that helps podcasters monetize their shows through enterprise-grade analytics, automated sponsor matching, and real-time attribution tracking.

**One-Sentence Description:**  
Turn your podcast into a revenue-generating machine with analytics that prove ROI to sponsors and automate the entire campaign lifecycle.

---

## Who Is The User?

**Primary Users:**
1. **Solo Podcasters** (1K-50K downloads/month) - Indie creators who need to prove value to sponsors
2. **Producers/Agencies** (5-50+ shows) - Managing multiple podcasts, need portfolio-level insights
3. **Brands/Sponsors** - Marketers who need ROI proof for podcast advertising spend

**Secondary Users:**
- Podcast Networks
- Enterprise Platforms (white-label)
- Data Marketers (API access)

**Target Market:** ~2M+ podcasters globally, with ~500K actively monetizing

---

## What Core Problem Does It Solve?

**The Problem:** Podcast monetization is broken.

1. **No Visibility:** Podcasters can't see who's listening, where they're coming from, or what drives conversions
2. **Manual Matching:** Finding sponsors is time-consuming and relationship-dependent
3. **Attribution Chaos:** Proving ROI means cobbling together data from multiple sources—still guesswork
4. **Pricing Blind Spots:** Either leaving money on the table or pricing yourself out of deals

**The Solution:**  
Unified platform that provides:
- Real-time analytics (not just downloads—actual insights)
- AI-powered sponsor matching
- Multiple attribution models (first-touch, last-touch, linear, time-decay, position-based)
- Automated campaign management and reporting
- Cross-platform tracking connecting podcast listens to website visits, purchases, conversions

---

## Architecture At A High Level

### Tech Stack

**Frontend:**
- Next.js 14 (React 18)
- TypeScript
- TailwindCSS
- Zustand (state management)
- TanStack Query (data fetching)

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 15+ with TimescaleDB extension (time-series data)
- Redis 7+ (caching, sessions)
- Prometheus + Grafana (monitoring)

**Infrastructure:**
- Docker Compose (local dev)
- Kubernetes (production deployment configs)
- Supabase (recommended hosted DB)
- Vercel (frontend hosting)

### Architecture Pattern

```
┌─────────────────────────────────────────┐
│     Frontend (Next.js)                  │
│     Dashboard | Analytics | Campaigns   │
└─────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│     API Layer (FastAPI)                  │
│     REST APIs | Auth | Webhooks          │
└──────────────────┬───────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌──────▼──────┐  ┌───▼────┐
│Postgres│  │ TimescaleDB │  │ Redis  │
│(Rel)   │  │ (Time-Series)│  │(Cache) │
└────────┘  └─────────────┘  └────────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
┌──────────────────▼───────────────────────┐
│  Background Processing                   │
│  RSS Ingestion | Analytics | Workflows  │
└─────────────────────────────────────────┘
```

### Key Components

1. **Ingestion Layer:** RSS feed polling, episode metadata extraction
2. **Analytics Store:** Time-series data (TimescaleDB) for listener metrics
3. **Attribution Engine:** Multiple models, cross-platform tracking, ROI calculations
4. **Campaign Management:** CRUD operations, sponsor relationships, lifecycle
5. **AI Framework:** Content analysis, predictive analytics, anomaly detection
6. **Orchestration:** Workflow engine, intelligent automation, event-driven processes
7. **Multi-Tenancy:** Tenant isolation, RBAC, white-labeling support

---

## Main Product (YC-Relevant)

**This is a B2B SaaS platform** targeting podcasters and agencies.

**Business Model:**
- Freemium → Starter ($29/mo) → Professional ($99/mo) → Enterprise (custom)
- Usage-based upsells (campaigns, reports, API calls)
- White-label options for enterprise

**Revenue Streams:**
1. Subscription tiers (primary)
2. Usage-based add-ons
3. Enterprise custom pricing
4. White-label licensing (future)

---

## Current State

**MVP Status:** ✅ Core features implemented
- RSS ingestion
- Campaign management
- Attribution tracking (promo codes)
- ROI calculations
- Report generation (PDF)
- Multi-tenant architecture

**Production Readiness:**
- Database migrations framework
- Monitoring & observability (Prometheus/Grafana)
- Security (OAuth2, RBAC, audit logs)
- Cost tracking & optimization
- Backup & disaster recovery

**What's Built:**
- Complete backend API (FastAPI)
- Frontend dashboard (Next.js)
- Database schema (PostgreSQL + TimescaleDB)
- Analytics & attribution engine
- Multi-tenant isolation
- Event tracking & telemetry

**What's Missing (from YC perspective):**
- Real user traction data
- Metrics instrumentation completeness
- Distribution channels validation
- Team background documentation
- Financial projections/model

---

## Key Files & Directories

**Product Definition:**
- `README.md` - Main product overview
- `mvp/mvp-scope.md` - MVP feature list
- `monetization/pricing-plan.md` - Pricing tiers & conversion logic
- `research/user-persona-matrix.md` - Detailed user personas

**GTM Strategy:**
- `gtm/` - Growth, SEO, content, influencer strategies
- `strategy/` - Competitive moat, innovation mechanisms

**Technical:**
- `src/main.py` - FastAPI app entry point
- `src/api/` - REST API routes
- `src/analytics/` - Analytics store & ROI calculator
- `src/attribution/` - Attribution models & engine
- `src/monetization/` - Pricing, billing, usage tracking
- `src/telemetry/` - Event logging & metrics

**Infrastructure:**
- `docker-compose.yml` - Local development setup
- `k8s/deployment.yaml` - Production deployment
- `db/migrations/` - Database schema
- `prometheus/`, `grafana/` - Monitoring configs

---

## Assumptions Made

1. **Main Product:** This is the primary YC-relevant product (not a side project)
2. **Target Market:** B2B SaaS for podcasters/agencies (not B2C consumer app)
3. **Stage:** Post-MVP, pre-traction (needs validation & growth)
4. **Team:** Inferred from codebase (needs explicit documentation)

---

## Next Steps

See `/yc/` directory for:
- YC narrative documents (product, problem, market, team)
- Metrics checklist & dashboard sketches
- Distribution plan
- Tech overview & defensibility
- Gap analysis
- Interview prep materials
