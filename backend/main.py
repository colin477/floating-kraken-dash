"""
EZ Eatin' Backend API
FastAPI application for meal planning and recipe management
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time
from dotenv import load_dotenv

from app.database import connect_to_mongo, close_mongo_connection
from app.crud.users import create_user_indexes
from app.models.responses import HealthResponse
from app.routers import auth, profile, pantry, recipes, meal_plans, shopping_lists, community, receipts, leftovers, health, nutrition

# Import security and performance middleware
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    RequestSizeLimitMiddleware,
    limiter,
    rate_limit_handler,
    get_redis_client as get_security_redis_client
)
from app.middleware.fixed_performance import (
    FixedCompressionMiddleware,
    FixedCacheMiddleware,
    PerformanceMonitoringMiddleware
)
from app.utils.redis_client import get_redis_client

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    try:
        await connect_to_mongo()
        await create_user_indexes()
        # Initialize Redis connection for rate limiting and caching
        await get_redis_client()
    except ConnectionError as e:
        print(f"Warning: Could not connect to MongoDB during startup: {e}")
        print("Server will start without database connection. Database features will be unavailable.")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")
    yield
    # Shutdown
    await close_mongo_connection()
    # Close Redis connection
    try:
        from app.utils.redis_client import close_redis_client
        await close_redis_client()
    except Exception as e:
        print(f"Warning: Error closing Redis connection: {e}")

# Create FastAPI application with production settings
app = FastAPI(
    title="EZ Eatin' API",
    description="AI-driven meal planning and recipe management backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT", "development") == "development" else None
)

# Configure CORS for production
origins = [
    "http://localhost:3000",  # React development server
    "http://localhost:3002",  # Frontend development server (current)
    "http://localhost:5173",  # Vite development server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3002",  # Frontend development server (current)
    "http://127.0.0.1:5173",
    "https://ez-eatin-demo-backend-v1.onrender.com",  # Production backend URL
    "https://ez-eatin-frontend-demo-v1.onrender.com", # Production frontend URL
]

# Add production CORS origins from environment
if cors_origins := os.getenv("CORS_ORIGINS"):
    origins.extend(cors_origins.split(","))

# Production CORS configuration
cors_config = {
    "allow_origins": origins,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    "expose_headers": ["X-Total-Count", "X-Cache", "Server-Timing"],
    "max_age": 86400  # 24 hours
}

# Add CORS middleware FIRST (critical for preflight requests)
app.add_middleware(CORSMiddleware, **cors_config)

# Add security and performance middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
app.add_middleware(PerformanceMonitoringMiddleware)
app.add_middleware(FixedCacheMiddleware, default_ttl=300)  # 5 minutes
app.add_middleware(FixedCompressionMiddleware, minimum_size=1024)
app.add_middleware(SlowAPIMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add TimeoutError exception handler for rate limiting middleware
@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service timeout",
            "message": "The request timed out. Please try again.",
            "status_code": 503
        }
    )

# Health check endpoint with rate limiting
@app.get("/healthz", response_model=HealthResponse)
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint with database connectivity status"""
    try:
        from app.database import db
        if db.database is not None:
            # Test database connection
            await db.database.command("ping")
            return HealthResponse(
                status="healthy",
                message="API is running and database is connected",
                database_connected=True
            )
        else:
            return HealthResponse(
                status="partial",
                message="API is running but database is not connected",
                database_connected=False
            )
    except Exception as e:
        return HealthResponse(
            status="partial",
            message=f"API is running but database connection failed: {str(e)}",
            database_connected=False
        )

# Database-specific health check endpoint with rate limiting
@app.get("/healthz/db")
@limiter.limit("50/minute")
async def database_health_check(request: Request):
    """Database-specific health check endpoint for monitoring MongoDB connection status"""
    try:
        from app.database import db, check_connection_health, get_connection_stats
        
        # Check connection health
        is_healthy = await check_connection_health()
        
        # Get connection statistics
        connection_stats = await get_connection_stats()
        
        if is_healthy and db.database is not None:
            # Test database connection with a simple operation
            await db.database.command("ping")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "message": "Database connection is healthy",
                    "database_connected": True,
                    "connection_stats": connection_stats,
                    "timestamp": time.time()
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Database connection is not healthy",
                    "database_connected": False,
                    "connection_stats": connection_stats,
                    "timestamp": time.time()
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": f"Database health check failed: {str(e)}",
                "database_connected": False,
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(pantry.router, prefix="/api/v1/pantry", tags=["pantry"])
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["receipts"])
app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
app.include_router(meal_plans.router, prefix="/api/v1/meal-plans", tags=["meal-plans"])
app.include_router(shopping_lists.router, prefix="/api/v1/shopping-lists", tags=["shopping-lists"])
app.include_router(community.router, prefix="/api/v1/community", tags=["community"])
app.include_router(leftovers.router, prefix="/api/v1/leftovers", tags=["leftovers"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(nutrition.router, prefix="/api/v1/nutrition", tags=["nutrition"])

# Root endpoint with rate limiting
@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "EZ Eatin' API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)