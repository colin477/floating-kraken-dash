#!/usr/bin/env python3
"""
Test script to verify the signup order of operations fix.
This tests that password validation happens BEFORE email checking.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
SIGNUP_URL = f"{BASE_URL}/api/v1/auth/signup"

# Test cases for password validation (should happen FIRST)
WEAK_PASSWORD_TESTS = [
    {
        "name": "Too short password",
        "data": {
            "email": "test1@example.com",
            "password": "weak",
            "full_name": "Test User 1"
        },
        "expected_status": 400,
        "expected_error_contains": "Password must be at least 8 characters long"
    },
    {
        "name": "No uppercase letter",
        "data": {
            "email": "test2@example.com", 
            "password": "weakpassword123!",
            "full_name": "Test User 2"
        },
        "expected_status": 400,
        "expected_error_contains": "Password must contain at least one uppercase letter"
    },
    {
        "name": "No special character",
        "data": {
            "email": "test3@example.com",
            "password": "WeakPassword123",
            "full_name": "Test User 3"
        },
        "expected_status": 400,
        "expected_error_contains": "Password must contain at least one special character"
    },
    {
        "name": "Common weak password",
        "data": {
            "email": "test4@example.com",
            "password": "password",
            "full_name": "Test User 4"
        },
        "expected_status": 400,
        "expected_error_contains": "Password is too common and easily guessable"
    }
]

# Test case for valid user creation
VALID_USER_TEST = {
    "name": "Valid user creation",
    "data": {
        "email": "validuser@example.com",
        "password": "StrongPassword123!",
        "full_name": "Valid User"
    },
    "expected_status": 201
}

# Test case for email conflict (should happen AFTER password validation)
EMAIL_CONFLICT_TEST = {
    "name": "Email already exists",
    "data": {
        "email": "validuser@example.com",  # Same as above
        "password": "AnotherStrongPassword456!",
        "full_name": "Another User"
    },
    "expected_status": 409,
    "expected_error_contains": "Email already registered"
}

# Critical test: weak password with existing email should return password error, NOT email error
CRITICAL_TEST = {
    "name": "CRITICAL: Weak password with existing email should return password error",
    "data": {
        "email": "validuser@example.com",  # Existing email
        "password": "weak",  # Weak password
        "full_name": "Critical Test User"
    },
    "expected_status": 400,
    "expected_error_contains": "Password must be at least 8 characters long",
    "should_not_contain": "Email already registered"
}

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

async def run_test(session: aiohttp.ClientSession, test: Dict[str, Any]) -> bool:
    """Run a single test case and return success status."""
    print(f"\n🧪 Testing: {test['name']}")
    print(f"   Email: {test['data']['email']}")
    print(f"   Password: {test['data']['password']}")
    
    response = await make_signup_request(session, test['data'])
    
    print(f"   Response Status: {response['status']}")
    print(f"   Response: {response.get('text', 'No response text')}")
    
    # Check status code
    expected_status = test['expected_status']
    if response['status'] != expected_status:
        print(f"   ❌ FAILED: Expected status {expected_status}, got {response['status']}")
        return False
    
    # Check error message content
    if 'expected_error_contains' in test:
        response_text = response.get('text', '')
        expected_text = test['expected_error_contains']
        if expected_text not in response_text:
            print(f"   ❌ FAILED: Expected error message to contain '{expected_text}'")
            print(f"   Actual response: {response_text}")
            return False
        else:
            print(f"   ✅ PASSED: Found expected error message '{expected_text}'")
    
    # Check that certain text should NOT be present (critical for order of operations)
    if 'should_not_contain' in test:
        response_text = response.get('text', '')
        forbidden_text = test['should_not_contain']
        if forbidden_text in response_text:
            print(f"   ❌ FAILED: Response should NOT contain '{forbidden_text}' but it does")
            print(f"   This indicates the order of operations is still wrong!")
            return False
        else:
            print(f"   ✅ PASSED: Correctly does NOT contain '{forbidden_text}'")
    
    if response['status'] == expected_status:
        print(f"   ✅ PASSED: Status code correct")
        return True
    
    return False

async def main():
    """Run all tests to verify the signup order of operations fix."""
    print("🚀 Testing Signup Order of Operations Fix")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        all_tests_passed = True
        
        # Test 1: Password validation errors (should work regardless of email existence)
        print("\n📋 Phase 1: Testing Password Validation (should happen FIRST)")
        for test in WEAK_PASSWORD_TESTS:
            success = await run_test(session, test)
            if not success:
                all_tests_passed = False
        
        # Test 2: Create a valid user
        print("\n📋 Phase 2: Creating Valid User")
        success = await run_test(session, VALID_USER_TEST)
        if not success:
            all_tests_passed = False
        
        # Test 3: Test email conflict with strong password
        print("\n📋 Phase 3: Testing Email Conflict (should happen AFTER password validation)")
        success = await run_test(session, EMAIL_CONFLICT_TEST)
        if not success:
            all_tests_passed = False
        
        # Test 4: CRITICAL TEST - weak password with existing email
        print("\n📋 Phase 4: CRITICAL TEST - Order of Operations")
        print("This test verifies that password validation happens BEFORE email checking.")
        print("If this fails, the bug still exists!")
        success = await run_test(session, CRITICAL_TEST)
        if not success:
            all_tests_passed = False
            print("\n🚨 CRITICAL FAILURE: The order of operations bug still exists!")
            print("Password validation is NOT happening before email checking.")
        else:
            print("\n🎉 CRITICAL TEST PASSED: Order of operations is now correct!")
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! The signup order of operations fix is working correctly.")
        print("✅ Password validation now happens BEFORE email checking")
        print("✅ Users get proper password error messages instead of 'Email already registered'")
        print("✅ Email conflicts return HTTP 409 as expected")
    else:
        print("❌ SOME TESTS FAILED! The fix may not be working correctly.")
        print("Please check the test output above for details.")
    
    return all_tests_passed

if __name__ == "__main__":
    asyncio.run(main())