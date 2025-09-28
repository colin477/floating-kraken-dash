#!/usr/bin/env python3
"""
Focused diagnostic test to understand the current signup behavior
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth/signup"

def test_single_scenario():
    """Test a single scenario to understand the current behavior"""
    print("🔍 FOCUSED DIAGNOSTIC TEST")
    print("=" * 50)
    
    # Test 1: Weak password with unique email (should get password validation error)
    print("\n1. Testing weak password with unique email:")
    test_data = {
        "email": f"unique_test_{hash('test')}@example.com",
        "password": "weak",  # Too short, no uppercase, no special char
        "full_name": "Test User"
    }
    
    response = requests.post(BASE_URL, json=test_data, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Test 2: Strong password with unique email (should succeed)
    print("\n2. Testing strong password with unique email:")
    test_data2 = {
        "email": f"unique_test2_{hash('test2')}@example.com",
        "password": "StrongPass123!",
        "full_name": "Test User 2"
    }
    
    response2 = requests.post(BASE_URL, json=test_data2, timeout=10)
    print(f"   Status: {response2.status_code}")
    print(f"   Response: {response2.text[:200]}...")
    
    # Test 3: Strong password with existing email (should get email conflict)
    print("\n3. Testing strong password with existing email:")
    test_data3 = {
        "email": f"unique_test2_{hash('test2')}@example.com",  # Same as test 2
        "password": "AnotherStrong456!",
        "full_name": "Test User 3"
    }
    
    response3 = requests.post(BASE_URL, json=test_data3, timeout=10)
    print(f"   Status: {response3.status_code}")
    print(f"   Response: {response3.text}")
    
    # Test 4: CRITICAL - Weak password with existing email (the original bug scenario)
    print("\n4. CRITICAL TEST - Weak password with existing email:")
    test_data4 = {
        "email": f"unique_test2_{hash('test2')}@example.com",  # Same as test 2 (exists)
        "password": "weak",  # Weak password
        "full_name": "Test User 4"
    }
    
    response4 = requests.post(BASE_URL, json=test_data4, timeout=10)
    print(f"   Status: {response4.status_code}")
    print(f"   Response: {response4.text}")
    
    print("\n" + "=" * 50)
    print("ANALYSIS:")
    
    if response4.status_code == 400 and "password" in response4.text.lower():
        print("✅ FIX WORKING: Password validation happens BEFORE email checking")
    elif response4.status_code == 409 or "already registered" in response4.text.lower():
        print("❌ BUG STILL EXISTS: Email checking happens BEFORE password validation")
    elif response4.status_code == 422:
        print("⚠️  PYDANTIC VALIDATION: Model-level validation happening first")
    else:
        print(f"🤔 UNEXPECTED: Got HTTP {response4.status_code}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_single_scenario()