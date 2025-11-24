# CI/CD Overview

**Last Updated:** 2024  
**Purpose:** Overview of CI/CD workflows, required checks, and branch protection

---

## Active Workflows

### 1. CI (`ci.yml`)

**Triggers:**
- Pull requests to `main` or `develop`
- Push to `main` or `develop`

**Jobs:**
- `lint-backend` - Ruff + mypy
- `lint-frontend` - ESLint + TypeScript check
- `test-backend` - pytest with coverage (50% minimum)
- `test-frontend` - Jest tests
- `build-backend` - Docker build verification
- `build-frontend` - Next.js build

**Status:** ✅ Active and required

---

### 2. Frontend CI & Deploy (`frontend-ci-deploy.yml`)

**Triggers:**
- Pull requests (preview deployment)
- Push to `main` or `develop` (production/staging deployment)
- Manual dispatch

**Jobs:**
- `build-and-test` - Lint, type-check, test, build
- `deploy-preview` - Deploy to Vercel preview (PRs)
- `deploy-production` - Deploy to Vercel production (main branch)

**Status:** ✅ Active

---

### 3. Database Migrations (`db-migrate.yml`)

**Triggers:**
- Push to `main` (staging migration)
- Changes to `db/migrations/**`
- Manual dispatch (staging or production)

**Jobs:**
- `validate-migrations` - Validate migration files
- `migrate-staging` - Apply migrations to staging
- `migrate-production` - Apply migrations to production (manual only)

**Status:** ✅ Active

---

### 4. Deploy Production (`deploy.yml`)

**Triggers:**
- Push to `main`
- Manual dispatch

**Jobs:**
- `deploy-production` - Full production deployment
  - Run migrations
  - Build and push Docker image
  - Deploy frontend to Vercel
  - Deploy backend (placeholder)
  - Run smoke tests (placeholder)
  - Notify deployment

**Status:** ✅ Active (backend deployment needs completion)

---

### 5. Deploy Staging (`deploy-staging.yml`)

**Triggers:**
- Push to `develop`
- Manual dispatch

**Jobs:**
- `deploy-staging` - Full staging deployment
  - Run tests
  - Run migrations
  - Build and push Docker image
  - Deploy frontend to Vercel
  - Deploy backend (placeholder)
  - Run smoke tests (placeholder)

**Status:** ✅ Active (backend deployment needs completion)

---

### 6. Test Migrations (`test-migrations.yml`)

**Triggers:**
- Pull requests affecting migrations
- Manual dispatch

**Jobs:**
- `test-migrations` - Validate and test migrations against test database

**Status:** ✅ Active

---

## Obsolete/Deprecated Workflows

### 1. `ci.yml.new`

**Status:** ❌ Obsolete - Duplicate of `ci.yml`

**Action:** Delete this file

---

### 2. `nightly.yml.new`

**Status:** ⚠️ Review - May be useful but needs activation

**Content:** Security scans, migration validation, E2E tests, Aurora Doctor

**Recommendation:** 
- If useful, rename to `nightly.yml` and activate
- If not needed, delete

---

### 3. `nightly.yml` (if exists)

**Status:** ⚠️ Review - Check if actively used

**Recommendation:** Keep if useful, otherwise delete

---

### 4. `e2e-tests.yml`

**Status:** ⚠️ Optional - E2E tests exist but may not be required for PRs

**Content:** Playwright E2E tests

**Recommendation:**
- Keep for manual testing
- Don't require for PRs (too slow)
- Run in nightly workflow if needed

---

### 5. `aurora-doctor.yml`

**Status:** ⚠️ Optional - Health check automation

**Recommendation:**
- Keep if Aurora Prime is actively used
- Otherwise, delete or move to nightly

---

## Required Checks for Main Branch

### Minimum Required Checks

1. ✅ **lint-backend** - Backend linting (ruff, mypy)
2. ✅ **lint-frontend** - Frontend linting (ESLint, TypeScript)
3. ✅ **test-backend** - Backend tests with coverage
4. ✅ **test-frontend** - Frontend tests
5. ✅ **build-backend** - Backend Docker build
6. ✅ **build-frontend** - Frontend Next.js build

### Optional Checks (Not Required)

- ⚠️ **e2e-tests** - E2E tests (too slow for PRs, run nightly)
- ⚠️ **test-migrations** - Migration tests (only when migrations change)
- ⚠️ **aurora-doctor** - Health checks (run nightly)

---

## Branch Protection Recommendations

### Main Branch Protection

