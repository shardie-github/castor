#!/bin/bash
# Start Infrastructure Script
# Starts all infrastructure services using Docker Compose

set -e

echo "=========================================="
echo "Starting Podcast Analytics Infrastructure"
echo "=========================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env file with your configuration before continuing."
        echo "Press Enter to continue or Ctrl+C to cancel..."
        read
    else
        echo "Error: .env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Start infrastructure services
echo ""
echo "Starting Docker Compose services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check PostgreSQL
echo "Checking PostgreSQL..."
for i in {1..30}; do
    if docker exec podcast_analytics_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

# Check Redis
echo "Checking Redis..."
for i in {1..30}; do
    if docker exec podcast_analytics_redis redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Redis failed to start"
        exit 1
    fi
    sleep 1
done

# Check Prometheus
echo "Checking Prometheus..."
for i in {1..30}; do
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo "✓ Prometheus is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Prometheus failed to start"
        exit 1
    fi
    sleep 1
done

# Check Grafana
echo "Checking Grafana..."
for i in {1..30}; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✓ Grafana is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Grafana failed to start"
        exit 1
    fi
    sleep 1
done

echo ""
echo "=========================================="
echo "Infrastructure is running!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - PostgreSQL:    localhost:5432"
echo "  - Redis:         localhost:6379"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000 (admin/admin)"
echo ""
echo "Next steps:"
echo "  1. Run database migrations: python scripts/init_db.py"
echo "  2. Start the API: uvicorn src.main:app --reload"
echo ""
