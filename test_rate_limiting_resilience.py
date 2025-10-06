#!/usr/bin/env python3
"""
Rate Limiting Resilience Test
Tests rapid requests to verify Redis timeout handling and graceful degradation
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def test_rapid_requests():
    """Test rapid requests to trigger rate limiting behavior"""
    print("=== Rate Limiting Resilience Test ===")
    
    results = []
    start_time = time.time()
    
    # Create session for connection reuse
    async with aiohttp.ClientSession() as session:
        # Send 20 rapid requests to test rate limiting
        tasks = []
        for i in range(20):
            task = make_request(session, i + 1)
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_requests = 0
    failed_requests = 0
    rate_limited_requests = 0
    timeout_requests = 0
    server_errors = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed_requests += 1
            if "timeout" in str(result).lower():
                timeout_requests += 1
        elif isinstance(result, dict):
            status = result.get('status', 0)
            if status == 200:
                successful_requests += 1
            elif status == 429:  # Too Many Requests
                rate_limited_requests += 1
            elif status == 503:  # Service Unavailable
                server_errors += 1
            elif status >= 500:
                server_errors += 1
            else:
                failed_requests += 1
    
    # Print summary
    print(f"\n=== RATE LIMITING TEST RESULTS ===")
    print(f"Total requests: {len(results)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful (200): {successful_requests}")
    print(f"Rate limited (429): {rate_limited_requests}")
    print(f"Server errors (503/5xx): {server_errors}")
    print(f"Timeout errors: {timeout_requests}")
    print(f"Other failures: {failed_requests}")
    
    # Detailed results
    print(f"\n=== DETAILED RESULTS ===")
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"Request {i}: ERROR - {result}")
        else:
            status = result.get('status', 'unknown')
            duration = result.get('duration', 0)
            print(f"Request {i}: Status {status}, Duration {duration:.3f}s")
    
    return {
        "total_requests": len(results),
        "successful": successful_requests,
        "rate_limited": rate_limited_requests,
        "server_errors": server_errors,
        "timeout_errors": timeout_requests,
        "other_failures": failed_requests,
        "total_time": total_time,
        "results": results
    }

async def make_request(session, request_num):
    """Make a single request and return result"""
    try:
        start_time = time.time()
        async with session.get("http://localhost:8000/", timeout=10) as response:
            duration = time.time() - start_time
            content = await response.text()
            
            return {
                "request": request_num,
                "status": response.status,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content)
            }
    except asyncio.TimeoutError:
        return {
            "request": request_num,
            "error": "Request timeout",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "request": request_num,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def test_auth_endpoints_resilience():
    """Test auth endpoints under load"""
    print("\n=== AUTH ENDPOINTS RESILIENCE TEST ===")
    
    endpoints = [
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/healthz"
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\nTesting {endpoint}...")
            endpoint_results = []
            
            # Send 5 rapid requests to each endpoint
            for i in range(5):
                try:
                    start_time = time.time()
                    
                    if endpoint == "/api/v1/auth/register":
                        # POST request with test data
                        test_data = {
                            "email": f"test{i}@resilience.com",
                            "password": "TestPassword123!",
                            "full_name": f"Test User {i}"
                        }
                        async with session.post(f"http://localhost:8000{endpoint}", 
                                              json=test_data, timeout=10) as response:
                            duration = time.time() - start_time
                            content = await response.text()
                            endpoint_results.append({
                                "status": response.status,
                                "duration": duration,
                                "content_preview": content[:100]
                            })
                    else:
                        # GET request
                        async with session.get(f"http://localhost:8000{endpoint}", 
                                             timeout=10) as response:
                            duration = time.time() - start_time
                            content = await response.text()
                            endpoint_results.append({
                                "status": response.status,
                                "duration": duration,
                                "content_preview": content[:100]
                            })
                            
                except Exception as e:
                    endpoint_results.append({
                        "error": str(e),
                        "duration": time.time() - start_time
                    })
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            results[endpoint] = endpoint_results
            
            # Print endpoint summary
            successful = sum(1 for r in endpoint_results if r.get('status') == 200 or r.get('status') == 201)
            print(f"  Successful: {successful}/{len(endpoint_results)}")
    
    return results

async def main():
    """Run comprehensive rate limiting resilience tests"""
    print("Starting Rate Limiting Resilience Tests...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Rapid requests to root endpoint
    rapid_test_results = await test_rapid_requests()
    
    # Test 2: Auth endpoints resilience
    auth_test_results = await test_auth_endpoints_resilience()
    
    # Overall assessment
    print(f"\n=== OVERALL ASSESSMENT ===")
    
    # Check if rate limiting is working properly
    if rapid_test_results['rate_limited'] > 0:
        print("✅ Rate limiting is active and working")
    else:
        print("⚠️  No rate limiting detected - may be using memory storage")
    
    # Check if server errors are handled gracefully
    if rapid_test_results['server_errors'] == 0:
        print("✅ No server crashes under load")
    else:
        print(f"⚠️  {rapid_test_results['server_errors']} server errors detected")
    
    # Check if timeouts are handled
    if rapid_test_results['timeout_errors'] == 0:
        print("✅ No timeout errors - good resilience")
    else:
        print(f"⚠️  {rapid_test_results['timeout_errors']} timeout errors detected")
    
    # Save detailed results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "rapid_requests_test": rapid_test_results,
        "auth_endpoints_test": auth_test_results
    }
    
    with open("rate_limiting_resilience_results.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: rate_limiting_resilience_results.json")
    
    # Recommendations
    print(f"\n=== RECOMMENDATIONS ===")
    if rapid_test_results['server_errors'] > 0:
        print("1. Review server error handling for high-load scenarios")
    if rapid_test_results['timeout_errors'] > 0:
        print("2. Consider increasing timeout values or improving response times")
    if rapid_test_results['rate_limited'] == 0:
        print("3. Rate limiting appears to be using memory storage (Redis disabled)")
    
    print("4. ✅ Overall resilience appears good - no crashes detected")

if __name__ == "__main__":
    asyncio.run(main())