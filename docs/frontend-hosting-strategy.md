# Frontend Hosting Strategy

**Last Updated:** 2024  
**Status:** Canonical frontend hosting strategy

---

## Executive Summary

**Canonical Frontend Hosting:** **Vercel**

**Rationale:** Next.js 14 is optimized for Vercel, providing zero-config deployments, automatic HTTPS, preview deployments for PRs, and excellent developer experience. Free tier is suitable for development and early production.

---

## Current Frontend Stack

### Framework & Build
- **Framework:** Next.js 14.0.0 (App Router)
- **React:** 18.2.0
- **TypeScript:** 5.2.0
- **Package Manager:** npm (package-lock.json)
- **Build Tool:** Next.js built-in (Webpack)

### Configuration Files
- `frontend/next.config.js` - Next.js configuration
- `vercel.json` - Vercel deployment configuration (root level)
- `frontend/package.json` - Dependencies and scripts

### Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (optional)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (optional)
- `NEXT_PUBLIC_SITE_URL` - Site URL for metadata

---

## Vercel Configuration

### Current Setup

**Config File:** `vercel.json` (root level)

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
  ],
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase_url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase_anon_key"
  }
}
```

**Note:** The `@supabase_url` and `@supabase_anon_key` syntax refers to Vercel environment variables that must be set in the Vercel dashboard.

### Vercel Project Structure

**Root Directory:** `/workspace`  
**Frontend Directory:** `/workspace/frontend`  
**Build Command:** `cd frontend && npm run build` (auto-detected by Vercel)  
**Output Directory:** `frontend/.next` (auto-detected by Vercel)

---

## Deployment Strategy

### Preview Deployments (PRs)

**Trigger:** Pull requests to `main` or `develop`

**Workflow:**
1. GitHub Actions CI runs (`ci.yml`)
2. On success, Vercel automatically creates preview deployment
3. Preview URL: `https://podcast-analytics-<hash>.vercel.app`
4. Environment variables from Vercel project settings are used

**Benefits:**
- Automatic preview for every PR
- Isolated environment per PR
- Easy to share with stakeholders

### Staging Deployments

**Trigger:** Push to `develop` branch or manual via `workflow_dispatch`

**Workflow:**
1. GitHub Actions runs `deploy-staging.yml`
2. Runs tests and builds
3. Deploys to Vercel preview (or staging project)
4. Uses staging environment variables

**URL:** Configured in Vercel project settings (e.g., `staging.yourdomain.com`)

### Production Deployments

**Trigger:** Push to `main` branch or manual via `workflow_dispatch`

**Workflow:**
1. GitHub Actions runs `deploy.yml`
2. Runs tests and builds
3. Deploys to Vercel production
4. Uses production environment variables

**URL:** Configured in Vercel project settings (e.g., `yourdomain.com`)

---

## CI-First Deployment Flow

### Current Workflow: `.github/workflows/deploy.yml`

**Frontend Deployment Step:**
```yaml
- name: Deploy frontend to Vercel
  if: ${{ secrets.VERCEL_TOKEN != '' }}
  env:
    VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
    VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
    VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
    NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
    NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
  run: |
    echo "Deploying frontend to Vercel"
    cd frontend
    npm install -g vercel
    vercel --prod --token $VERCEL_TOKEN --yes || echo "Vercel deployment check completed"
```

### Recommended: Use Vercel GitHub Integration

**Better Approach:** Use Vercel's GitHub integration instead of CLI in CI

**Benefits:**
- Automatic deployments on push
- No need for VERCEL_TOKEN in GitHub Secrets
- Better integration with Vercel dashboard
- Automatic preview deployments for PRs

**Setup:**
1. Connect GitHub repo to Vercel via Vercel dashboard
2. Configure build settings:
   - Root Directory: `frontend`
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)
3. Set environment variables in Vercel dashboard
4. Remove Vercel CLI deployment step from GitHub Actions (optional)

**Alternative:** Keep GitHub Actions deployment for more control, but use Vercel GitHub integration for automatic previews.

---

## Environment Variables Management

### Required Vercel Environment Variables

