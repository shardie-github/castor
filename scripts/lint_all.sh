#!/bin/bash
# Comprehensive linting script for the entire codebase

set -e

echo "🔍 Running comprehensive linting..."

# Python linting
echo "📝 Linting Python code..."
flake8 src/ --max-line-length=120 --exclude=__pycache__ --count --statistics || true
black --check src/ || true
mypy src/ --ignore-missing-imports --no-strict-optional || true

# Frontend linting
if [ -d "frontend" ]; then
    echo "🎨 Linting frontend code..."
    cd frontend
    npm run lint || true
    npm run type-check || true
    cd ..
fi

# Check for common issues
echo "🔎 Checking for common issues..."
# Check for TODO/FIXME comments
echo "Checking for TODO/FIXME comments..."
grep -r "TODO\|FIXME" src/ frontend/ --exclude-dir=node_modules --exclude-dir=__pycache__ || echo "No TODO/FIXME found"

# Check for console.log in production code
if [ -d "frontend" ]; then
    echo "Checking for console.log in frontend..."
    grep -r "console\.log" frontend/src --exclude-dir=node_modules || echo "No console.log found"
fi

echo "✅ Linting complete!"
