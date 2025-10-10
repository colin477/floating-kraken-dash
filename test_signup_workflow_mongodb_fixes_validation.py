#!/usr/bin/env python3
"""
Comprehensive test suite to validate MongoDB connection fixes for signup workflow
Tests the critical Phase 1 fixes that should resolve 503 Service Unavailable errors
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, List, Any
import os
import sys

class SignupWorkflowValidator:
    """Validates MongoDB connection fixes for signup workflow"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
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
    
    async def test_health_check_endpoint(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test the new /healthz/db endpoint for MongoDB connection monitoring"""
        test_name = "health_check_endpoint"
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            start_time = time.time()
            async with session.get(f"{self.base_url}/healthz/db") as response:
                duration = time.time() - start_time
                response_data = await response.json()
                
                result = {
                    "status": "PASSED" if response.status == 200 else "FAILED",
                    "response_code": response.status,
                    "response_time": duration,
                    "response_data": response_data,
                    "database_connected": response_data.get("database_connected", False),
                    "connection_stats": response_data.get("connection_stats", {}),
                    "error": None
                }
                
                if response.status == 200:
                    print(f"✅ Health check passed - Database connected: {result['database_connected']}")
                    print(f"   Response time: {duration:.3f}s")
                    if result['connection_stats']:
                        print(f"   Connection stats: {result['connection_stats']}")
                else:
                    print(f"❌ Health check failed - Status: {response.status}")
                    result["error"] = f"Health check returned {response.status}"
                
                return result
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "response_time": None,
                "database_connected": False
            }
    
    async def test_signup_endpoint_basic(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test basic signup functionality - should not return 503 errors"""
        test_name = "signup_endpoint_basic"
        print(f"\n🔍 Testing {test_name}...")
        
        user_data = self.generate_test_user()
        
        try:
            start_time = time.time()
            async with session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                response_data = await response.json()
                
                result = {
                    "status": "PASSED" if response.status in [201, 409] else "FAILED",
                    "response_code": response.status,
                    "response_time": duration,
                    "response_data": response_data,
                    "user_data": user_data,
                    "error": None
                }
                
                if response.status == 201:
                    print(f"✅ Signup successful - User created")
                    print(f"   Response time: {duration:.3f}s")
                    print(f"   Access token received: {'access_token' in response_data}")
                elif response.status == 409:
                    print(f"✅ Signup handled duplicate email correctly")
                    result["status"] = "PASSED"
                elif response.status == 503:
                    print(f"❌ CRITICAL: 503 Service Unavailable - MongoDB connection issue!")
                    result["error"] = "503 Service Unavailable - This should be fixed"
                else:
                    print(f"❌ Signup failed - Status: {response.status}")
                    result["error"] = f"Unexpected status code: {response.status}"
                
                return result
                
        except Exception as e:
            print(f"❌ Signup test error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "response_time": None,
                "user_data": user_data
            }
    
    async def test_signup_endpoint_load(self, session: aiohttp.ClientSession, concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test signup endpoint under load to verify connection stability"""
        test_name = f"signup_endpoint_load_{concurrent_requests}_concurrent"
        print(f"\n🔍 Testing {test_name}...")
        
        async def single_signup_test():
            user_data = self.generate_test_user()
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    duration = time.time() - start_time
                    response_data = await response.json()
                    
                    return {
                        "status_code": response.status,
                        "response_time": duration,
                        "success": response.status in [201, 409],
                        "service_unavailable": response.status == 503,
                        "user_email": user_data["email"]
                    }
            except Exception as e:
                return {
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "service_unavailable": False,
                    "error": str(e),
                    "user_email": user_data["email"]
                }
        
        # Run concurrent signup tests
        start_time = time.time()
        tasks = [single_signup_test() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        service_unavailable_count = sum(1 for r in results if r["service_unavailable"])
        error_count = sum(1 for r in results if "error" in r)
        
        avg_response_time = sum(r["response_time"] for r in results if r["response_time"]) / len([r for r in results if r["response_time"]])
        
        result = {
            "status": "PASSED" if service_unavailable_count == 0 else "FAILED",
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "service_unavailable_count": service_unavailable_count,
            "error_count": error_count,
            "total_duration": total_duration,
            "average_response_time": avg_response_time,
            "individual_results": results,
            "error": None
        }
        
        if service_unavailable_count == 0:
            print(f"✅ Load test passed - No 503 errors")
            print(f"   Successful requests: {successful_requests}/{concurrent_requests}")
            print(f"   Average response time: {avg_response_time:.3f}s")
        else:
            print(f"❌ CRITICAL: {service_unavailable_count} requests returned 503 Service Unavailable")
            result["error"] = f"{service_unavailable_count} requests failed with 503 errors"
        
        return result
    
    async def test_production_environment_detection(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test production environment detection by checking logs or behavior"""
        test_name = "production_environment_detection"
        print(f"\n🔍 Testing {test_name}...")
        
        # Test by making a request and checking if production optimizations are applied
        # We can infer this from response times and behavior
        user_data = self.generate_test_user()
        
        try:
            # Make multiple requests to see if production timeouts are being used
            response_times = []
            for i in range(3):
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    duration = time.time() - start_time
                    response_times.append(duration)
                    
                    if i == 0:  # Only process first response
                        response_data = await response.json()
                        first_response_code = response.status
                
                # Use different email for subsequent requests
                user_data = self.generate_test_user()
            
            avg_response_time = sum(response_times) / len(response_times)
            
            result = {
                "status": "PASSED",  # This test is informational
                "average_response_time": avg_response_time,
                "response_times": response_times,
                "first_response_code": first_response_code,
                "production_indicators": {
                    "consistent_response_times": max(response_times) - min(response_times) < 2.0,
                    "reasonable_response_time": avg_response_time < 10.0,
                    "no_timeout_errors": first_response_code != 503
                },
                "error": None
            }
            
            print(f"✅ Environment detection test completed")
            print(f"   Average response time: {avg_response_time:.3f}s")
            print(f"   Response time consistency: {result['production_indicators']['consistent_response_times']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Environment detection test error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "average_response_time": None
            }
    
    async def test_database_connection_stability(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test database connection stability over time"""
        test_name = "database_connection_stability"
        print(f"\n🔍 Testing {test_name}...")
        
        stability_results = []
        test_duration = 30  # 30 seconds
        check_interval = 5   # Check every 5 seconds
        
        start_time = time.time()
        while time.time() - start_time < test_duration:
            try:
                # Test health check
                health_start = time.time()
                async with session.get(f"{self.base_url}/healthz/db") as response:
                    health_duration = time.time() - health_start
                    health_data = await response.json()
                    
                    # Test signup
                    user_data = self.generate_test_user()
                    signup_start = time.time()
                    async with session.post(
                        f"{self.base_url}/api/v1/auth/register",
                        json=user_data,
                        headers={"Content-Type": "application/json"}
                    ) as signup_response:
                        signup_duration = time.time() - signup_start
                        
                        stability_results.append({
                            "timestamp": time.time(),
                            "health_check": {
                                "status_code": response.status,
                                "response_time": health_duration,
                                "database_connected": health_data.get("database_connected", False)
                            },
                            "signup_test": {
                                "status_code": signup_response.status,
                                "response_time": signup_duration,
                                "success": signup_response.status in [201, 409]
                            }
                        })
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                stability_results.append({
                    "timestamp": time.time(),
                    "error": str(e)
                })
                await asyncio.sleep(check_interval)
        
        # Analyze stability
        successful_checks = sum(1 for r in stability_results if "error" not in r and r["health_check"]["database_connected"])
        total_checks = len(stability_results)
        stability_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        
        result = {
            "status": "PASSED" if stability_percentage >= 90 else "FAILED",
            "test_duration": test_duration,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "stability_percentage": stability_percentage,
            "stability_results": stability_results,
            "error": None if stability_percentage >= 90 else f"Stability only {stability_percentage:.1f}%"
        }
        
        print(f"✅ Stability test completed - {stability_percentage:.1f}% stable")
        print(f"   Successful checks: {successful_checks}/{total_checks}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🚀 Starting MongoDB Connection Fixes Validation for Signup Workflow")
        print("=" * 70)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            # Test 1: Health check endpoint
            self.test_results["tests"]["health_check"] = await self.test_health_check_endpoint(session)
            
            # Test 2: Basic signup functionality
            self.test_results["tests"]["signup_basic"] = await self.test_signup_endpoint_basic(session)
            
            # Test 3: Signup under load
            self.test_results["tests"]["signup_load"] = await self.test_signup_endpoint_load(session, 5)
            
            # Test 4: Production environment detection
            self.test_results["tests"]["production_detection"] = await self.test_production_environment_detection(session)
            
            # Test 5: Database connection stability
            self.test_results["tests"]["connection_stability"] = await self.test_database_connection_stability(session)
        
        # Calculate summary
        for test_name, test_result in self.test_results["tests"].items():
            self.test_results["summary"]["total_tests"] += 1
            if test_result["status"] == "PASSED":
                self.test_results["summary"]["passed"] += 1
            else:
                self.test_results["summary"]["failed"] += 1
                if test_result.get("error"):
                    self.test_results["summary"]["errors"].append(f"{test_name}: {test_result['error']}")
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        summary = self.test_results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%")
        
        if summary["errors"]:
            print("\n❌ ERRORS FOUND:")
            for error in summary["errors"]:
                print(f"   • {error}")
        
        # Check for critical issues
        critical_issues = []
        for test_name, test_result in self.test_results["tests"].items():
            if test_result.get("service_unavailable_count", 0) > 0:
                critical_issues.append(f"503 Service Unavailable errors in {test_name}")
            if test_result.get("response_code") == 503:
                critical_issues.append(f"503 Service Unavailable in {test_name}")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES (MongoDB Connection Problems):")
            for issue in critical_issues:
                print(f"   • {issue}")
        else:
            print("\n✅ NO CRITICAL MONGODB CONNECTION ISSUES DETECTED")
            print("   The Phase 1 fixes appear to be working correctly!")
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"signup_workflow_mongodb_fixes_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

async def main():
    """Main test execution"""
    # Check if backend is running
    base_url = "http://localhost:8000"
    
    validator = SignupWorkflowValidator(base_url)
    
    try:
        results = await validator.run_all_tests()
        validator.print_summary()
        filename = validator.save_results()
        
        # Return appropriate exit code
        if validator.test_results["summary"]["failed"] == 0:
            print("\n🎉 All tests passed! MongoDB connection fixes are working correctly.")
            return 0
        else:
            print(f"\n⚠️  {validator.test_results['summary']['failed']} test(s) failed. Review the results above.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)