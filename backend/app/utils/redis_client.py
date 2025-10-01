"""
Centralized Redis client for the application
"""

import os
from typing import Optional
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)

redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get a single, shared Redis client for the entire application.
    """
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
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            redis_client = None
    return redis_client