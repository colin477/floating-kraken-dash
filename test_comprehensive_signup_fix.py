#!/usr/bin/env python3
"""
Comprehensive testing of the signup bug fix
Tests the critical order of operations fix: password validation BEFORE email checking
"""

import requests
import json
import sys
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
SIGNUP_ENDPOINT = f"{BASE_URL}/api/v1/auth/signup"

def test_weak_password_scenarios():
    """Test various weak password scenarios that should return HTTP 400"""
    print("🔍 Testing Weak Password Scenarios...")
    
    weak_password_tests = [
        {
            "name": "Too Short Password",
            "email": "test1@example.com",
            "password": "Abc1!",  # Only 5 characters
            "full_name": "Test User 1",
            "expected_status": 400,
            "expected_error_contains": "at least 8 characters"
        },
        {
            "name": "No Uppercase",
            "email": "test2@example.com", 
            "password": "abcd1234!",  # No uppercase
            "full_name": "Test User 2",
            "expected_status": 400,
            "expected_error_contains": "uppercase letter"
        },
        {
            "name": "No Lowercase",
            "email": "test3@example.com",
            "password": "ABCD1234!",  # No lowercase
            "full_name": "Test User 3", 
            "expected_status": 400,
            "expected_error_contains": "lowercase letter"
        },
        {
            "name": "No Digit",
            "email": "test4@example.com",
            "password": "AbcdEfgh!",  # No digit
            "full_name": "Test User 4",
            "expected_status": 400,
            "expected_error_contains": "digit"
        },
        {
            "name": "No Special Character",
            "email": "test5@example.com",
            "password": "Abcd1234",  # No special character
            "full_name": "Test User 5",
            "expected_status": 400,
            "expected_error_contains": "special character"
        },
        {
            "name": "Common Password",
            "email": "test6@example.com",
            "password": "Password123!",  # Contains "password"
            "full_name": "Test User 6",
            "expected_status": 400,
            "expected_error_contains": "common"
        }
    ]
    
    results = []
    
    for test in weak_password_tests:
        print(f"\n  Testing: {test['name']}")
        
        payload = {
            "email": test["email"],
            "password": test["password"],
            "full_name": test["full_name"]
        }
        
        try:
            response = requests.post(SIGNUP_ENDPOINT, json=payload, timeout=10)
            
            result = {
                "test_name": test["name"],
                "expected_status": test["expected_status"],
                "actual_status": response.status_code,
                "response_body": response.text,
                "passed": False
            }
            
            # Check status code
            if response.status_code == test["expected_status"]:
                # Check error message contains expected text
                if test["expected_error_contains"].lower() in response.text.lower():
                    result["passed"] = True
                    print(f"    ✅ PASS - Got HTTP {response.status_code} with expected error message")
                else:
                    print(f"    ❌ FAIL - Got HTTP {response.status_code} but error message doesn't contain '{test['expected_error_contains']}'")
                    print(f"    Response: {response.text}")
            else:
                print(f"    ❌ FAIL - Expected HTTP {test['expected_status']}, got HTTP {response.status_code}")
                print(f"    Response: {response.text}")
            
            results.append(result)
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ ERROR - Request failed: {e}")
            results.append({
                "test_name": test["name"],
                "expected_status": test["expected_status"],
                "actual_status": "ERROR",
                "response_body": str(e),
                "passed": False
            })
    
    return results

