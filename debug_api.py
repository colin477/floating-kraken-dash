#!/usr/bin/env python3
"""
Debug script to test the API directly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"

def test_signup():
    """Test signup and see raw response"""
    print(f"Testing signup with email: {TEST_EMAIL}")
    
    signup_data = {
        "email": TEST_EMAIL,
        "password": "TestPassword123!",
        "full_name": "Debug User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"Parsed Response: {json.dumps(data, indent=2)}")
            return data.get("access_token")
        else:
            print("Signup failed")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_profile_endpoints(token):
    """Test the new profile endpoints"""
    if not token:
        print("No token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test intake status
    print("\n--- Testing intake status ---")
    try:
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test complete intake
    print("\n--- Testing complete intake ---")
    try:
        response = requests.post(f"{BASE_URL}/profile/complete-intake", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test intake status after completion
    print("\n--- Testing intake status after completion ---")
    try:
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Debug API Test")
    token = test_signup()
    test_profile_endpoints(token)