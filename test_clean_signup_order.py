#!/usr/bin/env python3
"""
Clean test script to verify the signup order of operations fix.
This script clears the database first, then tests the order of operations.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
SIGNUP_URL = f"{BASE_URL}/api/v1/auth/signup"

async def clear_database():
    """Clear the users collection for clean testing."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Connect to MongoDB
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database("ez_eatin")
        users_collection = db.get_collection("users")
        
        # Clear all users
        result = await users_collection.delete_many({})
        print(f"🗑️  Cleared {result.deleted_count} users from database")
        
        await client.close()
        return True
    except Exception as e:
        print(f"⚠️  Could not clear database: {e}")
        print("Proceeding with tests anyway...")
        return False

async def make_signup_request(session: aiohttp.ClientSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a signup request and return the response details."""
    try:
        async with session.post(SIGNUP_URL, json=data) as response:
            response_text = await response.text()
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                response_json = {"raw_response": response_text}
            
            return {
                "status": response.status,
                "data": response_json,
                "text": response_text
            }
    except Exception as e:
        return {
            "status": 0,
            "error": str(e),
            "data": {}
        }

async def test_password_validation_first():
    """Test that password validation happens before email checking."""
    print("\n🧪 CRITICAL TEST: Password validation should happen FIRST")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a user with a strong password
        print("\n📝 Step 1: Creating user with strong password...")
        valid_user = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "full_name": "Test User"
        }
        
        response = await make_signup_request(session, valid_user)
        print(f"   Status: {response['status']}")
        
        if response['status'] == 201:
            print("   ✅ User created successfully")
        else:
            print(f"   ❌ Failed to create user: {response.get('text', 'Unknown error')}")
            return False
        
        # Step 2: Try to create another user with the SAME email but WEAK password
        print("\n📝 Step 2: Testing weak password with existing email...")
        print("   This is the CRITICAL test - should return password error, NOT email error")
        
        weak_password_user = {
            "email": "test@example.com",  # Same email as above
            "password": "weak",           # Weak password
            "full_name": "Another User"
        }
        
        response = await make_signup_request(session, weak_password_user)
        print(f"   Status: {response['status']}")
        print(f"   Response: {response.get('text', 'No response')}")
        
        # Check if we get password validation error (not email error)
        response_text = response.get('text', '')
        
        # We expect either:
        # 1. HTTP 422 with Pydantic validation error (FastAPI level)
        # 2. HTTP 400 with custom password validation error (our level)
        if response['status'] == 422:
            if "String should have at least 8 characters" in response_text:
                print("   ✅ PASSED: Got Pydantic password validation error (HTTP 422)")
                print("   ✅ Password validation happened BEFORE email checking!")
                return True
            else:
                print("   ❌ Got HTTP 422 but not for password length")
                return False
        elif response['status'] == 400:
            if "Password" in response_text and "Email already registered" not in response_text:
                print("   ✅ PASSED: Got custom password validation error (HTTP 400)")
                print("   ✅ Password validation happened BEFORE email checking!")
                return True
            elif "Email already registered" in response_text:
                print("   ❌ FAILED: Got email error instead of password error")
                print("   ❌ This means email checking happened BEFORE password validation")
                print("   🚨 THE BUG STILL EXISTS!")
                return False
            else:
                print("   ❌ Got HTTP 400 but unclear error message")
                return False
        else:
            print(f"   ❌ Unexpected status code: {response['status']}")
            return False

async def test_email_conflict_with_strong_password():
    """Test that email conflicts work properly with strong passwords."""
    print("\n🧪 Testing email conflict with strong password...")
    
    async with aiohttp.ClientSession() as session:
        # Try to create user with existing email but strong password
        strong_password_user = {
            "email": "test@example.com",  # Existing email
            "password": "AnotherStrongPassword456!",  # Strong password
            "full_name": "Another Strong User"
        }
        
        response = await make_signup_request(session, strong_password_user)
        print(f"   Status: {response['status']}")
        print(f"   Response: {response.get('text', 'No response')}")
        
        # Should get HTTP 409 with email conflict message
        if response['status'] == 409 and "Email already registered" in response.get('text', ''):
            print("   ✅ PASSED: Got proper email conflict error (HTTP 409)")
            return True
        else:
            print("   ❌ FAILED: Expected HTTP 409 with email conflict message")
            return False

async def main():
    """Run the clean order of operations test."""
    print("🚀 Clean Signup Order of Operations Test")
    print("This test verifies that password validation happens BEFORE email checking")
    print("=" * 70)
    
    # Clear database for clean test
    await clear_database()
    
    # Run the critical test
    password_test_passed = await test_password_validation_first()
    
    # Run the email conflict test
    email_test_passed = await test_email_conflict_with_strong_password()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"   Password validation first: {'✅ PASSED' if password_test_passed else '❌ FAILED'}")
    print(f"   Email conflict handling:   {'✅ PASSED' if email_test_passed else '❌ FAILED'}")
    
    if password_test_passed and email_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The signup order of operations fix is working correctly!")
        print("✅ Password validation now happens BEFORE email checking")
        print("✅ Users get proper error messages based on the actual issue")
    else:
        print("\n❌ SOME TESTS FAILED!")
        if not password_test_passed:
            print("🚨 CRITICAL: Password validation is NOT happening before email checking")
            print("🚨 The order of operations bug still exists!")
        if not email_test_passed:
            print("⚠️  Email conflict handling needs attention")
    
    return password_test_passed and email_test_passed

if __name__ == "__main__":
    asyncio.run(main())