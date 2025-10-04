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
    """Create database connection"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    logger.info(f"Attempting to connect to MongoDB at {mongodb_uri}")
    try:
        # Use the existing documented configuration approach
        connection_options = DatabasePoolConfig.get_connection_options()
        db.client = AsyncIOMotorClient(mongodb_uri, **connection_options)
        await db.client.admin.command('ping')
        db.database = db.client[database_name]
        
        # Log the negotiated TLS version
        server_info = await db.client.server_info()
        if 'openssl' in server_info and 'running' in server_info['openssl']:
            logger.info("Negotiated TLS version", tls_version=server_info['openssl']['running'])
        
        logger.info(f"Successfully connected to MongoDB database: {database_name}")
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
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