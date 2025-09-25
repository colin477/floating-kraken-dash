"""
EZ Eatin' Backend API
FastAPI application for meal planning and recipe management
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import connect_to_mongo, close_mongo_connection
from app.models.responses import HealthResponse
from app.routers import auth, profile, pantry, recipes, meal_plans, shopping_lists, community, receipts, leftovers

# Import security and performance middleware
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    RequestSizeLimitMiddleware,
    limiter,
    rate_limit_handler,
    get_redis_client
)
from app.middleware.fixed_performance import (
    FixedCompressionMiddleware,
    FixedCacheMiddleware,
    PerformanceMonitoringMiddleware
)

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
        # Initialize Redis connection for rate limiting and caching
        await get_redis_client()
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB during startup: {e}")
        print("Server will start without database connection. Database features will be unavailable.")
    yield
    # Shutdown
    await close_mongo_connection()

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

# Add security and performance middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
app.add_middleware(PerformanceMonitoringMiddleware)
app.add_middleware(FixedCacheMiddleware, default_ttl=300)  # 5 minutes
app.add_middleware(FixedCompressionMiddleware, minimum_size=1024)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(CORSMiddleware, **cors_config)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

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