# EZ Eatin' Deployment Automation Scripts and Templates

## Overview

This document provides comprehensive deployment automation scripts, templates, and configurations for the EZ Eatin' application. These scripts enable automated deployment, environment management, and operational tasks across development, staging, and production environments.

## Table of Contents

1. [Deployment Scripts](#deployment-scripts)
2. [Environment Templates](#environment-templates)
3. [Database Management Scripts](#database-management-scripts)
4. [Monitoring Setup Scripts](#monitoring-setup-scripts)
5. [Backup and Recovery Scripts](#backup-and-recovery-scripts)
6. [Utility Scripts](#utility-scripts)
7. [Configuration Templates](#configuration-templates)

---

## Deployment Scripts

### 1. Master Deployment Script (`scripts/deploy.sh`)

```bash
#!/bin/bash
# EZ Eatin' Master Deployment Script
# Usage: ./scripts/deploy.sh [environment] [options]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/ezeatin-deploy-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
ENVIRONMENT=""
SKIP_TESTS=false
SKIP_BUILD=false
FORCE_DEPLOY=false
DRY_RUN=false
ROLLBACK=false

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

usage() {
    cat << EOF
EZ Eatin' Deployment Script

Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    dev         Deploy to development environment
    staging     Deploy to staging environment
    prod        Deploy to production environment

OPTIONS:
    --skip-tests        Skip running tests before deployment
    --skip-build        Skip building Docker images
    --force            Force deployment without confirmation
    --dry-run          Show what would be deployed without executing
    --rollback         Rollback to previous deployment
    --help             Show this help message

EXAMPLES:
    $0 staging                          # Deploy to staging with all checks
    $0 prod --force                     # Force deploy to production
    $0 dev --skip-tests --skip-build    # Quick deploy to dev
    $0 prod --rollback                  # Rollback production deployment

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|staging|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    error "Environment is required. Use --help for usage information."
fi

# Load environment configuration
ENV_FILE="$PROJECT_ROOT/config/environments/$ENVIRONMENT.env"
if [[ ! -f "$ENV_FILE" ]]; then
    error "Environment file not found: $ENV_FILE"
fi

source "$ENV_FILE"

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks for $ENVIRONMENT..."
    
    # Check required tools
    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
    command -v curl >/dev/null 2>&1 || error "curl is required but not installed"
    
    # Check environment variables
    [[ -z "$RENDER_API_KEY" ]] && error "RENDER_API_KEY not set"
    [[ -z "$BACKEND_SERVICE_ID" ]] && error "BACKEND_SERVICE_ID not set"
    [[ -z "$FRONTEND_SERVICE_ID" ]] && error "FRONTEND_SERVICE_ID not set"
    
    # Check Git status
    if [[ $(git status --porcelain) ]]; then
        warning "Working directory has uncommitted changes"
        if [[ "$FORCE_DEPLOY" != true ]]; then
            error "Commit or stash changes before deployment, or use --force"
        fi
    fi
    
    success "Pre-deployment checks passed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        warning "Skipping tests as requested"
        return
    fi
    
    log "Running test suite..."
    
    # Backend tests
    log "Running backend tests..."
    cd "$PROJECT_ROOT/backend"
    python -m pytest tests/ -v --tb=short
    
    # Frontend tests
    log "Running frontend tests..."
    cd "$PROJECT_ROOT/frontend"
    pnpm test --run
    
    cd "$PROJECT_ROOT"
    success "All tests passed"
}

# Build Docker images
build_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        warning "Skipping image build as requested"
        return
    fi
    
    log "Building Docker images..."
    
    # Build backend image
    log "Building backend image..."
    docker build -t "ezeatin-backend:$ENVIRONMENT" ./backend
    
    # Build frontend image
    log "Building frontend image..."
    docker build -t "ezeatin-frontend:$ENVIRONMENT" ./frontend
    
    success "Docker images built successfully"
}

# Deploy to Render
deploy_to_render() {
    log "Deploying to Render ($ENVIRONMENT)..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log "DRY RUN: Would deploy to $ENVIRONMENT environment"
        log "Backend Service ID: $BACKEND_SERVICE_ID"
        log "Frontend Service ID: $FRONTEND_SERVICE_ID"
        return
    fi
    
    # Deploy backend
    log "Deploying backend service..."
    BACKEND_DEPLOY_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"clearCache": "clear"}' \
        "https://api.render.com/v1/services/$BACKEND_SERVICE_ID/deploys")
    
    BACKEND_DEPLOY_ID=$(echo "$BACKEND_DEPLOY_RESPONSE" | jq -r '.id')
    log "Backend deployment started: $BACKEND_DEPLOY_ID"
    
    # Deploy frontend
    log "Deploying frontend service..."
    FRONTEND_DEPLOY_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"clearCache": "clear"}' \
        "https://api.render.com/v1/services/$FRONTEND_SERVICE_ID/deploys")
    
    FRONTEND_DEPLOY_ID=$(echo "$FRONTEND_DEPLOY_RESPONSE" | jq -r '.id')
    log "Frontend deployment started: $FRONTEND_DEPLOY_ID"
    
    # Wait for deployments
    wait_for_deployment "$BACKEND_SERVICE_ID" "$BACKEND_DEPLOY_ID" "backend"
    wait_for_deployment "$FRONTEND_SERVICE_ID" "$FRONTEND_DEPLOY_ID" "frontend"
    
    success "Deployment completed successfully"
}

# Wait for deployment completion
wait_for_deployment() {
    local service_id="$1"
    local deploy_id="$2"
    local service_name="$3"
    local max_wait=1800  # 30 minutes
    local wait_time=0
    
    log "Waiting for $service_name deployment to complete..."
    
    while [[ $wait_time -lt $max_wait ]]; do
        DEPLOY_STATUS=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
            "https://api.render.com/v1/services/$service_id/deploys/$deploy_id" | \
            jq -r '.status')
        
        case "$DEPLOY_STATUS" in
            "live")
                success "$service_name deployment completed successfully"
                return 0
                ;;
            "build_failed"|"update_failed"|"canceled")
                error "$service_name deployment failed with status: $DEPLOY_STATUS"
                ;;
            "created"|"build_in_progress"|"update_in_progress")
                log "$service_name deployment in progress... ($DEPLOY_STATUS)"
                sleep 30
                wait_time=$((wait_time + 30))
                ;;
            *)
                warning "Unknown deployment status: $DEPLOY_STATUS"
                sleep 30
                wait_time=$((wait_time + 30))
                ;;
        esac
    done
    
    error "$service_name deployment timed out after $max_wait seconds"
}

# Health checks
run_health_checks() {
    log "Running health checks..."
    
    local backend_url="$BACKEND_URL"
    local frontend_url="$FRONTEND_URL"
    local max_attempts=10
    local attempt=1
    
    # Backend health check
    log "Checking backend health at $backend_url/healthz"
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$backend_url/healthz" >/dev/null; then
            success "Backend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Backend health check failed after $max_attempts attempts"
        fi
        
        log "Backend health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 30
        attempt=$((attempt + 1))
    done
    
    # Frontend health check
    log "Checking frontend health at $frontend_url"
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$frontend_url" >/dev/null; then
            success "Frontend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Frontend health check failed after $max_attempts attempts"
        fi
        
        log "Frontend health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 30
        attempt=$((attempt + 1))
    done
    
    success "All health checks passed"
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back $ENVIRONMENT deployment..."
    
    # Get previous deployment
    BACKEND_DEPLOYS=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$BACKEND_SERVICE_ID/deploys?limit=5")
    
    PREVIOUS_BACKEND_DEPLOY=$(echo "$BACKEND_DEPLOYS" | jq -r '.[1].id')
    
    if [[ "$PREVIOUS_BACKEND_DEPLOY" == "null" ]]; then
        error "No previous backend deployment found for rollback"
    fi
    
    # Rollback backend
    log "Rolling back backend to deployment: $PREVIOUS_BACKEND_DEPLOY"
    curl -s -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        "https://api.render.com/v1/services/$BACKEND_SERVICE_ID/deploys/$PREVIOUS_BACKEND_DEPLOY/rollback"
    
    # Similar for frontend
    FRONTEND_DEPLOYS=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$FRONTEND_SERVICE_ID/deploys?limit=5")
    
    PREVIOUS_FRONTEND_DEPLOY=$(echo "$FRONTEND_DEPLOYS" | jq -r '.[1].id')
    
    if [[ "$PREVIOUS_FRONTEND_DEPLOY" == "null" ]]; then
        error "No previous frontend deployment found for rollback"
    fi
    
    log "Rolling back frontend to deployment: $PREVIOUS_FRONTEND_DEPLOY"
    curl -s -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        "https://api.render.com/v1/services/$FRONTEND_SERVICE_ID/deploys/$PREVIOUS_FRONTEND_DEPLOY/rollback"
    
    success "Rollback initiated successfully"
}

# Confirmation prompt
confirm_deployment() {
    if [[ "$FORCE_DEPLOY" == true ]] || [[ "$DRY_RUN" == true ]]; then
        return
    fi
    
    echo
    echo "=== DEPLOYMENT CONFIRMATION ==="
    echo "Environment: $ENVIRONMENT"
    echo "Backend Service: $BACKEND_SERVICE_ID"
    echo "Frontend Service: $FRONTEND_SERVICE_ID"
    echo "Skip Tests: $SKIP_TESTS"
    echo "Skip Build: $SKIP_BUILD"
    echo
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled by user"
        exit 0
    fi
}

# Main execution
main() {
    log "Starting EZ Eatin' deployment to $ENVIRONMENT"
    log "Log file: $LOG_FILE"
    
    if [[ "$ROLLBACK" == true ]]; then
        rollback_deployment
        exit 0
    fi
    
    pre_deployment_checks
    confirm_deployment
    run_tests
    build_images
    deploy_to_render
    run_health_checks
    
    success "Deployment to $ENVIRONMENT completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
}

# Execute main function
main "$@"
```

### 2. Environment Setup Script (`scripts/setup-environment.sh`)

```bash
#!/bin/bash
# EZ Eatin' Environment Setup Script
# Usage: ./scripts/setup-environment.sh [environment]

set -e

ENVIRONMENT="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -z "$ENVIRONMENT" ]]; then
    echo "Usage: $0 [dev|staging|prod]"
    exit 1
fi

# Create environment configuration directory
mkdir -p "$PROJECT_ROOT/config/environments"

# Generate environment-specific configuration
case "$ENVIRONMENT" in
    "dev")
        cat > "$PROJECT_ROOT/config/environments/dev.env" << EOF
# Development Environment Configuration
ENVIRONMENT=development
BACKEND_SERVICE_ID=srv-dev-backend-id
FRONTEND_SERVICE_ID=srv-dev-frontend-id
BACKEND_URL=https://ezeatin-backend-dev.onrender.com
FRONTEND_URL=https://ezeatin-frontend-dev.onrender.com
MONGODB_URI=mongodb+srv://dev-user:dev-password@cluster.mongodb.net/ez_eatin_dev
RENDER_API_KEY=\${RENDER_API_KEY}
SLACK_WEBHOOK=\${SLACK_WEBHOOK}
EOF
        ;;
    "staging")
        cat > "$PROJECT_ROOT/config/environments/staging.env" << EOF
# Staging Environment Configuration
ENVIRONMENT=staging
BACKEND_SERVICE_ID=srv-staging-backend-id
FRONTEND_SERVICE_ID=srv-staging-frontend-id
BACKEND_URL=https://ezeatin-backend-staging.onrender.com
FRONTEND_URL=https://ezeatin-frontend-staging.onrender.com
MONGODB_URI=mongodb+srv://staging-user:staging-password@cluster.mongodb.net/ez_eatin_staging
RENDER_API_KEY=\${RENDER_API_KEY}
SLACK_WEBHOOK=\${SLACK_WEBHOOK}
EOF
        ;;
    "prod")
        cat > "$PROJECT_ROOT/config/environments/prod.env" << EOF
# Production Environment Configuration
ENVIRONMENT=production
BACKEND_SERVICE_ID=srv-prod-backend-id
FRONTEND_SERVICE_ID=srv-prod-frontend-id
BACKEND_URL=https://ezeatin-backend.onrender.com
FRONTEND_URL=https://ezeatin-frontend.onrender.com
MONGODB_URI=mongodb+srv://prod-user:prod-password@cluster.mongodb.net/ez_eatin_prod
RENDER_API_KEY=\${RENDER_API_KEY}
SLACK_WEBHOOK=\${SLACK_WEBHOOK}
EOF
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "Environment configuration created: config/environments/$ENVIRONMENT.env"
echo "Please update the configuration with actual values before deployment."
```

### 3. Database Migration Script (`scripts/migrate-database.py`)

```python
#!/usr/bin/env python3
"""
EZ Eatin' Database Migration Script
Usage: python scripts/migrate-database.py [--environment] [--dry-run]
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, mongodb_uri: str, database_name: str, dry_run: bool = False):
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.dry_run = dry_run
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create database indexes"""
        logger.info("Creating database indexes...")
        
        indexes = {
            'users': [
                {'keys': [('email', 1)], 'unique': True},
                {'keys': [('created_at', 1)]},
                {'keys': [('is_active', 1)]},
            ],
            'profiles': [
                {'keys': [('user_id', 1)], 'unique': True},
                {'keys': [('dietary_restrictions', 1)]},
                {'keys': [('household_size', 1)]},
            ],
            'pantry_items': [
                {'keys': [('user_id', 1)]},
                {'keys': [('user_id', 1), ('name', 1)]},
                {'keys': [('user_id', 1), ('category', 1)]},
                {'keys': [('user_id', 1), ('expiry_date', 1)]},
                {'keys': [('user_id', 1), ('quantity', 1)]},
            ],
            'recipes': [
                {'keys': [('user_id', 1)]},
                {'keys': [('name', 'text'), ('description', 'text')]},
                {'keys': [('cuisine_type', 1)]},
                {'keys': [('difficulty', 1)]},
                {'keys': [('prep_time', 1)]},
                {'keys': [('cook_time', 1)]},
                {'keys': [('created_at', 1)]},
                {'keys': [('is_public', 1)]},
            ],
            'meal_plans': [
                {'keys': [('user_id', 1)]},
                {'keys': [('user_id', 1), ('date', 1)]},
                {'keys': [('user_id', 1), ('meal_type', 1)]},
            ],
            'shopping_lists': [
                {'keys': [('user_id', 1)]},
                {'keys': [('user_id', 1), ('created_at', 1)]},
                {'keys': [('user_id', 1), ('is_completed', 1)]},
            ],
            'community_posts': [
                {'keys': [('user_id', 1)]},
                {'keys': [('post_type', 1)]},
                {'keys': [('created_at', 1)]},
                {'keys': [('is_active', 1)]},
                {'keys': [('tags', 1)]},
            ],
            'leftover_suggestions': [
                {'keys': [('user_id', 1)]},
                {'keys': [('user_id', 1), ('created_at', 1)]},
                {'keys': [('ingredients', 1)]},
            ],
            'receipt_scans': [
                {'keys': [('user_id', 1)]},
                {'keys': [('user_id', 1), ('created_at', 1)]},
                {'keys': [('store_name', 1)]},
            ]
        }
        
        for collection_name, collection_indexes in indexes.items():
            collection = self.db[collection_name]
            
            for index_spec in collection_indexes:
                keys = index_spec['keys']
                options = {k: v for k, v in index_spec.items() if k != 'keys'}
                
                if self.dry_run:
                    logger.info(f"DRY RUN: Would create index on {collection_name}: {keys}")
                else:
                    try:
                        await collection.create_index(keys, **options)
                        logger.info(f"Created index on {collection_name}: {keys}")
                    except Exception as e:
                        logger.warning(f"Failed to create index on {collection_name}: {e}")
    
    async def run_migrations(self):
        """Run database migrations"""
        logger.info("Running database migrations...")
        
        # Migration 1: Add created_at to existing documents
        await self._migration_add_timestamps()
        
        # Migration 2: Update user profiles schema
        await self._migration_update_profiles()
        
        # Migration 3: Add indexes for performance
        await self.create_indexes()
        
        logger.info("Database migrations completed")
    
    async def _migration_add_timestamps(self):
        """Add created_at and updated_at to documents missing them"""
        logger.info("Migration: Adding timestamps to existing documents")
        
        collections = ['users', 'profiles', 'pantry_items', 'recipes', 
                      'meal_plans', 'shopping_lists', 'community_posts']
        
        for collection_name in collections:
            collection = self.db[collection_name]
            
            # Find documents without created_at
            query = {'created_at': {'$exists': False}}
            count = await collection.count_documents(query)
            
            if count > 0:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would update {count} documents in {collection_name}")
                else:
                    update = {
                        '$set': {
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        }
                    }
                    result = await collection.update_many(query, update)
                    logger.info(f"Updated {result.modified_count} documents in {collection_name}")
    
    async def _migration_update_profiles(self):
        """Update user profiles with new schema fields"""
        logger.info("Migration: Updating user profiles schema")
        
        collection = self.db['profiles']
        
        # Add new fields to profiles that don't have them
        query = {'preferences': {'$exists': False}}
        count = await collection.count_documents(query)
        
        if count > 0:
            if self.dry_run:
                logger.info(f"DRY RUN: Would update {count} profile documents")
            else:
                update = {
                    '$set': {
                        'preferences': {
                            'notifications': True,
                            'theme': 'light',
                            'language': 'en'
                        },
                        'updated_at': datetime.utcnow()
                    }
                }
                result = await collection.update_many(query, update)
                logger.info(f"Updated {result.modified_count} profile documents")
    
    async def validate_migration(self):
        """Validate that migrations were applied correctly"""
        logger.info("Validating database migration...")
        
        # Check that all collections exist
        collections = await self.db.list_collection_names()
        required_collections = [
            'users', 'profiles', 'pantry_items', 'recipes',
            'meal_plans', 'shopping_lists', 'community_posts',
            'leftover_suggestions', 'receipt_scans'
        ]
        
        missing_collections = [col for col in required_collections if col not in collections]
        if missing_collections:
            logger.error(f"Missing collections: {missing_collections}")
            return False
        
        # Check indexes
        for collection_name in required_collections:
            collection = self.db[collection_name]
            indexes = await collection.list_indexes().to_list(length=None)
            index_count = len(indexes)
            logger.info(f"Collection {collection_name} has {index_count} indexes")
        
        logger.info("Database migration validation completed")
        return True

async def main():
    parser = argparse.ArgumentParser(description='EZ Eatin Database Migration')
    parser.add_argument('--environment', choices=['dev', 'staging', 'prod'], 
                       default='dev', help='Environment to migrate')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without executing')
    parser.add_argument('--mongodb-uri', help='MongoDB URI (overrides environment)')
    parser.add_argument('--database-name', help='Database name (overrides environment)')
    
    args = parser.parse_args()
    
    # Load environment configuration
    if args.mongodb_uri and args.database_name:
        mongodb_uri = args.mongodb_uri
        database_name = args.database_name
    else:
        env_file = f"config/environments/{args.environment}.env"
        if not os.path.exists(env_file):
            logger.error(f"Environment file not found: {env_file}")
            sys.exit(1)
        
        # Load environment variables
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        mongodb_uri = os.getenv('MONGODB_URI')
        database_name = f"ez_eatin_{args.environment}"
        
        if not mongodb_uri:
            logger.error("MONGODB_URI not found in environment configuration")
            sys.exit(1)
    
    # Run migration
    migrator = DatabaseMigrator(mongodb_uri, database_name, args.dry_run)
    
    try:
        await migrator.connect()
        await migrator.run_migrations()
        
        if not args.dry_run:
            await migrator.validate_migration()
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        await migrator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Health Check Script (`scripts/health-check.sh`)

```bash
#!/bin/bash
# EZ Eatin' Health Check Script
# Usage: ./scripts/health-check.sh [environment]

set -e

ENVIRONMENT="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment configuration
ENV_FILE="$PROJECT_ROOT/config/environments/$ENVIRONMENT.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

source "$ENV_FILE"

# Health check functions
check_backend() {
    echo "Checking backend health..."
    
    local url="$BACKEND_URL/healthz"
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url" || echo "HTTPSTATUS:000")
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [[ "$status_code" -eq 200 ]]; then
        echo -e "${GREEN}✓ Backend health check passed${NC}"
        echo "  Response: $body"
        return 0
    else
        echo -e "${RED}✗ Backend health check failed${NC}"
        echo "  Status: $status_code"
        echo "  Response: $body"
        return 1
    fi
}

check_frontend() {
    echo "Checking frontend health..."
    
    local url="$FRONTEND_URL"
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url" || echo "HTTPSTATUS:000")
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [[ "$status_code" -eq 200 ]]; then
        echo -e "${GREEN}✓ Frontend health check passed${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend health check failed${NC}"
        echo "  Status: $status_code"
        return 1
    fi
}

check_database() {
    echo "Checking database connectivity..."
    
    # Use Python to check MongoDB connection
    python3 << EOF
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_db():
    try:
        client = AsyncIOMotorClient("$MONGODB_URI")
        await client.admin.command('ping')
        print("✓ Database connection successful")
        client.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

result = asyncio.run(check_db())
sys.exit(0 if result