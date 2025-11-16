#!/bin/bash
# Validation script to check if all components are properly set up

set -e

echo "🔍 Validating Phase 2, 3, 4 Implementation..."

ERRORS=0

# Check API files exist
echo "📝 Checking API files..."
APIS=("podcasts" "episodes" "sponsors" "reports" "analytics" "users" "email")
for api in "${APIS[@]}"; do
    if [ -f "src/api/${api}.py" ]; then
        echo "  ✅ ${api}.py exists"
    else
        echo "  ❌ ${api}.py missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check frontend components
echo "🎨 Checking frontend components..."
COMPONENTS=("DataTable" "DateRangePicker" "FileUpload" "ExportButton")
for component in "${COMPONENTS[@]}"; do
    if [ -f "frontend/components/ui/${component}.tsx" ]; then
        echo "  ✅ ${component}.tsx exists"
    else
        echo "  ❌ ${component}.tsx missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check infrastructure files
echo "🏗️  Checking infrastructure files..."
if [ -f "Dockerfile.prod" ]; then
    echo "  ✅ Dockerfile.prod exists"
else
    echo "  ❌ Dockerfile.prod missing"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".github/workflows/ci-cd-complete.yml" ]; then
    echo "  ✅ CI/CD pipeline exists"
else
    echo "  ❌ CI/CD pipeline missing"
    ERRORS=$((ERRORS + 1))
fi

# Check email service
echo "📧 Checking email service..."
if [ -f "src/email/email_service.py" ]; then
    echo "  ✅ Email service exists"
else
    echo "  ❌ Email service missing"
    ERRORS=$((ERRORS + 1))
fi

# Check migrations
echo "🗄️  Checking migrations..."
if [ -f "migrations/018_email_preferences.sql" ]; then
    echo "  ✅ Email preferences migration exists"
else
    echo "  ❌ Email preferences migration missing"
    ERRORS=$((ERRORS + 1))
fi

# Check smoke tests
echo "🧪 Checking smoke tests..."
if [ -f "tests/smoke/test_critical_paths.py" ]; then
    echo "  ✅ Smoke tests exist"
else
    echo "  ❌ Smoke tests missing"
    ERRORS=$((ERRORS + 1))
fi

# Check linting script
echo "🔍 Checking linting script..."
if [ -f "scripts/lint_all.sh" ]; then
    echo "  ✅ Linting script exists"
else
    echo "  ❌ Linting script missing"
    ERRORS=$((ERRORS + 1))
fi

# Check main.py includes new routers
echo "🔗 Checking main.py integration..."
if grep -q "podcasts, episodes, sponsors" src/main.py; then
    echo "  ✅ New APIs integrated in main.py"
else
    echo "  ❌ New APIs not integrated in main.py"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed! Implementation complete."
    exit 0
else
    echo "❌ Found $ERRORS errors. Please review and fix."
    exit 1
fi
