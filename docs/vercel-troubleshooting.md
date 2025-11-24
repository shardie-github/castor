# Vercel Troubleshooting Guide

**Last Updated:** 2024-12  
**Purpose:** Troubleshoot Vercel Preview and Production deployment issues

---

## Quick Diagnosis Checklist

### If Preview Deployment Doesn't Appear

1. ✅ Check GitHub Actions workflow ran (`frontend-ci-deploy.yml`)
2. ✅ Verify `build-and-test` job passed
3. ✅ Verify `deploy-preview` job ran (not skipped)
4. ✅ Check `VERCEL_TOKEN` secret is set in GitHub Secrets
5. ✅ Check Vercel project is linked correctly
6. ✅ Check Vercel dashboard for deployment status

### If Production Deployment Doesn't Trigger

1. ✅ Check push was to `main` branch (not `develop` or other)
2. ✅ Verify workflow triggered (`frontend-ci-deploy.yml`)
3. ✅ Verify `build-and-test` job passed
4. ✅ Verify `deploy-production` job ran (not skipped)
5. ✅ Check `VERCEL_TOKEN` secret is set
6. ✅ Check Vercel project configuration

---

## Common Issues and Solutions

### Issue 1: "Vercel token not set, skipping deployment"

**Symptoms:**
- Workflow runs but deploy step is skipped
- Log shows: "Vercel token not set, skipping deployment"

**Root Cause:**
- `VERCEL_TOKEN` secret is not configured in GitHub Secrets

**Solution:**
1. Go to GitHub Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `VERCEL_TOKEN`
4. Value: Get from Vercel Dashboard → Settings → Tokens → Create Token
5. Save and retry deployment

**Prevention:**
- Workflow now validates `VERCEL_TOKEN` and fails early with clear error message

---

### Issue 2: "Vercel pull failed, continuing..."

**Symptoms:**
- `vercel pull` command fails silently
- Deployment may proceed with wrong environment variables

**Root Cause:**
- Vercel project not linked (no `.vercel/project.json`)
- Wrong `VERCEL_ORG_ID` or `VERCEL_PROJECT_ID`
- Invalid `VERCEL_TOKEN`

**Solution:**

**Option A: Link Project via CLI (Recommended)**
```bash
cd frontend
vercel link
# Follow prompts to select org and project
# This creates .vercel/project.json
```

**Option B: Set Secrets Explicitly**
1. Get `VERCEL_ORG_ID` from Vercel Dashboard → Settings → General → Team ID
2. Get `VERCEL_PROJECT_ID` from Vercel Dashboard → Project Settings → General → Project ID
3. Add to GitHub Secrets:
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

**Prevention:**
- Workflow now validates secrets and fails if `VERCEL_TOKEN` is missing
- Warnings shown if `VERCEL_ORG_ID` or `VERCEL_PROJECT_ID` are missing

---

### Issue 3: "Deployment goes to wrong project"

**Symptoms:**
- Preview/Production deployments appear in unexpected Vercel project
- Multiple projects receive deployments

**Root Cause:**
- Vercel Git Integration enabled AND GitHub Actions deploying (conflict)
- Wrong `VERCEL_PROJECT_ID` in secrets
- Project not properly linked

**Solution:**

**Step 1: Disable Vercel Git Integration (if using GitHub Actions)**
1. Go to Vercel Dashboard → Project Settings → Git
2. Click "Disconnect" or "Remove Git Integration"
3. This prevents duplicate deployments

**Step 2: Verify Project Linking**
```bash
cd frontend
vercel link
# Verify correct org and project selected
```

**Step 3: Verify Secrets**
- Check `VERCEL_PROJECT_ID` matches intended project
- Check `VERCEL_ORG_ID` matches intended organization

**Prevention:**
- Documented in `docs/deploy-strategy.md` that Git Integration should be disabled
- Use GitHub Actions as single source of truth

---

### Issue 4: "Build fails with missing environment variables"

**Symptoms:**
- Build step fails with errors like "NEXT_PUBLIC_API_URL is undefined"
- TypeScript errors about missing env vars

**Root Cause:**
- Environment variables not set in Vercel dashboard
- Or not passed correctly in GitHub Actions workflow

**Solution:**

**For Vercel Dashboard:**
1. Go to Vercel Dashboard → Project Settings → Environment Variables
2. Add variables for each environment:
   - Production: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, etc.
   - Preview: Same variables (or staging URLs)
   - Development: Local URLs

