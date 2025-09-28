#!/usr/bin/env python3
"""
Debug script to investigate the signup issue where all emails show "Email already registered"
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_collection, connect_to_mongo
from app.crud.users import get_user_by_email, create_user_indexes
from app.models.auth import UserCreate

async def debug_signup_issue():
    """Debug the signup issue by checking database state and user creation logic"""
    
    print("=== DEBUGGING SIGNUP ISSUE ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        # Connect to database
        await connect_to_mongo()
        print("✓ Connected to MongoDB")
        
        # Get users collection
        users_collection = await get_collection("users")
        
        # Check total user count
        total_users = await users_collection.count_documents({})
        print(f"✓ Total users in database: {total_users}")
        
        # List all users (first 10)
        print("\n=== EXISTING USERS ===")
        users_cursor = users_collection.find({}).limit(10)
        users = await users_cursor.to_list(length=10)
        
        if users:
            for i, user in enumerate(users, 1):
                print(f"{i}. Email: {user.get('email', 'N/A')}")
                print(f"   ID: {user.get('_id', 'N/A')}")
                print(f"   Active: {user.get('is_active', 'N/A')}")
                print(f"   Created: {user.get('created_at', 'N/A')}")
                print()
        else:
            print("No users found in database")
        
        # Check indexes
        print("=== DATABASE INDEXES ===")
        indexes = await users_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Index: {idx['name']} - Keys: {idx.get('key', {})}")
            if 'unique' in idx:
                print(f"  Unique: {idx['unique']}")
        print()
        
        # Test email lookup with various test emails
        test_emails = [
            "test@example.com",
            "newuser@test.com", 
            "fresh@email.com",
            "unique@domain.com"
        ]
        
        print("=== TESTING EMAIL LOOKUPS ===")
        for email in test_emails:
            existing_user = await get_user_by_email(email)
            status = "EXISTS" if existing_user else "NOT FOUND"
            print(f"Email: {email} - Status: {status}")
        print()
        
        # Test user creation process step by step
        print("=== TESTING USER CREATION PROCESS ===")
        test_user_data = UserCreate(
            email="debug-test@example.com",
            password="TestPassword123!",
            full_name="Debug Test User"
        )
        
        print(f"1. Testing with email: {test_user_data.email}")
        
        # Step 1: Check if user exists
        existing_user = await get_user_by_email(test_user_data.email)
        print(f"2. Existing user check: {'FOUND' if existing_user else 'NOT FOUND'}")
        
        if existing_user:
            print(f"   Existing user details:")
            print(f"   - ID: {existing_user.get('_id')}")
            print(f"   - Email: {existing_user.get('email')}")
            print(f"   - Active: {existing_user.get('is_active')}")
            print(f"   - Created: {existing_user.get('created_at')}")
        
        # Step 2: Test index creation
        print("3. Testing index creation...")
        index_result = await create_user_indexes()
        print(f"   Index creation result: {index_result}")
        
        # Step 3: Check for any database connection issues
        print("4. Testing database connection...")
        ping_result = await users_collection.database.client.admin.command('ping')
        print(f"   Database ping: {ping_result}")
        
        # Step 4: Check collection stats
        print("5. Collection statistics...")
        try:
            stats = await users_collection.database.command("collStats", "users")
            print(f"   Collection exists: True")
            print(f"   Document count: {stats.get('count', 0)}")
            print(f"   Index count: {stats.get('nindexes', 0)}")
        except Exception as e:
            print(f"   Collection stats error: {e}")
        
        # Clean up test user if it was created during debugging
        if existing_user and existing_user.get('email') == test_user_data.email:
            print(f"\n6. Cleaning up test user...")
            delete_result = await users_collection.delete_one({"email": test_user_data.email})
            print(f"   Deleted {delete_result.deleted_count} test user(s)")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(debug_signup_issue())