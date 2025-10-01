#!/usr/bin/env python3
"""
Direct test of the login endpoint without database access
Tests the /api/v1/auth/login-form endpoint specifically
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v1/auth/login-form"

async def test_login_endpoint_direct():
    """Test the login endpoint directly"""
    print("🧪 Direct Login Endpoint Test")
    print("=" * 50)
    
    # Test with some existing credentials that might be in the database
    # Note: login-form endpoint expects 'username' field (which contains email)
    test_credentials = [
        {"username": "test@example.com", "password": "testpassword123"},
        {"username": "brandnew12345@example.com", "password": "StrongPass123!"},
        {"username": "strongpass@example.com", "password": "StrongPass123!"},
        {"username": "authtest@example.com", "password": "testpassword123"}
    ]
    
    for i, creds in enumerate(test_credentials, 1):
        print(f"\n=== Test {i}: {creds['username']} ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test with form data
                async with session.post(
                    LOGIN_ENDPOINT,
                    data=creds,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    status = response.status
                    response_text = await response.text()
                    
                    print(f"Status Code: {status}")
                    print(f"Response: {response_text[:200]}...")
                    
                    if status == 200:
                        print("✅ Login successful!")
                        try:
                            response_json = json.loads(response_text)
                            if "access_token" in response_json:
                                print("✅ Access token received")
                            return True, creds, response_json
                        except json.JSONDecodeError:
                            print("✅ Login successful (non-JSON response)")
                            return True, creds, response_text
                    elif status == 401:
                        print("❌ Invalid credentials (expected for unknown users)")
                    elif status == 422:
                        print("❌ Validation error")
                    elif status == 500:
                        print("🚨 Server error - this indicates the NoneType issue!")
                        if "NoneType" in response_text:
                            print("🚨 CONFIRMED: NoneType error still present")
                        return False, creds, response_text
                    else:
                        print(f"❓ Unexpected status: {status}")
                        
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n=== Testing Invalid Credentials ===")
    invalid_creds = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LOGIN_ENDPOINT,
                data=invalid_creds,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"Status Code: {status}")
                print(f"Response: {response_text[:200]}...")
                
                if status == 500 and "NoneType" in response_text:
                    print("🚨 CONFIRMED: NoneType error occurs even with invalid credentials")
                    print("🚨 This suggests the issue is in the authentication logic itself")
                    return False, invalid_creds, response_text
                elif status == 401:
                    print("✅ Properly rejected invalid credentials")
                else:
                    print(f"❓ Unexpected status for invalid credentials: {status}")
                    
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None, None, None

async def main():
    """Main test function"""
    result, creds, response = await test_login_endpoint_direct()
    
    print(f"\n" + "=" * 50)
    print("🧪 DIRECT LOGIN TEST RESULTS")
    print("=" * 50)
    
    if result is True:
        print("✅ LOGIN ENDPOINT WORKING")
        print(f"   - Successful login with: {creds['username']}")
        print("   - Authentication fix appears to be working")
        print("   - No NoneType errors detected")
    elif result is False:
        print("❌ LOGIN ENDPOINT STILL HAS ISSUES")
        print(f"   - Failed with credentials: {creds['username']}")
        print("   - NoneType error likely still present")
        print("   - Further investigation needed")
    else:
        print("❓ INCONCLUSIVE RESULTS")
        print("   - No successful logins, but no clear NoneType errors")
        print("   - May need to create test user first")

if __name__ == "__main__":
    asyncio.run(main())