**For GitHub Actions:**
1. Go to GitHub Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_SITE_URL`

**Prevention:**
- See `docs/env-and-secrets.md` for complete mapping
- Workflow uses fallback values for non-critical vars

---

### Issue 5: "Preview deployment not created for PR"

**Symptoms:**
- PR opened but no Preview deployment appears
- Workflow doesn't run

**Root Cause:**
- Path filters preventing workflow from running (FIXED: removed path filters)
- Workflow disabled
- Branch protection blocking workflow

**Solution:**
1. Check GitHub Actions tab → See if workflow ran
2. If workflow didn't run:
   - Check workflow file exists: `.github/workflows/frontend-ci-deploy.yml`
   - Check workflow syntax is valid
   - Check branch protection rules
3. If workflow ran but deploy skipped:
   - Check `deploy-preview` job logs
   - Verify `if: github.event_name == 'pull_request'` condition

**Prevention:**
- Path filters removed from workflow (now runs on all PRs)
- Clear error messages if deploy is skipped

---

### Issue 6: "Production deployment doesn't trigger on push to main"

**Symptoms:**
- Push to `main` but no production deployment
- Workflow doesn't run

**Root Cause:**
- Workflow not configured for `push` to `main`
- Branch protection blocking workflow
- Workflow file syntax error

**Solution:**
1. Check workflow file: `.github/workflows/frontend-ci-deploy.yml`
2. Verify trigger:
   ```yaml
   on:
     push:
       branches: [main]
   ```
3. Check GitHub Actions tab → See if workflow ran
4. Check `deploy-production` job condition:
   ```yaml
   if: github.ref == 'refs/heads/main' && github.event_name == 'push'
   ```

**Prevention:**
- Workflow configured correctly
- Clear job conditions

---

### Issue 7: "npm ci fails: package-lock.json not found"

**Symptoms:**
- Build job fails with "npm ci requires package-lock.json"
- Error: "Cannot find a package-lock.json file"

**Root Cause:**
- `package-lock.json` not committed to repository
- Lockfile deleted or not generated

**Solution:**
1. Generate lockfile:
   ```bash
   cd frontend
   npm install
   ```
2. Commit `package-lock.json`:
   ```bash
   git add frontend/package-lock.json
   git commit -m "Add package-lock.json"
   git push
   ```

**Prevention:**
- `package-lock.json` is now committed to repository
- Workflow uses `npm ci` which requires lockfile

---

### Issue 8: "Deployment succeeds but site shows errors"

**Symptoms:**
- Deployment completes successfully
- But site shows runtime errors (API connection failures, etc.)

**Root Cause:**
- Environment variables not set correctly in Vercel
- Wrong API URLs
- CORS issues

**Solution:**
1. Check Vercel Dashboard → Project Settings → Environment Variables
2. Verify variables are set for correct environment (Production vs Preview)
3. Check browser console for errors
4. Verify API URLs are correct:
   - Production: `https://api.yourdomain.com`
   - Preview: May use staging API or production API
5. Check CORS settings on backend

**Prevention:**
- Documented env var requirements
- Clear separation between Preview and Production env vars

---

## Verifying Vercel Project Configuration

### Check Project is Linked

**Via CLI:**
```bash
cd frontend
vercel link
# Should show current project or prompt to link
```

**Via Dashboard:**
1. Go to Vercel Dashboard → Project Settings → General
2. Check "Project ID" matches `VERCEL_PROJECT_ID` secret
3. Check "Team" matches `VERCEL_ORG_ID` secret

### Check Git Integration Status

**Via Dashboard:**
1. Go to Vercel Dashboard → Project Settings → Git
2. If connected, shows GitHub repository
3. **Recommendation:** Disconnect if using GitHub Actions for deployments

**Why Disable:**
- Prevents duplicate deployments (Git Integration + GitHub Actions)
- GitHub Actions provides more control
- Single source of truth for deployments

---

## Environment Variable Checklist

### Required for Production

- [ ] `NEXT_PUBLIC_API_URL` - Production backend API URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL (if using)
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (if using)
- [ ] `NEXT_PUBLIC_SITE_URL` - Production site URL

### Required for Preview

- [ ] Same as Production (or use staging URLs)

### Required GitHub Secrets

- [ ] `VERCEL_TOKEN` - Vercel API token (REQUIRED)
- [ ] `VERCEL_ORG_ID` - Vercel organization ID (recommended)
- [ ] `VERCEL_PROJECT_ID` - Vercel project ID (recommended)
- [ ] `NEXT_PUBLIC_API_URL` - For builds
- [ ] `NEXT_PUBLIC_SUPABASE_URL` - For builds (if using)
- [ ] `SUPABASE_ANON_KEY` - For builds (if using)
- [ ] `NEXT_PUBLIC_SITE_URL` - For builds

**See:** `docs/env-and-secrets.md` for complete list

---

## Testing Deployment Locally

### Test Vercel CLI Commands

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel@latest

# Link project (if not already linked)
vercel link

# Pull environment variables
vercel pull --environment=preview

# Build
npm run build

# Deploy preview
vercel deploy --prebuilt

# Deploy production (be careful!)
vercel deploy --prebuilt --prod
```

### Verify Environment Variables

```bash
# After vercel pull, check .vercel/.env.preview or .vercel/.env.production
cat .vercel/.env.preview
```

---

## Getting Help

### Vercel Support

- **Documentation:** https://vercel.com/docs
- **Support:** https://vercel.com/support
- **Status:** https://www.vercel-status.com

### GitHub Actions Logs

1. Go to GitHub Repository → Actions
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step to see error logs

### Common Error Messages

| Error | Solution |
|-------|----------|
| "Vercel token not set" | Add `VERCEL_TOKEN` to GitHub Secrets |
| "Project not found" | Verify `VERCEL_PROJECT_ID` is correct |
| "Unauthorized" | Regenerate `VERCEL_TOKEN` |
| "Build failed" | Check build logs, verify env vars |
| "Deployment timeout" | Check for infinite loops, optimize build |

---

## Summary

**Most Common Issues:**
1. Missing `VERCEL_TOKEN` secret → Add to GitHub Secrets
2. Project not linked → Run `vercel link` or set `VERCEL_PROJECT_ID`
3. Git Integration conflict → Disable Vercel Git Integration
4. Missing env vars → Set in Vercel Dashboard and GitHub Secrets

**Prevention:**
- Use `scripts/deploy-doctor.sh` to check configuration
- Follow `docs/deploy-strategy.md` for deployment flow
- Keep `docs/env-and-secrets.md` up to date

**Next Steps:**
- If issue persists, check `docs/deploy-reliability-plan.md`
- Run deploy-doctor script: `./scripts/deploy-doctor.sh`
