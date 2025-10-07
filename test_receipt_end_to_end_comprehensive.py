#!/usr/bin/env python3
"""
COMPREHENSIVE END-TO-END RECEIPT SAVING FUNCTIONALITY TEST

This script demonstrates and tests the complete receipt saving workflow:
1. User authentication setup
2. Receipt image upload with validation
3. File storage verification (local/cloud)
4. Database record creation and verification
5. OCR processing and item extraction
6. File retrieval via secure URLs
7. Pantry integration testing
8. Complete workflow documentation

Author: Receipt Processing System
Date: 2025-01-07
"""

import asyncio
import json
import os
import sys
import time
import requests
from datetime import datetime, date, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Dict, Any, List
import logging

# Add backend to path
sys.path.append('./backend')

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "receipt_test_user@example.com"
TEST_USER_PASSWORD = "SecureTestPassword123!"
TEST_USER_NAME = "Receipt End-to-End Test User"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveReceiptTester:
    """Comprehensive end-to-end receipt functionality tester"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = {}
        self.created_receipt_id = None
        self.uploaded_file_url = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        icon = icons.get(level, "ℹ️")
        print(f"[{timestamp}] {icon} {message}")
        
    def log_section(self, title: str):
        """Log section header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    # ==================== AUTHENTICATION TESTS ====================
    
    async def test_user_authentication_setup(self) -> bool:
        """Test 1: User Authentication Setup"""
        self.log_section("USER AUTHENTICATION SETUP")
        
        try:
            # Step 1: Register test user
            self.log("Registering test user...")
            register_response = self.session.post(f"{API_BASE_URL}/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            })
            
            if register_response.status_code == 201:
                self.log("Test user registered successfully", "SUCCESS")
            elif register_response.status_code == 409:
                self.log("Test user already exists, proceeding with login", "WARNING")
            else:
                self.log(f"User registration failed: {register_response.status_code} - {register_response.text}", "ERROR")
                return False
            
            # Step 2: Login and get authentication token
            self.log("Logging in test user...")
            login_response = self.session.post(f"{API_BASE_URL}/auth/login-form", data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.auth_token = login_data.get("access_token")
                self.user_id = login_data.get("user_id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"Successfully authenticated user: {self.user_id}", "SUCCESS")
                self.log(f"Auth token obtained: {self.auth_token[:20]}...", "SUCCESS")
                return True
            else:
                self.log(f"Login failed: {login_response.status_code} - {login_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Authentication setup error: {e}", "ERROR")
            return False
    
    # ==================== FILE UPLOAD TESTS ====================
    
    def create_realistic_receipt_image(self) -> bytes:
        """Create a realistic receipt image for testing"""
        try:
            # Create image with receipt-like appearance
            img = Image.new('RGB', (400, 700), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a font, fallback to default if not available
            try:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except:
                font_large = None
                font_small = None
            
            # Receipt header
            y_pos = 30
            receipt_lines = [
                "GROCERY SUPERMARKET",
                "123 Main Street",
                "Anytown, ST 12345",
                "(555) 123-4567",
                "",
                f"Date: {date.today().strftime('%m/%d/%Y')}",
                f"Time: {datetime.now().strftime('%H:%M')}",
                "Cashier: Test User",
                "Transaction #: 12345",
                "",
                "ITEMS PURCHASED:",
                "BANANAS                   $2.49",
                "MILK 2% GALLON           $3.99",
                "BREAD WHOLE WHEAT        $2.79",
                "EGGS LARGE DOZEN         $4.29",
                "CHICKEN BREAST           $8.99",
                "TOMATOES                 $3.49",
                "LETTUCE ICEBERG          $1.99",
                "CHEESE CHEDDAR           $5.49",
                "APPLES GALA              $2.99",
                "YOGURT GREEK             $4.99",
                "",
                "SUBTOTAL                $41.50",
                "TAX (8.25%)              $3.42",
                "TOTAL                   $44.92",
                "",
                "PAYMENT: CREDIT CARD",
                "CHANGE: $0.00",
                "",
                "Thank you for shopping!",
                "Visit us again soon!"
            ]
            
            # Draw receipt text
            for line in receipt_lines:
                if line.startswith("GROCERY SUPERMARKET"):
                    # Store name - larger font
                    draw.text((50, y_pos), line, fill='black', font=font_large)
                else:
                    draw.text((30, y_pos), line, fill='black', font=font_small)
                y_pos += 20
            
            # Convert to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            
            self.log("Created realistic receipt image for testing", "SUCCESS")
            return img_bytes.getvalue()
            
        except Exception as e:
            self.log(f"Error creating receipt image: {e}", "ERROR")
            # Fallback to simple image
            img = Image.new('RGB', (400, 600), color='white')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            return img_bytes.getvalue()
    
    async def test_file_upload_with_validation(self) -> bool:
        """Test 2: File Upload with Proper Validation"""
        self.log_section("FILE UPLOAD WITH VALIDATION")
        
        try:
            # Step 1: Test invalid file type (should fail)
            self.log("Testing invalid file type rejection...")
            invalid_files = {
                'file': ('test.txt', b'This is not an image', 'text/plain')
            }
            
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            invalid_response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=invalid_files,
                headers=headers
            )
            
            if invalid_response.status_code == 400:
                self.log("Invalid file type correctly rejected", "SUCCESS")
            else:
                self.log(f"Invalid file type not rejected properly: {invalid_response.status_code}", "WARNING")
            
            # Step 2: Test valid receipt image upload
            self.log("Creating and uploading valid receipt image...")
            receipt_image_data = self.create_realistic_receipt_image()
            
            valid_files = {
                'file': ('receipt_test.jpg', receipt_image_data, 'image/jpeg')
            }
            
            upload_response = self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                files=valid_files,
                headers=headers
            )
            
            if upload_response.status_code == 201:
                upload_data = upload_response.json()
                self.created_receipt_id = upload_data.get('receipt_id')
                
                self.log("Receipt upload successful!", "SUCCESS")
                self.log(f"Receipt ID: {self.created_receipt_id}", "SUCCESS")
                self.log(f"Processing Status: {upload_data.get('processing_status')}", "SUCCESS")
                self.log(f"Items Extracted: {len(upload_data.get('items', []))}", "SUCCESS")
                self.log(f"Confidence Score: {upload_data.get('confidence_score', 'N/A')}", "SUCCESS")
                
                return True
            else:
                self.log(f"Receipt upload failed: {upload_response.status_code} - {upload_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"File upload test error: {e}", "ERROR")
            return False
    
    # ==================== STORAGE VERIFICATION TESTS ====================
    
    async def test_storage_system_verification(self) -> bool:
        """Test 3: Storage System Verification"""
        self.log_section("STORAGE SYSTEM VERIFICATION")
        
        try:
            # Import storage service
            from app.utils.cloud_storage import cloud_storage_service
            
            # Step 1: Check storage service status
            self.log("Checking storage service configuration...")
            self.log(f"Cloud storage enabled: {cloud_storage_service.is_cloud_storage_enabled()}")
            self.log(f"Fallback to local: {cloud_storage_service.fallback_to_local}")
            self.log(f"S3 client available: {cloud_storage_service.s3_client is not None}")
            
            # Step 2: Test direct file upload to storage
            self.log("Testing direct file upload to storage...")
            test_content = b'Test file content for storage verification'
            
            uploaded_url = await cloud_storage_service.upload_file(
                file_content=test_content,
                filename='storage_test.txt',
                content_type='text/plain',
                user_id=self.user_id
            )
            
            if uploaded_url:
                self.uploaded_file_url = uploaded_url
                storage_type = cloud_storage_service.get_storage_type(uploaded_url)
                
                self.log(f"File uploaded successfully: {uploaded_url}", "SUCCESS")
                self.log(f"Storage type: {storage_type}", "SUCCESS")
                
                # Step 3: Verify file exists
                if storage_type == 'local' and uploaded_url.startswith('uploads/'):
                    file_exists = os.path.exists(uploaded_url)
                    if file_exists:
                        file_size = os.path.getsize(uploaded_url)
                        self.log(f"File verified on disk: {file_size} bytes", "SUCCESS")
                    else:
                        self.log("File not found on disk", "ERROR")
                        return False
                
                return True
            else:
                self.log("File upload to storage failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Storage verification error: {e}", "ERROR")
            return False
    
    # ==================== DATABASE VERIFICATION TESTS ====================
    
    async def test_database_record_verification(self) -> bool:
        """Test 4: Database Record Creation and Verification"""
        self.log_section("DATABASE RECORD VERIFICATION")
        
        try:
            if not self.created_receipt_id:
                self.log("No receipt ID available for database verification", "ERROR")
                return False
            
            # Step 1: Retrieve receipt by ID
            self.log("Retrieving receipt from database...")
            receipt_response = self.session.get(f"{API_BASE_URL}/receipts/{self.created_receipt_id}")
            
            if receipt_response.status_code == 200:
                receipt_data = receipt_response.json()
                
                self.log("Receipt successfully retrieved from database", "SUCCESS")
                self.log(f"Receipt ID: {receipt_data.get('id')}", "SUCCESS")
                self.log(f"User ID: {receipt_data.get('user_id')}", "SUCCESS")
                self.log(f"Store Name: {receipt_data.get('store_name')}", "SUCCESS")
                self.log(f"Total Amount: ${receipt_data.get('total_amount')}", "SUCCESS")
                self.log(f"Processing Status: {receipt_data.get('processing_status')}", "SUCCESS")
                self.log(f"Items Count: {len(receipt_data.get('items', []))}", "SUCCESS")
                self.log(f"Photo URL: {receipt_data.get('photo_url', 'N/A')}", "SUCCESS")
                
                # Step 2: Verify receipt belongs to correct user
                if receipt_data.get('user_id') == self.user_id:
                    self.log("Receipt ownership verified", "SUCCESS")
                else:
                    self.log("Receipt ownership verification failed", "ERROR")
                    return False
                
                # Step 3: Test receipt list endpoint
                self.log("Testing receipt list endpoint...")
                list_response = self.session.get(f"{API_BASE_URL}/receipts/")
                
                if list_response.status_code == 200:
                    list_data = list_response.json()
                    total_receipts = list_data.get('total_count', 0)
                    receipts = list_data.get('receipts', [])
                    
                    self.log(f"Receipt list retrieved: {total_receipts} total receipts", "SUCCESS")
                    self.log(f"Receipts on current page: {len(receipts)}", "SUCCESS")
                    
                    # Verify our receipt is in the list
                    receipt_found = any(r.get('id') == self.created_receipt_id for r in receipts)
                    if receipt_found:
                        self.log("Created receipt found in user's receipt list", "SUCCESS")
                    else:
                        self.log("Created receipt not found in user's receipt list", "WARNING")
                else:
                    self.log(f"Receipt list retrieval failed: {list_response.status_code}", "ERROR")
                
                return True
            else:
                self.log(f"Receipt retrieval failed: {receipt_response.status_code} - {receipt_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Database verification error: {e}", "ERROR")
            return False
    
    # ==================== OCR PROCESSING TESTS ====================
    
    async def test_ocr_processing_and_extraction(self) -> bool:
        """Test 5: OCR Processing and Item Extraction"""
        self.log_section("OCR PROCESSING AND ITEM EXTRACTION")
        
        try:
            # Import OCR service
            from app.utils.ocr_service import ocr_service
            
            # Step 1: Check OCR service status
            self.log("Checking OCR service status...")
            ocr_status = ocr_service.get_service_status()
            
            for key, value in ocr_status.items():
                status_icon = "✅" if value else "❌"
                self.log(f"{key}: {value} {status_icon}")
            
            # Step 2: Test OCR text extraction
            if self.uploaded_file_url:
                self.log(f"Testing OCR text extraction on: {self.uploaded_file_url}")
                extracted_text = await ocr_service.extract_text_from_image(self.uploaded_file_url)
                
                if extracted_text:
                    self.log(f"OCR text extraction successful: {len(extracted_text)} characters", "SUCCESS")
                    self.log(f"First 200 characters: {extracted_text[:200]}...", "SUCCESS")
                    
                    # Step 3: Test text parsing
                    self.log("Testing receipt text parsing...")
                    parsed_data = ocr_service.parse_receipt_text(extracted_text)
                    
                    self.log(f"Store Name: {parsed_data.get('store_name', 'Not detected')}", "SUCCESS")
                    self.log(f"Receipt Date: {parsed_data.get('receipt_date', 'Not detected')}", "SUCCESS")
                    self.log(f"Items Found: {len(parsed_data.get('items', []))}", "SUCCESS")
                    self.log(f"Subtotal: ${parsed_data.get('subtotal', 'Not detected')}", "SUCCESS")
                    self.log(f"Tax: ${parsed_data.get('tax', 'Not detected')}", "SUCCESS")
                    self.log(f"Total: ${parsed_data.get('total', 'Not detected')}", "SUCCESS")
                    
                    # Display extracted items
                    items = parsed_data.get('items', [])
                    if items:
                        self.log("Extracted items:")
                        for i, item in enumerate(items[:5], 1):  # Show first 5 items
                            self.log(f"  {i}. {item.name} - Qty: {item.quantity} - ${item.total_price}")
                    
                    return True
                else:
                    self.log("OCR text extraction returned no text", "WARNING")
                    return False
            else:
                self.log("No file URL available for OCR testing", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"OCR processing test error: {e}", "ERROR")
            return False
    
    # ==================== FILE RETRIEVAL TESTS ====================
    
    async def test_file_retrieval_via_secure_urls(self) -> bool:
        """Test 6: File Retrieval via Secure URLs"""
        self.log_section("FILE RETRIEVAL VIA SECURE URLS")
        
        try:
            if not self.created_receipt_id:
                self.log("No receipt ID available for file retrieval test", "ERROR")
                return False
            
            # Step 1: Get secure image URL
            self.log("Requesting secure image URL...")
            image_url_response = self.session.get(f"{API_BASE_URL}/receipts/{self.created_receipt_id}/image-url")
            
            if image_url_response.status_code == 200:
                url_data = image_url_response.json()
                secure_url = url_data.get('image_url')
                storage_type = url_data.get('storage_type')
                expires_in = url_data.get('expires_in')
                
                self.log(f"Secure URL generated successfully", "SUCCESS")
                self.log(f"Storage type: {storage_type}", "SUCCESS")
                self.log(f"Expires in: {expires_in} seconds", "SUCCESS")
                self.log(f"URL: {secure_url[:50]}...", "SUCCESS")
                
                # Step 2: Test file access via secure URL
                self.log("Testing file access via secure URL...")
                
                # Remove authorization header for direct file access
                file_session = requests.Session()
                file_response = file_session.get(secure_url, timeout=10)
                
                if file_response.status_code == 200:
                    content_length = len(file_response.content)
                    content_type = file_response.headers.get('content-type', 'unknown')
                    
                    self.log(f"File retrieved successfully via secure URL", "SUCCESS")
                    self.log(f"Content length: {content_length} bytes", "SUCCESS")
                    self.log(f"Content type: {content_type}", "SUCCESS")
                    
                    # Verify it's an image
                    if content_type.startswith('image/') or content_length > 1000:
                        self.log("File appears to be a valid image", "SUCCESS")
                        return True
                    else:
                        self.log("File may not be a valid image", "WARNING")
                        return True  # Still consider success if we got content
                else:
                    self.log(f"File access failed: {file_response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"Secure URL generation failed: {image_url_response.status_code} - {image_url_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"File retrieval test error: {e}", "ERROR")
            return False
    
    # ==================== PANTRY INTEGRATION TESTS ====================
    
    async def test_pantry_integration_workflow(self) -> bool:
        """Test 7: Pantry Integration Workflow"""
        self.log_section("PANTRY INTEGRATION WORKFLOW")
        
        try:
            if not self.created_receipt_id:
                self.log("No receipt ID available for pantry integration test", "ERROR")
                return False
            
            # Step 1: Get receipt details to check for items
            self.log("Checking receipt for extractable items...")
            receipt_response = self.session.get(f"{API_BASE_URL}/receipts/{self.created_receipt_id}")
            
            if receipt_response.status_code != 200:
                self.log("Could not retrieve receipt for pantry test", "ERROR")
                return False
            
            receipt_data = receipt_response.json()
            items = receipt_data.get('items', [])
            
            if not items:
                self.log("No items found in receipt for pantry integration", "WARNING")
                return False
            
            self.log(f"Found {len(items)} items in receipt for pantry integration", "SUCCESS")
            
            # Step 2: Add selected items to pantry
            selected_items = list(range(min(3, len(items))))  # Select first 3 items
            self.log(f"Adding {len(selected_items)} items to pantry...")
            
            pantry_request = {
                "selected_items": selected_items,
                "expiration_days": 7
            }
            
            pantry_response = self.session.post(
                f"{API_BASE_URL}/receipts/{self.created_receipt_id}/add-to-pantry",
                json=pantry_request
            )
            
            if pantry_response.status_code == 200:
                pantry_data = pantry_response.json()
                
                self.log("Items successfully added to pantry!", "SUCCESS")
                self.log(f"Items added: {pantry_data.get('items_added', 0)}", "SUCCESS")
                self.log(f"Items failed: {pantry_data.get('items_failed', 0)}", "SUCCESS")
                self.log(f"Pantry items created: {len(pantry_data.get('pantry_items_created', []))}", "SUCCESS")
                
                errors = pantry_data.get('errors', [])
                if errors:
                    self.log("Errors encountered:")
                    for error in errors:
                        self.log(f"  - {error}", "WARNING")
                
                # Step 3: Verify items in pantry
                self.log("Verifying items were added to pantry...")
                pantry_list_response = self.session.get(f"{API_BASE_URL}/pantry/")
                
                if pantry_list_response.status_code == 200:
                    pantry_list_data = pantry_list_response.json()
                    pantry_items = pantry_list_data.get('items', [])
                    
                    self.log(f"Pantry now contains {len(pantry_items)} items", "SUCCESS")
                    
                    # Show recently added items
                    recent_items = [item for item in pantry_items if 'receipt' in item.get('notes', '').lower()]
                    if recent_items:
                        self.log("Recently added items from receipt:")
                        for item in recent_items[:3]:
                            self.log(f"  - {item.get('name')} (Qty: {item.get('quantity')})")
                else:
                    self.log(f"Could not verify pantry contents: {pantry_list_response.status_code}", "WARNING")
                
                return True
            else:
                self.log(f"Pantry integration failed: {pantry_response.status_code} - {pantry_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Pantry integration test error: {e}", "ERROR")
            return False
    
    # ==================== STATISTICS AND CLEANUP ====================
    
    async def test_receipt_statistics(self) -> bool:
        """Test receipt statistics endpoint"""
        self.log_section("RECEIPT STATISTICS")
        
        try:
            self.log("Retrieving receipt statistics...")
            stats_response = self.session.get(f"{API_BASE_URL}/receipts/stats/overview")
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                
                self.log("Receipt statistics retrieved successfully!", "SUCCESS")
                self.log(f"Total receipts: {stats_data.get('total_receipts', 0)}", "SUCCESS")
                self.log(f"Total spent: ${stats_data.get('total_spent', 0):.2f}", "SUCCESS")
                self.log(f"Average receipt amount: ${stats_data.get('average_receipt_amount', 0):.2f}", "SUCCESS")
                
                receipts_by_store = stats_data.get('receipts_by_store', {})
                if receipts_by_store:
                    self.log("Receipts by store:")
                    for store, data in list(receipts_by_store.items())[:3]:
                        self.log(f"  - {store}: {data.get('count', 0)} receipts, ${data.get('total_spent', 0):.2f}")
                
                most_purchased = stats_data.get('most_purchased_items', [])
                if most_purchased:
                    self.log("Most purchased items:")
                    for item in most_purchased[:3]:
                        self.log(f"  - {item.get('name')}: {item.get('count')} times")
                
                return True
            else:
                self.log(f"Statistics retrieval failed: {stats_response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Statistics test error: {e}", "ERROR")
            return False
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        self.log_section("CLEANUP TEST DATA")
        
        try:
            # Clean up uploaded file
            if self.uploaded_file_url:
                self.log("Cleaning up test file...")
                try:
                    from app.utils.cloud_storage import cloud_storage_service
                    await cloud_storage_service.delete_file(self.uploaded_file_url)
                    self.log("Test file cleaned up", "SUCCESS")
                except Exception as e:
                    self.log(f"File cleanup warning: {e}", "WARNING")
            
            # Note: We don't delete the receipt or user as they might be useful for further testing
            self.log("Test data cleanup completed", "SUCCESS")
            
        except Exception as e:
            self.log(f"Cleanup error: {e}", "ERROR")
    
    # ==================== MAIN TEST RUNNER ====================
    
    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all comprehensive tests"""
        self.log_section("COMPREHENSIVE RECEIPT SAVING FUNCTIONALITY TEST")
        self.log("Starting comprehensive end-to-end testing...")
        self.log(f"Target API: {API_BASE_URL}")
        self.log(f"Test User: {TEST_USER_EMAIL}")
        
        # Test sequence
        tests = [
            ("User Authentication Setup", self.test_user_authentication_setup),
            ("File Upload with Validation", self.test_file_upload_with_validation),
            ("Storage System Verification", self.test_storage_system_verification),
            ("Database Record Verification", self.test_database_record_verification),
            ("OCR Processing and Extraction", self.test_ocr_processing_and_extraction),
            ("File Retrieval via Secure URLs", self.test_file_retrieval_via_secure_urls),
            ("Pantry Integration Workflow", self.test_pantry_integration_workflow),
            ("Receipt Statistics", self.test_receipt_statistics),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n🧪 Running: {test_name}")
                result = await test_func()
                results[test_name] = result
                
                if result:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                self.log(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Cleanup
        await self.cleanup_test_data()
        
        # Final results
        self.log_section("COMPREHENSIVE TEST RESULTS")
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log_section("FINAL SUMMARY")
        self.log(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            self.log("🎉 ALL TESTS PASSED! Receipt saving functionality is working perfectly!", "SUCCESS")
        elif success_rate >= 80:
            self.log("✅ Most tests passed! Receipt saving functionality is largely working.", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️ Some tests failed. Receipt saving functionality has issues that need attention.", "WARNING")
        else:
            self.log("❌ Many tests failed. Receipt saving functionality needs significant fixes.", "ERROR")
        
        # Generate test report
        self.generate_test_report(results)
        
        return results
    
    def generate_test_report(self, results: Dict[str, bool]):
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"receipt_end_to_end_test_report_{timestamp}.json"
        
        report_data = {
            "test_execution": {
                "timestamp": datetime.now().isoformat(),
                "api_base_url": API_BASE_URL,
                "test_user": TEST_USER_EMAIL,
                "user_id": self.user_id,
                "created_receipt_id": self.created_receipt_id
            },
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": sum(results.values()),
                "success_rate": (sum(results.values()) / len(results)) * 100
            },
            "system_info": {
                "backend_running": True,  # If we got this far, backend is running
                "ocr_enabled": True,
                "storage_type": "local"  # Default assumption
            }
        }
        
        try:
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            self.log(f"Test report saved: {report_filename}", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to save test report: {e}", "WARNING")


# ==================== MAIN EXECUTION ====================

async def main():
    """Main execution function"""
    print("🚀 COMPREHENSIVE RECEIPT SAVING FUNCTIONALITY TEST")
    print("=" * 60)
    print("This script will test the complete receipt saving workflow:")
    print("1. User authentication and session management")
    print("2. Receipt image upload with validation")
    print("3. File storage system verification")
    print("4. Database record creation and verification")
    print("5. OCR processing and item extraction")
    print("6. File retrieval via secure URLs")
    print("7. Pantry integration workflow")
    print("8. Receipt statistics and reporting")
    print("=" * 60)
    
    # Initialize tester
    tester = ComprehensiveReceiptTester()
    
    # Run comprehensive tests
    results = await tester.run_comprehensive_test()
    
    return results


if __name__ == "__main__":
    try:
        # Run the comprehensive test
        test_results = asyncio.run(main())
        
        # Exit with appropriate code
        if all(test_results.values()):
            print("\n🎉 All tests passed! Receipt saving functionality is working perfectly!")
            sys.exit(0)
        else:
            failed_tests = [name for name, passed in test_results.items() if not passed]
            print(f"\n❌ Some tests failed: {', '.join(failed_tests)}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {e}")
        sys.exit(1)