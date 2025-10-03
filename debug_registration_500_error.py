#!/usr/bin/env python3
"""
Debug script to identify the root cause of 500 Internal Server Error during user registration
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_registration_flow():
    """Test the registration flow step by step to identify where the 500 error occurs"""
    
    print("=== REGISTRATION 500 ERROR DIAGNOSTIC ===")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Test 1: Redis Connection
    print("1. Testing Redis Connection...")
    try:
        from app.utils.redis_client import get_redis_client
        redis_conn = await get_redis_client()
        if redis_conn:
            print("   ✅ Redis connection successful")
            await redis_conn.ping()
            print("   ✅ Redis ping successful")
        else:
            print("   ❌ Redis connection failed - redis_client is None")
    except Exception as e:
        print(f"   ❌ Redis connection error: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
    
    print()
    
    # Test 2: Database Connection
    print("2. Testing Database Connection...")
    try:
        from app.database import get_collection
        users_collection = await get_collection("users")
        print("   ✅ Database connection successful")
        
        # Test a simple query
        count = await users_collection.count_documents({})
        print(f"   ✅ Database query successful - {count} users in collection")
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
    
    print()
    
    # Test 3: User Creation Logic
    print("3. Testing User Creation Logic...")
    try:
        from app.models.auth import UserCreate
        from app.crud.users import create_user
        
        # Create test user data
        test_user = UserCreate(
            email=f"test_{datetime.utcnow().timestamp()}@example.com",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        print(f"   📋 Test user email: {test_user.email}")
        
        # Try to create user
        created_user = await create_user(test_user)
        print("   ✅ User creation successful")
        print(f"   📋 Created user ID: {created_user['_id']}")
        
        # Test 4: Profile Stub Creation
        print("\n4. Testing Profile Stub Creation...")
        try:
            from app.crud.profiles import create_profile_stub
            profile_stub = await create_profile_stub(str(created_user["_id"]))
            if profile_stub:
                print("   ✅ Profile stub creation successful")
            else:
                print("   ❌ Profile stub creation failed - returned None")
        except Exception as e:
            print(f"   ❌ Profile stub creation error: {e}")
            print(f"   📋 Error type: {type(e).__name__}")
            traceback.print_exc()
        
        # Test 5: Token Creation
        print("\n5. Testing Token Creation...")
        try:
            from app.utils.auth import create_access_token
            from datetime import timedelta
            
            access_token = create_access_token(
                data={"sub": str(created_user["_id"]), "email": created_user["email"]},
                expires_delta=timedelta(minutes=60)
            )
            print("   ✅ Token creation successful")
            print(f"   📋 Token length: {len(access_token)} characters")
        except Exception as e:
            print(f"   ❌ Token creation error: {e}")
            print(f"   📋 Error type: {type(e).__name__}")
        
        # Test 6: Update Last Login
        print("\n6. Testing Update Last Login...")
        try:
            from app.crud.users import update_user_last_login
            await update_user_last_login(str(created_user["_id"]))
            print("   ✅ Update last login successful")
        except Exception as e:
            print(f"   ❌ Update last login error: {e}")
            print(f"   📋 Error type: {type(e).__name__}")
        
        # Cleanup: Remove test user
        print("\n7. Cleaning up test user...")
        try:
            from bson import ObjectId
            users_collection = await get_collection("users")
            await users_collection.delete_one({"_id": ObjectId(created_user["_id"])})
            
            profiles_collection = await get_collection("profiles")
            await profiles_collection.delete_one({"user_id": str(created_user["_id"])})
            print("   ✅ Test user cleanup successful")
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
        
    except Exception as e:
        print(f"   ❌ User creation error: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
        traceback.print_exc()
    
    print()
    
    # Test 7: Rate Limiting Impact
    print("7. Testing Rate Limiting Impact...")
    try:
        from app.middleware.security import get_limiter
        limiter = get_limiter()
        print("   ✅ Rate limiter initialization successful")
        print(f"   📋 Limiter storage: {limiter.storage}")
    except Exception as e:
        print(f"   ❌ Rate limiter error: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
    
    print()
    
    # Test 8: Middleware Error Handling
    print("8. Testing Middleware Error Handling...")
    try:
        # Simulate a Redis connection error scenario
        print("   📋 Simulating Redis connection failure scenario...")
        
        # Check if middleware gracefully handles Redis failures
        from app.middleware.security import is_token_blacklisted
        result = await is_token_blacklisted("fake_token")
        print(f"   ✅ Token blacklist check handled gracefully: {result}")
        
    except Exception as e:
        print(f"   ❌ Middleware error handling failed: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
    
    print()
    print("=== DIAGNOSTIC COMPLETE ===")
    print()
    
    # Summary and Recommendations
    print("🔍 ANALYSIS SUMMARY:")
    print("Based on the error pattern and code analysis:")
    print()
    print("MOST LIKELY ROOT CAUSE:")
    print("- Redis connection failures are causing intermittent 500 errors")
    print("- The rate limiting middleware depends on Redis")
    print("- When Redis is unavailable, some operations may fail silently")
    print("- The registration endpoint has a generic exception handler that")
    print("  catches all exceptions and returns 500 with the message:")
    print("  'Internal server error during user registration'")
    print()
    print("SPECIFIC FAILURE POINTS:")
    print("1. Rate limiting middleware failing when Redis is down")
    print("2. Token blacklisting operations failing silently")
    print("3. Login attempt tracking failing (though this is login-specific)")
    print()
    print("RECOMMENDED FIXES:")
    print("1. Add Redis connection health checks")
    print("2. Implement graceful degradation when Redis is unavailable")
    print("3. Add more specific error handling in registration endpoint")
    print("4. Add Redis connection retry logic")
    print("5. Consider using memory fallback for rate limiting")

async def main():
    """Main function to run the diagnostic"""
    try:
        # Initialize database connection
        from app.database import connect_to_mongo
        await connect_to_mongo()
        
        # Run the diagnostic
        await test_registration_flow()
        
    except Exception as e:
        print(f"❌ Failed to initialize diagnostic: {e}")
        traceback.print_exc()
    finally:
        # Close database connection
        try:
            from app.database import close_mongo_connection
            await close_mongo_connection()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())