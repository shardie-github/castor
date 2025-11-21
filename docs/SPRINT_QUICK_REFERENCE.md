# Sprint Quick Reference

**Current Sprint**: Validation Sprint (Nov 14 - Dec 13, 2024)  
**Sprint Goal**: Validate core product loop, measure TTFV and completion rate, learn top 3 friction points

---

## SPRINT GOAL

> By the end of this 30-day sprint, we validate that users can complete the product loop end-to-end, measure TTFV and completion rate, and learn the top 3 friction points preventing completion.

---

## SUCCESS CRITERIA

1. ✅ 3 beta users complete full loop without support
2. ✅ End-to-end integration test passes
3. ✅ TTFV and completion rate tracked with <5% data loss
4. ✅ Top 3 friction points documented
5. ✅ Analytics dashboard shows real data (not zeros)
6. ✅ Attribution pixel records events appearing in analytics within 5 seconds
7. ✅ Core loop works with <2% error rate
8. ✅ Sprint retrospective and user feedback docs created

---

## WEEK-BY-WEEK FOCUS

### Week 1: Foundation + Integration Validation
- Fix analytics endpoint (return real data)
- Add TTFV instrumentation
- Create sprint metrics dashboard
- End-to-end integration test

### Week 2: Attribution Pixel + Real Data Flow
- Create attribution pixel/script
- Connect attribution events to analytics
- Optimize event processing latency

### Week 3: Reporting Integration + Beta Users
- Complete report generation UI
- Add campaign completion tracking
- Conduct 3 beta user sessions

### Week 4: Polish + Metrics Dashboard + Retrospective
- Polish UI/UX based on feedback
- Complete sprint metrics dashboard
- Create sprint retrospective

---

## FIRST 72 HOURS CHECKLIST

### Day 1
- [ ] Fix campaign analytics endpoint (return real data)
- [ ] Fix analytics store database connection
- [ ] Add TTFV instrumentation
- [ ] Test analytics endpoint

### Day 2
- [ ] Create sprint metrics dashboard
- [ ] Set up event logging to analytics platform
- [ ] Create end-to-end integration test

### Day 3
- [ ] Create attribution pixel/script
- [ ] Connect attribution events to analytics store
- [ ] Test attribution pixel end-to-end

---

## KEY METRICS

| Metric | Target | How to Measure |
|--------|--------|----------------|
| TTFV | <15 min (80% users) | user.registered → campaign.created |
| Completion Rate | >70% | campaigns completed / campaigns created |
| Error Rate | <2% | API errors / total requests |
| Attribution Latency | <5s (p95) | event recorded → visible in analytics |

---

## CRITICAL FILES TO FIX

1. `src/api/campaigns.py:471` - TODO: Implement analytics aggregation
2. `src/analytics/analytics_store.py:99-103` - Remove in-memory fallback
3. `frontend/app/admin/sprint-metrics/page.tsx` - Create dashboard (missing)
4. `frontend/public/attribution.js` - Create attribution pixel (missing)
5. `frontend/app/campaigns/[id]/reports/page.tsx` - Create report UI (missing)

---

## VALIDATION ACTIVITIES

1. **Week 1**: Internal dogfooding - team completes full loop
2. **Week 2**: Attribution pixel testing - test on sponsor website
3. **Week 3**: Beta user sessions - 3 target users
4. **Week 4**: Final validation - 3-5 users independently

---

## DOCUMENTS TO CREATE

- [ ] `docs/SPRINT_RETROSPECTIVE_2024-11.md`
- [ ] `docs/USER_FEEDBACK_2024-11.md`
- [ ] `docs/FRICTION_POINTS_2024-11.md`

---

## QUICK LINKS

- Full Sprint Plan: `docs/SPRINT_REVIEW_AND_PLAN.md`
- Sprint Retrospective Template: `docs/SPRINT_RETROSPECTIVE_TEMPLATE.md`
- User Feedback Template: `docs/USER_FEEDBACK_TEMPLATE.md`
- Metrics Definitions: `docs/SPRINT_METRICS.md`

---

*Last Updated: 2024-11-13*
