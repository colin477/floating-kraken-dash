# EZ Eatin' Production Environment Configuration

## Overview

This document provides comprehensive production environment configuration for deploying the EZ Eatin' application to Render with GitHub integration. The configuration supports a development-to-production workflow with proper security, monitoring, and scalability considerations.

## Environment Management Strategy

### Environment Hierarchy
- **Development**: Local development environment with hot reload and demo mode
- **Production**: Optimized production deployment on Render with full security and monitoring

### Configuration Sources
- **Development**: Local `.env` files and environment variables
- **Production**: Render environment variables (secure secrets management)
- **CI/CD**: GitHub Actions with secrets for automated deployments

## Backend Production Configuration

### Production Environment Variables Template

Create these environment variables in your Render backend service:

```bash
# Application Environment
APP_ENV=production
PORT=10000

# MongoDB Configuration (Production)
MONGODB_URI=mongodb+srv://prod_user:SECURE_PASSWORD@cluster0.mongodb.net/ez_eatin_prod?retryWrites=true&w=majority&appName=EZEatinProd
DATABASE_NAME=ez_eatin_prod

# JWT Configuration (Production)
JWT_SECRET=GENERATE_SECURE_256_BIT_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN=86400

# CORS Configuration (Production)
CORS_ORIGINS=https://ezeatin-frontend.onrender.com,https://app.ezeatin.com,https://www.ezeatin.com

# API Configuration
API_BASE_PATH=/api/v1

# Logging Configuration
LOG_LEVEL=INFO

# Security Headers
SECURE_HEADERS=true
HTTPS_ONLY=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Monitoring
HEALTH_CHECK_ENABLED=true
METRICS_ENABLED=true

# Error Reporting
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ERROR_REPORTING_ENABLED=true
```

### Backend Production Dockerfile

```dockerfile
# Production Dockerfile for EZ Eatin' Backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/healthz || exit 1

# Start application
CMD ["python", "main.py"]
```

### Production-Ready main.py Enhancements

```python
# Enhanced main.py for production
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        await connect_to_mongo()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        if os.getenv("APP_ENV") == "production":
            raise e
    yield
    # Shutdown
    await close_mongo_connection()
    logger.info("Application shutdown completed")

# Create FastAPI application with production settings
app = FastAPI(
    title="EZ Eatin' API",
    description="AI-driven meal planning and recipe management backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("APP_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("APP_ENV") != "production" else None,
)

# Production middleware stack
if os.getenv("APP_ENV") == "production":
    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["ezeatin-api.onrender.com", "api.ezeatin.com"]
    )

# GZip compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enhanced CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
if os.getenv("APP_ENV") == "development":
    cors_origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Enhanced health check endpoint
@app.get("/healthz")
async def health_check():
    """Production health check with detailed status"""
    try:
        from app.database import db
        health_status = {
            "status": "healthy",
            "environment": os.getenv("APP_ENV", "unknown"),
            "version": "1.0.0",
            "database_connected": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if db.database is not None:
            await db.database.command("ping")
            health_status["database_connected"] = True
            health_status["message"] = "All systems operational"
        else:
            health_status["status"] = "degraded"
            health_status["message"] = "Database connection unavailable"
            
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "database_connected": False,
            "timestamp": datetime.utcnow().isoformat()
        }

# Production server configuration
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    host = "0.0.0.0"
    
    if os.getenv("APP_ENV") == "production":
        # Production server settings
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=4,
            access_log=True,
            log_level="info"
        )
    else:
        # Development server settings
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug"
        )
```

### Render Backend Service Configuration

```yaml
# render.yaml for backend service
services:
  - type: web
    name: ezeatin-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: APP_ENV
        value: production
      - key: PORT
        value: 10000
      - key: PYTHON_VERSION
        value: 3.11.0
    healthCheckPath: /healthz
    autoDeploy: true
    branch: main
    rootDir: backend
```

## Frontend Production Configuration

### Production Environment Variables

Set these in your Render frontend service:

```bash
# API Configuration
VITE_API_BASE_URL=https://ezeatin-backend.onrender.com/api/v1
VITE_APP_ENV=production

# Feature Flags
VITE_DEMO_MODE_ENABLED=false
VITE_DEBUG_MODE=false

# Analytics and Monitoring
VITE_ANALYTICS_ENABLED=true
VITE_SENTRY_DSN=https://your-frontend-sentry-dsn@sentry.io/project-id

# Performance
VITE_ENABLE_PWA=true
VITE_CACHE_STRATEGY=aggressive
```

