#!/usr/bin/env python3
"""
Test script to verify the receipt API response format fix
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append('./backend')

API_BASE_URL = "http://localhost:8000/api/v1"

async def test_receipt_api_fix():
    """Test the receipt API response format fix"""
    print("🧪 TESTING RECEIPT API RESPONSE FORMAT FIX")
    print("=" * 60)
    
    # Test credentials (you may need to adjust these)
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Login to get auth token
            print("📝 Step 1: Logging in...")
            login_data = aiohttp.FormData()
            login_data.add_field('username', test_email)
            login_data.add_field('password', test_password)
            
            async with session.post(f"{API_BASE_URL}/auth/login-form", data=login_data) as response:
                if response.status != 200:
                    print(f"❌ Login failed with status {response.status}")
                    # Try to register first
                    print("📝 Attempting to register user...")
                    register_data = {
                        "email": test_email,
                        "password": test_password,
                        "full_name": "Test User"
                    }
                    
                    async with session.post(f"{API_BASE_URL}/auth/register", 
                                          json=register_data,
                                          headers={'Content-Type': 'application/json'}) as reg_response:
                        if reg_response.status not in [200, 201]:
                            reg_error = await reg_response.text()
                            print(f"❌ Registration failed: {reg_error}")
                            return False
                        print("✅ User registered successfully")
                    
                    # Try login again
                    async with session.post(f"{API_BASE_URL}/auth/login-form", data=login_data) as retry_response:
                        if retry_response.status != 200:
                            retry_error = await retry_response.text()
                            print(f"❌ Login retry failed: {retry_error}")
                            return False
                        login_result = await retry_response.json()
                else:
                    login_result = await response.json()
                
                token = login_result.get('access_token')
                if not token:
                    print("❌ No access token received")
                    return False
                
                print("✅ Login successful")
            
            # Step 2: Create a test image file (mock)
            print("📝 Step 2: Creating test receipt image...")
            test_image_content = b"fake image content for testing"
            
            # Step 3: Test receipt upload and processing
            print("📝 Step 3: Testing receipt upload and processing...")
            
            # Create form data for file upload
            form_data = aiohttp.FormData()
            form_data.add_field('file', test_image_content, 
                              filename='test_receipt.jpg', 
                              content_type='image/jpeg')
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            async with session.post(f"{API_BASE_URL}/receipts/upload", 
                                  data=form_data, 
                                  headers=headers) as response:
                
                print(f"📊 Response Status: {response.status}")
                
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    print(f"❌ Upload failed: {error_text}")
                    return False
                
                # Get the response data
                response_data = await response.json()
                print(f"📊 Response Data: {json.dumps(response_data, indent=2, default=str)}")
                
                # Step 4: Verify the response format matches frontend expectations
                print("📝 Step 4: Verifying response format...")
                
                # Check for required frontend fields
                required_fields = ['success', 'items', 'message']
                missing_fields = []
                
                for field in required_fields:
                    if field not in response_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                # Verify field types
                if not isinstance(response_data.get('success'), bool):
                    print(f"❌ 'success' field should be boolean, got: {type(response_data.get('success'))}")
                    return False
                
                if not isinstance(response_data.get('items'), list):
                    print(f"❌ 'items' field should be list, got: {type(response_data.get('items'))}")
                    return False
                
                if not isinstance(response_data.get('message'), str):
                    print(f"❌ 'message' field should be string, got: {type(response_data.get('message'))}")
                    return False
                
                print("✅ Response format matches frontend expectations!")
                print(f"   - success: {response_data['success']}")
                print(f"   - items: {len(response_data['items'])} items")
                print(f"   - message: {response_data['message']}")
                
                # Check for optional backend fields (should still be present)
                optional_fields = ['receipt_id', 'processing_status', 'confidence_score']
                for field in optional_fields:
                    if field in response_data:
                        print(f"   - {field}: {response_data[field]}")
                
                return True
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test function"""
    success = await test_receipt_api_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 RECEIPT API FIX TEST PASSED!")
        print("✅ Backend response format now matches frontend expectations")
    else:
        print("❌ RECEIPT API FIX TEST FAILED!")
        print("❌ Backend response format still has issues")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)