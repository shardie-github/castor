#!/bin/bash
# Smoke Tests for Critical Paths
# Run this script to verify critical functionality before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=10

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    
    print_info "Testing: $description"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL$endpoint" --max-time $TIMEOUT || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" --max-time $TIMEOUT || echo -e "\n000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        print_success "$description (HTTP $http_code)"
        return 0
    else
        print_error "$description - Expected HTTP $expected_status, got $http_code"
        echo "Response: $body"
        return 1
    fi
}

# Main execution
echo "=========================================="
echo "  Smoke Tests - Critical Paths"
echo "=========================================="
echo ""
echo "API URL: $API_URL"
echo ""

FAILED_TESTS=0
TOTAL_TESTS=0

# Health Check
TOTAL_TESTS=$((TOTAL_TESTS + 1))
test_endpoint "GET" "/health" "200" "Health check endpoint" || FAILED_TESTS=$((FAILED_TESTS + 1))

# Root endpoint
TOTAL_TESTS=$((TOTAL_TESTS + 1))
test_endpoint "GET" "/" "200" "Root endpoint" || FAILED_TESTS=$((FAILED_TESTS + 1))

# Metrics endpoint
TOTAL_TESTS=$((TOTAL_TESTS + 1))
test_endpoint "GET" "/metrics" "200" "Metrics endpoint" || FAILED_TESTS=$((FAILED_TESTS + 1))

# API Documentation
TOTAL_TESTS=$((TOTAL_TESTS + 1))
test_endpoint "GET" "/api/docs" "200" "API documentation" || FAILED_TESTS=$((FAILED_TESTS + 1))

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $((TOTAL_TESTS - FAILED_TESTS))"
echo "Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "All smoke tests passed!"
    exit 0
else
    print_error "$FAILED_TESTS test(s) failed"
    exit 1
fi
