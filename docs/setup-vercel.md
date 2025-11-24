# Vercel Setup Guide

**Last Updated:** 2024  
**Purpose:** Complete guide for setting up Vercel for frontend deployment

---

## Quick Setup

### 1. Create Vercel Account

1. Go to: https://vercel.com/signup
2. Sign up with GitHub (recommended for easy integration)
3. Complete account setup

### 2. Connect Repository

**Option A: Via Vercel Dashboard (Recommended)**

1. Go to: https://vercel.com/new
2. Click "Import Git Repository"
3. Select your repository
4. Configure project:
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `.next` (auto-detected)
   - **Install Command:** `npm ci` (auto-detected)
5. Click "Deploy"

**Option B: Via Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project
cd frontend
vercel link

# Deploy
vercel
```

---

## Project Configuration

### Root Directory

**Important:** Set root directory to `frontend` since the Next.js app is in a subdirectory.

**In Vercel Dashboard:**
1. Go to Project Settings → General
2. Set "Root Directory" to `frontend`
3. Save

**Or use `vercel.json` (already configured):**

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

---

## Environment Variables

### Required Variables

Set these in **Vercel Dashboard → Project Settings → Environment Variables**:

**Production:**
- `NEXT_PUBLIC_API_URL` = `https://api.yourdomain.com`
- `NEXT_PUBLIC_SITE_URL` = `https://yourdomain.com`
- `NEXT_PUBLIC_SUPABASE_URL` = `https://[PROJECT-REF].supabase.co` (if using Supabase)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `[ANON-KEY]` (if using Supabase)

**Preview:**
- Same as production (or use staging URLs)

**Development:**
- `NEXT_PUBLIC_API_URL` = `http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL` = `http://localhost:3000`

### Setting Variables

**Via Dashboard:**
1. Go to Project Settings → Environment Variables
2. Click "Add New"
3. Enter variable name and value
4. Select environments (Production, Preview, Development)
5. Click "Save"

**Via CLI:**
```bash
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_SITE_URL production
```

**Bulk Import:**
```bash
# Pull existing variables
vercel env pull .env.local

# Edit .env.local
# Push back
vercel env push .env.local
```

---

## GitHub Integration

### Enable Automatic Deployments

1. Go to Project Settings → Git
2. Connect repository (if not already connected)
3. Configure:
   - **Production Branch:** `main`
   - **Preview Deployments:** Enabled
   - **Automatic Deployments:** Enabled

### Deploy Hooks

**Production Deployment:**
- Triggered on: Push to `main` branch
- URL: `https://yourdomain.com`

**Preview Deployment:**
- Triggered on: Pull requests
- URL: `https://your-project-[hash].vercel.app`

---

## Vercel Token for CI/CD

### Generate Token

1. Go to: https://vercel.com/account/tokens
2. Click "Create Token"
3. Name: `GitHub Actions CI/CD`
4. Scope: `Full Account`
5. Click "Create"
6. **Copy token immediately** (won't be shown again)

### Add to GitHub Secrets

```bash
# Via GitHub CLI
gh secret set VERCEL_TOKEN

# Or via GitHub Web UI
# Settings → Secrets → Actions → New repository secret
```

---

## Custom Domain Setup

### Add Domain

1. Go to Project Settings → Domains
2. Click "Add Domain"
3. Enter domain: `yourdomain.com`
4. Follow DNS configuration instructions

### DNS Configuration

**For Apex Domain (`yourdomain.com`):**
```
Type: A
Name: @
Value: 76.76.21.21 (Vercel IP)
```

**For Subdomain (`www.yourdomain.com`):**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**For Subdomain (`staging.yourdomain.com`):**
```
Type: CNAME
Name: staging
Value: cname.vercel-dns.com
```

### SSL Certificate

- Vercel automatically provisions SSL certificates via Let's Encrypt
- No manual configuration needed
- Certificate renews automatically

---

## Build Settings

### Verify Build Configuration

**In Vercel Dashboard → Settings → General:**

- **Framework:** Next.js (auto-detected)
- **Build Command:** `npm run build` (auto-detected)
- **Output Directory:** `.next` (auto-detected)
- **Install Command:** `npm ci` (auto-detected)
- **Node Version:** 20.x (from `package.json` engines)

### Custom Build Settings

If needed, override in `vercel.json`:

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm ci"
}
```

---

## Preview Deployments

### Automatic Previews

- Created automatically for every pull request
- URL format: `https://your-project-[pr-number]-[hash].vercel.app`
- Uses preview environment variables
- Commented on PR with preview URL

