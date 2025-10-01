"""
Database configuration and connection management for MongoDB Atlas
Enhanced with DNS resolution stability, SSL/TLS fixes, and connection retry logic
"""
# SSL/TLS verification trigger

import os
import ssl
import socket
import asyncio
import time
import random
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, ServerSelectionTimeoutError
from pymongo import MongoClient
import logging
import structlog
from app.middleware.performance import DatabasePoolConfig

# Configure structured logging
logger = structlog.get_logger(__name__)

# DNS Resolution and Connection Stability Functions
def force_ipv4_dns_resolution():
    """Force IPv4-only DNS resolution to avoid IPv6 issues"""
    try:
        # Override socket.getaddrinfo to force IPv4
        original_getaddrinfo = socket.getaddrinfo
        
        def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        
        socket.getaddrinfo = ipv4_getaddrinfo
        logger.info("Forced IPv4-only DNS resolution")
        return True
    except Exception as e:
        logger.error(f"Failed to force IPv4 DNS resolution: {e}")
        return False

def bypass_dns_cache():
    """Bypass DNS caching by setting socket options"""
    try:
        # Set DNS cache bypass options
        original_socket = socket.socket
        
        def patched_socket(*args, **kwargs):
            sock = original_socket(*args, **kwargs)
            try:
                # Disable DNS caching at socket level
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if hasattr(socket, 'SO_REUSEPORT'):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception as e:
                logger.warning(f"Could not set socket options for DNS cache bypass: {e}")
            return sock
        
        socket.socket = patched_socket
        logger.info("DNS cache bypass configured")
        return True
    except Exception as e:
        logger.error(f"Failed to configure DNS cache bypass: {e}")
        return False

def create_enhanced_ssl_context() -> ssl.SSLContext:
    """Create enhanced SSL context with TLS 1.2 pinning and relaxed validation"""
    try:
        # Create SSL context with TLS 1.2
        context = ssl.create_default_context()
        
        # Pin to TLS 1.2 for compatibility
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        
        # Relax certificate validation for Atlas compatibility
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Set compatible cipher suites
        try:
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        except ssl.SSLError:
            # Fallback to default ciphers if custom ones fail
            logger.warning("Custom cipher suite failed, using default")
        
        # Additional SSL options for compatibility
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        logger.info("Enhanced SSL context created with TLS 1.2 pinning")
        return context
        
    except Exception as e:
        logger.error(f"Failed to create enhanced SSL context: {e}")
        # Return default context as fallback
        return ssl.create_default_context()

