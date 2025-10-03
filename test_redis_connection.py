#!/usr/bin/env python3
"""
Test Redis connection to confirm the issue
"""

import asyncio
import os
import sys
sys.path.append('backend')

# Load environment variables from backend/.env
from dotenv import load_dotenv
load_dotenv('backend/.env')

from backend.app.utils.redis_client import get_redis_client

async def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    
    # Test with default configuration
    redis_client = await get_redis_client()
    
    if redis_client:
        print("✅ Redis connection successful")
        try:
            await redis_client.ping()
            print("✅ Redis ping successful")
        except Exception as e:
            print(f"❌ Redis ping failed: {e}")
    else:
        print("❌ Redis connection failed - client is None")
    
    # Test with explicit URL
    print(f"\nRedis URL from environment: {os.getenv('REDIS_URL', 'Not set')}")
    
    return redis_client is not None

if __name__ == "__main__":
    result = asyncio.run(test_redis_connection())
    print(f"\nRedis connection test result: {'PASS' if result else 'FAIL'}")
