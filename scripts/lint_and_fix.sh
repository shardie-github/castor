#!/bin/bash
# Comprehensive Linting and Code Fix Script

set -e

echo "=========================================="
echo "Code Linting and Fixing"
echo "=========================================="

# Python linting
echo ""
echo "Python Linting..."
echo "----------------------------------------"

# Run flake8
echo "Running flake8..."
cd /workspace
python3 -m flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
python3 -m flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true

# Run black (formatting)
echo ""
echo "Running black (check)..."
python3 -m black --check src/ || true

# Run mypy (type checking)
echo ""
echo "Running mypy..."
python3 -m mypy src/ --ignore-missing-imports || true

# Frontend linting
echo ""
echo "Frontend Linting..."
echo "----------------------------------------"
cd /workspace/frontend

# Run ESLint
echo "Running ESLint..."
npm run lint || true

# Run TypeScript check
echo ""
echo "Running TypeScript check..."
npm run type-check || true

echo ""
echo "=========================================="
echo "Linting Complete"
echo "=========================================="
