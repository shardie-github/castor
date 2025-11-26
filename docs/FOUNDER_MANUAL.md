# Founder Manual

**"For dummies" guide to running this startup**

---

## Section 1: MUST DO NOW (Blockers)

### 1.1 Get App Running Locally

**If you haven't done this yet:**

```bash
# 1. Clone repo
git clone <repo-url>
cd podcast-analytics-platform

# 2. Copy environment file
cp .env.example .env
# Edit .env - at minimum set DATABASE_URL for local

# 3. Start database
docker-compose up -d postgres redis
sleep 10

# 4. Run migrations
./scripts/db-migrate-local.sh

# 5. Install dependencies
pip install -r requirements.txt
cd frontend && npm ci && cd ..

# 6. Start servers
# Terminal 1:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2:
cd frontend && npm run dev
```

**Verify:** http://localhost:8000/health and http://localhost:3000

**See:** [`docs/SETUP_LOCAL.md`](SETUP_LOCAL.md) for details

---

### 1.2 Deploy to Production

**Choose one backend option:**

**Option A: Fly.io (Easiest)**
```bash
fly launch
fly secrets set DATABASE_URL="postgresql://..."
fly deploy
```

**Option B: Render**
- Connect GitHub repo in Render dashboard
- Set environment variables
- Deploy

**Frontend:**
- Connect repo to Vercel
- Set `NEXT_PUBLIC_API_URL` to backend URL
- Push to `main` → auto-deploys

**Database:**
- Create Supabase project
- Get connection string
- Run: `DATABASE_URL="..." ./scripts/db-migrate-hosted.sh`

**See:** [`docs/DEPLOYMENT_FLOW.md`](DEPLOYMENT_FLOW.md) for details

---

### 1.3 Set Up Environment Variables

**Required for production:**

**Backend:**
- `DATABASE_URL` - Supabase connection string
- `JWT_SECRET` - Generate: `openssl rand -hex 32`
- `ENCRYPTION_KEY` - Generate: `openssl rand -hex 32`
- `CORS_ALLOWED_ORIGINS` - Frontend URL

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SITE_URL` - Production site URL

**See:** [`.env.example`](../.env.example) for full list

---

### 1.4 Get First User / Customer

**If pre-traction:**

1. **Conduct 10-20 user interviews**
   - Use: [`validation/user-interview-framework.md`](../validation/user-interview-framework.md)
   - Document in: [`yc/USER_VALIDATION.md`](../yc/USER_VALIDATION.md)

2. **Run distribution experiments**
   - See: [`yc/YC_DISTRIBUTION_PLAN.md`](../yc/YC_DISTRIBUTION_PLAN.md)
   - Track results in: [`yc/DISTRIBUTION_RESULTS.md`](../yc/DISTRIBUTION_RESULTS.md)

3. **Get early adopters**
   - Offer free/discounted access
   - Collect feedback
   - Iterate

---

## Section 2: DO THIS SOON (NEXT)

### 2.1 Fill Team Information

**Update:** [`yc/TEAM.md`](../yc/TEAM.md)
- Founder bios
- Previous experience
- Why this problem

**Update:** [`yc/FOUNDER_MARKET_FIT.md`](../yc/FOUNDER_MARKET_FIT.md)
- Why you're uniquely qualified

---

### 2.2 Collect Real Metrics

**If you have users:**

1. **Check metrics dashboard:** http://localhost:8000/api/v1/metrics/dashboard
2. **Document traction:** Update [`yc/YC_PRODUCT_OVERVIEW.md`](../yc/YC_PRODUCT_OVERVIEW.md)
3. **Know numbers cold:** Rehearse with [`yc/YC_INTERVIEW_CHEATSHEET.md`](../yc/YC_INTERVIEW_CHEATSHEET.md)

**If pre-traction:**
- Show MVP completion (200+ Python files, production-ready)
- Show clear path to customers (distribution plan ready)
- Show user validation (interviews conducted)

---

### 2.3 Prepare Investor Materials

**Create/update:**
- [`dataroom/01_EXEC_SUMMARY.md`](../dataroom/01_EXEC_SUMMARY.md) - One-page summary
- [`dataroom/02_PRODUCT_DECK_OUTLINE.md`](../dataroom/02_PRODUCT_DECK_OUTLINE.md) - Deck structure
- [`dataroom/03_METRICS_OVERVIEW.md`](../dataroom/03_METRICS_OVERVIEW.md) - Key metrics
- [`demo/DEMO_SCRIPT.md`](../demo/DEMO_SCRIPT.md) - Demo talking points

**See:** [`dataroom/`](../dataroom/) directory for all investor assets

---

### 2.4 Run Growth Experiments

**From:** [`yc/YC_DISTRIBUTION_PLAN.md`](../yc/YC_DISTRIBUTION_PLAN.md)

**Top 3 experiments:**
1. **Referral program** - Implement [`src/api/referrals.py`](../src/api/referrals.py)
2. **SEO landing pages** - Create [`frontend/app/podcast-analytics/page.tsx`](../frontend/app/podcast-analytics/page.tsx)
3. **Shareable reports** - Add sharing to [`src/api/reports.py`](../src/api/reports.py)

**Track results:** [`yc/DISTRIBUTION_RESULTS.md`](../yc/DISTRIBUTION_RESULTS.md)

---

## Section 3: NICE TO HAVE LATER

### 3.1 Advanced Features

- A/B testing framework
- Advanced analytics dashboards
- White-label portals
- API for partners

### 3.2 Operations

- Automated monitoring/alerts
- Customer success playbooks
- Support documentation
- Onboarding automation

### 3.3 Growth

- Content marketing/blog
- Partnership integrations
- Marketplace features
- Viral loops optimization

---

## Section 4: Quick Reference

### Key Commands

```bash
# Development
make setup          # Full setup
make dev            # Start servers
make test           # Run tests
make lint           # Lint code

# Database
make db-migrate     # Run migrations
make db-reset       # Reset local DB

# Deployment
fly deploy          # Deploy backend (Fly.io)
git push origin main # Deploy frontend (Vercel)
```

### Key Files

- **Setup:** [`docs/SETUP_LOCAL.md`](SETUP_LOCAL.md)
- **Deploy:** [`docs/DEPLOYMENT_FLOW.md`](DEPLOYMENT_FLOW.md)
- **YC Prep:** [`yc/YC_INTERVIEW_CHEATSHEET.md`](../yc/YC_INTERVIEW_CHEATSHEET.md)
- **Gaps:** [`yc/YC_GAP_ANALYSIS.md`](../yc/YC_GAP_ANALYSIS.md)
- **Distribution:** [`yc/YC_DISTRIBUTION_PLAN.md`](../yc/YC_DISTRIBUTION_PLAN.md)

### Key URLs (Local)

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/api/v1/metrics/dashboard

### Key URLs (Production)

- Frontend: `https://yourdomain.com` (Vercel)
- Backend: `https://api.yourdomain.com` (Fly.io/Render)
- Database: Supabase dashboard

---

## Getting Help

- **Setup issues:** [`docs/SETUP_LOCAL.md`](SETUP_LOCAL.md) troubleshooting
- **Deploy issues:** [`docs/DEPLOYMENT_FLOW.md`](DEPLOYMENT_FLOW.md)
- **YC questions:** [`yc/YC_INTERVIEW_CHEATSHEET.md`](../yc/YC_INTERVIEW_CHEATSHEET.md)
- **Technical:** [`docs/local-dev.md`](local-dev.md)

---

**Last Updated:** 2024-12-XX
