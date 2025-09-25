"""
Security middleware for production-grade security enhancements
"""

import time
import uuid
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import structlog
import redis.asyncio as redis
import os

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Redis connection for rate limiting and token blacklisting
redis_client: Optional[redis.Redis] = None

async def get_redis_client():
    """Get Redis client for rate limiting and caching"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            await redis_client.ping()
            logger.info("Connected to Redis for rate limiting and caching")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Rate limiting will use in-memory storage.")
            redis_client = None
    return redis_client

# Rate limiter configuration
def get_limiter():
    """Create rate limiter with Redis backend if available"""
    try:
        return Limiter(
            key_func=get_remote_address,
            storage_uri=os.getenv("REDIS_URL", "memory://"),
            default_limits=["1000/hour"]
        )
    except Exception:
        # Fallback to memory storage
        return Limiter(
            key_func=get_remote_address,
            storage_uri="memory://",
            default_limits=["1000/hour"]
        )

limiter = get_limiter()

class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Security headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"content-security-policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
                    b"x-permitted-cross-domain-policies": b"none",
                    b"cross-origin-embedder-policy": b"require-corp",
                    b"cross-origin-opener-policy": b"same-origin",
                    b"cross-origin-resource-policy": b"same-origin"
                }
                
                # Add security headers
                for header_name, header_value in security_headers.items():
                    headers[header_name] = header_value
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class RequestLoggingMiddleware:
    """Middleware for comprehensive request/response logging"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract request information
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        client_ip = None
        user_agent = None
        
        # Extract headers
        headers = dict(scope.get("headers", []))
        if b"x-forwarded-for" in headers:
            client_ip = headers[b"x-forwarded-for"].decode().split(",")[0].strip()
        elif b"x-real-ip" in headers:
            client_ip = headers[b"x-real-ip"].decode()
        else:
            client_host = scope.get("client", ["unknown", 0])[0]
            client_ip = client_host if client_host != "unknown" else "unknown"
        
        if b"user-agent" in headers:
            user_agent = headers[b"user-agent"].decode()
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
            query_string=query_string,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Response capture
        response_status = None
        response_size = 0
        
        async def send_wrapper(message):
            nonlocal response_status, response_size
            
            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_size += len(body)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log error
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=method,
                path=path,
                error=str(e),
                duration=time.time() - start_time
            )
            raise
        finally:
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response_status,
                response_size=response_size,
                duration=duration
            )

class ErrorHandlingMiddleware:
    """Middleware for enhanced error handling and preventing information leakage"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            # Log the full error for debugging
            logger.error(
                "Unhandled exception in request",
                error=str(e),
                error_type=type(e).__name__,
                path=scope.get("path", ""),
                method=scope.get("method", "")
            )
            
            # Return generic error response to prevent information leakage
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "status_code": 500
                }
            )
            await response(scope, receive, send)

async def is_token_blacklisted(token: str) -> bool:
    """Check if a JWT token is blacklisted"""
    try:
        redis_conn = await get_redis_client()
        if redis_conn:
            return await redis_conn.exists(f"blacklisted_token:{token}")
        return False
    except Exception as e:
        logger.warning(f"Error checking token blacklist: {e}")
        return False

async def blacklist_token(token: str, expiry_seconds: int = 86400):
    """Add a JWT token to the blacklist"""
    try:
        redis_conn = await get_redis_client()
        if redis_conn:
            await redis_conn.setex(f"blacklisted_token:{token}", expiry_seconds, "1")
            logger.info("Token blacklisted successfully")
        else:
            logger.warning("Cannot blacklist token: Redis not available")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")

# Rate limit exceeded handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    logger.warning(
        "Rate limit exceeded",
        client_ip=get_remote_address(request),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "status_code": 429,
            "retry_after": exc.retry_after
        }
    )

# Request size limit middleware
class RequestSizeLimitMiddleware:
    """Middleware to limit request body size"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        self.app = app
        self.max_size = max_size
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check content-length header
        headers = dict(scope.get("headers", []))
        if b"content-length" in headers:
            content_length = int(headers[b"content-length"].decode())
            if content_length > self.max_size:
                response = JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request too large",
                        "message": f"Request body size exceeds maximum allowed size of {self.max_size} bytes",
                        "status_code": 413
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)