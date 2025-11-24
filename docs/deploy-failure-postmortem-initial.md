# Deployment Failure Postmortem - Initial Analysis

**Date:** 2024-12  
**Status:** Investigation Complete  
**Purpose:** Identify root causes of Vercel Preview and Production deployment failures

---

## Executive Summary

After examining the repository's CI/CD configuration, multiple failure modes have been identified that prevent reliable Vercel deployments for both Preview (PRs) and Production (main branch pushes).

---

## Existing Workflows Analysis

### 1. Frontend CI & Deploy (`frontend-ci-deploy.yml`)

**Triggers:**
- `pull_request` to `main` or `develop` (with path filters)
- `push` to `main` or `develop` (with path filters)
- `workflow_dispatch`

**Path Filters:**
```yaml
paths:
  - 'frontend/**'
  - '.github/workflows/frontend-ci-deploy.yml'
```

**Jobs:**
1. `build-and-test` - Runs lint, type-check, test, build
2. `deploy-preview` - Condition: `if: github.event_name == 'pull_request'`
3. `deploy-production` - Condition: `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`

**Status:** ⚠️ **CRITICAL ISSUES IDENTIFIED**

---

### 2. Deploy Production (`deploy.yml`)

**Triggers:**
- `push` to `main`
- `workflow_dispatch`

**Jobs:**
1. `deploy-production` - Full production deployment including:
   - Database migrations
   - Docker image build/push
   - Frontend Vercel deploy (basic CLI command)
   - Backend deploy (placeholder)
   - Smoke tests

**Status:** ⚠️ **ISSUES IDENTIFIED**

---

## Failure Mode 1: Workflow Not Triggering

### Issue 1.1: Path Filters Too Restrictive

**Problem:**
- `frontend-ci-deploy.yml` only runs when changes are in `frontend/**` or the workflow file itself
- If a PR changes:
  - `.github/workflows/*` (other workflows)
  - `docs/**`
  - `vercel.json` (root level)
  - `package.json` dependencies (if updated)
  - The workflow **will not run**, preventing Preview deployments

**Impact:** HIGH
- PRs that don't touch `frontend/**` won't get Preview deployments
- Changes to deployment config won't trigger validation

**Fix Required:** Remove or broaden path filters, or add additional paths

---

### Issue 1.2: Branch Filter Mismatch

**Problem:**
- `deploy-production` job in `frontend-ci-deploy.yml` checks: `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`
- But workflow triggers on `push` to `main` OR `develop`
- This means pushes to `develop` will trigger the workflow but skip production deploy (correct), but the condition is redundant

**Impact:** LOW (works correctly, but confusing)

**Fix Required:** Clarify or simplify conditions

---

## Failure Mode 2: Deploy Step Skipped

### Issue 2.1: Missing Job Dependencies

**Problem:**
- `deploy-preview` and `deploy-production` both depend on `build-and-test` via `needs: build-and-test`
- If `build-and-test` fails, deploy jobs are skipped (correct behavior)
- However, if `build-and-test` is skipped due to path filters, deploy jobs are also skipped

**Impact:** MEDIUM
- Deploy jobs won't run if build job doesn't run

**Fix Required:** Ensure build job always runs when deploy is needed

---

### Issue 2.2: Concurrency Settings

**Problem:**
- Preview deploy uses: `group: frontend-deploy-${{ github.head_ref }}` with `cancel-in-progress: false`
- Production deploy uses: `group: frontend-deploy-production` with `cancel-in-progress: false`
- `cancel-in-progress: false` means multiple deployments can run simultaneously, potentially causing conflicts

**Impact:** MEDIUM
- Could cause race conditions or duplicate deployments

**Fix Required:** Set `cancel-in-progress: true` to cancel older runs when new commits arrive

---

## Failure Mode 3: Workflow Runs But Fails

### Issue 3.1: Missing package-lock.json

**Problem:**
- Workflow references `frontend/package-lock.json` in cache config: `cache-dependency-path: frontend/package-lock.json`
- Uses `npm ci` which requires `package-lock.json`
- **package-lock.json does not exist** in the frontend directory

**Impact:** CRITICAL
- `npm ci` will fail immediately
- Build job will fail
- Deploy jobs will never run

**Fix Required:** Generate and commit `package-lock.json`

---

### Issue 3.2: Node Version Mismatch

**Problem:**
- Workflow uses `NODE_VERSION: '20'`
- `package.json` specifies `"node": ">=20.0.0"` (already correct)
- But no `.nvmrc` or `.node-version` file for local consistency

**Impact:** LOW
- CI uses correct version, but local dev might differ

**Fix Required:** Add `.nvmrc` file for consistency

---

### Issue 3.3: Missing Vercel Secrets

