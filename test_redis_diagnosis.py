#!/usr/bin/env python3
"""
Redis Connection Diagnosis Script
Tests Redis connectivity and rate limiting behavior
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def test_redis_connectivity():
    """Test direct Redis connectivity"""
    print("=== Redis Connectivity Test ===")
    try:
        import redis.asyncio as redis
        import os
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        print(f"Testing Redis connection to: {redis_url}")
        
        client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
        await client.ping()
        print("✅ Redis connection successful")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_backend_health():
    """Test backend health endpoint"""
    print("\n=== Backend Health Test ===")
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.get("http://localhost:8000/healthz", timeout=30) as response:
                duration = time.time() - start_time
                status = response.status
                content = await response.text()
                
                print(f"Health check status: {status}")
                print(f"Response time: {duration:.2f}s")
                print(f"Response content: {content}")
                
                return status == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_rate_limiting_behavior():
    """Test rate limiting behavior with rapid requests"""
    print("\n=== Rate Limiting Behavior Test ===")
    
    results = []
    async with aiohttp.ClientSession() as session:
        # Send 10 rapid requests to test rate limiting
        for i in range(10):
            try:
                start_time = time.time()
                async with session.get("http://localhost:8000/", timeout=10) as response:
                    duration = time.time() - start_time
                    status = response.status
                    content = await response.text()
                    
                    result = {
                        "request": i + 1,
                        "status": status,
                        "duration": duration,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if status != 200:
                        result["error_content"] = content
                    
                    results.append(result)
                    print(f"Request {i+1}: Status {status}, Duration {duration:.2f}s")
                    
            except Exception as e:
                result = {
                    "request": i + 1,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                print(f"Request {i+1}: Error - {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def test_auth_endpoints():
    """Test authentication endpoints that would be used in signup flow"""
    print("\n=== Auth Endpoints Test ===")
    
    endpoints = [
        "/api/v1/auth/register",
        "/api/v1/auth/login"
    ]
    
    results = {}
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                # Test with OPTIONS request first (CORS preflight)
                async with session.options(f"http://localhost:8000{endpoint}", timeout=10) as response:
                    results[f"{endpoint}_options"] = {
                        "status": response.status,
                        "headers": dict(response.headers)
                    }
                
                # Test with GET request to see if endpoint exists
                async with session.get(f"http://localhost:8000{endpoint}", timeout=10) as response:
                    content = await response.text()
                    results[f"{endpoint}_get"] = {
                        "status": response.status,
                        "content": content[:200] if content else None
                    }
                    
            except Exception as e:
                results[f"{endpoint}_error"] = str(e)
    
    for endpoint, result in results.items():
        print(f"{endpoint}: {result}")
    
    return results

async def main():
    """Run comprehensive Redis and backend diagnosis"""
    print("Starting Redis and Backend Diagnosis...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test Redis connectivity
    redis_ok = await test_redis_connectivity()
    
    # Test backend health
    health_ok = await test_backend_health()
    
    # Test rate limiting behavior
    rate_limit_results = await test_rate_limiting_behavior()
    
    # Test auth endpoints
    auth_results = await test_auth_endpoints()
    
    # Summary
    print("\n=== DIAGNOSIS SUMMARY ===")
    print(f"Redis Connection: {'✅ OK' if redis_ok else '❌ FAILED'}")
    print(f"Backend Health: {'✅ OK' if health_ok else '❌ FAILED'}")
    
    # Analyze rate limiting results
    successful_requests = sum(1 for r in rate_limit_results if r.get('status') == 200)
    failed_requests = len(rate_limit_results) - successful_requests
    print(f"Rate Limiting: {successful_requests}/{len(rate_limit_results)} requests successful")
    
    if failed_requests > 0:
        print("Failed request details:")
        for r in rate_limit_results:
            if r.get('status') != 200:
                print(f"  - Request {r.get('request', '?')}: {r}")
    
    # Save detailed results
    diagnosis_results = {
        "timestamp": datetime.now().isoformat(),
        "redis_connectivity": redis_ok,
        "backend_health": health_ok,
        "rate_limiting_results": rate_limit_results,
        "auth_endpoints_results": auth_results
    }
    
    with open("redis_diagnosis_results.json", "w") as f:
        json.dump(diagnosis_results, f, indent=2)
    
    print(f"\nDetailed results saved to: redis_diagnosis_results.json")
    
    # Recommendations
    print("\n=== RECOMMENDATIONS ===")
    if not redis_ok:
        print("1. Redis connection is failing - consider:")
        print("   - Check if Redis server is running")
        print("   - Verify REDIS_URL environment variable")
        print("   - Test Redis connection manually")
        print("   - Consider using memory-based rate limiting as fallback")
    
    if not health_ok:
        print("2. Backend health check is failing - consider:")
        print("   - Check backend logs for specific errors")
        print("   - Verify database connectivity")
        print("   - Review middleware configuration")
    
    if failed_requests > 0:
        print("3. Rate limiting issues detected - consider:")
        print("   - Review SlowAPI middleware configuration")
        print("   - Check TimeoutError exception handling")
        print("   - Verify Redis fallback mechanisms")

if __name__ == "__main__":
    asyncio.run(main())