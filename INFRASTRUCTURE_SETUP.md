# Infrastructure Setup Guide

This guide provides step-by-step instructions for building out and starting the complete infrastructure for the Podcast Analytics & Sponsorship Platform.

## Prerequisites

- **Docker** and **Docker Compose** (or Docker Compose V2)
- **Python 3.11+** with pip
- **PostgreSQL 15+** (if not using Docker)
- **Redis 7+** (if not using Docker)
- **Node.js 20+** (for frontend, optional)

## Quick Start (Docker)

The fastest way to get started is using Docker Compose:

```bash
# 1. Clone/navigate to the project directory
cd /workspace

# 2. Copy environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Run the complete setup script
bash scripts/setup.sh
```

This will:
- Start all infrastructure services (PostgreSQL, Redis, Prometheus, Grafana)
- Run database migrations
- Set up TimescaleDB hypertables
- Verify all services are healthy

## Manual Setup Steps

### Step 1: Start Infrastructure Services

#### Option A: Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Manual Installation

**PostgreSQL/TimescaleDB:**
```bash
# Install TimescaleDB
# Follow instructions at: https://docs.timescale.com/install/latest/

# Create database
createdb podcast_analytics

# Enable TimescaleDB extension
psql -d podcast_analytics -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

**Redis:**
```bash
# Install Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Start Redis
redis-server
```

**Prometheus:**
```bash
# Download and run Prometheus
# https://prometheus.io/download/

# Start Prometheus with config
./prometheus --config.file=prometheus/prometheus.yml
```

**Grafana:**
```bash
# Install Grafana
# https://grafana.com/docs/grafana/latest/setup-grafana/installation/

# Start Grafana
grafana-server
```

### Step 2: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

**Required variables:**
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_DATABASE` - Database name (default: podcast_analytics)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)

### Step 3: Install Python Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Or using pip3
pip3 install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Run database migrations
python3 scripts/init_db.py
```

This script will:
- Create all database tables
- Set up TimescaleDB hypertables
- Create indexes and constraints
- Set up retention policies
- Create continuous aggregates

### Step 5: Verify Infrastructure

```bash
# Run health checks
python3 scripts/check_health.py
```

Expected output:
```
============================================================
Infrastructure Health Check
============================================================

Checking PostgreSQL...
  ✓ PostgreSQL: Healthy

Checking Redis...
  ✓ Redis: Healthy

Checking Health Service...
  Status: healthy
  Checks:
    ✓ database: healthy (5ms)
    ✓ cache: healthy (2ms)
```

## Service Endpoints

Once infrastructure is running:

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | User: `postgres` |
| Redis | `localhost:6379` | None (or password from .env) |
| Prometheus | http://localhost:9090 | None |
| Grafana | http://localhost:3000 | `admin` / `admin` |

## Database Schema

The database includes:

### Core Tables
- `users` - User accounts and authentication
- `podcasts` - Podcast metadata
- `episodes` - Episode information
- `sponsors` - Sponsor details
- `campaigns` - Campaign management
- `transcripts` - Episode transcripts
- `reports` - Generated reports

### Time-Series Tables (Hypertables)
- `listener_events` - Listener activity events
- `attribution_events` - Conversion attribution events
- `listener_metrics` - Aggregated listener metrics

### Continuous Aggregates
- `listener_events_hourly` - Hourly aggregated metrics
- `listener_events_daily` - Daily aggregated metrics

## Monitoring Dashboards

### Accessing Grafana

1. Navigate to http://localhost:3000
2. Login with `admin` / `admin`
3. Change password on first login
4. Dashboards are automatically provisioned:
   - **System Health Dashboard** - Infrastructure metrics
   - **Business Metrics Dashboard** - Business KPIs

### Prometheus Metrics

- Metrics endpoint: http://localhost:9090
- Query interface: http://localhost:9090/graph
- Targets: http://localhost:9090/targets

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker exec podcast_analytics_postgres pg_isready -U postgres

# Or manually
pg_isready -h localhost -p 5432

# Connect to database
psql -h localhost -U postgres -d podcast_analytics
```

### Redis Connection Issues

```bash
# Check Redis is running
docker exec podcast_analytics_redis redis-cli ping

# Or manually
redis-cli ping
```

### Migration Issues

```bash
# Check migration status
psql -h localhost -U postgres -d podcast_analytics -c "
SELECT * FROM timescaledb_information.hypertables;
"

# Re-run migrations (idempotent)
python3 scripts/init_db.py
```

### Service Logs

```bash
# Docker Compose logs
docker-compose logs -f [service_name]

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Restart and reinitialize
docker-compose up -d
python3 scripts/init_db.py
```

## Next Steps

After infrastructure is running:

1. **Start the API Server:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend** (if applicable):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Run Tests:**
   ```bash
   pytest tests/integration/
   ```

4. **Access API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Production Deployment

For production deployment:

1. **Use managed services:**
   - AWS RDS (PostgreSQL/TimescaleDB)
   - AWS ElastiCache (Redis)
   - Managed Prometheus/Grafana

2. **Configure SSL/TLS:**
   - Use SSL connections for PostgreSQL
   - Enable Redis AUTH
   - Use HTTPS for all web services

3. **Set up backups:**
   - Configure automated database backups
   - Set up Redis persistence
   - Backup Grafana dashboards

4. **Security:**
   - Change all default passwords
   - Use strong encryption keys
   - Configure firewall rules
   - Enable rate limiting

5. **Monitoring:**
   - Set up alerting rules
   - Configure PagerDuty/Slack notifications
   - Monitor disk space and performance

---

*Last Updated: [Current Date]*
