"""
Database configuration and connection management for MongoDB Atlas
"""
# SSL/TLS verification trigger

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging
import structlog
from app.middleware.performance import DatabasePoolConfig

# Configure structured logging
logger = structlog.get_logger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def create_comprehensive_indexes():
    """Create comprehensive database indexes for optimal query performance"""
    try:
        # Users collection indexes
        await create_users_indexes()
        
        # Profiles collection indexes
        await create_profiles_indexes()
        
        # Pantry items collection indexes
        await create_pantry_indexes()
        
        # Recipes collection indexes
        await create_recipes_indexes()
        
        # Meal plans collection indexes
        await create_meal_plans_indexes()
        
        # Shopping lists collection indexes
        await create_shopping_lists_indexes()
        
        # Community collections indexes
        await create_community_indexes()
        
        # Receipts collection indexes
        await create_receipts_indexes()
        
        logger.info("All database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating comprehensive database indexes: {e}")

async def create_users_indexes():
    """Create indexes for users collection"""
    try:
        users_collection = await get_collection("users")
        existing_indexes = await users_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Unique index on email (use existing email_1 index name)
        if "email_1" not in existing_index_names:
            await users_collection.create_index(
                [("email", 1)],
                unique=True,
                name="email_1"
            )
            logger.info("Created unique index on users.email")
        
        # Index on created_at for sorting
        if "created_at_desc" not in existing_index_names:
            await users_collection.create_index(
                [("created_at", -1)],
                name="created_at_desc"
            )
            logger.info("Created index on users.created_at")
            
        # Index on is_active for filtering
        if "is_active_index" not in existing_index_names:
            await users_collection.create_index(
                [("is_active", 1)],
                name="is_active_index"
            )
            logger.info("Created index on users.is_active")
            
    except Exception as e:
        logger.error(f"Error creating users indexes: {e}")

async def create_profiles_indexes():
    """Create indexes for profiles collection"""
    try:
        profiles_collection = await get_collection("profiles")
        existing_indexes = await profiles_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Unique index on user_id
        if "user_id_unique" not in existing_index_names:
            await profiles_collection.create_index(
                [("user_id", 1)],
                unique=True,
                name="user_id_unique"
            )
            logger.info("Created unique index on profiles.user_id")
        
        # Compound index for family member operations
        if "user_id_family_member_id" not in existing_index_names:
            await profiles_collection.create_index(
                [("user_id", 1), ("family_members.id", 1)],
                name="user_id_family_member_id"
            )
            logger.info("Created compound index on profiles.user_id and family_members.id")
            
    except Exception as e:
        logger.error(f"Error creating profiles indexes: {e}")

async def create_pantry_indexes():
    """Create indexes for pantry_items collection"""
    try:
        pantry_collection = await get_collection("pantry_items")
        existing_indexes = await pantry_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Compound index on user_id and name for queries
        if "user_id_name" not in existing_index_names:
            await pantry_collection.create_index(
                [("user_id", 1), ("name", 1)],
                name="user_id_name"
            )
            logger.info("Created compound index on pantry_items.user_id and name")
        
        # Index on expiry_date for expiration queries
        if "expiry_date_index" not in existing_index_names:
            await pantry_collection.create_index(
                [("expiry_date", 1)],
                name="expiry_date_index"
            )
            logger.info("Created index on pantry_items.expiry_date")
        
        # Compound index for category filtering (use existing user_id_category_index name)
        if "user_id_category_index" not in existing_index_names:
            await pantry_collection.create_index(
                [("user_id", 1), ("category", 1)],
                name="user_id_category_index"
            )
            logger.info("Created compound index on pantry_items.user_id and category")
            
    except Exception as e:
        logger.error(f"Error creating pantry indexes: {e}")

