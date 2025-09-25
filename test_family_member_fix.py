#!/usr/bin/env python3
"""
Test script to verify the family member functionality fix
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_family_member_functionality():
    """Test the family member add functionality"""
    
    print("🧪 Testing Family Member Functionality Fix")
    print("=" * 50)
    
    # Step 1: Login to get a token
    print("1. Logging in...")
    login_data = {
        "username": "test@example.com",  # Replace with actual test user
        "password": "testpassword123"    # Replace with actual test password
    }
    
    try:
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login-form",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ No access token received")
            return False
            
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Try to add a family member
    print("2. Adding family member...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    family_member_data = {
        "name": "Test Family Member",
        "age": 25,
        "dietary_restrictions": ["Vegetarian"],
        "allergies": ["Peanuts"],
        "loved_foods": ["Pizza"],
        "disliked_foods": ["Broccoli"]
    }
    
    try:
        add_member_response = requests.post(
            f"{API_BASE_URL}/profile/family-members",
            json=family_member_data,
            headers=headers
        )
        
        print(f"Response status: {add_member_response.status_code}")
        print(f"Response body: {add_member_response.text}")
        
        if add_member_response.status_code == 200:
            print("✅ Family member added successfully!")
            response_data = add_member_response.json()
            
            # Check if family member is in the response
            family_members = response_data.get("family_members", [])
            if family_members:
                print(f"✅ Profile now has {len(family_members)} family member(s)")
                for member in family_members:
                    print(f"   - {member.get('name')} (age {member.get('age')})")
                return True
            else:
                print("❌ No family members found in response")
                return False
        else:
            print(f"❌ Failed to add family member: {add_member_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding family member: {e}")
        return False

if __name__ == "__main__":
    success = test_family_member_functionality()
    if success:
        print("\n🎉 Test PASSED - Family member functionality is working!")
    else:
        print("\n💥 Test FAILED - Family member functionality needs more work")