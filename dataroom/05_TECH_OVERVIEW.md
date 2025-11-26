# Tech Overview

**Technical architecture for investors**

---

## High-Level Architecture

```
Frontend (Next.js/Vercel)
    ↓ HTTPS/REST API
Backend API (FastAPI/Python)
    ↓
PostgreSQL + TimescaleDB + Redis
    ↓
Background Processing (RSS, Analytics, Workflows)
```

---

## Tech Stack

### Frontend
- **Framework:** Next.js 14 (React 18, TypeScript)
- **Hosting:** Vercel (CDN, automatic deployments)
- **State:** Zustand, TanStack Query
- **UI:** TailwindCSS, HeadlessUI

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Hosting:** Fly.io / Render / Kubernetes
- **Database:** PostgreSQL 15 + TimescaleDB (Supabase)
- **Cache:** Redis 7
- **ORM:** SQLAlchemy 2.0 (async)

### Infrastructure
- **Database:** Supabase (managed PostgreSQL with TimescaleDB)
- **Monitoring:** Prometheus + Grafana
- **CI/CD:** GitHub Actions
- **Error Tracking:** [FILL IN - Sentry, etc.]

---

## Key Technical Features

### Multi-Tenant Architecture
- Row-Level Security (RLS) for data isolation
- Tenant context functions
- RBAC/ABAC for access control

### Time-Series Data
- TimescaleDB hypertables for listener events
- Continuous aggregates for analytics
- Time-based partitioning and retention

### Attribution Engine
- Multiple attribution models (first-touch, last-touch, linear, time-decay, position-based)
- Cross-platform tracking (podcast → website → purchase)
- Configurable attribution windows

### AI Framework
- Content analysis (episode transcripts)
- Predictive analytics (audience growth, engagement)
- Anomaly detection (unusual patterns)

### Workflow Engine
- Event-driven automation
- Campaign lifecycle management
- Report generation (async)

---

## Scalability

### Current Capacity
- **Database:** Supabase Pro (8GB RAM, 250GB storage)
- **Backend:** Fly.io (scales horizontally)
- **Frontend:** Vercel (global CDN, auto-scaling)

### Scaling Path
- **Database:** Supabase Team tier → Self-hosted Postgres
- **Backend:** Multiple instances → Kubernetes
- **Frontend:** Vercel Pro → Enterprise

**Limits:** [FILL IN - Current limits, scaling triggers]

---

## Security

### Authentication
- JWT tokens with expiration
- OAuth2 support
- Multi-factor authentication (MFA) ready

### Authorization
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- API key management

### Data Protection
- Encryption at rest (Supabase default)
- Encryption in transit (HTTPS)
- Row-Level Security (RLS) for multi-tenant isolation
- Audit logs

### Compliance
- [FILL IN - GDPR, SOC 2, etc.]

---

## Performance

### API Response Times
- **Target:** <200ms P95
- **Current:** [FILL IN - Actual metrics]

### Database
- **Query Optimization:** Indexes on foreign keys, frequently queried columns
- **Caching:** Redis for expensive queries
- **Connection Pooling:** Configured for scalability

### Frontend
- **Bundle Size:** [FILL IN - Current size]
- **Load Time:** [FILL IN - Current metrics]
- **CDN:** Vercel global CDN

---

## Reliability

### Uptime
- **Target:** 99.9%+
- **Current:** [FILL IN - Actual uptime]

### Monitoring
- Health checks: `/health` endpoint
- Metrics: Prometheus + Grafana
- Error tracking: [FILL IN - Sentry, etc.]
- Alerts: [FILL IN - Alerting setup]

### Disaster Recovery
- **Backups:** Daily automated backups (Supabase)
- **Point-in-Time Recovery:** Available (Supabase Pro)
- **Rollback:** Deployment rollback procedures

---

## Development Velocity

### Codebase
- **Backend:** 200+ Python files
- **Frontend:** 70+ TypeScript/React files
- **Tests:** [FILL IN - Test coverage %]
- **Documentation:** Comprehensive docs

### Deployment
- **Frontend:** Automatic on push to `main` (Vercel)
- **Backend:** Manual deploy (Fly.io/Render) or CI/CD
- **Database Migrations:** Versioned, tested

### Team
- **Current:** [FILL IN - Team size]
- **Hiring:** [FILL IN - Planned hires]

---

## Technical Risks

### Risk 1: Database Scaling
- **Mitigation:** Supabase scales to Team tier, then self-hosted
- **Timeline:** [FILL IN - When scaling needed]

### Risk 2: Performance at Scale
- **Mitigation:** Caching, query optimization, horizontal scaling
- **Timeline:** [FILL IN - When optimization needed]

### Risk 3: Security
- **Mitigation:** Security audit, penetration testing
- **Timeline:** [FILL IN - When audit scheduled]

---

## Technical Differentiators

1. **TimescaleDB** - Optimized for time-series analytics at scale
2. **Multi-Attribution** - Multiple models with cross-platform tracking
3. **AI Framework** - Content analysis and predictive analytics
4. **Workflow Engine** - Event-driven automation
5. **Multi-Tenant** - Built for agencies/networks from day one

---

## Notes

- **Placeholder Values:** Marked with [FILL IN] - replace with real data
- **Technical Details:** See [`yc/YC_TECH_OVERVIEW.md`](../yc/YC_TECH_OVERVIEW.md) for more
- **Architecture:** See [`architecture/system-architecture.md`](../architecture/system-architecture.md) for diagrams

---

**See Also:**
- [`yc/YC_TECH_OVERVIEW.md`](../yc/YC_TECH_OVERVIEW.md) - Detailed tech overview
- [`docs/backend-strategy.md`](../docs/backend-strategy.md) - Backend architecture
- [`docs/frontend-hosting-strategy.md`](../docs/frontend-hosting-strategy.md) - Frontend hosting
