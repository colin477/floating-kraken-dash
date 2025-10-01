"""
Database configuration and connection management for MongoDB Atlas
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import structlog

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
        # For production, consider using a CA file instead of tlsAllowInvalidCertificates
        # See: https://motor.readthedocs.io/en/stable/api-asyncio/asyncio_motor_client.html#motor.motor_asyncio.AsyncIOMotorClient
        db.client = AsyncIOMotorClient(
            mongodb_uri,
            maxPoolSize=100,
            minPoolSize=10,
            tls=True,
            tlsAllowInvalidCertificates=os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "false").lower() == "true"
        )
        await db.client.admin.command('ping')
        db.database = db.client[database_name]
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