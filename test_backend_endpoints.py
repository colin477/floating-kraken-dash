#!/usr/bin/env python3
"""
Simple script to test backend API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_signup_endpoint():
    """Test the signup endpoint"""
    try:
        data = {
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=data)
        print(f"Signup Test: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [201, 400]  # 201 for success, 400 for duplicate user
    except Exception as e:
        print(f"Signup test failed: {e}")
        return False

def test_recipes_endpoint():
    """Test the recipes endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/recipes/")
        print(f"Recipes List: {response.status_code}")
        if response.status_code == 401:
            print("Response: Authentication required (expected)")
            return True
        else:
            print(f"Response: {response.json()}")
            return response.status_code == 200
    except Exception as e:
        print(f"Recipes test failed: {e}")
        return False

def main():
    print("Testing Backend API Endpoints...")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    print()
    
    # Test signup endpoint
    signup_ok = test_signup_endpoint()
    print()
    
    # Test recipes endpoint
    recipes_ok = test_recipes_endpoint()
    print()
    
    print("=" * 50)
    print("Test Results:")
    print(f"Health Check: {'✓' if health_ok else '✗'}")
    print(f"Signup Endpoint: {'✓' if signup_ok else '✗'}")
    print(f"Recipes Endpoint: {'✓' if recipes_ok else '✗'}")
    
    if all([health_ok, signup_ok, recipes_ok]):
        print("\n🎉 All tests passed! Backend is functioning correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()