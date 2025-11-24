#!/usr/bin/env bash
# Setup Monitoring Stack
# Configures Prometheus and Grafana for production monitoring

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Setting Up Monitoring Stack ===${NC}"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker not found. Skipping local monitoring setup.${NC}"
    echo "For production, configure Prometheus and Grafana separately."
    exit 0
fi

# Start monitoring services
if [ -f "docker-compose.yml" ]; then
    echo -e "${BLUE}Starting Prometheus and Grafana...${NC}"
    docker-compose up -d prometheus grafana
    
    echo ""
    echo -e "${GREEN}✅ Monitoring stack started${NC}"
    echo ""
    echo "Access monitoring services:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo "    Default credentials: admin/admin"
    echo ""
    echo "Next steps:"
    echo "  1. Import Grafana dashboards from monitoring/grafana-dashboards/"
    echo "  2. Configure Prometheus alerts in monitoring/prometheus-alerts.yml"
    echo "  3. Set up alerting channels (email, Slack, etc.)"
else
    echo -e "${YELLOW}⚠ docker-compose.yml not found${NC}"
    echo "Monitoring configuration files are available in:"
    echo "  - monitoring/prometheus-alerts.yml"
    echo "  - monitoring/grafana-dashboards/"
fi
