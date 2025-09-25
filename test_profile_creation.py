#!/usr/bin/env python3
"""
Test script to create a profile and test family member operations
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

def test_profile_creation_and_family():
    """Test profile creation and family member operations"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing profile creation and family member operations...")
    
    # First, try to create a profile
    print("\n1. Creating a profile...")
    profile_data = {
        "dietary_restrictions": ["Vegetarian"],
        "weekly_budget": 100.0,
        "zip_code": "12345"
    }
    
    response = requests.put(f"{BASE_URL}/profile/", headers=headers, json=profile_data)
    print(f"Create profile status: {response.status_code}")
    print(f"Create profile response: {response.text}")
    
    # Now test get profile
    print("\n2. Testing GET /profile/")
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    print(f"Get profile status: {response.status_code}")
    print(f"Get profile response: {response.text}")
    
    if response.status_code == 200:
        # Test add family member
        print("\n3. Testing POST /profile/family-members")
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
        print(f"Add family member status: {response.status_code}")
        print(f"Add family member response: {response.text}")

if __name__ == "__main__":
    test_profile_creation_and_family()