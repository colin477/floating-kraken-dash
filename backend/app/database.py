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
    """Create database connection with retry logic"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    # Retry configuration
    max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "3"))
    retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "2.0"))
    
    logger.info(f"Attempting to connect to MongoDB at {mongodb_uri}")
    
    for attempt in range(max_retries + 1):
        try:
            # Use the existing documented configuration approach
            connection_options = DatabasePoolConfig.get_connection_options()
            db.client = AsyncIOMotorClient(mongodb_uri, **connection_options)
            
            # Test the connection with a ping
            await db.client.admin.command('ping')
            db.database = db.client[database_name]
            
            # Log the negotiated TLS version
            server_info = await db.client.server_info()
            if 'openssl' in server_info and 'running' in server_info['openssl']:
                logger.info("Negotiated TLS version", tls_version=server_info['openssl']['running'])
            
            logger.info(f"Successfully connected to MongoDB database: {database_name}")
            return
            
        except ConnectionFailure as e:
            if attempt < max_retries:
                logger.warning(
                    f"MongoDB connection attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
                # Exponential backoff: double the delay for next attempt
                retry_delay *= 2
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries + 1} attempts: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB connection: {e}")
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