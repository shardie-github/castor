# Incident Response Playbook

**Last Updated:** 2024-12  
**Purpose:** Enterprise-grade incident response procedures

---

## Incident Severity Levels

### P0 - Critical (Immediate Response)
- **Service completely down**
- **Data breach or security incident**
- **Complete data loss**
- **Response Time:** Immediate (< 5 minutes)

### P1 - High (Urgent)
- **Major feature broken**
- **Performance degradation (>50%)**
- **Partial data loss**
- **Response Time:** < 15 minutes

### P2 - Medium (Important)
- **Minor feature broken**
- **Performance degradation (10-50%)**
- **Non-critical errors**
- **Response Time:** < 1 hour

### P3 - Low (Normal)
- **Cosmetic issues**
- **Minor performance issues**
- **Non-user-facing errors**
- **Response Time:** < 4 hours

---

## Incident Response Process

### Phase 1: Detection & Triage (0-5 minutes)

1. **Detect Incident**
   - Monitoring alerts
   - User reports
   - Error tracking alerts
   - Health check failures

2. **Assess Severity**
   - Determine P0/P1/P2/P3
   - Check impact scope
   - Identify affected users/services

3. **Activate Response Team**
   - Page on-call engineer
   - Create incident channel
   - Notify stakeholders

### Phase 2: Investigation (5-30 minutes)

1. **Gather Information**
   ```bash
   # Check health endpoints
   curl https://api.castor.app/health
   
   # Check logs
   # Render: Dashboard → Logs
   # Fly.io: flyctl logs
   # Kubernetes: kubectl logs -f deployment/podcast-analytics-api
   
   # Check metrics
   # Prometheus: http://localhost:9090
   # Grafana: http://localhost:3000
   ```

2. **Identify Root Cause**
   - Review error logs
   - Check recent deployments
   - Review metrics/dashboards
   - Check external dependencies

3. **Document Findings**
   - Update incident channel
   - Document timeline
   - Note affected systems

### Phase 3: Mitigation (30-60 minutes)

1. **Immediate Actions**
   - **If deployment-related:** Rollback immediately
   - **If database-related:** Check backups, consider restore
   - **If external service:** Check status, implement fallback
   - **If resource exhaustion:** Scale up resources

2. **Short-term Fixes**
   - Apply hotfixes if needed
   - Restart services if needed
   - Clear caches if needed
   - Disable problematic features

3. **Monitor Recovery**
   - Watch health endpoints
   - Monitor error rates
   - Check user reports
   - Verify metrics returning to normal

### Phase 4: Resolution (1-4 hours)

1. **Implement Permanent Fix**
   - Root cause analysis
   - Design solution
   - Test solution
   - Deploy fix

2. **Verify Resolution**
   - Run smoke tests
   - Monitor metrics
   - Check user reports
   - Verify no regressions

3. **Communicate Resolution**
   - Update status page
   - Notify stakeholders
   - Post-mortem scheduled

### Phase 5: Post-Mortem (Within 48 hours)

1. **Incident Review**
   - Timeline reconstruction
   - Root cause analysis
   - Impact assessment
   - Response evaluation

2. **Action Items**
   - Identify improvements
   - Assign owners
   - Set deadlines
   - Track completion

3. **Documentation**
   - Write post-mortem
   - Update runbooks
   - Share learnings
   - Update monitoring/alerts

---

## Common Incident Scenarios

### Scenario 1: Service Down

**Symptoms:**
- Health check returns 503
- All requests failing
- No recent deployments

**Response:**
1. Check service status (Render/Fly.io/Kubernetes)
2. Check database connectivity
3. Check Redis connectivity
4. Review recent logs
5. Restart service if needed
6. Rollback if recent deployment

**Rollback Procedure:**
```bash
# Render
# Dashboard → Deployments → Rollback

# Fly.io
flyctl releases list
flyctl releases rollback <release-id>

# Kubernetes
kubectl rollout undo deployment/podcast-analytics-api
```

### Scenario 2: High Error Rate

**Symptoms:**
- Error rate > 5%
- User complaints
- Error tracking alerts

