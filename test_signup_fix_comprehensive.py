#!/usr/bin/env python3
"""
Comprehensive test script for signup bug fix validation
Tests password validation vs email conflict error handling
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import sys

# Test configuration
BASE_URL = "http://localhost:8000"
SIGNUP_ENDPOINT = f"{BASE_URL}/api/v1/auth/signup"

class TestResult:
    def __init__(self, test_name: str, expected_status: int, expected_error_type: str):
        self.test_name = test_name
        self.expected_status = expected_status
        self.expected_error_type = expected_error_type
        self.actual_status = None
        self.actual_response = None
        self.passed = False
        self.error_message = None

class SignupTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_signup(self, test_name: str, email: str, password: str, full_name: str, 
                         expected_status: int, expected_error_type: str) -> TestResult:
        """Test signup with given parameters"""
        result = TestResult(test_name, expected_status, expected_error_type)
        
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        
        try:
            async with self.session.post(SIGNUP_ENDPOINT, json=payload) as response:
                result.actual_status = response.status
                result.actual_response = await response.json()
                
                # Check if status code matches expectation
                if result.actual_status == expected_status:
                    # For error cases, check if error message contains expected type
                    if expected_status >= 400:
                        detail = result.actual_response.get('detail', '')
                        if expected_error_type.lower() in detail.lower():
                            result.passed = True
                        else:
                            result.error_message = f"Expected error type '{expected_error_type}' not found in: {detail}"
                    else:
                        # Success case
                        if 'access_token' in result.actual_response:
                            result.passed = True
                        else:
                            result.error_message = "Expected access_token in successful response"
                else:
                    result.error_message = f"Expected status {expected_status}, got {result.actual_status}"
                    
        except Exception as e:
            result.error_message = f"Request failed: {str(e)}"
        
        self.results.append(result)
        return result
    
    def print_test_result(self, result: TestResult):
        """Print formatted test result"""
        status_icon = "✅" if result.passed else "❌"
        print(f"{status_icon} {result.test_name}")
        print(f"   Expected: HTTP {result.expected_status} with '{result.expected_error_type}'")
        print(f"   Actual: HTTP {result.actual_status}")
        
        if result.actual_response:
            if result.actual_status >= 400:
                detail = result.actual_response.get('detail', 'No detail')
                print(f"   Response: {detail}")
            else:
                # Success response - show user info
                user_info = result.actual_response.get('user', {})
                print(f"   Response: User created - {user_info.get('email', 'N/A')}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        print()
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print("=" * 60)
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 60)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The signup bug fix is working correctly.")
        else:
            print("⚠️  Some tests failed. The fix may need additional work.")
            print("\nFailed tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.test_name}: {result.error_message}")

async def main():
    """Run comprehensive signup tests"""
    print("🧪 Starting Comprehensive Signup Bug Fix Tests")
    print("=" * 60)
    
    async with SignupTester() as tester:
        # Test 1: Weak password - too short
        await tester.test_signup(
            "Weak Password - Too Short",
            "test1@example.com",
            "weak",
            "Test User 1",
            400,
            "Password validation failed"
        )
        
        # Test 2: Weak password - no uppercase
        await tester.test_signup(
            "Weak Password - No Uppercase",
            "test2@example.com", 
            "weakpassword123!",
            "Test User 2",
            400,
            "Password validation failed"
        )
        
        # Test 3: Weak password - no lowercase
        await tester.test_signup(
            "Weak Password - No Lowercase",
            "test3@example.com",
            "WEAKPASSWORD123!",
            "Test User 3", 
            400,
            "Password validation failed"
        )
        
        # Test 4: Weak password - no digits
        await tester.test_signup(
            "Weak Password - No Digits",
            "test4@example.com",
            "WeakPassword!",
            "Test User 4",
            400,
            "Password validation failed"
        )
        
        # Test 5: Weak password - no special characters
        await tester.test_signup(
            "Weak Password - No Special Characters",
            "test5@example.com",
            "WeakPassword123",
            "Test User 5",
            400,
            "Password validation failed"
        )
        
        # Test 6: Common weak password
        await tester.test_signup(
            "Common Weak Password",
            "test6@example.com",
            "password",
            "Test User 6",
            400,
            "Password validation failed"
        )
        
        # Test 7: Strong password with new email (should succeed)
        await tester.test_signup(
            "Strong Password - New Email",
            "newuser@example.com",
            "StrongPass123!",
            "New User",
            201,
            "success"
        )
        
        # Test 8: Strong password with existing email (should conflict)
        await tester.test_signup(
            "Strong Password - Existing Email",
            "newuser@example.com",  # Same email as above
            "AnotherStrongPass456!",
            "Another User",
            409,
            "Email already registered"
        )
        
        # Test 9: Multiple validation errors
        await tester.test_signup(
            "Multiple Validation Errors",
            "test9@example.com",
            "123",  # Too short, no uppercase, no lowercase, no special chars
            "Test User 9",
            400,
            "Password validation failed"
        )
        
        # Test 10: Edge case - very long password but valid
        await tester.test_signup(
            "Very Long Valid Password",
            "longpass@example.com",
            "VeryLongButValidPassword123!WithManyCharacters",
            "Long Pass User",
            201,
            "success"
        )
        
        # Print all results
        print("\n📊 DETAILED TEST RESULTS:")
        print("=" * 60)
        for result in tester.results:
            tester.print_test_result(result)
        
        # Print summary
        tester.print_summary()
        
        # Additional validation - check that password errors don't mention email
        print("\n🔍 ADDITIONAL VALIDATION:")
        print("Checking that password validation errors don't mention 'email already registered'...")
        
        password_error_tests = [r for r in tester.results if r.expected_status == 400]
        email_mentions = []
        
        for result in password_error_tests:
            if result.actual_response and 'detail' in result.actual_response:
                detail = result.actual_response['detail'].lower()
                if 'email already registered' in detail:
                    email_mentions.append(result.test_name)
        
        if email_mentions:
            print(f"❌ CRITICAL: Found password validation errors mentioning 'email already registered':")
            for test_name in email_mentions:
                print(f"   - {test_name}")
            print("   This indicates the original bug is NOT fully fixed!")
        else:
            print("✅ GOOD: No password validation errors mention 'email already registered'")
        
        print("\n" + "=" * 60)
        return len([r for r in tester.results if r.passed]) == len(tester.results)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)