async def create_recipes_indexes():
    """Create indexes for recipes collection"""
    try:
        recipes_collection = await get_collection("recipes")
        existing_indexes = await recipes_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Index on user_id for user recipes
        if "user_id_index" not in existing_index_names:
            await recipes_collection.create_index(
                [("user_id", 1)],
                name="user_id_index"
            )
            logger.info("Created index on recipes.user_id")
        
        # Text index for recipe search (use existing text_search_index name and weights)
        if "text_search_index" not in existing_index_names:
            await recipes_collection.create_index(
                [("title", "text"), ("description", "text"), ("tags", "text")],
                name="text_search_index"
            )
            logger.info("Created text search index on recipes")
        
        # Index on created_at for sorting
        if "created_at_desc" not in existing_index_names:
            await recipes_collection.create_index(
                [("created_at", -1)],
                name="created_at_desc"
            )
            logger.info("Created index on recipes.created_at")
            
    except Exception as e:
        logger.error(f"Error creating recipes indexes: {e}")

async def create_meal_plans_indexes():
    """Create indexes for meal_plans collection"""
    try:
        meal_plans_collection = await get_collection("meal_plans")
        existing_indexes = await meal_plans_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Compound index on user_id and date
        if "user_id_date" not in existing_index_names:
            await meal_plans_collection.create_index(
                [("user_id", 1), ("date", 1)],
                name="user_id_date"
            )
            logger.info("Created compound index on meal_plans.user_id and date")
        
        # Index on date range queries
        if "date_range" not in existing_index_names:
            await meal_plans_collection.create_index(
                [("date", 1)],
                name="date_range"
            )
            logger.info("Created index on meal_plans.date")
            
    except Exception as e:
        logger.error(f"Error creating meal plans indexes: {e}")

async def create_shopping_lists_indexes():
    """Create indexes for shopping_lists collection"""
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        existing_indexes = await shopping_lists_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Index on user_id (use existing user_id_1 name)
        if "user_id_1" not in existing_index_names:
            await shopping_lists_collection.create_index(
                [("user_id", 1)],
                name="user_id_1"
            )
            logger.info("Created index on shopping_lists.user_id")
        
        # Compound index on user_id and status (use existing user_id_1_status_1 name)
        if "user_id_1_status_1" not in existing_index_names:
            await shopping_lists_collection.create_index(
                [("user_id", 1), ("status", 1)],
                name="user_id_1_status_1"
            )
            logger.info("Created compound index on shopping_lists.user_id and status")
            
    except Exception as e:
        logger.error(f"Error creating shopping lists indexes: {e}")

async def create_community_indexes():
    """Create indexes for community collections"""
    try:
        # Community posts indexes
        posts_collection = await get_collection("community_posts")
        existing_indexes = await posts_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        if "created_at_-1" not in existing_index_names:
            await posts_collection.create_index(
                [("created_at", -1)],
                name="created_at_-1"
            )
            logger.info("Created index on community_posts.created_at")
        
        if "user_id_1" not in existing_index_names:
            await posts_collection.create_index(
                [("user_id", 1)],
                name="user_id_1"
            )
            logger.info("Created index on community_posts.user_id")
        
        # Community comments indexes
        comments_collection = await get_collection("community_comments")
        existing_indexes = await comments_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        if "post_id_1" not in existing_index_names:
            await comments_collection.create_index(
                [("post_id", 1)],
                name="post_id_1"
            )
            logger.info("Created index on community_comments.post_id")
        
        # Community likes indexes
        likes_collection = await get_collection("community_likes")
        existing_indexes = await likes_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        if "post_id_user_id" not in existing_index_names:
            await likes_collection.create_index(
                [("post_id", 1), ("user_id", 1)],
                unique=True,
                name="post_id_user_id"
            )
            logger.info("Created unique compound index on community_likes.post_id and user_id")
            
    except Exception as e:
        logger.error(f"Error creating community indexes: {e}")

async def create_receipts_indexes():
    """Create indexes for receipts collection"""
    try:
        receipts_collection = await get_collection("receipts")
        existing_indexes = await receipts_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Index on user_id
        if "user_id_index" not in existing_index_names:
            await receipts_collection.create_index(
                [("user_id", 1)],
                name="user_id_index"
            )
            logger.info("Created index on receipts.user_id")
        
        # Index on created_at for sorting
        if "created_at_desc" not in existing_index_names:
            await receipts_collection.create_index(
                [("created_at", -1)],
                name="created_at_desc"
            )
            logger.info("Created index on receipts.created_at")
            
    except Exception as e:
        logger.error(f"Error creating receipts indexes: {e}")


