# Security Checklist: Podcast Analytics & Sponsorship Platform

**Last Updated:** 2024-12-19  
**Version:** 1.0  
**Owner:** Security Team

## Purpose

This checklist ensures security best practices are implemented and maintained across the platform. Use this for:
- Pre-production deployment reviews
- Security audits
- Incident response preparation
- Compliance verification

---

## 1. AUTHENTICATION & AUTHORIZATION

### 1.1 Password Security
- [ ] **PASS-001:** Passwords hashed with bcrypt/argon2id (NOT SHA-256)
  - **Check:** `src/users/user_manager.py` uses `passlib[bcrypt]`
  - **Action:** Replace `_hash_password()` method, migrate existing passwords
  - **Priority:** CRITICAL

- [ ] **PASS-002:** Password policy enforced
  - Minimum 12 characters
  - Complexity requirements (uppercase, lowercase, number, special char)
  - Password strength meter in UI
  - **Check:** Frontend validation + backend enforcement

- [ ] **PASS-003:** Password reset flow secure
  - Reset tokens expire after 1 hour
  - Tokens single-use only
  - Rate limit: max 3 reset requests per email per hour
  - **Check:** `src/api/auth.py` reset endpoint

- [ ] **PASS-004:** No password in logs or error messages
  - **Check:** Search codebase for password logging
  - **Action:** Ensure passwords never logged, even in debug mode

### 1.2 Multi-Factor Authentication (MFA)
- [ ] **MFA-001:** MFA enforced for admin users
  - **Check:** `src/security/auth/mfa.py` is required for ADMIN role
  - **Action:** Add middleware to enforce MFA on admin endpoints

- [ ] **MFA-002:** MFA backup codes generated
  - Store encrypted backup codes
  - Allow user to regenerate codes
  - **Check:** Backup code generation in MFA module

- [ ] **MFA-003:** MFA rate limiting
  - Max 5 failed MFA attempts per 15 minutes
  - Lock account after 10 failed attempts
  - **Check:** Rate limiting in MFA verification

### 1.3 Session Management
- [ ] **SESS-001:** JWT tokens use strong secret
  - Secret length >= 64 bytes
  - Secret stored in secret manager (not env file)
  - **Check:** `JWT_SECRET` environment variable validation

- [ ] **SESS-002:** Token expiration reasonable
  - Access tokens: 15 minutes
  - Refresh tokens: 7 days
  - **Check:** Token expiration in `user_manager.py:171`

- [ ] **SESS-003:** Token revocation implemented
  - Revoke on logout
  - Revoke all tokens on password change
  - Revoke on suspicious activity
  - **Check:** `revoke_session()` method usage

- [ ] **SESS-004:** Secure token storage
  - Tokens stored in httpOnly cookies (preferred) or secure localStorage
  - Never store tokens in regular cookies or URL parameters
  - **Check:** Frontend token storage strategy

### 1.4 API Keys
- [ ] **API-001:** API keys hashed before storage
  - **Check:** `src/security/auth/api_key_manager.py:157` uses SHA-256
  - **Action:** Consider stronger hashing (bcrypt) for API keys

- [ ] **API-002:** API key scoping implemented
  - Read-only vs read-write vs admin scopes
  - Resource-level scoping (e.g., specific campaigns)
  - **Check:** API key permissions in database schema

- [ ] **API-003:** API key rotation
  - Expiration dates enforced
  - Rotation workflow for users
  - **Check:** API key expiration in schema

- [ ] **API-004:** API key rate limiting
  - Per-key rate limits (default: 1000 req/hour)
  - IP whitelisting per key
  - **Check:** Rate limiting middleware for API keys

---

## 2. DATA PROTECTION

### 2.1 Encryption
- [ ] **ENC-001:** Encryption at rest enabled
  - Database encryption (PostgreSQL TDE or RDS encryption)
  - TimescaleDB encryption
  - Redis encryption (if storing sensitive data)
  - **Check:** Database configuration, cloud provider settings

- [ ] **ENC-002:** Encryption in transit enforced
  - TLS 1.2+ required for all connections
  - HTTPS only in production (no HTTP)
  - Database connections use SSL
  - **Check:** Application TLS configuration, database SSL settings

- [ ] **ENC-003:** Field-level encryption for PII
  - Encrypt email addresses, phone numbers
  - Encrypt API keys, OAuth tokens
  - **Check:** Application-level encryption for sensitive fields

### 2.2 Secret Management
- [ ] **SEC-001:** No secrets in code
  - No hardcoded passwords, API keys, tokens
  - **Check:** Code scan (GitGuardian, TruffleHog)
  - **Action:** Remove any hardcoded secrets

- [ ] **SEC-002:** Secrets in secret manager
  - AWS Secrets Manager / Parameter Store
  - HashiCorp Vault
  - Never in `.env` files committed to git
  - **Check:** `.gitignore` includes `.env`, `.env.*`

- [ ] **SEC-003:** Secret rotation implemented
  - Database passwords rotated quarterly
  - API keys rotated on compromise
  - JWT secrets rotated annually
  - **Check:** Rotation procedures documented

