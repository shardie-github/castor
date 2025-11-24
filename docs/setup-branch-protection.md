# Branch Protection Setup Guide

**Last Updated:** 2024  
**Purpose:** Guide for configuring GitHub branch protection rules

---

## Quick Setup

### Using GitHub Web UI

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/branches`
2. Click "Add rule" or "Add branch protection rule"
3. Configure rules (see below)
4. Click "Create"

### Using GitHub CLI

```bash
# Install GitHub CLI if not installed
# Authenticate: gh auth login

# Create branch protection rule
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint-backend","lint-frontend","test-backend","test-frontend","build-backend","build-frontend"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

---

## Main Branch Protection

### Required Settings

**Branch name pattern:** `main`

**Protect matching branches:** ✅ Enabled

**Required Status Checks:**
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- **Required checks:**
  - `lint-backend`
  - `lint-frontend`
  - `test-backend`
  - `test-frontend`
  - `build-backend`
  - `build-frontend`

**Pull Request Reviews:**
- ✅ Require pull request reviews before merging
- **Required approving reviews:** 1
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners (if CODEOWNERS file exists)

**Restrictions:**
- ✅ Do not allow bypassing the above settings
- ✅ Include administrators

**Additional Settings:**
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ❌ Do not allow force pushes
- ❌ Do not allow deletions

---

## Develop Branch Protection (Optional)

### Recommended Settings

**Branch name pattern:** `develop`

**Protect matching branches:** ✅ Enabled

**Required Status Checks:**
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- **Required checks:**
  - `lint-backend`
  - `lint-frontend`
  - `test-backend`
  - `test-frontend`

**Pull Request Reviews:**
- ⚠️ Require pull request reviews (optional, less strict than main)
- **Required approving reviews:** 0 or 1

**Restrictions:**
- ✅ Do not allow bypassing the above settings
- ⚠️ Include administrators (optional)

**Additional Settings:**
- ✅ Require conversation resolution before merging
- ❌ Do not allow force pushes
- ❌ Do not allow deletions

---

## Required CI Checks

### From `.github/workflows/ci.yml`

These checks must pass before merging:

1. **lint-backend** - Backend linting (ruff, mypy)
2. **lint-frontend** - Frontend linting (ESLint, TypeScript)
3. **test-backend** - Backend tests with coverage
4. **test-frontend** - Frontend tests
5. **build-backend** - Backend Docker build
6. **build-frontend** - Frontend Next.js build

### Optional Checks (Not Required)

- `e2e-tests` - E2E tests (too slow for PRs, run nightly)
- `test-migrations` - Migration tests (only when migrations change)
- `aurora-doctor` - Health checks (run nightly)

---

## Configuration Script

### Automated Setup

Create a script to configure branch protection:

```bash
#!/bin/bash
# scripts/setup-branch-protection.sh

REPO="YOUR_USERNAME/YOUR_REPO"

# Main branch protection
gh api repos/$REPO/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint-backend","lint-frontend","test-backend","test-frontend","build-backend","build-frontend"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field required_conversation_resolution=true \
  --field require_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false

echo "✅ Main branch protection configured"

# Develop branch protection (optional)
gh api repos/$REPO/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint-backend","lint-frontend","test-backend","test-frontend"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":0}' \
  --field restrictions=null \
  --field required_conversation_resolution=true \
  --field require_linear_history=false \
  --field allow_force_pushes=false \
  --field allow_deletions=false

echo "✅ Develop branch protection configured"
```

**Usage:**
```bash
chmod +x scripts/setup-branch-protection.sh
./scripts/setup-branch-protection.sh
```

---

## Verification

### Check Protection Status

**Via GitHub Web UI:**
1. Go to: Settings → Branches
2. Verify rules are listed
3. Check required checks are correct

**Via GitHub CLI:**
```bash
# Check main branch protection
gh api repos/:owner/:repo/branches/main/protection

# Check develop branch protection
gh api repos/:owner/:repo/branches/develop/protection
```

### Test Protection

1. Create a test branch
2. Make a change
3. Open a pull request to `main`
4. Verify:
   - ✅ PR requires review
   - ✅ PR requires CI checks to pass
   - ✅ Cannot merge without approval
   - ✅ Cannot merge with failing checks

---

## Troubleshooting

### Checks Not Showing

**Issue:** Required checks not appearing in branch protection

**Solutions:**
1. Ensure workflows are in `.github/workflows/`
2. Ensure workflows have correct job names
3. Push a commit to trigger workflows
4. Wait for workflows to run at least once
5. Refresh branch protection settings page

### Cannot Merge PR

**Issue:** PR shows "Merging is blocked"

**Solutions:**
1. Check all required checks are passing
2. Ensure PR has required approvals
3. Resolve any conversation threads
4. Ensure branch is up to date with base branch
5. Check for merge conflicts

### Bypass Not Working

**Issue:** Cannot bypass protection (even as admin)

**Solutions:**
1. Check "Include administrators" is enabled
2. Verify you have admin access to repository
3. Check organization settings (if org repo)
4. Use GitHub CLI with admin token

---

## Best Practices

### 1. Start Strict, Relax Later

- Begin with strict protection rules
- Relax rules if needed based on team feedback
- Better to be too strict than too loose

### 2. Require Reviews

- At least 1 approval for main branch
- 0-1 approval for develop branch
- Use CODEOWNERS for critical files

### 3. Require CI Checks

- All tests must pass
- All builds must succeed
- Keep checks fast (< 15 minutes total)

### 4. Prevent Force Pushes

- Never allow force pushes to protected branches
- Use `git revert` instead of `git push --force`
- Force pushes can break CI/CD

### 5. Require Linear History

- Prevents merge commits
- Cleaner git history
- Easier to track changes

---

## CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to require reviews from specific teams:

```
# Global owners
* @team-leads

# Backend code
/src/ @backend-team
/requirements.txt @backend-team

# Frontend code
/frontend/ @frontend-team

# Database migrations
/db/migrations/ @backend-team @dba-team

# CI/CD workflows
/.github/workflows/ @devops-team
```

**Benefits:**
- Automatic reviewer assignment
- Required reviews for critical files
- Better code ownership

---

## Quick Reference

### Required Checks (Main Branch)

- `lint-backend`
- `lint-frontend`
- `test-backend`
- `test-frontend`
- `build-backend`
- `build-frontend`

### Protection Settings

**Main Branch:**
- ✅ Require PR reviews (1 approval)
- ✅ Require status checks
- ✅ Require conversation resolution
- ✅ Require linear history
- ❌ No force pushes
- ❌ No deletions

**Develop Branch:**
- ⚠️ Require PR reviews (0-1 approval)
- ✅ Require status checks
- ✅ Require conversation resolution
- ❌ No force pushes
- ❌ No deletions

---

## Next Steps

1. ✅ Configure main branch protection
2. ✅ Configure develop branch protection (optional)
3. ✅ Verify required checks are listed
4. ✅ Test protection with a PR
5. ✅ Create CODEOWNERS file (optional)
6. ✅ Document team workflow

For detailed CI/CD overview, see: `docs/ci-overview.md`
