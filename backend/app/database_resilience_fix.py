"""
MongoDB Connection Resilience Fix
Addresses DNS resolution inconsistencies and improves connection stability
"""

import os
import asyncio
import ssl
import random
import time
import socket
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect
import structlog
from dotenv import load_dotenv
from app.middleware.performance import DatabasePoolConfig

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)

class ResilientDatabase:
    """Enhanced database class with DNS resolution resilience and connection stability"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database = None
        self._connection_healthy = False
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._connection_attempts = 0
        self._max_connection_attempts = 5
        self._backoff_multiplier = 2.0
        self._base_retry_delay = 1.0

    async def _resolve_mongodb_hosts(self, mongodb_uri: str) -> list:
        """
        Resolve MongoDB hosts using multiple DNS resolution strategies
        to work around Windows DNS resolution issues
        """
        try:
            from urllib.parse import urlparse
            
            # Parse the MongoDB URI
            if mongodb_uri.startswith("mongodb+srv://"):
                # For SRV records, let the MongoDB driver handle resolution
                logger.info("Using MongoDB driver SRV resolution for Atlas connection")
                return [mongodb_uri]  # Return original URI for driver to handle
            
            # For standard mongodb:// URIs, try to resolve hosts
            parsed = urlparse(mongodb_uri.replace("mongodb://", "http://"))
            hostname = parsed.hostname
            
            if not hostname:
                logger.warning("Could not extract hostname from MongoDB URI")
                return [mongodb_uri]
            
            # Try multiple DNS resolution strategies
            resolved_ips = []
            
            # Strategy 1: Use socket.getaddrinfo with different parameters
            try:
                addr_info = socket.getaddrinfo(
                    hostname, 27017, 
                    socket.AF_UNSPEC, 
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP
                )
                resolved_ips.extend([addr[4][0] for addr in addr_info])
                logger.info(f"DNS resolution successful via getaddrinfo: {resolved_ips}")
            except socket.gaierror as e:
                logger.warning(f"getaddrinfo DNS resolution failed: {e}")
            
            # Strategy 2: Use gethostbyname as fallback
            if not resolved_ips:
                try:
                    ip = socket.gethostbyname(hostname)
                    resolved_ips.append(ip)
                    logger.info(f"DNS resolution successful via gethostbyname: {ip}")
                except socket.gaierror as e:
                    logger.warning(f"gethostbyname DNS resolution failed: {e}")
            
            # If DNS resolution failed, return original URI and let MongoDB driver handle it
            if not resolved_ips:
                logger.info("DNS resolution failed, using original URI for MongoDB driver resolution")
                return [mongodb_uri]
            
            # Create alternative URIs with resolved IPs (for debugging/fallback)
            alternative_uris = []
            for ip in resolved_ips[:3]:  # Limit to first 3 IPs
                alt_uri = mongodb_uri.replace(hostname, ip)
                alternative_uris.append(alt_uri)
            
            logger.info(f"Created {len(alternative_uris)} alternative connection URIs")
            return [mongodb_uri] + alternative_uris  # Original first, then alternatives
            
        except Exception as e:
            logger.warning(f"Host resolution failed: {e}, using original URI")
            return [mongodb_uri]

    async def _create_resilient_client(self, mongodb_uri: str) -> AsyncIOMotorClient:
        """
        Create MongoDB client with enhanced resilience settings
        """
        # Get optimized connection options
        connection_options = DatabasePoolConfig.get_connection_options()
        
        # Enhanced resilience options for Windows DNS issues
        resilience_options = {
            # Increase timeouts to handle DNS resolution delays
            'serverSelectionTimeoutMS': 60000,  # 60 seconds
            'connectTimeoutMS': 60000,           # 60 seconds
            'socketTimeoutMS': 60000,            # 60 seconds
            
            # Connection pool resilience
            'maxPoolSize': 10,  # Reduced pool size for stability
            'minPoolSize': 1,   # Ensure at least one connection
            'maxIdleTimeMS': 45000,  # 45 seconds
            'waitQueueTimeoutMS': 30000,  # 30 seconds
            
            # Retry and reconnection settings
            'retryWrites': True,
            'retryReads': True,
            'heartbeatFrequencyMS': 10000,  # 10 seconds
            
            # Application name for monitoring
            'appName': 'EZ_Eatin_Resilient'
        }
        
        # Merge with existing options, prioritizing resilience options
        connection_options.update(resilience_options)
        
        logger.info("Creating resilient MongoDB client", **{
            k: v for k, v in connection_options.items() 
            if not k.lower().endswith('password')
        })
        
        return AsyncIOMotorClient(mongodb_uri, **connection_options)

    async def connect_with_resilience(self):
        """
        Connect to MongoDB with enhanced resilience and DNS resolution handling
        """
        mongodb_uri = os.getenv("MONGODB_URI", "")
        database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
        if not mongodb_uri:
            raise ConnectionFailure("MongoDB URI not configured")
        
        logger.info("Starting resilient MongoDB connection process")
        
        # Resolve potential connection URIs
        connection_uris = await self._resolve_mongodb_hosts(mongodb_uri)
        
        # Try each URI with exponential backoff
        last_error = None
        retry_delay = self._base_retry_delay
        
        for attempt in range(self._max_connection_attempts):
            for uri_index, uri in enumerate(connection_uris):
                try:
                    logger.info(f"Connection attempt {attempt + 1}/{self._max_connection_attempts}, URI {uri_index + 1}/{len(connection_uris)}")
                    
                    # Create client with resilience settings
                    self.client = await self._create_resilient_client(uri)
                    
                    # Test connection with timeout
                    start_time = time.time()
                    await asyncio.wait_for(
                        self.client.admin.command('ping'),
                        timeout=30.0  # 30 second timeout for initial connection
                    )
                    connect_time = time.time() - start_time
                    
                    # Set database
                    self.database = self.client[database_name]
                    
                    # Mark as healthy
                    self._connection_healthy = True
                    self._last_health_check = time.time()
                    self._connection_attempts = attempt + 1
                    
                    # Log success
                    server_info = await self.client.server_info()
                    logger.info(
                        "Resilient MongoDB connection established",
                        database=database_name,
                        mongodb_version=server_info.get('version', 'Unknown'),
                        connection_time=f"{connect_time:.3f}s",
                        attempt=attempt + 1,
                        uri_index=uri_index + 1
                    )
                    
                    return  # Success!
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    logger.warning(f"Connection timeout on attempt {attempt + 1}, URI {uri_index + 1}: {e}")
                    
                except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
                    last_error = e
                    logger.warning(f"Connection failed on attempt {attempt + 1}, URI {uri_index + 1}: {e}")
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"Unexpected error on attempt {attempt + 1}, URI {uri_index + 1}: {e}")
                
                # Clean up failed client
                if self.client:
                    self.client.close()
                    self.client = None
            
            # If not the last attempt, wait with exponential backoff
            if attempt < self._max_connection_attempts - 1:
                jitter = random.uniform(0.1, 0.5) * retry_delay
                total_delay = retry_delay + jitter
                logger.info(f"Waiting {total_delay:.2f}s before next attempt")
                await asyncio.sleep(total_delay)
                retry_delay *= self._backoff_multiplier
        
        # All attempts failed
        self._connection_healthy = False
        error_msg = f"Failed to establish MongoDB connection after {self._max_connection_attempts} attempts"
        logger.error(error_msg, last_error=str(last_error))
        raise ConnectionFailure(f"{error_msg}: {last_error}")

    async def health_check_with_resilience(self) -> bool:
        """
        Enhanced health check with automatic reconnection
        """
        current_time = time.time()
        
        # Check if we need to perform a health check
        if (self._connection_healthy and 
            current_time - self._last_health_check < self._health_check_interval):
            return True
        
        if not self.client:
            logger.warning("No MongoDB client available, attempting reconnection")
            try:
                await self.connect_with_resilience()
                return True
            except Exception as e:
                logger.error(f"Reconnection failed during health check: {e}")
                return False
        
        # Perform health check with timeout
        try:
            await asyncio.wait_for(
                self.client.admin.command('ping'),
                timeout=10.0  # 10 second timeout for health check
            )
            
            self._connection_healthy = True
            self._last_health_check = current_time
            logger.debug("MongoDB health check passed")
            return True
            
        except asyncio.TimeoutError:
            logger.warning("MongoDB health check timed out")
            self._connection_healthy = False
            return False
            
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            self._connection_healthy = False
            
            # Attempt automatic reconnection
            try:
                logger.info("Attempting automatic reconnection after health check failure")
                await self.connect_with_resilience()
                return True
            except Exception as reconnect_error:
                logger.error(f"Automatic reconnection failed: {reconnect_error}")
                return False

    async def get_collection_with_resilience(self, collection_name: str):
        """
        Get collection with automatic health check and reconnection
        """
        # Ensure connection is healthy
        if not await self.health_check_with_resilience():
            raise ConnectionFailure("MongoDB connection is not healthy and reconnection failed")
        
        return self.database[collection_name]

    async def close_connection(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._connection_healthy = False
            logger.info("MongoDB connection closed")

# Create global resilient database instance
resilient_db = ResilientDatabase()

# Enhanced connection functions for backward compatibility
async def connect_to_mongo_resilient():
    """Enhanced connection function with resilience"""
    await resilient_db.connect_with_resilience()

async def get_database_resilient():
    """Get database with resilience"""
    if not await resilient_db.health_check_with_resilience():
        raise ConnectionFailure("Database connection is not available")
    return resilient_db.database

async def get_collection_resilient(collection_name: str):
    """Get collection with resilience"""
    return await resilient_db.get_collection_with_resilience(collection_name)

async def close_mongo_connection_resilient():
    """Close connection with resilience"""
    await resilient_db.close_connection()

async def check_connection_health_resilient() -> bool:
    """Check connection health with resilience"""
    return await resilient_db.health_check_with_resilience()