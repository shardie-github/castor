# Cost & Limits Documentation

**Last Updated:** 2024  
**Purpose:** Overview of hosting costs, usage limits, and cost optimization

---

## Monthly Cost Breakdown

### Development Environment

| Service | Cost | Notes |
|---------|------|-------|
| **Database (Local)** | $0 | Docker Compose (self-hosted) |
| **Redis (Local)** | $0 | Docker Compose (self-hosted) |
| **Frontend (Local)** | $0 | Local Next.js dev server |
| **Backend (Local)** | $0 | Local FastAPI server |
| **Total** | **$0** | Free for local development |

---

### Production Environment (Early Stage)

| Service | Tier | Monthly Cost | Limits |
|---------|------|--------------|--------|
| **Database** | Supabase Pro | $25 | 8 GB storage, 50 GB bandwidth |
| **Redis** | Upstash Free | $0 | 10K commands/day |
| **Frontend** | Vercel Hobby | $0 | 100 GB bandwidth |
| **Backend** | Render Free | $0 | Limited hours/month |
| **Total** | | **$25** | Suitable for 10-100 tenants |

---

### Production Environment (Growth Stage)

| Service | Tier | Monthly Cost | Limits |
|---------|------|--------------|--------|
| **Database** | Supabase Team | $599 | 32 GB storage, 250 GB bandwidth |
| **Redis** | Upstash Paid | $20-50 | Pay per command |
| **Frontend** | Vercel Pro | $20 | Unlimited bandwidth |
| **Backend** | Render Paid | $25-50 | Always-on instance |
| **Total** | | **$664-719** | Suitable for 100-1,000 tenants |

---

## Service-Specific Limits

### Supabase (Database)

**Free Tier:**
- 500 MB database storage
- 2 GB bandwidth/month
- Daily backups
- ❌ No TimescaleDB extension

**Pro Tier ($25/month):**
- 8 GB database storage
- 50 GB bandwidth/month
- Daily backups
- Point-in-time recovery
- ⚠️ TimescaleDB extension (may need to request)

**Team Tier ($599/month):**
- 32 GB database storage
- 250 GB bandwidth/month
- Hourly backups
- Dedicated support

**Limits:**
- Connection limit: 200 connections (Pro), 400 connections (Team)
- Query timeout: 60 seconds
- Max database size: 8 GB (Pro), 32 GB (Team)

---

### Vercel (Frontend)

**Hobby (Free):**
- Unlimited personal projects
- 100 GB bandwidth/month
- 100 serverless function executions/day
- Automatic HTTPS
- Preview deployments

**Pro ($20/month per user):**
- Unlimited bandwidth
- Unlimited serverless function executions
- Team collaboration
- Password protection
- Analytics

**Limits:**
- Build time: 45 minutes (Hobby), unlimited (Pro)
- Function execution: 10 seconds (Hobby), 60 seconds (Pro)
- File size: 50 MB per file

---

### Upstash Redis

**Free Tier:**
- 10,000 commands/day
- 256 MB storage
- Global edge caching

**Paid Tier:**
- $0.20 per 100K commands
- Pay-as-you-go storage
- No daily limits

**Estimated Costs:**
- Low usage (100K commands/month): $0.20
- Medium usage (1M commands/month): $2
- High usage (10M commands/month): $20

---

### Render (Backend)

**Free Tier:**
- 750 hours/month (shared)
- Sleeps after 15 minutes of inactivity
- 512 MB RAM

**Paid Tier ($7-25/month):**
- Always-on instance
- 512 MB - 2 GB RAM
- Auto-scaling available

**Limits:**
- Free tier: Sleeps when inactive
- Paid tier: Always-on, no sleep

---

## Cost Optimization Strategies

### 1. Start with Free Tiers

**Recommendation:** Use free tiers for development and early production

- Supabase Free (development only)
- Vercel Hobby (production OK for low traffic)
- Upstash Free (if usage < 10K commands/day)
- Render Free (if OK with sleep/wake)

**Upgrade when:**
- Exceeding free tier limits
- Need always-on backend
- Need more database storage

---

### 2. Monitor Usage

**Key Metrics to Track:**
- Database storage usage
- Bandwidth usage (Supabase, Vercel)
- Redis command count
- Backend uptime (if using free tier)

**Tools:**
- Supabase dashboard → Usage
- Vercel dashboard → Analytics
- Upstash dashboard → Metrics
- Render dashboard → Metrics

---

### 3. Optimize Database Usage

