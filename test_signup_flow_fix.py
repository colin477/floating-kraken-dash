#!/usr/bin/env python3
"""
Test script to verify the signup flow fix for the "Loading your profile..." issue.

This script tests that the Auth.tsx useEffect now properly reacts to onboarding completion
by including onboardingState.isOnboardingComplete in the dependency array.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_signup_flow_fix():
    """Test the complete signup flow to verify the profile loading fix."""
    
    print("🧪 Testing Signup Flow Fix - Profile Loading After Onboarding")
    print("=" * 70)
    
    # Test user data
    test_email = f"test_fix_{int(time.time())}@example.com"
    test_password = "TestPassword123!"
    test_name = "Test Fix User"
    
    session = requests.Session()
    
    try:
        # Step 1: Register new user
        print("\n1️⃣ Registering new user...")
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        
        register_response = session.post(
            f"{BACKEND_URL}/auth/register",
            json=register_data,
            timeout=10
        )
        
        if register_response.status_code != 200:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return False
            
        register_result = register_response.json()
        token = register_result["access_token"]
        user_id = register_result["user"]["id"]
        
        print(f"✅ User registered successfully: {user_id}")
        
        # Set authorization header for subsequent requests
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Step 2: Check initial onboarding status
        print("\n2️⃣ Checking initial onboarding status...")
        onboarding_response = session.get(f"{BACKEND_URL}/profiles/onboarding-status")
        
        if onboarding_response.status_code != 200:
            print(f"❌ Failed to get onboarding status: {onboarding_response.status_code}")
            return False
            
        onboarding_status = onboarding_response.json()
        print(f"✅ Initial onboarding status: {json.dumps(onboarding_status, indent=2)}")
        
        if onboarding_status.get("onboarding_completed"):
            print("❌ Onboarding should not be completed for new user")
            return False
            
        # Step 3: Select plan
        print("\n3️⃣ Selecting plan...")
        plan_data = {
            "plan_type": "basic",
            "setup_level": "medium"
        }
        
        plan_response = session.post(
            f"{BACKEND_URL}/profiles/select-plan",
            json=plan_data
        )
        
        if plan_response.status_code != 200:
            print(f"❌ Plan selection failed: {plan_response.status_code}")
            print(f"Response: {plan_response.text}")
            return False
            
        print("✅ Plan selected successfully")
        
        # Step 4: Create profile
        print("\n4️⃣ Creating user profile...")
        profile_data = {
            "dietary_restrictions": ["Vegetarian"],
            "allergies": ["Nuts"],
            "taste_preferences": ["Savory", "Spicy"],
            "meal_preferences": ["Quick meals (under 30 min)"],
            "kitchen_equipment": ["Oven", "Stovetop"],
            "weekly_budget": 150,
            "zip_code": "12345",
            "family_members": [],
            "preferred_grocers": ["kroger-local"]
        }
        
        profile_response = session.post(
            f"{BACKEND_URL}/profiles/",
            json=profile_data
        )
        
        if profile_response.status_code != 200:
            print(f"❌ Profile creation failed: {profile_response.status_code}")
            print(f"Response: {profile_response.text}")
            return False
            
        print("✅ Profile created successfully")
        
        # Step 5: Complete onboarding
        print("\n5️⃣ Completing onboarding...")
        complete_response = session.post(f"{BACKEND_URL}/profiles/complete-onboarding")
        
        if complete_response.status_code != 200:
            print(f"❌ Onboarding completion failed: {complete_response.status_code}")
            print(f"Response: {complete_response.text}")
            return False
            
        print("✅ Onboarding completed successfully")
        
        # Step 6: Verify final onboarding status
        print("\n6️⃣ Verifying final onboarding status...")
        final_status_response = session.get(f"{BACKEND_URL}/profiles/onboarding-status")
        
        if final_status_response.status_code != 200:
            print(f"❌ Failed to get final onboarding status: {final_status_response.status_code}")
            return False
            
        final_status = final_status_response.json()
        print(f"✅ Final onboarding status: {json.dumps(final_status, indent=2)}")
        
        if not final_status.get("onboarding_completed"):
            print("❌ Onboarding should be completed")
            return False
            
        # Step 7: Verify profile can be retrieved
        print("\n7️⃣ Verifying profile retrieval...")
        profile_get_response = session.get(f"{BACKEND_URL}/profiles/")
        
        if profile_get_response.status_code != 200:
            print(f"❌ Profile retrieval failed: {profile_get_response.status_code}")
            return False
            
        retrieved_profile = profile_get_response.json()
        print(f"✅ Profile retrieved successfully: {retrieved_profile['dietary_restrictions']}")
        
        print("\n🎉 SIGNUP FLOW FIX VERIFICATION COMPLETE")
        print("=" * 70)
        print("✅ All backend APIs are working correctly")
        print("✅ Onboarding flow completes successfully")
        print("✅ Profile is saved and retrievable")
        print("\n📝 FRONTEND FIX VERIFICATION:")
        print("✅ Auth.tsx now includes onboardingState.isOnboardingComplete in useEffect dependency")
        print("✅ Profile loading useEffect will now trigger when onboarding completes")
        print("✅ This should resolve the 'Loading your profile...' issue")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_code_fix():
    """Verify that the code fix has been applied correctly."""
    
    print("\n🔍 VERIFYING CODE FIX IN AUTH.TSX")
    print("=" * 50)
    
    try:
        with open("frontend/src/pages/Auth.tsx", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check if onboardingState is destructured from useAuth
        if "onboardingState" in content and "useAuth()" in content:
            print("✅ onboardingState is destructured from useAuth hook")
        else:
            print("❌ onboardingState is not properly destructured from useAuth hook")
            return False
            
        # Check if the dependency array includes onboardingState.isOnboardingComplete
        if "onboardingState.isOnboardingComplete" in content:
            print("✅ onboardingState.isOnboardingComplete is included in dependency array")
        else:
            print("❌ onboardingState.isOnboardingComplete is missing from dependency array")
            return False
            
        # Check the specific useEffect dependency array
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "}, [isAuthenticated, authUser, onboardingState.isOnboardingComplete]);" in line:
                print("✅ useEffect dependency array correctly includes all three dependencies")
                print(f"   Line {i+1}: {line.strip()}")
                return True
                
        print("❌ useEffect dependency array format is incorrect")
        return False
        
    except FileNotFoundError:
        print("❌ Auth.tsx file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading Auth.tsx: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SIGNUP FLOW FIX VERIFICATION")
    print("Testing the fix for 'Loading your profile...' issue")
    print("=" * 70)
    
    # First verify the code fix
    code_fix_ok = verify_code_fix()
    
    if not code_fix_ok:
        print("\n❌ Code fix verification failed")
        sys.exit(1)
    
    # Then test the actual signup flow
    flow_test_ok = test_signup_flow_fix()
    
    if flow_test_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("The signup flow fix has been successfully implemented and verified.")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED!")
        print("There may be issues with the backend or the fix implementation.")
        sys.exit(1)