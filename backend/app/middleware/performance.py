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

logger = structlog.get_logger(__name__)

# Redis connection for caching
redis_client: Optional[redis.Redis] = None

async def get_redis_client():
    """Get Redis client for caching"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await redis_client.ping()
            logger.info("Connected to Redis for caching")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for caching: {e}")
            redis_client = None
    return redis_client

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
    """Configuration for MongoDB connection pooling"""
    
    @staticmethod
    def get_connection_options():
        """Get optimized MongoDB connection options for production with SSL/TLS support"""
        options = {
            "maxPoolSize": int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
            "minPoolSize": int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
            "maxIdleTimeMS": int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000")),
            "waitQueueTimeoutMS": int(os.getenv("MONGODB_WAIT_QUEUE_TIMEOUT_MS", "5000")),
            "serverSelectionTimeoutMS": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "30000")),
            "connectTimeoutMS": int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "30000")),
            "socketTimeoutMS": int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "30000")),
            "retryWrites": True,
            "retryReads": True,
            "readPreference": "secondaryPreferred"
        }
        
        # Add SSL/TLS options if enabled
        if os.getenv("MONGODB_TLS_ENABLED", "false").lower() == "true":
            options.update({
                "tls": True,
                "tlsAllowInvalidCertificates": os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "false").lower() == "true"
            })
        
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