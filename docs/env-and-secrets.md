# Environment Variables & Secrets Management

**Last Updated:** 2024  
**Purpose:** Complete mapping of environment variables across local, CI, and hosting environments

---

## Overview

This document provides a comprehensive mapping of all environment variables required across the entire stack: **GitHub Secrets → Vercel Environment Variables → Supabase → Next.js Frontend → Python Backend → External Integrations**.

---

## Variable Categories

### 1. Public Variables (Client-Side Safe)

These variables are exposed to the browser and must be prefixed with `NEXT_PUBLIC_*` for Next.js.

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ | `http://localhost:8000` | Frontend API calls |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | ⚠️ Optional | - | Frontend Supabase client |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | ⚠️ Optional | - | Frontend Supabase client |
| `NEXT_PUBLIC_SITE_URL` | Site URL for metadata | ✅ | `https://castor.app` | Next.js metadata |

**Security Note:** Only variables prefixed with `NEXT_PUBLIC_*` are available in the browser. Never expose secrets or API keys in client-side code.

---

### 2. Database Variables (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `DATABASE_URL` | PostgreSQL connection string (recommended) | ✅ | - | Backend DB connection |
| `POSTGRES_HOST` | PostgreSQL host (fallback) | ⚠️ If no DATABASE_URL | `localhost` | Backend DB connection |
| `POSTGRES_PORT` | PostgreSQL port (fallback) | ⚠️ If no DATABASE_URL | `5432` | Backend DB connection |
| `POSTGRES_DATABASE` | Database name (fallback) | ⚠️ If no DATABASE_URL | `podcast_analytics` | Backend DB connection |
| `POSTGRES_USER` | Database user (fallback) | ⚠️ If no DATABASE_URL | `postgres` | Backend DB connection |
| `POSTGRES_PASSWORD` | Database password (fallback) | ⚠️ If no DATABASE_URL | `postgres` | Backend DB connection |
| `POSTGRES_READ_REPLICA_HOST` | Read replica host (optional) | ❌ | - | Backend read queries |
| `POSTGRES_READ_REPLICA_PORT` | Read replica port (optional) | ❌ | `5432` | Backend read queries |

**Format:** `DATABASE_URL=postgresql://user:password@host:port/database`

**Examples:**
- Local: `postgresql://postgres:postgres@localhost:5432/podcast_analytics`
- Supabase: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
- AWS RDS: `postgresql://user:password@rds-instance.region.rds.amazonaws.com:5432/database`

---

### 3. Redis Variables (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `REDIS_URL` | Redis connection string | ⚠️ If using Redis | - | Backend cache/sessions |
| `REDIS_HOST` | Redis host (fallback) | ⚠️ If no REDIS_URL | `localhost` | Backend cache/sessions |
| `REDIS_PORT` | Redis port (fallback) | ⚠️ If no REDIS_URL | `6379` | Backend cache/sessions |
| `REDIS_PASSWORD` | Redis password (fallback) | ❌ | - | Backend cache/sessions |

**Format:** `REDIS_URL=redis://:password@host:port` or `redis://host:port`

---

### 4. Security Variables (Private - Critical)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `JWT_SECRET` | JWT signing secret (min 32 chars) | ✅ | - | Backend auth |
| `ENCRYPTION_KEY` | Encryption key (min 32 chars) | ✅ | - | Backend encryption |

**⚠️ CRITICAL:** These must be strong, random secrets in production. Generate with:
```bash
openssl rand -base64 32
```

---

### 5. Supabase Variables (Private - Optional)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `SUPABASE_URL` | Supabase project URL | ⚠️ If using Supabase | - | Backend Supabase features |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | ⚠️ If using Supabase | - | Backend admin operations |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ⚠️ If using Supabase | - | Backend/client Supabase client |

