"""
Database configuration and connection management for MongoDB Atlas
Enhanced with DNS resolution resilience for Windows environments
"""

import os
import asyncio
import ssl
import random
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import structlog
from dotenv import load_dotenv
from app.middleware.performance import DatabasePoolConfig

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None
    _connection_healthy = False
    _last_health_check = 0
    _health_check_interval = 30  # seconds
    _use_resilient_connection = True  # Enable resilient connection by default

db = Database()

# Import resilient database functions
try:
    from app.database_resilience_fix import (
        resilient_db,
        connect_to_mongo_resilient,
        get_database_resilient,
        get_collection_resilient,
        close_mongo_connection_resilient,
        check_connection_health_resilient
    )
    logger.info("Resilient database module loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load resilient database module: {e}")
    db._use_resilient_connection = False

def _is_production_environment() -> bool:
    """Detect if running in production environment (Render deployment)"""
    # Check for Render-specific environment variables
    render_indicators = [
        os.getenv("RENDER"),
        os.getenv("RENDER_SERVICE_ID"),
        os.getenv("RENDER_SERVICE_NAME")
    ]
    
    # Check for explicit production environment setting
    env = os.getenv("ENVIRONMENT", "").lower()
    is_prod_env = env in ["production", "prod"]
    
    # Check if any Render indicators are present
    is_render = any(indicator for indicator in render_indicators)
    
    # Log detection result for debugging
    logger.info(
        "Production environment detection",
        environment=env,
        render_detected=is_render,
        is_production=is_prod_env or is_render
    )
    
    return is_prod_env or is_render

async def get_database():
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection with enhanced resilience for DNS resolution issues"""
    # Try resilient connection first if available
    if db._use_resilient_connection:
        try:
            logger.info("Using resilient MongoDB connection method")
            await connect_to_mongo_resilient()
            
            # Update legacy db object for backward compatibility
            db.client = resilient_db.client
            db.database = resilient_db.database
            db._connection_healthy = resilient_db._connection_healthy
            db._last_health_check = resilient_db._last_health_check
            
            logger.info("Resilient MongoDB connection established successfully")
            return
            
        except Exception as e:
            logger.warning(f"Resilient connection failed, falling back to legacy method: {e}")
            db._use_resilient_connection = False
    
    # Fallback to legacy connection method
    await _connect_to_mongo_legacy()

async def _connect_to_mongo_legacy():
    """Legacy MongoDB connection method (fallback)"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    # Detect production environment
    is_production = _is_production_environment()
    
    # Retry configuration with production-optimized defaults
    max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "4"))
    retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "3.0"))
    
    logger.info(
        f"Using legacy connection method for MongoDB at {mongodb_uri[:50]}...",
        is_production=is_production,
        max_retries=max_retries,
        retry_delay=retry_delay
    )
    
    # Production connection warmup delay for network stack initialization
    if is_production:
        logger.info("Production environment detected - applying connection warmup delay")
        await asyncio.sleep(2.0)  # 2-second warmup delay for production
    
    for attempt in range(max_retries + 1):
        try:
            # Get connection options from DatabasePoolConfig
            connection_options = DatabasePoolConfig.get_connection_options()
            
            # Apply production-specific timeout optimizations
            if is_production:
                # Increase timeouts for production resilience (60s instead of 45s)
                production_timeouts = {
                    'serverSelectionTimeoutMS': 60000,  # 60 seconds
                    'connectTimeoutMS': 60000,           # 60 seconds
                    'socketTimeoutMS': 60000             # 60 seconds
                }
                connection_options.update(production_timeouts)
                logger.info("Applied production timeout optimizations", **production_timeouts)
            
            # Create client with connection options (no duplicate parameters)
            db.client = AsyncIOMotorClient(mongodb_uri, **connection_options)
            
            # Test the connection with a ping (with production-optimized timeout)
            ping_timeout = connection_options.get('serverSelectionTimeoutMS', 30000) / 1000
            await asyncio.wait_for(
                db.client.admin.command('ping'),
                timeout=ping_timeout
            )
            
            db.database = db.client[database_name]
            
            # Log successful connection details
            try:
                server_info = await db.client.server_info()
                logger.info(
                    "Legacy MongoDB connection established successfully",
                    database=database_name,
                    mongodb_version=server_info.get('version', 'Unknown'),
                    attempt=attempt + 1
                )
                
                # Log TLS information if available
                if 'openssl' in server_info and 'running' in server_info['openssl']:
                    logger.info("TLS connection established", tls_version=server_info['openssl']['running'])
                    
            except Exception as info_error:
                # Don't fail connection if we can't get server info
                logger.warning(f"Could not retrieve server info: {info_error}")
            
            # Mark connection as healthy after successful connection
            db._connection_healthy = True
            db._last_health_check = time.time()
            return
            
        except Exception as e:
            error_msg = f"Legacy MongoDB connection error on attempt {attempt + 1}: {e}"
            logger.error(error_msg)
            
            if attempt < max_retries:
                # Add random jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.5) * retry_delay
                total_delay = retry_delay + jitter
                logger.warning(f"Retrying in {total_delay:.2f} seconds")
                await asyncio.sleep(total_delay)
                retry_delay *= 2
            else:
                logger.error(f"All legacy connection attempts failed after {max_retries + 1} attempts")
                raise

