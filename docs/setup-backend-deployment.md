# Backend Deployment Setup Guide

**Last Updated:** 2024  
**Purpose:** Guide for setting up backend deployment to various platforms

---

## Deployment Platform Options

Choose one of the following platforms:

1. **Render** - Simple, Docker-based, free tier available (Recommended for simplicity)
2. **Fly.io** - Global edge deployment, Docker-based, free tier available
3. **Kubernetes** - Enterprise-grade, requires cluster setup
4. **Other** - AWS ECS, GCP Cloud Run, etc. (custom setup required)

---

## Option 1: Render (Recommended)

### Setup Steps

1. **Create Render Account**
   - Go to: https://render.com
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Name:** `podcast-analytics-api`
     - **Environment:** Docker
     - **Dockerfile Path:** `Dockerfile.prod`
     - **Docker Context:** `.` (root)
     - **Branch:** `main` (production) or `develop` (staging)
     - **Region:** Choose closest to users
     - **Instance Type:** Free tier (or paid for always-on)

3. **Set Environment Variables**
   - Go to: Service Settings → Environment
   - Add variables:
     ```
     DATABASE_URL=postgresql://...
     REDIS_URL=redis://...
     JWT_SECRET=...
     ENCRYPTION_KEY=...
     ENVIRONMENT=production
     DEBUG=false
     CORS_ALLOWED_ORIGINS=https://yourdomain.com
     ```

4. **Get API Key**
   - Go to: Account Settings → API Keys
   - Create new API key
   - Copy key

5. **Get Service ID**
   - Go to: Service Settings → General
   - Copy Service ID

6. **Configure GitHub Secrets**
   ```bash
   gh secret set RENDER_API_KEY
   gh secret set RENDER_SERVICE_ID
   gh secret set BACKEND_DEPLOYMENT_PLATFORM=render
   ```

7. **Deploy**
   - Push to `main` branch
   - Or use workflow: `.github/workflows/deploy-backend-render.yml`

### Cost

- **Free Tier:** Sleeps after 15 min inactivity, 750 hours/month
- **Paid Tier:** $7-25/month (always-on, 512 MB - 2 GB RAM)

---

## Option 2: Fly.io

### Setup Steps

1. **Create Fly.io Account**
   - Go to: https://fly.io
   - Sign up

2. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

3. **Login**
   ```bash
   fly auth login
   ```

4. **Create App**
   ```bash
   fly apps create podcast-analytics-api
   ```

5. **Create fly.toml**
   ```toml
   app = "podcast-analytics-api"
   primary_region = "iad"
   
   [build]
     dockerfile = "Dockerfile.prod"
   
   [env]
     ENVIRONMENT = "production"
     DEBUG = "false"
   
   [[services]]
     internal_port = 8000
     protocol = "tcp"
   
     [[services.ports]]
       port = 80
       handlers = ["http"]
       force_https = true
   
     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   
     [services.concurrency]
       type = "connections"
       hard_limit = 1000
       soft_limit = 500
   
     [[services.http_checks]]
       interval = "10s"
       timeout = "2s"
       grace_period = "5s"
       method = "GET"
       path = "/health"
   ```

6. **Set Secrets**
   ```bash
   fly secrets set DATABASE_URL="postgresql://..."
   fly secrets set REDIS_URL="redis://..."
   fly secrets set JWT_SECRET="..."
   fly secrets set ENCRYPTION_KEY="..."
   fly secrets set CORS_ALLOWED_ORIGINS="https://yourdomain.com"
   ```

7. **Deploy**
   ```bash
   fly deploy
   ```

8. **Get API Token**
   - Go to: https://fly.io/user/personal_access_tokens
   - Create token
   - Copy token

9. **Configure GitHub Secrets**
   ```bash
   gh secret set FLY_API_TOKEN
   gh secret set FLY_APP_NAME=podcast-analytics-api
   gh secret set BACKEND_DEPLOYMENT_PLATFORM=fly
   ```

### Cost

- **Free Tier:** Limited resources, shared CPU
- **Paid Tier:** Pay-as-you-go, ~$5-20/month for small instance

---

## Option 3: Kubernetes

### Prerequisites

- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- kubectl configured
- Container registry (Docker Hub, GHCR, GCR, ECR, etc.)

### Setup Steps

1. **Build and Push Docker Image**
   ```bash
   docker build -f Dockerfile.prod -t your-registry/podcast-analytics:latest .
   docker push your-registry/podcast-analytics:latest
   ```

