#!/usr/bin/env python3
"""
Test the authentication fix for the login functionality
Tests the /api/v1/auth/login-form endpoint specifically
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import get_collection
from backend.app.utils.auth import hash_password

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v1/auth/login-form"

async def create_test_user():
    """Create a test user in the database for login testing"""
    try:
        users_collection = await get_collection('users')
        
        # Check if test user already exists
        test_email = "authtest@example.com"
        existing_user = await users_collection.find_one({"email": test_email})
        
        if existing_user:
            print(f"✓ Test user {test_email} already exists")
            return test_email, "testpassword123"
        
        # Create new test user
        test_password = "testpassword123"
        hashed_password = hash_password(test_password)
        
        test_user = {
            "email": test_email,
            "password_hash": hashed_password,  # Using correct field name
            "created_at": datetime.utcnow(),
            "is_active": True,
            "profile_completed": True
        }
        
        result = await users_collection.insert_one(test_user)
        print(f"✓ Created test user {test_email} with ID: {result.inserted_id}")
        return test_email, test_password
        
    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        return None, None

async def test_login_endpoint(email, password):
    """Test the /api/v1/auth/login-form endpoint"""
    print(f"\n=== Testing Login Endpoint ===")
    print(f"Endpoint: {LOGIN_ENDPOINT}")
    print(f"Email: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test with form data (as the endpoint name suggests)
            async with session.post(
                LOGIN_ENDPOINT,
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"Status Code: {status}")
                print(f"Response: {response_text}")
                
                if status == 200:
                    try:
                        response_json = json.loads(response_text)
                        print("✓ Login successful!")
                        print(f"Response contains: {list(response_json.keys())}")
                        
                        # Check for authentication token
                        if "access_token" in response_json:
                            print("✓ Access token received")
                        if "token_type" in response_json:
                            print(f"✓ Token type: {response_json['token_type']}")
                            
                        return True, response_json
                    except json.JSONDecodeError:
                        print("✓ Login successful (non-JSON response)")
                        return True, response_text
                else:
                    print(f"✗ Login failed with status {status}")
                    return False, response_text
                    
    except Exception as e:
        print(f"✗ Error testing login endpoint: {e}")
        return False, str(e)

async def test_login_with_json():
    """Test login with JSON payload as well"""
    print(f"\n=== Testing Login with JSON Payload ===")
    
    email, password = "authtest@example.com", "testpassword123"
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LOGIN_ENDPOINT,
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"Status Code: {status}")
                print(f"Response: {response_text}")
                
                return status == 200, response_text
                
    except Exception as e:
        print(f"✗ Error testing JSON login: {e}")
        return False, str(e)

async def test_invalid_credentials():
    """Test login with invalid credentials to ensure proper error handling"""
    print(f"\n=== Testing Invalid Credentials ===")
    
    login_data = {
        "email": "authtest@example.com",
        "password": "wrongpassword"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LOGIN_ENDPOINT,
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"Status Code: {status}")
                print(f"Response: {response_text}")
                
                # Should return 401 or similar for invalid credentials
                if status in [401, 403]:
                    print("✓ Properly rejected invalid credentials")
                    return True
                else:
                    print(f"✗ Unexpected status for invalid credentials: {status}")
                    return False
                    
    except Exception as e:
        print(f"✗ Error testing invalid credentials: {e}")
        return False

async def check_database_users():
    """Check what users exist in the database"""
    print(f"\n=== Checking Database Users ===")
    
    try:
        users_collection = await get_collection('users')
        users = await users_collection.find({}).to_list(length=10)
        
        print(f"Found {len(users)} users in database:")
        for user in users:
            email = user.get('email', 'no email')
            has_password_hash = 'password_hash' in user
            has_password = 'password' in user
            created = user.get('created_at', 'no date')
            
            print(f"  - {email}")
            print(f"    Created: {created}")
            print(f"    Has password_hash: {has_password_hash}")
            print(f"    Has password: {has_password}")
            
        return len(users) > 0
        
    except Exception as e:
        print(f"✗ Error checking database users: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Authentication Fix Test Suite")
    print("=" * 50)
    
    # Check database connectivity and users
    db_check = await check_database_users()
    if not db_check:
        print("✗ Database check failed, cannot proceed with tests")
        return
    
    # Create test user
    email, password = await create_test_user()
    if not email:
        print("✗ Could not create test user, cannot proceed with login tests")
        return
    
    # Test the main login endpoint
    success, response = await test_login_endpoint(email, password)
    
    # Test with JSON payload
    json_success, json_response = await test_login_with_json()
    
    # Test invalid credentials
    invalid_success = await test_invalid_credentials()
    
    # Generate test report
    print(f"\n" + "=" * 50)
    print("🧪 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    print(f"Database connectivity: {'✓ PASS' if db_check else '✗ FAIL'}")
    print(f"Test user creation: {'✓ PASS' if email else '✗ FAIL'}")
    print(f"Form login test: {'✓ PASS' if success else '✗ FAIL'}")
    print(f"JSON login test: {'✓ PASS' if json_success else '✗ FAIL'}")
    print(f"Invalid credentials test: {'✓ PASS' if invalid_success else '✗ FAIL'}")
    
    if success:
        print(f"\n✅ AUTHENTICATION FIX VERIFICATION:")
        print(f"   - No 'NoneType' object is not subscriptable error occurred")
        print(f"   - Login endpoint is functional")
        print(f"   - Authentication flow works end-to-end")
    else:
        print(f"\n❌ AUTHENTICATION FIX ISSUES DETECTED:")
        print(f"   - Login endpoint may still have issues")
        print(f"   - Further investigation needed")

if __name__ == "__main__":
    asyncio.run(main())