**Public (Client-Side):**
- `NEXT_PUBLIC_API_URL` - Backend API URL (e.g., `https://api.yourdomain.com`)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (if using Supabase features)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (if using Supabase features)
- `NEXT_PUBLIC_SITE_URL` - Site URL (e.g., `https://yourdomain.com`)

**Private (Server-Side):**
- None required for frontend-only deployment (backend runs separately)

### Environment-Specific Variables

**Development:**
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL=http://localhost:3000`

**Staging:**
- `NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com`
- `NEXT_PUBLIC_SITE_URL=https://staging.yourdomain.com`

**Production:**
- `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
- `NEXT_PUBLIC_SITE_URL=https://yourdomain.com`

### Setting Variables in Vercel

1. **Via Dashboard:**
   - Go to Project Settings → Environment Variables
   - Add variables for each environment (Production, Preview, Development)
   - Variables are automatically injected at build time

2. **Via CLI:**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production
   ```

3. **Via GitHub Actions:**
   - Use `vercel env pull` to sync variables
   - Or set in workflow (less secure, not recommended)

---

## Build & Deployment Process

### Build Process

1. **Install Dependencies:**
   ```bash
   cd frontend
   npm ci  # Uses package-lock.json for reproducible builds
   ```

2. **Type Check:**
   ```bash
   npm run type-check  # TypeScript validation
   ```

3. **Lint:**
   ```bash
   npm run lint  # ESLint
   ```

4. **Build:**
   ```bash
   npm run build  # Next.js production build
   ```

5. **Output:**
   - Static pages: `frontend/.next/static`
   - Server components: `frontend/.next/server`
   - Build manifest: `frontend/.next/build-manifest.json`

### Vercel Build Settings

**Auto-Detected:**
- Framework: Next.js
- Build Command: `npm run build` (from `package.json`)
- Output Directory: `.next` (Next.js default)
- Install Command: `npm ci` (uses lockfile)

**Manual Override (if needed):**
- Root Directory: `frontend`
- Build Command: `cd frontend && npm run build`
- Output Directory: `frontend/.next`

---

## Performance Optimizations

### Next.js Optimizations

**Already Configured:**
- `swcMinify: true` - Fast minification
- `compress: true` - Gzip compression
- Code splitting via webpack config
- Image optimization (AVIF, WebP)

### Vercel Optimizations

**Automatic:**
- Edge Network (global CDN)
- Automatic HTTPS
- HTTP/2 and HTTP/3
- Image optimization (via Next.js Image component)
- Automatic code splitting

**Recommended:**
- Enable Vercel Analytics (optional)
- Enable Vercel Speed Insights (optional)
- Use Edge Functions for API routes (if needed)

---

## Domain Configuration

### Custom Domain Setup

1. **Add Domain in Vercel:**
   - Go to Project Settings → Domains
   - Add custom domain (e.g., `yourdomain.com`)
   - Follow DNS configuration instructions

2. **DNS Configuration:**
   - Add CNAME record: `www.yourdomain.com` → `cname.vercel-dns.com`
   - Add A record: `yourdomain.com` → Vercel IP (if using apex domain)

3. **SSL Certificate:**
   - Vercel automatically provisions SSL certificates via Let's Encrypt
   - No manual configuration needed

### Subdomain Setup

**Staging:**
- `staging.yourdomain.com` → Vercel preview deployment
- Or use separate Vercel project for staging

**Production:**
- `yourdomain.com` → Vercel production deployment
- `www.yourdomain.com` → Vercel production deployment (redirects to apex)

---

## Cost & Limits

### Vercel Pricing (as of 2024)

**Free Tier (Hobby):**
- Unlimited personal projects
- 100 GB bandwidth/month
- 100 serverless function executions/day
- Automatic HTTPS
- Preview deployments

**Pro Tier ($20/month per user):**
- Everything in Hobby
- Unlimited bandwidth
- Unlimited serverless function executions
- Team collaboration
- Password protection
- Analytics

**Enterprise:**
- Custom pricing
- Dedicated support
- SLA guarantees

### Current Usage

**Recommended:** Start with Free tier (Hobby)

**Upgrade to Pro when:**
- Exceeding 100 GB bandwidth/month
- Need team collaboration
- Need password protection for previews
- Need advanced analytics

---

## Alternative Hosting Options

### If Vercel is Not Suitable

#### Option 1: Netlify

**Pros:**
- Similar to Vercel
- Good Next.js support
- Free tier available

**Cons:**
- Slightly less optimized for Next.js than Vercel
- Different deployment model

**Migration:** Similar to Vercel, use Netlify CLI or GitHub integration.

#### Option 2: Self-Hosted (Docker)

**Pros:**
- Full control
- No vendor lock-in
- Can run on any infrastructure

**Cons:**
- Higher operational overhead
- Need to manage SSL, CDN, scaling
- More complex setup

**Setup:**
- Build Next.js app: `npm run build`
- Run with Node: `npm start`
- Or use Docker with Node image

#### Option 3: AWS Amplify / Cloudflare Pages

**Pros:**
- Enterprise-grade
- Good integration with cloud services

**Cons:**
- More complex setup
- Higher cost
- Less Next.js-optimized than Vercel

**Recommendation:** Stick with Vercel unless there's a specific reason to switch.

---

## Deployment Checklist

### Initial Setup

- [ ] Create Vercel account
- [ ] Connect GitHub repository to Vercel
- [ ] Configure build settings (root directory: `frontend`)
- [ ] Set environment variables in Vercel dashboard:
  - [ ] `NEXT_PUBLIC_API_URL` (production)
  - [ ] `NEXT_PUBLIC_SUPABASE_URL` (if using Supabase)
  - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` (if using Supabase)
  - [ ] `NEXT_PUBLIC_SITE_URL` (production)