2. **Create Kubernetes Secrets**
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=database-url="postgresql://..." \
     --from-literal=redis-url="redis://..." \
     --from-literal=jwt-secret="..." \
     --from-literal=encryption-key="..."
   ```

3. **Update k8s/deployment.yaml**
   - Update image: `your-registry/podcast-analytics:latest`
   - Update CORS_ALLOWED_ORIGINS
   - Review resource limits

4. **Deploy**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl rollout status deployment/podcast-analytics-api
   ```

5. **Configure GitHub Secrets**
   ```bash
   gh secret set CONTAINER_REGISTRY=your-registry
   gh secret set REGISTRY_USERNAME=your-username
   gh secret set REGISTRY_PASSWORD=your-password
   gh secret set KUBE_CONFIG  # Base64 encoded kubeconfig
   gh secret set BACKEND_DEPLOYMENT_PLATFORM=k8s
   ```

### Cost

- **GKE:** ~$70/month (minimum cluster)
- **EKS:** ~$73/month (control plane) + nodes
- **AKS:** ~$0 (control plane) + nodes
- **Self-hosted:** Varies

---

## GitHub Secrets Configuration

### Required Secrets

**For Render:**
- `RENDER_API_KEY` - Render API key
- `RENDER_SERVICE_ID` - Render service ID
- `BACKEND_DEPLOYMENT_PLATFORM=render`

**For Fly.io:**
- `FLY_API_TOKEN` - Fly.io API token
- `FLY_APP_NAME` - Fly.io app name
- `BACKEND_DEPLOYMENT_PLATFORM=fly`

**For Kubernetes:**
- `CONTAINER_REGISTRY` - Container registry URL
- `REGISTRY_USERNAME` - Registry username
- `REGISTRY_PASSWORD` - Registry password
- `KUBE_CONFIG` - Base64 encoded kubeconfig
- `BACKEND_DEPLOYMENT_PLATFORM=k8s`

**Common:**
- `PRODUCTION_API_URL` - Production API URL (for smoke tests)
- `STAGING_API_URL` - Staging API URL (for smoke tests)

---

## Deployment Workflows

### Automatic Deployment

**Production:** Push to `main` branch
- Triggers: `.github/workflows/deploy.yml`
- Runs migrations
- Builds Docker image
- Deploys backend (if platform configured)
- Deploys frontend
- Runs smoke tests

**Staging:** Push to `develop` branch
- Triggers: `.github/workflows/deploy-staging.yml`
- Similar to production but for staging

### Manual Deployment

**Render:**
```bash
# Trigger workflow
gh workflow run deploy-backend-render.yml -f environment=production
```

**Fly.io:**
```bash
# Trigger workflow
gh workflow run deploy-backend-fly.yml -f environment=production
```

**Kubernetes:**
```bash
# Trigger workflow
gh workflow run deploy-backend-k8s.yml -f environment=production
```

---

## Health Checks

### Health Endpoint

All deployments should expose `/health` endpoint:
- **URL:** `https://api.yourdomain.com/health`
- **Method:** GET
- **Response:** JSON with status and checks

### Monitoring

**Render:**
- Built-in metrics dashboard
- Logs available in dashboard

**Fly.io:**
- Built-in metrics
- Logs: `fly logs`

**Kubernetes:**
- Use Prometheus + Grafana
- Logs: `kubectl logs`

---

## Troubleshooting

### Deployment Fails

**Issue:** Deployment workflow fails

**Solutions:**
1. Check GitHub Secrets are set correctly
2. Verify platform credentials are valid
3. Check deployment logs
4. Verify Docker image builds successfully
5. Check environment variables are set

### Health Check Fails

**Issue:** `/health` endpoint returns error

**Solutions:**
1. Check database connection
2. Check Redis connection
3. Verify environment variables
4. Check application logs
5. Verify service is running

### High Latency

**Issue:** API responses are slow

**Solutions:**
1. Check database connection pooling
2. Verify Redis caching is working
3. Check instance resources (CPU/memory)
4. Consider upgrading instance size
5. Add CDN for static assets (if any)

---

## Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Render** | ✅ (sleeps) | $7-25/mo | Simple deployments |
| **Fly.io** | ✅ (limited) | $5-20/mo | Global edge |
| **Kubernetes** | ❌ | $70+/mo | Enterprise scale |

**Recommendation:** Start with Render or Fly.io, migrate to Kubernetes when needed.

---

## Next Steps

1. ✅ Choose deployment platform
2. ✅ Set up platform account
3. ✅ Configure service/environment
4. ✅ Set environment variables
5. ✅ Get API keys/tokens
6. ✅ Configure GitHub Secrets
7. ✅ Test deployment
8. ✅ Set up monitoring
9. ✅ Configure custom domain (optional)

For detailed backend strategy, see: `docs/backend-strategy.md`
