#!/usr/bin/env python3
"""
Sprint 5 Endpoint Testing Script
Tests meal planning and shopping list endpoints with proper authentication.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "pantrytest@example.com",
    "password": "testpassword123"
}

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_result(success, message, data=None):
    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"{status}: {message}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")

def get_auth_token():
    """Get authentication token"""
    print_test_header("Authentication")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_result(True, "Authentication successful", {
                "token_type": data.get("token_type"),
                "user_id": data.get("user", {}).get("id")
            })
            return token
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return None

def test_meal_plan_endpoints(token):
    """Test meal planning endpoints"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    results = []
    
    # Test 1: List meal plans
    print_test_header("1. List Meal Plans (GET /meal-plans/)")
    try:
        response = requests.get(f"{BASE_URL}/meal-plans/", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(True, "List meal plans successful", {
                "total_count": data.get("total_count", 0),
                "items_count": len(data.get("items", []))
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("List Meal Plans", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("List Meal Plans", False))
    
    # Test 2: Generate meal plan
    print_test_header("2. Generate Meal Plan (POST /meal-plans/generate)")
    try:
        generation_request = {
            "week_starting": (date.today() + timedelta(days=7)).isoformat(),
            "budget_target": 100.0,
            "meal_types": ["dinner"],
            "days": ["monday", "tuesday", "wednesday"],
            "servings_per_meal": 4,
            "use_pantry_items": True,
            "dietary_restrictions": ["vegetarian"],
            "cuisine_preferences": ["italian"]
        }
        
        response = requests.post(f"{BASE_URL}/meal-plans/generate", json=generation_request, headers=headers)
        success = response.status_code in [200, 201]
        if success:
            data = response.json()
            print_result(True, "Generate meal plan successful", {
                "title": data.get("title"),
                "total_cost": data.get("total_estimated_cost"),
                "meals_generated": data.get("meals_generated", 0)
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("Generate Meal Plan", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("Generate Meal Plan", False))
    
    # Test 3: Create meal plan
    print_test_header("3. Create Meal Plan (POST /meal-plans/)")
    try:
        meal_plan_data = {
            "title": "Test Weekly Meal Plan",
            "description": "A test meal plan for Sprint 5 testing",
            "week_starting": (date.today() + timedelta(days=14)).isoformat(),
            "budget_target": 75.0,
            "preferences": {"test": True}
        }
        
        response = requests.post(f"{BASE_URL}/meal-plans/", json=meal_plan_data, headers=headers)
        success = response.status_code in [200, 201]
        meal_plan_id = None
        if success:
            data = response.json()
            meal_plan_id = data.get("id")
            print_result(True, "Create meal plan successful", {
                "id": meal_plan_id,
                "title": data.get("title"),
                "budget_target": data.get("budget_target")
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("Create Meal Plan", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("Create Meal Plan", False))
    
    # Test 4: Get meal plan stats
    print_test_header("4. Get Meal Plan Stats (GET /meal-plans/stats/overview)")
    try:
        response = requests.get(f"{BASE_URL}/meal-plans/stats/overview", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(True, "Get meal plan stats successful", {
                "total_meal_plans": data.get("total_meal_plans", 0),
                "active_meal_plans": data.get("active_meal_plans", 0)
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("Get Meal Plan Stats", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("Get Meal Plan Stats", False))
    
    return results

def test_shopping_list_endpoints(token):
    """Test shopping list endpoints"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    results = []
    
    # Test 1: List shopping lists
    print_test_header("5. List Shopping Lists (GET /shopping-lists/)")
    try:
        response = requests.get(f"{BASE_URL}/shopping-lists/", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(True, "List shopping lists successful", {
                "total_count": data.get("total_count", 0),
                "items_count": len(data.get("items", []))
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("List Shopping Lists", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("List Shopping Lists", False))
    
    # Test 2: Create shopping list
    print_test_header("6. Create Shopping List (POST /shopping-lists/)")
    try:
        shopping_list_data = {
            "title": "Test Weekly Shopping",
            "description": "A test shopping list for Sprint 5",
            "items": [
                {
                    "id": "item1",
                    "name": "Chicken Breast",
                    "quantity": 2.0,
                    "unit": "lbs",
                    "category": "meat",
                    "estimated_price": 8.99,
                    "store": "Local Grocery",
                    "status": "pending"
                },
                {
                    "id": "item2",
                    "name": "Broccoli",
                    "quantity": 1.0,
                    "unit": "head",
                    "category": "produce",
                    "estimated_price": 2.49,
                    "store": "Local Grocery",
                    "status": "pending"
                }
            ],
            "stores": ["Local Grocery"],
            "budget_limit": 50.0,
            "shopping_date": (date.today() + timedelta(days=2)).isoformat(),
            "tags": ["weekly", "test"]
        }
        
        response = requests.post(f"{BASE_URL}/shopping-lists/", json=shopping_list_data, headers=headers)
        success = response.status_code in [200, 201]
        shopping_list_id = None
        if success:
            data = response.json()
            shopping_list_id = data.get("id")
            print_result(True, "Create shopping list successful", {
                "id": shopping_list_id,
                "title": data.get("title"),
                "items_count": data.get("items_count", 0),
                "total_cost": data.get("total_estimated_cost", 0)
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("Create Shopping List", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("Create Shopping List", False))
    
    # Test 3: Get shopping list stats
    print_test_header("7. Get Shopping List Stats (GET /shopping-lists/stats/overview)")
    try:
        response = requests.get(f"{BASE_URL}/shopping-lists/stats/overview", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(True, "Get shopping list stats successful", {
                "total_shopping_lists": data.get("total_shopping_lists", 0),
                "active_shopping_lists": data.get("active_shopping_lists", 0)
            })
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
        results.append(("Get Shopping List Stats", success))
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        results.append(("Get Shopping List Stats", False))
    
    return results

def main():
    print("🧪 Sprint 5 Endpoint Test Suite")
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_USER['email']}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Test meal planning endpoints
    meal_plan_results = test_meal_plan_endpoints(token)
    
    # Test shopping list endpoints
    shopping_list_results = test_shopping_list_endpoints(token)
    
    # Combine all results
    all_results = meal_plan_results + shopping_list_results
    
    # Summary
    print(f"\n{'='*60}")
    print("SPRINT 5 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in all_results if success)
    total = len(all_results)
    
    for test_name, success in all_results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:<8} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All Sprint 5 tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some Sprint 5 tests failed - check the details above")
        sys.exit(1)

if __name__ == "__main__":
    main()