- [ ] **SEC-004:** Secret access logging
  - Log all secret access (audit trail)
  - Alert on unusual access patterns
  - **Check:** Secret manager access logs

### 2.3 Data Privacy
- [ ] **PRIV-001:** GDPR compliance
  - User data export endpoint (Article 15)
  - User data deletion endpoint (Article 17)
  - Consent tracking for data processing
  - **Check:** `src/api/users.py` export/delete endpoints

- [ ] **PRIV-002:** Data retention policy
  - Delete user data after account deletion + 30 days
  - Archive old data (>2 years) to cold storage
  - **Check:** Data retention implementation

- [ ] **PRIV-003:** PII handling documented
  - What PII is collected
  - How it's used
  - Who has access
  - **Check:** Privacy policy, data processing documentation

- [ ] **PRIV-004:** Data minimization
  - Only collect necessary data
  - Anonymize data when possible
  - **Check:** Data collection points, anonymization logic

---

## 3. API SECURITY

### 3.1 Input Validation
- [ ] **VAL-001:** All inputs validated
  - Use Pydantic models for request validation
  - Validate data types, ranges, formats
  - **Check:** All API endpoints use Pydantic models

- [ ] **VAL-002:** SQL injection prevention
  - All queries use parameterized placeholders (`$1, $2`)
  - Never use string concatenation for SQL
  - **Check:** Search codebase for SQL string formatting

- [ ] **VAL-003:** XSS prevention
  - Sanitize user input before display
  - Use React's built-in XSS protection
  - **Check:** Frontend input sanitization

- [ ] **VAL-004:** File upload security
  - Validate file types (whitelist)
  - Scan for malware
  - Store outside web root
  - **Check:** File upload endpoints (CSV import, etc.)

### 3.2 Rate Limiting
- [ ] **RATE-001:** Rate limiting enabled
  - Per-user rate limits (60 req/min default)
  - Per-IP rate limits for unauthenticated endpoints
  - Per-API-key rate limits
  - **Check:** `src/security/api_security.py` rate limiting

- [ ] **RATE-002:** Rate limit headers returned
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
  - **Check:** Rate limit middleware response headers

- [ ] **RATE-003:** DDoS protection
  - Cloud provider DDoS protection enabled
  - Rate limiting at edge (Cloudflare, AWS WAF)
  - **Check:** Infrastructure configuration

### 3.3 CORS & Headers
- [ ] **CORS-001:** CORS configured correctly
  - Only allow specific origins (no wildcard in production)
  - Credentials only allowed for trusted origins
  - **Check:** `src/config/validation.py:53` CORS settings

