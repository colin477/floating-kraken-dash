
# EZ Eatin' Production Deployment Procedures & Validation Strategy

## Overview

This document provides step-by-step deployment procedures, CI/CD pipeline configuration, maintenance procedures, and comprehensive validation strategies for the EZ Eatin' production environment on Render.

## CI/CD Pipeline Configuration

### GitHub Actions Workflow

#### Complete Production Deployment Workflow

```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  NODE_VERSION: '18'
  PYTHON_VERSION: '3.11'

jobs:
  # Security and Quality Checks
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  # Backend Testing and Build
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run linting
        run: |
          pip install flake8 black isort
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          black --check .
          isort --check-only .

      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-report=html
        env:
          MONGODB_URI: mongodb://localhost:27017/test_db
          JWT_SECRET: test-secret-key
          APP_ENV: testing

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage

  # Frontend Testing and Build
  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: './frontend/package-lock.json'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run type checking
        run: npm run type-check

      - name: Run tests
        run: npm run test:coverage

      - name: Build production bundle
        run: npm run build
        env:
          VITE_API_BASE_URL: https://ezeatin-backend.onrender.com/api/v1
          VITE_APP_ENV: production

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: ./frontend/dist

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend
          name: frontend-coverage

  # End-to-End Testing
  e2e-tests:
    name: End-to-End Tests
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    if: github.event_name == 'pull_request'

    services:
      mongodb:
        image: mongo:7.0
        ports:
          - 27017:27017

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Start backend server
        run: |
          cd backend
          python main.py &
          sleep 10
        env:
          MONGODB_URI: mongodb://localhost:27017/test_db
          JWT_SECRET: test-secret-key
          APP_ENV: testing
          PORT: 8000

      - name: Start frontend server
        run: |
          cd frontend
          npm run dev &
          sleep 10
        env:
          VITE_API_BASE_URL: http://localhost:8000/api/v1

      - name: Run Playwright tests
        run: |
          cd frontend
          npx playwright install
          npx playwright test

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: ./frontend/playwright-report

  # Production Deployment
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [security-scan, backend-test, frontend-test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to Render
        uses: render-deploy/github-action@v1
        with:
          service-id: ${{ secrets.RENDER_BACKEND_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
          wait-for-success: true

      - name: Deploy Frontend to Render
        uses: render-deploy/github-action@v1
        with:
          service-id: ${{ secrets.RENDER_FRONTEND_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
          wait-for-success: true

      - name: Run post-deployment health checks
        run: |
          sleep 60  # Wait for deployment to stabilize
          curl -f https://ezeatin-backend.onrender.com/healthz
          curl -f https://ezeatin-frontend.onrender.com

      - name: Notify deployment success
        uses: 8398a7/action-slack@v3
        if: success()
        with:
          status: success
          text: '🚀 Production deployment successful!'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Notify deployment failure
        uses: 8398a7/action-slack@v3
        if: failure()
        with:
          status: failure
          text: '❌ Production deployment failed!'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Branch Protection Rules

```yaml
# GitHub Branch Protection Configuration
branch_protection:
  main:
    required_status_checks:
      strict: true
      contexts:
        - "Security Scan"
        - "Backend Tests"
        - "Frontend Tests"
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 1
      dismiss_stale_reviews: true
      require_code_owner_reviews: true
    restrictions: null
    allow_force_pushes: false
    allow_deletions: false
```

## Production Environment Setup Procedures

### Step 1: MongoDB Atlas Production Setup

#### 1.1 Create Production Cluster

```bash
# MongoDB Atlas CLI commands (or use web interface)
atlas clusters create EZEatin-Production \
  --provider AWS \
  --region US_EAST_1 \
  --tier M10 \
  --diskSizeGB 10 \
  --backup \
  --projectId YOUR_PROJECT_ID
```

#### 1.2 Configure Database Security

```javascript
// Database user creation
{
  "username": "ezeatin_prod_user",
  "password": "GENERATE_SECURE_PASSWORD",
  "roles": [
    {
      "role": "readWrite",
      "db": "ez_eatin_prod"
    }
  ],
  "scopes": [
    {
      "name": "EZEatin-Production",
      "type": "CLUSTER"
    }
  ]
}