### Production Vite Configuration

```typescript
// vite.config.production.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false, // Disable in production for security
    minify: "terser",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          ui: ["@radix-ui/react-dialog", "@radix-ui/react-dropdown-menu"],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 3000,
    host: true,
  },
  preview: {
    port: 3000,
    host: true,
  },
});
```

### Production API Service Configuration

```typescript
// src/services/api.production.ts
const getApiBaseUrl = (): string => {
  // Use environment variable in production, fallback for development
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

// Enhanced error handling for production
const apiRequest = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const token = getAuthToken();
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        detail: `HTTP ${response.status}: ${response.statusText}` 
      }));
      
      // Log errors in production for monitoring
      if (import.meta.env.VITE_APP_ENV === 'production') {
        console.error('API Error:', {
          endpoint,
          status: response.status,
          error: errorData
        });
      }
      
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    
    return response;
  } catch (error) {
    // Enhanced error handling for production
    if (import.meta.env.VITE_APP_ENV === 'production') {
      console.error('Network Error:', { endpoint, error });
    }
    throw error;
  }
};
```

### Render Frontend Service Configuration

```yaml
# Frontend service in render.yaml
  - type: web
    name: ezeatin-frontend
    env: static
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_BASE_URL
        value: https://ezeatin-backend.onrender.com/api/v1
      - key: VITE_APP_ENV
        value: production
    headers:
      - path: /*
        name: X-Frame-Options
        value: DENY
      - path: /*
        name: X-Content-Type-Options
        value: nosniff
      - path: /*
        name: Referrer-Policy
        value: strict-origin-when-cross-origin
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    autoDeploy: true
    branch: main
    rootDir: frontend
```

## Database Production Setup

### MongoDB Atlas Production Configuration

1. **Create Production Cluster**
   - Use MongoDB Atlas M10+ tier for production
   - Enable backup with point-in-time recovery
   - Configure multiple availability zones
   - Set up monitoring and alerting

2. **Security Configuration**
   ```javascript
   // Database security settings
   {
     "networkAccessList": [
       {
         "ipAddress": "0.0.0.0/0", // Render's IP ranges
         "comment": "Render deployment access"
       }
     ],
     "databaseUsers": [
       {
         "username": "prod_user",
         "password": "SECURE_GENERATED_PASSWORD",
         "roles": [
           {
             "role": "readWrite",
             "db": "ez_eatin_prod"
           }
         ]
       }
     ]
   }
   ```

3. **Connection String Template**
   ```
   mongodb+srv://prod_user:SECURE_PASSWORD@cluster0.mongodb.net/ez_eatin_prod?retryWrites=true&w=majority&appName=EZEatinProd
   ```

4. **Backup Strategy**
   - Automated daily backups
   - 7-day backup retention
   - Point-in-time recovery enabled
   - Cross-region backup replication

## Security Configuration

### Backend Security Headers

```python
# Security middleware configuration
from fastapi.middleware.security import SecurityHeadersMiddleware

if os.getenv("SECURE_HEADERS") == "true":
    app.add_middleware(
        SecurityHeadersMiddleware,
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    )
```

### JWT Security Configuration

```python
# Enhanced JWT configuration for production
JWT_SETTINGS = {
    "secret_key": os.getenv("JWT_SECRET"),
    "algorithm": "HS256",
    "expires_in": int(os.getenv("JWT_EXPIRES_IN", 86400)),
    "issuer": "ezeatin-api",
    "audience": "ezeatin-app",
    "verify_signature": True,
    "verify_exp": True,
    "verify_iat": True,
    "require_exp": True,
    "require_iat": True
}
```

### Rate Limiting Configuration

```python
# Production rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limiting to sensitive endpoints
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login implementation
    pass
```

## Monitoring and Logging

### Application Monitoring

```python
# Enhanced logging configuration
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging for production
if os.getenv("APP_ENV") == "production":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                "app.log", maxBytes=10485760, backupCount=5
            )
        ]
    )
```

### Health Check Monitoring

```python
# Comprehensive health checks
@app.get("/healthz")
async def health_check():
    checks = {
        "database": await check_database_health(),
        "external_apis": await check_external_apis(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }
    
    overall_status = "healthy" if all(checks.values()) else "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Performance Monitoring

```python
# Request timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response
```

## Deployment Strategy

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest
      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm run test

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        uses: render-deploy/github-action@v1
        with:
          service-id: ${{ secrets.RENDER_BACKEND_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        uses: render-deploy/github-action@v1
        with:
          service-id: ${{ secrets.RENDER_FRONTEND_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
```

