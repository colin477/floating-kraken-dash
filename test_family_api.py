#!/usr/bin/env python3
"""
Test script for family member API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Login and get access token"""
    login_data = {
        "username": "testuser@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login-form",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_profile_endpoints():
    """Test profile and family member endpoints"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing profile endpoints...")
    
    # Test get profile
    print("\n1. Testing GET /profile/")
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test add family member
    print("\n2. Testing POST /profile/family-members")
    family_member_data = {
        "name": "Test Child",
        "age": 8,
        "dietary_restrictions": ["Vegetarian"],
        "allergies": ["Peanuts"],
        "loved_foods": ["Pizza"],
        "disliked_foods": ["Broccoli"]
    }
    
    response = requests.post(
        f"{BASE_URL}/profile/family-members",
        headers=headers,
        json=family_member_data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        profile_data = response.json()
        if profile_data.get("family_members"):
            member_id = profile_data["family_members"][0]["id"]
            
            # Test update family member
            print(f"\n3. Testing PUT /profile/family-members/{member_id}")
            update_data = {
                "name": "Updated Child",
                "age": 9
            }
            
            response = requests.put(
                f"{BASE_URL}/profile/family-members/{member_id}",
                headers=headers,
                json=update_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    test_profile_endpoints()