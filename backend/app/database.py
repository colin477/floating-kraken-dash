"""
Database configuration and connection management for MongoDB Atlas
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

db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection with retry logic and proper SSL/TLS handling"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    # Retry configuration with optimized defaults
    max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "4"))
    retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "3.0"))
    
    logger.info(f"Attempting to connect to MongoDB at {mongodb_uri[:50]}...")
    
    for attempt in range(max_retries + 1):
        try:
            # Get connection options from DatabasePoolConfig
            connection_options = DatabasePoolConfig.get_connection_options()
            
            # Create client with connection options (no duplicate parameters)
            db.client = AsyncIOMotorClient(mongodb_uri, **connection_options)
            
            # Test the connection with a ping (with timeout)
            await asyncio.wait_for(
                db.client.admin.command('ping'),
                timeout=connection_options.get('serverSelectionTimeoutMS', 30000) / 1000
            )
            
            db.database = db.client[database_name]
            
            # Log successful connection details
            try:
                server_info = await db.client.server_info()
                logger.info(
                    "MongoDB connection established successfully",
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
            
        except asyncio.TimeoutError as e:
            error_msg = f"MongoDB connection timeout on attempt {attempt + 1}"
            if attempt < max_retries:
                # Add random jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.5) * retry_delay
                total_delay = retry_delay + jitter
                logger.warning(f"{error_msg}. Retrying in {total_delay:.2f} seconds (base: {retry_delay}s + jitter: {jitter:.2f}s)...")
                await asyncio.sleep(total_delay)
                retry_delay *= 2
            else:
                logger.error(f"{error_msg}. Max retries exceeded.")
                raise ConnectionFailure(f"Connection timeout after {max_retries + 1} attempts: {e}")
                
        except ConnectionFailure as e:
            error_msg = f"MongoDB connection failed on attempt {attempt + 1}: {e}"
            
            # Check for specific SSL/TLS errors
            if any(ssl_indicator in str(e).lower() for ssl_indicator in ['ssl', 'tls', 'certificate', 'handshake']):
                logger.error(f"SSL/TLS connection error: {e}")
                if attempt < max_retries:
                    logger.warning("SSL/TLS error detected. Retrying with current configuration...")
                else:
                    logger.error("SSL/TLS connection failed after all retries. Check SSL configuration and network connectivity.")
            
            if attempt < max_retries:
                # Add random jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.5) * retry_delay
                total_delay = retry_delay + jitter
                logger.warning(f"{error_msg} Retrying in {total_delay:.2f} seconds (base: {retry_delay}s + jitter: {jitter:.2f}s)...")
                await asyncio.sleep(total_delay)
                retry_delay *= 2
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries + 1} attempts: {e}")
                raise
                
        except Exception as e:
            error_msg = f"Unexpected MongoDB connection error on attempt {attempt + 1}: {e}"
            logger.error(error_msg)
            
            # Check for DNS resolution errors
            if 'getaddrinfo failed' in str(e) or 'Name or service not known' in str(e):
                logger.error("DNS resolution failed. Check network connectivity and MongoDB URI hostname.")
                if attempt < max_retries:
                    logger.warning("DNS error detected. Retrying...")
                else:
                    logger.error("DNS resolution failed after all retries. Check network configuration.")
            
            if attempt < max_retries:
                # Add random jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.5) * retry_delay
                total_delay = retry_delay + jitter
                logger.warning(f"Retrying in {total_delay:.2f} seconds (base: {retry_delay}s + jitter: {jitter:.2f}s)...")
                await asyncio.sleep(total_delay)
                retry_delay *= 2
            else:
                raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def check_connection_health() -> bool:
    """Check if MongoDB connection is healthy with periodic health checks"""
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
    """Get a specific collection with connection health check"""
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