**Response:**
1. Check error tracking (Sentry/Rollbar)
2. Identify error patterns
3. Check recent deployments
4. Review error logs
5. Check database performance
6. Check external API status

**Mitigation:**
- Rollback if deployment-related
- Scale up if resource-related
- Fix code if bug-related
- Disable feature if feature-related

### Scenario 3: Database Issues

**Symptoms:**
- Database connection errors
- Slow queries
- Timeout errors

**Response:**
1. Check database status
2. Check connection pool
3. Review slow queries
4. Check database metrics
5. Consider read replica
6. Scale database if needed

**Mitigation:**
- Restart connection pool
- Kill long-running queries
- Scale database resources
- Enable read replicas

### Scenario 4: Performance Degradation

**Symptoms:**
- Response times > 2s
- High CPU/memory usage
- Timeout errors

**Response:**
1. Check resource usage
2. Review slow queries
3. Check cache hit rates
4. Review recent changes
5. Check external API performance

**Mitigation:**
- Scale up resources
- Optimize queries
- Increase cache
- Add CDN
- Optimize code

### Scenario 5: Security Incident

**Symptoms:**
- Unusual access patterns
- Failed authentication spikes
- WAF alerts
- Data breach indicators

**Response:**
1. **IMMEDIATE:** Isolate affected systems
2. Preserve logs/evidence
3. Notify security team
4. Review access logs
5. Check for data exfiltration
6. Notify affected users (if required)

**Mitigation:**
- Block suspicious IPs
- Rotate secrets
- Review access controls
- Patch vulnerabilities
- Notify authorities (if required)

---

## Communication Templates

### Incident Declaration

```
🚨 INCIDENT DECLARED

Severity: P0/P1/P2/P3
Status: Investigating/Mitigating/Resolved
Impact: [Description]
Affected Services: [List]
Incident Channel: #incident-[id]
On-Call: @engineer
```

### Status Update

```
📊 INCIDENT UPDATE

Status: [Current Status]
Timeline:
- [Time] - Incident detected
- [Time] - Root cause identified
- [Time] - Mitigation applied
- [Time] - Resolution in progress

Next Update: [Time]
```

### Resolution

```
✅ INCIDENT RESOLVED

Status: Resolved
Duration: [Duration]
Root Cause: [Description]
Resolution: [Description]
Post-Mortem: [Link]
```

---

## Escalation Procedures

### Escalation Path

1. **On-Call Engineer** (First responder)
2. **Engineering Lead** (If unresolved in 30 min)
3. **CTO/VP Engineering** (If P0/P1 unresolved in 1 hour)
4. **CEO** (If P0 data breach/security incident)

### When to Escalate

- **P0:** Escalate immediately if not resolved in 15 minutes
- **P1:** Escalate if not resolved in 1 hour
- **P2:** Escalate if not resolved in 4 hours
- **P3:** Escalate if not resolved in 24 hours

---

## Tools & Resources

### Monitoring
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Error Tracking: Sentry/Rollbar dashboard
- Uptime Monitoring: Status page

### Communication
- Incident Channel: #incidents
- Status Page: https://status.castor.app
- On-Call Schedule: PagerDuty/Opsgenie

### Documentation
- Runbooks: `docs/deployment-runbook.md`
- Architecture: `docs/ARCHITECTURE.md`
- API Docs: `docs/api.md`

---

## Post-Mortem Template

### Incident Summary
- **Title:** [Brief description]
- **Severity:** P0/P1/P2/P3
- **Duration:** [Start] to [End]
- **Impact:** [Users affected, revenue impact, etc.]

### Timeline
- [Time] - Incident detected
- [Time] - Investigation started
- [Time] - Root cause identified
- [Time] - Mitigation applied
- [Time] - Resolution completed

### Root Cause
[Detailed analysis]

### Impact
- Users affected: [Number]
- Revenue impact: [If applicable]
- Data impact: [If applicable]

### Resolution
[What was done to resolve]

### Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]

### Lessons Learned
[Key takeaways]

---

**Documentation Generated By:** Unified Background Agent  
**Last Updated:** 2024-12
