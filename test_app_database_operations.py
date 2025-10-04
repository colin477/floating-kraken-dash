#!/usr/bin/env python3
"""
Test script to verify key database operations work with the MongoDB SSL/TLS fixes
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append('backend')

from app.database import connect_to_mongo, close_mongo_connection, db
from app.crud.users import create_user, authenticate_user
from app.models.auth import UserCreate
from app.utils.auth import hash_password

async def test_key_database_operations():
    """Test key database operations that the application uses"""
    print("=== Testing Key Database Operations ===")
    
    # Load environment variables
    load_dotenv('backend/.env')
    
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        await connect_to_mongo()
        
        if db.database is None:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Connected to MongoDB successfully")
        
        # Test 1: User Authentication Operations
        print("\n--- Testing User Authentication Operations ---")
        
        # Create a test user
        test_email = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        test_password = "TestPassword123!"
        
        user_data = UserCreate(
            email=test_email,
            password=test_password,
            full_name="Test User SSL/TLS"
        )
        
        print(f"Creating test user: {test_email}")
        created_user = await create_user(user_data)
        print(f"✅ User created successfully: {created_user['_id']}")
        
        # Test authenticating the user
        print("Testing user authentication...")
        authenticated_user = await authenticate_user(test_email, test_password, None)
        if authenticated_user:
            print(f"✅ User authenticated successfully: {authenticated_user['email']}")
        else:
            print("❌ Failed to authenticate user")
            return False
        
        # Test 2: Profile Operations
        print("\n--- Testing Profile Operations ---")
        
        profiles_collection = db.database['profiles']
        
        # Create a test profile
        test_profile = {
            "user_id": str(created_user['_id']),
            "dietary_preferences": ["vegetarian"],
            "allergies": ["nuts"],
            "household_size": 2,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        print("Creating test profile...")
        profile_result = await profiles_collection.insert_one(test_profile)
        print(f"✅ Profile created successfully: {profile_result.inserted_id}")
        
        # Retrieve the profile
        print("Retrieving profile...")
        retrieved_profile = await profiles_collection.find_one({"user_id": str(created_user['_id'])})
        if retrieved_profile:
            print(f"✅ Profile retrieved successfully for user: {retrieved_profile['user_id']}")
        else:
            print("❌ Failed to retrieve profile")
            return False
        
        # Test 3: Data Retrieval Operations
        print("\n--- Testing Data Retrieval Operations ---")
        
        # Test collection queries
        users_collection = db.database['users']
        user_count = await users_collection.count_documents({})
        print(f"✅ Total users in database: {user_count}")
        
        profile_count = await profiles_collection.count_documents({})
        print(f"✅ Total profiles in database: {profile_count}")
        
        # Test aggregation pipeline
        print("Testing aggregation pipeline...")
        pipeline = [
            {"$match": {"email": {"$regex": "@example.com$"}}},
            {"$count": "test_users"}
        ]
        
        async for result in users_collection.aggregate(pipeline):
            print(f"✅ Aggregation successful: {result}")
        
        # Clean up test data
        print("\n--- Cleaning up test data ---")
        await users_collection.delete_one({"_id": created_user['_id']})
        await profiles_collection.delete_one({"user_id": str(created_user['_id'])})
        print("✅ Test data cleaned up")
        
        print("\n🎉 All key database operations completed successfully!")
        print("The MongoDB SSL/TLS fixes are working correctly in the application context.")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_mongo_connection()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    success = asyncio.run(test_key_database_operations())
    sys.exit(0 if success else 1)