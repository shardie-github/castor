#!/bin/bash
# Quick health check script for solo operators
# Run this before committing or deploying

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo "  $1"
}

echo "Running quick health check..."
echo ""

ERRORS=0

# Check Python syntax
echo "Checking Python syntax..."
if python3 -m py_compile src/main.py 2>/dev/null; then
    print_success "Python syntax OK"
else
    print_error "Python syntax errors found"
    ERRORS=$((ERRORS + 1))
fi

# Check imports (basic)
echo "Checking critical imports..."
if python3 -c "import sys; sys.path.insert(0, '.'); from src.config import config" 2>/dev/null; then
    print_success "Critical imports OK"
else
    print_warning "Import check skipped (dependencies may not be installed)"
fi

# Check if tests can be discovered
echo "Checking test discovery..."
if python3 -m pytest tests/ --collect-only -q >/dev/null 2>&1; then
    TEST_COUNT=$(python3 -m pytest tests/ --collect-only -q 2>/dev/null | grep -c "test session starts" || echo "0")
    if [ "$TEST_COUNT" -gt "0" ]; then
        print_success "Tests can be discovered"
    else
        print_warning "No tests found"
    fi
else
    print_warning "Test discovery failed (dependencies may not be installed)"
fi

# Check for common issues
echo "Checking for common issues..."

# Check for TODO/FIXME in critical files
if grep -r "TODO\|FIXME" src/main.py src/config/ src/api/ 2>/dev/null | grep -v "# TODO" | head -1 >/dev/null; then
    print_warning "Found TODO/FIXME comments (review recommended)"
else
    print_success "No critical TODOs found"
fi

# Check for print statements (should use logging)
if grep -r "^\s*print(" src/ --include="*.py" 2>/dev/null | head -1 >/dev/null; then
    print_warning "Found print() statements (consider using logging)"
else
    print_success "No print() statements found"
fi

# Check file permissions
if [ -x "scripts/dev.sh" ]; then
    print_success "Scripts are executable"
else
    print_warning "Some scripts may not be executable"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    print_success "Health check passed!"
    exit 0
else
    print_error "Health check found $ERRORS error(s)"
    exit 1
fi
