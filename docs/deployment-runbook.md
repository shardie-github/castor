# Deployment Runbook

**Last Updated:** 2024-12  
**Purpose:** Step-by-step guide for deploying to production

---

## Pre-Deployment Checklist

### 1. Code Review
- [ ] All PRs reviewed and approved
- [ ] Tests passing in CI
- [ ] No critical security issues
- [ ] Documentation updated

### 2. Environment Preparation
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets rotated (if needed)
- [ ] Backup created

### 3. Monitoring Setup
- [ ] Monitoring dashboards configured
- [ ] Alerts configured
- [ ] On-call rotation scheduled

---

## Deployment Steps

### Step 1: Pre-Deployment Verification

```bash
# Verify CI is passing
gh pr checks <pr-number>

# Verify migrations
./scripts/validate_migrations.py

# Check environment variables
python scripts/env-doctor.py
```

### Step 2: Database Migration

**⚠️ CRITICAL: Always run migrations before deploying code**

```bash
# Staging migration (automatic on merge to main)
# Or manual:
gh workflow run db-migrate.yml -f environment=staging

# Production migration (manual only)
gh workflow run db-migrate.yml -f environment=production
```

**Verify Migration:**
```bash
# Check migration status
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

### Step 3: Frontend Deployment

**Automatic (on push to main):**
- Frontend deploys automatically via `.github/workflows/frontend-ci-deploy.yml`
- Preview deployments created for PRs

**Manual (if needed):**
```bash
cd frontend
vercel deploy --prod
```

**Verify:**
- Check Vercel dashboard
- Visit production URL
- Run smoke tests

### Step 4: Backend Deployment

**Choose platform and deploy:**

#### Option A: Render
```bash
gh workflow run deploy-backend-render.yml -f environment=production
```

#### Option B: Fly.io
```bash
gh workflow run deploy-backend-fly.yml -f environment=production
```

#### Option C: Kubernetes
```bash
gh workflow run deploy-backend-k8s.yml -f environment=production
```

**Verify:**
```bash
# Health check
curl https://api.castor.app/health

# Smoke tests
pytest tests/smoke/test_production_smoke.py -v --asyncio-mode=auto
```

### Step 5: Post-Deployment Verification

```bash
# 1. Health checks
curl https://api.castor.app/health
curl https://castor.app/api/health

# 2. Smoke tests
export API_URL=https://api.castor.app
pytest tests/smoke/test_production_smoke.py -v

# 3. Check logs
# Render: Dashboard → Logs
# Fly.io: flyctl logs
# Kubernetes: kubectl logs -f deployment/podcast-analytics-api

# 4. Monitor metrics
# Check Prometheus/Grafana dashboards
# Verify error rates
# Check response times
```

---

## Rollback Procedures

### Frontend Rollback (Vercel)

```bash
# Via Vercel Dashboard:
# 1. Go to Deployments
# 2. Find previous deployment
# 3. Click "Promote to Production"

# Or via CLI:
cd frontend
vercel rollback
```

### Backend Rollback

#### Render
```bash
# Via Dashboard:
# 1. Go to Deployments
# 2. Find previous deployment
# 3. Click "Rollback"
```

#### Fly.io
```bash
flyctl releases list
flyctl releases rollback <release-id>
```

#### Kubernetes
```bash
kubectl rollout undo deployment/podcast-analytics-api
kubectl rollout status deployment/podcast-analytics-api
```

### Database Rollback

**⚠️ CRITICAL: Database rollbacks are complex**

1. **If migration failed:**
   ```bash
   # Restore from backup
   psql $DATABASE_URL < backup.sql
   ```

2. **If migration succeeded but code has issues:**
   - Deploy previous code version
   - Or create rollback migration

**⚠️ Always have backups before migrations**

---

## Emergency Procedures

### Service Down

1. **Check Status:**
   ```bash
   curl https://api.castor.app/health
   ```

2. **Check Logs:**
   - Render: Dashboard → Logs
   - Fly.io: `flyctl logs`
   - Kubernetes: `kubectl logs -f deployment/podcast-analytics-api`

3. **Check Database:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

4. **Rollback if needed:**
   - Follow rollback procedures above

### Database Issues

1. **Check Connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

2. **Check Health:**
   ```bash
   curl https://api.castor.app/health
   # Look for database check status
   ```

3. **Restore from Backup:**
   ```bash
   # If critical, restore from latest backup
   psql $DATABASE_URL < backup.sql
   ```

### High Error Rate

1. **Check Metrics:**
   - Prometheus: Error rate graph
   - Grafana: Error dashboard

2. **Check Logs:**
   - Look for error patterns
   - Check recent deployments

3. **Scale Up (if needed):**
   - Render: Increase instance size
   - Fly.io: Scale up
   - Kubernetes: Increase replicas

4. **Rollback if needed**

---

## Monitoring During Deployment

### Key Metrics to Watch

1. **Error Rate:**
   - Should stay below 1%
   - Alert if > 5%

2. **Response Time:**
   - p95 should stay below 500ms
   - Alert if > 1s

3. **Database Connections:**
   - Should stay within pool limits
   - Alert if connection errors

4. **Health Checks:**
   - Should return "healthy"
   - Alert if "unhealthy"

### Dashboards

- **Prometheus:** http://localhost:9090 (local) or configured URL
- **Grafana:** http://localhost:3000 (local) or configured URL
- **Vercel:** Dashboard → Analytics

---

## Communication

### During Deployment

1. **Notify Team:**
   - Slack: `#deployments` channel
   - Status: "Deploying to production"

2. **Monitor:**
   - Watch for errors
   - Check metrics
   - Be ready to rollback

3. **Post-Deployment:**
   - Verify everything works
   - Notify team: "Deployment successful"
   - Document any issues

### Incident Communication

1. **Immediate:**
   - Notify team in Slack
   - Update status page (if available)

2. **Investigation:**
   - Check logs
   - Review metrics
   - Identify root cause

3. **Resolution:**
   - Apply fix or rollback
   - Verify fix
   - Document incident

---

## Best Practices

1. **Always Test in Staging First**
   - Deploy to staging
   - Run smoke tests
   - Verify functionality

2. **Deploy During Low Traffic**
   - Avoid peak hours
   - Schedule deployments
   - Communicate schedule

3. **Have Rollback Plan**
   - Know how to rollback
   - Test rollback procedure
   - Keep backups

4. **Monitor Closely**
   - Watch metrics during deployment
   - Check logs
   - Be ready to act

5. **Document Everything**
   - Document deployment steps
   - Record issues
   - Update runbook

---

## Troubleshooting

### Common Issues

1. **Migration Fails:**
   - Check database connection
   - Verify migration file syntax
   - Check for conflicts

2. **Deployment Timeout:**
   - Check build logs
   - Verify dependencies
   - Check resource limits

3. **Health Check Fails:**
   - Check application logs
   - Verify database connection
   - Check Redis connection

4. **High Error Rate:**
   - Check recent changes
   - Review error logs
   - Consider rollback

---

## Related Documentation

- `docs/deploy-strategy.md` - Deployment strategy overview
- `docs/db-migrations-and-schema.md` - Database migration guide
- `docs/launch-readiness-report.md` - Pre-launch checklist
- `.github/workflows/deploy.yml` - Deployment workflow

---

**Documentation Generated By:** Unified Background Agent  
**Last Updated:** 2024-12
