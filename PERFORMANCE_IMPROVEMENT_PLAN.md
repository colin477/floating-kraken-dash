# Comprehensive Performance Improvement Plan

## 1. Introduction

This document outlines the plan to resolve Redis connection errors, improve database performance, and enhance the overall performance and reliability of the application.

## 2. Redis Performance Improvement Plan

### 2.1. Proposed Solution

To address the Redis connection errors, we will centralize the Redis connection logic into a single, shared client. This will ensure that the entire application uses a single connection pool, preventing connection exhaustion and improving performance.

#### 2.1.1. Create a Centralized Redis Client

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

#### 2.1.2. Update Middleware to Use the Centralized Client

The existing middleware files (`security.py`, `performance.py`, and `fixed_performance.py`) will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`. The local `get_redis_client` functions in these files will be removed.

#### 2.1.3. Update `main.py` to Use the Centralized Client

The `main.py` file will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`.

#### 2.1.4. Update `utils/auth.py` to Use the Centralized Client

The `utils/auth.py` file will be updated to import and use the centralized `get_redis_client` function from `backend/app/utils/redis_client.py`.

### 2.2. Implementation Steps

1.  Create the `backend/app/utils/redis_client.py` file with the code above.
2.  Update `backend/app/middleware/security.py` to use the centralized Redis client.
3.  Update `backend/app/middleware/performance.py` to use the centralized Redis client.
4.  Update `backend/app/middleware/fixed_performance.py` to use the centralized Redis client.
5.  Update `backend/main.py` to use the centralized Redis client.
6.  Update `backend/app/utils/auth.py` to use the centralized Redis client.
7.  Restart the application and monitor for Redis connection errors.

## 3. Database Performance Improvement Plan

### 3.1. Proposed Solution

To improve database performance, we will implement connection pooling and add indexes to the collections.

#### 3.1.1. Implement Connection Pooling

We will update the `connect_to_mongo` function in `backend/app/database.py` to include connection pooling options. This will allow the application to reuse existing connections, reducing the overhead of establishing new connections for each request.

**`backend/app/database.py` (updated):**

```python
"""
Database configuration and connection management for MongoDB Atlas
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import structlog

logger = structlog.get_logger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "ez_eatin")
    
    logger.info(f"Attempting to connect to MongoDB at {mongodb_uri}")
    try:
        db.client = AsyncIOMotorClient(
            mongodb_uri,
            maxPoolSize=100,
            minPoolSize=10,
            tls=True,
            tlsAllowInvalidCertificates=os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "false").lower() == "true"
        )
        await db.client.admin.command('ping')
        db.database = db.client[database_name]
        logger.info(f"Successfully connected to MongoDB database: {database_name}")
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def get_collection(collection_name: str):
    """Get a specific collection"""
    if db.database is None:
        await connect_to_mongo()
    return db.database[collection_name]
```

#### 3.1.2. Add Indexing

To improve query performance, we will add indexes to the collections. We will start by adding an index to the `users` collection on the `email` field, as this is a common query.

**`backend/app/crud/users.py` (updated):**

```python
from ..database import get_collection

async def create_user_indexes():
    """Create indexes for the users collection"""
    users_collection = await get_collection("users")
    await users_collection.create_index("email", unique=True)
```

We will also need to call this function on application startup.

**`backend/main.py` (updated):**

```python
from app.crud.users import create_user_indexes

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await create_user_indexes()
```

### 3.2. Implementation Steps

1.  Update the `connect_to_mongo` function in `backend/app/database.py` to include connection pooling options.
2.  Update the `users` collection to include an index on the `email` field.
3.  Call the `create_user_indexes` function on application startup.
4.  Restart the application and monitor for performance improvements.

## 4. Expected Outcome

After implementing these changes, the application will use a single, shared Redis connection pool and a connection pool for the database, which will resolve the Redis connection errors and improve the overall performance and stability of the application. The addition of indexes will also improve query performance.