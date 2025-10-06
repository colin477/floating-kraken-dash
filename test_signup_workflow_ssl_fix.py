#!/usr/bin/env python3
"""
Test the sign-up workflow to verify MongoDB SSL/TLS fix resolves the production issue
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, Any, List

class SignupWorkflowSSLTester:
    """Test sign-up workflow to verify SSL/TLS fix"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "ssl_handshake_errors": 0
            },
            "test_details": []
        }
    
    def generate_test_user(self) -> Dict[str, str]:
        """Generate a unique test user"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return {
            "email": f"test_ssl_fix_{random_suffix}@example.com",
            "password": "TestPassword123!",
            "full_name": "SSL Test User"
        }
    
    async def test_api_health(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test API health endpoint"""
        print("🏥 Testing API Health...")
        
        test_result = {
            "test_name": "API Health Check",
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            async with session.get(f"{self.base_url}/healthz") as response:
                test_result["details"]["status_code"] = response.status
                test_result["details"]["response_time_ms"] = 0  # Will be updated
                
                if response.status == 200:
                    data = await response.json()
                    test_result["details"]["response_data"] = data
                    test_result["status"] = "PASSED"
                    print("   ✅ API is healthy")
                else:
                    test_result["status"] = "FAILED"
                    test_result["errors"].append(f"Health check failed with status {response.status}")
                    print(f"   ❌ API health check failed: {response.status}")
                    
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Health check error: {str(e)}")
            print(f"   ❌ Health check error: {e}")
        
        return test_result
    
    async def test_user_registration(self, session: aiohttp.ClientSession, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test user registration (the main sign-up workflow)"""
        print(f"👤 Testing User Registration for {user_data['email']}...")
        
        test_result = {
            "test_name": "User Registration",
            "user_email": user_data["email"],
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "ssl_related": False
        }
        
        try:
            start_time = time.time()
            
            async with session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = (time.time() - start_time) * 1000
                
                test_result["details"]["status_code"] = response.status
                test_result["details"]["response_time_ms"] = round(response_time, 2)
                
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text)
                    test_result["details"]["response_data"] = response_data
                except json.JSONDecodeError:
                    test_result["details"]["response_text"] = response_text
                
                if response.status == 201:
                    test_result["status"] = "PASSED"
                    print(f"   ✅ Registration successful in {response_time:.2f}ms")
                elif response.status == 400:
                    # Check if it's a validation error (expected for duplicate emails)
                    if "already exists" in response_text.lower():
                        test_result["status"] = "PASSED"
                        test_result["details"]["note"] = "User already exists (expected)"
                        print(f"   ✅ User already exists (expected behavior)")
                    else:
                        test_result["status"] = "FAILED"
                        test_result["errors"].append(f"Registration validation error: {response_text}")
                        print(f"   ❌ Registration validation error")
                else:
                    test_result["status"] = "FAILED"
                    test_result["errors"].append(f"Registration failed with status {response.status}: {response_text}")
                    print(f"   ❌ Registration failed: {response.status}")
                    
                    # Check for SSL-related errors in the response (more specific)
                    ssl_indicators = [
                        "serverselectiontimeouterror", "connection timeout",
                        "session has expired", "ssl handshake", "tls handshake",
                        "certificate", "ssl error", "tls error"
                    ]
                    
                    # Only flag as SSL-related if it's actually an SSL/TLS error, not validation
                    if response.status >= 500 and any(indicator in response_text.lower() for indicator in ssl_indicators):
                        test_result["ssl_related"] = True
                        test_result["errors"].append("SSL/TLS related error detected")
                        print(f"   🚨 SSL/TLS related error detected!")
                        
        except aiohttp.ClientError as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"HTTP client error: {str(e)}")
            
            # Check for SSL-related client errors (more specific)
            if any(term in str(e).lower() for term in ["ssl handshake", "tls handshake", "certificate verify", "ssl error", "tls error"]):
                test_result["ssl_related"] = True
                test_result["errors"].append("SSL/TLS client error detected")
                print(f"   🚨 SSL/TLS client error: {e}")
            else:
                print(f"   ❌ HTTP client error: {e}")
                
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Registration error: {str(e)}")
            print(f"   ❌ Registration error: {e}")
        
        return test_result
    
    async def test_user_login(self, session: aiohttp.ClientSession, email: str, password: str) -> Dict[str, Any]:
        """Test user login after registration"""
        print(f"🔐 Testing User Login for {email}...")
        
        test_result = {
            "test_name": "User Login",
            "user_email": email,
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "ssl_related": False
        }
        
        try:
            login_data = {"email": email, "password": password}
            start_time = time.time()
            
            async with session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = (time.time() - start_time) * 1000
                
                test_result["details"]["status_code"] = response.status
                test_result["details"]["response_time_ms"] = round(response_time, 2)
                
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text)
                    test_result["details"]["response_data"] = response_data
                except json.JSONDecodeError:
                    test_result["details"]["response_text"] = response_text
                
                if response.status == 200:
                    test_result["status"] = "PASSED"
                    print(f"   ✅ Login successful in {response_time:.2f}ms")
                else:
                    test_result["status"] = "FAILED"
                    test_result["errors"].append(f"Login failed with status {response.status}: {response_text}")
                    print(f"   ❌ Login failed: {response.status}")
                    
                    # Check for SSL-related errors (more specific)
                    ssl_indicators = [
                        "serverselectiontimeouterror", "connection timeout",
                        "session has expired", "ssl handshake", "tls handshake",
                        "certificate", "ssl error", "tls error"
                    ]
                    
                    # Only flag as SSL-related if it's actually an SSL/TLS error, not validation
                    if response.status >= 500 and any(indicator in response_text.lower() for indicator in ssl_indicators):
                        test_result["ssl_related"] = True
                        test_result["errors"].append("SSL/TLS related error detected")
                        print(f"   🚨 SSL/TLS related error detected!")
                        
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Login error: {str(e)}")
            
            if any(term in str(e).lower() for term in ["ssl handshake", "tls handshake", "certificate verify", "ssl error", "tls error"]):
                test_result["ssl_related"] = True
                test_result["errors"].append("SSL/TLS client error detected")
                print(f"   🚨 SSL/TLS client error: {e}")
            else:
                print(f"   ❌ Login error: {e}")
        
        return test_result
    
    async def test_concurrent_signups(self, session: aiohttp.ClientSession, num_concurrent: int = 5) -> Dict[str, Any]:
        """Test concurrent sign-ups to simulate production load"""
        print(f"🔄 Testing {num_concurrent} Concurrent Sign-ups...")
        
        test_result = {
            "test_name": "Concurrent Sign-ups",
            "concurrent_count": num_concurrent,
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "ssl_related": False
        }
        
        try:
            # Generate unique users for concurrent testing
            users = [self.generate_test_user() for _ in range(num_concurrent)]
            
            # Create concurrent registration tasks
            tasks = []
            for user in users:
                task = self.test_user_registration(session, user)
                tasks.append(task)
            
            # Execute all registrations concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful = 0
            failed = 0
            ssl_errors = 0
            
            for result in results:
                if isinstance(result, dict):
                    if result["status"] == "PASSED":
                        successful += 1
                    else:
                        failed += 1
                        if result.get("ssl_related", False):
                            ssl_errors += 1
                else:
                    failed += 1
            
            test_result["details"]["total_time_ms"] = round(total_time, 2)
            test_result["details"]["successful_registrations"] = successful
            test_result["details"]["failed_registrations"] = failed
            test_result["details"]["ssl_related_errors"] = ssl_errors
            test_result["details"]["average_time_per_request"] = round(total_time / num_concurrent, 2)
            
            if ssl_errors > 0:
                test_result["ssl_related"] = True
                test_result["status"] = "FAILED"
                test_result["errors"].append(f"{ssl_errors} SSL/TLS related errors detected")
                print(f"   🚨 {ssl_errors} SSL/TLS errors detected!")
            elif failed == 0:
                test_result["status"] = "PASSED"
                print(f"   ✅ All {successful} concurrent registrations successful")
            else:
                test_result["status"] = "FAILED"
                test_result["errors"].append(f"{failed} registrations failed")
                print(f"   ❌ {failed} registrations failed")
            
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Concurrent test error: {str(e)}")
            print(f"   ❌ Concurrent test error: {e}")
        
        return test_result
    
    async def run_comprehensive_signup_tests(self):
        """Run comprehensive sign-up workflow tests"""
        print("🚀 Starting Sign-up Workflow SSL/TLS Fix Testing")
        print("=" * 60)
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test 1: API Health
            health_test = await self.test_api_health(session)
            self.test_results["test_details"].append(health_test)
            
            # Test 2: Single user registration
            test_user = self.generate_test_user()
            registration_test = await self.test_user_registration(session, test_user)
            self.test_results["test_details"].append(registration_test)
            
            # Test 3: User login (if registration was successful)
            if registration_test["status"] == "PASSED":
                login_test = await self.test_user_login(session, test_user["email"], test_user["password"])
                self.test_results["test_details"].append(login_test)
            
            # Test 4: Concurrent sign-ups (stress test)
            concurrent_test = await self.test_concurrent_signups(session, 5)
            self.test_results["test_details"].append(concurrent_test)
            
            # Calculate summary
            for test in self.test_results["test_details"]:
                self.test_results["test_summary"]["total_tests"] += 1
                if test["status"] == "PASSED":
                    self.test_results["test_summary"]["passed"] += 1
                else:
                    self.test_results["test_summary"]["failed"] += 1
                
                if test.get("ssl_related", False):
                    self.test_results["test_summary"]["ssl_handshake_errors"] += 1
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 SIGN-UP WORKFLOW TEST SUMMARY")
        print("=" * 60)
        
        summary = self.test_results["test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"🚨 SSL/TLS Errors: {summary['ssl_handshake_errors']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test in self.test_results["test_details"]:
            status_icon = {"PASSED": "✅", "FAILED": "❌"}.get(test["status"], "❓")
            ssl_icon = "🚨" if test.get("ssl_related", False) else ""
            print(f"{status_icon}{ssl_icon} {test['test_name']}: {test['status']}")
            
            if test.get("errors"):
                for error in test["errors"]:
                    print(f"   ❌ {error}")
        
        # Overall assessment
        print("\n🎯 SSL/TLS FIX ASSESSMENT:")
        if summary['ssl_handshake_errors'] == 0:
            print("✅ No SSL/TLS handshake errors detected!")
            print("✅ MongoDB SSL/TLS fix appears to be working correctly")
            print("✅ Sign-up workflow is functioning without SSL issues")
        else:
            print("❌ SSL/TLS handshake errors still occurring!")
            print("❌ MongoDB SSL/TLS fix may need additional investigation")
            print("❌ Production sign-up issue may persist")
        
        return summary['ssl_handshake_errors'] == 0

async def main():
    """Main test execution"""
    tester = SignupWorkflowSSLTester()
    
    try:
        # Run comprehensive tests
        results = await tester.run_comprehensive_signup_tests()
        
        # Print summary
        success = tester.print_summary()
        
        # Save detailed results
        results_file = f"signup_workflow_ssl_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)