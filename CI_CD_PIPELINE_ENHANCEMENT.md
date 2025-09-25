# EZ Eatin' CI/CD Pipeline Enhancement Guide

## Overview

This document outlines the enhanced CI/CD pipeline for EZ Eatin', building upon the existing [`test.yml`](.github/workflows/test.yml:1) workflow to include production deployment capabilities, security scanning, and automated quality gates.

## Table of Contents

1. [Current Pipeline Analysis](#current-pipeline-analysis)
2. [Enhanced Pipeline Architecture](#enhanced-pipeline-architecture)
3. [Production Deployment Workflows](#production-deployment-workflows)
4. [Security and Quality Gates](#security-and-quality-gates)
5. [Environment Management](#environment-management)
6. [Monitoring and Notifications](#monitoring-and-notifications)
7. [Implementation Guide](#implementation-guide)

---

## Current Pipeline Analysis

### Existing Workflow (`.github/workflows/test.yml`)
The current pipeline includes:
- **Trigger**: Push to main branch and pull requests
- **Backend Testing**: Python 3.11, pytest, MongoDB service
- **Frontend Testing**: Node.js 18, pnpm, Vitest
- **Basic Quality Checks**: Linting and testing

### Identified Enhancements Needed
1. **Production Deployment**: Automated deployment to staging and production
2. **Security Scanning**: Vulnerability assessment and dependency checks
3. **Performance Testing**: Load testing and performance regression detection
4. **Docker Integration**: Container building and registry management
5. **Environment Promotion**: Staged deployment with approval gates
6. **Monitoring Integration**: Deployment health checks and rollback capabilities

---

## Enhanced Pipeline Architecture

### Pipeline Stages Overview

```mermaid
graph TD
    A[Code Push/PR] --> B[Quality Gates]
    B --> C[Security Scan]
    C --> D[Build & Test]
    D --> E[Docker Build]
    E --> F[Deploy to Staging]
    F --> G[Integration Tests]
    G --> H[Manual Approval]
    H --> I[Deploy to Production]
    I --> J[Health Checks]
    J --> K[Monitoring Setup]
    
    B --> B1[Lint Check]
    B --> B2[Unit Tests]
    B --> B3[Type Check]
    
    C --> C1[Dependency Scan]
    C --> C2[SAST Analysis]
    C --> C3[Container Scan]
    
    D --> D1[Backend Tests]
    D --> D2[Frontend Tests]
    D --> D3[Integration Tests]
    
    E --> E1[Backend Image]
    E --> E2[Frontend Image]
    
    G --> G1[API Tests]
    G --> G2[E2E Tests]
    G --> G3[Performance Tests]
```

### Workflow Files Structure

```
.github/
├── workflows/
│   ├── test.yml                    # Existing - Enhanced
│   ├── deploy-staging.yml          # New - Staging deployment
│   ├── deploy-production.yml       # New - Production deployment
│   ├── security-scan.yml          # New - Security scanning
│   ├── performance-test.yml       # New - Performance testing
│   └── rollback.yml               # New - Emergency rollback
├── actions/
│   ├── setup-backend/             # Reusable backend setup
│   ├── setup-frontend/            # Reusable frontend setup
│   ├── docker-build/              # Docker build action
│   └── deploy-render/             # Render deployment action
└── templates/
    ├── bug_report.md
    ├── feature_request.md
    └── pull_request_template.md
```

---

## Production Deployment Workflows

### 1. Enhanced Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Test and Quality Assurance

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  NODE_VERSION: '18'
  PYTHON_VERSION: '3.11'
  PNPM_VERSION: '8'

jobs:
  # Quality Gates
  quality-gates:
    name: Quality Gates
    runs-on: ubuntu-latest
    outputs:
      backend-changed: ${{ steps.changes.outputs.backend }}
      frontend-changed: ${{ steps.changes.outputs.frontend }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect changes
        uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            backend:
              - 'backend/**'
              - 'requirements.txt'
            frontend:
              - 'frontend/**'
              - 'package.json'
              - 'pnpm-lock.yaml'

      - name: Setup Python
        if: steps.changes.outputs.backend == 'true'
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Setup Node.js
        if: steps.changes.outputs.frontend == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install pnpm
        if: steps.changes.outputs.frontend == 'true'
        uses: pnpm/action-setup@v2
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Backend linting
        if: steps.changes.outputs.backend == 'true'
        run: |
          cd backend
          pip install flake8 black isort bandit
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          black --check .
          isort --check-only .
          bandit -r . -f json -o bandit-report.json

      - name: Frontend linting
        if: steps.changes.outputs.frontend == 'true'
        run: |
          cd frontend
          pnpm install --frozen-lockfile
          pnpm run lint
          pnpm run type-check

      - name: Upload security report
        if: steps.changes.outputs.backend == 'true'
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: backend/bandit-report.json

  # Security Scanning
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: quality-gates
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
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
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Dependency vulnerability scan
        run: |
          # Backend dependencies
          cd backend
          pip install safety
          safety check --json --output safety-report.json || true
          
          # Frontend dependencies
          cd ../frontend
          npm audit --audit-level=high --json > npm-audit.json || true

  # Backend Testing
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    needs: quality-gates
    if: needs.quality-gates.outputs.backend-changed == 'true'
    
    services:
      mongodb:
        image: mongo:7.0
        env:
          MONGO_INITDB_ROOT_USERNAME: admin
          MONGO_INITDB_ROOT_PASSWORD: password
        ports:
          - 27017:27017
        options: >-
          --health-cmd "mongosh --eval 'db.adminCommand(\"ping\")'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest-cov pytest-xdist

      - name: Run tests with coverage
        env:
          MONGODB_URI: mongodb://admin:password@localhost:27017/test_db?authSource=admin
          JWT_SECRET: test-secret-key-for-ci
          APP_ENV: testing
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=html -n auto

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
          flags: backend
          name: backend-coverage

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-test-results
          path: |
            backend/coverage.xml
            backend/htmlcov/

  # Frontend Testing
  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest
    needs: quality-gates
    if: needs.quality-gates.outputs.frontend-changed == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install pnpm
        uses: pnpm/action-setup@v2
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Cache pnpm dependencies
        uses: actions/cache@v3
        with:
          path: ~/.pnpm-store
          key: ${{ runner.os }}-pnpm-${{ hashFiles('frontend/pnpm-lock.yaml') }}
          restore-keys: |
            ${{ runner.os }}-pnpm-

      - name: Install dependencies
        run: |
          cd frontend
          pnpm install --frozen-lockfile

      - name: Run unit tests
        run: |
          cd frontend
          pnpm run test:coverage

      - name: Run E2E tests
        run: |
          cd frontend
          pnpm run build
          pnpm run test:e2e

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: frontend/coverage/lcov.info
          flags: frontend
          name: frontend-coverage

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: frontend-test-results
          path: |
            frontend/coverage/
            frontend/test-results/
            frontend/playwright-report/

  # Build Docker Images
  build-images:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    outputs:
      backend-image: ${{ steps.backend-meta.outputs.tags }}
      frontend-image: ${{ steps.frontend-meta.outputs.tags }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract backend metadata
        id: backend-meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/backend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.backend-meta.outputs.tags }}
          labels: ${{ steps.backend-meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Extract frontend metadata
        id: frontend-meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/frontend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.frontend-meta.outputs.tags }}
          labels: ${{ steps.frontend-meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Trigger Staging Deployment
  trigger-staging:
    name: Trigger Staging Deployment
    runs-on: ubuntu-latest
    needs: build-images
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Trigger staging deployment
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          event-type: deploy-staging
          client-payload: |
            {
              "backend_image": "${{ needs.build-images.outputs.backend-image }}",
              "frontend_image": "${{ needs.build-images.outputs.frontend-image }}",
              "commit_sha": "${{ github.sha }}"
            }
```

### 2. Staging Deployment Workflow (`.github/workflows/deploy-staging.yml`)

```yaml
name: Deploy to Staging

on:
  repository_dispatch:
    types: [deploy-staging]
  workflow_dispatch:
    inputs:
      backend_image:
        description: 'Backend Docker image tag'
        required: true
        default: 'latest'
      frontend_image:
        description: 'Frontend Docker image tag'
        required: true
        default: 'latest'

env:
  RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
  STAGING_BACKEND_SERVICE_ID: ${{ secrets.STAGING_BACKEND_SERVICE_ID }}
  STAGING_FRONTEND_SERVICE_ID: ${{ secrets.STAGING_FRONTEND_SERVICE_ID }}

jobs:
  deploy-staging:
    name: Deploy to Staging Environment
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup deployment variables
        id: vars
        run: |
          if [ "${{ github.event_name }}" = "repository_dispatch" ]; then
            echo "backend_image=${{ github.event.client_payload.backend_image }}" >> $GITHUB_OUTPUT
            echo "frontend_image=${{ github.event.client_payload.frontend_image }}" >> $GITHUB_OUTPUT
            echo "commit_sha=${{ github.event.client_payload.commit_sha }}" >> $GITHUB_OUTPUT
          else
            echo "backend_image=${{ github.event.inputs.backend_image }}" >> $GITHUB_OUTPUT
            echo "frontend_image=${{ github.event.inputs.frontend_image }}" >> $GITHUB_OUTPUT
            echo "commit_sha=${{ github.sha }}" >> $GITHUB_OUTPUT
          fi

      - name: Deploy backend to Render
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ env.RENDER_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "clearCache": "clear",
              "imageUrl": "${{ steps.vars.outputs.backend_image }}"
            }' \
            "https://api.render.com/v1/services/${{ env.STAGING_BACKEND_SERVICE_ID }}/deploys"

      - name: Deploy frontend to Render
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ env.RENDER_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "clearCache": "clear",
              "imageUrl": "${{ steps.vars.outputs.frontend_image }}"
            }' \
            "https://api.render.com/v1/services/${{ env.STAGING_FRONTEND_SERVICE_ID }}/deploys"

      - name: Wait for deployment
        run: |
          echo "Waiting for deployment to complete..."
          sleep 60

      - name: Run health checks
        run: |
          # Backend health check
          for i in {1..10}; do
            if curl -f "${{ secrets.STAGING_BACKEND_URL }}/healthz"; then
              echo "Backend health check passed"
              break
            fi
            echo "Backend health check failed, attempt $i/10"
            sleep 30
          done

          # Frontend health check
          for i in {1..10}; do
            if curl -f "${{ secrets.STAGING_FRONTEND_URL }}/health"; then
              echo "Frontend health check passed"
              break
            fi
            echo "Frontend health check failed, attempt $i/10"
            sleep 30
          done

      - name: Run integration tests
        run: |
          # Install test dependencies
          pip install pytest requests
          
          # Run staging integration tests
          export API_BASE_URL="${{ secrets.STAGING_BACKEND_URL }}"
          export FRONTEND_URL="${{ secrets.STAGING_FRONTEND_URL }}"
          pytest tests/integration/ -v

      - name: Notify deployment status
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          fields: repo,message,commit,author,action,eventName,ref,workflow

      - name: Trigger production deployment approval
        if: success()
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          event-type: staging-success
          client-payload: |
            {
              "backend_image": "${{ steps.vars.outputs.backend_image }}",
              "frontend_image": "${{ steps.vars.outputs.frontend_image }}",
              "commit_sha": "${{ steps.vars.outputs.commit_sha }}"
            }
```

### 3. Production Deployment Workflow (`.github/workflows/deploy-production.yml`)

```yaml
name: Deploy to Production

on:
  repository_dispatch:
    types: [staging-success]
  workflow_dispatch:
    inputs:
      backend_image:
        description: 'Backend Docker image tag'
        required: true
      frontend_image:
        description: 'Frontend Docker image tag'
        required: true
      skip_approval:
        description: 'Skip manual approval (emergency deployment)'
        type: boolean
        default: false

env:
  RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
  PROD_BACKEND_SERVICE_ID: ${{ secrets.PROD_BACKEND_SERVICE_ID }}
  PROD_FRONTEND_SERVICE_ID: ${{ secrets.PROD_FRONTEND_SERVICE_ID }}

jobs:
  # Manual approval gate
  approval:
    name: Production Deployment Approval
    runs-on: ubuntu-latest
    environment: production-approval
    if: github.event.inputs.skip_approval != 'true'
    steps:
      - name: Manual approval required
        run: |
          echo "Production deployment requires manual approval"
          echo "Backend image: ${{ github.event.client_payload.backend_image || github.event.inputs.backend_image }}"
          echo "Frontend image: ${{ github.event.client_payload.frontend_image || github.event.inputs.frontend_image }}"

  # Pre-deployment validation
  pre-deployment:
    name: Pre-deployment Validation
    runs-on: ubuntu-latest
    needs: [approval]
    if: always() && (needs.approval.result == 'success' || github.event.inputs.skip_approval == 'true')
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Validate staging environment
        run: |
          # Ensure staging is healthy before production deployment
          curl -f "${{ secrets.STAGING_BACKEND_URL }}/healthz"
          curl -f "${{ secrets.STAGING_FRONTEND_URL }}/health"

      - name: Run production readiness checks
        run: |
          # Run production readiness validation script
          python scripts/production_readiness_check.py

      - name: Database migration dry run
        run: |
          # Test database migrations in staging
          export MONGODB_URI="${{ secrets.STAGING_MONGODB_URI }}"
          python backend/scripts/migrate.py --dry-run

  # Production deployment
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    needs: [pre-deployment]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup deployment variables
        id: vars
        run: |
          if [ "${{ github.event_name }}" = "repository_dispatch" ]; then
            echo "backend_image=${{ github.event.client_payload.backend_image }}" >> $GITHUB_OUTPUT
            echo "frontend_image=${{ github.event.client_payload.frontend_image }}" >> $GITHUB_OUTPUT
            echo "commit_sha=${{ github.event.client_payload.commit_sha }}" >> $GITHUB_OUTPUT
          else
            echo "backend_image=${{ github.event.inputs.backend_image }}" >> $GITHUB_OUTPUT
            echo "frontend_image=${{ github.event.inputs.frontend_image }}" >> $GITHUB_OUTPUT
            echo "commit_sha=${{ github.sha }}" >> $GITHUB_OUTPUT
          fi

      - name: Create deployment record
        run: |
          # Record deployment in monitoring system
          curl -X POST \
            -H "Content-Type: application/json" \
            -d '{
              "deployment_id": "${{ github.run_id }}",
              "commit_sha": "${{ steps.vars.outputs.commit_sha }}",
              "backend_image": "${{ steps.vars.outputs.backend_image }}",
              "frontend_image": "${{ steps.vars.outputs.frontend_image }}",
              "environment": "production",
              "status": "started"
            }' \
            "${{ secrets.MONITORING_WEBHOOK_URL }}"

      - name: Run database migrations
        run: |
          export MONGODB_URI="${{ secrets.PROD_MONGODB_URI }}"
          python backend/scripts/migrate.py

      - name: Deploy backend to production
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ env.RENDER_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "clearCache": "clear",
              "imageUrl": "${{ steps.vars.outputs.backend_image }}"
            }' \
            "https://api.render.com/v1/services/${{ env.PROD_BACKEND_SERVICE_ID }}/deploys"

      - name: Wait for backend deployment
        run: |
          echo "Waiting for backend deployment..."
          sleep 90

      - name: Validate backend deployment
        run: |
          for i in {1..15}; do
            if curl -f "${{ secrets.PROD_BACKEND_URL }}/healthz"; then
              echo "Backend deployment successful"
              break
            fi
            echo "Backend validation failed, attempt $i/15"
            if [ $i -eq 15 ]; then
              echo "Backend deployment failed, initiating rollback"
              exit 1
            fi
            sleep 30
          done

      - name: Deploy frontend to production
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ env.RENDER_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "clearCache": "clear",
              "imageUrl": "${{ steps.vars.outputs.frontend_image }}"
            }' \
            "https://api.render.com/v1/services/${{ env.PROD_FRONTEND_SERVICE_ID }}/deploys"

      - name: Wait for frontend deployment
        run: |
          echo "Waiting for frontend deployment..."
          sleep 60

      - name: Validate frontend deployment
        run: |
          for i in {1..10}; do
            if curl -f "${{ secrets.PROD_FRONTEND_URL }}/health"; then
              echo "Frontend deployment successful"
              break
            fi
            echo "Frontend validation failed, attempt $i/10"
            if [ $i -eq 10 ]; then
              echo "Frontend deployment failed, initiating rollback"
              exit 1
            fi
            sleep 30
          done

      - name: Run smoke tests
        run: |
          # Run critical path smoke tests
          export API_BASE_URL="${{ secrets.PROD_BACKEND_URL }}"
          export FRONTEND_URL="${{ secrets.PROD_FRONTEND_URL }}"
          pytest tests/smoke/ -v

      - name: Update deployment record
        if: always()
        run: |
          STATUS="success"
          if [ "${{ job.status }}" != "success" ]; then
            STATUS="failed"
          fi
          
          curl -X PATCH \
            -H "Content-Type: application/json" \
            -d '{
              "deployment_id": "${{ github.run_id }}",
              "status": "'$STATUS'",
              "completed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
            }' \
            "${{ secrets.MONITORING_WEBHOOK_URL }}"

      - name: Notify deployment success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          fields: repo,message,commit,author,action,eventName,ref,workflow
          custom_payload: |
            {
              "text": "🚀 Production deployment successful!",
              "attachments": [{
                "color": "good",
                "fields": [{
                  "title": "Commit",
                  "value": "${{ steps.vars.outputs.commit_sha }}",
                  "short": true
                }, {
                  "title": "Backend Image",
                  "value": "${{ steps.vars.outputs.backend_image }}",
                  "short": true
                }, {
                  "title": "Frontend Image",
                  "value": "${{ steps.vars.outputs.frontend_image }}",
                  "short": true
                }]
              }]
            }

      - name: Trigger rollback on failure
        if: failure()
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          event-type: emergency-rollback
          client-payload: |
            {
              "reason": "Production deployment failed",
              "failed_deployment_id": "${{ github.run_id }}"
            }
```

### 4. Security Scanning Workflow (`.github/workflows/security-scan.yml`)

```yaml
name: Security Scanning

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
  push:
    branches: [ main ]
    paths:
      - 'backend/requirements.txt'
      - 'frontend/package.json'
      - 'frontend/pnpm-lock.yaml'

jobs:
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install pnpm
        uses: pnpm/action-setup@v2
        with:
          version: '8'

      - name: Python dependency scan
        run: |
          cd backend
          pip install safety
          safety check --json --output safety-report.json || true
          safety check --short-report

      - name: Node.js dependency scan
        run: |
          cd frontend
          pnpm install --frozen-lockfile
          pnpm audit --audit-level=high --json > npm-audit.json || true
          pnpm audit --audit-level=high

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            backend/safety-report.json
            frontend/npm-audit.json

  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build backend image for scanning
        run: |
          docker build -t ezeatin-backend:scan ./backend

      - name: Build frontend image for scanning
        run: |
          docker build -t ezeatin-frontend:scan ./frontend

      - name: Run Trivy scan on backend
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'ezeatin-backend:scan'
          format: 'sarif'
          output: 'backend-trivy.sarif'

      - name: Run Trivy scan on frontend
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'ezeatin-frontend:scan'
          format: 'sarif'
          output: 'frontend-trivy.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'backend-trivy.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'frontend-trivy.sarif'

  sast-analysis:
    name: Static Application Security Testing
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: python, javascript

      - name: Autobuild
        uses: github/codeql-action/autobuild@v2

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2

      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r backend/ -f json -o bandit-report.json || true
          bandit -r backend/ -f txt

      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
```

### 5