**Note:** `DATABASE_URL` is still required even when using Supabase (it's the Postgres connection string).

---

### 6. External Service Variables (Private)

#### Payment Processing
| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `STRIPE_SECRET_KEY` | Stripe secret key | ⚠️ If using Stripe | - | Backend payments |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | ⚠️ If using Stripe | - | Frontend payments |

#### Email Service
| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `SENDGRID_API_KEY` | SendGrid API key | ⚠️ If using SendGrid | - | Backend email |

#### AWS Services
| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `AWS_ACCESS_KEY_ID` | AWS access key | ⚠️ If using AWS | - | Backend AWS services |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | ⚠️ If using AWS | - | Backend AWS services |
| `AWS_REGION` | AWS region | ⚠️ If using AWS | `us-east-1` | Backend AWS services |

#### Other Integrations
| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `SHOPIFY_API_KEY` | Shopify API key | ❌ | - | Backend Shopify integration |
| `SHOPIFY_API_SECRET` | Shopify API secret | ❌ | - | Backend Shopify integration |
| `WIX_API_KEY` | Wix API key | ❌ | - | Backend Wix integration |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | ❌ | - | Backend Google integration |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | ❌ | - | Backend Google integration |
| `OPENAI_API_KEY` | OpenAI API key | ❌ | - | Backend AI features |
| `ANTHROPIC_API_KEY` | Anthropic API key | ❌ | - | Backend AI features |

---

### 7. Application Configuration (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `ENVIRONMENT` | Environment name | ✅ | `development` | Backend config |
| `DEBUG` | Debug mode | ✅ | `true` | Backend logging |
| `API_URL` | Backend API URL (server-side) | ⚠️ | `http://localhost:8000` | Backend internal |
| `API_KEY` | API key (if using API key auth) | ❌ | - | Backend API auth |
| `API_SECRET_KEY` | API secret key | ❌ | - | Backend API auth |

---

### 8. CORS & Security Configuration (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | ✅ | `http://localhost:3000` | Backend CORS |
| `CORS_ALLOWED_METHODS` | Comma-separated allowed methods | ✅ | `GET,POST,PUT,DELETE,OPTIONS` | Backend CORS |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS | ✅ | `true` | Backend CORS |
| `CORS_MAX_AGE` | CORS preflight cache time | ✅ | `3600` | Backend CORS |
| `ENABLE_SECURITY_HEADERS` | Enable security headers | ✅ | `true` | Backend security |
| `FORCE_HTTPS` | Force HTTPS redirects | ⚠️ Production | `false` | Backend security |
| `HSTS_ENABLED` | Enable HSTS | ⚠️ Production | `false` | Backend security |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | ✅ | `true` | Backend rate limiting |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | ✅ | `60` | Backend rate limiting |
| `RATE_LIMIT_PER_HOUR` | Requests per hour | ✅ | `1000` | Backend rate limiting |
| `RATE_LIMIT_PER_DAY` | Requests per day | ✅ | `10000` | Backend rate limiting |
| `WAF_ENABLED` | Enable WAF | ⚠️ Production | `false` | Backend security |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | ✅ | `30` | Backend sessions |
| `SESSION_SECURE` | Secure session cookies | ⚠️ Production | `false` | Backend sessions |

---

### 9. Monitoring & Observability (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `PROMETHEUS_PORT` | Prometheus metrics port | ✅ | `9090` | Backend metrics |
| `GRAFANA_URL` | Grafana URL | ❌ | `http://localhost:3000` | Backend monitoring |

---

### 10. Feature Flags (Private)

| Variable | Description | Required | Default | Where Used |
|----------|-------------|----------|---------|------------|
| `ENABLE_ETL_CSV_UPLOAD` | Enable CSV upload ETL | ❌ | `false` | Backend features |
| `ENABLE_MATCHMAKING` | Enable sponsor matching | ❌ | `false` | Backend features |
| `ENABLE_IO_BOOKINGS` | Enable insertion orders | ❌ | `false` | Backend features |
| `ENABLE_DEAL_PIPELINE` | Enable deal pipeline | ❌ | `false` | Backend features |
| `ENABLE_NEW_DASHBOARD_CARDS` | Enable new dashboard | ❌ | `false` | Frontend features |
| `MATCHMAKING_ENABLED` | Enable matchmaking (alias) | ❌ | `false` | Backend features |
| `ENABLE_ORCHESTRATION` | Enable workflow engine | ❌ | `false` | Backend features |
| `ENABLE_MONETIZATION` | Enable monetization features | ❌ | `false` | Backend features |
| `ENABLE_AUTOMATION_JOBS` | Enable automation jobs | ❌ | `false` | Backend features |

---

## Environment-Specific Configurations

### Local Development

**File:** `.env` (create from `.env.example`)

**Required Variables:**
```bash
# Database (local Docker Compose)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics
REDIS_HOST=localhost
REDIS_PORT=6379

# Security (generate strong secrets)
JWT_SECRET=your-local-jwt-secret-min-32-chars
ENCRYPTION_KEY=your-local-encryption-key-min-32-chars

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000

# Environment
ENVIRONMENT=development
DEBUG=true
```

**Optional Variables:**
- Stripe test keys
- SendGrid API key (for email testing)
- Supabase credentials (if using Supabase locally)

---

### CI (GitHub Actions)

**Location:** GitHub Repository Secrets

**Required Secrets:**
- `PRODUCTION_DATABASE_URL` - Production database connection string
- `STAGING_DATABASE_URL` - Staging database connection string
- `PRODUCTION_REDIS_URL` - Production Redis connection string
- `STAGING_REDIS_URL` - Staging Redis connection string
- `JWT_SECRET` - JWT secret (same for staging/production or separate)
- `ENCRYPTION_KEY` - Encryption key (same for staging/production or separate)
- `VERCEL_TOKEN` - Vercel API token (for frontend deployment)
- `VERCEL_ORG_ID` - Vercel organization ID (optional)
- `VERCEL_PROJECT_ID` - Vercel project ID (optional)

**Optional Secrets:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL for frontend
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_API_URL` - Backend API URL for frontend
- `NEXT_PUBLIC_SITE_URL` - Site URL for frontend
- `STRIPE_SECRET_KEY` - Stripe secret key
- `SENDGRID_API_KEY` - SendGrid API key
- `CONTAINER_REGISTRY` - Docker registry URL
- `REGISTRY_USERNAME` - Docker registry username
- `REGISTRY_PASSWORD` - Docker registry password

---

### Vercel (Frontend Hosting)

**Location:** Vercel Project Settings → Environment Variables

**Required Variables (per environment):**

**Production:**
- `NEXT_PUBLIC_API_URL` - Production backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (if using)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (if using)
- `NEXT_PUBLIC_SITE_URL` - Production site URL

**Preview:**
- Same as production (or use staging URLs)

**Development:**
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL=http://localhost:3000`

**Note:** Vercel automatically injects these variables at build time. Variables prefixed with `NEXT_PUBLIC_*` are available in the browser.

---

### Supabase (Database Hosting)

**Location:** Supabase Dashboard → Project Settings → Database

**Connection String:**
- Available in Supabase dashboard
- Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
- Use as `DATABASE_URL` in backend

**Additional Variables:**
- `SUPABASE_URL` - Project URL (e.g., `https://[PROJECT-REF].supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (from API settings)
- `SUPABASE_ANON_KEY` - Anonymous key (from API settings)

---

### Backend Hosting (Render, Fly.io, AWS, etc.)

**Location:** Hosting platform environment variables

**Required Variables:**
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string (or `REDIS_HOST`/`REDIS_PORT`)
- `JWT_SECRET` - JWT signing secret
- `ENCRYPTION_KEY` - Encryption key
- `ENVIRONMENT` - `production` or `staging`
- `DEBUG` - `false` in production
- `CORS_ALLOWED_ORIGINS` - Comma-separated frontend URLs
- `API_URL` - Backend API URL (for internal use)

**Optional Variables:**
- All external service keys (Stripe, SendGrid, AWS, etc.)
- Feature flags
- Monitoring configuration

---

## Variable Mapping Summary

### GitHub Secrets → CI Workflows

| GitHub Secret | Used In | Purpose |
|---------------|---------|---------|
| `PRODUCTION_DATABASE_URL` | `deploy.yml` | Production DB migrations |
| `STAGING_DATABASE_URL` | `deploy-staging.yml` | Staging DB migrations |
| `VERCEL_TOKEN` | `deploy.yml`, `frontend-ci-deploy.yml` | Frontend deployment |
| `NEXT_PUBLIC_API_URL` | `frontend-ci-deploy.yml` | Frontend build |

### Vercel Variables → Frontend Build

| Vercel Variable | Used In | Purpose |
|-----------------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `next.config.js`, frontend code | API endpoint |
| `NEXT_PUBLIC_SUPABASE_URL` | `next.config.js`, Supabase client | Supabase endpoint |
| `NEXT_PUBLIC_SITE_URL` | `app/layout.tsx` | Site metadata |

### Backend Hosting → Backend Runtime

| Hosting Variable | Used In | Purpose |
|------------------|---------|---------|
| `DATABASE_URL` | `src/config/validation.py` | DB connection |
| `REDIS_HOST`/`REDIS_PORT` | `src/config/validation.py` | Redis connection |
| `JWT_SECRET` | `src/config/validation.py` | Auth signing |
| `ENCRYPTION_KEY` | `src/config/validation.py` | Data encryption |

---

## Security Best Practices

### 1. Never Commit Secrets

- ✅ Add `.env` to `.gitignore`
- ✅ Use `.env.example` for templates
- ✅ Store secrets in GitHub Secrets, Vercel, or hosting platform

### 2. Rotate Secrets Regularly

- Rotate `JWT_SECRET` and `ENCRYPTION_KEY` quarterly
- Rotate API keys when team members leave
- Use different secrets for staging and production

### 3. Use Strong Secrets

Generate secrets with:
```bash
# JWT Secret
openssl rand -base64 32

# Encryption Key
openssl rand -base64 32

# Database Password
openssl rand -base64 24
```

### 4. Limit Secret Access

- Use GitHub Environments for production secrets
- Restrict Vercel project access
- Use IAM roles for AWS/cloud services

### 5. Audit Secret Usage

- Review which services have access to which secrets
- Remove unused secrets
- Monitor secret access logs (if available)

---

## Troubleshooting

### Variable Not Available

**Frontend:**
- Ensure variable is prefixed with `NEXT_PUBLIC_*`
- Check Vercel dashboard → Environment Variables
- Rebuild deployment after adding variable

**Backend:**
- Check hosting platform environment variables
- Verify variable name matches code exactly
- Check for typos (case-sensitive)

### Variable Value Incorrect

- Check environment-specific settings (Production vs Preview)
- Verify variable is set in correct environment
- Check for variable overrides in code

### Secrets Leaked

**If secrets are committed:**
1. Rotate all exposed secrets immediately
2. Remove from git history (use `git filter-branch` or BFG Repo-Cleaner)
3. Update all services with new secrets
4. Review access logs for unauthorized access

---

## Quick Reference

### Minimum Required Variables

**Local Development:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics
JWT_SECRET=local-secret-min-32-chars-long
ENCRYPTION_KEY=local-key-min-32-chars-long
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production:**
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=strong-production-secret-min-32-chars
ENCRYPTION_KEY=strong-production-key-min-32-chars
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

---

## Summary

**Key Principles:**
1. **Public variables:** Prefixed with `NEXT_PUBLIC_*`, safe for browser
2. **Private variables:** Never exposed to browser, stored in secrets
3. **Environment-specific:** Different values for dev/staging/production
4. **Centralized management:** GitHub Secrets, Vercel, hosting platform
5. **Documentation:** Keep `.env.example` up to date

**Next Steps:**
1. Review `.env.example` and ensure all variables are documented
2. Set up GitHub Secrets for CI/CD
3. Configure Vercel environment variables
4. Set up backend hosting environment variables
5. Test variable loading in each environment
