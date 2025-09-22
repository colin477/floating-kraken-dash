"""
EZ Eatin' Backend API
FastAPI application for meal planning and recipe management
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import connect_to_mongo, close_mongo_connection
from app.models.responses import HealthResponse
from app.routers import auth, profile, pantry, recipes, meal_plans, shopping_lists, community, receipts, leftovers

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB during startup: {e}")
        print("Server will start without database connection. Database features will be unavailable.")
    yield
    # Shutdown
    await close_mongo_connection()

# Create FastAPI application
app = FastAPI(
    title="EZ Eatin' API",
    description="AI-driven meal planning and recipe management backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://localhost:5173",  # Vite development server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Add CORS origins from environment if specified
if cors_origins := os.getenv("CORS_ORIGINS"):
    origins.extend(cors_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/healthz", response_model=HealthResponse)
async def health_check():
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

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "EZ Eatin' API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)