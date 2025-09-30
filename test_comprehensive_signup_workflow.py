#!/usr/bin/env python3
"""
Comprehensive Sign-up Workflow Testing Script

This script tests the complete sign-up workflow implementation to verify that new users
are properly taken through the sign-up flow with intake questions.

Testing Areas:
1. Backend API endpoints for onboarding workflow
2. Profile stub creation during registration
3. Onboarding status checking and management
4. Plan selection during onboarding
5. Profile completion and onboarding finalization
6. Server-side validation enforcement
7. Authentication token validation
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_signup_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Test User"

class SignupWorkflowTester:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None, error: str = None):
        """Log test result for reporting"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()
    
    async def test_user_registration(self) -> bool:
        """Test user registration and profile stub creation"""
        try:
            print("🧪 Testing User Registration...")
            
            # Test registration endpoint
            registration_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_NAME
            }
            
            async with self.session.post(
                f"{BASE_URL}/auth/register",
                json=registration_data
            ) as response:
                if response.status != 201:
                    error_text = await response.text()
                    self.log_test_result(
                        "User Registration",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Registration failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate response structure
                required_fields = ["access_token", "token_type", "expires_in", "user"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test_result(
                        "User Registration",
                        False,
                        {"missing_fields": missing_fields, "response": data},
                        f"Missing required fields in registration response"
                    )
                    return False
                
                # Store authentication details
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                
                self.log_test_result(
                    "User Registration",
                    True,
                    {
                        "user_id": self.user_id,
                        "token_type": data["token_type"],
                        "expires_in": data["expires_in"]
                    }
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "User Registration",
                False,
                error=f"Exception during registration: {str(e)}"
            )
            return False
    
    async def test_onboarding_status_check(self) -> bool:
        """Test onboarding status checking after registration"""
        try:
            print("🧪 Testing Onboarding Status Check...")
            
            if not self.access_token:
                self.log_test_result(
                    "Onboarding Status Check",
                    False,
                    error="No access token available"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.get(
                f"{BASE_URL}/profile/onboarding-status",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(
                        "Onboarding Status Check",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Onboarding status check failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate expected initial state for new user
                expected_state = {
                    "onboarding_completed": False,
                    "has_profile": True,  # Profile stub should be created during registration
                    "user_id": self.user_id
                }
                
                validation_errors = []
                for key, expected_value in expected_state.items():
                    if key not in data:
                        validation_errors.append(f"Missing field: {key}")
                    elif data[key] != expected_value:
                        validation_errors.append(f"Field {key}: expected {expected_value}, got {data[key]}")
                
                if validation_errors:
                    self.log_test_result(
                        "Onboarding Status Check",
                        False,
                        {"validation_errors": validation_errors, "response": data},
                        "Onboarding status validation failed"
                    )
                    return False
                
                self.log_test_result(
                    "Onboarding Status Check",
                    True,
                    {"onboarding_status": data}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Onboarding Status Check",
                False,
                error=f"Exception during onboarding status check: {str(e)}"
            )
            return False
    
    async def test_plan_selection(self) -> bool:
        """Test plan selection during onboarding"""
        try:
            print("🧪 Testing Plan Selection...")
            
            if not self.access_token:
                self.log_test_result(
                    "Plan Selection",
                    False,
                    error="No access token available"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test plan selection
            plan_data = {
                "plan_type": "basic",
                "setup_level": "medium"
            }
            
            async with self.session.post(
                f"{BASE_URL}/profile/plan-selection",
                json=plan_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(
                        "Plan Selection",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Plan selection failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate that profile was updated with plan information
                if "subscription" not in data or data["subscription"] != "basic":
                    self.log_test_result(
                        "Plan Selection",
                        False,
                        {"response": data},
                        "Plan selection did not update subscription correctly"
                    )
                    return False
                
                self.log_test_result(
                    "Plan Selection",
                    True,
                    {"updated_profile": {"subscription": data["subscription"]}}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Plan Selection",
                False,
                error=f"Exception during plan selection: {str(e)}"
            )
            return False
    
    async def test_profile_update(self) -> bool:
        """Test profile update with intake question data"""
        try:
            print("🧪 Testing Profile Update...")
            
            if not self.access_token:
                self.log_test_result(
                    "Profile Update",
                    False,
                    error="No access token available"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test profile update with comprehensive data
            profile_data = {
                "dietary_restrictions": ["Vegetarian", "Low-sodium"],
                "allergies": ["Nuts", "Shellfish"],
                "taste_preferences": ["Italian", "Comfort Food"],
                "meal_preferences": ["Quick meals (under 30 min)", "Family-friendly"],
                "kitchen_equipment": ["Oven", "Stovetop", "Microwave", "Air fryer"],
                "weekly_budget": 150,
                "zip_code": "80202",
                "preferred_grocers": ["kroger-local", "safeway-local", "amazon-fresh"]
            }
            
            async with self.session.put(
                f"{BASE_URL}/profile/",
                json=profile_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(
                        "Profile Update",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Profile update failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate that all profile fields were updated correctly
                validation_errors = []
                for key, expected_value in profile_data.items():
                    if key not in data:
                        validation_errors.append(f"Missing field: {key}")
                    elif data[key] != expected_value:
                        validation_errors.append(f"Field {key}: expected {expected_value}, got {data[key]}")
                
                if validation_errors:
                    self.log_test_result(
                        "Profile Update",
                        False,
                        {"validation_errors": validation_errors, "sent_data": profile_data, "response": data},
                        "Profile update validation failed"
                    )
                    return False
                
                self.log_test_result(
                    "Profile Update",
                    True,
                    {"updated_fields": list(profile_data.keys())}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Profile Update",
                False,
                error=f"Exception during profile update: {str(e)}"
            )
            return False
    
    async def test_onboarding_completion(self) -> bool:
        """Test onboarding completion"""
        try:
            print("🧪 Testing Onboarding Completion...")
            
            if not self.access_token:
                self.log_test_result(
                    "Onboarding Completion",
                    False,
                    error="No access token available"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test onboarding completion
            completion_data = {}  # Empty data as per API specification
            
            async with self.session.post(
                f"{BASE_URL}/profile/complete-onboarding",
                json=completion_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(
                        "Onboarding Completion",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Onboarding completion failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate that onboarding_completed is now true
                if not data.get("onboarding_completed", False):
                    self.log_test_result(
                        "Onboarding Completion",
                        False,
                        {"response": data},
                        "Onboarding completion did not set onboarding_completed to true"
                    )
                    return False
                
                self.log_test_result(
                    "Onboarding Completion",
                    True,
                    {"onboarding_completed": data["onboarding_completed"]}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Onboarding Completion",
                False,
                error=f"Exception during onboarding completion: {str(e)}"
            )
            return False
    
    async def test_final_onboarding_status(self) -> bool:
        """Test final onboarding status after completion"""
        try:
            print("🧪 Testing Final Onboarding Status...")
            
            if not self.access_token:
                self.log_test_result(
                    "Final Onboarding Status",
                    False,
                    error="No access token available"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.get(
                f"{BASE_URL}/profile/onboarding-status",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(
                        "Final Onboarding Status",
                        False,
                        {"status_code": response.status, "response": error_text},
                        f"Final onboarding status check failed with status {response.status}"
                    )
                    return False
                
                data = await response.json()
                
                # Validate expected final state
                expected_state = {
                    "onboarding_completed": True,
                    "has_profile": True,
                    "user_id": self.user_id
                }
                
                validation_errors = []
                for key, expected_value in expected_state.items():
                    if key not in data:
                        validation_errors.append(f"Missing field: {key}")
                    elif data[key] != expected_value:
                        validation_errors.append(f"Field {key}: expected {expected_value}, got {data[key]}")
                
                if validation_errors:
                    self.log_test_result(
                        "Final Onboarding Status",
                        False,
                        {"validation_errors": validation_errors, "response": data},
                        "Final onboarding status validation failed"
                    )
                    return False
                
                self.log_test_result(
                    "Final Onboarding Status",
                    True,
                    {"final_status": data}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Final Onboarding Status",
                False,
                error=f"Exception during final onboarding status check: {str(e)}"
            )
            return False
    
    async def test_bypass_prevention(self) -> bool:
        """Test that users cannot bypass onboarding by accessing protected endpoints"""
        try:
            print("🧪 Testing Bypass Prevention...")
            
            # Create a new user without completing onboarding
            bypass_email = f"bypass_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            registration_data = {
                "email": bypass_email,
                "password": TEST_PASSWORD,
                "full_name": "Bypass Test User"
            }
            
            async with self.session.post(
                f"{BASE_URL}/auth/register",
                json=registration_data
            ) as response:
                if response.status != 201:
                    self.log_test_result(
                        "Bypass Prevention",
                        False,
                        error="Failed to create test user for bypass prevention test"
                    )
                    return False
                
                data = await response.json()
                bypass_token = data["access_token"]
            
            # Try to access protected endpoints that should require completed onboarding
            headers = {"Authorization": f"Bearer {bypass_token}"}
            protected_endpoints = [
                "/pantry/items",
                "/recipes/",
                "/meal-plans/",
                "/shopping-lists/"
            ]
            
            bypass_attempts = []
            for endpoint in protected_endpoints:
                try:
                    async with self.session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                        if response.status == 200:
                            # This should not happen - user should be blocked
                            bypass_attempts.append({
                                "endpoint": endpoint,
                                "status": response.status,
                                "allowed": True
                            })
                        else:
                            # This is expected - user should be blocked
                            bypass_attempts.append({
                                "endpoint": endpoint,
                                "status": response.status,
                                "allowed": False
                            })
                except Exception as e:
                    bypass_attempts.append({
                        "endpoint": endpoint,
                        "error": str(e),
                        "allowed": False
                    })
            
            # Check if any bypasses were successful
            successful_bypasses = [attempt for attempt in bypass_attempts if attempt.get("allowed", False)]
            
            if successful_bypasses:
                self.log_test_result(
                    "Bypass Prevention",
                    False,
                    {"successful_bypasses": successful_bypasses, "all_attempts": bypass_attempts},
                    f"Found {len(successful_bypasses)} successful bypass attempts"
                )
                return False
            
            self.log_test_result(
                "Bypass Prevention",
                True,
                {"blocked_attempts": len(bypass_attempts)}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Bypass Prevention",
                False,
                error=f"Exception during bypass prevention test: {str(e)}"
            )
            return False
    
    async def test_authentication_validation(self) -> bool:
        """Test authentication token validation"""
        try:
            print("🧪 Testing Authentication Validation...")
            
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            
            async with self.session.get(
                f"{BASE_URL}/profile/onboarding-status",
                headers=invalid_headers
            ) as response:
                if response.status == 200:
                    self.log_test_result(
                        "Authentication Validation",
                        False,
                        {"status_code": response.status},
                        "Invalid token was accepted"
                    )
                    return False
            
            # Test with no token
            async with self.session.get(f"{BASE_URL}/profile/onboarding-status") as response:
                if response.status == 200:
                    self.log_test_result(
                        "Authentication Validation",
                        False,
                        {"status_code": response.status},
                        "Request without token was accepted"
                    )
                    return False
            
            # Test with valid token (should work)
            if self.access_token:
                valid_headers = {"Authorization": f"Bearer {self.access_token}"}
                async with self.session.get(
                    f"{BASE_URL}/profile/onboarding-status",
                    headers=valid_headers
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            "Authentication Validation",
                            False,
                            {"status_code": response.status},
                            "Valid token was rejected"
                        )
                        return False
            
            self.log_test_result(
                "Authentication Validation",
                True,
                {"invalid_token_blocked": True, "no_token_blocked": True, "valid_token_accepted": True}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Authentication Validation",
                False,
                error=f"Exception during authentication validation test: {str(e)}"
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🚀 Starting Comprehensive Sign-up Workflow Testing")
        print("=" * 60)
        
        # Run tests in sequence
        test_methods = [
            self.test_user_registration,
            self.test_onboarding_status_check,
            self.test_plan_selection,
            self.test_profile_update,
            self.test_onboarding_completion,
            self.test_final_onboarding_status,
            self.test_bypass_prevention,
            self.test_authentication_validation
        ]
        
        results = []
        for test_method in test_methods:
            try:
                success = await test_method()
                results.append(success)
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_method.__name__}: {str(e)}")
                results.append(False)
        
        # Generate summary
        total_tests = len(results)
        passed_tests = sum(results)
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results,
            "test_email": TEST_EMAIL,
            "test_timestamp": datetime.now().isoformat()
        }
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        return summary

async def main():
    """Main test execution function"""
    try:
        async with SignupWorkflowTester() as tester:
            results = await tester.run_all_tests()
            
            # Save results to file
            results_file = f"signup_workflow_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📄 Detailed results saved to: {results_file}")
            
            # Exit with appropriate code
            if results["failed_tests"] > 0:
                print("\n🚨 Some tests failed. Please review the results above.")
                sys.exit(1)
            else:
                print("\n✅ All tests passed successfully!")
                sys.exit(0)
                
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())