**Problem:**
- Workflow references secrets:
  - `VERCEL_TOKEN`
  - `VERCEL_ORG_ID`
  - `VERCEL_PROJECT_ID`
- If these are missing, deployment will fail silently or skip
- No validation that secrets exist before attempting deploy

**Impact:** CRITICAL
- Deployments will fail if secrets are not configured

**Fix Required:** Add secret validation and clear error messages

---

### Issue 3.4: Incorrect Vercel Deploy Commands

**Problem:**
- Preview deploy uses: `vercel deploy --prebuilt --token=$VERCEL_TOKEN`
- But `vercel pull` is run before deploy, which may not pull the correct environment
- Production deploy rebuilds unnecessarily: runs `npm run build` again after `vercel pull`
- `vercel pull` may fail silently with `|| echo "Vercel pull failed, continuing..."`

**Impact:** HIGH
- Preview deployments may use wrong environment variables
- Production deployments waste time rebuilding
- Silent failures hide real issues

**Fix Required:** Fix Vercel CLI command sequence and error handling

---

### Issue 3.5: Environment Variables Not Passed Correctly

**Problem:**
- Build step uses fallback values: `NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL || 'http://localhost:8000' }}`
- Deploy step uses secrets directly without fallbacks
- If secrets are missing, build succeeds but deploy may fail
- `vercel pull` should pull env vars from Vercel, but if project isn't linked, it fails

**Impact:** MEDIUM
- Inconsistent behavior between build and deploy

**Fix Required:** Ensure consistent env var handling

---

## Failure Mode 4: Vercel Project Misconfiguration

### Issue 4.1: Vercel Git Integration Conflict

**Problem:**
- Workflow uses Vercel CLI to deploy
- If Vercel Git Integration is also enabled, both will try to deploy
- This can cause:
  - Duplicate deployments
  - Race conditions
  - Confusion about which deployment is "canonical"

**Impact:** HIGH
- Unclear deployment source
- Potential conflicts

**Fix Required:** Document whether to use Git Integration OR CLI, not both

---

### Issue 4.2: Missing Vercel Project Link

**Problem:**
- Workflow runs `vercel pull` but if project isn't linked (no `.vercel/project.json`), it may fail
- `vercel deploy` without proper project linking may deploy to wrong project or create new project

**Impact:** CRITICAL
- Deployments may go to wrong project
- Or fail entirely

**Fix Required:** Ensure project is properly linked or use explicit project flags

---

### Issue 4.3: vercel.json Configuration

**Problem:**
- `vercel.json` exists at root level
- References `frontend/package.json` for build
- Uses `@supabase_url` and `@supabase_anon_key` syntax which requires Vercel env vars
- If Vercel project isn't configured with these vars, build may fail

**Impact:** MEDIUM
- Build failures if env vars not set in Vercel

**Fix Required:** Document required Vercel env vars

---

## Failure Mode 5: Deploy.yml Workflow Issues

### Issue 5.1: Basic Vercel Deploy Step

**Problem:**
- `deploy.yml` has a simple Vercel deploy step:
  ```yaml
  vercel --prod --token $VERCEL_TOKEN --yes || echo "Vercel deployment check completed"
  ```
- This doesn't:
  - Pull environment variables first
  - Build the project
  - Use `--prebuilt` flag
  - Handle errors properly (silently fails)

**Impact:** HIGH
- Production deployments from `deploy.yml` will likely fail or deploy incorrectly

**Fix Required:** Use same comprehensive deploy steps as `frontend-ci-deploy.yml`

---

## Summary of Critical Issues

### 🔴 CRITICAL (Must Fix)

1. **Missing package-lock.json** - Build will fail immediately
2. **Missing Vercel secrets** - Deployments will fail silently
3. **Vercel project not linked** - Deployments may go to wrong project
4. **Incorrect Vercel CLI commands** - Deployments may fail or deploy incorrectly

### 🟡 HIGH (Should Fix)

1. **Path filters too restrictive** - Workflows won't run on many PRs
2. **Vercel Git Integration conflict** - Unclear deployment source
3. **deploy.yml Vercel step incomplete** - Production deploys may fail
4. **Silent error handling** - Failures are hidden

### 🟢 MEDIUM (Nice to Fix)

1. **Concurrency settings** - Could cause race conditions
2. **Environment variable inconsistencies** - May cause confusion
3. **Missing .nvmrc** - Local dev inconsistency

---

## Next Steps

1. Generate `package-lock.json` for frontend
2. Fix Vercel CLI command sequence
3. Remove or adjust path filters
4. Add secret validation
5. Document Vercel project setup requirements
6. Decide on Git Integration vs CLI approach
7. Fix `deploy.yml` Vercel step

---

**See:** `docs/deploy-strategy.md` for intended deployment flow  
**See:** `docs/deploy-failure-postmortem-final.md` for fixes applied
