#!/usr/bin/env bash
# Production Health Check Script
# Comprehensive health check for production deployments

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="${API_URL:-https://api.castor.app}"
FRONTEND_URL="${FRONTEND_URL:-https://castor.app}"

echo -e "${BLUE}=== Production Health Check ===${NC}"
echo ""

FAILURES=0

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $HTTP_CODE)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $HTTP_CODE)"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check response time
check_response_time() {
    local name=$1
    local url=$2
    local max_time=${3:-2.0}
    
    echo -n "Checking $name response time... "
    
    TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$url" || echo "999")
    
    if (( $(echo "$TIME < $max_time" | bc -l) )); then
        echo -e "${GREEN}✓${NC} (${TIME}s)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} (${TIME}s, threshold: ${max_time}s)"
        return 1
    fi
}

# Backend checks
echo -e "${BLUE}Backend Checks:${NC}"
check_endpoint "Health endpoint" "$API_URL/health" 200
check_endpoint "Root endpoint" "$API_URL/" 200
check_endpoint "Metrics endpoint" "$API_URL/metrics" 200
check_endpoint "API docs" "$API_URL/api/docs" 200

# Check health endpoint details
echo ""
echo -e "${BLUE}Health Details:${NC}"
HEALTH_JSON=$(curl -s --max-time 10 "$API_URL/health" || echo "{}")
STATUS=$(echo "$HEALTH_JSON" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

if [ "$STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ Status: $STATUS${NC}"
else
    echo -e "${RED}✗ Status: $STATUS${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Frontend checks
echo ""
echo -e "${BLUE}Frontend Checks:${NC}"
check_endpoint "Frontend root" "$FRONTEND_URL" 200
check_response_time "Frontend load time" "$FRONTEND_URL" 3.0

# Performance checks
echo ""
echo -e "${BLUE}Performance Checks:${NC}"
check_response_time "API response time" "$API_URL/health" 1.0

# Database connectivity (via health endpoint)
echo ""
echo -e "${BLUE}Service Checks:${NC}"
DB_STATUS=$(echo "$HEALTH_JSON" | grep -o '"name":"database"[^}]*"status":"[^"]*"' | cut -d'"' -f8 || echo "unknown")

if [ "$DB_STATUS" = "healthy" ] || [ "$DB_STATUS" = "degraded" ]; then
    echo -e "${GREEN}✓ Database: $DB_STATUS${NC}"
else
    echo -e "${RED}✗ Database: $DB_STATUS${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Summary
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    exit 1
fi
