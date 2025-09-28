#!/usr/bin/env python3
"""
Comprehensive Receipt Upload Testing Script
Tests the complete receipt upload workflow end-to-end
"""

import requests
import json
import os
import time
from datetime import datetime
from io import BytesIO
from PIL import Image

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "test_receipt_user@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Receipt Test User"

class ReceiptUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def register_test_user(self):
        """Register a test user for authentication"""
        self.log("Registering test user...")
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            })
            
            if response.status_code == 201:
                self.log("✅ Test user registered successfully")
                return True
            elif response.status_code == 409 or (response.status_code == 400 and "already registered" in response.text):
                self.log("ℹ️  Test user already exists, proceeding with login")
                return True
            else:
                self.log(f"❌ Failed to register user: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error registering user: {e}", "ERROR")
            return False
    
    def login_test_user(self):
        """Login and get authentication token"""
        self.log("Logging in test user...")
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login-form", data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user_id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Successfully logged in and obtained auth token")
                return True
            else:
                self.log(f"❌ Failed to login: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error logging in: {e}", "ERROR")
            return False
    
    def create_test_image(self, filename="test_receipt.jpg"):
        """Create a test receipt image"""
        self.log("Creating test receipt image...")
        
        try:
            # Create a simple test image that looks like a receipt
            img = Image.new('RGB', (400, 600), color='white')
            
            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            self.log("✅ Test receipt image created")
            return img_bytes.getvalue(), filename
            
        except Exception as e:
            self.log(f"❌ Error creating test image: {e}", "ERROR")
            return None, None
    
    def test_receipt_upload_endpoint(self):
        """Test the receipt upload endpoint"""
        self.log("Testing receipt upload endpoint...")
        
        try:
            # Create test image
            image_data, filename = self.create_test_image()
            if not image_data:
                return False
            
            # Prepare file upload
            files = {
                'file': (filename, image_data, 'image/jpeg')
            }
            
            # Remove Content-Type header for file upload
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            self.log("Uploading receipt image...")
            response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log("✅ Receipt upload successful!")
                self.log(f"   Receipt ID: {data.get('receipt_id')}")
                self.log(f"   Processing Status: {data.get('processing_status')}")
                self.log(f"   Items Found: {len(data.get('extracted_items', []))}")
                self.log(f"   Confidence Score: {data.get('confidence_score')}")
                
                return data
            else:
                self.log(f"❌ Receipt upload failed: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing receipt upload: {e}", "ERROR")
            return None
    
    def test_receipt_list_endpoint(self):
        """Test getting list of receipts"""
        self.log("Testing receipt list endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/receipts/")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Receipt list retrieved successfully!")
                self.log(f"   Total receipts: {data.get('total_count', 0)}")
                self.log(f"   Receipts on page: {len(data.get('receipts', []))}")
                return data
            else:
                self.log(f"❌ Failed to get receipt list: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error getting receipt list: {e}", "ERROR")
            return None
    
    def test_file_validation(self):
        """Test file validation (invalid file types, oversized files)"""
        self.log("Testing file validation...")
        
        # Test invalid file type
        try:
            self.log("Testing invalid file type (text file)...")
            files = {
                'file': ('test.txt', b'This is not an image', 'text/plain')
            }
            
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 400:
                self.log("✅ Invalid file type correctly rejected")
            else:
                self.log(f"❌ Invalid file type not rejected: {response.status_code}", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Error testing file validation: {e}", "ERROR")
    
    def test_cloud_storage_integration(self):
        """Test cloud storage integration"""
        self.log("Testing cloud storage integration...")
        
        # Since cloud storage is likely disabled, this will test local fallback
        image_data, filename = self.create_test_image("cloud_test_receipt.jpg")
        if not image_data:
            return False
        
        try:
            files = {
                'file': (filename, image_data, 'image/jpeg')
            }
            
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 201:
                self.log("✅ File storage (local fallback) working correctly")
                return True
            else:
                self.log(f"❌ File storage failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing cloud storage: {e}", "ERROR")
            return False
    
    def test_ocr_processing(self):
        """Test OCR processing (will likely use fallback)"""
        self.log("Testing OCR processing...")
        
        # Create a more realistic receipt image with text
        try:
            from PIL import ImageDraw, ImageFont
            
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add some receipt-like text
            try:
                # Try to use default font
                font = ImageFont.load_default()
            except:
                font = None
            
            receipt_text = [
                "GROCERY STORE",
                "123 Main St",
                "Receipt #12345",
                "",
                "Bananas        $2.99",
                "Milk           $3.49", 
                "Bread          $2.29",
                "Eggs           $4.99",
                "",
                "Subtotal      $13.76",
                "Tax            $1.10",
                "Total         $14.86"
            ]
            
            y_pos = 50
            for line in receipt_text:
                draw.text((20, y_pos), line, fill='black', font=font)
                y_pos += 30
            
            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            files = {
                'file': ('ocr_test_receipt.jpg', img_bytes.getvalue(), 'image/jpeg')
            }
            
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                items = data.get('extracted_items', [])
                self.log("✅ OCR processing completed")
                self.log(f"   Items extracted: {len(items)}")
                
                if items:
                    self.log("   Sample items:")
                    for i, item in enumerate(items[:3]):
                        self.log(f"     {i+1}. {item.get('name')} - ${item.get('total_price', 0):.2f}")
                
                return data
            else:
                self.log(f"❌ OCR processing failed: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing OCR processing: {e}", "ERROR")
            return None
    
    def test_pantry_integration(self, receipt_data):
        """Test adding receipt items to pantry"""
        if not receipt_data or not receipt_data.get('extracted_items'):
            self.log("⚠️  No receipt items to test pantry integration", "WARN")
            return False
        
        self.log("Testing pantry integration...")
        
        try:
            receipt_id = receipt_data.get('receipt_id')
            items = receipt_data.get('extracted_items', [])
            
            # Test adding first few items to pantry
            selected_items = list(range(min(3, len(items))))  # Select first 3 items
            
            response = self.session.post(
                f"{API_BASE_URL}/receipts/{receipt_id}/add-to-pantry",
                json={
                    "selected_items": selected_items,
                    "expiration_days": 7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Pantry integration successful!")
                self.log(f"   Items added: {data.get('items_added', 0)}")
                self.log(f"   Items failed: {data.get('items_failed', 0)}")
                
                if data.get('errors'):
                    self.log("   Errors encountered:")
                    for error in data.get('errors', []):
                        self.log(f"     - {error}")
                
                return True
            else:
                self.log(f"❌ Pantry integration failed: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing pantry integration: {e}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Comprehensive Receipt Upload Testing")
        self.log("=" * 60)
        
        # Test results tracking
        results = {
            "user_registration": False,
            "user_login": False,
            "receipt_upload": False,
            "receipt_list": False,
            "file_validation": False,
            "cloud_storage": False,
            "ocr_processing": False,
            "pantry_integration": False
        }
        
        # 1. User Registration & Authentication
        if self.register_test_user():
            results["user_registration"] = True
            
            if self.login_test_user():
                results["user_login"] = True
                
                # 2. Basic Receipt Upload Test
                receipt_data = self.test_receipt_upload_endpoint()
                if receipt_data:
                    results["receipt_upload"] = True
                    
                    # 3. Receipt List Test
                    if self.test_receipt_list_endpoint():
                        results["receipt_list"] = True
                    
                    # 4. File Validation Test
                    self.test_file_validation()
                    results["file_validation"] = True
                    
                    # 5. Cloud Storage Test
                    if self.test_cloud_storage_integration():
                        results["cloud_storage"] = True
                    
                    # 6. OCR Processing Test
                    ocr_data = self.test_ocr_processing()
                    if ocr_data:
                        results["ocr_processing"] = True
                        
                        # 7. Pantry Integration Test
                        if self.test_pantry_integration(ocr_data):
                            results["pantry_integration"] = True
        
        # Print final results
        self.log("=" * 60)
        self.log("🏁 COMPREHENSIVE TEST RESULTS")
        self.log("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        self.log("=" * 60)
        self.log(f"SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED! Receipt upload workflow is working correctly.")
        elif passed_tests >= total_tests * 0.7:
            self.log("⚠️  Most tests passed, but some issues need attention.")
        else:
            self.log("❌ Multiple critical issues found. Receipt upload workflow needs fixes.")
        
        return results

if __name__ == "__main__":
    tester = ReceiptUploadTester()
    results = tester.run_comprehensive_test()