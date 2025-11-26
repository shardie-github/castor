# Demo Checklist

**Pre-demo checklist and quick recovery tips**

---

## Pre-Demo Checklist

### Environment Setup
- [ ] Backend running: `uvicorn src.main:app --reload`
- [ ] Frontend running: `cd frontend && npm run dev`
- [ ] Database running: `docker-compose ps postgres`
- [ ] Redis running: `docker-compose ps redis`
- [ ] Migrations applied: `./scripts/db-migrate-local.sh`

### Demo Data
- [ ] Demo account created (or credentials ready)
- [ ] Demo podcast RSS feed available
- [ ] Demo data seeded (if seed script exists)
- [ ] Demo campaigns created (if needed)

### Browser Setup
- [ ] Browser tabs pre-opened:
  - [ ] Signup page: http://localhost:3000/signup
  - [ ] Dashboard: http://localhost:3000/dashboard
  - [ ] Campaigns: http://localhost:3000/campaigns
- [ ] Browser console cleared (no errors visible)
- [ ] Browser zoom set to 100%

### Demo Materials
- [ ] Demo script reviewed: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
- [ ] Demo path memorized: [`DEMO_PATH.md`](DEMO_PATH.md)
- [ ] Key talking points ready
- [ ] Questions prepared (common questions)

### Technical Checks
- [ ] Health endpoint working: http://localhost:8000/health
- [ ] API docs accessible: http://localhost:8000/api/docs
- [ ] No console errors in browser
- [ ] Network tab shows successful API calls

---

## Quick Recovery Tips

### Issue: Backend Not Running

**Symptoms:** Frontend shows connection errors, API calls fail

**Quick Fix:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Prevention:** Start backend before demo, verify health endpoint

---

### Issue: Database Connection Fails

**Symptoms:** Backend errors, "could not connect to server"

**Quick Fix:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres
sleep 10

# Verify connection
psql postgresql://postgres:postgres@localhost:5432/podcast_analytics -c "SELECT 1;"
```

**Prevention:** Start database before demo, wait 10-15 seconds

---

### Issue: Frontend Not Loading

**Symptoms:** Browser shows "This site can't be reached", blank page

**Quick Fix:**
```bash
# Check if frontend is running
curl http://localhost:3000

# If not running, start it
cd frontend && npm run dev
```

**Prevention:** Start frontend before demo, verify it loads

---

### Issue: No Demo Data

**Symptoms:** Dashboard empty, no podcasts, no campaigns

**Quick Fix:**
```bash
# Run seed script (if available)
python scripts/seed-demo-data.py

# Or manually create demo data via API
# POST /api/v1/podcasts with demo RSS feed
```

**Prevention:** Seed demo data before demo, verify it exists

---

### Issue: Slow Performance

**Symptoms:** Pages load slowly, API calls timeout

**Quick Fix:**
```bash
# Check database performance
docker-compose logs postgres | grep -i slow

# Restart Redis (clear cache)
docker-compose restart redis

# Check backend logs for errors
# Look for slow queries, connection issues
```

**Prevention:** Test demo path before actual demo, optimize queries

---

### Issue: Migration Errors

**Symptoms:** Database errors, missing tables

**Quick Fix:**
```bash
# Re-run migrations
./scripts/db-migrate-local.sh

# If that fails, reset database (destructive!)
docker-compose down -v
docker-compose up -d postgres redis
sleep 10
./scripts/db-migrate-local.sh
```

**Prevention:** Test migrations before demo, don't modify schema during demo

---

### Issue: Port Conflicts

**Symptoms:** "Port already in use" errors

**Quick Fix:**
```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Kill process (if safe)
kill -9 <PID>

# Or use different ports
uvicorn src.main:app --reload --port 8001  # Backend
cd frontend && PORT=3001 npm run dev  # Frontend
```

**Prevention:** Check ports before demo, use different ports if needed

---

## Demo Day Preparation

### Day Before
- [ ] Run full demo path end-to-end
- [ ] Test all recovery scenarios
- [ ] Verify demo data exists
- [ ] Review demo script
- [ ] Prepare backup plan (screenshots, video)

### Day Of
- [ ] Start services 30 minutes before demo
- [ ] Verify all endpoints working
- [ ] Test demo path one more time
- [ ] Have recovery commands ready
- [ ] Have backup plan ready (screenshots, video)

### During Demo
- [ ] Stay calm if issues arise
- [ ] Use recovery tips quickly
- [ ] Have backup plan ready (screenshots, video)
- [ ] Don't apologize excessively—fix and move on

---

## Backup Plans

### Plan A: Live Demo
- Full interactive demo as planned

### Plan B: Screenshots
- Pre-prepared screenshots of key flows
- Walk through screenshots if live demo fails

### Plan C: Video
- Pre-recorded demo video
- Play video if live demo fails

### Plan D: Slides
- Slides with key screenshots and value props
- Present slides if all else fails

---

## Post-Demo

### Immediate
- [ ] Note any issues encountered
- [ ] Document what worked well
- [ ] Update demo script if needed
- [ ] Fix any bugs discovered

### Follow-Up
- [ ] Send demo recording (if recorded)
- [ ] Answer any questions
- [ ] Collect feedback
- [ ] Schedule follow-up if needed

---

**See Also:**
- [`DEMO_PATH.md`](DEMO_PATH.md) - Demo steps
- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) - Talking points
- [`docs/SETUP_LOCAL.md`](../docs/SETUP_LOCAL.md) - Setup guide
