# Tech Due Diligence Checklist

**Minimal but sharp checklist for technical readiness**

---

## Tests to Add Soonest

### Critical Path Tests

- [ ] **User signup → onboarding → first value**
  - File: `tests/e2e/test_onboarding_flow.py`
  - Covers: Registration, podcast connection, first analytics view

- [ ] **Campaign creation → attribution tracking**
  - File: `tests/e2e/test_campaign_attribution.py`
  - Covers: Campaign setup, tracking URL generation, event capture

- [ ] **Multi-tenant isolation**
  - File: `tests/integration/test_tenant_isolation.py`
  - Covers: RLS policies, cross-tenant data access prevention

- [ ] **Database migrations**
  - File: `tests/integration/test_migrations.py`
  - Covers: Migration up/down, data integrity

**Priority:** HIGH (before production launch)

---

## Security Hotspots to Fix

### Authentication & Authorization

- [ ] **JWT token expiration**
  - Verify: Tokens expire correctly
  - File: `src/api/auth.py`
  - Risk: Stolen tokens valid indefinitely

- [ ] **Rate limiting**
  - Verify: API rate limits enforced
  - File: `src/api/middleware.py` (if exists)
  - Risk: DDoS, abuse

- [ ] **SQL injection**
  - Verify: All queries use parameterized statements
  - File: `src/database/` (all files)
  - Risk: Data breach

- [ ] **CORS configuration**
  - Verify: Only allowed origins
  - File: `src/main.py` or config
  - Risk: CSRF attacks

### Data Protection

- [ ] **Secrets in environment**
  - Verify: No secrets in code/logs
  - File: All files
  - Risk: Credential exposure

- [ ] **Encryption at rest**
  - Verify: Database encryption enabled (Supabase default)
  - Risk: Data breach

- [ ] **Encryption in transit**
  - Verify: HTTPS enforced in production
  - Risk: Man-in-the-middle

- [ ] **Row-Level Security (RLS)**
  - Verify: RLS policies tested
  - File: `db/migrations/99999999999999_master_schema.sql`
  - Risk: Cross-tenant data access

**Priority:** HIGH (before production launch)

---

## Infrastructure & Data Risks

### Database

- [ ] **Backup strategy**
  - Verify: Automated backups configured (Supabase default)
  - Risk: Data loss

- [ ] **Migration rollback**
  - Verify: Can rollback migrations
  - File: `scripts/db-migrate-hosted.sh`
  - Risk: Failed migrations break production

- [ ] **Connection pooling**
  - Verify: Connection pool configured
  - File: `src/database/connection.py`
  - Risk: Database exhaustion

- [ ] **TimescaleDB retention**
  - Verify: Retention policies set for time-series data
  - File: `db/migrations/99999999999999_master_schema.sql`
  - Risk: Unbounded storage growth

### Infrastructure

- [ ] **Health checks**
  - Verify: `/health` endpoint works
  - File: `src/main.py`
  - Risk: Unhealthy deployments

- [ ] **Graceful shutdown**
  - Verify: App handles SIGTERM
  - File: `src/main.py`
  - Risk: Data loss on restart

- [ ] **Error handling**
  - Verify: Errors logged, not exposed to users
  - File: `src/api/` (all files)
  - Risk: Information disclosure

- [ ] **Monitoring**
  - Verify: Error tracking configured (Sentry, etc.)
  - Risk: Unknown production issues

**Priority:** MEDIUM (before scale)

---

## Performance Risks

### Database

- [ ] **Query performance**
  - Verify: Slow queries identified
  - File: `src/analytics/` (all files)
  - Risk: Slow user experience

- [ ] **Index coverage**
  - Verify: Indexes on foreign keys, frequently queried columns
  - File: `db/migrations/99999999999999_master_schema.sql`
  - Risk: Slow queries

- [ ] **N+1 queries**
  - Verify: Eager loading where needed
  - File: `src/api/` (all files)
  - Risk: Slow API responses

### API

- [ ] **Response times**
  - Verify: API responses < 200ms (p95)
  - Risk: Poor UX

- [ ] **Caching**
  - Verify: Redis caching for expensive queries
  - File: `src/cache/` (if exists)
  - Risk: Unnecessary database load

- [ ] **Pagination**
  - Verify: List endpoints paginated
  - File: `src/api/` (all files)
  - Risk: Memory issues, slow responses

**Priority:** MEDIUM (before scale)

---

## Quick Wins (Low Effort, High Impact)

1. **Add health check endpoint** ✅ (already exists)
2. **Set up error tracking** (Sentry - 30 minutes)
3. **Add request logging** (structured logs - 1 hour)
4. **Configure rate limiting** (if not done - 1 hour)
5. **Add database query logging** (slow query log - 30 minutes)

---

## Testing Strategy

### Unit Tests
- **Coverage target:** 70%+ for critical paths
- **Focus:** Business logic, utilities
- **Run:** `pytest tests/unit/`

### Integration Tests
- **Coverage target:** All API endpoints
- **Focus:** Database interactions, auth flows
- **Run:** `pytest tests/integration/`

### E2E Tests
- **Coverage target:** Critical user flows
- **Focus:** Signup → value, campaign → attribution
- **Run:** `pytest tests/e2e/`

---

## Security Audit Checklist

- [ ] Run `pip-audit` for Python dependencies
- [ ] Run `npm audit` for Node.js dependencies
- [ ] Review OWASP Top 10 vulnerabilities
- [ ] Test authentication flows
- [ ] Test authorization (RBAC/ABAC)
- [ ] Review environment variable usage
- [ ] Check for hardcoded secrets
- [ ] Review CORS configuration
- [ ] Test rate limiting
- [ ] Review error messages (no info disclosure)

**See:** [`docs/SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md) for detailed checklist

---

## Risk Summary

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| No E2E tests | HIGH | Add critical path tests | ⚠️ TODO |
| Security audit | HIGH | Run security checklist | ⚠️ TODO |
| No monitoring | MEDIUM | Set up Sentry/alerts | ⚠️ TODO |
| Performance | MEDIUM | Add caching, optimize queries | ⚠️ TODO |
| Backup strategy | LOW | Verify Supabase backups | ✅ Default |

---

**Next Steps:**
1. Add critical path E2E tests (Week 1)
2. Run security audit (Week 1)
3. Set up monitoring (Week 2)
4. Performance optimization (Week 3)

---

**See also:**
- [`docs/PROJECT_READINESS_REPORT.md`](PROJECT_READINESS_REPORT.md) - Overall readiness
- [`docs/SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md) - Security details