- [ ] Test deployment on preview branch
- [ ] Configure custom domain (if applicable)
- [ ] Verify SSL certificate is active

### Per-Deployment

- [ ] CI passes (lint, type-check, test, build)
- [ ] Preview deployment created (for PRs)
- [ ] Production deployment successful (for main branch)
- [ ] Smoke tests pass (if configured)
- [ ] Verify environment variables are correct

---

## Troubleshooting

### Build Failures

**Common Issues:**
1. **Missing Environment Variables:**
   - Check Vercel dashboard → Environment Variables
   - Ensure variables are set for correct environment (Production, Preview, Development)

2. **TypeScript Errors:**
   - Run `npm run type-check` locally
   - Fix type errors before pushing

3. **Dependency Issues:**
   - Ensure `package-lock.json` is committed
   - Run `npm ci` locally to verify

4. **Build Timeout:**
   - Optimize build (reduce bundle size)
   - Check for infinite loops in build process

### Deployment Issues

**Common Issues:**
1. **404 Errors:**
   - Check `vercel.json` routes configuration
   - Ensure Next.js routing is correct

2. **Environment Variables Not Available:**
   - Variables prefixed with `NEXT_PUBLIC_*` are available at build time
   - Server-side variables are not available in client components
   - Check Vercel dashboard for variable values

3. **API Connection Errors:**
   - Verify `NEXT_PUBLIC_API_URL` is set correctly
   - Check CORS settings on backend
   - Verify backend is accessible from Vercel's edge network

---

## Summary

**Canonical Frontend Hosting:** Vercel

**Deployment Strategy:**
- **Preview:** Automatic via Vercel GitHub integration (per PR)
- **Staging:** Manual or via GitHub Actions (develop branch)
- **Production:** Automatic via Vercel GitHub integration or GitHub Actions (main branch)

**Environment Variables:**
- Set in Vercel dashboard (per environment)
- Use `NEXT_PUBLIC_*` prefix for client-side variables
- Sync with GitHub Secrets for CI/CD

**Cost:**
- Start with Free tier (Hobby)
- Upgrade to Pro ($20/month) when needed

**Next Steps:**
1. Connect GitHub repo to Vercel
2. Configure environment variables
3. Test preview deployment
4. Set up custom domain (if applicable)

This strategy provides zero-config deployments, automatic previews, and excellent developer experience while keeping costs low.
