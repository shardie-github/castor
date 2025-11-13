# Infrastructure Overview

This document provides an overview of the infrastructure setup for the Podcast Analytics & Sponsorship Platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   FastAPI    │  │   Frontend   │  │  Background   │   │
│  │     API      │  │   (Next.js)  │  │    Agents     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘   │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼────────────┐
│         │                  │                  │             │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐    │
│  │ PostgreSQL  │   │    Redis    │   │ Prometheus  │    │
│  │ TimescaleDB │   │   (Cache)   │   │ (Metrics)   │    │
│  └─────────────┘   └─────────────┘   └─────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Grafana (Dashboards)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. PostgreSQL with TimescaleDB

**Purpose:** Primary database for relational data and time-series data

**Features:**
- Relational tables: users, podcasts, episodes, campaigns, sponsors, reports
- Time-series hypertables: listener_events, attribution_events, listener_metrics
- Continuous aggregates for hourly/daily metrics
- Data retention policies

**Connection:**
- Host: `localhost:5432` (or from `.env`)
- Database: `podcast_analytics`
- User: `postgres` (or from `.env`)

**Key Tables:**
- `users` - User accounts
- `podcasts` - Podcast metadata
- `episodes` - Episode information
- `campaigns` - Campaign management
- `listener_events` - Time-series listener activity
- `attribution_events` - Conversion attribution events

### 2. Redis

**Purpose:** Caching and session management

**Features:**
- Session storage
- Rate limiting tokens
- API key caching
- Temporary data storage

**Connection:**
- Host: `localhost:6379` (or from `.env`)
- Password: Optional (from `.env`)

### 3. Prometheus

**Purpose:** Metrics collection and storage

**Features:**
- Scrapes metrics from application endpoints
- Stores time-series metrics
- Query language (PromQL) for metrics

**Access:**
- URL: http://localhost:9090
- Metrics endpoint: `/metrics`
- Query interface: `/graph`

### 4. Grafana

**Purpose:** Metrics visualization and dashboards

**Features:**
- Pre-configured dashboards
- System health monitoring
- Business metrics visualization
- Alerting (when configured)

**Access:**
- URL: http://localhost:3000
- Default credentials: `admin` / `admin`

**Dashboards:**
- System Health Dashboard
- Business Metrics Dashboard

## Data Flow

### Ingestion Flow
```
RSS Feeds / Platform APIs
    ↓
Ingestion Service (rss_ingest.py, host_apis.py)
    ↓
PostgreSQL (podcasts, episodes)
    ↓
TimescaleDB (listener_events)
```

### Attribution Flow
```
Conversion Events (Pixels, Promo Codes, UTM)
    ↓
Attribution Engine
    ↓
TimescaleDB (attribution_events)
    ↓
ROI Calculations
```

### Reporting Flow
```
Campaigns + Listener Events + Attribution Events
    ↓
Analytics Aggregation
    ↓
Report Generation
    ↓
PostgreSQL (reports table)
```

## Setup Commands

### Quick Start
```bash
# Complete setup
bash scripts/setup.sh

# Or step by step:
bash scripts/start_infrastructure.sh  # Start Docker services
python3 scripts/init_db.py              # Initialize database
python3 scripts/check_health.py        # Verify health
python3 scripts/verify_setup.py        # Verify setup
```

### Manual Start
```bash
# Start services
docker-compose up -d

# Initialize database
python3 scripts/init_db.py

# Check status
docker-compose ps
python3 scripts/check_health.py
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Monitoring

### Health Checks

**Application Health:**
```bash
curl http://localhost:8000/health
```

**Database Health:**
```bash
python3 scripts/check_health.py
```

**Service Health:**
```bash
docker-compose ps
```

### Metrics

**Prometheus Metrics:**
- Application: http://localhost:8000/metrics
- Prometheus: http://localhost:9090

**Grafana Dashboards:**
- System Health: http://localhost:3000/d/system-health
- Business Metrics: http://localhost:3000/d/business-metrics

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `docker-compose ps`
   - Verify credentials in `.env`
   - Check network connectivity

2. **Migration Errors**
   - Ensure TimescaleDB extension is enabled
   - Check database permissions
   - Review migration logs

3. **Redis Connection Failed**
   - Check Redis is running: `docker exec podcast_analytics_redis redis-cli ping`
   - Verify host/port in `.env`

4. **Grafana Not Loading Dashboards**
   - Check Prometheus data source is configured
   - Verify dashboard files exist in `grafana/dashboards/`
   - Check Grafana logs: `docker-compose logs grafana`

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

## Production Considerations

### Security
- Use strong passwords for all services
- Enable SSL/TLS for database connections
- Configure Redis AUTH
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Enable firewall rules

### Scalability
- Use connection pooling
- Configure read replicas for PostgreSQL
- Use Redis Cluster for high availability
- Scale Prometheus horizontally if needed
- Use managed Grafana for production

### Backup & Recovery
- Automated database backups (daily)
- Redis persistence (AOF + RDB)
- Grafana dashboard backups
- Disaster recovery plan

### Monitoring
- Set up alerting rules in Prometheus
- Configure PagerDuty/Slack notifications
- Monitor disk space and performance
- Track error rates and latency

---

*For detailed setup instructions, see [INFRASTRUCTURE_SETUP.md](./INFRASTRUCTURE_SETUP.md)*