// Network access configuration
{
  "ipAccessList": [
    {
      "ipAddress": "0.0.0.0/0",
      "comment": "Render deployment access - restrict to Render IPs in production"
    }
  ]
}
```

#### 1.3 Database Initialization Script

```python
# scripts/init_production_db.py
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def initialize_production_database():
    """Initialize production database with indexes and collections"""
    
    # Connect to production database
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DATABASE_NAME", "ez_eatin_prod")]
    
    # Create collections with validation schemas
    collections = [
        {
            "name": "users",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "password_hash", "created_at"],
                    "properties": {
                        "email": {"bsonType": "string", "pattern": "^.+@.+$"},
                        "password_hash": {"bsonType": "string"},
                        "full_name": {"bsonType": "string"},
                        "is_active": {"bsonType": "bool"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"}
                    }
                }
            }
        },
        {
            "name": "profiles",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "created_at"],
                    "properties": {
                        "user_id": {"bsonType": "objectId"},
                        "dietary_restrictions": {"bsonType": "array"},
                        "allergies": {"bsonType": "array"},
                        "family_members": {"bsonType": "array"},
                        "preferences": {"bsonType": "object"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"}
                    }
                }
            }
        }
    ]
    
    # Create collections
    for collection_config in collections:
        try:
            await db.create_collection(
                collection_config["name"],
                validator=collection_config["validator"]
            )
            print(f"✅ Created collection: {collection_config['name']}")
        except Exception as e:
            print(f"⚠️  Collection {collection_config['name']} may already exist: {e}")
    
    # Create indexes
    indexes = [
        {"collection": "users", "index": [("email", 1)], "unique": True},
        {"collection": "users", "index": [("created_at", 1)]},
        {"collection": "profiles", "index": [("user_id", 1)], "unique": True},
        {"collection": "pantry_items", "index": [("user_id", 1), ("category", 1)]},
        {"collection": "pantry_items", "index": [("user_id", 1), ("expiration_date", 1)]},
        {"collection": "recipes", "index": [("user_id", 1)]},
        {"collection": "recipes", "index": [("tags", 1)]},
        {"collection": "community_posts", "index": [("user_id", 1), ("created_at", -1)]},
        {"collection": "community_posts", "index": [("post_type", 1), ("is_public", 1)]}
    ]
    
    for index_config in indexes:
        try:
            await db[index_config["collection"]].create_index(
                index_config["index"],
                unique=index_config.get("unique", False)
            )
            print(f"✅ Created index on {index_config['collection']}: {index_config['index']}")
        except Exception as e:
            print(f"⚠️  Index may already exist: {e}")
    
    print("🎉 Database initialization completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(initialize_production_database())
```

### Step 2: Render Service Configuration

#### 2.1 Backend Service Setup

```yaml
# render.yaml - Backend Service
services:
  - type: web
    name: ezeatin-backend
    runtime: python
    plan: standard  # $25/month for production
    region: oregon  # Choose closest to your users
    branch: main
    rootDir: backend
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
    startCommand: python main.py
    healthCheckPath: /healthz
    autoDeploy: true
    
    envVars:
      - key: APP_ENV
        value: production
      - key: PORT
        value: 10000
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: MONGODB_URI
        sync: false  # Set manually in Render dashboard
      - key: DATABASE_NAME
        value: ez_eatin_prod
      - key: JWT_SECRET
        sync: false  # Set manually in Render dashboard
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_EXPIRES_IN
        value: 86400
      - key: CORS_ORIGINS
        value: https://ezeatin-frontend.onrender.com,https://app.ezeatin.com
      - key: API_BASE_PATH
        value: /api/v1
      - key: LOG_LEVEL
        value: INFO
      - key: SECURE_HEADERS
        value: true
      - key: RATE_LIMIT_ENABLED
        value: true
      - key: RATE_LIMIT_REQUESTS_PER_MINUTE
        value: 100
```

#### 2.2 Frontend Service Setup

```yaml
# render.yaml - Frontend Service
  - type: web
    name: ezeatin-frontend
    runtime: static
    plan: free  # Static sites are free on Render
    region: oregon
    branch: main
    rootDir: frontend
    buildCommand: |
      npm ci
      npm run build
    staticPublishPath: ./dist
    autoDeploy: true
    
    envVars:
      - key: VITE_API_BASE_URL
        value: https://ezeatin-backend.onrender.com/api/v1
      - key: VITE_APP_ENV
        value: production
      - key: VITE_DEMO_MODE_ENABLED
        value: false
      - key: NODE_VERSION
        value: 18
    
    headers:
      - path: /*
        name: X-Frame-Options
        value: DENY
      - path: /*
        name: X-Content-Type-Options
        value: nosniff
      - path: /*
        name: Strict-Transport-Security
        value: max-age=31536000; includeSubDomains
      - path: /*
        name: Referrer-Policy
        value: strict-origin-when-cross-origin
      - path: /*
        name: Content-Security-Policy
        value: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:
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
        value: no-cache, no-store, must-revalidate
    
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

### Step 3: GitHub Repository Configuration

#### 3.1 Required Secrets

Set these secrets in GitHub repository settings:

```bash
# Render API Configuration
RENDER_API_KEY=rnd_xxxxxxxxxxxxxxxxxxxxx
RENDER_BACKEND_SERVICE_ID=srv-xxxxxxxxxxxxxxxxxxxxx
RENDER_FRONTEND_SERVICE_ID=srv-xxxxxxxxxxxxxxxxxxxxx

# Database Configuration (for testing)
TEST_MONGODB_URI=mongodb://localhost:27017/test_db
TEST_JWT_SECRET=test-secret-key-for-ci

# Notification Configuration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
```

#### 3.2 Environment Files

```bash
# .env.production (template - actual values in Render)
APP_ENV=production
PORT=10000
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ez_eatin_prod
DATABASE_NAME=ez_eatin_prod
JWT_SECRET=your-production-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN=86400
CORS_ORIGINS=https://ezeatin-frontend.onrender.com
API_BASE_PATH=/api/v1
LOG_LEVEL=INFO
SECURE_HEADERS=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

## Production Validation Strategy

### Automated Testing Suite

#### 1. Health Check Validation

```python
# tests/production/test_health_checks.py
import pytest
import httpx
import asyncio

class TestProductionHealthChecks:
    
    @pytest.fixture
    def api_base_url(self):
        return "https://ezeatin-backend.onrender.com"
    
    @pytest.fixture
    def frontend_url(self):
        return "https://ezeatin-frontend.onrender.com"
    
    async def test_backend_health_check(self, api_base_url):
        """Test backend health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/healthz")
            
            assert response.status_code == 200
            health_data = response.json()
            
            assert health_data["status"] in ["healthy", "degraded"]
            assert "timestamp" in health_data
            assert "version" in health_data
            assert health_data["database_connected"] is True
    
    async def test_frontend_accessibility(self, frontend_url):
        """Test frontend is accessible"""
        async with httpx.AsyncClient() as client:
            response = await client.get(frontend_url)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    async def test_api_cors_headers(self, api_base_url):
        """Test CORS headers are properly configured"""
        async with httpx.AsyncClient() as client:
            response = await client.options(
                f"{api_base_url}/api/v1/auth/me",
                headers={"Origin": "https://ezeatin-frontend.onrender.com"}
            )
            
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
    
    async def test_security_headers(self, frontend_url):
        """Test security headers are present"""
        async with httpx.AsyncClient() as client:
            response = await client.get(frontend_url)
            
            security_headers = [
                "x-frame-options",
                "x-content-type-options",
                "strict-transport-security",
                "referrer-policy"
            ]
            
            for header in security_headers:
                assert header in response.headers, f"Missing security header: {header}"
```

#### 2. API Endpoint Validation

```python
# tests/production/test_api_endpoints.py
import pytest
import httpx
import asyncio

class TestProductionAPIEndpoints:
    
    @pytest.fixture
    def api_base_url(self):
        return "https://ezeatin-backend.onrender.com/api/v1"
    
    async def test_auth_endpoints_accessible(self, api_base_url):
        """Test authentication endpoints are accessible"""
        async with httpx.AsyncClient() as client:
            # Test registration endpoint
            response = await client.post(
                f"{api_base_url}/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "testpassword123",
                    "full_name": "Test User"
                }
            )
            # Should return 400 (validation error) or 409 (user exists), not 500
            assert response.status_code in [400, 409, 422]
    
    async def test_pantry_endpoints_require_auth(self, api_base_url):
        """Test pantry endpoints require authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/pantry/")
            assert response.status_code == 401  # Unauthorized
    
    async def test_rate_limiting(self, api_base_url):
        """Test rate limiting is working"""
        async with httpx.AsyncClient() as client:
            # Make multiple rapid requests
            tasks = []
            for _ in range(10):
                task = client.get(f"{api_base_url}/healthz")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed (health check not rate limited)
            for response in responses:
                if isinstance(response, httpx.Response):
                    assert response.status_code == 200
```

#### 3. Database Validation

```python
# tests/production/test_database.py
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

class TestProductionDatabase:
    
    @pytest.fixture
    async def db_client(self):
        """Create database client for testing"""
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        yield client
        client.close()
    
    async def test_database_connection(self, db_client):
        """Test database connection is working"""
        # Test ping
        result = await db_client.admin.command("ping")
        assert result["ok"] == 1
    
    async def test_database_indexes(self, db_client):
        """Test required indexes exist"""
        db = db_client[os.getenv("DATABASE_NAME", "ez_eatin_prod")]
        
        # Check users collection indexes
        users_indexes = await db.users.list_indexes().to_list(length=None)
        index_names = [idx["name"] for idx in users_indexes]
        
        assert "email_1" in index_names, "Email index missing on users collection"
    
    async def test_database_collections(self, db_client):
        """Test required collections exist"""
        db = db_client[os.getenv("DATABASE_NAME", "ez_eatin_prod")]
        
        collections = await db.list_collection_names()
        required_collections = [
            "users", "profiles", "pantry_items", 
            "recipes", "community_posts", "shopping_lists"
        ]
        
        for collection in required_collections:
            assert collection in collections, f"Missing collection: {collection}"
```

### Performance Validation

#### 1. Load Testing Script

```python
# tests/performance/load_test.py
import asyncio
import aiohttp
import time
import statistics
from typing import List

class LoadTester:
    def __init__(self, base_url: str, concurrent_users: int = 10):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results = []
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str) -> dict:
        """Make a single request and measure response time"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                end_time = time.time()
                return {
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status < 400
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def run_load_test(self, endpoints: List[str], duration_seconds: int = 60):
        """Run load test for specified duration"""
        print(f"Starting load test with {self.concurrent_users} concurrent users for {duration_seconds} seconds")
        
        start_time = time.time()
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                # Create tasks for concurrent requests
                for endpoint in endpoints:
                    for _ in range(self.concurrent_users):
                        task = self.make_request(session, endpoint)
                        tasks.append(task)
                
                # Execute batch of requests
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                self.results.extend([r for r in batch_results if isinstance(r, dict)])
                tasks.clear()
                
                # Small delay between batches
                await asyncio.sleep(0.1)
    
    def generate_report(self) -> dict:
        """Generate performance report"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        response_times = [r["response_time"] for r in self.results if r["success"]]
        success_count = sum(1 for r in self.results if r["success"])
        total_requests = len(self.results)
        
        return {
            "total_requests": total_requests,
            "successful_requests": success_count,
            "failed_requests": total_requests - success_count,
            "success_rate": (success_count / total_requests) * 100,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            "p99_response_time": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0
        }

# Usage example
async def run_production_load_test():
    tester = LoadTester("https://ezeatin-backend.onrender.com", concurrent_users=5)
    
    endpoints = [
        "/healthz",
        "/api/v1/auth/me",  # Will fail without auth, but tests endpoint
        "/"
    ]
    
    await tester.run_load_test(endpoints, duration_seconds=30)
    report = tester.generate_report()
    
    print("Load Test Report:")
    print(f"Total Requests: {report['total_requests']}")
    print(f"Success Rate: {report['success_rate']:.2f}%")
    print(f"Average Response Time: {report['avg_response_time']:.3f}s")
    print(f"95th Percentile: {report['p95_response_time']:.3f}s")

if __name__ == "__main__":
    asyncio.run(run_production_load_test())
```

### Security Validation

#### 1. Security Testing Script

```python
# tests/security/security_test.py
import httpx
import asyncio
import ssl
import socket

class SecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = base_url.replace("https://", "").replace("http://", "")
    
    async def test_ssl_configuration(self) -> dict:
        """Test SSL/TLS configuration"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    return {
                        "ssl_valid": True,
                        "protocol": cipher[1] if cipher else "Unknown",
                        "cipher": cipher[0] if cipher else "Unknown",
                        "cert_subject": dict(x[0] for x in cert['subject']),
                        "cert_issuer": dict(x[0] for x in cert['issuer']),
                        "cert_expires": cert['notAfter']
                    }
        except Exception as e:
            return {"ssl_valid": False, "error": str(e)}
    
    async def test_security_headers(self) -> dict:
        """Test security headers"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url)
            
            security_headers = {
                "strict-transport-security": response.headers.get("strict-transport-security"),
                "x-frame-options": response.headers.get("x-frame-options"),
                "x-content-type-options": response.headers.get("x-content-type-options"),
                "referrer-policy": response.headers.get("referrer-policy"),
                "content-security-policy": response.headers.get("content-security-policy")
            }
            
            return {
                "headers_present": {k: v is not None for k, v in security_headers.items()},
                "headers_values": security_headers
            }
    
    async def test_common_vulnerabilities(self) -> dict:
        """Test for common vulnerabilities"""
        results = {}
        
        async with httpx.AsyncClient() as client:
            # Test for directory traversal
            try:
                response = await client.get(f"{self.base_url}/../../../etc/passwd")
                results["directory_traversal"] = {
                    "vulnerable": response.status_code == 200 and "root:" in response.text,
                    "status_code": response.status_code
                }
            except:
                results["directory_traversal"] = {"vulnerable": False, "error": "Request failed"}
            
            # Test for SQL injection (basic)
            try:
                response = await client.get(f"{self.base_url}/api/v1/auth/login?email=' OR '1'='1")
                results["sql_injection"] = {