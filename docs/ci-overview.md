# CI/CD Overview

This document provides a comprehensive overview of the CI/CD pipeline, workflows, and deployment strategies.

## Workflow Overview

### Main CI Pipeline (`ci.yml`)

**Triggers:**
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`

**Jobs:**
1. **Lint Backend** - Runs `ruff check` and `mypy`
2. **Lint Frontend** - Runs ESLint and TypeScript type checking
3. **Test Backend** - Runs pytest with coverage (minimum 50%)
4. **Test Frontend** - Runs Jest tests
5. **Build Backend** - Builds Docker image (if Dockerfile exists)
6. **Build Frontend** - Builds Next.js application

**Status:** ✅ Active

### Frontend CI & Deploy (`frontend-ci-deploy.yml`)

**Triggers:**
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Manual workflow dispatch

**Jobs:**
1. **Build and Test** - Lint, type-check, test, and build frontend
2. **Deploy Preview** - Deploys preview to Vercel (on PR)
3. **Deploy Production** - Deploys to Vercel production (on main branch)

**Status:** ✅ Active

### Database Migrations (`db-migrate.yml`)

**Triggers:**
- Manual workflow dispatch
- Scheduled (optional)

**Jobs:**
- Validates migration files
- Tests migrations against test database
- Applies migrations (if configured)

**Status:** ✅ Active

### End-to-End Tests (`e2e-tests.yml`)

**Triggers:**
- Pull requests
- Manual workflow dispatch

**Jobs:**
- Runs Playwright E2E tests
- Tests critical user flows

**Status:** ✅ Active

### Smoke Tests (`smoke-tests.yml`)

**Triggers:**
- After deployments
- Manual workflow dispatch

**Jobs:**
- Health check validation
- Critical endpoint verification

**Status:** ✅ Active

### Security Scanning (`security-scan.yml`)

**Triggers:**
- Weekly schedule
- Manual workflow dispatch

**Jobs:**
- Dependency vulnerability scanning
- Code security analysis

**Status:** ✅ Active

## Deployment Strategies

### Frontend Deployment

**Provider:** Vercel

**Strategy:**
- **Preview Deployments:** Automatic on every PR
- **Production Deployments:** Automatic on push to `main`

**Configuration:**
- `vercel.json` - Vercel configuration
- Environment variables managed in Vercel dashboard
- Build command: `cd frontend && npm run build`

**Status:** ✅ Configured

### Backend Deployment Options

#### Option 1: Fly.io (`deploy-backend-fly.yml`)

**Provider:** Fly.io

**Configuration:**
- Docker-based deployment
- Automatic scaling
- Health checks

**Status:** ⚠️ Available but not primary

#### Option 2: Kubernetes (`deploy-backend-k8s.yml`)

**Provider:** Kubernetes cluster

**Configuration:**
- `k8s/deployment.yaml` - Kubernetes manifests
- Helm charts (if applicable)

**Status:** ⚠️ Available but not primary

#### Option 3: Render (`deploy-backend-render.yml`)

**Provider:** Render

**Configuration:**
- `render.yaml` - Render configuration
- Automatic deployments

**Status:** ⚠️ Available but not primary

## Branch Protection

### Main Branch (`main`)

**Protection Rules:**
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- Require conversation resolution before merging

**Required Status Checks:**
- ✅ Lint Backend
- ✅ Lint Frontend
- ✅ Test Backend
- ✅ Test Frontend
- ✅ Build Backend
- ✅ Build Frontend

**Status:** ⚠️ Should be configured in GitHub settings

### Develop Branch (`develop`)

**Protection Rules:**
- Similar to main (less strict)
- Allows faster iteration

**Status:** ⚠️ Should be configured in GitHub settings

## Environment Variables

### CI/CD Secrets

Required GitHub Secrets:
- `VERCEL_TOKEN` - Vercel deployment token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID
- `NEXT_PUBLIC_API_URL` - Public API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key

**Status:** ⚠️ Must be configured in GitHub Secrets

### Environment-Specific Variables

**Development:**
- Uses `.env` file (gitignored)
- Default values for local development

**Staging:**
- Configured in Vercel staging environment
- Uses staging database

**Production:**
- Configured in Vercel production environment
- Uses production database
- All secrets must be set

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Migration scripts tested
- [ ] Environment variables updated
- [ ] Documentation updated

### Deployment

- [ ] Merge to `main` branch
- [ ] CI pipeline passes
- [ ] Frontend deploys to Vercel
- [ ] Backend deploys (if applicable)
- [ ] Database migrations applied (if needed)

### Post-Deployment

- [ ] Smoke tests pass
- [ ] Health checks pass
- [ ] Monitor error rates
- [ ] Verify critical features

## Troubleshooting

### CI Pipeline Failures

**Common Issues:**
1. **Lint failures** - Run `ruff check` and `npm run lint` locally
2. **Test failures** - Run tests locally to reproduce
3. **Build failures** - Check for missing dependencies or configuration

### Deployment Failures

**Frontend:**
- Check Vercel deployment logs
- Verify environment variables
- Check build errors in Vercel dashboard

**Backend:**
- Check deployment provider logs
- Verify database connectivity
- Check health endpoint

### Database Migration Issues

- Test migrations locally first
- Use `db-migrate.yml` workflow for validation
- Always backup production database before migrations

## Best Practices

1. **Always test locally** before pushing
2. **Keep PRs small** for easier review
3. **Write tests** for new features
4. **Update documentation** with changes
5. **Monitor deployments** after release
6. **Use feature flags** for gradual rollouts
7. **Keep secrets secure** - never commit secrets
8. **Review CI logs** regularly for issues

## Future Improvements

- [ ] Add automated performance testing
- [ ] Implement canary deployments
- [ ] Add deployment notifications (Slack, email)
- [ ] Automate database backup before migrations
- [ ] Add rollback automation
- [ ] Implement blue-green deployments
- [ ] Add deployment metrics dashboard

---

**Last Updated:** 2024-12-XX
