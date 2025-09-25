#!/usr/bin/env python3
"""
Test script to verify backend API connectivity and authentication flow
"""
import requests
import json
import sys

API_BASE_URL = 'http://localhost:8000/api/v1'

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://localhost:8000/healthz')
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication Endpoints:")
    
    # Test registration
    try:
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = requests.post(f"{API_BASE_URL}/auth/register", json=register_data)
        print(f"✅ Registration: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Registration Failed: {e}")
    
    # Test login
    try:
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(
            f"{API_BASE_URL}/auth/login-form", 
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(f"✅ Login: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Token received: {result.get('access_token', 'No token')[:20]}...")
            return result.get('access_token')
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
    
    return None

def test_protected_endpoints(token):
    """Test protected endpoints with authentication"""
    if not token:
        print("\n❌ No token available for protected endpoint testing")
        return
    
    print("\n🔒 Testing Protected Endpoints:")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test /auth/me
    try:
        response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
        print(f"✅ Get Current User: {response.status_code}")
        if response.status_code == 200:
            print(f"   User: {response.json()}")
    except Exception as e:
        print(f"❌ Get Current User Failed: {e}")
    
    # Test pantry endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/pantry/", headers=headers)
        print(f"✅ Pantry Endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Pantry items: {len(response.json().get('items', []))}")
    except Exception as e:
        print(f"❌ Pantry Endpoint Failed: {e}")

def test_cors():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS Configuration:")
    try:
        # Test preflight request
        response = requests.options(
            f"{API_BASE_URL}/auth/login-form",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        print(f"✅ CORS Preflight: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ CORS Test Failed: {e}")

def main():
    """Run all tests"""
    print("🧪 Backend API Connection Test")
    print("=" * 40)
    
    # Test health check
    if not test_health_check():
        print("❌ Backend is not running or not accessible")
        sys.exit(1)
    
    # Test CORS
    test_cors()
    
    # Test authentication
    token = test_auth_endpoints()
    
    # Test protected endpoints
    test_protected_endpoints(token)
    
    print("\n" + "=" * 40)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()