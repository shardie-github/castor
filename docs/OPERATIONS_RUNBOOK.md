# Operations Runbook: Podcast Analytics & Sponsorship Platform

**Last Updated:** 2024-12-19  
**Version:** 1.0  
**Owner:** DevOps Team

## Purpose

This runbook provides step-by-step procedures for common operational tasks, incident response, and maintenance. Use this for:
- On-call engineers responding to incidents
- Routine maintenance procedures
- Disaster recovery scenarios
- System troubleshooting

---

## Table of Contents

1. [Incident Response](#incident-response)
2. [Monitoring & Alerts](#monitoring--alerts)
3. [Database Operations](#database-operations)
4. [Deployment Procedures](#deployment-procedures)
5. [Backup & Recovery](#backup--recovery)
6. [Performance Troubleshooting](#performance-troubleshooting)
7. [Security Incidents](#security-incidents)

---

## 1. INCIDENT RESPONSE

### 1.1 Incident Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **P0 - Critical** | System down, data loss, security breach | 15 minutes | Database corruption, full outage |
| **P1 - High** | Major feature broken, significant degradation | 1 hour | API 50% error rate, payment processing down |
| **P2 - Medium** | Minor feature broken, moderate impact | 4 hours | Report generation slow, single integration failing |
| **P3 - Low** | Cosmetic issue, low impact | Next business day | UI typo, non-critical feature |

### 1.2 Incident Response Process

#### Step 1: Acknowledge and Assess
1. **Acknowledge alert** in monitoring system (PagerDuty, Opsgenie)
2. **Check status page** for known issues
3. **Assess severity** based on impact:
   - How many users affected?
   - What functionality is broken?
   - Is data at risk?

#### Step 2: Investigate
1. **Check monitoring dashboards:**
   - Grafana: System health, error rates, latency
   - Prometheus: Metrics, alert status
   - Logs: Recent errors, exceptions

2. **Review recent changes:**
   ```bash
   # Check recent deployments
   git log --oneline --since="2 hours ago"
   
   # Check recent configuration changes
   kubectl get events --sort-by='.lastTimestamp' | tail -20
   ```

3. **Check system resources:**
   ```bash
   # CPU, memory, disk usage
   kubectl top nodes
   kubectl top pods
   
   # Database connections
   psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

#### Step 3: Mitigate
1. **Immediate actions:**
   - Restart failing services if safe
   - Scale up if resource-constrained
   - Enable maintenance mode if needed

2. **Document actions taken:**
   - Update incident ticket
   - Log commands executed
   - Note any side effects

#### Step 4: Resolve and Verify
1. **Verify fix:**
   - Check monitoring dashboards
   - Test affected functionality
   - Confirm with users if possible

2. **Post-incident:**
   - Write post-mortem within 48 hours
   - Update runbook with lessons learned
   - Create follow-up tasks

### 1.3 Common Incidents

#### Database Connection Pool Exhausted

**Symptoms:**
- High error rate: "too many connections"
- API timeouts
- Database connection wait time > 1s

**Investigation:**
```bash
# Check active connections
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check connection pool settings
kubectl get configmap api-config -o yaml | grep -i pool

# Check for long-running queries
psql -c "SELECT pid, now() - query_start as duration, query 
         FROM pg_stat_activity 
         WHERE state = 'active' AND now() - query_start > interval '30 seconds';"
```

**Mitigation:**
1. **Kill long-running queries** (if safe):
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE pid IN (SELECT pid FROM pg_stat_activity 
                 WHERE state = 'active' 
                 AND now() - query_start > interval '5 minutes');
   ```

2. **Increase connection pool size:**
   ```yaml
   # Update deployment config
   env:
     - name: DB_POOL_MAX_SIZE
       value: "50"
   ```

3. **Restart application** to apply new pool size

**Prevention:**
- Add query timeouts (10s read, 30s write)
- Monitor pool utilization, alert at 80%
- Review and optimize slow queries

---

#### High Error Rate (>5%)

**Symptoms:**
- Error rate > 5% in monitoring
- User reports of failures
- Increased support tickets

**Investigation:**
```bash
# Check error logs
kubectl logs -l app=api --since=10m | grep -i error | tail -50

# Check error rates by endpoint
# Query Prometheus:
# rate(api_errors_total[5m]) / rate(api_requests_total[5m])

# Check recent deployments
git log --oneline --since="1 hour ago"
```

**Mitigation:**
1. **Identify error pattern:**
   - Check error logs for common exception types
   - Check if errors are from specific endpoints
   - Check if errors correlate with recent deployment

2. **Rollback if recent deployment:**
   ```bash
   # Rollback to previous version
   kubectl rollout undo deployment/api-service
   
   # Verify rollback
   kubectl rollout status deployment/api-service
   ```

3. **If not deployment-related:**
   - Check external dependencies (Stripe, SendGrid, AI APIs)
   - Check database health
   - Check infrastructure (CPU, memory, disk)

**Prevention:**
- Canary deployments for major changes
- Gradual rollout (10% → 50% → 100%)
- Automated rollback on error rate spike

---

#### External API Failure (Stripe, SendGrid, AI Providers)

**Symptoms:**
- Payment processing failures
- Email delivery failures
- AI feature timeouts

**Investigation:**
```bash
# Check external API status pages
# Stripe: https://status.stripe.com
# SendGrid: https://status.sendgrid.com
# OpenAI: https://status.openai.com

# Check application logs for API errors
kubectl logs -l app=api --since=10m | grep -i "stripe\|sendgrid\|openai" | grep -i error
```

**Mitigation:**
1. **Check API status pages** for known outages
2. **Verify API keys** are valid and not expired
3. **Check rate limits:**
   ```bash
   # Check rate limit headers in logs
   kubectl logs -l app=api | grep -i "rate limit\|429"
   ```

4. **Implement fallback:**
   - Queue failed requests for retry
   - Use fallback provider if available
   - Show user-friendly error message

**Prevention:**
- Implement retry logic with exponential backoff
- Use circuit breaker pattern
- Monitor external API health

---

## 2. MONITORING & ALERTS

### 2.1 Key Metrics to Monitor

#### Application Metrics
- **Error Rate:** `rate(api_errors_total[5m]) / rate(api_requests_total[5m])`
  - Alert if > 1%
- **Latency (p95):** `histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))`
  - Alert if > 1s
- **Request Rate:** `rate(api_requests_total[5m])`
  - Alert if > 2x normal (possible DDoS)

#### Infrastructure Metrics
- **CPU Usage:** `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
  - Alert if > 80%
- **Memory Usage:** `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
  - Alert if > 85%
- **Disk Usage:** `(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100`
  - Alert if > 80%

#### Database Metrics
- **Connection Pool Utilization:** `db_connections_active / db_connections_max`
  - Alert if > 80%
- **Query Duration (p95):** `histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))`
  - Alert if > 1s
- **Database Size:** `pg_database_size_bytes`
  - Alert if > 80% of quota

### 2.2 Alert Configuration

#### Critical Alerts (PagerDuty)
```yaml
# prometheus/alerts.yml
groups:
  - name: critical
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate is {{ $value | humanizePercentage }}"
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        annotations:
          summary: "P95 latency is {{ $value }}s"
```

#### Warning Alerts (Email/Slack)
```yaml
  - name: warnings
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 15m
        annotations:
          summary: "CPU usage is {{ $value }}%"
```

### 2.3 Dashboard Access

- **Grafana:** https://grafana.yourdomain.com
  - Login: `admin` / Check password manager
  - Dashboards:
    - System Health
    - API Performance
    - Business Metrics
    - Database Performance

- **Prometheus:** https://prometheus.yourdomain.com
  - Query interface for ad-hoc investigations

---

## 3. DATABASE OPERATIONS

### 3.1 Backup Procedures

#### Daily Backup (Automated)
```bash
# Backup script runs daily at 2 AM UTC
# Location: scripts/backup_daily.sh

# Manual backup
kubectl exec -it postgres-pod -- pg_dump -U postgres podcast_analytics | gzip > backup_$(date +%Y%m%d).sql.gz

# Verify backup
gunzip -c backup_20241219.sql.gz | head -20
```

#### Backup Verification
```bash
# Weekly test restore (automated)
# Restore to staging database
gunzip -c backup_20241219.sql.gz | psql -h staging-db -U postgres podcast_analytics_staging

# Verify data integrity
psql -h staging-db -c "SELECT count(*) FROM users;"
psql -h staging-db -c "SELECT count(*) FROM campaigns;"
```

### 3.2 Database Migrations

#### Running Migrations
```bash
# 1. Backup database first
./scripts/backup_daily.sh

# 2. Review migration file
cat migrations/019_new_feature.sql

# 3. Test on staging
psql -h staging-db -f migrations/019_new_feature.sql

# 4. Run on production (during maintenance window)
kubectl exec -it postgres-pod -- psql -U postgres -d podcast_analytics -f /migrations/019_new_feature.sql

# 5. Verify migration
psql -c "\d new_table"  # Check new table exists
```

#### Rollback Procedure
```bash
# If migration fails, rollback:
# 1. Check if rollback script exists
ls migrations/019_new_feature_rollback.sql

# 2. Run rollback
kubectl exec -it postgres-pod -- psql -U postgres -d podcast_analytics -f /migrations/019_new_feature_rollback.sql

# 3. Restore from backup if needed
gunzip -c backup_20241219.sql.gz | psql -U postgres podcast_analytics
```

### 3.3 Database Maintenance

#### Vacuum and Analyze
```bash
# Weekly maintenance (automated)
kubectl exec -it postgres-pod -- psql -U postgres -c "VACUUM ANALYZE;"

# Check table bloat
psql -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
         FROM pg_tables 
         WHERE schemaname = 'public' 
         ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

#### Connection Management
```bash
# Check active connections
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Kill idle connections (if needed)
psql -c "SELECT pg_terminate_backend(pid) 
         FROM pg_stat_activity 
         WHERE state = 'idle' 
         AND now() - state_change > interval '1 hour';"
```

---

## 4. DEPLOYMENT PROCEDURES

### 4.1 Pre-Deployment Checklist

- [ ] All tests passing (`pytest`, `npm test`)
- [ ] Code review approved
- [ ] Security scan passed (no high/critical vulnerabilities)
- [ ] Database migrations tested on staging
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready
- [ ] On-call engineer notified

### 4.2 Deployment Steps

#### Staging Deployment
```bash
# 1. Build and push image
docker build -t your-registry/api:staging-$(git rev-parse --short HEAD) .
docker push your-registry/api:staging-$(git rev-parse --short HEAD)

# 2. Update deployment
kubectl set image deployment/api-service api=your-registry/api:staging-abc123 -n staging

# 3. Monitor deployment
kubectl rollout status deployment/api-service -n staging

# 4. Verify health
curl https://staging-api.yourdomain.com/health
```

#### Production Deployment
```bash
# 1. Create release branch
git checkout -b release/v1.2.0
git push origin release/v1.2.0

# 2. Tag release
git tag v1.2.0
git push origin v1.2.0

# 3. Deploy to production (canary)
kubectl set image deployment/api-service-canary api=your-registry/api:v1.2.0 -n production

# 4. Monitor canary (10% traffic)
# Check error rates, latency for 15 minutes

# 5. If healthy, roll out to full
kubectl set image deployment/api-service api=your-registry/api:v1.2.0 -n production
kubectl rollout status deployment/api-service -n production

# 6. Verify production
curl https://api.yourdomain.com/health
```

### 4.3 Rollback Procedure

```bash
# Quick rollback to previous version
kubectl rollout undo deployment/api-service -n production

# Or rollback to specific version
kubectl rollout undo deployment/api-service --to-revision=5 -n production

# Verify rollback
kubectl rollout status deployment/api-service -n production
curl https://api.yourdomain.com/health
```

---

## 5. BACKUP & RECOVERY

### 5.1 Backup Locations

- **Daily backups:** S3 bucket `s3://backups-podcast-analytics/daily/`
- **Weekly backups:** S3 bucket `s3://backups-podcast-analytics/weekly/`
- **Monthly backups:** S3 bucket `s3://backups-podcast-analytics/monthly/`
- **Retention:** Daily (7 days), Weekly (4 weeks), Monthly (12 months)

### 5.2 Recovery Procedures

#### Point-in-Time Recovery
```bash
# 1. Identify target time
TARGET_TIME="2024-12-19 14:30:00"

# 2. Restore base backup
gunzip -c backup_20241219.sql.gz | psql -U postgres podcast_analytics_restore

# 3. Apply WAL logs up to target time
# (Requires WAL archiving enabled)
pg_basebackup -D /restore -Ft -z -P
```

#### Full Database Restore
```bash
# 1. Stop application
kubectl scale deployment/api-service --replicas=0 -n production

# 2. Drop existing database (CAREFUL!)
psql -c "DROP DATABASE podcast_analytics;"
psql -c "CREATE DATABASE podcast_analytics;"

# 3. Restore backup
gunzip -c backup_20241219.sql.gz | psql -U postgres podcast_analytics

# 4. Verify data
psql -c "SELECT count(*) FROM users;"
psql -c "SELECT count(*) FROM campaigns;"

# 5. Restart application
kubectl scale deployment/api-service --replicas=3 -n production
```

### 5.3 Disaster Recovery

#### RTO (Recovery Time Objective): 4 hours
#### RPO (Recovery Point Objective): 1 hour

**DR Procedure:**
1. **Assess damage:** Determine scope of data loss/corruption
2. **Choose recovery point:** Select backup closest to incident time
3. **Restore to DR environment:** Test restore first
4. **Verify data integrity:** Run data validation scripts
5. **Failover to DR:** Update DNS, routing
6. **Notify stakeholders:** Communicate recovery status

---

## 6. PERFORMANCE TROUBLESHOOTING

### 6.1 Slow API Endpoints

**Investigation:**
```bash
# Check slow endpoints in Prometheus
# Query: topk(10, histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])))

# Check application logs for slow queries
kubectl logs -l app=api | grep -i "slow\|timeout" | tail -50

# Check database slow query log
psql -c "SELECT pid, now() - query_start as duration, query 
         FROM pg_stat_activity 
         WHERE state = 'active' 
         AND now() - query_start > interval '1 second'
         ORDER BY duration DESC;"
```

**Mitigation:**
1. **Add database indexes:**
   ```sql
   CREATE INDEX CONCURRENTLY idx_campaigns_tenant_id ON campaigns(tenant_id);
   ```

2. **Optimize queries:**
   - Use EXPLAIN ANALYZE to identify bottlenecks
   - Add WHERE clause filters
   - Limit result sets

3. **Add caching:**
   - Cache frequently accessed data in Redis
   - Set appropriate TTLs

### 6.2 High Memory Usage

**Investigation:**
```bash
# Check memory usage
kubectl top pods | grep api-service

# Check for memory leaks
kubectl logs -l app=api | grep -i "memory\|oom" | tail -50
```

**Mitigation:**
1. **Increase memory limits:**
   ```yaml
   resources:
     limits:
       memory: "2Gi"
   ```

2. **Identify memory leaks:**
   - Use profiling tools (py-spy, memory_profiler)
   - Check for unbounded data structures

3. **Restart pods:**
   ```bash
   kubectl rollout restart deployment/api-service
   ```

---

## 7. SECURITY INCIDENTS

### 7.1 Suspected Breach

**Immediate Actions:**
1. **Isolate affected systems:**
   ```bash
   # Scale down affected service
   kubectl scale deployment/api-service --replicas=0
   ```

2. **Preserve evidence:**
   - Save logs
   - Take snapshots
   - Document timeline

3. **Notify security team:**
   - Escalate to security@company.com
   - Create incident ticket

### 7.2 Credential Compromise

**Actions:**
1. **Rotate compromised credentials:**
   - Database passwords
   - API keys
   - OAuth tokens

2. **Revoke access:**
   - Revoke compromised API keys
   - Invalidate user sessions
   - Lock affected accounts

3. **Investigate:**
   - Check access logs
   - Identify what was accessed
   - Notify affected users if PII accessed

### 7.3 DDoS Attack

**Symptoms:**
- Unusual traffic spike
- High error rate
- Service degradation

**Mitigation:**
1. **Enable DDoS protection:**
   - Cloud provider DDoS protection (AWS Shield, Cloudflare)
   - Rate limiting at edge

2. **Block malicious IPs:**
   ```bash
   # Add to firewall rules
   # Use WAF rules to block IPs
   ```

3. **Scale up resources:**
   ```bash
   kubectl scale deployment/api-service --replicas=10
   ```

---

## APPENDIX

### A. Useful Commands

```bash
# View logs
kubectl logs -l app=api --tail=100 -f

# Execute command in pod
kubectl exec -it api-pod -- /bin/bash

# Port forward for local access
kubectl port-forward svc/api-service 8000:8000

# Check resource usage
kubectl top nodes
kubectl top pods

# View events
kubectl get events --sort-by='.lastTimestamp'
```

### B. Contact Information

- **On-Call:** Check PagerDuty
- **Security Team:** security@company.com
- **DevOps Team:** devops@company.com
- **Engineering Lead:** engineering-lead@company.com

### C. External Resources

- **Status Page:** https://status.yourdomain.com
- **Documentation:** https://docs.yourdomain.com
- **Monitoring:** https://grafana.yourdomain.com
- **Logs:** https://logs.yourdomain.com

---

## Document Maintenance

- **Review Frequency:** Monthly
- **Update Trigger:** After incidents, major changes
- **Owner:** DevOps Team Lead
