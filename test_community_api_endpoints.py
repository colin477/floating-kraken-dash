#!/usr/bin/env python3
"""
Test script for Community API endpoints (Comments and Likes)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
COMMUNITY_URL = f"{BASE_URL}/community"

# Test user credentials (you may need to adjust these)
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

def print_test_result(test_name, success, details=""):
    """Print formatted test result"""
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

def test_comment_endpoints(headers):
    """Test comment-related endpoints"""
    print("🧪 Testing Comment Endpoints")
    print("=" * 50)
    
    # First, create a test post
    post_data = {
        "title": "Test Post for Comments",
        "content": "This is a test post to test comment functionality",
        "post_type": "general",
        "tags": ["test", "comments"]
    }
    
    try:
        response = requests.post(f"{COMMUNITY_URL}/posts/", json=post_data, headers=headers)
        if response.status_code == 201:
            post_id = response.json()["id"]
            print_test_result("Create test post", True, f"Post ID: {post_id}")
        else:
            print_test_result("Create test post", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test_result("Create test post", False, f"Error: {e}")
        return None
    
    # Test 1: Create comment on post
    comment_data = {
        "content": "This is a test comment on the post"
    }
    
    try:
        response = requests.post(f"{COMMUNITY_URL}/posts/{post_id}/comments/", json=comment_data, headers=headers)
        success = response.status_code == 201
        comment_id = response.json().get("id") if success else None
        print_test_result("Create comment on post", success, f"Comment ID: {comment_id}" if comment_id else f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Create comment on post", False, f"Error: {e}")
        comment_id = None
    
    if not comment_id:
        return post_id
    
    # Test 2: Get comments for post
    try:
        response = requests.get(f"{COMMUNITY_URL}/posts/{post_id}/comments/")
        success = response.status_code == 200
        comments_count = len(response.json().get("comments", [])) if success else 0
        print_test_result("Get comments for post", success, f"Comments found: {comments_count}")
    except Exception as e:
        print_test_result("Get comments for post", False, f"Error: {e}")
    
    # Test 3: Get single comment
    try:
        response = requests.get(f"{COMMUNITY_URL}/comments/{comment_id}")
        success = response.status_code == 200
        print_test_result("Get single comment", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Get single comment", False, f"Error: {e}")
    
    # Test 4: Create reply to comment
    reply_data = {
        "content": "This is a reply to the comment"
    }
    
    try:
        response = requests.post(f"{COMMUNITY_URL}/comments/{comment_id}/replies/", json=reply_data, headers=headers)
        success = response.status_code == 201
        reply_id = response.json().get("id") if success else None
        print_test_result("Create reply to comment", success, f"Reply ID: {reply_id}" if reply_id else f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Create reply to comment", False, f"Error: {e}")
        reply_id = None
    
    # Test 5: Get replies to comment
    try:
        response = requests.get(f"{COMMUNITY_URL}/comments/{comment_id}/replies/")
        success = response.status_code == 200
        replies_count = len(response.json().get("comments", [])) if success else 0
        print_test_result("Get replies to comment", success, f"Replies found: {replies_count}")
    except Exception as e:
        print_test_result("Get replies to comment", False, f"Error: {e}")
    
    # Test 6: Update comment
    update_data = {
        "content": "This is an updated test comment"
    }
    
    try:
        response = requests.put(f"{COMMUNITY_URL}/comments/{comment_id}", json=update_data, headers=headers)
        success = response.status_code == 200
        print_test_result("Update comment", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Update comment", False, f"Error: {e}")
    
    return post_id, comment_id

def test_like_endpoints(headers, post_id, comment_id):
    """Test like-related endpoints"""
    print("❤️ Testing Like Endpoints")
    print("=" * 50)
    
    # Test 1: Like a comment
    try:
        response = requests.post(f"{COMMUNITY_URL}/comments/{comment_id}/like", headers=headers)
        success = response.status_code == 200
        print_test_result("Like comment", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Like comment", False, f"Error: {e}")
    
    # Test 2: Get likes for comment
    try:
        response = requests.get(f"{COMMUNITY_URL}/comments/{comment_id}/likes")
        success = response.status_code == 200
        likes_count = len(response.json().get("likes", [])) if success else 0
        print_test_result("Get comment likes", success, f"Likes found: {likes_count}")
    except Exception as e:
        print_test_result("Get comment likes", False, f"Error: {e}")
    
    # Test 3: Get likes for post
    try:
        response = requests.get(f"{COMMUNITY_URL}/posts/{post_id}/likes")
        success = response.status_code == 200
        likes_count = len(response.json().get("likes", [])) if success else 0
        print_test_result("Get post likes", success, f"Likes found: {likes_count}")
    except Exception as e:
        print_test_result("Get post likes", False, f"Error: {e}")
    
    # Test 4: Unlike comment
    try:
        response = requests.delete(f"{COMMUNITY_URL}/comments/{comment_id}/like", headers=headers)
        success = response.status_code == 200
        print_test_result("Unlike comment", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Unlike comment", False, f"Error: {e}")

def test_user_interaction_endpoints(headers, post_id, comment_id):
    """Test user interaction endpoints"""
    print("👤 Testing User Interaction Endpoints")
    print("=" * 50)
    
    # Test 1: Get post user interaction
    try:
        response = requests.get(f"{COMMUNITY_URL}/posts/{post_id}/user-interaction", headers=headers)
        success = response.status_code == 200
        interaction_data = response.json() if success else {}
        print_test_result("Get post user interaction", success, f"Has liked: {interaction_data.get('has_liked')}, Has commented: {interaction_data.get('has_commented')}")
    except Exception as e:
        print_test_result("Get post user interaction", False, f"Error: {e}")
    
    # Test 2: Get comment user interaction
    try:
        response = requests.get(f"{COMMUNITY_URL}/comments/{comment_id}/user-interaction", headers=headers)
        success = response.status_code == 200
        interaction_data = response.json() if success else {}
        print_test_result("Get comment user interaction", success, f"Has liked: {interaction_data.get('has_liked')}")
    except Exception as e:
        print_test_result("Get comment user interaction", False, f"Error: {e}")

def main():
    """Main test function"""
    print("🚀 Community API Endpoints Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Authenticate
    print("🔐 Authenticating...")
    headers = authenticate()
    if not headers:
        print("❌ Authentication failed. Cannot proceed with tests.")
        sys.exit(1)
    print("✅ Authentication successful")
    print()
    
    # Test comment endpoints
    result = test_comment_endpoints(headers)
    if result is None:
        print("❌ Comment tests failed. Cannot proceed with like tests.")
        sys.exit(1)
    
    if len(result) == 2:
        post_id, comment_id = result
        
        # Test like endpoints
        test_like_endpoints(headers, post_id, comment_id)
        
        # Test user interaction endpoints
        test_user_interaction_endpoints(headers, post_id, comment_id)
    else:
        post_id = result
        print("⚠️ Some comment tests failed. Skipping like and interaction tests.")
    
    print("🏁 Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()