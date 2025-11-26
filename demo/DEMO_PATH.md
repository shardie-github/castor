# Demo Path

**Exact steps to run a "happy path" demo from fresh user to "aha" moment**

---

## Pre-Demo Setup

### 1. Environment Setup
```bash
# Start services
docker-compose up -d postgres redis
sleep 10

# Run migrations
./scripts/db-migrate-local.sh

# Start backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (separate terminal)
cd frontend && npm run dev
```

### 2. Seed Demo Data (If Available)
```bash
# If seed script exists
python scripts/seed-demo-data.py
```

### 3. Create Demo Account
- Sign up at http://localhost:3000/signup
- Or use existing demo account: [FILL IN - Credentials]

---

## Demo Flow: Solo Podcaster Journey

### Step 1: Signup & Onboarding (2 minutes)

**URL:** http://localhost:3000/signup

**Actions:**
1. Click "Sign Up"
2. Enter email: `demo@example.com`
3. Enter password: `demo123456`
4. Click "Create Account"
5. Complete onboarding:
   - Enter podcast name: "Tech Talk Podcast"
   - Enter RSS feed: [FILL IN - Demo RSS feed URL]
   - Click "Connect Podcast"

**Expected Result:** Podcast connected, episodes ingesting

**Aha Moment:** "Wow, it automatically found my episodes!"

---

### Step 2: View Analytics Dashboard (1 minute)

**URL:** http://localhost:3000/dashboard

**Actions:**
1. Navigate to Dashboard
2. View listener metrics:
   - Total downloads
   - Episode performance
   - Audience demographics

**Expected Result:** See real analytics data

**Aha Moment:** "I can see who's listening and when!"

---

### Step 3: Create Campaign (2 minutes)

**URL:** http://localhost:3000/campaigns/new

**Actions:**
1. Click "Create Campaign"
2. Fill in campaign details:
   - Campaign name: "Q4 Sponsor Campaign"
   - Sponsor: "Tech Company X"
   - Start date: Today
   - End date: [30 days from now]
3. Set up attribution:
   - Choose: Promo code or Pixel
   - Promo code: "TECHTALK25"
   - Click "Save Campaign"

**Expected Result:** Campaign created, attribution tracking active

**Aha Moment:** "Attribution is set up automatically!"

---

### Step 4: View Campaign Performance (1 minute)

**URL:** http://localhost:3000/campaigns/[campaign-id]

**Actions:**
1. Navigate to campaign detail page
2. View performance metrics:
   - Downloads/streams
   - Attribution events
   - ROI calculation

**Expected Result:** See campaign performance in real-time

**Aha Moment:** "I can see exactly how the campaign is performing!"

---

### Step 5: Generate Sponsor Report (30 seconds)

**URL:** http://localhost:3000/campaigns/[campaign-id]/report

**Actions:**
1. Click "Generate Report"
2. Select report template: "Sponsor Report"
3. Click "Generate"
4. View PDF report

**Expected Result:** Professional PDF report generated in <30 seconds

**Aha Moment:** "This took 30 seconds instead of 2 hours!"

---

### Step 6: Sponsor Matching (1 minute)

**URL:** http://localhost:3000/sponsors/match

**Actions:**
1. Navigate to Sponsor Matching
2. View matched sponsors:
   - See AI-powered matches
   - View match score
   - View sponsor details
3. Click "Contact Sponsor" on a match

**Expected Result:** See relevant sponsor matches

**Aha Moment:** "It found perfect sponsors automatically!"

---

## Demo Flow: Agency/Network Journey

### Step 1: Multi-Tenant Setup (2 minutes)

**Actions:**
1. Create tenant: "Podcast Network"
2. Add multiple podcasts:
   - Podcast 1: "Tech Talk"
   - Podcast 2: "Business Insights"
   - Podcast 3: "Marketing Masters"
3. View portfolio dashboard

**Expected Result:** See all podcasts in one view

**Aha Moment:** "I can manage all my shows in one place!"

---

### Step 2: Portfolio Analytics (1 minute)

**Actions:**
1. Navigate to Portfolio Analytics
2. View aggregated metrics:
   - Total downloads across all shows
   - Top performing episodes
   - Audience overlap

**Expected Result:** Portfolio-level insights

**Aha Moment:** "I can see the big picture across all shows!"

---

## Key Demo Points

### Value Propositions to Highlight

1. **Time Saved:** "2 hours → 30 seconds" for report generation
2. **ROI Proof:** "Real attribution data, not guesswork"
3. **Automation:** "Set it and forget it" campaign management
4. **Multi-Tenant:** "Manage all your shows in one place"
5. **AI Matching:** "Find perfect sponsors automatically"

### Technical Highlights

1. **Real-Time Analytics:** Show live data updates
2. **Attribution Tracking:** Show cross-platform tracking
3. **Report Generation:** Show fast PDF generation
4. **Multi-Tenant:** Show data isolation

---

## Demo Checklist

### Before Demo
- [ ] Services running (backend, frontend, database)
- [ ] Demo data seeded (if available)
- [ ] Demo account created
- [ ] Browser tabs pre-opened
- [ ] Demo script reviewed

### During Demo
- [ ] Follow demo path exactly
- [ ] Highlight key value props
- [ ] Show "aha" moments
- [ ] Answer questions confidently

### After Demo
- [ ] Collect feedback
- [ ] Note any issues
- [ ] Update demo script if needed

---

## Troubleshooting

### Common Issues

**Issue:** Database connection fails
- **Fix:** Check PostgreSQL is running: `docker-compose ps postgres`
- **Fix:** Wait 10-15 seconds after starting

**Issue:** Frontend not loading
- **Fix:** Check frontend is running: `cd frontend && npm run dev`
- **Fix:** Check port 3000 is available

**Issue:** No demo data
- **Fix:** Run seed script: `python scripts/seed-demo-data.py`
- **Fix:** Or manually create demo data

**Issue:** Slow performance
- **Fix:** Check database indexes
- **Fix:** Clear cache: `docker-compose restart redis`

---

## Demo Variations

### Quick Demo (5 minutes)
- Signup → Dashboard → Create Campaign → Generate Report

### Full Demo (10 minutes)
- All steps above + Sponsor Matching + Multi-Tenant

### Technical Demo (15 minutes)
- All steps + Technical architecture + API demo

---

**See Also:**
- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) - Talking points
- [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md) - Pre-demo checklist