### Deployment Checklist

- [ ] Set up MongoDB Atlas production cluster
- [ ] Configure Render backend service with environment variables
- [ ] Configure Render frontend service with build settings
- [ ] Set up GitHub repository with deployment secrets
- [ ] Configure custom domain (if applicable)
- [ ] Set up SSL certificates
- [ ] Configure monitoring and alerting
- [ ] Test production deployment
- [ ] Set up backup and recovery procedures

## Environment Variables Security

### Required Secrets for Render

**Backend Service:**
- `MONGODB_URI` - Production MongoDB connection string
- `JWT_SECRET` - Secure 256-bit secret key
- `SENTRY_DSN` - Error reporting endpoint (optional)

**Frontend Service:**
- `VITE_API_BASE_URL` - Backend API endpoint
- `VITE_SENTRY_DSN` - Frontend error reporting (optional)

**GitHub Secrets:**
- `RENDER_API_KEY` - Render API key for deployments
- `RENDER_BACKEND_SERVICE_ID` - Backend service ID
- `RENDER_FRONTEND_SERVICE_ID` - Frontend service ID

### Security Best Practices

1. **Never commit secrets to version control**
2. **Use strong, randomly generated passwords**
3. **Rotate secrets regularly**
4. **Use environment-specific secrets**
5. **Monitor for secret exposure**
6. **Use least-privilege access principles**

## Performance Optimization

### Backend Optimizations

```python
# Database connection pooling
MONGODB_SETTINGS = {
    "maxPoolSize": 50,
    "minPoolSize": 5,
    "maxIdleTimeMS": 30000,
    "waitQueueTimeoutMS": 5000,
    "serverSelectionTimeoutMS": 5000,
    "socketTimeoutMS": 20000,
    "connectTimeoutMS": 10000,
    "retryWrites": True,
    "w": "majority"
}
```

### Frontend Optimizations

```typescript
// Code splitting and lazy loading
const Dashboard = lazy(() => import('./components/Dashboard'));
const Profile = lazy(() => import('./components/Profile'));
const Pantry = lazy(() => import('./components/Pantry'));

// Service worker for caching
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register('/sw.js');
}
```

### CDN and Caching Strategy

```yaml
# Render static site configuration
headers:
  - path: /assets/*
    name: Cache-Control
    value: public, max-age=31536000, immutable
  - path: /*.js
    name: Cache-Control
    value: public, max-age=86400
  - path: /*.css
    name: Cache-Control
    value: public, max-age=86400
  - path: /index.html
    name: Cache-Control
    value: no-cache
```

## Disaster Recovery

### Backup Strategy

1. **Database Backups**
   - Automated daily backups via MongoDB Atlas
   - Point-in-time recovery enabled
   - Cross-region backup replication
   - Monthly backup testing

2. **Application Backups**
   - Source code in GitHub (primary)
   - Docker images in registry
   - Configuration templates documented

3. **Recovery Procedures**
   - Database restore from backup
   - Application redeployment from GitHub
   - DNS and domain reconfiguration
   - User notification procedures

### Monitoring and Alerting

```python
# Health check alerts
ALERT_THRESHOLDS = {
    "response_time": 2.0,  # seconds
    "error_rate": 0.05,    # 5%
    "database_connections": 45,  # out of 50 max
    "memory_usage": 0.85,  # 85%
    "disk_usage": 0.90     # 90%
}
```

## Next Steps for Implementation

1. **Immediate Actions**
   - Set up MongoDB Atlas production cluster
   - Create Render services for backend and frontend
   - Configure environment variables in Render
   - Set up GitHub repository with deployment workflows

2. **Security Setup**
   - Generate secure JWT secrets
   - Configure CORS for production domains
   - Set up SSL certificates
   - Enable security headers

3. **Monitoring Setup**
   - Configure application logging
   - Set up health check monitoring
   - Configure error reporting (Sentry)
   - Set up performance monitoring

4. **Testing and Validation**
   - Deploy to production environment
   - Run end-to-end tests
   - Validate security configuration
   - Test backup and recovery procedures

This configuration provides a robust, secure, and scalable production environment for the EZ Eatin' application on Render with proper monitoring, security, and disaster recovery capabilities.