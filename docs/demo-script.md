# Demo Script

**Last Updated:** 2024  
**Purpose:** Step-by-step demo script for showcasing the podcast analytics platform

---

## Demo Environment

### URLs

**Production:** `https://yourdomain.com` (or Vercel production URL)  
**Staging:** `https://staging.yourdomain.com` (or Vercel preview URL)  
**Local:** `http://localhost:3000` (for local demos)

### Demo User

**Email:** `demo@example.com`  
**Password:** (Set in demo environment)  
**Tenant:** Demo Podcast Network

---

## Demo Flow (10-15 minutes)

### 1. Landing & Authentication (2 minutes)

**Steps:**
1. Navigate to production/staging URL
2. Show landing page (if exists) or go directly to login
3. Log in with demo credentials
4. Show dashboard overview

**Key Points:**
- Clean, modern UI
- Fast load times
- Responsive design

---

### 2. Dashboard Overview (3 minutes)

**Steps:**
1. Show main dashboard
2. Highlight key metrics:
   - Total listeners
   - Episode performance
   - Campaign performance
   - Revenue metrics
3. Show date range picker
4. Show different chart types (if available)

**Key Points:**
- Real-time data visualization
- Multi-tenant isolation
- Time-series analytics

---

### 3. Podcast Management (2 minutes)

**Steps:**
1. Navigate to Podcasts section
2. Show list of podcasts
3. Click into a podcast
4. Show episode list
5. Show episode details (if available)

**Key Points:**
- RSS feed integration
- Episode metadata
- Listener metrics per episode

---

### 4. Campaign Management (3 minutes)

**Steps:**
1. Navigate to Campaigns section
2. Show active campaigns
3. Create a new campaign (if time permits)
4. Show campaign performance:
   - Impressions
   - Clicks
   - Conversions
   - ROI metrics
5. Show attribution models (if available)

**Key Points:**
- Campaign lifecycle management
- Attribution tracking
- ROI calculations

---

### 5. Analytics Deep Dive (3 minutes)

**Steps:**
1. Navigate to Analytics section
2. Show listener demographics
3. Show episode performance trends
4. Show attribution events
5. Show cross-platform tracking (if available)

**Key Points:**
- Advanced analytics
- Time-series data
- Multi-touch attribution

---

### 6. Settings & Configuration (2 minutes)

**Steps:**
1. Navigate to Settings
2. Show tenant settings
3. Show user management (if available)
4. Show API keys (if available)
5. Show billing/subscription (if available)

**Key Points:**
- Multi-tenant configuration
- User management
- API access

---

## Quick Demo (5 minutes)

**If time is limited:**

1. **Login** → Dashboard (1 min)
2. **Show Dashboard** → Key metrics (2 min)
3. **Show Campaign** → Performance data (2 min)

---

## Demo Preparation Checklist

### Before Demo

- [ ] Verify production/staging environment is up
- [ ] Check database has demo data
- [ ] Verify all services are healthy (`/health` endpoint)
- [ ] Test login credentials
- [ ] Clear browser cache (if needed)
- [ ] Have backup demo URL ready

### Demo Data Requirements

**Minimum Data Needed:**
- 1 tenant (Demo Podcast Network)
- 2-3 podcasts
- 5-10 episodes per podcast
- 2-3 active campaigns
- Listener events (last 30 days)
- Attribution events (if campaigns exist)

---

## Seed Data Script

**Location:** `scripts/seed-demo-data.py` (to be created)

**Purpose:** Populate database with demo data

**Usage:**
```bash
DATABASE_URL=postgresql://... python scripts/seed-demo-data.py
```

**Data Created:**
- Demo tenant
- Demo user
- Sample podcasts
- Sample episodes
- Sample campaigns
- Sample listener events
- Sample attribution events

---

## Troubleshooting

### Demo Environment Down

**Fallback:** Use local environment
```bash
# Start local services
docker-compose up -d
./scripts/db-migrate-local.sh
npm run dev  # Frontend
uvicorn src.main:app --reload  # Backend
```

### Missing Data

**Solution:** Run seed script
```bash
python scripts/seed-demo-data.py
```

### Slow Performance

**Check:**
- Database connection
- Redis cache
- Network latency
- Backend health (`/health`)

---

## Demo Talking Points

### Value Proposition

1. **"Most podcasters fly blind"**
   - No visibility into listener behavior
   - Can't prove ROI to sponsors
   - Manual campaign management

2. **"We solve that"**
   - Real-time analytics
   - Automated attribution
   - Campaign management
   - Multi-tenant support

3. **"Built for scale"**
   - Multi-tenant architecture
   - Time-series database
   - Enterprise features (RBAC, audit logs)

### Technical Highlights

- **FastAPI backend** - High performance, async
- **Next.js frontend** - Modern, fast, SEO-friendly
- **PostgreSQL + TimescaleDB** - Time-series analytics
- **Multi-tenant** - Isolated data per organization
- **Real-time** - Live dashboard updates

---

## Post-Demo Follow-up

### Questions to Expect

1. **"How does attribution work?"**
   - Multiple attribution models
   - Cross-platform tracking
   - ROI calculations

2. **"Can we integrate with our existing tools?"**
   - API access
   - Webhooks
   - Export capabilities

3. **"What's the pricing?"**
   - Refer to pricing plan document
   - Free tier available
   - Usage-based pricing

4. **"How do we get started?"**
   - Sign up process
   - Onboarding flow
   - Support available

---

## Summary

**Demo Duration:** 10-15 minutes (full), 5 minutes (quick)

**Key Sections:**
1. Landing & Auth
2. Dashboard Overview
3. Podcast Management
4. Campaign Management
5. Analytics Deep Dive
6. Settings & Configuration

**Success Metrics:**
- Demo runs smoothly
- All features work
- Data is realistic
- Performance is good

**Next Steps:** Create seed data script and test demo flow end-to-end.
