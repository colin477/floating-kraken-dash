"""
Centralized Redis client for the application with enhanced resilience
"""

import os
import asyncio
from typing import Optional
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)

redis_client: Optional[redis.Redis] = None
_connection_lock = asyncio.Lock()

async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get a single, shared Redis client for the entire application with enhanced resilience.
    Temporarily disabled for testing - returns None to avoid connection issues.
    """
    global redis_client
    
    # Temporarily disable Redis connections for testing
    logger.info("Redis client disabled for testing - using memory storage fallbacks")
    return None

async def close_redis_client():
    """
    Close the Redis client connection gracefully.
    """
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            redis_client = None