#!/usr/bin/env python3
"""
Test registration endpoint to verify error handling improvements
"""

import requests
import json

def test_registration_endpoint():
    """Test the registration endpoint"""
    print("Testing registration endpoint...")
    
    url = "http://localhost:8000/api/v1/auth/signup"
    
    # Test data with unique email
    import time
    unique_email = f"test{int(time.time())}@example.com"
    test_data = {
        "email": unique_email,
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    print(f"Testing with email: {unique_email}")
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful")
            return True
        elif response.status_code == 409:
            print("⚠️  User already exists (expected if running multiple times)")
            return True
        elif response.status_code == 503:
            print("⚠️  Service unavailable (Redis/Database issue)")
            return False
        elif response.status_code == 500:
            print("❌ Internal server error (this is what we're trying to fix)")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        return False
    except Exception as e:
        print(f"❌ Error testing registration: {e}")
        return False

if __name__ == "__main__":
    result = test_registration_endpoint()
    print(f"\nRegistration endpoint test result: {'PASS' if result else 'FAIL'}")