### Manual Previews

```bash
# Deploy preview
vercel

# Deploy to specific branch
vercel --target production
```

---

## Monitoring & Analytics

### Vercel Analytics (Optional)

1. Go to Project Settings → Analytics
2. Enable "Web Analytics"
3. View metrics in Vercel dashboard

### Speed Insights (Optional)

1. Go to Project Settings → Speed Insights
2. Enable "Speed Insights"
3. View Core Web Vitals in dashboard

---

## Troubleshooting

### Build Failures

**Issue:** Build fails with module not found

**Solutions:**
1. Verify `package-lock.json` is committed
2. Check Node version matches `package.json` engines
3. Clear build cache: Project Settings → General → Clear Build Cache
4. Check build logs for specific errors

### Environment Variables Not Available

**Issue:** `process.env.NEXT_PUBLIC_*` is undefined

**Solutions:**
1. Verify variable is prefixed with `NEXT_PUBLIC_*`
2. Check variable is set in correct environment
3. Rebuild deployment after adding variable
4. Check `next.config.js` includes variable

### Domain Not Working

**Issue:** Domain shows "Not Found" or SSL error

**Solutions:**
1. Verify DNS records are correct
2. Wait for DNS propagation (up to 48 hours)
3. Check domain is added in Vercel dashboard
4. Verify SSL certificate is active (may take a few minutes)

### Deployment Not Triggered

**Issue:** Push to main doesn't trigger deployment

**Solutions:**
1. Verify GitHub integration is connected
2. Check branch name matches production branch (`main`)
3. Verify Vercel app is linked to correct repository
4. Check GitHub webhook is active

---

## CI/CD Integration

### GitHub Actions Deployment

The repository includes `.github/workflows/frontend-ci-deploy.yml` which:
- Builds and tests on PRs
- Deploys preview on PRs
- Deploys production on push to `main`

**Requirements:**
- `VERCEL_TOKEN` set in GitHub Secrets
- Vercel project linked to GitHub repository

### Manual Deployment via CLI

```bash
# Install CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod
```

---

## Cost & Limits

### Free Tier (Hobby)

- Unlimited personal projects
- 100 GB bandwidth/month
- 100 serverless function executions/day
- Automatic HTTPS
- Preview deployments

### Pro Tier ($20/month per user)

- Unlimited bandwidth
- Unlimited serverless function executions
- Team collaboration
- Password protection
- Analytics

**Recommendation:** Start with Free tier, upgrade when needed.

---

## Quick Reference

### Vercel CLI Commands

```bash
# Login
vercel login

# Link project
vercel link

# Deploy preview
vercel

# Deploy production
vercel --prod

# List deployments
vercel ls

# View logs
vercel logs

# Environment variables
vercel env add VARIABLE_NAME
vercel env pull .env.local
vercel env push .env.local
```

### Dashboard URLs

- **Projects:** https://vercel.com/dashboard
- **Project Settings:** https://vercel.com/[username]/[project]/settings
- **Deployments:** https://vercel.com/[username]/[project]/deployments
- **Environment Variables:** https://vercel.com/[username]/[project]/settings/environment-variables

---

## Next Steps

1. ✅ Create Vercel account
2. ✅ Connect GitHub repository
3. ✅ Configure root directory (`frontend`)
4. ✅ Set environment variables
5. ✅ Generate Vercel token for CI/CD
6. ✅ Add token to GitHub Secrets
7. ✅ Test deployment
8. ✅ Set up custom domain (optional)

For detailed frontend hosting strategy, see: `docs/frontend-hosting-strategy.md`