**Required Checks:**
- `lint-backend`
- `lint-frontend`
- `test-backend`
- `test-frontend`
- `build-backend`
- `build-frontend`

**Settings:**
- Require PR reviews: 1 approval
- Require status checks to pass: ✅
- Require branches to be up to date: ✅
- Require conversation resolution: ✅
- Do not allow force pushes: ✅
- Do not allow deletions: ✅

### Develop Branch Protection

**Required Checks:**
- Same as main (or subset)

**Settings:**
- Require PR reviews: Optional
- Require status checks to pass: ✅
- Allow force pushes: ❌
- Allow deletions: ❌

---

## Package Manager & Version Locking

### Frontend

**Package Manager:** npm  
**Lockfile:** `frontend/package-lock.json` ✅ Present

**Node Version:**
- CI: Node 20 (pinned in workflows)
- **Missing:** `engines` field in `package.json`

**Action Required:** Add `engines` field to `frontend/package.json`:
```json
{
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=9.0.0"
  }
}
```

### Backend

**Package Manager:** pip  
**Lockfile:** ❌ No `requirements.lock` or `Pipfile.lock`

**Python Version:**
- CI: Python 3.11 (pinned in workflows)
- **Missing:** `python_requires` in `setup.py` or `pyproject.toml`

**Action Required:** Consider adding version pinning (optional for pip, but recommended)

---

## CI Scripts in package.json

### Frontend Scripts

**Current:**
```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "type-check": "tsc --noEmit"
}
```

**Status:** ✅ Complete and matches CI

**Optional Addition:**
```json
{
  "ci:check": "npm run lint && npm run type-check && npm test -- --watchAll=false && npm run build"
}
```

### Backend Scripts

**Current:** Managed via Makefile

**Makefile Commands:**
- `make ci` - Run all CI checks
- `make lint` - Lint backend and frontend
- `make test` - Run all tests
- `make build` - Build backend and frontend

**Status:** ✅ Complete

---

## Dependency Automation

### Current Status

**Dependabot:** ❌ Not configured  
**Renovate:** ❌ Not configured

### Recommendation

**Add Dependabot** (simpler, GitHub-native):

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

**Benefits:**
- Automatic dependency updates
- Security vulnerability alerts
- Weekly schedule (not too frequent)

---

## Workflow Concurrency

### Current Concurrency Settings

**Frontend Deploy:**
- Preview: `frontend-deploy-${{ github.head_ref }}` ✅
- Production: `frontend-deploy-production` ✅

**Backend Deploy:**
- ❌ No concurrency settings (may cause conflicts)

### Recommendation

Add concurrency to backend deployment workflows:
```yaml
concurrency:
  group: backend-deploy-${{ github.ref }}
  cancel-in-progress: false
```

---

## CI Performance

### Current Job Times (Estimated)

- `lint-backend`: ~2 minutes
- `lint-frontend`: ~3 minutes
- `test-backend`: ~5 minutes
- `test-frontend`: ~3 minutes
- `build-backend`: ~5 minutes
- `build-frontend`: ~4 minutes

**Total PR Check Time:** ~22 minutes (parallel jobs)

### Optimization Opportunities

1. **Cache Dependencies:**
   - ✅ Frontend: npm cache configured
   - ✅ Backend: pip cache configured

2. **Parallel Jobs:**
   - ✅ Jobs run in parallel where possible

3. **Conditional Runs:**
   - ⚠️ Consider path-based triggers (only run relevant jobs)

---

## Summary

### ✅ What's Working

- Comprehensive CI pipeline
- Frontend deployment automation
- Database migration workflows
- Proper caching and parallelization

### ⚠️ Needs Attention

1. **Remove obsolete workflows:**
   - Delete `ci.yml.new`
   - Review `nightly.yml.new` (activate or delete)

2. **Add Node version pinning:**
   - Add `engines` to `frontend/package.json`

3. **Complete backend deployment:**
   - Replace placeholder steps in `deploy.yml` and `deploy-staging.yml`

4. **Add dependency automation:**
   - Configure Dependabot for npm and pip

5. **Branch protection:**
   - Configure required checks for main branch

### 📋 Action Items

- [ ] Delete `ci.yml.new`
- [ ] Review and activate/delete `nightly.yml.new`
- [ ] Add `engines` to `frontend/package.json`
- [ ] Create `.github/dependabot.yml`
- [ ] Configure branch protection rules
- [ ] Complete backend deployment workflows

---

**Next Steps:** See individual workflow files for details on each CI job.
