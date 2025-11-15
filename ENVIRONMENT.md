# Environment Variables Reference

This document provides a comprehensive mapping of all environment variables required across the entire stack: **GitHub Secrets → Vercel Environment Variables → Supabase → Next.js Frontend → Python Backend → External Integrations**.

---

## 🔐 CRITICAL SECRETS (GitHub Secrets + Vercel)

These must be set in both GitHub Repository Secrets and Vercel Project Environment Variables.

### Supabase Configuration
```bash
# Supabase Project Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Service role key (admin access)
SUPABASE_ANON_KEY=eyJhbGc...          # Anonymous/public key (client access)

# Frontend Public Variables (exposed to browser)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Mobile/Expo (if applicable)
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

**Where Used:**
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`: Python backend (`src/config/__init__.py`)
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Next.js frontend (`frontend/next.config.js`, `vercel.json`)
- `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY`: Expo mobile app (if present)

---

## 🗄️ DATABASE CONFIGURATION

### PostgreSQL (Local Development)
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=podcast_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

**Where Used:**
- Python backend: `src/config/__init__.py`, `src/database/postgres.py`
- Docker Compose: `docker-compose.yml`

**Production:** Use Supabase connection string instead (via `SUPABASE_URL`)

### Redis
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional, leave empty for local dev
```

**Where Used:**
- Python backend: `src/config/__init__.py`, `src/database/redis.py`
- Docker Compose: `docker-compose.yml`

---

## 🌐 API CONFIGURATION

### Backend API
```bash
API_URL=http://localhost:8000
API_KEY=  # Optional API key for authentication
API_SECRET_KEY=  # Optional secret key
```

**Where Used:**
- Python backend: `src/config/__init__.py`
- Next.js frontend: `frontend/next.config.js` → `NEXT_PUBLIC_API_URL`
- Frontend API client: `frontend/lib/api.ts`

### Frontend Public API URL
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Where Used:**
- Next.js frontend: `frontend/next.config.js`, `frontend/lib/api.ts`

### Site URL (SEO/Metadata)
```bash
NEXT_PUBLIC_SITE_URL=https://castor.app
```

**Where Used:**
- Next.js frontend: `frontend/app/layout.tsx` (metadata base URL)

---

## 🔒 SECURITY

### Authentication & Encryption
```bash
JWT_SECRET=change-me-in-production-generate-random-secret
ENCRYPTION_KEY=change-me-in-production-generate-random-key
```

**Where Used:**
- Python backend: `src/config/__init__.py`, `src/config/security.py`
- **CRITICAL:** Must be strong random strings in production

### OAuth (if using OAuth flows)
```bash
OAUTH_CLIENT_ID=default_client
OAUTH_CLIENT_SECRET=default_secret
OAUTH_REDIRECT_URI=http://localhost:8000/callback
```

**Where Used:**
- Python backend: `src/main.py`

### CORS & Security Headers
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://castor.app
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=3600
ENABLE_SECURITY_HEADERS=true
FORCE_HTTPS=true
HSTS_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
WAF_ENABLED=true
SESSION_TIMEOUT_MINUTES=30
SESSION_SECURE=true
```

**Where Used:**
- Python backend: `src/config/security.py`

---

## 💳 PAYMENT PROCESSING

### Stripe
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**Where Used:**
- Python backend: `src/config/__init__.py`, `src/payments/stripe.py`
- Frontend: Should be exposed via `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` if needed

---

## 📧 EMAIL SERVICE

### SendGrid
```bash
SENDGRID_API_KEY=SG.xxx...
```

**Where Used:**
- Python backend: `src/config/__init__.py`

---

## ☁️ AWS CONFIGURATION

