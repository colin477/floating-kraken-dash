#!/usr/bin/env python3
"""
Test script to verify MongoDB SSL/TLS connection fixes are working
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        print(f"Health Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200 and response.json().get("database_connected", False)
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_signup_endpoint():
    """Test user signup (database write operation)"""
    print("\nTesting signup endpoint...")
    test_user = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User SSL"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=test_user)
        print(f"Signup Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            return True, test_user["email"]
        else:
            return False, None
    except Exception as e:
        print(f"Signup test failed: {e}")
        return False, None

def test_login_endpoint(email):
    """Test user login (database read operation)"""
    print("\nTesting login endpoint...")
    login_data = {
        "email": email,
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return True, response.json().get("access_token")
        else:
            return False, None
    except Exception as e:
        print(f"Login test failed: {e}")
        return False, None

def test_profile_endpoint(token):
    """Test profile endpoint (authenticated database operation)"""
    print("\nTesting profile endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/profile/me", headers=headers)
        print(f"Profile Status: {response.status_code}")
        print(f"Response: {response.json()}")
        # 404 is acceptable if no profile exists yet - the important thing is the database connection works
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Profile test failed: {e}")
        return False

def test_pantry_endpoint(token):
    """Test pantry endpoint (database operations)"""
    print("\nTesting pantry endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pantry", headers=headers)
        print(f"Pantry Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # 404 is OK if no pantry items exist
    except Exception as e:
        print(f"Pantry test failed: {e}")
        return False

def main():
    """Run all SSL/TLS connection tests"""
    print("=== MongoDB SSL/TLS Connection Test ===\n")
    
    # Test 1: Health check
    if not test_health_endpoint():
        print("❌ Health check failed - database not connected")
        sys.exit(1)
    print("✅ Health check passed - database connected")
    
    # Test 2: Signup (database write)
    signup_success, email = test_signup_endpoint()
    if not signup_success:
        print("❌ Signup test failed")
        sys.exit(1)
    print("✅ Signup test passed - database write operation successful")
    
    # Test 3: Login (database read)
    login_success, token = test_login_endpoint(email)
    if not login_success:
        print("❌ Login test failed")
        sys.exit(1)
    print("✅ Login test passed - database read operation successful")
    
    # Test 4: Profile (authenticated database operation)
    if not test_profile_endpoint(token):
        print("❌ Profile test failed")
        sys.exit(1)
    print("✅ Profile test passed - authenticated database operation successful")
    
    # Test 5: Pantry (additional database operation)
    if not test_pantry_endpoint(token):
        print("❌ Pantry test failed")
        sys.exit(1)
    print("✅ Pantry test passed - additional database operation successful")
    
    print("\n=== All SSL/TLS Connection Tests Passed! ===")
    print("✅ MongoDB SSL/TLS connection is working properly")
    print("✅ Database operations are functioning correctly")
    print("✅ No SSL handshake errors detected")

if __name__ == "__main__":
    main()