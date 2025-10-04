#!/usr/bin/env python3
"""
Test script to verify MongoDB SSL/TLS connection is working with the new configuration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append('backend')

from app.database import connect_to_mongo, close_mongo_connection, db
from app.middleware.performance import DatabasePoolConfig

async def test_mongodb_connection():
    """Test MongoDB connection with SSL/TLS configuration"""
    print("=== MongoDB SSL/TLS Connection Verification ===")
    
    # Load environment variables
    load_dotenv('backend/.env')
    
    # Display connection configuration
    print(f"MongoDB URI: {os.getenv('MONGODB_URI', 'Not set')}")
    print(f"Database Name: {os.getenv('DATABASE_NAME', 'ez_eatin')}")
    
    # Show SSL/TLS configuration
    connection_options = DatabasePoolConfig.get_connection_options()
    print(f"Connection Options: {connection_options}")
    
    try:
        # Test connection
        print("\nAttempting to connect to MongoDB...")
        await connect_to_mongo()
        
        if db.database is not None:
            print("✅ Successfully connected to MongoDB!")
            
            # Test basic database operation
            print("\nTesting database operations...")
            
            # Test ping command
            result = await db.client.admin.command('ping')
            print(f"✅ Ping successful: {result}")
            
            # Test server info to check SSL/TLS
            server_info = await db.client.server_info()
            print(f"✅ Server info retrieved: MongoDB version {server_info.get('version', 'unknown')}")
            
            # Check if SSL/TLS is being used
            if 'openssl' in server_info:
                print(f"✅ SSL/TLS info: {server_info['openssl']}")
            
            # Test a simple collection operation
            test_collection = db.database['connection_test']
            test_doc = {"test": "connection_verification", "timestamp": "2025-10-04T02:33:00Z"}
            
            # Insert test document
            insert_result = await test_collection.insert_one(test_doc)
            print(f"✅ Test document inserted: {insert_result.inserted_id}")
            
            # Find test document
            found_doc = await test_collection.find_one({"_id": insert_result.inserted_id})
            print(f"✅ Test document retrieved: {found_doc}")
            
            # Clean up test document
            await test_collection.delete_one({"_id": insert_result.inserted_id})
            print("✅ Test document cleaned up")
            
            print("\n🎉 MongoDB SSL/TLS connection verification SUCCESSFUL!")
            print("The original SSL handshake error has been resolved.")
            
        else:
            print("❌ Database connection failed - db.database is None")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False
    finally:
        await close_mongo_connection()
        print("\nConnection closed.")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mongodb_connection())
    sys.exit(0 if success else 1)