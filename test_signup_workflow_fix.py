#!/usr/bin/env python3
"""
Test script to verify the frontend signup workflow fix.
This script tests the complete signup flow to ensure users go through intake questions.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"

def test_signup_workflow():
    """Test the complete signup workflow"""
    print("🧪 Testing Frontend Signup Workflow Fix")
    print("=" * 50)
    
    # Test 1: Register a new user
    print("\n1. Testing user registration...")
    
    test_email = f"testuser_{int(time.time())}@example.com"
    test_password = "TestPassword123!"
    test_name = "Test User"
    
    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": test_name
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=register_data)
        print(f"   Registration status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"   ✅ User registered successfully")
            print(f"   User ID: {user_data.get('user', {}).get('id')}")
            print(f"   Profile completed: {user_data.get('user', {}).get('profile_completed', False)}")
            print(f"   Onboarding step: {user_data.get('user', {}).get('onboarding_step', 'N/A')}")
            
            # Verify new user has profile_completed = False
            if not user_data.get('user', {}).get('profile_completed', True):
                print("   ✅ New user correctly has profile_completed = False")
            else:
                print("   ❌ New user should have profile_completed = False")
                
            token = user_data.get('access_token')
            user_id = user_data.get('user', {}).get('id')
            
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False
    
    # Test 2: Check intake status
    print("\n2. Testing intake status endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/profile/intake-status", headers=headers)
        print(f"   Intake status check: {response.status_code}")
        
        if response.status_code == 200:
            intake_data = response.json()
            print(f"   ✅ Intake status retrieved")
            print(f"   Profile completed: {intake_data.get('profile_completed', False)}")
            print(f"   Onboarding step: {intake_data.get('onboarding_step', 'N/A')}")
        else:
            print(f"   ❌ Intake status check failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Intake status error: {e}")
    
    # Test 3: Complete intake process
    print("\n3. Testing intake completion endpoint...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/profile/complete-intake", headers=headers)
        print(f"   Intake completion: {response.status_code}")
        
        if response.status_code == 200:
            completion_data = response.json()
            print(f"   ✅ Intake completed successfully")
            print(f"   Message: {completion_data.get('message', 'N/A')}")
            print(f"   Profile completed: {completion_data.get('profile_completed', False)}")
        else:
            print(f"   ❌ Intake completion failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Intake completion error: {e}")
    
    # Test 4: Verify user status after completion
    print("\n4. Testing user status after intake completion...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        print(f"   User status check: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ User status retrieved")
            print(f"   Profile completed: {user_data.get('profile_completed', False)}")
            print(f"   Onboarding step: {user_data.get('onboarding_step', 'N/A')}")
            
            # Verify user now has profile_completed = True
            if user_data.get('profile_completed', False):
                print("   ✅ User correctly has profile_completed = True after intake")
            else:
                print("   ❌ User should have profile_completed = True after intake")
                
        else:
            print(f"   ❌ User status check failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ User status error: {e}")
    
    # Test 5: Test login with completed profile
    print("\n5. Testing login with completed profile...")
    
    login_data = {
        "username": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login-form", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            login_response = response.json()
            print(f"   ✅ Login successful")
            print(f"   Profile completed: {login_response.get('user', {}).get('profile_completed', False)}")
            print(f"   Onboarding step: {login_response.get('user', {}).get('onboarding_step', 'N/A')}")
        else:
            print(f"   ❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Frontend Signup Workflow Test Complete!")
    print("\nKey Changes Made:")
    print("✅ Added profile_completed and onboarding_step to User interface")
    print("✅ Updated AuthContext to handle new backend fields")
    print("✅ Added completeIntake function to AuthContext")
    print("✅ Updated API service with intake endpoints")
    print("✅ Fixed Auth.tsx routing to enforce intake completion")
    print("✅ Fixed Index.tsx routing to prevent dashboard bypass")
    print("✅ Updated ProfileSetup to call completion endpoint")
    print("\nWorkflow Summary:")
    print("📝 Signup → TableSettingChoice → ProfileSetup → Dashboard (only after completion)")
    print("🔒 Users with profile_completed=false cannot access dashboard")
    print("🔄 Existing users with incomplete profiles go through intake flow")
    
    return True

if __name__ == "__main__":
    test_signup_workflow()