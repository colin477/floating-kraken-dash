"""
Performance middleware for caching, compression, and optimization
"""

import gzip
import json
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import os
import structlog
from app.utils.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

class CompressionMiddleware:
    """Middleware for response compression"""
    
    def __init__(self, app, minimum_size: int = 1024):
        self.app = app
        self.minimum_size = minimum_size
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if client accepts gzip
        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode().lower()
        supports_gzip = "gzip" in accept_encoding
        
        if not supports_gzip:
            await self.app(scope, receive, send)
            return
        
        # Capture response
        response_body = b""
        response_headers = {}
        response_status = 200
        
        async def send_wrapper(message):
            nonlocal response_body, response_headers, response_status
            
            if message["type"] == "http.response.start":
                response_status = message.get("status", 200)
                response_headers = dict(message.get("headers", []))
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body += body
                
                # If this is the last chunk, compress if needed
                if not message.get("more_body", False):
                    if len(response_body) >= self.minimum_size:
                        # Compress the response
                        compressed_body = gzip.compress(response_body)
                        
                        # Update headers
                        response_headers[b"content-encoding"] = b"gzip"
                        response_headers[b"content-length"] = str(len(compressed_body)).encode()
                        
                        # Send compressed response
                        await send({
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": list(response_headers.items())
                        })
                        await send({
                            "type": "http.response.body",
                            "body": compressed_body
                        })
                    else:
                        # Send uncompressed response
                        await send({
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": list(response_headers.items())
                        })
                        await send({
                            "type": "http.response.body",
                            "body": response_body
                        })
                    return
            
            # For streaming responses or start messages, pass through
            if message["type"] == "http.response.start":
                await send(message)
        
        await self.app(scope, receive, send_wrapper)

class CacheMiddleware:
    """Middleware for response caching"""
    
    def __init__(self, app, default_ttl: int = 300):  # 5 minutes default
        self.app = app
        self.default_ttl = default_ttl
        self.cacheable_methods = {"GET"}
        self.cacheable_paths = {
            "/api/v1/recipes",
            "/api/v1/community",
            "/healthz"
        }
    
    def _get_cache_key(self, method: str, path: str, query_string: str) -> str:
        """Generate cache key for request"""
        return f"cache:{method}:{path}:{query_string}"
    
    def _is_cacheable(self, method: str, path: str) -> bool:
        """Check if request is cacheable"""
        if method not in self.cacheable_methods:
            return False
        
        # Check if path starts with any cacheable path
        return any(path.startswith(cacheable_path) for cacheable_path in self.cacheable_paths)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        
        # Check if request is cacheable
        if not self._is_cacheable(method, path):
            await self.app(scope, receive, send)
            return
        
        # Try to get from cache
        cache_key = self._get_cache_key(method, path, query_string)
        redis_conn = await get_redis_client()
        
        if redis_conn:
            try:
                cached_response = await redis_conn.get(cache_key)
                if cached_response:
                    # Return cached response
                    cached_data = json.loads(cached_response)
                    response = JSONResponse(
                        content=cached_data["content"],
                        status_code=cached_data["status_code"],
                        headers={"X-Cache": "HIT"}
                    )
                    await response(scope, receive, send)
                    return
            except Exception as e:
                logger.warning(f"Cache retrieval error: {e}")
        
        # Capture response for caching
        response_body = b""
        response_headers = {}
        response_status = 200
        
        async def send_wrapper(message):
            nonlocal response_body, response_headers, response_status
            
            if message["type"] == "http.response.start":
                response_status = message.get("status", 200)
                response_headers = dict(message.get("headers", []))
                
                # Add cache miss header
                response_headers[b"x-cache"] = b"MISS"
                message["headers"] = list(response_headers.items())
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body += body
                
                # If this is the last chunk and response is successful, cache it
                if not message.get("more_body", False) and response_status == 200:
                    if redis_conn and response_body:
                        try:
                            # Parse response content
                            content = json.loads(response_body.decode())
                            cache_data = {
                                "content": content,
                                "status_code": response_status
                            }
                            
                            # Cache the response
                            await redis_conn.setex(
                                cache_key,
                                self.default_ttl,
                                json.dumps(cache_data)
                            )
                        except Exception as e:
                            logger.warning(f"Cache storage error: {e}")
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class PerformanceMonitoringMiddleware:
    """Middleware for performance monitoring and metrics"""
    
    def __init__(self, app):
        self.app = app
        self.slow_request_threshold = 1.0  # 1 second
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Add performance headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add server timing header
                duration = time.time() - start_time
                headers[b"server-timing"] = f"total;dur={duration*1000:.2f}".encode()
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Log slow requests
            duration = time.time() - start_time
            if duration > self.slow_request_threshold:
                logger.warning(
                    "Slow request detected",
                    method=method,
                    path=path,
                    duration=duration
                )

