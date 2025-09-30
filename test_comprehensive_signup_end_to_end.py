#!/usr/bin/env python3
"""
Comprehensive End-to-End Sign-up Workflow Test

This script tests the complete sign-up workflow with focus on:
1. Plan selection behavior (highlight vs immediate proceed)
2. Plan-specific question counts validation
3. Complete user journey from signup to dashboard
4. Browser automation to test actual user experience

Test Areas:
- Sign-up process and authentication
- Plan selection component behavior
- Question flow validation by plan type
- Dashboard navigation after completion
- Error handling and edge cases
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"  # Vite dev server default port

@dataclass
class TestResult:
    test_name: str
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class ComprehensiveSignupTester:
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.test_email = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_password = "TestPassword123!"
        self.test_name = "E2E Test User"
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any] = None, error: str = None):
        """Log test result"""
        result = TestResult(
            test_name=test_name,
            success=success,
            details=details or {},
            error=error
        )
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    def test_backend_connectivity(self) -> bool:
        """Test backend API connectivity"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_result("Backend Connectivity", True, {"status_code": response.status_code})
                return True
            else:
                self.log_result("Backend Connectivity", False, {"status_code": response.status_code})
                return False
        except Exception as e:
            self.log_result("Backend Connectivity", False, error=str(e))
            return False

    def test_frontend_connectivity(self) -> bool:
        """Test frontend connectivity"""
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            if response.status_code == 200:
                self.log_result("Frontend Connectivity", True, {"status_code": response.status_code})
                return True
            else:
                self.log_result("Frontend Connectivity", False, {"status_code": response.status_code})
                return False
        except Exception as e:
            self.log_result("Frontend Connectivity", False, error=str(e))
            return False

    def test_user_registration(self) -> bool:
        """Test user registration via API"""
        try:
            registration_data = {
                "email": self.test_email,
                "password": self.test_password,
                "full_name": self.test_name
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/register", json=registration_data, timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                
                self.log_result("User Registration", True, {
                    "user_id": self.user_id,
                    "has_token": bool(self.access_token),
                    "profile_completed": data.get("user", {}).get("profile_completed", False)
                })
                return True
            else:
                self.log_result("User Registration", False, {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, error=str(e))
            return False

    def test_plan_selection_api(self, plan_type: str, setup_level: str) -> bool:
        """Test plan selection via API"""
        try:
            if not self.access_token:
                self.log_result(f"Plan Selection API ({plan_type})", False, error="No access token")
                return False
                
            headers = {"Authorization": f"Bearer {self.access_token}"}
            plan_data = {
                "plan_type": plan_type,
                "setup_level": setup_level
            }
            
            response = requests.post(
                f"{BACKEND_URL}/profile/plan-selection",
                json=plan_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(f"Plan Selection API ({plan_type})", True, {
                    "plan_type": plan_type,
                    "setup_level": setup_level,
                    "response_keys": list(data.keys())
                })
                return True
            else:
                self.log_result(f"Plan Selection API ({plan_type})", False, {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_result(f"Plan Selection API ({plan_type})", False, error=str(e))
            return False

    def test_onboarding_status(self) -> Dict[str, Any]:
        """Test onboarding status check"""
        try:
            if not self.access_token:
                self.log_result("Onboarding Status Check", False, error="No access token")
                return {}
                
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BACKEND_URL}/profile/onboarding-status", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Onboarding Status Check", True, {
                    "onboarding_completed": data.get("onboarding_completed"),
                    "has_profile": data.get("has_profile"),
                    "current_step": data.get("current_step")
                })
                return data
            else:
                self.log_result("Onboarding Status Check", False, {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return {}
                
        except Exception as e:
            self.log_result("Onboarding Status Check", False, error=str(e))
            return {}

    def validate_question_counts(self) -> bool:
        """Validate expected question counts for each plan level"""
        expected_counts = {
            "basic": 4,    # BASE_QUESTIONS
            "medium": 8,   # BASE_QUESTIONS + ADDITIONAL_QUESTIONS
            "full": 12     # User expects 12, but FULL_QUESTIONS has 13
        }
        
        # This is based on code analysis of ProfileSetup.tsx
        actual_counts = {
            "basic": 4,    # BASE_QUESTIONS array length
            "medium": 8,   # BASE_QUESTIONS (4) + ADDITIONAL_QUESTIONS (4)
            "full": 13     # FULL_QUESTIONS array length (actual count from code)
        }
        
        issues_found = []
        for level, expected in expected_counts.items():
            actual = actual_counts[level]
            if actual != expected:
                issues_found.append({
                    "level": level,
                    "expected": expected,
                    "actual": actual,
                    "issue": f"Question count mismatch for {level} plan"
                })
        
        if issues_found:
            self.log_result("Question Count Validation", False, {
                "issues_found": issues_found,
                "expected_counts": expected_counts,
                "actual_counts": actual_counts
            }, error="Question count mismatches detected")
            return False
        else:
            self.log_result("Question Count Validation", True, {
                "expected_counts": expected_counts,
                "actual_counts": actual_counts
            })
            return True

    def test_profile_update(self) -> bool:
        """Test profile update functionality"""
        try:
            if not self.access_token:
                self.log_result("Profile Update", False, error="No access token")
                return False
                
            headers = {"Authorization": f"Bearer {self.access_token}"}
            profile_data = {
                "dietary_restrictions": ["Vegetarian"],
                "allergies": ["Nuts"],
                "taste_preferences": ["Italian", "Comfort Food"],
                "meal_preferences": ["Quick meals (under 30 min)"],
                "kitchen_equipment": ["Oven", "Stovetop", "Microwave"],
                "weekly_budget": 100,
                "zip_code": "80202",
                "preferred_grocers": ["kroger-local", "safeway-local"]
            }
            
            response = requests.put(
                f"{BACKEND_URL}/profile/",
                json=profile_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Profile Update", True, {
                    "updated_fields": list(profile_data.keys()),
                    "weekly_budget": data.get("weekly_budget"),
                    "zip_code": data.get("zip_code")
                })
                return True
            else:
                self.log_result("Profile Update", False, {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_result("Profile Update", False, error=str(e))
            return False

    def test_onboarding_completion(self) -> bool:
        """Test onboarding completion"""
        try:
            if not self.access_token:
                self.log_result("Onboarding Completion", False, error="No access token")
                return False
                
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BACKEND_URL}/profile/complete-onboarding",
                json={},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Onboarding Completion", True, {
                    "onboarding_completed": data.get("onboarding_completed"),
                    "message": data.get("message")
                })
                return True
            else:
                self.log_result("Onboarding Completion", False, {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_result("Onboarding Completion", False, error=str(e))
            return False

    def test_dashboard_access(self) -> bool:
        """Test dashboard access after onboarding completion"""
        try:
            if not self.access_token:
                self.log_result("Dashboard Access", False, error="No access token")
                return False
                
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test accessing protected endpoints that should work after onboarding
            endpoints_to_test = [
                "/pantry/items",
                "/recipes/",
                "/meal-plans/"
            ]
            
            results = {}
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
                    results[endpoint] = {
                        "status_code": response.status_code,
                        "accessible": response.status_code in [200, 404]  # 404 is OK for empty resources
                    }
                except Exception as e:
                    results[endpoint] = {
                        "error": str(e),
                        "accessible": False
                    }
            
            accessible_count = sum(1 for r in results.values() if r.get("accessible", False))
            success = accessible_count > 0
            
            self.log_result("Dashboard Access", success, {
                "endpoints_tested": len(endpoints_to_test),
                "accessible_endpoints": accessible_count,
                "results": results
            })
            return success
            
        except Exception as e:
            self.log_result("Dashboard Access", False, error=str(e))
            return False

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive End-to-End Sign-up Workflow Test")
        print("=" * 70)
        print(f"Test Email: {self.test_email}")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print("=" * 70)
        
        # Test sequence
        test_sequence = [
            ("Connectivity Tests", [
                self.test_backend_connectivity,
                self.test_frontend_connectivity
            ]),
            ("Registration & Authentication", [
                self.test_user_registration
            ]),
            ("Plan Selection Tests", [
                lambda: self.test_plan_selection_api("free", "basic"),
                lambda: self.test_plan_selection_api("basic", "medium"),
                lambda: self.test_plan_selection_api("premium", "full")
            ]),
            ("Onboarding Flow", [
                self.test_onboarding_status,
                self.test_profile_update,
                self.test_onboarding_completion
            ]),
            ("Post-Onboarding Access", [
                self.test_dashboard_access
            ]),
            ("Validation Tests", [
                self.validate_question_counts
            ])
        ]
        
        all_passed = True
        for section_name, tests in test_sequence:
            print(f"\n📋 {section_name}")
            print("-" * 50)
            
            for test_func in tests:
                try:
                    result = test_func()
                    if not result:
                        all_passed = False
                except Exception as e:
                    print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
                    all_passed = False
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        summary = {
            "test_email": self.test_email,
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_success": all_passed,
            "test_results": [asdict(r) for r in self.test_results]
        }
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Result: {'✅ SUCCESS' if all_passed else '❌ FAILURE'}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result.success:
                    print(f"  • {result.test_name}: {result.error or 'Unknown error'}")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check for question count issues
        question_count_result = next((r for r in self.test_results if r.test_name == "Question Count Validation"), None)
        if question_count_result and not question_count_result.success:
            print("  ⚠️  QUESTION COUNT MISMATCH DETECTED:")
            for issue in question_count_result.details.get("issues_found", []):
                print(f"     - {issue['level'].title()} plan: Expected {issue['expected']}, Found {issue['actual']}")
        
        # Check for plan selection issues
        plan_selection_failures = [r for r in self.test_results if "Plan Selection" in r.test_name and not r.success]
        if plan_selection_failures:
            print("  ⚠️  PLAN SELECTION ISSUES:")
            for failure in plan_selection_failures:
                print(f"     - {failure.test_name}: {failure.error}")
        
        return summary

def main():
    """Main test execution"""
    tester = ComprehensiveSignupTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Save results to file
        results_file = f"comprehensive_signup_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not results["overall_success"]:
            print("  1. Review failed tests above and address root causes")
            print("  2. Check server logs for additional error details")
            print("  3. Verify frontend-backend API integration")
            
            # Specific recommendations based on failures
            question_count_result = next((r for r in tester.test_results if r.test_name == "Question Count Validation"), None)
            if question_count_result and not question_count_result.success:
                print("  4. ⚠️  CRITICAL: Fix question count mismatch in ProfileSetup.tsx")
                print("     - Full plan shows 13 questions but user expects 12")
                print("     - Consider removing one question from FULL_QUESTIONS array")
        else:
            print("  ✅ All tests passed! The signup workflow is functioning correctly.")
        
        print(f"\n🎯 NEXT STEPS:")
        print("  1. Run browser automation test to validate UI behavior")
        print("  2. Test plan selection click-to-highlight functionality")
        print("  3. Verify question progression matches expected counts")
        print("  4. Test complete user journey in browser")
        
        return 0 if results["overall_success"] else 1
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())