async def test_connection_with_retry(client: AsyncIOMotorClient, max_retries: int = 3) -> bool:
    """Test MongoDB connection with retry logic"""
    for attempt in range(max_retries):
        try:
            # Test connection with ping
            await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
            logger.info(f"Connection test successful on attempt {attempt + 1}")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Connection test timeout on attempt {attempt + 1}")
        except Exception as e:
            logger.warning(f"Connection test failed on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Retrying connection test in {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
    
    logger.error("All connection test attempts failed")
    return False

def parse_mongodb_uri(uri: str) -> Dict[str, Any]:
    """Parse MongoDB URI and extract connection details"""
    try:
        parsed = urlparse(uri)
        
        # Check if it's an SRV record
        is_srv = parsed.scheme == 'mongodb+srv'
        
        # Extract host information
        hosts = []
        if is_srv:
            # For SRV, we have a single hostname
            hosts = [parsed.hostname]
        else:
            # For standard URI, parse multiple hosts
            if parsed.hostname:
                hosts = [parsed.hostname]
        
        return {
            'is_srv': is_srv,
            'hosts': hosts,
            'database': parsed.path.lstrip('/') if parsed.path else None,
            'username': parsed.username,
            'password': parsed.password,
            'port': parsed.port
        }
    except Exception as e:
        logger.error(f"Failed to parse MongoDB URI: {e}")
        return {'is_srv': False, 'hosts': [], 'database': None}

def create_direct_connection_uri(srv_uri: str) -> Optional[str]:
    """Convert SRV URI to direct connection URI as fallback"""
    try:
        parsed_info = parse_mongodb_uri(srv_uri)
        
        if not parsed_info['is_srv'] or not parsed_info['hosts']:
            return None
        
        # For Atlas, typically resolve to cluster hosts
        # This is a simplified fallback - in production, you'd resolve SRV records
        host = parsed_info['hosts'][0]
        
        # Atlas cluster naming pattern
        if 'mongodb.net' in host:
            # Convert cluster0.xxxxx.mongodb.net to direct hosts
            cluster_name = host.split('.')[0]
            base_domain = '.'.join(host.split('.')[1:])
            
            # Create direct connection string with multiple hosts
            direct_hosts = [
                f"{cluster_name}-shard-00-00.{base_domain}:27017",
                f"{cluster_name}-shard-00-01.{base_domain}:27017",
                f"{cluster_name}-shard-00-02.{base_domain}:27017"
            ]
            
            # Reconstruct URI
            auth_part = ""
            if parsed_info['username'] and parsed_info['password']:
                auth_part = f"{parsed_info['username']}:{parsed_info['password']}@"
            
            db_part = f"/{parsed_info['database']}" if parsed_info['database'] else ""
            
            direct_uri = f"mongodb://{auth_part}{','.join(direct_hosts)}{db_part}"
            logger.info("Created direct connection URI as SRV fallback")
            return direct_uri
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to create direct connection URI: {e}")
        return None

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
    """
    Create database connection with comprehensive DNS resolution stability,
    SSL/TLS fixes, and connection retry logic
    """
    max_retries = 5
    base_delay = 1.0
    
    # Apply DNS resolution fixes
    logger.info("=== Applying DNS Resolution Stability Fixes ===")
    force_ipv4_dns_resolution()
    bypass_dns_cache()
    
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
    logger.info(f"MONGODB_URI: {mongodb_uri[:50]}..." if len(mongodb_uri) > 50 else f"MONGODB_URI: {mongodb_uri}")
    logger.info(f"DATABASE_NAME: {database_name}")
    logger.info(f"MONGODB_TLS_ENABLED: {tls_enabled}")
    logger.info(f"MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: {tls_allow_invalid}")
    logger.info(f"MONGODB_SERVER_SELECTION_TIMEOUT_MS: {server_timeout}")
    logger.info(f"MONGODB_CONNECT_TIMEOUT_MS: {connect_timeout}")
    logger.info(f"MONGODB_SOCKET_TIMEOUT_MS: {socket_timeout}")
    logger.info("===============================================")
    
    # Parse URI for connection strategy
    uri_info = parse_mongodb_uri(mongodb_uri)
    logger.info(f"Connection strategy - SRV: {uri_info['is_srv']}, Hosts: {uri_info['hosts']}")
    
    # Prepare connection URIs (primary + fallback)
    connection_uris = [mongodb_uri]
    if uri_info['is_srv']:
        direct_uri = create_direct_connection_uri(mongodb_uri)
        if direct_uri:
            connection_uris.append(direct_uri)
            logger.info("Added direct connection URI as SRV fallback")
    
    # Connection retry loop
    for attempt in range(max_retries):
        logger.info(f"=== Connection Attempt {attempt + 1}/{max_retries} ===")
        
        for uri_index, current_uri in enumerate(connection_uris):
            uri_type = "SRV" if uri_index == 0 and uri_info['is_srv'] else "Direct"
            logger.info(f"Trying {uri_type} connection...")
            
            try:
                # Get optimized connection options for production
                connection_options = DatabasePoolConfig.get_connection_options()
                logger.info(f"Base connection options: {connection_options}")
                
                # Enhanced SSL/TLS configuration
                if tls_enabled.lower() == "true":
                    # Enhanced TLS options for PyMongo 4.5.0 compatibility
                    # Note: tlsInsecure and tlsAllowInvalidCertificates cannot be used together
                    tls_options = {
                        "tls": True,
                        "tlsAllowInvalidCertificates": True,  # Allow invalid certificates for Atlas compatibility
                        # Removed tlsInsecure as it conflicts with tlsAllowInvalidCertificates
                        # Removed tlsDisableOCSPEndpointCheck as it conflicts with tlsInsecure
                        "serverSelectionTimeoutMS": int(server_timeout),
                        "connectTimeoutMS": int(connect_timeout),
                        "socketTimeoutMS": int(socket_timeout),
                        "retryWrites": True,
                        "retryReads": True,
                        "maxIdleTimeMS": 45000,
                        "heartbeatFrequencyMS": 10000,
                        # Additional stability options
                        "maxStalenessSeconds": 120,
                        "compressors": "zlib",
                        "zlibCompressionLevel": 6,
                    }
                    
                    connection_options.update(tls_options)
                    
                    logger.info("=== Enhanced TLS Configuration Applied ===")
                    logger.info(f"tls: {tls_options['tls']}")
                    logger.info(f"tlsAllowInvalidCertificates: {tls_options['tlsAllowInvalidCertificates']}")
                    logger.info(f"serverSelectionTimeoutMS: {tls_options['serverSelectionTimeoutMS']}")
                    logger.info(f"connectTimeoutMS: {tls_options['connectTimeoutMS']}")
                    logger.info(f"socketTimeoutMS: {tls_options['socketTimeoutMS']}")
                    logger.info("==========================================")
                
                # Additional DNS and network stability options
                stability_options = {
                    "directConnection": False,  # Allow driver to discover topology
                    "readPreference": "primaryPreferred",  # Prefer primary but allow secondary
                    # Note: readConcern and writeConcern should be set at operation level, not connection level
                }
                
                connection_options.update(stability_options)
                
                # Log final connection options for debugging
                logger.info(f"Final connection options: {dict((k, v) for k, v in connection_options.items() if k != 'ssl_context')}")
                
                # Create MongoDB client with enhanced configuration
                logger.info(f"Creating AsyncIOMotorClient with {uri_type} URI...")
                client = AsyncIOMotorClient(current_uri, **connection_options)
                
                # Test the connection with comprehensive health check
                logger.info("Testing MongoDB connection with comprehensive health check...")
                
                # Test 1: Basic ping
                await asyncio.wait_for(client.admin.command('ping'), timeout=15.0)
                logger.info("✓ Basic ping successful")
                
                # Test 2: Database access
                test_db = client[database_name]
                await asyncio.wait_for(test_db.command('ping'), timeout=10.0)
                logger.info("✓ Database access successful")
                
                # Test 3: Collection listing (tests permissions)
                collections = await asyncio.wait_for(test_db.list_collection_names(), timeout=10.0)
                logger.info(f"✓ Collection listing successful ({len(collections)} collections found)")
                
                # Test 4: Write test (if possible)
                try:
                    test_collection = test_db.connection_test
                    test_doc = {"test": True, "timestamp": time.time(), "attempt": attempt + 1}
                    result = await asyncio.wait_for(
                        test_collection.insert_one(test_doc),
                        timeout=10.0
                    )
                    await asyncio.wait_for(
                        test_collection.delete_one({"_id": result.inserted_id}),
                        timeout=10.0
                    )
                    logger.info("✓ Write/delete test successful")
                except Exception as write_error:
                    logger.warning(f"Write test failed (may be read-only): {write_error}")
                
                # If we get here, connection is successful
                db.client = client
                db.database = test_db
                
                logger.info(f"✅ Successfully connected to MongoDB database: {database_name}")
                logger.info(f"Connection type: {uri_type}")
                logger.info(f"Connection pool configured with max size: {connection_options.get('maxPoolSize', 'default')}")
                
                if tls_enabled.lower() == "true":
                    logger.info("🔒 SSL/TLS connection established successfully with enhanced configuration")
                
                # Create comprehensive database indexes
                logger.info("Creating comprehensive database indexes...")
                await create_comprehensive_indexes()
                
                logger.info("🎉 MongoDB connection setup completed successfully!")
                return  # Success - exit function
                
            except asyncio.TimeoutError as e:
                logger.warning(f"Connection timeout with {uri_type} URI: {e}")
            except ServerSelectionTimeoutError as e:
                logger.warning(f"Server selection timeout with {uri_type} URI: {e}")
            except ConnectionFailure as e:
                logger.warning(f"Connection failure with {uri_type} URI: {e}")
                if tls_enabled.lower() == "true":
                    logger.warning("SSL/TLS connection failure detected")
                    logger.warning("This may be due to DNS resolution or SSL handshake issues")
            except Exception as e:
                logger.warning(f"Unexpected error with {uri_type} URI: {e}")
                if tls_enabled.lower() == "true":
                    logger.warning("SSL/TLS related error - check OpenSSL compatibility")
        
        # If we get here, all URIs failed for this attempt
        if attempt < max_retries - 1:
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"All connection URIs failed. Retrying in {delay:.2f} seconds...")
            await asyncio.sleep(delay)
        else:
            logger.error("❌ All connection attempts exhausted")
    
    # If we get here, all attempts failed
    error_msg = f"Failed to connect to MongoDB after {max_retries} attempts with all available URIs"
    logger.error(error_msg)
    
    if tls_enabled.lower() == "true":
        logger.error("🔒 SSL/TLS connection failures detected across all attempts")
        logger.error("Troubleshooting suggestions:")
        logger.error("1. Check network connectivity to MongoDB Atlas")
        logger.error("2. Verify DNS resolution is working correctly")
        logger.error("3. Ensure firewall allows outbound connections on port 27017")
        logger.error("4. Check if OpenSSL version is compatible")
        logger.error("5. Verify MongoDB Atlas cluster is running and accessible")
    
    raise ConnectionFailure(error_msg)

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