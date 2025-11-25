# Rollback Procedures

This document describes procedures for rolling back deployments, database migrations, and configuration changes.

## Overview

Rollback procedures are critical for maintaining system stability and quickly recovering from issues. This document covers:

1. Frontend rollback (Vercel)
2. Backend rollback (various providers)
3. Database migration rollback
4. Configuration rollback
5. Emergency procedures

---

## Frontend Rollback (Vercel)

### Automatic Rollback

Vercel automatically keeps previous deployments available for quick rollback.

### Manual Rollback via Dashboard

1. **Access Vercel Dashboard**
   - Go to https://vercel.com/dashboard
   - Select your project

2. **Find Previous Deployment**
   - Navigate to "Deployments" tab
   - Find the deployment you want to rollback to
   - Click on the deployment

3. **Promote to Production**
   - Click "..." menu
   - Select "Promote to Production"
   - Confirm the rollback

### Rollback via CLI

```bash
# List deployments
vercel ls

# Promote specific deployment
vercel promote <deployment-url> --prod
```

### Rollback via GitHub Actions

If using GitHub Actions, you can trigger a rollback by:
1. Finding the previous successful deployment commit
2. Creating a new deployment from that commit
3. Or manually triggering the deployment workflow

---

## Backend Rollback

### Fly.io Rollback

```bash
# List releases
fly releases

# Rollback to specific release
fly releases rollback <release-id>

# Or rollback to previous release
fly releases rollback
```

### Kubernetes Rollback

```bash
# View deployment history
kubectl rollout history deployment/backend

# Rollback to previous revision
kubectl rollout undo deployment/backend

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=<revision-number>

# Check rollout status
kubectl rollout status deployment/backend
```

### Render Rollback

1. **Via Dashboard**
   - Go to Render dashboard
   - Select your service
   - Navigate to "Events" tab
   - Find previous successful deployment
   - Click "Redeploy"

2. **Via Git**
   - Revert the problematic commit
   - Push to trigger new deployment

---

## Database Migration Rollback

### Using Migration Manager

```bash
# Rollback last migration
python scripts/migration-manager.py rollback --count=1

# Rollback multiple migrations
python scripts/migration-manager.py rollback --count=3

# Check migration status
python scripts/migration-manager.py status
```

### Manual Rollback

1. **Identify Migration to Rollback**
   ```sql
   SELECT version, name, applied_at 
   FROM schema_migrations 
   ORDER BY applied_at DESC;
   ```

2. **Execute Down Migration**
   - Find the migration file
   - Locate the DOWN MIGRATION section
   - Execute the SQL manually:
   ```sql
   BEGIN;
   -- Down migration SQL here
   COMMIT;
   ```

3. **Remove Migration Record**
   ```sql
   DELETE FROM schema_migrations WHERE version = '<version>';
   ```

### Emergency Rollback

If migration causes critical issues:

1. **Stop Application**
   - Prevent further data corruption
   - Stop accepting new requests

2. **Restore from Backup**
   ```bash
   # Restore database backup
   psql -U postgres -d podcast_analytics < backup_<timestamp>.sql
   ```

3. **Verify Data Integrity**
   ```bash
   # Run schema validation
   ts-node scripts/db-validate-schema.ts
   ```

4. **Restart Application**
   - Start application
   - Verify functionality
   - Monitor for issues

---

## Configuration Rollback

### Environment Variables

1. **Vercel (Frontend)**
   - Go to Vercel dashboard
   - Project Settings → Environment Variables
   - Restore previous values
   - Redeploy

2. **Backend Provider**
   - Access provider dashboard
   - Restore environment variables
   - Restart service

3. **Local Development**
   ```bash
   # Restore from backup
   cp .env.backup .env
   ```

### Feature Flags

```bash
# Disable problematic feature flag
python -c "
from src.features.flags import FeatureFlagService
import asyncio
import asyncpg

async def disable_flag():
    conn = await asyncpg.connect('DATABASE_URL')
    service = FeatureFlagService(conn)
    await service.set_flag('feature_name', False)
    await conn.close()

asyncio.run(disable_flag())
"
```

---

## Emergency Procedures

### Complete System Rollback

If critical issues affect the entire system:

1. **Immediate Actions**
   - Stop all deployments
   - Put system in maintenance mode
   - Notify team

2. **Assess Impact**
   - Identify affected components
   - Determine root cause
   - Assess data integrity

3. **Rollback Components
   - Frontend: Rollback to last known good deployment
   - Backend: Rollback to previous version
   - Database: Restore from backup if needed

4. **Verify System**
   - Run smoke tests
   - Verify critical paths
   - Check data integrity

5. **Monitor**
   - Watch error rates
   - Monitor performance
   - Check user reports

### Communication Plan

During rollback:

1. **Internal Communication**
   - Notify team immediately
   - Create incident ticket
   - Document rollback steps

2. **User Communication** (if needed)
   - Update status page
   - Send user notification
   - Provide timeline

3. **Post-Rollback**
   - Document incident
   - Root cause analysis
   - Prevent future occurrences

---

## Rollback Checklist

### Pre-Rollback

- [ ] Identify issue and root cause
- [ ] Determine rollback scope
- [ ] Verify backup availability
- [ ] Notify team
- [ ] Prepare rollback commands

### During Rollback

- [ ] Stop new deployments
- [ ] Execute rollback steps
- [ ] Verify each step
- [ ] Monitor system health

### Post-Rollback

- [ ] Verify system functionality
- [ ] Run smoke tests
- [ ] Check error rates
- [ ] Monitor performance
- [ ] Document incident
- [ ] Plan fix for original issue

---

## Prevention

### Best Practices

1. **Always Test Migrations**
   - Test on staging first
   - Verify rollback procedures
   - Test with production-like data

2. **Use Feature Flags**
   - Gradual rollout
   - Quick disable if issues
   - A/B testing

3. **Maintain Backups**
   - Regular database backups
   - Configuration backups
   - Code backups (Git)

4. **Monitor Deployments**
   - Watch error rates
   - Monitor performance
   - Set up alerts

5. **Document Changes**
   - Document all changes
   - Keep changelog
   - Document rollback procedures

---

## Testing Rollback Procedures

### Regular Testing

Test rollback procedures regularly:

1. **Monthly**
   - Test database migration rollback
   - Test configuration rollback
   - Verify backup restoration

2. **Quarterly**
   - Full system rollback drill
   - Test emergency procedures
   - Review and update procedures

### Rollback Drill Checklist

- [ ] Schedule drill with team
- [ ] Set up test environment
- [ ] Execute rollback steps
- [ ] Verify success
- [ ] Document learnings
- [ ] Update procedures

---

## Tools and Scripts

### Migration Manager

```bash
# Status
python scripts/migration-manager.py status

# Rollback
python scripts/migration-manager.py rollback --count=1
```

### Database Backup

```bash
# Create backup
make db-backup

# Restore backup
make db-restore FILE=backup.sql
```

### Health Checks

```bash
# Check system health
make health

# Check frontend
make health-frontend
```

---

## Support Contacts

- **Infrastructure:** [Team Contact]
- **Database:** [DBA Contact]
- **On-Call:** [On-Call Engineer]

---

**Last Updated:** 2024-12-XX  
**Review Frequency:** Quarterly
