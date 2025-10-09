#!/usr/bin/env python3
"""
Test script to reproduce MongoDB connection timeout issues during user registration
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import random
import string

async def test_registration_endpoint():
    """Test the registration endpoint to reproduce timeout issues"""
    
    print("🧪 Testing User Registration Endpoint for MongoDB Timeout Issues")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    registration_url = f"{base_url}/api/v1/auth/register"
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Single Registration",
            "concurrent_requests": 1,
            "total_requests": 1
        },
        {
            "name": "Multiple Sequential Registrations", 
            "concurrent_requests": 1,
            "total_requests": 5
        },
        {
            "name": "Concurrent Registrations (Low Load)",
            "concurrent_requests": 3,
            "total_requests": 3
        },
        {
            "name": "Concurrent Registrations (Medium Load)",
            "concurrent_requests": 5,
            "total_requests": 5
        },
        {
            "name": "Concurrent Registrations (High Load)",
            "concurrent_requests": 10,
            "total_requests": 10
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print(f"   Concurrent: {scenario['concurrent_requests']}, Total: {scenario['total_requests']}")
        
        scenario_results = {
            "scenario": scenario["name"],
            "concurrent_requests": scenario["concurrent_requests"],
            "total_requests": scenario["total_requests"],
            "successful": 0,
            "failed": 0,
            "timeout_errors": 0,
            "connection_errors": 0,
            "other_errors": 0,
            "total_duration": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        # Create batches of concurrent requests
        batch_size = scenario["concurrent_requests"]
        total_requests = scenario["total_requests"]
        
        for batch_start in range(0, total_requests, batch_size):
            batch_end = min(batch_start + batch_size, total_requests)
            batch_requests = batch_end - batch_start
            
            print(f"   📦 Processing batch {batch_start//batch_size + 1}: {batch_requests} requests")
            
            # Create tasks for this batch
            tasks = []
            for i in range(batch_requests):
                request_id = batch_start + i + 1
                tasks.append(make_registration_request(registration_url, request_id))
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    scenario_results["failed"] += 1
                    error_type = type(result).__name__
                    error_msg = str(result)
                    scenario_results["errors"].append(f"{error_type}: {error_msg}")
                    
                    if "timeout" in error_msg.lower():
                        scenario_results["timeout_errors"] += 1
                    elif "connection" in error_msg.lower():
                        scenario_results["connection_errors"] += 1
                    else:
                        scenario_results["other_errors"] += 1
                        
                    print(f"     ❌ Request failed: {error_type}")
                elif result.get("success"):
                    scenario_results["successful"] += 1
                    print(f"     ✅ Request succeeded in {result.get('duration', 0):.2f}s")
                else:
                    scenario_results["failed"] += 1
                    error_msg = result.get("error", "Unknown error")
                    scenario_results["errors"].append(error_msg)
                    
                    if "timeout" in error_msg.lower():
                        scenario_results["timeout_errors"] += 1
                    elif "connection" in error_msg.lower():
                        scenario_results["connection_errors"] += 1
                    else:
                        scenario_results["other_errors"] += 1
                        
                    print(f"     ❌ Request failed: {error_msg}")
            
            # Small delay between batches to avoid overwhelming
            if batch_end < total_requests:
                await asyncio.sleep(0.5)
        
        scenario_results["total_duration"] = time.time() - start_time
        
        # Print scenario summary
        print(f"   📊 Results: {scenario_results['successful']}/{scenario_results['total_requests']} successful")
        print(f"   ⏱️  Total Duration: {scenario_results['total_duration']:.2f}s")
        if scenario_results["timeout_errors"] > 0:
            print(f"   ⏰ Timeout Errors: {scenario_results['timeout_errors']}")
        if scenario_results["connection_errors"] > 0:
            print(f"   🔌 Connection Errors: {scenario_results['connection_errors']}")
        
        results.append(scenario_results)
    
    # Overall analysis
    print(f"\n📈 Overall Analysis")
    print("=" * 50)
    
    total_timeout_errors = sum(r["timeout_errors"] for r in results)
    total_connection_errors = sum(r["connection_errors"] for r in results)
    total_requests = sum(r["total_requests"] for r in results)
    total_successful = sum(r["successful"] for r in results)
    
    print(f"Total Requests: {total_requests}")
    print(f"Total Successful: {total_successful}")
    print(f"Total Timeout Errors: {total_timeout_errors}")
    print(f"Total Connection Errors: {total_connection_errors}")
    
    if total_timeout_errors > 0:
        print(f"\n🚨 TIMEOUT ISSUES DETECTED!")
        print("   This confirms MongoDB connection timeout problems under load.")
        
        # Find scenarios with timeouts
        timeout_scenarios = [r for r in results if r["timeout_errors"] > 0]
        if timeout_scenarios:
            print("   Scenarios with timeouts:")
            for scenario in timeout_scenarios:
                print(f"   - {scenario['scenario']}: {scenario['timeout_errors']} timeouts")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"registration_timeout_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": {
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_timeout_errors": total_timeout_errors,
                "total_connection_errors": total_connection_errors
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {filename}")
    
    return results

async def make_registration_request(url, request_id):
    """Make a single registration request"""
    
    # Generate unique user data
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user_data = {
        "email": f"testuser{request_id}_{random_suffix}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Test User {request_id}"
    }
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 201:
                    # Successful registration
                    return {
                        "success": True,
                        "status_code": response.status,
                        "duration": duration,
                        "request_id": request_id
                    }
                elif response.status == 409:
                    # Email already exists - this is expected in some cases
                    return {
                        "success": True,  # Consider this success for testing purposes
                        "status_code": response.status,
                        "duration": duration,
                        "request_id": request_id,
                        "note": "Email already exists"
                    }
                else:
                    # Other error
                    response_text = await response.text()
                    return {
                        "success": False,
                        "status_code": response.status,
                        "duration": duration,
                        "request_id": request_id,
                        "error": f"HTTP {response.status}: {response_text}"
                    }
                    
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        return {
            "success": False,
            "duration": duration,
            "request_id": request_id,
            "error": f"Request timeout after {duration:.2f}s"
        }
    except aiohttp.ClientError as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "duration": duration,
            "request_id": request_id,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "duration": duration,
            "request_id": request_id,
            "error": f"Unexpected error: {str(e)}"
        }

async def main():
    """Main test function"""
    print("🔍 MongoDB Connection Timeout Test - User Registration")
    print("This test will attempt to reproduce the timeout issues during user registration")
    print()
    
    # First, test if the server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/healthz") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Server is running: {health_data.get('message', 'Unknown status')}")
                    print(f"📊 Database Connected: {health_data.get('database_connected', False)}")
                else:
                    print(f"⚠️  Server responded with status {response.status}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the backend server is running on http://localhost:8000")
        return
    
    print()
    
    # Run the registration tests
    await test_registration_endpoint()

if __name__ == "__main__":
    asyncio.run(main())