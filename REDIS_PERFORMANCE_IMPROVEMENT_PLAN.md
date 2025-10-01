# Redis Performance Improvement Plan

## 1. Introduction

This document outlines the plan to resolve Redis connection errors and improve the overall performance of the application. The root cause of the Redis connection errors has been identified as the creation of multiple Redis connection pools across different middleware files, leading to connection exhaustion.

## 2. Proposed Solution

To address this issue, we will centralize the Redis connection logic into a single, shared client. This will ensure that the entire application uses a single connection pool, preventing connection exhaustion and improving performance.

### 2.1. Create a Centralized Redis Client

A new file, `backend/app/utils/redis_client.py`, will be created to house the Redis connection logic. This file will contain a single `get_redis_client` function that will be used by the entire application.

**`backend/app/utils/redis_client.py`:**

```python
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
```

### 2.2. Update Middleware to Use the Centralized Client

The existing middleware files (`security.py`, `performance.py`, and `fixed_performance.py`) will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`. The local `get_redis_client` functions in these files will be removed.

### 2.3. Update `main.py` to Use the Centralized Client

The `main.py` file will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`.

### 2.4. Update `utils/auth.py` to Use the Centralized Client

The `utils/auth.py` file will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`.

## 3. Implementation Steps

1.  Create the `backend/app/utils/redis_client.py` file with the code above.
2.  Update `backend/app/middleware/security.py` to use the centralized Redis client.
3.  Update `backend/app/middleware/performance.py` to use the centralized Redis client.
4.  Update `backend/app/middleware/fixed_performance.py` to use the centralized Redis client.
5.  Update `backend/main.py` to use the centralized Redis client.
6.  Update `backend/app/utils/auth.py` to use the centralized Redis client.
7.  Restart the application and monitor for Redis connection errors.

## 4. Expected Outcome

After implementing these changes, the application will use a single, shared Redis connection pool, which will resolve the Redis connection errors and improve the overall performance and stability of the application.