- [ ] **CORS-002:** Security headers set
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000`
  - `Content-Security-Policy` configured
  - **Check:** Security middleware headers

### 3.4 API Authentication
- [ ] **AUTH-001:** All endpoints require authentication
  - Except public endpoints (health, docs)
  - **Check:** All routes have auth middleware

- [ ] **AUTH-002:** Token validation on every request
  - Verify JWT signature and expiration
  - Check token revocation list
  - **Check:** Auth middleware implementation

- [ ] **AUTH-003:** Authorization checks
  - RBAC enforced on all endpoints
  - Resource-level permissions checked
  - **Check:** Permission checks in endpoints

---

## 4. INFRASTRUCTURE SECURITY

### 4.1 Network Security
- [ ] **NET-001:** Firewall rules configured
  - Only necessary ports open
  - Database not exposed to internet
  - **Check:** Cloud provider security groups, firewall rules

- [ ] **NET-002:** VPC/network isolation
  - Application in private subnets
  - Database in isolated subnet
  - **Check:** Network architecture diagram

- [ ] **NET-003:** VPN/SSH access secured
  - SSH key-based authentication only
  - VPN required for admin access
  - **Check:** Access control configuration

### 4.2 Container Security
- [ ] **CONT-001:** Base images scanned
  - Use official, maintained images
  - Scan for vulnerabilities (Trivy, Snyk)
  - **Check:** Dockerfile base images, scan results

- [ ] **CONT-002:** Non-root user in containers
  - Run application as non-root user
  - **Check:** Dockerfile USER directive

- [ ] **CONT-003:** Secrets not in images
  - Use environment variables or secret mounts
  - Never bake secrets into images
  - **Check:** Dockerfile for secrets

- [ ] **CONT-004:** Minimal image size
  - Multi-stage builds
  - Remove unnecessary packages
  - **Check:** Docker image size, Dockerfile optimization

### 4.3 Database Security
- [ ] **DB-001:** Database access restricted
  - Only application servers can connect
  - No direct internet access
  - **Check:** Database network configuration

- [ ] **DB-002:** Database credentials rotated
  - Strong passwords (20+ chars, random)
  - Rotated quarterly
  - **Check:** Password rotation procedure

- [ ] **DB-003:** Database backups encrypted
  - Backup encryption enabled
  - Backup access restricted
  - **Check:** Backup configuration

- [ ] **DB-004:** Row-level security (RLS) enabled
  - Tenant isolation via RLS policies
  - **Check:** `migrations/003_multi_tenant_schema.sql` RLS policies

### 4.4 Monitoring & Logging
- [ ] **MON-001:** Security events logged
  - Failed login attempts
  - Permission denials
  - API key usage
  - **Check:** Security event logging implementation

- [ ] **MON-002:** Logs protected
  - Logs encrypted at rest
  - Log access restricted
  - **Check:** Log storage configuration

- [ ] **MON-003:** Security monitoring alerts
  - Alert on failed login spikes
  - Alert on permission denial spikes
  - Alert on unusual API usage
  - **Check:** Alert rules in monitoring system

---

## 5. DEPENDENCY SECURITY

### 5.1 Dependency Management
- [ ] **DEP-001:** Dependencies up to date
  - Regular updates (monthly)
  - Security patches applied immediately
  - **Check:** `requirements.txt`, `package.json` versions

- [ ] **DEP-002:** Vulnerability scanning
  - Scan dependencies (Snyk, Dependabot)
  - Fix high/critical vulnerabilities within 7 days
  - **Check:** Vulnerability scan results

- [ ] **DEP-003:** Dependency pinning
  - Pin exact versions in production
  - Use lock files (`requirements.lock`, `package-lock.json`)
  - **Check:** Lock files present and used

### 5.2 Third-Party Services
- [ ] **3RD-001:** Third-party API security reviewed
  - API keys stored securely
  - Rate limits understood and handled
  - **Check:** Integration security documentation

- [ ] **3RD-002:** Vendor security assessments
  - Review vendor security practices
  - Check SOC 2, ISO 27001 certifications
  - **Check:** Vendor security documentation

---

## 6. INCIDENT RESPONSE

### 6.1 Preparation
- [ ] **IR-001:** Incident response plan documented
  - Roles and responsibilities defined
  - Escalation procedures
  - **Check:** Incident response runbook exists

- [ ] **IR-002:** Security contacts defined
  - Security team contact info
  - On-call rotation
  - **Check:** Contact information documented

- [ ] **IR-003:** Backup and recovery tested
  - Regular backup restores tested
  - Recovery time objectives (RTO) defined
  - **Check:** Backup test results

### 6.2 Detection
- [ ] **IR-004:** Intrusion detection configured
  - Monitor for suspicious activity
  - Alert on anomalies
  - **Check:** IDS/IPS configuration

- [ ] **IR-005:** Log aggregation and analysis
  - Centralized log storage
  - Log analysis tools (ELK, Splunk)
  - **Check:** Log aggregation setup

---

## 7. COMPLIANCE

### 7.1 GDPR
- [ ] **GDPR-001:** Data processing legal basis documented
  - Consent, contract, legitimate interest
  - **Check:** Privacy policy, data processing documentation

- [ ] **GDPR-002:** User rights implemented
  - Right to access (data export)
  - Right to erasure (data deletion)
  - Right to rectification (data update)
  - **Check:** User rights endpoints

- [ ] **GDPR-003:** Data breach notification procedure
  - Detect breaches within 72 hours
  - Notify authorities and users
  - **Check:** Breach notification procedure

### 7.2 SOC 2 / ISO 27001
- [ ] **SOC-001:** Access controls documented
  - User access reviews quarterly
  - Access removal on termination
  - **Check:** Access control procedures

- [ ] **SOC-002:** Change management process
  - Code reviews required
  - Testing before production
  - **Check:** Change management process

---

## 8. CODE SECURITY

### 8.1 Secure Coding Practices
- [ ] **CODE-001:** Code reviews required
  - All code reviewed before merge
  - Security-focused reviews for sensitive changes
  - **Check:** PR review requirements

- [ ] **CODE-002:** Static analysis enabled
  - SAST tools (Bandit, Semgrep)
  - Fix high/critical findings
  - **Check:** CI/CD static analysis

- [ ] **CODE-003:** Secrets scanning in CI/CD
  - Scan commits for secrets
  - Block commits with secrets
  - **Check:** Pre-commit hooks, CI/CD secrets scanning

### 8.2 Error Handling
- [ ] **ERR-001:** Errors don't leak information
  - No stack traces in production
  - Generic error messages for users
  - **Check:** Error handling middleware

- [ ] **ERR-002:** Error logging secure
  - Log errors with context (no secrets)
  - Alert on error spikes
  - **Check:** Error logging implementation

---

## Pre-Production Security Review

Before deploying to production, ensure:

1. **All CRITICAL items completed**
2. **All HIGH items completed**
3. **Security audit performed**
4. **Penetration testing completed** (optional but recommended)
5. **Incident response plan tested**

---

## Regular Reviews

- **Weekly:** Review security alerts and incidents
- **Monthly:** Update dependencies, review access logs
- **Quarterly:** Full security audit, update this checklist
- **Annually:** Penetration testing, security training

---

## Sign-off

- [ ] **Security Lead:** _________________ Date: _______
- [ ] **Engineering Lead:** _________________ Date: _______
- [ ] **DevOps Lead:** _________________ Date: _______

---

## Notes

- This checklist should be reviewed and updated quarterly
- New security requirements should be added as they're identified
- All items should have clear owners and deadlines
