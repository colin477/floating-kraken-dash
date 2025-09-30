#!/usr/bin/env python3
"""
Final test of the intake workflow implementation
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_complete_workflow():
    """Test the complete intake workflow"""
    print("🚀 Testing Complete Intake Workflow")
    
    # Step 1: Create a new user
    test_email = f"final_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    signup_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "Final Test User"
    }
    
    print(f"📧 Creating user: {test_email}")
    
    try:
        # Signup
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Signup Status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"❌ Signup failed: {response.text}")
            return False
        
        data = response.json()
        token = data["access_token"]
        user = data["user"]
        
        print(f"✅ User created with ID: {user['id']}")
        print(f"📋 User fields: {list(user.keys())}")
        
        # Check if profile_completed is in the response
        if "profile_completed" in user:
            print(f"✅ profile_completed field present: {user['profile_completed']}")
        else:
            print("❌ profile_completed field missing from signup response")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Test intake status endpoint
        print("\n🔍 Testing intake status endpoint...")
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        print(f"Intake Status Code: {response.status_code}")
        print(f"Intake Status Response: {response.text}")
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Intake status: profile_completed={status_data.get('profile_completed')}")
        else:
            print(f"❌ Intake status failed")
        
        # Step 3: Test complete intake endpoint
        print("\n✅ Testing complete intake endpoint...")
        response = requests.post(f"{BASE_URL}/profile/complete-intake", headers=headers)
        print(f"Complete Intake Status Code: {response.status_code}")
        print(f"Complete Intake Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Complete intake successful")
        else:
            print(f"❌ Complete intake failed")
        
        # Step 4: Test intake status after completion
        print("\n🔍 Testing intake status after completion...")
        response = requests.get(f"{BASE_URL}/profile/intake-status", headers=headers)
        print(f"Final Status Code: {response.status_code}")
        print(f"Final Status Response: {response.text}")
        
        if response.status_code == 200:
            status_data = response.json()
            if status_data.get('profile_completed') == True:
                print("✅ Profile completion status correctly updated to True")
            else:
                print("❌ Profile completion status not updated correctly")
        
        # Step 5: Test /auth/me endpoint
        print("\n👤 Testing /auth/me endpoint...")
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Auth Me Status Code: {response.status_code}")
        
        if response.status_code == 200:
            me_data = response.json()
            print(f"Auth Me Response: {json.dumps(me_data, indent=2)}")
            if "profile_completed" in me_data:
                print(f"✅ /auth/me includes profile_completed: {me_data['profile_completed']}")
            else:
                print("❌ /auth/me missing profile_completed field")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🎉 Intake workflow implementation test completed!")
    else:
        print("\n❌ Test failed")