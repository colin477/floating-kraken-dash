import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import ssl
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """Test MongoDB connection with detailed error reporting"""
    
    # MongoDB URI from .env
    mongodb_uri = "mongodb+srv://colin_db_user:FnaPFUQh6aAjhfiR@cluster0.vcpyxwh.mongodb.net/ez_eatin?retryWrites=true&w=majority&appName=Cluster0"
    
    print("=== Testing MongoDB Connection ===")
    print(f"URI: {mongodb_uri}")
    print()
    
    # Test 1: Basic connection with default settings
    print("Test 1: Basic connection with default settings")
    try:
        client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("✓ Basic connection successful")
        client.close()
    except Exception as e:
        print(f"✗ Basic connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print()
    
    # Test 2: Connection with explicit SSL settings
    print("Test 2: Connection with explicit SSL settings")
    try:
        client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            ssl_ca_certs=None,  # Use system CA bundle
            ssl_match_hostname=True
        )
        await client.admin.command('ping')
        print("✓ SSL connection successful")
        client.close()
    except Exception as e:
        print(f"✗ SSL connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print()
    
    # Test 3: Connection with relaxed SSL settings
    print("Test 3: Connection with relaxed SSL settings")
    try:
        client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_match_hostname=False
        )
        await client.admin.command('ping')
        print("✓ Relaxed SSL connection successful")
        client.close()
    except Exception as e:
        print(f"✗ Relaxed SSL connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print()
    
    # Test 4: Connection with custom SSL context
    print("Test 4: Connection with custom SSL context")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,
            ssl_context=ssl_context
        )
        await client.admin.command('ping')
        print("✓ Custom SSL context connection successful")
        client.close()
    except Exception as e:
        print(f"✗ Custom SSL context connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print()
    
    # Test 5: Connection with TLS 1.2 minimum
    print("Test 5: Connection with TLS 1.2 minimum")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,
            ssl_context=ssl_context
        )
        await client.admin.command('ping')
        print("✓ TLS 1.2+ connection successful")
        client.close()
    except Exception as e:
        print(f"✗ TLS 1.2+ connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())