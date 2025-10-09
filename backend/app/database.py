"""
Database configuration and connection management for MongoDB Atlas
"""

import os
import asyncio
import ssl
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

db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection with retry logic and proper SSL/TLS handling"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    # Retry configuration
    max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "3"))
    retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "2.0"))
    
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
            
            return
            
        except asyncio.TimeoutError as e:
            error_msg = f"MongoDB connection timeout on attempt {attempt + 1}"
            if attempt < max_retries:
                logger.warning(f"{error_msg}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
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
                logger.warning(f"{error_msg} Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
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
                logger.warning(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def get_collection(collection_name: str):
    """Get a specific collection"""
    if db.database is None:
        await connect_to_mongo()
    return db.database[collection_name]