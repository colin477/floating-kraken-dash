#!/usr/bin/env python3
"""
Test the AI recipe generation API endpoints
"""

import requests
import json

def test_api_endpoint():
    """Test the AI recipe generation API endpoint"""
    print("🧪 Testing AI Recipe Generation API Endpoint")
    print("=" * 50)
    
    # Test data
    test_data = {
        "ingredients": ["chicken", "rice", "vegetables"],
        "servings": 4,
        "cuisine_preference": "Asian",
        "difficulty_preference": "easy"
    }
    
    try:
        # Test the API endpoint
        url = "http://localhost:8000/api/v1/recipes/generate-from-ingredients"
        headers = {"Content-Type": "application/json"}
        
        print(f"📡 Making POST request to: {url}")
        print(f"📦 Request data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            recipe_data = response.json()
            print(f"✅ API Test Successful!")
            print(f"  Recipe Title: {recipe_data.get('title', 'N/A')}")
            print(f"  Recipe ID: {recipe_data.get('id', 'N/A')}")
            print(f"  Ingredients Count: {len(recipe_data.get('ingredients', []))}")
            print(f"  Instructions Count: {len(recipe_data.get('instructions', []))}")
            print(f"  Tags: {', '.join(recipe_data.get('tags', []))}")
            return True
        else:
            print(f"❌ API Test Failed!")
            print(f"  Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_service_status():
    """Test the service status endpoint"""
    print(f"\n🔍 Testing Service Status Endpoint")
    print("=" * 50)
    
    try:
        url = "http://localhost:8000/api/v1/recipes/ai-generation-status"
        response = requests.get(url, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Service Status Retrieved!")
            print(f"  Enabled: {status_data.get('enabled', 'N/A')}")
            print(f"  Demo Mode: {status_data.get('demo_mode', 'N/A')}")
            print(f"  OpenAI Available: {status_data.get('openai_available', 'N/A')}")
            return True
        else:
            print(f"❌ Service Status Test Failed!")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Service status test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API Endpoint Tests")
    print("=" * 60)
    
    # Test service status first
    status_success = test_service_status()
    
    # Test recipe generation endpoint
    api_success = test_api_endpoint()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 50)
    print(f"Service Status: {'✅ PASSED' if status_success else '❌ FAILED'}")
    print(f"Recipe Generation API: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    overall_success = status_success and api_success
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")