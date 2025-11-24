#!/bin/bash
# Deploy Doctor - Diagnostic script for deployment configuration
# Checks for common misconfigurations that prevent reliable deployments

set -e

echo "🔍 Deploy Doctor - Checking deployment configuration..."
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $2 missing: $1"
        ((ERRORS++))
        return 1
    fi
}

check_file_warn() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 exists"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $2 missing: $1 (optional)"
        ((WARNINGS++))
        return 1
    fi
}

# Check frontend directory structure
echo "📁 Checking frontend directory structure..."
check_file "frontend/package.json" "package.json"
check_file "frontend/package-lock.json" "package-lock.json"
check_file "frontend/next.config.js" "next.config.js"
check_file_warn "frontend/.nvmrc" ".nvmrc file"

# Check Node version consistency
echo ""
echo "📦 Checking Node version consistency..."
if [ -f "frontend/.nvmrc" ]; then
    NVM_VERSION=$(cat frontend/.nvmrc | tr -d ' \n')
    echo -e "${GREEN}✓${NC} .nvmrc specifies Node $NVM_VERSION"
else
    echo -e "${YELLOW}⚠${NC} .nvmrc not found (optional but recommended)"
    ((WARNINGS++))
fi

if [ -f "frontend/package.json" ]; then
    if grep -q '"node"' frontend/package.json; then
        echo -e "${GREEN}✓${NC} package.json has engines.node specified"
    else
        echo -e "${YELLOW}⚠${NC} package.json missing engines.node"
        ((WARNINGS++))
    fi
fi

# Check for multiple lockfiles (conflict)
echo ""
echo "🔒 Checking for lockfile conflicts..."
LOCKFILE_COUNT=0
[ -f "frontend/package-lock.json" ] && ((LOCKFILE_COUNT++))
[ -f "frontend/yarn.lock" ] && ((LOCKFILE_COUNT++))
[ -f "frontend/pnpm-lock.yaml" ] && ((LOCKFILE_COUNT++))

if [ $LOCKFILE_COUNT -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Single lockfile detected (no conflicts)"
elif [ $LOCKFILE_COUNT -gt 1 ]; then
    echo -e "${RED}✗${NC} Multiple lockfiles detected (conflict!)"
    [ -f "frontend/package-lock.json" ] && echo "  - package-lock.json"
    [ -f "frontend/yarn.lock" ] && echo "  - yarn.lock"
    [ -f "frontend/pnpm-lock.yaml" ] && echo "  - pnpm-lock.yaml"
    ((ERRORS++))
else
    echo -e "${RED}✗${NC} No lockfile found"
    ((ERRORS++))
fi

# Check package.json scripts
echo ""
echo "📜 Checking package.json scripts..."
if [ -f "frontend/package.json" ]; then
    REQUIRED_SCRIPTS=("build" "lint" "type-check")
    for script in "${REQUIRED_SCRIPTS[@]}"; do
        if grep -q "\"$script\"" frontend/package.json; then
            echo -e "${GREEN}✓${NC} Script '$script' exists"
        else
            echo -e "${RED}✗${NC} Script '$script' missing"
            ((ERRORS++))
        fi
    done
fi

# Check GitHub Actions workflows
echo ""
echo "⚙️  Checking GitHub Actions workflows..."
check_file ".github/workflows/frontend-ci-deploy.yml" "Frontend CI & Deploy workflow"
check_file ".github/workflows/deploy.yml" "Deploy workflow"
check_file_warn ".github/workflows/ci.yml" "CI workflow"

# Check workflow configuration
if [ -f ".github/workflows/frontend-ci-deploy.yml" ]; then
    echo ""
    echo "🔍 Analyzing frontend-ci-deploy.yml..."
    
    # Check for path filters (should be removed)
    if grep -q "paths:" .github/workflows/frontend-ci-deploy.yml && ! grep -q "# Path filters removed" .github/workflows/frontend-ci-deploy.yml; then
        echo -e "${YELLOW}⚠${NC} Path filters detected (may prevent workflow from running)"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} Path filters removed or commented"
    fi
    
    # Check for VERCEL_TOKEN usage
    if grep -q "VERCEL_TOKEN" .github/workflows/frontend-ci-deploy.yml; then
        echo -e "${GREEN}✓${NC} VERCEL_TOKEN referenced in workflow"
    else
        echo -e "${RED}✗${NC} VERCEL_TOKEN not found in workflow"
        ((ERRORS++))
    fi
    
    # Check for secret validation
    if grep -q "Validate Vercel Secrets" .github/workflows/frontend-ci-deploy.yml; then
        echo -e "${GREEN}✓${NC} Secret validation step present"
    else
        echo -e "${YELLOW}⚠${NC} Secret validation step missing (recommended)"
        ((WARNINGS++))
    fi
    
    # Check concurrency settings
    if grep -q "cancel-in-progress: true" .github/workflows/frontend-ci-deploy.yml; then
        echo -e "${GREEN}✓${NC} Concurrency set to cancel-in-progress: true"
    else
        echo -e "${YELLOW}⚠${NC} Concurrency may allow duplicate deployments"
        ((WARNINGS++))
    fi
fi

# Check Vercel configuration
echo ""
echo "🚀 Checking Vercel configuration..."
check_file_warn "vercel.json" "vercel.json"
check_file_warn ".vercel/project.json" ".vercel/project.json (project linking)"

# Check environment variable documentation
echo ""
echo "📚 Checking documentation..."
check_file_warn "docs/env-and-secrets.md" "Environment variables documentation"
check_file_warn "docs/deploy-strategy.md" "Deployment strategy documentation"
check_file_warn "docs/vercel-troubleshooting.md" "Vercel troubleshooting guide"

# Check .env.example
echo ""
echo "🔐 Checking environment variable templates..."
check_file_warn ".env.example" ".env.example file"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your deployment configuration looks good."
    echo "Next steps:"
    echo "  1. Ensure GitHub Secrets are configured (VERCEL_TOKEN, etc.)"
    echo "  2. Verify Vercel project is linked"
    echo "  3. Test a deployment with a PR or push to main"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Found $WARNINGS warning(s)${NC}"
    echo ""
    echo "Configuration is functional but could be improved."
    echo "Review the warnings above and address them when possible."
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before deploying."
    echo ""
    echo "Common fixes:"
    echo "  1. Generate package-lock.json: cd frontend && npm install"
    echo "  2. Add missing scripts to package.json"
    echo "  3. Fix workflow configuration issues"
    exit 1
fi