def test_strong_password_new_email():
    """Test strong password with new email - should succeed with HTTP 201"""
    print("\n🔍 Testing Strong Password with New Email...")
    
    test_data = {
        "email": "newuser@example.com",
        "password": "StrongPass123!",
        "full_name": "New User"
    }
    
    try:
        response = requests.post(SIGNUP_ENDPOINT, json=test_data, timeout=10)
        
        if response.status_code == 201:
            print("    ✅ PASS - New user created successfully with HTTP 201")
            response_data = response.json()
            if "access_token" in response_data and "user" in response_data:
                print("    ✅ PASS - Response contains access_token and user data")
                return {"passed": True, "status": 201, "response": response_data}
            else:
                print("    ❌ FAIL - Response missing access_token or user data")
                return {"passed": False, "status": 201, "response": response.text}
        else:
            print(f"    ❌ FAIL - Expected HTTP 201, got HTTP {response.status_code}")
            print(f"    Response: {response.text}")
            return {"passed": False, "status": response.status_code, "response": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return {"passed": False, "status": "ERROR", "response": str(e)}

def test_strong_password_existing_email():
    """Test strong password with existing email - should return HTTP 409"""
    print("\n🔍 Testing Strong Password with Existing Email...")
    
    # First, create a user
    first_user_data = {
        "email": "existing@example.com",
        "password": "FirstUser123!",
        "full_name": "First User"
    }
    
    try:
        # Create first user
        first_response = requests.post(SIGNUP_ENDPOINT, json=first_user_data, timeout=10)
        print(f"    First user creation: HTTP {first_response.status_code}")
        
        # Now try to create second user with same email but different password
        second_user_data = {
            "email": "existing@example.com",  # Same email
            "password": "SecondUser456!",     # Different strong password
            "full_name": "Second User"
        }
        
        second_response = requests.post(SIGNUP_ENDPOINT, json=second_user_data, timeout=10)
        
        if second_response.status_code == 409:
            if "already registered" in second_response.text.lower():
                print("    ✅ PASS - Got HTTP 409 with 'Email already registered' message")
                return {"passed": True, "status": 409, "response": second_response.text}
            else:
                print("    ❌ FAIL - Got HTTP 409 but wrong error message")
                print(f"    Response: {second_response.text}")
                return {"passed": False, "status": 409, "response": second_response.text}
        else:
            print(f"    ❌ FAIL - Expected HTTP 409, got HTTP {second_response.status_code}")
            print(f"    Response: {second_response.text}")
            return {"passed": False, "status": second_response.status_code, "response": second_response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return {"passed": False, "status": "ERROR", "response": str(e)}

def test_original_failing_scenario():
    """Test the exact scenario that was failing before the fix"""
    print("\n🔍 Testing Original Failing Scenario...")
    print("    This tests weak password + existing email to ensure password validation happens FIRST")
    
    # First create a user with strong password
    setup_user = {
        "email": "original@example.com",
        "password": "SetupUser123!",
        "full_name": "Setup User"
    }
    
    try:
        # Create the setup user
        setup_response = requests.post(SIGNUP_ENDPOINT, json=setup_user, timeout=10)
        print(f"    Setup user creation: HTTP {setup_response.status_code}")
        
        # Now try to register with WEAK password and SAME email
        # Before fix: would return "Email already registered" (HTTP 409)
        # After fix: should return password validation error (HTTP 400)
        failing_user = {
            "email": "original@example.com",  # Same email (exists)
            "password": "weak",               # Weak password (multiple issues)
            "full_name": "Failing User"
        }
        
        failing_response = requests.post(SIGNUP_ENDPOINT, json=failing_user, timeout=10)
        
        if failing_response.status_code == 400:
            if "password" in failing_response.text.lower() and "validation" in failing_response.text.lower():
                print("    ✅ PASS - Got HTTP 400 with password validation error (not email conflict)")
                print("    ✅ CRITICAL FIX VERIFIED - Password validation happens BEFORE email checking")
                return {"passed": True, "status": 400, "response": failing_response.text}
            else:
                print("    ❌ FAIL - Got HTTP 400 but not password validation error")
                print(f"    Response: {failing_response.text}")
                return {"passed": False, "status": 400, "response": failing_response.text}
        elif failing_response.status_code == 409:
            print("    ❌ CRITICAL FAIL - Got HTTP 409 (email conflict) instead of HTTP 400 (password validation)")
            print("    ❌ This indicates the fix is NOT working - email checking still happens first")
            print(f"    Response: {failing_response.text}")
            return {"passed": False, "status": 409, "response": failing_response.text}
        else:
            print(f"    ❌ FAIL - Expected HTTP 400, got HTTP {failing_response.status_code}")
            print(f"    Response: {failing_response.text}")
            return {"passed": False, "status": failing_response.status_code, "response": failing_response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return {"passed": False, "status": "ERROR", "response": str(e)}

def test_edge_cases():
    """Test edge cases for password validation"""
    print("\n🔍 Testing Password Validation Edge Cases...")
    
    edge_cases = [
        {
            "name": "Exactly 8 Characters (Minimum)",
            "email": "edge1@example.com",
            "password": "Abcd123!",  # Exactly 8 chars, meets all requirements
            "full_name": "Edge Case 1",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Multiple Special Characters",
            "email": "edge2@example.com",
            "password": "Complex!@#123Abc",  # Multiple special chars
            "full_name": "Edge Case 2",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Very Long Password",
            "email": "edge3@example.com",
            "password": "VeryLongPassword123!WithManyCharacters",  # Very long
            "full_name": "Edge Case 3",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Empty Password",
            "email": "edge4@example.com",
            "password": "",  # Empty
            "full_name": "Edge Case 4",
            "expected_status": 400,
            "should_pass": False
        }
    ]
    
    results = []
    
    for test in edge_cases:
        print(f"\n  Testing: {test['name']}")
        
        payload = {
            "email": test["email"],
            "password": test["password"],
            "full_name": test["full_name"]
        }
        
        try:
            response = requests.post(SIGNUP_ENDPOINT, json=payload, timeout=10)
            
            result = {
                "test_name": test["name"],
                "expected_status": test["expected_status"],
                "actual_status": response.status_code,
                "should_pass": test["should_pass"],
                "response_body": response.text,
                "passed": response.status_code == test["expected_status"]
            }
            
            if result["passed"]:
                print(f"    ✅ PASS - Got expected HTTP {response.status_code}")
            else:
                print(f"    ❌ FAIL - Expected HTTP {test['expected_status']}, got HTTP {response.status_code}")
                print(f"    Response: {response.text}")
            
            results.append(result)
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ ERROR - Request failed: {e}")
            results.append({
                "test_name": test["name"],
                "expected_status": test["expected_status"],
                "actual_status": "ERROR",
                "should_pass": test["should_pass"],
                "response_body": str(e),
                "passed": False
            })
    
    return results

def run_comprehensive_tests():
    """Run all comprehensive tests and generate report"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE SIGNUP BUG FIX TESTING")
    print("=" * 80)
    print("Testing the critical order of operations fix:")
    print("✅ Password validation now happens BEFORE email checking")
    print("✅ HTTP 400 for password validation errors")
    print("✅ HTTP 409 for email conflicts")
    print("=" * 80)
    
    all_results = {}
    
    # Test 1: Weak passwords
    all_results["weak_passwords"] = test_weak_password_scenarios()
    
    # Test 2: Strong password + new email
    all_results["strong_new_email"] = test_strong_password_new_email()
    
    # Test 3: Strong password + existing email
    all_results["strong_existing_email"] = test_strong_password_existing_email()
    
    # Test 4: Original failing scenario (CRITICAL)
    all_results["original_failing_scenario"] = test_original_failing_scenario()
    
    # Test 5: Edge cases
    all_results["edge_cases"] = test_edge_cases()
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    critical_fix_verified = False
    
    # Count weak password tests
    weak_passed = sum(1 for r in all_results["weak_passwords"] if r["passed"])
    weak_total = len(all_results["weak_passwords"])
    total_tests += weak_total
    passed_tests += weak_passed
    print(f"Weak Password Tests: {weak_passed}/{weak_total} passed")
    
    # Count other tests
    for test_category in ["strong_new_email", "strong_existing_email", "original_failing_scenario"]:
        if all_results[test_category]["passed"]:
            passed_tests += 1
            if test_category == "original_failing_scenario":
                critical_fix_verified = True
        total_tests += 1
        status = "✅ PASS" if all_results[test_category]["passed"] else "❌ FAIL"
        print(f"{test_category.replace('_', ' ').title()}: {status}")
    
    # Count edge case tests
    edge_passed = sum(1 for r in all_results["edge_cases"] if r["passed"])
    edge_total = len(all_results["edge_cases"])
    total_tests += edge_total
    passed_tests += edge_passed
    print(f"Edge Case Tests: {edge_passed}/{edge_total} passed")
    
    print("=" * 80)
    print(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if critical_fix_verified:
        print("🎉 CRITICAL FIX VERIFIED: Password validation happens BEFORE email checking")
    else:
        print("🚨 CRITICAL FIX FAILED: Order of operations issue still exists")
    
    print("=" * 80)
    
    return all_results, critical_fix_verified

if __name__ == "__main__":
    try:
        results, fix_verified = run_comprehensive_tests()
        
        # Save detailed results to file
        with open("signup_fix_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: signup_fix_test_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if fix_verified else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        sys.exit(1)