"""
Database configuration and connection management for MongoDB Atlas
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def create_indexes():
    """Create database indexes for optimal query performance"""
    try:
        # Get profiles collection
        profiles_collection = await get_collection("profiles")
        
        # Get existing indexes
        existing_indexes = await profiles_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Create unique index on user_id
        if "user_id_unique" not in existing_index_names:
            try:
                await profiles_collection.create_index(
                    [("user_id", 1)],
                    unique=True,
                    name="user_id_unique"
                )
                logger.info("Created unique index on profiles.user_id")
            except Exception as e:
                logger.error(f"Error creating unique index on profiles.user_id: {e}")
        else:
            logger.info("Unique index on profiles.user_id already exists")
        
        # Create compound index for family member operations
        if "user_id_family_member_id" not in existing_index_names:
            try:
                await profiles_collection.create_index(
                    [("user_id", 1), ("family_members.id", 1)],
                    name="user_id_family_member_id"
                )
                logger.info("Created compound index on profiles.user_id and family_members.id")
            except Exception as e:
                logger.error(f"Error creating compound index on profiles.user_id and family_members.id: {e}")
        else:
            logger.info("Compound index on profiles.user_id and family_members.id already exists")
            
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")


async def connect_to_mongo():
    """Create database connection"""
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
        # Create MongoDB client
        db.client = AsyncIOMotorClient(mongodb_uri)
        db.database = db.client[database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: {database_name}")
        
        # Create database indexes
        await create_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

# Database instance for use in other modules
database = db.database

# Collection names
COLLECTIONS = {
    "users": "users",
    "profiles": "profiles", 
    "pantry_items": "pantry_items",
    "recipes": "recipes",
    "meal_plans": "meal_plans",
    "receipts": "receipts",
    "community_posts": "community_posts",
    "shopping_lists": "shopping_lists"
}

async def get_collection(collection_name: str):
    """Get a specific collection"""
    database = await get_database()
    return database[COLLECTIONS[collection_name]]