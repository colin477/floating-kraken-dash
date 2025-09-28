#!/usr/bin/env python3
"""
Test script to verify receipt file upload functionality
"""

import requests
import os
import json
from pathlib import Path

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_receipt_upload():
    """Test the receipt upload endpoint"""
    print("🧾 Testing Receipt Upload Functionality")
    print("=" * 50)
    
    # Create a simple test image file
    test_image_path = "test_receipt.jpg"
    
    # Create a minimal JPEG file (just for testing - this won't be a real image)
    # In a real test, you'd use an actual image file
    test_image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    with open(test_image_path, 'wb') as f:
        f.write(test_image_content)
    
    print(f"✅ Created test image file: {test_image_path}")
    
    try:
        # Test 1: Upload without authentication (should fail)
        print("\n📤 Test 1: Upload without authentication")
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_receipt.jpg', f, 'image/jpeg')}
            response = requests.post(f"{API_BASE_URL}/receipts/upload", files=files)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly rejected unauthenticated request")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test 2: Check if endpoint exists and accepts file uploads
        print("\n📤 Test 2: Check endpoint structure")
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_receipt.jpg', f, 'image/jpeg')}
            # Add a fake auth header to see if we get past auth
            headers = {'Authorization': 'Bearer fake_token'}
            response = requests.post(f"{API_BASE_URL}/receipts/upload", files=files, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("❌ Validation error - check if endpoint expects different format")
        elif response.status_code == 401:
            print("✅ Authentication required (expected)")
        elif response.status_code == 500:
            print("⚠️  Server error - check backend logs")
        else:
            print(f"ℹ️  Got status {response.status_code}")
        
        # Test 3: Test with wrong file type
        print("\n📤 Test 3: Test with non-image file")
        test_text_path = "test_file.txt"
        with open(test_text_path, 'w') as f:
            f.write("This is not an image")
        
        with open(test_text_path, 'rb') as f:
            files = {'file': ('test_file.txt', f, 'text/plain')}
            headers = {'Authorization': 'Bearer fake_token'}
            response = requests.post(f"{API_BASE_URL}/receipts/upload", files=files, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✅ Correctly rejected non-image file")
        else:
            print(f"Response: {response.text}")
        
        # Clean up test files
        os.remove(test_text_path)
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"🧹 Cleaned up test file: {test_image_path}")

def test_api_structure():
    """Test the API structure and available endpoints"""
    print("\n🔍 Testing API Structure")
    print("=" * 30)
    
    try:
        # Test if the API is running
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation available at /docs")
        
        # Test receipts endpoint structure
        response = requests.get(f"{API_BASE_URL}/receipts/")
        print(f"GET /receipts/ - Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required for receipts endpoint")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")

if __name__ == "__main__":
    test_api_structure()
    test_receipt_upload()
    print("\n🎉 Test completed!")