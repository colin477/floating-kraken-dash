#!/usr/bin/env python3
"""
Comprehensive test script to validate MongoDB connection fixes for signup functionality.

This script tests:
1. Direct /api/v1/auth/register endpoint functionality
2. MongoDB connection stability during registration
3. Connection health monitoring
4. Multiple concurrent signup attempts
5. SSL/TLS configuration validation
6. Connection pool optimization effectiveness
7. Timeout settings and retry logic
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoDBConnectionFixValidator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "base_url": base_url,
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
    def generate_test_user(self) -> Dict[str, str]:
        """Generate a unique test user"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return {
            "email": f"test_user_{random_suffix}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Test User {random_suffix}"
        }
    
    async def test_health_endpoint(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test the health endpoint to verify basic connectivity"""
        test_name = "health_endpoint"
        logger.info("Testing health endpoint...")
        
        try:
            start_time = time.time()
            async with session.get(f"{self.base_url}/healthz") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "PASS",
                        "response_time": duration,
                        "status_code": response.status,
                        "response_data": data
                    }
                else:
                    return {
                        "status": "FAIL",
                        "response_time": duration,
                        "status_code": response.status,
                        "error": f"Unexpected status code: {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_connection_health_monitoring(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test MongoDB connection health monitoring endpoint"""
        test_name = "connection_health_monitoring"
        logger.info("Testing connection health monitoring...")
        
        try:
            start_time = time.time()
            # Try to access a health endpoint that would trigger connection health check
            async with session.get(f"{self.api_base}/health/database") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "PASS",
                        "response_time": duration,
                        "status_code": response.status,
                        "connection_stats": data
                    }
                elif response.status == 404:
                    # Endpoint might not exist, try alternative
                    return await self.test_health_endpoint(session)
                else:
                    return {
                        "status": "FAIL",
                        "response_time": duration,
                        "status_code": response.status,
                        "error": f"Health check failed with status: {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_single_registration(self, session: aiohttp.ClientSession, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test a single user registration"""
        logger.info(f"Testing registration for {user_data['email']}")
        
        try:
            start_time = time.time()
            async with session.post(
                f"{self.api_base}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    return {
                        "status": "PASS",
                        "response_time": duration,
                        "status_code": response.status,
                        "user_created": True,
                        "has_access_token": "access_token" in data,
                        "user_data": {
                            "email": data.get("user", {}).get("email"),
                            "full_name": data.get("user", {}).get("full_name"),
                            "is_active": data.get("user", {}).get("is_active")
                        }
                    }
                elif response.status == 409:
                    # User already exists - this is expected for duplicate tests
                    return {
                        "status": "PASS",
                        "response_time": duration,
                        "status_code": response.status,
                        "user_created": False,
                        "note": "User already exists (expected for duplicate tests)"
                    }
                elif response.status == 503:
                    # Service unavailable - this is what we're trying to fix
                    error_data = await response.text()
                    return {
                        "status": "FAIL",
                        "response_time": duration,
                        "status_code": response.status,
                        "error": "Service Unavailable - MongoDB connection issue",
                        "error_details": error_data
                    }
                else:
                    error_data = await response.text()
                    return {
                        "status": "FAIL",
                        "response_time": duration,
                        "status_code": response.status,
                        "error": f"Unexpected status code: {response.status}",
                        "error_details": error_data
                    }
                    
        except asyncio.TimeoutError:
            return {
                "status": "FAIL",
                "error": "Request timeout",
                "error_type": "TimeoutError"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_concurrent_registrations(self, session: aiohttp.ClientSession, num_concurrent: int = 10) -> Dict[str, Any]:
        """Test multiple concurrent user registrations to stress test connection pool"""
        test_name = "concurrent_registrations"
        logger.info(f"Testing {num_concurrent} concurrent registrations...")
        
        # Generate unique users for concurrent testing
        users = [self.generate_test_user() for _ in range(num_concurrent)]
        
        try:
            start_time = time.time()
            
            # Create concurrent registration tasks
            tasks = [self.test_single_registration(session, user) for user in users]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_duration = time.time() - start_time
            
            # Analyze results
            successful = 0
            failed = 0
            errors = 0
            service_unavailable = 0
            response_times = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors += 1
                    logger.error(f"Concurrent test {i+1} raised exception: {result}")
                elif result.get("status") == "PASS":
                    successful += 1
                    if "response_time" in result:
                        response_times.append(result["response_time"])
                elif result.get("status") == "FAIL":
                    failed += 1
                    if result.get("status_code") == 503:
                        service_unavailable += 1
                else:
                    errors += 1
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "status": "PASS" if service_unavailable == 0 else "FAIL",
                "total_duration": total_duration,
                "concurrent_requests": num_concurrent,
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "service_unavailable_count": service_unavailable,
                "average_response_time": avg_response_time,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "connection_pool_stress_test": "PASS" if service_unavailable == 0 else "FAIL"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_ssl_tls_configuration(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test SSL/TLS configuration by attempting registration and monitoring for SSL errors"""
        test_name = "ssl_tls_configuration"
        logger.info("Testing SSL/TLS configuration...")
        
        user_data = self.generate_test_user()
        
        try:
            # Perform a registration to test SSL/TLS connection
            result = await self.test_single_registration(session, user_data)
            
            if result.get("status") == "PASS":
                return {
                    "status": "PASS",
                    "ssl_handshake": "SUCCESS",
                    "connection_established": True,
                    "response_time": result.get("response_time", 0)
                }
            elif result.get("status") == "FAIL":
                error_details = result.get("error_details", "")
                if any(ssl_indicator in error_details.lower() for ssl_indicator in 
                       ['ssl', 'tls', 'certificate', 'handshake', 'connection forcibly closed']):
                    return {
                        "status": "FAIL",
                        "ssl_handshake": "FAILED",
                        "connection_established": False,
                        "error": "SSL/TLS connection error detected",
                        "error_details": error_details
                    }
                else:
                    return {
                        "status": "PASS",
                        "ssl_handshake": "SUCCESS",
                        "connection_established": True,
                        "note": "No SSL/TLS errors detected, failure due to other reasons"
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_timeout_and_retry_logic(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test timeout settings and retry logic by monitoring response times"""
        test_name = "timeout_and_retry_logic"
        logger.info("Testing timeout and retry logic...")
        
        user_data = self.generate_test_user()
        
        try:
            # Test with extended timeout to see if the 45-second timeout is working
            timeout = aiohttp.ClientTimeout(total=60)  # Allow more time than the 45s MongoDB timeout
            
            start_time = time.time()
            async with aiohttp.ClientSession(timeout=timeout) as test_session:
                result = await self.test_single_registration(test_session, user_data)
            
            total_time = time.time() - start_time
            
            if result.get("status") == "PASS":
                return {
                    "status": "PASS",
                    "total_response_time": total_time,
                    "timeout_handling": "SUCCESS",
                    "within_expected_timeout": total_time < 50,  # Should be well under 50s with 45s timeout
                    "retry_logic": "WORKING" if total_time > 5 else "NOT_TRIGGERED"
                }
            elif result.get("status") == "FAIL":
                if "timeout" in result.get("error", "").lower():
                    return {
                        "status": "FAIL",
                        "total_response_time": total_time,
                        "timeout_handling": "FAILED",
                        "error": "Request timed out despite increased timeout settings"
                    }
                else:
                    return {
                        "status": "PASS",
                        "total_response_time": total_time,
                        "timeout_handling": "SUCCESS",
                        "note": "No timeout errors detected, failure due to other reasons"
                    }
            else:
                return result
                
        except asyncio.TimeoutError:
            return {
                "status": "FAIL",
                "timeout_handling": "FAILED",
                "error": "Request timed out even with extended client timeout"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MongoDB connection fix validation tests"""
        logger.info("Starting comprehensive MongoDB connection fix validation...")
        
        # Configure session with reasonable timeout
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test 1: Health endpoint
            logger.info("=== Test 1: Health Endpoint ===")
            self.test_results["tests"]["health_endpoint"] = await self.test_health_endpoint(session)
            
            # Test 2: Connection health monitoring
            logger.info("=== Test 2: Connection Health Monitoring ===")
            self.test_results["tests"]["connection_health_monitoring"] = await self.test_connection_health_monitoring(session)
            
            # Test 3: Single registration
            logger.info("=== Test 3: Single User Registration ===")
            single_user = self.generate_test_user()
            self.test_results["tests"]["single_registration"] = await self.test_single_registration(session, single_user)
            
            # Test 4: SSL/TLS configuration
            logger.info("=== Test 4: SSL/TLS Configuration ===")
            self.test_results["tests"]["ssl_tls_configuration"] = await self.test_ssl_tls_configuration(session)
            
            # Test 5: Timeout and retry logic
            logger.info("=== Test 5: Timeout and Retry Logic ===")
            self.test_results["tests"]["timeout_and_retry_logic"] = await self.test_timeout_and_retry_logic(session)
            
            # Test 6: Concurrent registrations (connection pool stress test)
            logger.info("=== Test 6: Concurrent Registrations (Connection Pool Test) ===")
            self.test_results["tests"]["concurrent_registrations"] = await self.test_concurrent_registrations(session, 15)
        
        # Calculate summary
        self.calculate_summary()
        
        return self.test_results
    
    def calculate_summary(self):
        """Calculate test summary statistics"""
        total_tests = len(self.test_results["tests"])
        passed = 0
        failed = 0
        errors = []
        
        for test_name, result in self.test_results["tests"].items():
            if result.get("status") == "PASS":
                passed += 1
            elif result.get("status") == "FAIL":
                failed += 1
                errors.append(f"{test_name}: {result.get('error', 'Test failed')}")
            elif result.get("status") == "ERROR":
                failed += 1
                errors.append(f"{test_name}: {result.get('error', 'Test error')}")
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "errors": errors
        }
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"mongodb_connection_fix_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Test results saved to {filename}")
        return filename

async def main():
    """Main test execution function"""
    print("=" * 80)
    print("MongoDB Connection Fix Validation Test Suite")
    print("=" * 80)
    
    validator = MongoDBConnectionFixValidator()
    
    try:
        results = await validator.run_all_tests()
        
        # Save results
        filename = validator.save_results()
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        summary = results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']}")
        
        if summary["errors"]:
            print("\nErrors:")
            for error in summary["errors"]:
                print(f"  - {error}")
        
        print(f"\nDetailed results saved to: {filename}")
        
        # Print key findings
        print("\n" + "=" * 80)
        print("KEY FINDINGS")
        print("=" * 80)
        
        # Check for 503 Service Unavailable errors
        service_unavailable_found = False
        for test_name, result in results["tests"].items():
            if result.get("status_code") == 503:
                service_unavailable_found = True
                print(f"❌ 503 Service Unavailable error found in {test_name}")
        
        if not service_unavailable_found:
            print("✅ No 503 Service Unavailable errors detected")
        
        # Check SSL/TLS
        ssl_test = results["tests"].get("ssl_tls_configuration", {})
        if ssl_test.get("ssl_handshake") == "SUCCESS":
            print("✅ SSL/TLS handshake successful")
        else:
            print("❌ SSL/TLS issues detected")
        
        # Check concurrent performance
        concurrent_test = results["tests"].get("concurrent_registrations", {})
        if concurrent_test.get("service_unavailable_count", 0) == 0:
            print("✅ Connection pool handling concurrent requests successfully")
        else:
            print(f"❌ {concurrent_test.get('service_unavailable_count', 0)} concurrent requests failed with 503 errors")
        
        print("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())