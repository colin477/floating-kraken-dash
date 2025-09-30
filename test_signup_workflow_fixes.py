#!/usr/bin/env python3
"""
Comprehensive test script to verify the critical signup workflow fixes
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = f"test_user_{int(datetime.now().timestamp())}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Test User"

class SignupWorkflowTester:
    def __init__(self):
        self.session = None
        self.user_token = None
        self.user_id = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, message: str = "", details: Dict[Any, Any] = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
    
    async def test_user_registration(self):
        """Test 1: User registration works correctly"""
        try:
            async with self.session.post(f"{BASE_URL}/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }) as response:
                if response.status == 201:
                    data = await response.json()
                    self.user_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    self.log_test("User Registration", True, "User registered successfully")
                    return True
                else:
                    error_data = await response.json()
                    self.log_test("User Registration", False, f"Registration failed: {error_data}")
                    return False
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    async def test_onboarding_status_detailed_response(self):
        """Test 2: Onboarding status returns detailed information"""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            async with self.session.get(f"{BASE_URL}/profile/onboarding-status", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = [
                        "onboarding_completed", "has_profile", "user_id", 
                        "current_step", "plan_selected", "profile_completed", 
                        "setup_level", "plan_type"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        self.log_test("Onboarding Status Response", True, 
                                    "All required fields present", data)
                        return True
                    else:
                        self.log_test("Onboarding Status Response", False, 
                                    f"Missing fields: {missing_fields}", data)
                        return False
                else:
                    error_data = await response.json()
                    self.log_test("Onboarding Status Response", False, 
                                f"Status check failed: {error_data}")
                    return False
        except Exception as e:
            self.log_test("Onboarding Status Response", False, f"Exception: {str(e)}")
            return False
    
    async def test_plan_selection_api_fix(self):
        """Test 3: Plan selection API accepts correct data structure"""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            plan_data = {
                "plan_type": "basic",
                "setup_level": "medium"
            }
            
            async with self.session.post(f"{BASE_URL}/profile/plan-selection", 
                                       json=plan_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Plan Selection API", True, 
                                "Plan selection successful", data)
                    return True
                else:
                    error_data = await response.json()
                    self.log_test("Plan Selection API", False, 
                                f"Plan selection failed: {error_data}")
                    return False
        except Exception as e:
            self.log_test("Plan Selection API", False, f"Exception: {str(e)}")
            return False
    
    async def test_protected_routes_security(self):
        """Test 4: Protected routes require completed onboarding"""
        protected_endpoints = [
            "/recipes/",
            "/meal-plans/",
            "/shopping-lists/"
        ]
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        security_test_results = []
        
        for endpoint in protected_endpoints:
            try:
                async with self.session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                    if response.status == 403:
                        error_data = await response.json()
                        if "onboarding" in error_data.get("detail", {}).get("error", "").lower():
                            security_test_results.append(f"✅ {endpoint} properly protected")
                        else:
                            security_test_results.append(f"❌ {endpoint} wrong error type")
                    else:
                        security_test_results.append(f"❌ {endpoint} not protected (status: {response.status})")
            except Exception as e:
                security_test_results.append(f"❌ {endpoint} exception: {str(e)}")
        
        all_protected = all("✅" in result for result in security_test_results)
        self.log_test("Protected Routes Security", all_protected, 
                    "Security middleware applied", {"results": security_test_results})
        return all_protected
    
    async def test_complete_onboarding_flow(self):
        """Test 5: Complete onboarding flow works end-to-end"""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Complete onboarding
            async with self.session.post(f"{BASE_URL}/profile/complete-onboarding", 
                                       json={}, headers=headers) as response:
                if response.status == 200:
                    # Check onboarding status again
                    async with self.session.get(f"{BASE_URL}/profile/onboarding-status", 
                                               headers=headers) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            if status_data.get("onboarding_completed"):
                                self.log_test("Complete Onboarding Flow", True, 
                                            "Onboarding completed successfully")
                                return True
                            else:
                                self.log_test("Complete Onboarding Flow", False, 
                                            "Onboarding not marked as complete", status_data)
                                return False
                        else:
                            self.log_test("Complete Onboarding Flow", False, 
                                        "Failed to check status after completion")
                            return False
                else:
                    error_data = await response.json()
                    self.log_test("Complete Onboarding Flow", False, 
                                f"Completion failed: {error_data}")
                    return False
        except Exception as e:
            self.log_test("Complete Onboarding Flow", False, f"Exception: {str(e)}")
            return False
    
    async def test_protected_routes_after_onboarding(self):
        """Test 6: Protected routes accessible after onboarding completion"""
        protected_endpoints = [
            "/recipes/",
            "/meal-plans/",
            "/shopping-lists/"
        ]
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        access_test_results = []
        
        for endpoint in protected_endpoints:
            try:
                async with self.session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                    if response.status == 200:
                        access_test_results.append(f"✅ {endpoint} accessible")
                    else:
                        access_test_results.append(f"❌ {endpoint} not accessible (status: {response.status})")
            except Exception as e:
                access_test_results.append(f"❌ {endpoint} exception: {str(e)}")
        
        all_accessible = all("✅" in result for result in access_test_results)
        self.log_test("Protected Routes After Onboarding", all_accessible, 
                    "Routes accessible after completion", {"results": access_test_results})
        return all_accessible
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting Signup Workflow Fix Tests")
        print("=" * 50)
        
        # Test 1: User Registration
        if not await self.test_user_registration():
            print("❌ Cannot proceed without successful registration")
            return False
        
        # Test 2: Onboarding Status Response
        await self.test_onboarding_status_detailed_response()
        
        # Test 3: Plan Selection API
        await self.test_plan_selection_api_fix()
        
        # Test 4: Protected Routes Security (before onboarding)
        await self.test_protected_routes_security()
        
        # Test 5: Complete Onboarding Flow
        await self.test_complete_onboarding_flow()
        
        # Test 6: Protected Routes After Onboarding
        await self.test_protected_routes_after_onboarding()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 100:
            print("🎉 ALL CRITICAL FIXES VERIFIED SUCCESSFULLY!")
            return True
        elif success_rate >= 80:
            print("⚠️  Most fixes working, some issues remain")
            return False
        else:
            print("❌ CRITICAL ISSUES STILL PRESENT")
            return False

async def main():
    """Main test execution"""
    try:
        async with SignupWorkflowTester() as tester:
            success = await tester.run_all_tests()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())