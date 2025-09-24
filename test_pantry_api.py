#!/usr/bin/env python3
"""
Pantry API Testing Script
Tests all 8 pantry endpoints with proper error handling and output formatting.
"""

import requests
import json
import sys
from datetime import datetime

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

def test_authentication():
    print_test_header("1. Authentication/Login")
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
                "expires_in": data.get("expires_in"),
                "user_id": data.get("user", {}).get("id")
            })
            return token
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return None

def test_list_pantry_items(token):
    print_test_header("2. List Pantry Items (GET /pantry/)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/pantry/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "List pantry items successful", {
                "total_count": data.get("total_count", 0),
                "items_count": len(data.get("items", []))
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_create_pantry_item(token):
    print_test_header("3. Create Pantry Item (POST /pantry/)")
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        new_item = {
            "name": "Test Apples",
            "category": "produce",
            "quantity": 5.0,
            "unit": "piece",
            "expiration_date": "2025-01-15",
            "purchase_date": "2025-01-01",
            "notes": "Fresh red apples for testing"
        }
        
        response = requests.post(f"{BASE_URL}/pantry/", json=new_item, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            item_id = data.get("id")
            print_result(True, "Create pantry item successful", {
                "item_id": item_id,
                "name": data.get("name"),
                "quantity": data.get("quantity")
            })
            return item_id
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return None

def test_get_specific_item(token, item_id):
    print_test_header(f"4. Get Specific Item (GET /pantry/{item_id})")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/pantry/{item_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Get specific item successful", {
                "item_id": data.get("id"),
                "name": data.get("name"),
                "category": data.get("category")
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_update_item(token, item_id):
    print_test_header(f"5. Update Item (PUT /pantry/{item_id})")
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        update_data = {
            "quantity": 3.0,
            "notes": "Updated quantity - some apples consumed"
        }
        
        response = requests.put(f"{BASE_URL}/pantry/{item_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Update item successful", {
                "item_id": data.get("id"),
                "updated_quantity": data.get("quantity"),
                "updated_notes": data.get("notes")
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_expiring_items(token):
    print_test_header("6. Get Expiring Items (GET /pantry/expiring/items)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/pantry/expiring/items", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Get expiring items successful", {
                "expiring_soon_count": len(data.get("expiring_soon", [])),
                "expired_count": len(data.get("expired", []))
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_pantry_stats(token):
    print_test_header("7. Get Pantry Statistics (GET /pantry/stats/overview)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/pantry/stats/overview", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Get pantry stats successful", {
                "total_items": data.get("total_items"),
                "expiring_soon_count": data.get("expiring_soon_count"),
                "categories": data.get("categories", {})
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_search_items(token):
    print_test_header("8. Search Items (GET /pantry/search/items)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/pantry/search/items?q=apple", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Search items successful", {
                "search_query": "apple",
                "results_count": len(data) if isinstance(data, list) else data.get("count", 0)
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_delete_item(token, item_id):
    print_test_header(f"9. Delete Item (DELETE /pantry/{item_id})")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{BASE_URL}/pantry/{item_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Delete item successful", {
                "message": data.get("message", "Item deleted successfully")
            })
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def main():
    print("🧪 EZ Eatin' Pantry API Test Suite")
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_USER['email']}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test results tracking
    results = []
    
    # 1. Authentication
    token = test_authentication()
    results.append(("Authentication", token is not None))
    
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # 2. List pantry items
    success = test_list_pantry_items(token)
    results.append(("List Pantry Items", success))
    
    # 3. Create pantry item
    item_id = test_create_pantry_item(token)
    results.append(("Create Pantry Item", item_id is not None))
    
    # 4. Get specific item (only if create succeeded)
    if item_id:
        success = test_get_specific_item(token, item_id)
        results.append(("Get Specific Item", success))
        
        # 5. Update item
        success = test_update_item(token, item_id)
        results.append(("Update Item", success))
    else:
        results.append(("Get Specific Item", False))
        results.append(("Update Item", False))
    
    # 6. Get expiring items
    success = test_expiring_items(token)
    results.append(("Get Expiring Items", success))
    
    # 7. Get pantry statistics
    success = test_pantry_stats(token)
    results.append(("Get Pantry Stats", success))
    
    # 8. Search items
    success = test_search_items(token)
    results.append(("Search Items", success))
    
    # 9. Delete item (only if create succeeded)
    if item_id:
        success = test_delete_item(token, item_id)
        results.append(("Delete Item", success))
    else:
        results.append(("Delete Item", False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:<8} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed - check the details above")
        sys.exit(1)

if __name__ == "__main__":
    main()