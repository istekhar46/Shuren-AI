# Shuren Backend Deployment Guide

**Version:** 1.0.0  
**Last Updated:** February 17, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Nginx Configuration for SSE](#nginx-configuration-for-sse)
5. [Docker Deployment](#docker-deployment)
6. [Database Migrations](#database-migrations)
7. [Health Checks](#health-checks)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying the Shuren backend application with proper configuration for Server-Sent Events (SSE) streaming endpoints.

**Key Components:**
- FastAPI application (Python 3.11+)
- PostgreSQL 15+ database
- Redis 7.0+ cache
- Nginx reverse proxy
- Celery workers for background tasks

---

## Prerequisites

### System Requirements
- Linux server (Ubuntu 22.04 LTS recommended)
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ disk space
- Python 3.11+
- Poetry package manager
- Docker and Docker Compose (optional)

### External Services
- PostgreSQL database (managed service recommended)
- Redis instance (managed service or self-hosted)
- LiveKit server (for voice/text agent features)
- AI API keys (Anthropic Claude, OpenAI, Deepgram, Cartesia)

---

## Environment Configuration

Create a `.env` file with the following variables:

```bash
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=<generate-secure-random-key>
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/shuren

# Redis
REDIS_URL=redis://host:6379/0

# JWT Authentication
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LiveKit
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=<your-api-key>
LIVEKIT_API_SECRET=<your-api-secret>

# AI Services
ANTHROPIC_API_KEY=<your-anthropic-key>
OPENAI_API_KEY=<your-openai-key>
DEEPGRAM_API_KEY=<your-deepgram-key>
CARTESIA_API_KEY=<your-cartesia-key>

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

**Security Notes:**
- Generate secure random keys using: `openssl rand -hex 32`
- Never commit `.env` files to version control
- Use environment-specific configurations for staging/production
- Rotate secrets regularly

---

## Nginx Configuration for SSE

### Why Special Configuration is Needed

Server-Sent Events (SSE) require special nginx configuration because:
1. **Buffering**: Nginx buffers responses by default, which delays SSE events
2. **Timeouts**: Long-lived connections need extended timeout values
3. **Headers**: SSE requires specific HTTP headers to function correctly

### Nginx Configuration File

Create or update `/etc/nginx/sites-available/shuren`:

```nginx
# Upstream FastAPI application
upstream shuren_backend {
    server 127.0.0.1:8000;
    # For multiple workers, add more servers:
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # General Settings
    client_max_body_size 10M;
    
    # Logging
    access_log /var/log/nginx/shuren_access.log;
    error_log /var/log/nginx/shuren_error.log;
    
    # SSE Streaming Endpoints - CRITICAL CONFIGURATION
    location ~ ^/api/v1/chat/(stream|onboarding-stream) {
        proxy_pass http://shuren_backend;
        
        # Disable buffering for SSE
        proxy_buffering off;
        
        # Disable nginx buffering (critical for SSE)
        proxy_cache off;
        
        # Set headers for SSE
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE-specific headers
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        
        # Disable proxy buffering (alternative method)
        proxy_request_buffering off;
        
        # Extended timeouts for long-lived connections
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Chunked transfer encoding
        chunked_transfer_encoding on;
        
        # Disable gzip for SSE (prevents buffering)
        gzip off;
    }
    
    # Regular API Endpoints
    location /api/ {
        proxy_pass http://shuren_backend;
        
        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Standard timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://shuren_backend;
        access_log off;
    }
    
    # API Documentation
    location /api/docs {
        proxy_pass http://shuren_backend;
    }
    
    location /api/redoc {
        proxy_pass http://shuren_backend;
    }
}
```

### Key Configuration Directives Explained

#### For SSE Endpoints (`/api/v1/chat/stream` and `/api/v1/chat/onboarding-stream`):

1. **`proxy_buffering off;`**
   - Disables nginx response buffering
   - Allows SSE events to pass through immediately
   - **Critical for real-time streaming**

2. **`proxy_cache off;`**
   - Disables response caching
   - Ensures each request gets fresh streaming data

3. **`proxy_set_header Connection '';`**
   - Clears the Connection header
   - Prevents connection closure between nginx and upstream

4. **`proxy_http_version 1.1;`**
   - Uses HTTP/1.1 for upstream connections
   - Required for persistent connections

5. **`proxy_request_buffering off;`**
   - Disables request body buffering
   - Improves streaming performance

6. **Extended Timeouts**
   - `proxy_read_timeout 300s;` - Allows 5-minute streaming sessions
   - `proxy_send_timeout 300s;` - Prevents premature connection closure
   - Adjust based on expected response times

7. **`chunked_transfer_encoding on;`**
   - Enables chunked transfer encoding
   - Required for streaming responses

8. **`gzip off;`**
   - Disables gzip compression for SSE endpoints
   - Compression buffers data, breaking real-time streaming

### Testing Nginx Configuration

```bash
# Test configuration syntax
sudo nginx -t

# Reload nginx (zero-downtime)
sudo nginx -s reload

# Restart nginx (if reload fails)
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx

# View nginx error logs
sudo tail -f /var/log/nginx/shuren_error.log
```

### Verifying SSE Configuration

Test SSE endpoints using curl:

```bash
# Test streaming endpoint
curl -N -H "Accept: text/event-stream" \
  "https://api.yourdomain.com/api/v1/chat/stream?message=hello&token=YOUR_JWT_TOKEN"

# Expected output (streaming):
# data: {"chunk": "Hello"}
# 
# data: {"chunk": " there!"}
# 
# data: {"done": true, "agent_type": "general"}
```

**Success Indicators:**
- Events appear immediately as they're generated
- No buffering delay (< 1 second between chunks)
- Connection stays open until completion event
- No 502/504 gateway timeout errors

**Failure Indicators:**
- All events arrive at once (buffering enabled)
- Connection times out before completion
- 502 Bad Gateway errors
- Events delayed by several seconds

---

## Docker Deployment

### Docker Compose Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    restart: unless-stopped
    
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.core.celery_app worker --loglevel=info
    restart: unless-stopped
    
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.core.celery_app beat --loglevel=info
    restart: unless-stopped
    
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: shuren
      POSTGRES_USER: shuren
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Deployment Commands

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update application
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Database Migrations

### Running Migrations

```bash
# Using Poetry
poetry run alembic upgrade head

# Using Docker
docker-compose exec api poetry run alembic upgrade head

# Check current migration version
poetry run alembic current

# View migration history
poetry run alembic history
```

### Rollback Procedure

```bash
# Rollback one migration
poetry run alembic downgrade -1

# Rollback to specific version
poetry run alembic downgrade <revision_id>

# Rollback all migrations
poetry run alembic downgrade base
```

---

## Health Checks

### Application Health Endpoint

The application provides a health check endpoint:

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### Monitoring Health

```bash
# Check application health
curl https://api.yourdomain.com/health

# Check from load balancer
curl -f http://localhost:8000/health || exit 1
```

---

## Monitoring

### Key Metrics to Monitor

1. **Application Metrics**
   - Request rate (requests/second)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Active streaming connections

2. **SSE-Specific Metrics**
   - Streaming session duration
   - Chunks per session
   - Stream error rate
   - Database save success rate

3. **Infrastructure Metrics**
   - CPU usage
   - Memory usage
   - Database connections
   - Redis memory usage

### Logging

Application logs are written to stdout/stderr. Configure log aggregation:

```bash
# View application logs
docker-compose logs -f api

# View nginx access logs
tail -f /var/log/nginx/shuren_access.log

# View nginx error logs
tail -f /var/log/nginx/shuren_error.log
```

---

## Troubleshooting

### SSE Streaming Issues

**Problem:** Events arrive all at once instead of streaming

**Solution:**
- Verify `proxy_buffering off;` in nginx config
- Check `X-Accel-Buffering: no` header is set by FastAPI
- Disable gzip compression for SSE endpoints
- Test directly against FastAPI (bypass nginx) to isolate issue

**Problem:** Connection times out during streaming

**Solution:**
- Increase `proxy_read_timeout` in nginx config
- Check FastAPI timeout settings
- Verify no intermediate proxies are buffering

**Problem:** 502 Bad Gateway errors

**Solution:**
- Check FastAPI application is running: `curl http://localhost:8000/health`
- Verify upstream configuration in nginx
- Check application logs for errors
- Ensure sufficient worker processes

### Database Connection Issues

**Problem:** "Too many connections" error

**Solution:**
- Increase PostgreSQL `max_connections`
- Reduce application connection pool size
- Check for connection leaks in application code

### Performance Issues

**Problem:** Slow response times

**Solution:**
- Check database query performance
- Verify Redis cache is working
- Monitor CPU/memory usage
- Scale horizontally (add more workers)

---

## Security Checklist

- [ ] SSL/TLS certificates configured and valid
- [ ] Environment variables secured (not in version control)
- [ ] Database credentials rotated regularly
- [ ] JWT secrets are strong and unique
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled
- [ ] Firewall rules configured
- [ ] Regular security updates applied
- [ ] Logs monitored for suspicious activity

---

## Support

For deployment issues or questions:
- Check application logs first
- Review nginx error logs
- Consult the API documentation
- Contact the backend team

---

## Changelog

### Version 1.0.0 (2026-02-17)
- Initial deployment guide
- Added nginx configuration for SSE streaming
- Documented Docker deployment
- Added health checks and monitoring guidelines

