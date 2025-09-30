#!/usr/bin/env python3
"""
Test script for the new intake workflow endpoints
"""

import asyncio
import json
import sys
from datetime import datetime
import requests

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_intake_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Test User"

def test_signup_includes_profile_completed():
    """Test that signup response includes profile_completed field"""
    print("🧪 Testing signup includes profile_completed field...")
    
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        
        if response.status_code == 201:
            data = response.json()
            user = data.get("user", {})
            
            print(f"📋 Signup response user fields: {list(user.keys())}")
            print(f"📋 Full user data: {user}")
            
            # Check if profile_completed field exists and is False for new users
            if "profile_completed" in user:
                if user["profile_completed"] == False:
                    print("✅ Signup correctly returns profile_completed=False for new users")
                    return data["access_token"], user["id"]
                else:
                    print("❌ Signup should return profile_completed=False for new users")
                    return None, None
            else:
                print("❌ Signup response missing profile_completed field")
                return None, None
        else:
            print(f"❌ Signup failed with status {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Signup test failed: {e}")
        return None, None

def test_intake_status_endpoint(token):
    """Test the intake status endpoint"""
    print("🧪 Testing intake status endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if "profile_completed" in data and "onboarding_step" in data:
                if data["profile_completed"] == False:
                    print("✅ Intake status correctly shows profile_completed=False for new user")
                    return True
                else:
                    print("❌ Intake status should show profile_completed=False for new user")
                    return False
            else:
                print("❌ Intake status response missing required fields")
                return False
        else:
            print(f"❌ Intake status failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Intake status test failed: {e}")
        return False

def test_complete_intake_endpoint(token):
    """Test the complete intake endpoint"""
    print("🧪 Testing complete intake endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/profile/complete-intake", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("message") and "completed" in data["message"].lower():
                print("✅ Complete intake endpoint works correctly")
                return True
            else:
                print("❌ Complete intake response doesn't contain expected message")
                return False
        else:
            print(f"❌ Complete intake failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complete intake test failed: {e}")
        return False

def test_intake_status_after_completion(token):
    """Test that intake status shows completed after calling complete-intake"""
    print("🧪 Testing intake status after completion...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("profile_completed") == True:
                print("✅ Intake status correctly shows profile_completed=True after completion")
                return True
            else:
                print("❌ Intake status should show profile_completed=True after completion")
                return False
        else:
            print(f"❌ Intake status check failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Intake status after completion test failed: {e}")
        return False

def test_auth_me_includes_profile_completed(token):
    """Test that /auth/me endpoint includes profile_completed field"""
    print("🧪 Testing /auth/me includes profile_completed field...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if "profile_completed" in data:
                if data["profile_completed"] == True:
                    print("✅ /auth/me correctly includes profile_completed=True")
                    return True
                else:
                    print("❌ /auth/me shows profile_completed=False but should be True")
                    return False
            else:
                print("❌ /auth/me response missing profile_completed field")
                return False
        else:
            print(f"❌ /auth/me failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ /auth/me test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting intake workflow tests...")
    print(f"📧 Using test email: {TEST_EMAIL}")
    print()
    
    # Test 1: Signup includes profile_completed field
    token, user_id = test_signup_includes_profile_completed()
    if not token:
        print("❌ Cannot continue tests without valid signup")
        sys.exit(1)
    
    print()
    
    # Test 2: Intake status endpoint works
    if not test_intake_status_endpoint(token):
        print("❌ Intake status test failed")
        sys.exit(1)
    
    print()
    
    # Test 3: Complete intake endpoint works
    if not test_complete_intake_endpoint(token):
        print("❌ Complete intake test failed")
        sys.exit(1)
    
    print()
    
    # Test 4: Intake status shows completed after completion
    if not test_intake_status_after_completion(token):
        print("❌ Intake status after completion test failed")
        sys.exit(1)
    
    print()
    
    # Test 5: /auth/me includes profile_completed field
    if not test_auth_me_includes_profile_completed(token):
        print("❌ /auth/me test failed")
        sys.exit(1)
    
    print()
    print("🎉 All intake workflow tests passed!")
    print("✅ Backend successfully supports signup intake workflow tracking")

if __name__ == "__main__":
    main()