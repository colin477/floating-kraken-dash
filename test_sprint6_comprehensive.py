#!/usr/bin/env python3
"""
Comprehensive Sprint 6 Testing Script
Tests both Community Features and Leftover Suggestions API endpoints
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

class TestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, success, details=""):
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        if success:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        print()

def authenticate():
    """Authenticate and get access token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"Authentication failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def test_community_endpoints(headers, results):
    """Test Community API endpoints"""
    print("🏘️ Testing Community API Endpoints")
    print("=" * 60)
    
    # Test 1: Create a community post
    post_data = {
        "title": "Sprint 6 Test Post",
        "content": "Testing community features for Sprint 6",
        "post_type": "general",
        "tags": ["sprint6", "test"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/community/posts/", json=post_data, headers=headers)
        success = response.status_code == 201
        post_id = response.json().get("id") if success else None
        results.add_result("Create Community Post", success, 
                         f"Post ID: {post_id}" if post_id else f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Create Community Post", False, f"Error: {e}")
        return None
    
    if not post_id:
        return None
    
    # Test 2: Get community posts
    try:
        response = requests.get(f"{BASE_URL}/community/posts/")
        success = response.status_code == 200
        posts_count = len(response.json().get("posts", [])) if success else 0
        results.add_result("Get Community Posts", success, f"Posts found: {posts_count}")
    except Exception as e:
        results.add_result("Get Community Posts", False, f"Error: {e}")
    
    # Test 3: Get single post
    try:
        response = requests.get(f"{BASE_URL}/community/posts/{post_id}")
        success = response.status_code == 200
        results.add_result("Get Single Post", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Single Post", False, f"Error: {e}")
    
    # Test 4: Create comment on post
    comment_data = {
        "content": "This is a test comment for Sprint 6"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/community/posts/{post_id}/comments/", 
                               json=comment_data, headers=headers)
        success = response.status_code == 201
        comment_id = response.json().get("id") if success else None
        results.add_result("Create Comment", success, 
                         f"Comment ID: {comment_id}" if comment_id else f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Create Comment", False, f"Error: {e}")
        comment_id = None
    
    # Test 5: Get comments for post
    try:
        response = requests.get(f"{BASE_URL}/community/posts/{post_id}/comments/")
        success = response.status_code == 200
        comments_count = len(response.json().get("comments", [])) if success else 0
        results.add_result("Get Post Comments", success, f"Comments found: {comments_count}")
    except Exception as e:
        results.add_result("Get Post Comments", False, f"Error: {e}")
    
    if comment_id:
        # Test 6: Like comment
        try:
            response = requests.post(f"{BASE_URL}/community/comments/{comment_id}/like", headers=headers)
            success = response.status_code == 200
            results.add_result("Like Comment", success, f"Status: {response.status_code}")
        except Exception as e:
            results.add_result("Like Comment", False, f"Error: {e}")
        
        # Test 7: Get comment likes
        try:
            response = requests.get(f"{BASE_URL}/community/comments/{comment_id}/likes")
            success = response.status_code == 200
            likes_count = len(response.json().get("likes", [])) if success else 0
            results.add_result("Get Comment Likes", success, f"Likes found: {likes_count}")
        except Exception as e:
            results.add_result("Get Comment Likes", False, f"Error: {e}")
        
        # Test 8: Unlike comment
        try:
            response = requests.delete(f"{BASE_URL}/community/comments/{comment_id}/like", headers=headers)
            success = response.status_code == 200
            results.add_result("Unlike Comment", success, f"Status: {response.status_code}")
        except Exception as e:
            results.add_result("Unlike Comment", False, f"Error: {e}")
    
    # Test 9: Get community stats
    try:
        response = requests.get(f"{BASE_URL}/community/stats/overview", headers=headers)
        success = response.status_code == 200
        if success:
            stats = response.json()
            results.add_result("Get Community Stats", success, 
                             f"Posts: {stats.get('total_posts', 0)}, Comments: {stats.get('total_comments', 0)}")
        else:
            results.add_result("Get Community Stats", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Community Stats", False, f"Error: {e}")
    
    return post_id

def test_leftover_endpoints(headers, results):
    """Test Leftover Suggestions API endpoints"""
    print("🥬 Testing Leftover Suggestions API Endpoints")
    print("=" * 60)
    
    # Test 1: Get leftover suggestions (basic)
    try:
        response = requests.get(f"{BASE_URL}/leftovers/suggestions", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            suggestions_count = data.get("total_suggestions", 0)
            results.add_result("Get Basic Leftover Suggestions", success, 
                             f"Suggestions: {suggestions_count}")
        else:
            results.add_result("Get Basic Leftover Suggestions", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Basic Leftover Suggestions", False, f"Error: {e}")
    
    # Test 2: Get leftover suggestions with filters
    try:
        params = {
            "max_suggestions": 5,
            "min_match_percentage": 0.3,
            "include_substitutes": True,
            "prioritize_expiring": True
        }
        response = requests.get(f"{BASE_URL}/leftovers/suggestions", params=params, headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            suggestions_count = data.get("total_suggestions", 0)
            results.add_result("Get Filtered Leftover Suggestions", success, 
                             f"Suggestions: {suggestions_count}")
        else:
            results.add_result("Get Filtered Leftover Suggestions", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Filtered Leftover Suggestions", False, f"Error: {e}")
    
    # Test 3: Create custom suggestion filter
    try:
        filter_data = {
            "name": "Sprint 6 Test Filter",
            "description": "Test filter for Sprint 6",
            "min_match_percentage": 0.4,
            "max_prep_time_minutes": 30,
            "difficulty_levels": ["easy", "medium"],
            "include_substitutes": True,
            "prioritize_expiring": True,
            "cuisine_preferences": ["italian", "american"],
            "dietary_restrictions": ["vegetarian"]
        }
        response = requests.post(f"{BASE_URL}/leftovers/filters", json=filter_data, headers=headers)
        success = response.status_code in [200, 201]
        filter_id = response.json().get("id") if success else None
        results.add_result("Create Custom Filter", success, 
                         f"Filter ID: {filter_id}" if filter_id else f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Create Custom Filter", False, f"Error: {e}")
        filter_id = None
    
    # Test 4: Get user's custom filters
    try:
        response = requests.get(f"{BASE_URL}/leftovers/filters", headers=headers)
        success = response.status_code == 200
        if success:
            filters = response.json()
            filters_count = len(filters.get("filters", []))
            results.add_result("Get Custom Filters", success, f"Filters found: {filters_count}")
        else:
            results.add_result("Get Custom Filters", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Custom Filters", False, f"Error: {e}")
    
    # Test 5: Get suggestions with custom filter
    if filter_id:
        try:
            response = requests.get(f"{BASE_URL}/leftovers/suggestions/{filter_id}", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                suggestions_count = data.get("total_suggestions", 0)
                results.add_result("Get Suggestions with Custom Filter", success, 
                                 f"Suggestions: {suggestions_count}")
            else:
                results.add_result("Get Suggestions with Custom Filter", success, f"Status: {response.status_code}")
        except Exception as e:
            results.add_result("Get Suggestions with Custom Filter", False, f"Error: {e}")
    
    # Test 6: Get debug information
    try:
        response = requests.get(f"{BASE_URL}/leftovers/debug/matching-details", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            results.add_result("Get Debug Matching Details", success, 
                             f"Debug info available: {bool(data)}")
        else:
            results.add_result("Get Debug Matching Details", success, f"Status: {response.status_code}")
    except Exception as e:
        results.add_result("Get Debug Matching Details", False, f"Error: {e}")

def test_authentication_and_authorization(results):
    """Test authentication and authorization across endpoints"""
    print("🔐 Testing Authentication & Authorization")
    print("=" * 60)
    
    # Test 1: Access protected endpoint without token
    try:
        response = requests.get(f"{BASE_URL}/community/posts/")
        # Community posts might be public, so let's test a protected one
        response = requests.post(f"{BASE_URL}/community/posts/", json={"title": "test", "content": "test"})
        success = response.status_code == 401
        results.add_result("Reject Unauthenticated Request", success, 
                         f"Status: {response.status_code} (expected 401)")
    except Exception as e:
        results.add_result("Reject Unauthenticated Request", False, f"Error: {e}")
    
    # Test 2: Access with invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = requests.post(f"{BASE_URL}/community/posts/", 
                               json={"title": "test", "content": "test"}, 
                               headers=invalid_headers)
        success = response.status_code == 401
        results.add_result("Reject Invalid Token", success, 
                         f"Status: {response.status_code} (expected 401)")
    except Exception as e:
        results.add_result("Reject Invalid Token", False, f"Error: {e}")

def test_error_handling(headers, results):
    """Test error handling and validation"""
    print("⚠️ Testing Error Handling & Validation")
    print("=" * 60)
    
    # Test 1: Create post with invalid data
    try:
        invalid_post = {"title": "", "content": ""}  # Empty title should fail
        response = requests.post(f"{BASE_URL}/community/posts/", json=invalid_post, headers=headers)
        success = response.status_code == 422
        results.add_result("Validate Post Data", success, 
                         f"Status: {response.status_code} (expected 422)")
    except Exception as e:
        results.add_result("Validate Post Data", False, f"Error: {e}")
    
    # Test 2: Access non-existent post
    try:
        response = requests.get(f"{BASE_URL}/community/posts/507f1f77bcf86cd799439011")
        success = response.status_code == 404
        results.add_result("Handle Non-existent Post", success, 
                         f"Status: {response.status_code} (expected 404)")
    except Exception as e:
        results.add_result("Handle Non-existent Post", False, f"Error: {e}")
    
    # Test 3: Create comment with invalid data
    try:
        invalid_comment = {"content": ""}  # Empty content should fail
        response = requests.post(f"{BASE_URL}/community/posts/507f1f77bcf86cd799439011/comments/", 
                               json=invalid_comment, headers=headers)
        success = response.status_code in [404, 422]  # Either not found or validation error
        results.add_result("Validate Comment Data", success, 
                         f"Status: {response.status_code} (expected 404 or 422)")
    except Exception as e:
        results.add_result("Validate Comment Data", False, f"Error: {e}")

def test_performance_and_edge_cases(headers, results):
    """Test performance and edge cases"""
    print("⚡ Testing Performance & Edge Cases")
    print("=" * 60)
    
    # Test 1: Large pagination request
    try:
        start_time = datetime.now()
        response = requests.get(f"{BASE_URL}/community/posts/?skip=0&limit=100")
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        success = response.status_code == 200 and response_time < 5.0
        results.add_result("Large Pagination Performance", success, 
                         f"Response time: {response_time:.2f}s (should be < 5s)")
    except Exception as e:
        results.add_result("Large Pagination Performance", False, f"Error: {e}")
    
    # Test 2: Concurrent requests simulation
    try:
        import threading
        import time
        
        responses = []
        def make_request():
            resp = requests.get(f"{BASE_URL}/community/posts/")
            responses.append(resp.status_code)
        
        threads = []
        start_time = time.time()
        for _ in range(5):  # 5 concurrent requests
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        success = all(status == 200 for status in responses) and (end_time - start_time) < 10
        results.add_result("Concurrent Requests", success, 
                         f"All requests successful: {all(status == 200 for status in responses)}, Time: {end_time - start_time:.2f}s")
    except Exception as e:
        results.add_result("Concurrent Requests", False, f"Error: {e}")

def main():
    """Main test function"""
    print("🚀 Sprint 6 Comprehensive Test Suite")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = TestResults()
    
    # Authenticate
    print("🔐 Authenticating...")
    headers = authenticate()
    if not headers:
        print("❌ Authentication failed. Cannot proceed with tests.")
        sys.exit(1)
    print("✅ Authentication successful")
    print()
    
    # Run all test suites
    test_community_endpoints(headers, results)
    test_leftover_endpoints(headers, results)
    test_authentication_and_authorization(results)
    test_error_handling(headers, results)
    test_performance_and_edge_cases(headers, results)
    
    # Generate summary report
    print("📊 SPRINT 6 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(results.results)}")
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Success Rate: {(results.passed / len(results.results) * 100):.1f}%")
    print()
    
    # Detailed results
    print("📋 DETAILED RESULTS")
    print("=" * 80)
    for result in results.results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status:<10} {result['test']}")
        if result["details"]:
            print(f"           {result['details']}")
    
    print()
    if results.failed == 0:
        print("🎉 All Sprint 6 tests passed! Ready for production.")
        sys.exit(0)
    else:
        print(f"⚠️ {results.failed} test(s) failed. Review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()