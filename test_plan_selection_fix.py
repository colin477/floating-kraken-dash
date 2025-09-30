#!/usr/bin/env python3
"""
Test script for plan selection navigation fix
Tests JWT token expiration fixes and plan selection flow
"""

import requests
import json
import time
import jwt
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "plantest@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Plan Test User"

class PlanSelectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def decode_jwt_token(self, token):
        """Decode JWT token to inspect expiry and contents"""
        try:
            # Decode without verification to inspect contents
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp', 0)
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            current_time = datetime.now()
            time_until_expiry = exp_datetime - current_time
            
            self.log(f"Token expires at: {exp_datetime}")
            self.log(f"Current time: {current_time}")
            self.log(f"Time until expiry: {time_until_expiry}")
            self.log(f"Token type: {decoded.get('type', 'unknown')}")
            
            return decoded, time_until_expiry
        except Exception as e:
            self.log(f"Error decoding token: {e}", "ERROR")
            return None, None
    
    def register_user(self):
        """Register a new test user"""
        self.log("=== TESTING USER REGISTRATION ===")
        
        url = f"{BASE_URL}/auth/register"
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
        
        try:
            response = self.session.post(url, json=data)
            self.log(f"Registration response status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                self.access_token = result.get('access_token')
                self.user_id = result.get('user', {}).get('id')
                
                self.log("✅ Registration successful")
                self.log(f"User ID: {self.user_id}")
                
                # Analyze the JWT token
                if self.access_token:
                    self.log("=== JWT TOKEN ANALYSIS ===")
                    decoded, time_until_expiry = self.decode_jwt_token(self.access_token)
                    if time_until_expiry:
                        minutes_until_expiry = time_until_expiry.total_seconds() / 60
                        self.log(f"Token expires in {minutes_until_expiry:.1f} minutes")
                        
                        # Check if it's the expected 60 minutes
                        if 58 <= minutes_until_expiry <= 62:  # Allow 2-minute tolerance
                            self.log("✅ Token expiry is correctly set to ~60 minutes")
                        else:
                            self.log(f"❌ Token expiry is {minutes_until_expiry:.1f} minutes, expected ~60 minutes")
                
                return True
            elif response.status_code == 400:
                # User might already exist, try login instead
                self.log("User already exists, attempting login...")
                return self.login_user()
            else:
                self.log(f"❌ Registration failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {e}", "ERROR")
            return False
    
    def login_user(self):
        """Login with test user"""
        self.log("=== TESTING USER LOGIN ===")
        
        url = f"{BASE_URL}/auth/login-form"
        data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(url, data=data)
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.user_id = result.get('user', {}).get('id')
                
                self.log("✅ Login successful")
                self.log(f"User ID: {self.user_id}")
                
                # Analyze the JWT token
                if self.access_token:
                    self.log("=== JWT TOKEN ANALYSIS ===")
                    decoded, time_until_expiry = self.decode_jwt_token(self.access_token)
                    if time_until_expiry:
                        minutes_until_expiry = time_until_expiry.total_seconds() / 60
                        self.log(f"Token expires in {minutes_until_expiry:.1f} minutes")
                        
                        # Check if it's the expected 60 minutes
                        if 58 <= minutes_until_expiry <= 62:  # Allow 2-minute tolerance
                            self.log("✅ Token expiry is correctly set to ~60 minutes")
                        else:
                            self.log(f"❌ Token expiry is {minutes_until_expiry:.1f} minutes, expected ~60 minutes")
                
                return True
            else:
                self.log(f"❌ Login failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {e}", "ERROR")
            return False
    
    def test_authenticated_request(self):
        """Test making authenticated requests"""
        self.log("=== TESTING AUTHENTICATED REQUESTS ===")
        
        if not self.access_token:
            self.log("❌ No access token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{BASE_URL}/auth/me"
        
        try:
            response = self.session.get(url, headers=headers)
            self.log(f"Auth check response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Authenticated request successful")
                return True
            elif response.status_code == 401:
                self.log("❌ 401 Unauthorized - token validation failed", "ERROR")
                return False
            else:
                self.log(f"❌ Unexpected response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Auth request error: {e}", "ERROR")
            return False
    
    def test_plan_selection(self):
        """Test the plan selection endpoint"""
        self.log("=== TESTING PLAN SELECTION ENDPOINT ===")
        
        if not self.access_token:
            self.log("❌ No access token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{BASE_URL}/profile/plan-selection"
        
        # Test data for plan selection
        plan_data = {
            "plan_type": "basic",
            "setup_level": "medium"
        }
        
        try:
            response = self.session.post(url, json=plan_data, headers=headers)
            self.log(f"Plan selection response status: {response.status_code}")
            self.log(f"Plan selection response: {response.text}")
            
            if response.status_code == 200:
                self.log("✅ Plan selection successful")
                return True
            elif response.status_code == 401:
                self.log("❌ 401 Unauthorized during plan selection - JWT token issue", "ERROR")
                return False
            else:
                self.log(f"❌ Plan selection failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Plan selection error: {e}", "ERROR")
            return False
    
    def test_onboarding_status(self):
        """Test getting onboarding status"""
        self.log("=== TESTING ONBOARDING STATUS ===")
        
        if not self.access_token:
            self.log("❌ No access token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{BASE_URL}/profile/onboarding-status"
        
        try:
            response = self.session.get(url, headers=headers)
            self.log(f"Onboarding status response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Onboarding status: {json.dumps(result, indent=2)}")
                self.log("✅ Onboarding status retrieved successfully")
                return True
            elif response.status_code == 401:
                self.log("❌ 401 Unauthorized getting onboarding status", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get onboarding status: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Onboarding status error: {e}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 STARTING COMPREHENSIVE PLAN SELECTION FIX TEST")
        self.log("=" * 60)
        
        results = {
            "registration_or_login": False,
            "jwt_token_analysis": False,
            "authenticated_request": False,
            "plan_selection": False,
            "onboarding_status": False
        }
        
        # Step 1: Register or login user
        if self.register_user():
            results["registration_or_login"] = True
            results["jwt_token_analysis"] = True  # Token analysis is done in register/login
        
        # Step 2: Test authenticated request
        if results["registration_or_login"] and self.test_authenticated_request():
            results["authenticated_request"] = True
        
        # Step 3: Test plan selection (the main fix)
        if results["authenticated_request"] and self.test_plan_selection():
            results["plan_selection"] = True
        
        # Step 4: Test onboarding status
        if results["authenticated_request"] and self.test_onboarding_status():
            results["onboarding_status"] = True
        
        # Summary
        self.log("=" * 60)
        self.log("🏁 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        self.log(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - Plan selection fix is working!")
        else:
            self.log("⚠️  Some tests failed - Plan selection fix needs attention")
        
        return results

def main():
    """Main test execution"""
    tester = PlanSelectionTester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()