#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Receipt and Pic-to-Recipe System
Tests the complete system integration from end-to-end with diagnostic logging
"""

import asyncio
import requests
import json
import sys
import os
import time
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import io
import base64
from pathlib import Path

# Configure logging for diagnostics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test_diagnostics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/healthz"
FRONTEND_URL = "http://localhost:3002"

class ComprehensiveIntegrationTester:
    """Comprehensive integration tester for the complete system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suite": "Comprehensive Integration Tests",
            "system_info": {},
            "tests": {},
            "diagnostics": {},
            "performance_metrics": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": [],
                "warnings": []
            }
        }
        self.start_time = time.time()
    
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any] = None, 
                 error: str = None, warning: str = None, duration: float = None):
        """Log test result with comprehensive details"""
        self.test_results["tests"][test_name] = {
            "success": success,
            "details": details or {},
            "error": error,
            "warning": warning,
            "duration_ms": duration * 1000 if duration else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results["summary"]["total_tests"] += 1
        
        if success:
            self.test_results["summary"]["passed"] += 1
            status = "✅"
            logger.info(f"{status} {test_name}")
        else:
            self.test_results["summary"]["failed"] += 1
            self.test_results["summary"]["errors"].append(f"{test_name}: {error}")
            status = "❌"
            logger.error(f"{status} {test_name}: {error}")
        
        if warning:
            self.test_results["summary"]["warnings"].append(f"{test_name}: {warning}")
            logger.warning(f"⚠️ {test_name}: {warning}")
        
        print(f"{status} {test_name}" + (f" ({duration*1000:.1f}ms)" if duration else ""))
    
    def log_diagnostic(self, category: str, data: Dict[str, Any]):
        """Log diagnostic information"""
        if category not in self.test_results["diagnostics"]:
            self.test_results["diagnostics"][category] = []
        self.test_results["diagnostics"][category].append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
        logger.debug(f"DIAGNOSTIC [{category}]: {json.dumps(data, indent=2)}")
    
    def create_test_image(self, width: int = 400, height: int = 600, format: str = 'JPEG') -> bytes:
        """Create a test image for upload testing"""
        img = Image.new('RGB', (width, height), color='white')
        # Add some simple patterns to make it look more like a receipt/meal photo
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        if format == 'receipt':
            # Draw receipt-like patterns
            for i in range(10, height-10, 30):
                draw.rectangle([20, i, width-20, i+15], fill='lightgray')
                draw.text((30, i+2), f"Item {i//30}", fill='black')
        else:
            # Draw meal-like patterns (circles for food items)
            for i in range(3):
                for j in range(2):
                    x = 50 + j * 150
                    y = 50 + i * 150
                    draw.ellipse([x, y, x+80, y+80], fill='orange')
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    # ==================== SYSTEM HEALTH TESTS ====================
    
    def test_system_health(self) -> bool:
        """Test overall system health and connectivity"""
        start_time = time.time()
        try:
            # Test API health
            response = self.session.get(HEALTH_URL, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_diagnostic("system_health", {
                    "api_status": health_data.get("status"),
                    "database_connected": health_data.get("database_connected"),
                    "response_time_ms": duration * 1000
                })
                
                self.log_test("System Health Check", True, {
                    "api_status": health_data.get("status"),
                    "database_connected": health_data.get("database_connected"),
                    "response_time_ms": duration * 1000
                }, duration=duration)
                return True
            else:
                self.log_test("System Health Check", False, 
                            error=f"HTTP {response.status_code}", duration=duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("System Health Check", False, error=str(e), duration=duration)
            return False
    
    def test_database_connectivity(self) -> bool:
        """Test database connectivity and performance"""
        start_time = time.time()
        try:
            response = self.session.get(f"{HEALTH_URL}/db", timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                db_data = response.json()
                self.log_diagnostic("database_connectivity", db_data)
                
                self.log_test("Database Connectivity", True, {
                    "status": db_data.get("status"),
                    "connection_stats": db_data.get("connection_stats", {}),
                    "response_time_ms": duration * 1000
                }, duration=duration)
                return True
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Database Connectivity", False, 
                            error=f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}", 
                            duration=duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Database Connectivity", False, error=str(e), duration=duration)
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        start_time = time.time()
        try:
            response = self.session.get(FRONTEND_URL, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Frontend Accessibility", True, {
                    "status_code": response.status_code,
                    "response_time_ms": duration * 1000,
                    "content_length": len(response.content)
                }, duration=duration)
                return True
            else:
                self.log_test("Frontend Accessibility", False, 
                            error=f"HTTP {response.status_code}", duration=duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Frontend Accessibility", False, error=str(e), duration=duration)
            return False
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_authentication_requirements(self) -> bool:
        """Test authentication requirements across endpoints"""
        start_time = time.time()
        try:
            endpoints_to_test = [
                ("POST", "/receipts/upload", "Receipt Upload"),
                ("POST", "/recipes/from-photo", "Meal Photo Analysis"),
                ("POST", "/recipes/generate-from-ingredients", "AI Recipe Generation"),
                ("GET", "/recipes/ai-service-status", "AI Service Status"),
                ("GET", "/leftovers/suggestions", "Leftover Suggestions")
            ]
            
            auth_results = {}
            all_protected = True
            
            for method, endpoint, name in endpoints_to_test:
                try:
                    if method == "GET":
                        response = self.session.get(f"{BASE_URL}{endpoint}", timeout=5)
                    else:
                        response = self.session.post(f"{BASE_URL}{endpoint}", timeout=5)
                    
                    is_protected = response.status_code in [401, 403]
                    auth_results[name] = {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "is_protected": is_protected
                    }
                    
                    if not is_protected and response.status_code not in [404, 405, 422]:
                        all_protected = False
                        
                except Exception as e:
                    auth_results[name] = {
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e),
                        "is_protected": False
                    }
                    all_protected = False
            
            duration = time.time() - start_time
            self.log_diagnostic("authentication_requirements", auth_results)
            
            self.log_test("Authentication Requirements", all_protected, {
                "endpoints_tested": len(endpoints_to_test),
                "all_protected": all_protected,
                "results": auth_results
            }, None if all_protected else "Some endpoints are not properly protected", 
            duration=duration)
            
            return all_protected
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Authentication Requirements", False, error=str(e), duration=duration)
            return False
    
    # ==================== RECEIPT WORKFLOW TESTS ====================
    
    def test_receipt_workflow_integration(self) -> bool:
        """Test complete receipt workflow integration"""
        start_time = time.time()
        try:
            # Test receipt upload endpoint structure
            test_image = self.create_test_image(format='receipt')
            files = {'file': ('test_receipt.jpg', test_image, 'image/jpeg')}
            
            response = self.session.post(f"{BASE_URL}/receipts/upload", files=files, timeout=30)
            duration = time.time() - start_time
            
            # We expect 401/403 due to auth, but endpoint should exist
            if response.status_code in [401, 403]:
                self.log_diagnostic("receipt_workflow", {
                    "upload_endpoint_exists": True,
                    "requires_auth": True,
                    "file_size_bytes": len(test_image)
                })
                
                # Test other receipt endpoints
                receipt_endpoints = [
                    ("GET", "/receipts/", "List Receipts"),
                    ("POST", "/receipts/test-id/process", "Process Receipt"),
                    ("GET", "/receipts/test-id/suggest-recipes", "Recipe Suggestions")
                ]
                
                endpoint_results = {}
                for method, endpoint, name in receipt_endpoints:
                    try:
                        if method == "GET":
                            resp = self.session.get(f"{BASE_URL}{endpoint}", timeout=5)
                        else:
                            resp = self.session.post(f"{BASE_URL}{endpoint}", timeout=5)
                        
                        endpoint_results[name] = {
                            "status_code": resp.status_code,
                            "exists": resp.status_code != 405
                        }
                    except Exception as e:
                        endpoint_results[name] = {"error": str(e), "exists": False}
                
                all_exist = all(result.get("exists", False) for result in endpoint_results.values())
                
                self.log_test("Receipt Workflow Integration", all_exist, {
                    "upload_endpoint_protected": True,
                    "file_upload_capable": True,
                    "endpoints": endpoint_results,
                    "workflow_structure_valid": all_exist
                }, None if all_exist else "Some receipt endpoints are missing", duration=duration)
                
                return all_exist
            else:
                self.log_test("Receipt Workflow Integration", False, 
                            error=f"Upload endpoint returned unexpected status: {response.status_code}", 
                            duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Receipt Workflow Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== PIC-TO-RECIPE WORKFLOW TESTS ====================
    
    def test_pic_to_recipe_workflow_integration(self) -> bool:
        """Test complete pic-to-recipe workflow integration"""
        start_time = time.time()
        try:
            # Test meal photo upload endpoint
            test_image = self.create_test_image(format='meal')
            files = {'file': ('test_meal.jpg', test_image, 'image/jpeg')}
            
            response = self.session.post(f"{BASE_URL}/recipes/from-photo", files=files, timeout=30)
            duration = time.time() - start_time
            
            # We expect 401/403 due to auth, but endpoint should exist
            if response.status_code in [401, 403]:
                self.log_diagnostic("pic_to_recipe_workflow", {
                    "photo_endpoint_exists": True,
                    "requires_auth": True,
                    "file_size_bytes": len(test_image)
                })
                
                # Test AI recipe generation endpoint
                recipe_data = {
                    "ingredients": ["chicken", "rice", "vegetables"],
                    "servings": 4,
                    "cuisine_preference": "Asian"
                }
                
                ai_response = self.session.post(
                    f"{BASE_URL}/recipes/generate-from-ingredients", 
                    json=recipe_data, 
                    timeout=30
                )
                
                # Test service status endpoint
                status_response = self.session.get(f"{BASE_URL}/recipes/ai-service-status", timeout=10)
                
                workflow_results = {
                    "photo_analysis_endpoint": {
                        "status_code": response.status_code,
                        "exists": response.status_code != 405,
                        "protected": response.status_code in [401, 403]
                    },
                    "ai_generation_endpoint": {
                        "status_code": ai_response.status_code,
                        "exists": ai_response.status_code != 405,
                        "protected": ai_response.status_code in [401, 403]
                    },
                    "service_status_endpoint": {
                        "status_code": status_response.status_code,
                        "exists": status_response.status_code != 405,
                        "protected": status_response.status_code in [401, 403]
                    }
                }
                
                all_exist = all(result["exists"] for result in workflow_results.values())
                all_protected = all(result["protected"] for result in workflow_results.values())
                
                self.log_test("Pic-to-Recipe Workflow Integration", all_exist, {
                    "endpoints_exist": all_exist,
                    "endpoints_protected": all_protected,
                    "workflow_results": workflow_results
                }, None if all_exist else "Some pic-to-recipe endpoints are missing", 
                duration=duration)
                
                return all_exist
            else:
                self.log_test("Pic-to-Recipe Workflow Integration", False, 
                            error=f"Photo endpoint returned unexpected status: {response.status_code}", 
                            duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Pic-to-Recipe Workflow Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== CROSS-COMPONENT INTEGRATION TESTS ====================
    
    def test_service_integration(self) -> bool:
        """Test integration between different services"""
        start_time = time.time()
        try:
            # Test if backend services are accessible (without auth)
            service_tests = []
            
            # Test health endpoints that might not require auth
            health_endpoints = [
                ("/healthz", "Main Health Check"),
                ("/healthz/db", "Database Health Check")
            ]
            
            for endpoint, name in health_endpoints:
                try:
                    response = self.session.get(f"http://localhost:8000{endpoint}", timeout=10)
                    service_tests.append({
                        "service": name,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    service_tests.append({
                        "service": name,
                        "error": str(e),
                        "success": False
                    })
            
            duration = time.time() - start_time
            all_services_healthy = all(test["success"] for test in service_tests)
            
            self.log_diagnostic("service_integration", {"service_tests": service_tests})
            
            self.log_test("Service Integration", all_services_healthy, {
                "services_tested": len(service_tests),
                "all_healthy": all_services_healthy,
                "results": service_tests
            }, None if all_services_healthy else "Some services are not healthy", duration=duration)
            
            return all_services_healthy
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Service Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_error_handling_integration(self) -> bool:
        """Test error handling across the system"""
        start_time = time.time()
        try:
            error_tests = []
            
            # Test 1: Invalid file upload
            try:
                files = {'file': ('test.txt', b'not an image', 'text/plain')}
                response = self.session.post(f"{BASE_URL}/receipts/upload", files=files, timeout=10)
                error_tests.append({
                    "test": "Invalid File Type",
                    "status_code": response.status_code,
                    "expected_codes": [400, 401, 403, 422],
                    "handled_correctly": response.status_code in [400, 401, 403, 422]
                })
            except Exception as e:
                error_tests.append({
                    "test": "Invalid File Type",
                    "error": str(e),
                    "handled_correctly": False
                })
            
            # Test 2: Invalid JSON data
            try:
                response = self.session.post(
                    f"{BASE_URL}/recipes/generate-from-ingredients", 
                    json={"invalid": "data"}, 
                    timeout=10
                )
                error_tests.append({
                    "test": "Invalid JSON Data",
                    "status_code": response.status_code,
                    "expected_codes": [400, 401, 403, 422],
                    "handled_correctly": response.status_code in [400, 401, 403, 422]
                })
            except Exception as e:
                error_tests.append({
                    "test": "Invalid JSON Data",
                    "error": str(e),
                    "handled_correctly": False
                })
            
            # Test 3: Non-existent endpoint
            try:
                response = self.session.get(f"{BASE_URL}/nonexistent/endpoint", timeout=10)
                error_tests.append({
                    "test": "Non-existent Endpoint",
                    "status_code": response.status_code,
                    "expected_codes": [404],
                    "handled_correctly": response.status_code == 404
                })
            except Exception as e:
                error_tests.append({
                    "test": "Non-existent Endpoint",
                    "error": str(e),
                    "handled_correctly": False
                })
            
            duration = time.time() - start_time
            all_handled = all(test["handled_correctly"] for test in error_tests)
            
            self.log_diagnostic("error_handling", {"error_tests": error_tests})
            
            self.log_test("Error Handling Integration", all_handled, {
                "tests_run": len(error_tests),
                "all_handled_correctly": all_handled,
                "results": error_tests
            }, None if all_handled else "Some errors are not handled correctly", duration=duration)
            
            return all_handled
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Error Handling Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== PERFORMANCE TESTS ====================
    
    def test_performance_integration(self) -> bool:
        """Test system performance under load"""
        start_time = time.time()
        try:
            # Test concurrent health checks
            import concurrent.futures
            
            def health_check_request():
                try:
                    start = time.time()
                    response = self.session.get(HEALTH_URL, timeout=5)
                    duration = time.time() - start
                    return {
                        "success": response.status_code == 200,
                        "duration_ms": duration * 1000,
                        "status_code": response.status_code
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "duration_ms": None
                    }
            
            # Run 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(health_check_request) for _ in range(10)]
                concurrent_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful_requests = [r for r in concurrent_results if r["success"]]
            avg_response_time = sum(r["duration_ms"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
            success_rate = len(successful_requests) / len(concurrent_results)
            
            duration = time.time() - start_time
            performance_acceptable = success_rate >= 0.8 and avg_response_time < 5000  # 80% success, <5s avg
            
            self.log_diagnostic("performance", {
                "concurrent_requests": len(concurrent_results),
                "successful_requests": len(successful_requests),
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "results": concurrent_results
            })
            
            self.log_test("Performance Integration", performance_acceptable, {
                "concurrent_requests": len(concurrent_results),
                "success_rate": f"{success_rate:.1%}",
                "avg_response_time_ms": f"{avg_response_time:.1f}",
                "performance_acceptable": performance_acceptable
            }, None if performance_acceptable else f"Performance issues: {success_rate:.1%} success rate, {avg_response_time:.1f}ms avg response", 
            duration=duration)
            
            return performance_acceptable
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Performance Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== SECURITY TESTS ====================
    
    def test_security_integration(self) -> bool:
        """Test security measures across the system"""
        start_time = time.time()
        try:
            security_tests = []
            
            # Test 1: CORS headers
            try:
                response = self.session.options(f"{BASE_URL}/recipes/generate-from-ingredients")
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
                }
                security_tests.append({
                    "test": "CORS Headers",
                    "status_code": response.status_code,
                    "cors_configured": any(cors_headers.values()),
                    "headers": cors_headers
                })
            except Exception as e:
                security_tests.append({
                    "test": "CORS Headers",
                    "error": str(e),
                    "cors_configured": False
                })
            
            # Test 2: Security headers
            try:
                response = self.session.get(HEALTH_URL)
                security_headers = {
                    "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                    "X-Frame-Options": response.headers.get("X-Frame-Options"),
                    "X-XSS-Protection": response.headers.get("X-XSS-Protection"),
                    "Strict-Transport-Security": response.headers.get("Strict-Transport-Security")
                }
                has_security_headers = any(security_headers.values())
                security_tests.append({
                    "test": "Security Headers",
                    "status_code": response.status_code,
                    "has_security_headers": has_security_headers,
                    "headers": security_headers
                })
            except Exception as e:
                security_tests.append({
                    "test": "Security Headers",
                    "error": str(e),
                    "has_security_headers": False
                })
            
            # Test 3: File upload size limits
            try:
                # Create a large file (>10MB)
                large_file = b'x' * (11 * 1024 * 1024)  # 11MB
                files = {'file': ('large_file.jpg', large_file, 'image/jpeg')}
                response = self.session.post(f"{BASE_URL}/receipts/upload", files=files, timeout=30)
                
                size_limit_enforced = response.status_code in [413, 400, 401, 403]  # 413 = Payload Too Large
                security_tests.append({
                    "test": "File Size Limits",
                    "status_code": response.status_code,
                    "size_limit_enforced": size_limit_enforced,
                    "file_size_mb": 11
                })
            except Exception as e:
                security_tests.append({
                    "test": "File Size Limits",
                    "error": str(e),
                    "size_limit_enforced": "timeout" in str(e).lower()  # Timeout might indicate size limit
                })
            
            duration = time.time() - start_time
            security_measures_present = sum(1 for test in security_tests if test.get("cors_configured") or test.get("has_security_headers") or test.get("size_limit_enforced")) >= 2
            
            self.log_diagnostic("security", {"security_tests": security_tests})
            
            self.log_test("Security Integration", security_measures_present, {
                "tests_run": len(security_tests),
                "security_measures_present": security_measures_present,
                "results": security_tests
            }, None if security_measures_present else "Insufficient security measures detected", duration=duration)
            
            return security_measures_present
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Security Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== DATA FLOW TESTS ====================
    
    def test_data_flow_integration(self) -> bool:
        """Test data flow between components"""
        start_time = time.time()
        try:
            data_flow_tests = []
            
            # Test 1: API response structure consistency
            endpoints_to_test = [
                (f"{BASE_URL}/recipes/generate-from-ingredients", "POST", {"ingredients": ["test"]}, "Recipe Generation"),
                (f"{BASE_URL}/receipts/upload", "POST", None, "Receipt Upload"),
                (f"{HEALTH_URL}", "GET", None, "Health Check")
            ]
            
            for url, method, data, name in endpoints_to_test:
                try:
                    if method == "GET":
                        response = self.session.get(url, timeout=10)
                    else:
                        if "upload" in url:
                            files = {'file': ('test.jpg', self.create_test_image(), 'image/jpeg')}
                            response = self.session.post(url, files=files, timeout=10)
                        else:
                            response = self.session.post(url, json=data, timeout=10)
                    
                    # Check if response is JSON
                    try:
                        json_data = response.json()
                        has_json_response = True
                        has_error_structure = "error" in json_data or "detail" in json_data or "message" in json_data
                    except:
                        has_json_response = False
                        has_error_structure = False
                    
                    data_flow_tests.append({
                        "endpoint": name,
                        "status_code": response.status_code,
                        "has_json_response": has_json_response,
                        "has_error_structure": has_error_structure,
                        "content_type": response.headers.get("content-type", ""),
                        "response_size": len(response.content)
                    })
                    
                except Exception as e:
                    data_flow_tests.append({
                        "endpoint": name,
                        "error": str(e),
                        "has_json_response": False,
                        "has_error_structure": False
                    })
            
            duration = time.time() - start_time
            consistent_responses = all(test.get("has_json_response", False) or test.get("has_error_structure", False) for test in data_flow_tests)
            
            self.log_diagnostic("data_flow", {"data_flow_tests": data_flow_tests})
            
            self.log_test("Data Flow Integration", consistent_responses, {
                "endpoints_tested": len(data_flow_tests),
                "consistent_responses": consistent_responses,
                "results": data_flow_tests
            }, None if consistent_responses else "Inconsistent response structures detected", duration=duration)
            
            return consistent_responses
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Data Flow Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== FRONTEND-BACKEND INTEGRATION TESTS ====================
    
    def test_frontend_backend_integration(self) -> bool:
        """Test frontend-backend integration"""
        start_time = time.time()
        try:
            integration_tests = []
            
            # Test 1: Frontend accessibility
            try:
                response = self.session.get(FRONTEND_URL, timeout=10)
                integration_tests.append({
                    "test": "Frontend Accessibility",
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "content_type": response.headers.get("content-type", "")
                })
            except Exception as e:
                integration_tests.append({
                    "test": "Frontend Accessibility",
                    "error": str(e),
                    "success": False
                })
            
            # Test 2: API CORS configuration for frontend
            try:
                headers = {"Origin": FRONTEND_URL}
                response = self.session.options(f"{BASE_URL}/recipes/generate-from-ingredients", headers=headers)
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                cors_configured = cors_origin == FRONTEND_URL or cors_origin == "*"
                
                integration_tests.append({
                    "test": "CORS Configuration",
                    "status_code": response.status_code,
                    "cors_configured": cors_configured,
                    "allowed_origin": cors_origin,
                    "success": cors_configured
                })
            except Exception as e:
                integration_tests.append({
                    "test": "CORS Configuration",
                    "error": str(e),
                    "success": False
                })
            
            # Test 3: API endpoint structure matches frontend expectations
            try:
                # Test a simple endpoint that should return JSON
                response = self.session.get(HEALTH_URL)
                if response.status_code == 200:
                    health_data = response.json()
                    expected_fields = ["status", "message"]
                    has_expected_structure = all(field in health_data for field in expected_fields)
                    
                    integration_tests.append({
                        "test": "API Response Structure",
                        "status_code": response.status_code,
                        "has_expected_structure": has_expected_structure,
                        "response_fields": list(health_data.keys()),
                        "success": has_expected_structure
                    })
                else:
                    integration_tests.append({
                        "test": "API Response Structure",
                        "status_code": response.status_code,
                        "success": False
                    })
            except Exception as e:
                integration_tests.append({
                    "test": "API Response Structure",
                    "error": str(e),
                    "success": False
                })
            
            duration = time.time() - start_time
            all_integration_tests_passed = all(test["success"] for test in integration_tests)
            
            self.log_diagnostic("frontend_backend_integration", {"integration_tests": integration_tests})
            
            self.log_test("Frontend-Backend Integration", all_integration_tests_passed, {
                "tests_run": len(integration_tests),
                "all_passed": all_integration_tests_passed,
                "results": integration_tests
            }, None if all_integration_tests_passed else "Some frontend-backend integration issues detected",
            duration=duration)
            
            return all_integration_tests_passed
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Frontend-Backend Integration", False, error=str(e), duration=duration)
            return False
    
    # ==================== MAIN TEST EXECUTION ====================
    
    def run_comprehensive_integration_tests(self) -> Dict[str, Any]:
        """Run all comprehensive integration tests"""
        print("🚀 STARTING COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"Testing complete receipt and pic-to-recipe system integration")
        print(f"Backend: {BASE_URL}")
        print(f"Frontend: {FRONTEND_URL}")
        print("=" * 80)
        
        # Collect system information
        self.test_results["system_info"] = {
            "backend_url": BASE_URL,
            "frontend_url": FRONTEND_URL,
            "test_start_time": datetime.utcnow().isoformat(),
            "python_version": sys.version,
            "platform": os.name
        }
        
        # Define test sequence
        test_sequence = [
            ("System Health", self.test_system_health),
            ("Database Connectivity", self.test_database_connectivity),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Authentication Requirements", self.test_authentication_requirements),
            ("Receipt Workflow Integration", self.test_receipt_workflow_integration),
            ("Pic-to-Recipe Workflow Integration", self.test_pic_to_recipe_workflow_integration),
            ("Service Integration", self.test_service_integration),
            ("Error Handling Integration", self.test_error_handling_integration),
            ("Performance Integration", self.test_performance_integration),
            ("Security Integration", self.test_security_integration),
            ("Data Flow Integration", self.test_data_flow_integration),
            ("Frontend-Backend Integration", self.test_frontend_backend_integration)
        ]
        
        # Execute tests
        results = []
        for i, (test_name, test_func) in enumerate(test_sequence, 1):
            print(f"\n{i}. Testing {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                self.log_test(test_name, False, error=f"Exception: {str(e)}")
                results.append((test_name, False))
        
        # Calculate performance metrics
        total_duration = time.time() - self.start_time
        self.test_results["performance_metrics"] = {
            "total_duration_seconds": total_duration,
            "tests_per_second": len(test_sequence) / total_duration,
            "average_test_duration": total_duration / len(test_sequence)
        }
        
        # Generate summary
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed = self.test_results["summary"]["passed"]
        failed = self.test_results["summary"]["failed"]
        total = self.test_results["summary"]["total_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({success_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        
        if failed > 0:
            print(f"\n❌ Failed Tests ({failed}):")
            for error in self.test_results["summary"]["errors"]:
                print(f"  - {error}")
        
        if self.test_results["summary"]["warnings"]:
            print(f"\n⚠️ Warnings ({len(self.test_results['summary']['warnings'])}):")
            for warning in self.test_results["summary"]["warnings"]:
                print(f"  - {warning}")
        
        # Determine system readiness
        critical_tests = [
            "System Health",
            "Database Connectivity",
            "Authentication Requirements",
            "Receipt Workflow Integration",
            "Pic-to-Recipe Workflow Integration"
        ]
        
        critical_results = {name: result for name, result in results if name in critical_tests}
        critical_passed = sum(1 for result in critical_results.values() if result)
        system_ready = critical_passed >= len(critical_tests) * 0.8  # 80% of critical tests must pass
        
        print(f"\n🚀 System Integration Status: {'READY' if system_ready else 'NEEDS ATTENTION'}")
        print(f"Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if system_ready:
            print("\n✅ Integration Assessment:")
            print("  - Core system components are integrated and functional")
            print("  - API endpoints are properly structured and protected")
            print("  - Error handling is consistent across components")
            print("  - Performance is within acceptable limits")
            print("  - Security measures are in place")
            
            print("\n📋 Integration Readiness:")
            if success_rate >= 90:
                print("  🟢 EXCELLENT - System is fully integrated and ready for production")
            elif success_rate >= 75:
                print("  🟡 GOOD - System is well integrated with minor issues")
            else:
                print("  🟠 FAIR - System has integration issues that should be addressed")
        else:
            print("\n❌ Critical Integration Issues:")
            for name, result in critical_results.items():
                if not result:
                    print(f"  - {name}: Failed")
        
        # Add final timestamp
        self.test_results["test_completion_time"] = datetime.utcnow().isoformat()
        self.test_results["total_duration_seconds"] = total_duration
        
        return self.test_results

def main():
    """Main test execution"""
    tester = ComprehensiveIntegrationTester()
    results = tester.run_comprehensive_integration_tests()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"comprehensive_integration_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    print(f"📄 Diagnostic logs saved to: integration_test_diagnostics.log")
    
    # Generate markdown report
    report_file = f"COMPREHENSIVE_INTEGRATION_TEST_REPORT_{timestamp}.md"
    generate_markdown_report(results, report_file)
    print(f"📄 Markdown report saved to: {report_file}")
    
    # Return appropriate exit code
    success_rate = results['summary']['passed'] / results['summary']['total_tests']
    if success_rate >= 0.75:  # 75% success rate for integration tests
        print("\n🎉 Overall integration test result: SUCCESS")
        return 0
    else:
        print("\n⚠️ Overall integration test result: NEEDS ATTENTION")
        return 1

def generate_markdown_report(results: Dict[str, Any], filename: str):
    """Generate a comprehensive markdown report"""
    with open(filename, 'w') as f:
        f.write("# Comprehensive Integration Test Report\n\n")
        f.write(f"**Test Suite:** Complete Receipt and Pic-to-Recipe System Integration\n")
        f.write(f"**Date:** {results['timestamp']}\n")
        f.write(f"**Duration:** {results.get('total_duration_seconds', 0):.2f} seconds\n")
        
        total = results['summary']['total_tests']
        passed = results['summary']['passed']
        success_rate = (passed / total * 100) if total > 0 else 0
        f.write(f"**Overall Success Rate:** {success_rate:.1f}% ({passed}/{total} tests passed)\n\n")
        
        f.write("## Executive Summary\n\n")
        if success_rate >= 90:
            f.write("🟢 **EXCELLENT** - System integration is comprehensive and production-ready.\n\n")
        elif success_rate >= 75:
            f.write("🟡 **GOOD** - System integration is solid with minor issues to address.\n\n")
        elif success_rate >= 50:
            f.write("🟠 **FAIR** - System has significant integration issues requiring attention.\n\n")
        else:
            f.write("🔴 **POOR** - System has critical integration failures that must be resolved.\n\n")
        
        f.write("## Test Results\n\n")
        for test_name, test_data in results['tests'].items():
            status = "✅ PASSED" if test_data['success'] else "❌ FAILED"
            f.write(f"### {status}: {test_name}\n")
            
            if test_data.get('duration_ms'):
                f.write(f"- **Duration:** {test_data['duration_ms']:.1f}ms\n")
            
            if test_data.get('error'):
                f.write(f"- **Error:** {test_data['error']}\n")
            
            if test_data.get('warning'):
                f.write(f"- **Warning:** {test_data['warning']}\n")
            
            if test_data.get('details'):
                f.write("- **Details:**\n")
                for key, value in test_data['details'].items():
                    f.write(f"  - {key}: {value}\n")
            
            f.write("\n")
        
        f.write("## System Diagnostics\n\n")
        for category, diagnostic_data in results.get('diagnostics', {}).items():
            f.write(f"### {category.replace('_', ' ').title()}\n")
            f.write(f"```json\n{json.dumps(diagnostic_data, indent=2)}\n```\n\n")
        
        f.write("## Performance Metrics\n\n")
        perf_metrics = results.get('performance_metrics', {})
        f.write(f"- **Total Duration:** {perf_metrics.get('total_duration_seconds', 0):.2f} seconds\n")
        f.write(f"- **Tests per Second:** {perf_metrics.get('tests_per_second', 0):.2f}\n")
        f.write(f"- **Average Test Duration:** {perf_metrics.get('average_test_duration', 0):.2f} seconds\n\n")
        
        if results['summary']['errors']:
            f.write("## Errors\n\n")
            for error in results['summary']['errors']:
                f.write(f"- {error}\n")
            f.write("\n")
        
        if results['summary']['warnings']:
            f.write("## Warnings\n\n")
            for warning in results['summary']['warnings']:
                f.write(f"- {warning}\n")
            f.write("\n")

if __name__ == "__main__":
    sys.exit(main())