async def connect_to_mongo():
    """Create database connection with production-grade connection pooling and SSL/TLS support"""
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
        # Enhanced SSL Environment Variable Logging
        tls_enabled = os.getenv("MONGODB_TLS_ENABLED", "false")
        tls_allow_invalid = os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "false")
        server_timeout = os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "30000")
        connect_timeout = os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "30000")
        socket_timeout = os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "30000")
        
        logger.info("=== MongoDB SSL/TLS Environment Variables ===")
        logger.info(f"MONGODB_TLS_ENABLED: {tls_enabled}")
        logger.info(f"MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: {tls_allow_invalid}")
        logger.info(f"MONGODB_SERVER_SELECTION_TIMEOUT_MS: {server_timeout}")
        logger.info(f"MONGODB_CONNECT_TIMEOUT_MS: {connect_timeout}")
        logger.info(f"MONGODB_SOCKET_TIMEOUT_MS: {socket_timeout}")
        logger.info("===============================================")
        
        # Get optimized connection options for production
        connection_options = DatabasePoolConfig.get_connection_options()
        logger.info(f"Base connection options: {connection_options}")
        
        # Strengthen SSL/TLS configuration for OpenSSL 3.0.16 compatibility
        if tls_enabled.lower() == "true":
            # Ensure tlsAllowInvalidCertificates is definitively set to true
            tls_allow_invalid_bool = tls_allow_invalid.lower() == "true"
            
            tls_options = {
                "tls": True,
                "tlsAllowInvalidCertificates": tls_allow_invalid_bool,
                "serverSelectionTimeoutMS": int(server_timeout),
                "connectTimeoutMS": int(connect_timeout),
                "socketTimeoutMS": int(socket_timeout),
                "retryWrites": True,
                "retryReads": True,
                "maxIdleTimeMS": 45000,  # Close connections after 45 seconds of inactivity
                "heartbeatFrequencyMS": 10000,  # Send heartbeat every 10 seconds
            }
            
            connection_options.update(tls_options)
            
            logger.info("=== TLS Configuration Applied ===")
            logger.info(f"tls: {tls_options['tls']}")
            logger.info(f"tlsAllowInvalidCertificates: {tls_options['tlsAllowInvalidCertificates']}")
            logger.info(f"serverSelectionTimeoutMS: {tls_options['serverSelectionTimeoutMS']}")
            logger.info(f"connectTimeoutMS: {tls_options['connectTimeoutMS']}")
            logger.info(f"socketTimeoutMS: {tls_options['socketTimeoutMS']}")
            logger.info(f"maxIdleTimeMS: {tls_options['maxIdleTimeMS']}")
            logger.info(f"heartbeatFrequencyMS: {tls_options['heartbeatFrequencyMS']}")
            logger.info("=================================")
        
        # Log final connection options for debugging
        logger.info(f"Final connection options: {connection_options}")
        
        # Create MongoDB client with connection pooling
        logger.info("Creating AsyncIOMotorClient with enhanced SSL configuration...")
        db.client = AsyncIOMotorClient(mongodb_uri, **connection_options)
        db.database = db.client[database_name]
        
        # Test the connection with extended timeout for SSL handshake
        logger.info("Testing MongoDB connection with ping command...")
        await db.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: {database_name}")
        logger.info(f"Connection pool configured with max size: {connection_options['maxPoolSize']}")
        
        if tls_enabled.lower() == "true":
            logger.info("SSL/TLS connection established successfully with enhanced configuration")
        
        # Create comprehensive database indexes
        await create_comprehensive_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        if tls_enabled.lower() == "true":
            logger.error("SSL/TLS connection failure detected")
            logger.error("This may be due to OpenSSL 3.0.16 certificate validation strictness")
            logger.error("Check certificate configuration and network connectivity")
            logger.error(f"TLS settings - Enabled: {tls_enabled}, Allow Invalid: {tls_allow_invalid}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        if tls_enabled.lower() == "true":
            logger.error("SSL/TLS related error - check OpenSSL compatibility and certificate configuration")
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
    "community_comments": "community_comments",
    "community_likes": "community_likes",
    "shopping_lists": "shopping_lists"
}

async def get_collection(collection_name: str):
    """Get a specific collection"""
    database = await get_database()
    return database[COLLECTIONS[collection_name]]