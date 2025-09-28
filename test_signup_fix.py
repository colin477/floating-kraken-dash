"""
Test script to verify the signup error handling fix
"""

import asyncio
import aiohttp
import json

async def test_password_validation_error():
    """Test that password validation errors return proper error messages"""
    
    # Test data with weak password (8+ chars but fails our custom validation)
    test_data = {
        "email": "passwordtest@example.com",
        "password": "weakpass",  # This should fail our custom validation
        "full_name": "Test User"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/api/v1/auth/signup",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check if we get the correct error message
                if response.status == 400:
                    detail = response_data.get("detail", "")
                    if "Password validation failed" in detail:
                        print("✅ SUCCESS: Password validation error properly returned")
                        return True
                    else:
                        print(f"❌ FAIL: Expected password validation error, got: {detail}")
                        return False
                else:
                    print(f"❌ FAIL: Expected 400 status code, got: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

async def test_email_already_exists():
    """Test that email already exists errors return proper error messages"""
    
    # First, create a user
    test_data = {
        "email": "existing@example.com",
        "password": "StrongPassword123!",
        "full_name": "Existing User"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Create the user first
            async with session.post(
                "http://localhost:8000/api/v1/auth/signup",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    print("✅ First user created successfully")
                else:
                    print(f"⚠️  First user creation returned status: {response.status}")
            
            # Try to create the same user again
            async with session.post(
                "http://localhost:8000/api/v1/auth/signup",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check if we get the correct error message
                if response.status == 409:  # Conflict status code
                    detail = response_data.get("detail", "")
                    if "Email already registered" in detail:
                        print("✅ SUCCESS: Email already exists error properly returned")
                        return True
                    else:
                        print(f"❌ FAIL: Expected email already exists error, got: {detail}")
                        return False
                else:
                    print(f"❌ FAIL: Expected 409 status code, got: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

async def main():
    """Run all tests"""
    print("Testing signup error handling fix...")
    print("=" * 50)
    
    print("\n1. Testing password validation error:")
    password_test = await test_password_validation_error()
    
    print("\n2. Testing email already exists error:")
    email_test = await test_email_already_exists()
    
    print("\n" + "=" * 50)
    if password_test and email_test:
        print("✅ ALL TESTS PASSED: Error handling is working correctly!")
    else:
        print("❌ SOME TESTS FAILED: Error handling needs more work")

if __name__ == "__main__":
    asyncio.run(main())