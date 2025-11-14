# Phase 5 — Verification & Safety Nets
**RUN-ID:** 20251113T114706Z  
**Timestamp:** 2025-11-13T11:47:06Z UTC

## Verification Checklist

### 5A) Schema Diff Check ✅

#### Verification Steps
1. **Dry-run migration:**
   ```bash
   PGURL="postgresql://..." ./scripts/db_migrate.sh migrations/20251113T114706Z --dry-run
   ```
   - ✅ Script parses correctly
   - ✅ SQL syntax validated
   - ✅ Idempotent patterns confirmed

2. **Expected Additive Objects:**
   - `matches` table (verify exists or will be created)
   - `io_bookings.promo_code` column (verify exists or will be added)
   - `io_bookings.vanity_url` column (verify exists or will be added)
   - `ux_metrics_daily_day_ep_source` unique index (verify exists or will be created)

#### Status
✅ **PASS** - Migration pack is additive-only. No destructive changes detected.

---

### 5B) Seed & Smoke ⚠️

#### Verification Steps
1. **Run migration:**
   ```bash
   PGURL="postgresql://..." ./scripts/db_migrate.sh migrations/20251113T114706Z
   ```

2. **Verify objects exist:**
   ```bash
   PGURL="postgresql://..." psql -f scripts/verify_run.sql
   ```

3. **Upload sample CSV:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/etl/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@samples/metrics_daily.csv"
   ```

4. **Verify metrics_daily rows:**
   ```sql
   SELECT COUNT(*) FROM metrics_daily WHERE day >= '2025-11-01';
   ```

#### Status
⚠️ **PENDING** - Requires database connection. Steps documented for manual execution.

---

### 5C) Functional Smoke ⚠️

#### Verification Steps

1. **Create Deal → Move Stages:**
   ```bash
   # Create campaign (deal)
   curl -X POST http://localhost:8000/api/v1/deals \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"campaign_id": "...", "stage": "lead"}'
   
   # Update stage
   curl -X PATCH http://localhost:8000/api/v1/deals/{campaign_id}/stage \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"stage": "qualified"}'
   ```

2. **Create IO → Set Flight:**
   ```bash
   # Create IO
   curl -X POST http://localhost:8000/api/v1/io \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"campaign_id": "...", "flight_start": "2025-11-15", "flight_end": "2025-12-15"}'
   
   # Update status to completed (triggers io.delivered event)
   curl -X PATCH http://localhost:8000/api/v1/io/{io_id}/status \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"status": "completed"}'
   ```

3. **Call Matchmaking Endpoint:**
   ```bash
   curl -X POST "http://localhost:8000/api/match/recalculate?advertiser_id=...&podcast_id=..." \
     -H "Authorization: Bearer $TOKEN"
   ```

4. **Verify Events Emitted:**
   ```sql
   SELECT event_type, properties FROM events 
   WHERE event_type IN ('deal.stage_changed', 'io.scheduled', 'io.delivered', 'match.recalculated')
   ORDER BY created_at DESC LIMIT 10;
   ```

#### Status
⚠️ **PENDING** - Requires API server and database. Steps documented for manual execution.

---

### 5D) Dashboard Snapshot ⚠️

#### Verification Steps
1. **Access Creator Dashboard:**
   ```bash
   curl http://localhost:8000/api/v1/dashboard/creator \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Access Advertiser Dashboard:**
   ```bash
   curl http://localhost:8000/api/v1/dashboard/advertiser \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Access Ops Dashboard:**
   ```bash
   curl http://localhost:8000/api/v1/dashboard/ops \
     -H "Authorization: Bearer $TOKEN"
   ```

4. **Verify Frontend Renders:**
   - Navigate to `/dashboard` in browser
   - Verify new cards display with seed data

#### Status
⚠️ **PENDING** - Requires frontend server. Steps documented for manual execution.

---

### 5E) Rollback Rehearsal ⚠️

#### Verification Steps
1. **Test Rollback (on throwaway DB):**
   ```bash
   PGURL="postgresql://..." ./scripts/db_rollback.sh migrations/20251113T114706Z
   ```

2. **Verify Pre-State:**
   ```sql
   -- Check index dropped
   SELECT 1 FROM pg_class WHERE relname='ux_metrics_daily_day_ep_source';
   -- Should return 0 rows
   
   -- Check policies dropped
   SELECT 1 FROM pg_policies WHERE tablename='matches';
   -- Should return 0 rows (if policies were added)
   ```

#### Status
⚠️ **PENDING** - Requires throwaway database. Steps documented for manual execution.

---

## Summary

### Completed ✅
- Schema diff check (dry-run)
- Migration scripts created and validated
- Code changes implemented
- Documentation complete

### Pending ⚠️
- Seed & smoke tests (requires DB)
- Functional smoke tests (requires API server)
- Dashboard snapshot (requires frontend)
- Rollback rehearsal (requires throwaway DB)

## Gate Status

⚠️ **CONDITIONAL PASS** - Code changes complete. Manual verification required.

**Recommendations:**
1. Run migration on development database
2. Test new endpoints with sample data
3. Verify events are emitted correctly
4. Test rollback on throwaway database
5. Update verification report with actual results

---

## Next Steps

Proceed to Phase 6 (Handoff Docs) with note that manual verification is required.
