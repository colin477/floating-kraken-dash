# Database Performance Improvement Plan

## 1. Introduction

This document outlines the plan to improve the performance and reliability of the database connection. The current implementation lacks connection pooling and uses a security setting that is not recommended for production.

## 2. Proposed Solution

To address these issues, we will implement connection pooling and configure the database connection for a production environment.

### 2.1. Implement Connection Pooling

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

### 2.2. Add Indexing

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

## 3. Implementation Steps

1.  Update the `connect_to_mongo` function in `backend/app/database.py` to include connection pooling options.
2.  Update the `users` collection to include an index on the `email` field.
3.  Call the `create_user_indexes` function on application startup.
4.  Restart the application and monitor for performance improvements.

## 4. Expected Outcome

After implementing these changes, the application will use a connection pool to connect to the database, which will improve performance and reduce the overhead of establishing new connections. The addition of indexes will also improve query performance.