**Strategies:**
- Archive old data (move to cold storage)
- Use TimescaleDB retention policies
- Optimize queries (add indexes)
- Use read replicas for analytics (if needed)

**Cost Impact:**
- Reduce database storage → Lower Supabase tier possible
- Faster queries → Better user experience

---

### 4. Optimize Frontend

**Strategies:**
- Code splitting (already implemented)
- Image optimization (Next.js Image component)
- Static generation where possible
- CDN caching (Vercel edge network)

**Cost Impact:**
- Reduce bandwidth usage → Stay on Vercel Hobby longer
- Faster page loads → Better SEO/conversion

---

### 5. Optimize Redis Usage

**Strategies:**
- Cache frequently accessed data
- Set appropriate TTLs
- Use Redis only for hot data
- Monitor command count

**Cost Impact:**
- Stay within Upstash Free tier longer
- Reduce paid tier costs

---

## Scaling Costs

### Early Stage (10-100 tenants)

**Monthly Cost:** $25-50
- Supabase Pro: $25
- Vercel Hobby: $0
- Upstash Free: $0
- Render Free: $0 (or Paid $7)

**Traffic:** Low to moderate
**Storage:** < 8 GB database

---

### Growth Stage (100-1,000 tenants)

**Monthly Cost:** $664-719
- Supabase Team: $599
- Vercel Pro: $20
- Upstash Paid: $20-50
- Render Paid: $25-50

**Traffic:** High
**Storage:** 8-32 GB database

---

### Mature Stage (1,000+ tenants)

**Monthly Cost:** $1,000+
- Supabase Enterprise: Custom pricing
- Vercel Enterprise: Custom pricing
- Upstash Paid: $50-200
- Render/Kubernetes: $100-500

**Traffic:** Very high
**Storage:** 32+ GB database

**Considerations:**
- Multi-region setup
- Read replicas
- Dedicated infrastructure
- Custom pricing negotiations

---

## Cost Alerts & Budgets

### Recommended Budget Alerts

**Set up alerts for:**
- Database storage > 80% of limit
- Bandwidth > 80% of monthly limit
- Redis commands > 80% of daily limit
- Monthly spend > $100 (growth stage)

**Tools:**
- Supabase dashboard → Alerts
- Vercel dashboard → Usage alerts
- Upstash dashboard → Alerts
- GitHub Actions → Cost monitoring (if configured)

---

## Free Tier Limitations

### Supabase Free Tier

**Limitations:**
- ❌ No TimescaleDB extension (critical for this project)
- 500 MB storage (very limited)
- 2 GB bandwidth/month (low)

**Recommendation:** Not suitable for production. Use Pro tier ($25/month) minimum.

---

### Vercel Hobby

**Limitations:**
- 100 GB bandwidth/month (may be limiting)
- 100 serverless function executions/day (not used if backend is separate)
- No team collaboration

**Recommendation:** Suitable for early production. Upgrade to Pro when:
- Exceeding bandwidth
- Need team features
- Need password protection

---

### Render Free Tier

**Limitations:**
- Sleeps after 15 minutes inactivity
- 750 hours/month shared
- 512 MB RAM

**Recommendation:** Not suitable for production backend. Use Paid tier ($7-25/month) for always-on.

---

## Cost Summary

### Minimum Production Cost

**$25/month:**
- Supabase Pro: $25
- Vercel Hobby: $0
- Upstash Free: $0
- Render Free: $0 (or Paid $7 for always-on)

**Total:** $25-32/month

### Recommended Production Cost

**$50-75/month:**
- Supabase Pro: $25
- Vercel Hobby: $0 (or Pro $20)
- Upstash Paid: $2-5
- Render Paid: $25

**Total:** $52-75/month

---

## Cost Optimization Checklist

- [ ] Monitor database storage usage
- [ ] Monitor bandwidth usage
- [ ] Monitor Redis command count
- [ ] Set up cost alerts
- [ ] Archive old data regularly
- [ ] Optimize queries and indexes
- [ ] Use caching effectively
- [ ] Review costs monthly
- [ ] Consider upgrading/downgrading tiers based on usage

---

## Summary

**Development:** $0/month (local Docker Compose)

**Early Production:** $25-32/month (Supabase Pro + free tiers)

**Growth Production:** $664-719/month (Supabase Team + paid tiers)

**Key Optimization:**
- Start with free/low-cost tiers
- Monitor usage closely
- Upgrade only when needed
- Archive old data
- Optimize queries and caching

**Next Steps:** Set up monitoring and alerts for cost tracking.