async def close_mongo_connection():
    """Close database connection with resilience support"""
    if db._use_resilient_connection:
        try:
            await close_mongo_connection_resilient()
        except Exception as e:
            logger.warning(f"Error closing resilient connection: {e}")
    
    if db.client:
        db.client.close()
        db.client = None
        db.database = None
        db._connection_healthy = False
        logger.info("Disconnected from MongoDB")

async def check_connection_health() -> bool:
    """Check if MongoDB connection is healthy with enhanced resilience"""
    # Use resilient health check if available
    if db._use_resilient_connection:
        try:
            return await check_connection_health_resilient()
        except Exception as e:
            logger.warning(f"Resilient health check failed, using legacy method: {e}")
            db._use_resilient_connection = False
    
    # Legacy health check
    current_time = time.time()
    
    # If we recently checked and connection was healthy, return cached result
    if (db._connection_healthy and
        current_time - db._last_health_check < db._health_check_interval):
        return True
    
    # Perform health check
    if db.client is None:
        db._connection_healthy = False
        return False
    
    try:
        # Quick ping with short timeout
        await asyncio.wait_for(
            db.client.admin.command('ping'),
            timeout=5.0  # 5 second timeout for health check
        )
        db._connection_healthy = True
        db._last_health_check = current_time
        logger.debug("MongoDB connection health check passed")
        return True
    except Exception as e:
        db._connection_healthy = False
        logger.warning(f"MongoDB connection health check failed: {e}")
        return False

async def get_collection(collection_name: str):
    """Get a specific collection with enhanced resilience"""
    # Use resilient collection getter if available
    if db._use_resilient_connection:
        try:
            return await get_collection_resilient(collection_name)
        except Exception as e:
            logger.warning(f"Resilient collection access failed, using legacy method: {e}")
            db._use_resilient_connection = False
    
    # Legacy collection access
    # Check connection health before returning collection
    if not await check_connection_health():
        logger.warning("MongoDB connection unhealthy, attempting reconnection...")
        await connect_to_mongo()
    
    if db.database is None:
        await connect_to_mongo()
    return db.database[collection_name]

async def get_connection_stats() -> dict:
    """Get MongoDB connection pool statistics for monitoring"""
    if db.client is None:
        return {"status": "disconnected", "pool_size": 0}
    
    try:
        # Get server status for connection info
        server_status = await db.client.admin.command("serverStatus")
        connections = server_status.get("connections", {})
        
        return {
            "status": "connected" if db._connection_healthy else "unhealthy",
            "current_connections": connections.get("current", 0),
            "available_connections": connections.get("available", 0),
            "total_created": connections.get("totalCreated", 0),
            "last_health_check": db._last_health_check,
            "health_check_interval": db._health_check_interval
        }
    except Exception as e:
        logger.warning(f"Failed to get connection stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "last_health_check": db._last_health_check
        }