# Database connection pooling configuration
class DatabasePoolConfig:
    """Configuration for MongoDB connection pooling with production-safe SSL/TLS defaults"""
    
    @staticmethod
    def _is_mongodb_atlas_uri(uri: str) -> bool:
        """Detect if the MongoDB URI is for MongoDB Atlas"""
        if not uri:
            return False
        return ".mongodb.net" in uri.lower()
    
    @staticmethod
    def _get_env_bool(key: str, default: bool = False) -> bool:
        """Safely get boolean environment variable with fallback"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    @staticmethod
    def _get_env_int(key: str, default: int) -> int:
        """Safely get integer environment variable with fallback"""
        try:
            value = os.getenv(key)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    @staticmethod
    def get_connection_options():
        """
        Get optimized MongoDB connection options with production-safe SSL/TLS defaults.
        
        Automatically enables SSL/TLS for MongoDB Atlas connections even if environment
        variables are not available in production.
        """
        # Get MongoDB URI to detect Atlas connections
        mongodb_uri = os.getenv("MONGODB_URI", "")
        is_atlas = DatabasePoolConfig._is_mongodb_atlas_uri(mongodb_uri)
        
        # Base connection options optimized for MongoDB Atlas free tier stability
        options = {
            "maxPoolSize": DatabasePoolConfig._get_env_int("MONGODB_MAX_POOL_SIZE", 50),
            "minPoolSize": DatabasePoolConfig._get_env_int("MONGODB_MIN_POOL_SIZE", 5),
            "maxIdleTimeMS": DatabasePoolConfig._get_env_int("MONGODB_MAX_IDLE_TIME_MS", 30000),
            "waitQueueTimeoutMS": DatabasePoolConfig._get_env_int("MONGODB_WAIT_QUEUE_TIMEOUT_MS", 15000),
            "serverSelectionTimeoutMS": DatabasePoolConfig._get_env_int("MONGODB_SERVER_SELECTION_TIMEOUT_MS", 45000),
            "connectTimeoutMS": DatabasePoolConfig._get_env_int("MONGODB_CONNECT_TIMEOUT_MS", 45000),
            "socketTimeoutMS": DatabasePoolConfig._get_env_int("MONGODB_SOCKET_TIMEOUT_MS", 45000),
            "retryWrites": True,
            "retryReads": True,
            "readPreference": "secondaryPreferred"
        }
        
        # SSL/TLS Configuration with intelligent defaults
        # Priority: valid explicit env var > Atlas detection > fallback to false
        tls_enabled_explicit = os.getenv("MONGODB_TLS_ENABLED")
        
        if tls_enabled_explicit is not None:
            # Check if the explicit value is valid
            valid_values = {"true", "1", "yes", "on", "false", "0", "no", "off"}
            if tls_enabled_explicit.lower() in valid_values:
                # Valid explicit environment variable takes precedence
                tls_enabled = DatabasePoolConfig._get_env_bool("MONGODB_TLS_ENABLED", False)
                logger.info(f"SSL/TLS explicitly configured via MONGODB_TLS_ENABLED: {tls_enabled}")
            else:
                # Invalid value - fall back to Atlas detection
                logger.warning(f"Invalid MONGODB_TLS_ENABLED value '{tls_enabled_explicit}', falling back to Atlas detection")
                if is_atlas:
                    tls_enabled = True
                    logger.info("SSL/TLS auto-enabled for MongoDB Atlas connection (fallback)")
                else:
                    tls_enabled = False
                    logger.info("SSL/TLS disabled for non-Atlas connection (fallback)")
        elif is_atlas:
            # Auto-enable SSL/TLS for MongoDB Atlas connections
            tls_enabled = True
            logger.info("SSL/TLS auto-enabled for MongoDB Atlas connection")
        else:
            # Default to false for local/non-Atlas connections
            tls_enabled = False
            logger.info("SSL/TLS disabled for non-Atlas connection")
        
        # Apply SSL/TLS configuration if enabled
        if tls_enabled:
            # Simplified SSL/TLS options compatible with PyMongo 4.8.0
            ssl_options = {
                "tls": True
            }
            
            # Only add certificate validation option if explicitly disabled for development
            allow_invalid_certs = DatabasePoolConfig._get_env_bool(
                "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES",
                False  # Default to strict certificate validation in production
            )
            
            if allow_invalid_certs:
                ssl_options["tlsAllowInvalidCertificates"] = True
            
            # Add authSource for Atlas connections (moved outside SSL options)
            if is_atlas:
                options["authSource"] = "admin"
            
            options.update(ssl_options)
            logger.info(f"SSL/TLS configuration applied: {ssl_options}")
        
        # Log final configuration for debugging
        logger.info(
            "MongoDB connection options configured",
            is_atlas=is_atlas,
            tls_enabled=tls_enabled,
            max_pool_size=options["maxPoolSize"],
            server_selection_timeout=options["serverSelectionTimeoutMS"]
        )
        
        return options

# Cache utilities
async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    redis_conn = await get_redis_client()
    if redis_conn:
        try:
            value = await redis_conn.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
    return None

async def cache_set(key: str, value: Any, ttl: int = 300):
    """Set value in cache"""
    redis_conn = await get_redis_client()
    if redis_conn:
        try:
            await redis_conn.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

async def cache_delete(key: str):
    """Delete value from cache"""
    redis_conn = await get_redis_client()
    if redis_conn:
        try:
            await redis_conn.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")