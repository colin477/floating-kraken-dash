#!/usr/bin/env python3
"""
Test script to verify the signup fix by testing the API endpoint directly
and checking if the frontend can connect to the local backend.
"""

import requests
import json
import time

def test_backend_connection():
    """Test if the backend is running and accessible"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible at http://localhost:8000")
            return True
        else:
            print(f"❌ Backend responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_signup_endpoint():
    """Test the signup endpoint directly"""
    signup_url = "http://localhost:8000/api/v1/auth/register"
    test_user = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    try:
        print(f"🧪 Testing signup endpoint: {signup_url}")
        response = requests.post(
            signup_url,
            json=test_user,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Signup endpoint is working correctly")
            response_data = response.json()
            print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"❌ Signup failed with status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📊 Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📊 Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Signup request failed: {e}")
        return False

def test_frontend_server():
    """Test if the frontend server is running"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server is running at http://localhost:5173")
            return True
        else:
            print(f"❌ Frontend server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend server connection failed: {e}")
        return False

def main():
    print("🔧 Testing Signup Fix Implementation")
    print("=" * 50)
    
    # Test backend connection
    backend_ok = test_backend_connection()
    
    # Test frontend server
    frontend_ok = test_frontend_server()
    
    # Test signup endpoint
    signup_ok = test_signup_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"Backend Connection: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Server: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"Signup Endpoint: {'✅ PASS' if signup_ok else '❌ FAIL'}")
    
    if backend_ok and signup_ok:
        print("\n🎉 Backend signup functionality is working correctly!")
        if frontend_ok:
            print("🎉 Frontend server is also running - you can test the full flow at http://localhost:5173")
        else:
            print("⚠️  Frontend server is not running - start it with 'cd frontend && npm run dev'")
    else:
        print("\n❌ There are issues that need to be resolved.")
    
    print("\n📝 Next Steps:")
    print("1. Open http://localhost:5173 in your browser")
    print("2. Check the browser console for debug logging from api.ts")
    print("3. Try to sign up with a new account")
    print("4. Verify that the signup uses the local backend (http://localhost:8000/api/v1)")

if __name__ == "__main__":
    main()