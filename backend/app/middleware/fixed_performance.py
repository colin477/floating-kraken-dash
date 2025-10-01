"""
Fixed performance middleware with proper ASGI message handling
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

class FixedCompressionMiddleware:
    """Fixed compression middleware with proper ASGI message handling"""
    
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
        response_started = False
        response_complete = False
        
        async def send_wrapper(message):
            nonlocal response_body, response_headers, response_status, response_started, response_complete
            
            if message["type"] == "http.response.start":
                if response_started:
                    logger.error("ASGI Protocol Violation: Response already started")
                    return
                
                response_started = True
                response_status = message.get("status", 200)
                response_headers = dict(message.get("headers", []))
                
                # Don't send the start message yet - we'll send it after processing the body
                return
                
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body += body
                more_body = message.get("more_body", False)
                
                if not more_body:  # This is the final chunk
                    response_complete = True
                    
                    # Now we can decide whether to compress and send the complete response
                    if len(response_body) >= self.minimum_size:
                        # Compress the response
                        try:
                            compressed_body = gzip.compress(response_body)
                            response_headers[b"content-encoding"] = b"gzip"
                            response_headers[b"content-length"] = str(len(compressed_body)).encode()
                            
                            # Send start message
                            await send({
                                "type": "http.response.start",
                                "status": response_status,
                                "headers": list(response_headers.items())
                            })
                            
                            # Send compressed body
                            await send({
                                "type": "http.response.body",
                                "body": compressed_body
                            })
                        except Exception as e:
                            logger.error(f"Compression error: {e}")
                            # Fall back to uncompressed
                            await send({
                                "type": "http.response.start",
                                "status": response_status,
                                "headers": list(response_headers.items())
                            })
                            await send({
                                "type": "http.response.body",
                                "body": response_body
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
                else:
                    # For streaming responses, we can't compress, so pass through
                    if not response_started:
                        await send({
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": list(response_headers.items())
                        })
                        response_started = True
                    
                    await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"Error in compression middleware: {e}")
            # If we haven't started the response yet, send an error response
            if not response_started:
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")]
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Internal server error"}'
                })
            raise

class FixedCacheMiddleware:
    """Fixed cache middleware with proper ASGI message handling"""
    
    def __init__(self, app, default_ttl: int = 300):
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
                    
                    await send({
                        "type": "http.response.start",
                        "status": cached_data["status_code"],
                        "headers": [(b"content-type", b"application/json"), (b"x-cache", b"HIT")]
                    })
                    await send({
                        "type": "http.response.body",
                        "body": json.dumps(cached_data["content"]).encode()
                    })
                    return
            except Exception as e:
                logger.warning(f"Cache retrieval error: {e}")
        
        # Capture response for caching
        response_body = b""
        response_headers = {}
        response_status = 200
        response_started = False
        
        async def send_wrapper(message):
            nonlocal response_body, response_headers, response_status, response_started
            
            if message["type"] == "http.response.start":
                if response_started:
                    logger.error("ASGI Protocol Violation: Response already started in cache middleware")
                    return
                
                response_started = True
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