### AWS Services (S3, SES, etc.)
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx...
AWS_REGION=us-east-1
AWS_S3_BACKUP_BUCKET=  # Optional, for backups
```

**Where Used:**
- Python backend: `src/config/__init__.py`, `src/backup/backup_manager.py`
- Disaster recovery: `src/disaster_recovery/replication_manager.py`

---

## 🤖 AI PROVIDERS

### OpenAI
```bash
OPENAI_API_KEY=sk-...
```

**Where Used:**
- Python backend: `src/main.py`

### Anthropic
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Where Used:**
- Python backend: `src/main.py`

---

## 📊 MONITORING & OBSERVABILITY

### Prometheus & Grafana
```bash
PROMETHEUS_PORT=9090
GRAFANA_URL=http://localhost:3000
```

**Where Used:**
- Python backend: `src/config/__init__.py`
- Docker Compose: `docker-compose.yml`

---

## 🔧 EXTERNAL INTEGRATIONS

### Google Workspace / Google Sheets
```bash
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REFRESH_TOKEN=xxx
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json  # Optional
```

**Where Used:**
- Python backend: `src/integrations/google_workspace.py`, `src/etl/google_sheets.py`
- Google Sheets sync: `docs/sheets/push_metrics_daily.gs`

### Shopify
```bash
SHOPIFY_API_KEY=xxx
SHOPIFY_API_SECRET=xxx
```

**Where Used:**
- Python backend: `src/integrations/shopify.py`

### Wix
```bash
WIX_API_KEY=xxx
```

**Where Used:**
- Python backend: `src/integrations/wix.py`

### Host API Credentials
```bash
LIBSYN_API_KEY=xxx
ANCHOR_ACCESS_TOKEN=xxx
BUZZSPROUT_API_KEY=xxx
```

**Where Used:**
- Python backend: `src/ingestion/host_apis.py`

---

## 🎯 FEATURE FLAGS

Control feature availability via environment variables:

```bash
ENABLE_ETL_CSV_UPLOAD=false
ENABLE_MATCHMAKING=false
ENABLE_IO_BOOKINGS=false
ENABLE_DEAL_PIPELINE=false
ENABLE_NEW_DASHBOARD_CARDS=false
MATCHMAKING_ENABLED=false
ENABLE_ORCHESTRATION=false
ENABLE_MONETIZATION=false
ENABLE_AUTOMATION_JOBS=false
```

**Where Used:**
- Python backend: `src/main.py`, `src/api/*.py` (feature gate checks)

---

## 🌍 ENVIRONMENT SETTINGS

### Environment Type
```bash
ENVIRONMENT=development  # development | staging | production
DEBUG=true  # true | false
```

**Where Used:**
- Python backend: `src/config/__init__.py`

### Disaster Recovery
```bash
PRIMARY_REGION=us-east-1
SECONDARY_REGION=us-west-2
BACKUP_STORAGE_PATH=/backups
```

**Where Used:**
- Python backend: `src/main.py`, `src/disaster_recovery/`

### Vanity URLs (if applicable)
```bash
VANITY_URL_BASE=https://track.example.com
```

**Where Used:**
- Python backend: `src/api/io.py`

---

## 🔗 AI AGENT MESH INTEGRATIONS

### Zapier
No environment variables required. Uses webhook URLs configured in database (`integrations` table).

**Where Used:**
- Python backend: `src/integrations/zapier.py`
- Database: `migrations/010_integrations.sql` (webhooks table)

### MindStudio, AutoDS, TikTok Ads, Meta Ads, ElevenLabs, CapCut
These integrations are configured via:
1. Database `integrations` table (OAuth tokens stored in `integration_tokens`)
2. Environment variables for API keys (if required):
   ```bash
   TIKTOK_ADS_API_KEY=xxx
   TIKTOK_ADS_SECRET=xxx
   META_ADS_API_KEY=xxx
   META_ADS_SECRET=xxx
   ELEVENLABS_API_KEY=xxx
   AUTODS_API_KEY=xxx
   CAPCUT_API_KEY=xxx
   MINDSTUDIO_API_KEY=xxx
   ```

**Note:** These are not currently implemented in codebase but should be added if these integrations are used.

---

## 📋 ENVIRONMENT VARIABLE MAPPING BY FRAMEWORK

### Next.js (Frontend)
**Public Variables (exposed to browser):**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (if needed)

**Server-Side Only:**
- All other variables are server-side only

**Configuration Files:**
- `frontend/next.config.js` - Next.js config
- `vercel.json` - Vercel deployment config

### Python Backend
**All variables** except `NEXT_PUBLIC_*` are used server-side.

**Configuration Files:**
- `src/config/__init__.py` - Main config loader
- `src/config/security.py` - Security config
- `.env` / `.env.example` - Local development

### Vercel Deployment
**Required in Vercel Dashboard:**
- All `NEXT_PUBLIC_*` variables
- `SUPABASE_URL` (if backend runs on Vercel)
- `SUPABASE_SERVICE_ROLE_KEY` (if backend runs on Vercel)

**Configuration Files:**
- `vercel.json` - Vercel project config

### GitHub Actions / CI/CD
**Required in GitHub Secrets:**
- All production secrets
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_URL` (if mobile)

**Configuration Files:**
- `.github/workflows/*.yml` - CI/CD workflows

---

## ✅ VALIDATION CHECKLIST

Before deploying, ensure:

- [ ] All `NEXT_PUBLIC_*` variables are set in Vercel
- [ ] All backend secrets are set in GitHub Secrets
- [ ] Supabase credentials match between GitHub, Vercel, and local `.env`
- [ ] `JWT_SECRET` and `ENCRYPTION_KEY` are strong random strings (not defaults)
- [ ] `NEXT_PUBLIC_SITE_URL` matches your production domain
- [ ] CORS origins include your production domain
- [ ] Feature flags are set appropriately for production
- [ ] AWS credentials are configured if using S3/SES
- [ ] Stripe keys are production keys (not test keys) in production
- [ ] All external integration API keys are set if those features are enabled

---

## 🔍 TROUBLESHOOTING

### "Supabase client not initialized"
- Ensure `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set
- Check `frontend/lib/supabase.ts` exists (create if missing)

### "Environment variable not found"
- Check variable name matches exactly (case-sensitive)
- Verify variable is set in correct environment (local `.env`, Vercel, GitHub Secrets)
- For `NEXT_PUBLIC_*` variables, ensure they're in `next.config.js` and Vercel

### "Database connection failed"
- Verify `SUPABASE_URL` is correct
- Check `SUPABASE_SERVICE_ROLE_KEY` has correct permissions
- For local dev, ensure PostgreSQL is running and `POSTGRES_*` vars are set

---

## 📚 ADDITIONAL RESOURCES

- [Supabase Environment Variables](https://supabase.com/docs/guides/getting-started/local-development#environment-variables)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
