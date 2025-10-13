#!/usr/bin/env python3
"""
Comprehensive test script to validate the 422 error fixes in receipt processing workflow.

This script tests:
1. Receipt upload and processing
2. Receipt detail retrieval
3. Adding receipt items to pantry (main 422 error scenario)
4. Error handling and logging improvements
5. Frontend-backend data flow validation
"""

import asyncio
import aiohttp
import json
import logging
import os
import tempfile
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'receipt_422_fix_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Receipt422FixTester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "detailed_results": {}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result and update statistics"""
        self.test_results["tests_run"] += 1
        if success:
            self.test_results["tests_passed"] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.test_results["tests_failed"] += 1
            logger.error(f"❌ {test_name}: FAILED")
            self.test_results["errors"].append(f"{test_name}: {details.get('error', 'Unknown error')}")
        
        self.test_results["detailed_results"][test_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            **details
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with the API"""
        try:
            # Try to register a test user
            register_data = {
                "email": f"test_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "full_name": "Receipt Test User"
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/register",
                json=register_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    logger.info("✅ Successfully registered and authenticated test user")
                    return True
                elif response.status == 400:
                    # User might already exist, try login
                    logger.info("User might exist, trying login...")
                    return await self.login(register_data["email"], register_data["password"])
                else:
                    logger.error(f"Registration failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def login(self, email: str, password: str) -> bool:
        """Login with existing credentials"""
        try:
            login_data = {
                "username": email,
                "password": password
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/login-form",
                data=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    logger.info("✅ Successfully logged in")
                    return True
                else:
                    logger.error(f"Login failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_receipt_image(self) -> bytes:
        """Create a simple test receipt image"""
        # Create a simple white image with some text-like patterns
        img = Image.new('RGB', (400, 600), color='white')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    async def test_receipt_upload_and_processing(self) -> Optional[str]:
        """Test 1: Upload receipt image and process it"""
        test_name = "Receipt Upload and Processing"
        
        try:
            # Create test image
            image_data = self.create_test_receipt_image()
            
            # Upload receipt
            form_data = aiohttp.FormData()
            form_data.add_field('file', image_data, filename='test_receipt.jpg', content_type='image/jpeg')
            
            async with self.session.post(
                f"{self.base_url}/receipts/upload",
                data=form_data,
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    receipt_id = result.get("receipt_id")
                    
                    self.log_test_result(test_name, True, {
                        "receipt_id": receipt_id,
                        "processing_status": result.get("processing_status"),
                        "items_count": len(result.get("items", [])),
                        "message": result.get("message")
                    })
                    
                    logger.info(f"Receipt uploaded successfully: {receipt_id}")
                    logger.info(f"Processing status: {result.get('processing_status')}")
                    logger.info(f"Items extracted: {len(result.get('items', []))}")
                    
                    return receipt_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": error_text
                    })
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return None
    
    async def test_receipt_detail_retrieval(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Test 2: Retrieve receipt details"""
        test_name = "Receipt Detail Retrieval"
        
        try:
            async with self.session.get(
                f"{self.base_url}/receipts/{receipt_id}",
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    receipt_data = await response.json()
                    
                    # Validate receipt structure
                    required_fields = ["id", "store_name", "receipt_date", "total_amount", "items", "processing_status"]
                    missing_fields = [field for field in required_fields if field not in receipt_data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, {
                            "error": f"Missing required fields: {missing_fields}",
                            "receipt_data": receipt_data
                        })
                        return None
                    
                    self.log_test_result(test_name, True, {
                        "receipt_id": receipt_data["id"],
                        "store_name": receipt_data["store_name"],
                        "items_count": len(receipt_data["items"]),
                        "processing_status": receipt_data["processing_status"],
                        "processed": receipt_data["processing_status"] == "completed"
                    })
                    
                    logger.info(f"Receipt details retrieved: {len(receipt_data['items'])} items")
                    return receipt_data
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": error_text
                    })
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return None
    
    async def test_add_items_to_pantry_success(self, receipt_id: str, receipt_data: Dict[str, Any]) -> bool:
        """Test 3: Successfully add receipt items to pantry (main 422 fix test)"""
        test_name = "Add Items to Pantry - Success Case"
        
        try:
            items = receipt_data.get("items", [])
            if not items:
                self.log_test_result(test_name, False, {
                    "error": "No items in receipt to add to pantry"
                })
                return False
            
            # Test with valid item indices
            selected_items = list(range(min(3, len(items))))  # Select first 3 items or all if less
            
            request_data = {
                "selected_items": selected_items,
                "expiration_days": 7
            }
            
            logger.info(f"Testing add to pantry with valid indices: {selected_items}")
            logger.info(f"Request data: {request_data}")
            
            async with self.session.post(
                f"{self.base_url}/receipts/{receipt_id}/add-to-pantry",
                json=request_data,
                headers=self.get_auth_headers()
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text}")
                
                if response.status == 200:
                    result = await response.json() if response_text else {}
                    
                    self.log_test_result(test_name, True, {
                        "selected_items": selected_items,
                        "items_added": result.get("items_added", 0),
                        "items_failed": result.get("items_failed", 0),
                        "pantry_items_created": result.get("pantry_items_created", []),
                        "errors": result.get("errors", [])
                    })
                    
                    logger.info(f"✅ Successfully added {result.get('items_added', 0)} items to pantry")
                    if result.get("errors"):
                        logger.warning(f"Some errors occurred: {result['errors']}")
                    
                    return True
                else:
                    # This is the main test - we should NOT get 422 errors anymore
                    if response.status == 422:
                        logger.error("🚨 CRITICAL: Still getting 422 errors! Fix not working!")
                    
                    try:
                        error_data = await response.json() if response_text else {}
                    except:
                        error_data = {"detail": response_text}
                    
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": error_data,
                        "selected_items": selected_items,
                        "critical_422_error": response.status == 422
                    })
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_add_items_to_pantry_invalid_indices(self, receipt_id: str, receipt_data: Dict[str, Any]) -> bool:
        """Test 4: Test error handling with invalid item indices"""
        test_name = "Add Items to Pantry - Invalid Indices"
        
        try:
            items = receipt_data.get("items", [])
            items_count = len(items)
            
            # Test with invalid indices (out of range)
            invalid_indices = [items_count, items_count + 1, -1]  # These should be invalid
            
            request_data = {
                "selected_items": invalid_indices,
                "expiration_days": 7
            }
            
            logger.info(f"Testing add to pantry with invalid indices: {invalid_indices}")
            logger.info(f"Items count: {items_count}, so valid indices are 0-{items_count-1}")
            
            async with self.session.post(
                f"{self.base_url}/receipts/{receipt_id}/add-to-pantry",
                json=request_data,
                headers=self.get_auth_headers()
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text}")
                
                # We expect this to fail with proper error handling
                if response.status == 422:
                    try:
                        error_data = await response.json() if response_text else {}
                        error_detail = error_data.get("detail", "")
                        
                        # Check if error message mentions invalid indices
                        if "invalid" in error_detail.lower() and "indices" in error_detail.lower():
                            self.log_test_result(test_name, True, {
                                "status_code": response.status,
                                "error_detail": error_detail,
                                "invalid_indices": invalid_indices,
                                "proper_error_handling": True
                            })
                            logger.info("✅ Proper error handling for invalid indices")
                            return True
                        else:
                            self.log_test_result(test_name, False, {
                                "status_code": response.status,
                                "error_detail": error_detail,
                                "invalid_indices": invalid_indices,
                                "error": "Error message doesn't mention invalid indices"
                            })
                            return False
                    except:
                        error_data = {"detail": response_text}
                        self.log_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Could not parse error response",
                            "raw_response": response_text
                        })
                        return False
                else:
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": f"Expected 422 status for invalid indices, got {response.status}",
                        "response": response_text
                    })
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_add_items_empty_selection(self, receipt_id: str) -> bool:
        """Test 5: Test error handling with empty item selection"""
        test_name = "Add Items to Pantry - Empty Selection"
        
        try:
            request_data = {
                "selected_items": [],  # Empty selection
                "expiration_days": 7
            }
            
            logger.info("Testing add to pantry with empty selection")
            
            async with self.session.post(
                f"{self.base_url}/receipts/{receipt_id}/add-to-pantry",
                json=request_data,
                headers=self.get_auth_headers()
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text}")
                
                # We expect this to fail with proper error handling
                if response.status in [400, 422]:
                    try:
                        error_data = await response.json() if response_text else {}
                        error_detail = error_data.get("detail", "")
                        
                        self.log_test_result(test_name, True, {
                            "status_code": response.status,
                            "error_detail": error_detail,
                            "proper_error_handling": True
                        })
                        logger.info("✅ Proper error handling for empty selection")
                        return True
                    except:
                        self.log_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Could not parse error response",
                            "raw_response": response_text
                        })
                        return False
                else:
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": f"Expected 400/422 status for empty selection, got {response.status}",
                        "response": response_text
                    })
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_frontend_backend_data_flow(self, receipt_id: str, receipt_data: Dict[str, Any]) -> bool:
        """Test 6: Validate frontend-backend data flow format"""
        test_name = "Frontend-Backend Data Flow Validation"
        
        try:
            items = receipt_data.get("items", [])
            if not items:
                self.log_test_result(test_name, False, {
                    "error": "No items in receipt to test data flow"
                })
                return False
            
            # Test the exact format that frontend sends
            frontend_request = {
                "selected_items": [0, 1] if len(items) >= 2 else [0],  # Array of indices
                "expiration_days": 7
            }
            
            logger.info("Testing frontend-backend data flow format")
            logger.info(f"Frontend request format: {frontend_request}")
            
            async with self.session.post(
                f"{self.base_url}/receipts/{receipt_id}/add-to-pantry",
                json=frontend_request,
                headers=self.get_auth_headers()
            ) as response:
                
                response_text = await response.text()
                
                # Validate request was processed correctly
                if response.status == 200:
                    result = await response.json() if response_text else {}
                    
                    # Validate response format
                    expected_fields = ["receipt_id", "items_added", "items_failed", "pantry_items_created", "errors"]
                    missing_fields = [field for field in expected_fields if field not in result]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, {
                            "error": f"Response missing fields: {missing_fields}",
                            "response": result
                        })
                        return False
                    
                    self.log_test_result(test_name, True, {
                        "request_format": frontend_request,
                        "response_format": result,
                        "data_flow_valid": True,
                        "items_processed": result.get("items_added", 0)
                    })
                    
                    logger.info("✅ Frontend-backend data flow validation successful")
                    return True
                else:
                    self.log_test_result(test_name, False, {
                        "status_code": response.status,
                        "error": response_text,
                        "request_format": frontend_request
                    })
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting comprehensive receipt 422 fix validation tests")
        
        # Step 1: Authenticate
        if not await self.authenticate():
            logger.error("❌ Authentication failed - cannot proceed with tests")
            return self.test_results
        
        # Step 2: Upload and process receipt
        receipt_id = await self.test_receipt_upload_and_processing()
        if not receipt_id:
            logger.error("❌ Receipt upload failed - cannot proceed with remaining tests")
            return self.test_results
        
        # Step 3: Retrieve receipt details
        receipt_data = await self.test_receipt_detail_retrieval(receipt_id)
        if not receipt_data:
            logger.error("❌ Receipt detail retrieval failed - cannot proceed with remaining tests")
            return self.test_results
        
        # Step 4: Test successful add to pantry (main 422 fix test)
        await self.test_add_items_to_pantry_success(receipt_id, receipt_data)
        
        # Step 5: Test error handling with invalid indices
        await self.test_add_items_to_pantry_invalid_indices(receipt_id, receipt_data)
        
        # Step 6: Test error handling with empty selection
        await self.test_add_items_empty_selection(receipt_id)
        
        # Step 7: Test frontend-backend data flow
        await self.test_frontend_backend_data_flow(receipt_id, receipt_data)
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        results = self.test_results
        
        report = f"""
# Receipt 422 Error Fix Validation Report

**Test Execution Time:** {results['timestamp']}
**Total Tests:** {results['tests_run']}
**Passed:** {results['tests_passed']}
**Failed:** {results['tests_failed']}
**Success Rate:** {(results['tests_passed'] / results['tests_run'] * 100) if results['tests_run'] > 0 else 0:.1f}%

## Test Results Summary

"""
        
        for test_name, details in results['detailed_results'].items():
            status = "✅ PASSED" if details['success'] else "❌ FAILED"
            report += f"### {test_name}: {status}\n"
            report += f"- **Timestamp:** {details['timestamp']}\n"
            
            if details['success']:
                # Add success details
                for key, value in details.items():
                    if key not in ['success', 'timestamp']:
                        report += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            else:
                # Add error details
                report += f"- **Error:** {details.get('error', 'Unknown error')}\n"
                for key, value in details.items():
                    if key not in ['success', 'timestamp', 'error']:
                        report += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            
            report += "\n"
        
        if results['errors']:
            report += "## Errors Encountered\n\n"
            for error in results['errors']:
                report += f"- {error}\n"
            report += "\n"
        
        # Critical analysis
        report += "## Critical Analysis\n\n"
        
        # Check if 422 errors are fixed
        pantry_tests = [name for name in results['detailed_results'].keys() if 'pantry' in name.lower()]
        pantry_success = all(results['detailed_results'][name]['success'] for name in pantry_tests if 'success' in name.lower())
        
        if pantry_success:
            report += "✅ **422 Error Fix Status:** SUCCESSFUL - No 422 errors detected in pantry operations\n"
        else:
            report += "❌ **422 Error Fix Status:** FAILED - 422 errors still occurring\n"
        
        # Check data flow validation
        data_flow_test = results['detailed_results'].get('Frontend-Backend Data Flow Validation', {})
        if data_flow_test.get('success'):
            report += "✅ **Data Flow Validation:** PASSED - Frontend-backend communication working correctly\n"
        else:
            report += "❌ **Data Flow Validation:** FAILED - Issues with frontend-backend communication\n"
        
        # Check error handling
        error_tests = [name for name in results['detailed_results'].keys() if 'invalid' in name.lower() or 'empty' in name.lower()]
        error_handling_success = all(results['detailed_results'][name]['success'] for name in error_tests)
        
        if error_handling_success:
            report += "✅ **Error Handling:** IMPROVED - Proper validation and error messages\n"
        else:
            report += "❌ **Error Handling:** NEEDS WORK - Error handling could be improved\n"
        
        report += f"\n## Recommendations\n\n"
        
        if results['tests_failed'] == 0:
            report += "🎉 All tests passed! The 422 error fixes are working correctly.\n"
        else:
            report += "⚠️ Some tests failed. Review the detailed results above and address the issues.\n"
            
            # Specific recommendations based on failures
            for test_name, details in results['detailed_results'].items():
                if not details['success']:
                    if '422' in str(details.get('status_code', '')):
                        report += f"- **Critical:** {test_name} still returning 422 errors - fix not complete\n"
                    elif 'pantry' in test_name.lower():
                        report += f"- **High Priority:** {test_name} failed - pantry integration needs attention\n"
                    else:
                        report += f"- **Medium Priority:** {test_name} failed - review implementation\n"
        
        return report

async def main():
    """Main test execution function"""
    async with Receipt422FixTester() as tester:
        results = await tester.run_all_tests()
        
        # Generate and save report
        report = tester.generate_report()
        
        # Save results to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        with open(f"receipt_422_fix_test_results_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save markdown report
        with open(f"receipt_422_fix_test_report_{timestamp}.md", "w") as f:
            f.write(report)
        
        # Print summary
        print("\n" + "="*80)
        print("RECEIPT 422 FIX VALIDATION TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {results['tests_run']}")
        print(f"Passed: {results['tests_passed']}")
        print(f"Failed: {results['tests_failed']}")
        print(f"Success Rate: {(results['tests_passed'] / results['tests_run'] * 100) if results['tests_run'] > 0 else 0:.1f}%")
        
        if results['tests_failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! 422 error fixes are working correctly.")
        else:
            print(f"\n⚠️ {results['tests_failed']} tests failed. Check the detailed report.")
        
        print(f"\nDetailed report saved to: receipt_422_fix_test_report_{timestamp}.md")
        print(f"JSON results saved to: receipt_422_fix_test_results_{timestamp}.json")
        print("="*80)
        
        return results

if __name__ == "__main__":
    asyncio.run(main())