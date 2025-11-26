# Deployment Flow

**Path from repo ready → app deployed to production**

---

## Overview

- **Frontend:** Vercel (automatic on push to `main`)
- **Backend:** Fly.io / Render / Kubernetes (choose one)
- **Database:** Supabase (managed PostgreSQL with TimescaleDB)

---

## Frontend Deployment (Vercel)

### Setup (One-time)

1. **Connect GitHub repo** to Vercel
2. **Configure:**
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `.next`
3. **Set environment variables** in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` - Backend API URL
   - `NEXT_PUBLIC_SITE_URL` - Production site URL
   - `NEXT_PUBLIC_SUPABASE_URL` (if using Supabase auth)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Deploy

```bash
git push origin main  # Automatic deployment
```

**Preview deployments:** Created automatically on PRs

---

## Backend Deployment

### Option 1: Fly.io (Recommended for MVP)

**Setup:**
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch (first time)
fly launch
# Follow prompts, use existing Dockerfile

# Set secrets
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set JWT_SECRET="$(openssl rand -hex 32)"
fly secrets set ENCRYPTION_KEY="$(openssl rand -hex 32)"
```

**Deploy:**
```bash
fly deploy
```

**Status:** `fly status`
**Logs:** `fly logs`

### Option 2: Render

1. **Create Web Service** in Render dashboard
2. **Connect GitHub repo**
3. **Configure:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. **Set environment variables** in dashboard
5. **Deploy:** Automatic on push to `main`

### Option 3: Kubernetes

See [`k8s/deployment.yaml`](../k8s/deployment.yaml) and [`docs/deploy-strategy.md`](deploy-strategy.md)

---

## Database Setup (Supabase)

### Setup (One-time)

1. **Create Supabase project** at https://supabase.com
2. **Get connection string:**
   - Settings → Database → Connection string
   - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
3. **Apply migrations:**
   ```bash
   export DATABASE_URL="postgresql://..."
   ./scripts/db-migrate-hosted.sh
   ```

### Verify

```bash
psql "$DATABASE_URL" -c "\dt"  # List tables
psql "$DATABASE_URL" -c "SELECT * FROM timescaledb_information.hypertables;"  # Check TimescaleDB
```

---

## Environment Variables Checklist

### Backend (Production)

**Required:**
- `DATABASE_URL` - Supabase connection string
- `REDIS_HOST` / `REDIS_PORT` - Redis cache
- `JWT_SECRET` - Random 32+ char secret
- `ENCRYPTION_KEY` - Random 32+ char secret
- `CORS_ALLOWED_ORIGINS` - Frontend URL(s)

**Optional:**
- `STRIPE_SECRET_KEY` - Payments
- `SENDGRID_API_KEY` - Email
- `OPENAI_API_KEY` - AI features

### Frontend (Vercel)

**Required:**
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SITE_URL` - Production site URL

**Optional:**
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

---

## Deployment Checklist

### Pre-Deploy

- [ ] All tests passing (`make test`)
- [ ] Code reviewed
- [ ] Migrations tested locally
- [ ] Environment variables set in hosting dashboard
- [ ] Database migrations applied to production DB

### Deploy

- [ ] Frontend: Push to `main` → Vercel auto-deploys
- [ ] Backend: `fly deploy` / Render auto-deploys / `kubectl apply`
- [ ] Verify health endpoints:
  - Frontend: `https://yourdomain.com`
  - Backend: `https://api.yourdomain.com/health`

### Post-Deploy

- [ ] Smoke test critical flows
- [ ] Check error logs
- [ ] Monitor metrics (if configured)

---

## Rollback

### Frontend (Vercel)
- Dashboard → Deployments → Promote previous deployment

### Backend (Fly.io)
```bash
fly releases
fly releases rollback <release-id>
```

### Database
- Supabase dashboard → Backups → Restore point-in-time

---

## Monitoring

- **Vercel Analytics:** Frontend performance (built-in)
- **Fly.io Metrics:** `fly metrics`
- **Supabase Dashboard:** Database metrics
- **Health Checks:** `/health` endpoint

---

## Cost Estimate (MVP)

- **Frontend (Vercel):** Free tier (100GB bandwidth/month)
- **Backend (Fly.io):** $5-20/month
- **Database (Supabase):** $25/month (Pro tier)
- **Total:** ~$30-45/month

---

**See also:**
- [`docs/deploy-strategy.md`](deploy-strategy.md) - Detailed strategy
- [`docs/backend-strategy.md`](backend-strategy.md) - Backend architecture
- [`docs/frontend-hosting-strategy.md`](frontend-hosting-strategy.md) - Frontend hosting
