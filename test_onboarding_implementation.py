"""
Test script to verify the onboarding implementation works correctly
"""

import asyncio
import json
import requests
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

async def test_onboarding_workflow():
    """Test the complete onboarding workflow"""
    
    print("Testing Onboarding Implementation")
    print("=" * 50)
    
    # Test data
    test_user = {
        "email": f"test_onboarding_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test Onboarding User"
    }
    
    try:
        # Step 1: Register a new user (should create profile stub)
        print("\n1. Testing user registration with profile stub creation...")
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user
        )
        
        if register_response.status_code == 201:
            print("SUCCESS: User registration successful")
            auth_data = register_response.json()
            token = auth_data["access_token"]
            user_id = auth_data["user"]["id"]
            print(f"   User ID: {user_id}")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"FAILED: Registration failed: {register_response.status_code}")
            print(f"   Response: {register_response.text}")
            return
        
        # Headers for authenticated requests
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Check onboarding status (should be incomplete)
        print("\n2. Testing onboarding status check...")
        status_response = requests.get(
            f"{BASE_URL}/profile/onboarding-status",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("SUCCESS: Onboarding status check successful")
            print(f"   Has profile: {status_data['has_profile']}")
            print(f"   Onboarding completed: {status_data['onboarding_completed']}")
            
            if not status_data['onboarding_completed'] and status_data['has_profile']:
                print("SUCCESS: Profile stub created correctly with onboarding_completed: false")
            else:
                print("FAILED: Profile stub not created correctly")
        else:
            print(f"FAILED: Onboarding status check failed: {status_response.status_code}")
            print(f"   Response: {status_response.text}")
        
        # Step 3: Test plan selection
        print("\n3. Testing plan selection...")
        plan_data = {
            "subscription": "basic",
            "trial_ends_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        plan_response = requests.post(
            f"{BASE_URL}/profile/plan-selection",
            json=plan_data,
            headers=headers
        )
        
        if plan_response.status_code == 200:
            print("SUCCESS: Plan selection successful")
            plan_result = plan_response.json()
            print(f"   Subscription: {plan_result['subscription']}")
            print(f"   Trial ends at: {plan_result.get('trial_ends_at', 'N/A')}")
        else:
            print(f"FAILED: Plan selection failed: {plan_response.status_code}")
            print(f"   Response: {plan_response.text}")
        
        # Step 4: Complete onboarding
        print("\n4. Testing onboarding completion...")
        complete_data = {"onboarding_completed": True}
        
        complete_response = requests.post(
            f"{BASE_URL}/profile/complete-onboarding",
            json=complete_data,
            headers=headers
        )
        
        if complete_response.status_code == 200:
            print("SUCCESS: Onboarding completion successful")
            complete_result = complete_response.json()
            print(f"   Onboarding completed: {complete_result['onboarding_completed']}")
        else:
            print(f"FAILED: Onboarding completion failed: {complete_response.status_code}")
            print(f"   Response: {complete_response.text}")
        
        # Step 5: Verify final onboarding status
        print("\n5. Testing final onboarding status...")
        final_status_response = requests.get(
            f"{BASE_URL}/profile/onboarding-status",
            headers=headers
        )
        
        if final_status_response.status_code == 200:
            final_status_data = final_status_response.json()
            print("SUCCESS: Final onboarding status check successful")
            print(f"   Has profile: {final_status_data['has_profile']}")
            print(f"   Onboarding completed: {final_status_data['onboarding_completed']}")
            
            if final_status_data['onboarding_completed'] and final_status_data['has_profile']:
                print("SUCCESS: Onboarding workflow completed successfully!")
            else:
                print("FAILED: Onboarding workflow not completed correctly")
        else:
            print(f"FAILED: Final status check failed: {final_status_response.status_code}")
            print(f"   Response: {final_status_response.text}")
        
        # Step 6: Test profile access
        print("\n6. Testing profile access...")
        profile_response = requests.get(
            f"{BASE_URL}/profile/",
            headers=headers
        )
        
        if profile_response.status_code == 200:
            print("SUCCESS: Profile access successful")
            profile_data = profile_response.json()
            print(f"   Profile ID: {profile_data.get('id', 'N/A')}")
            print(f"   User ID: {profile_data.get('user_id', 'N/A')}")
            print(f"   Subscription: {profile_data.get('subscription', 'N/A')}")
            print(f"   Onboarding completed: {profile_data.get('onboarding_completed', 'N/A')}")
        else:
            print(f"FAILED: Profile access failed: {profile_response.status_code}")
            print(f"   Response: {profile_response.text}")
        
        print("\n" + "=" * 50)
        print("Onboarding implementation test completed!")
        
    except requests.exceptions.ConnectionError:
        print("FAILED: Connection error: Make sure the backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"FAILED: Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_onboarding_workflow())