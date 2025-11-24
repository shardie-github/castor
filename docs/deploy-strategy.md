# Deployment Strategy

**Last Updated:** 2024-12  
**Status:** Canonical deployment strategy  
**Purpose:** Define the source of truth for Preview and Production deployments

---

## Canonical Deploy Path

### Preview Deployments (Pull Requests)

**Trigger:** Pull requests to `main` branch

**Workflow:** `.github/workflows/frontend-ci-deploy.yml`

**Process:**
1. PR opened or updated → Workflow triggers
2. `build-and-test` job runs:
   - Lint (`npm run lint`)
   - Type check (`npm run type-check`)
   - Tests (`npm test`)
   - Build (`npm run build`)
3. On success, `deploy-preview` job runs:
   - Install Vercel CLI
   - Pull Vercel environment variables (`vercel pull --environment=preview`)
   - Deploy to Vercel Preview (`vercel deploy --prebuilt`)
4. Preview URL available in PR comments (via Vercel bot if Git Integration enabled, or manual)

**Environment:** Preview (uses Vercel Preview environment variables)

**URL Pattern:** `https://podcast-analytics-frontend-<hash>.vercel.app`

---

### Production Deployments (Main Branch)

**Trigger:** Push to `main` branch

**Workflow:** `.github/workflows/frontend-ci-deploy.yml`

**Process:**
1. Push to `main` → Workflow triggers
2. `build-and-test` job runs (same as Preview)
3. On success, `deploy-production` job runs:
   - Install Vercel CLI
   - Pull Vercel environment variables (`vercel pull --environment=production`)
   - Build for production (`npm run build`)
   - Deploy to Vercel Production (`vercel deploy --prebuilt --prod`)
4. Production URL updated (configured in Vercel project settings)

**Environment:** Production (uses Vercel Production environment variables)

**URL:** Configured custom domain or `https://podcast-analytics-frontend.vercel.app`

---

## Hosting Platform

**Canonical Host:** **Vercel**

**Rationale:**
- Next.js 14 optimized for Vercel
- Zero-config deployments
- Automatic HTTPS
- Preview deployments for PRs
- Excellent developer experience
- Free tier suitable for development

**Alternative:** None (Vercel is the single source of truth for frontend hosting)

---

## Workflow Mapping

### Preview Deployments

| Branch | Event | Workflow | Job | Environment |
|--------|-------|----------|-----|-------------|
| Any → `main` | `pull_request` | `frontend-ci-deploy.yml` | `deploy-preview` | Preview |

### Production Deployments

| Branch | Event | Workflow | Job | Environment |
|--------|-------|----------|-----|-------------|
| `main` | `push` | `frontend-ci-deploy.yml` | `deploy-production` | Production |

---

## Vercel Project Configuration

### Project Details

**Project Name:** `podcast-analytics-frontend` (or as configured in Vercel)

**Root Directory:** `frontend` (configured in Vercel project settings)

**Build Command:** `npm run build` (auto-detected by Vercel)

**Output Directory:** `.next` (auto-detected by Vercel)

**Install Command:** `npm ci` (uses package-lock.json)

### Project IDs (from Secrets)

- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID

**Note:** These are stored in GitHub Secrets and used by CI workflows.

---

## Git Integration Strategy

**Decision:** Use **GitHub Actions (CLI-based)** as primary deployment method

**Rationale:**
- More control over deployment process
- Can run tests/builds before deploy
- Can handle complex multi-step deployments
- Better integration with CI/CD pipeline

**Vercel Git Integration:** **DISABLED** (to avoid conflicts)

**Note:** If Vercel Git Integration is enabled, it will conflict with GitHub Actions deployments. Choose one approach:
- **Option A:** Use GitHub Actions (recommended) - Disable Vercel Git Integration
- **Option B:** Use Vercel Git Integration - Remove Vercel CLI steps from GitHub Actions

**Current Choice:** Option A (GitHub Actions)

---

## Environment Variables

### Required Vercel Environment Variables

**Production:**
- `NEXT_PUBLIC_API_URL` - Production backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (if using)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (if using)
- `NEXT_PUBLIC_SITE_URL` - Production site URL

**Preview:**
- Same as Production (or use staging URLs)

**Development:**
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL=http://localhost:3000`

### Required GitHub Secrets

**For CI/CD:**
- `VERCEL_TOKEN` - Vercel API token (required)
- `VERCEL_ORG_ID` - Vercel organization ID (optional, but recommended)
- `VERCEL_PROJECT_ID` - Vercel project ID (optional, but recommended)
- `NEXT_PUBLIC_API_URL` - Backend API URL for builds
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL (if using)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (if using)
- `NEXT_PUBLIC_SITE_URL` - Site URL for builds

**See:** `docs/env-and-secrets.md` for complete mapping

---

## Deployment Verification

### Preview Deployment Verification

**Checklist:**
- [ ] PR created → Workflow runs
- [ ] `build-and-test` job passes
- [ ] `deploy-preview` job runs
- [ ] Preview URL appears in PR (or Vercel dashboard)
- [ ] Preview site loads correctly
- [ ] Environment variables are correct (check browser console)

### Production Deployment Verification

**Checklist:**
- [ ] Push to `main` → Workflow runs
- [ ] `build-and-test` job passes
- [ ] `deploy-production` job runs
- [ ] Production URL updated (check Vercel dashboard)
- [ ] Production site loads correctly
- [ ] Environment variables are correct
- [ ] Smoke tests pass (if configured)

---

## Failure Handling

### If Preview Deployment Fails

1. Check GitHub Actions logs for error
2. Verify secrets are set (`VERCEL_TOKEN`, etc.)
3. Check Vercel project is linked correctly
4. Verify environment variables in Vercel dashboard
5. Check `package-lock.json` exists and is up to date

### If Production Deployment Fails

1. Check GitHub Actions logs for error
2. Verify all required secrets are set
3. Check Vercel project configuration
4. Verify production environment variables
5. Check for build errors (TypeScript, lint, etc.)
6. Review `vercel.json` configuration

**See:** `docs/vercel-troubleshooting.md` for detailed troubleshooting

---

## Summary

**Canonical Deploy Path:**
- **Preview:** PR → `frontend-ci-deploy.yml` → `deploy-preview` → Vercel Preview
- **Production:** Push to `main` → `frontend-ci-deploy.yml` → `deploy-production` → Vercel Production

**Hosting:** Vercel (single source of truth)

**Deployment Method:** GitHub Actions with Vercel CLI (Vercel Git Integration disabled)

**Workflow:** `.github/workflows/frontend-ci-deploy.yml`

**Next Steps:** See `docs/deploy-reliability-plan.md` for implementation details
