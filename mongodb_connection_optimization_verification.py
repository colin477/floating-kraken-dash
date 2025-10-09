#!/usr/bin/env python3
"""
MongoDB Connection Optimization Verification Script

This script verifies that the MongoDB connection optimizations have resolved
the registration timeout errors by testing:
1. Single user registration functionality
2. Concurrent user registrations (reproducing original timeout scenario)
3. Connection pool monitoring and validation
4. Performance metrics comparison
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBOptimizationVerifier:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "single_user_test": {},
            "concurrent_test": {},
            "performance_metrics": {},
            "connection_pool_validation": {},
            "errors": [],
            "recommendations": []
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def generate_test_user(self, suffix: str = None) -> Dict[str, str]:
        """Generate a test user with random data"""
        if suffix is None:
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        return {
            "email": f"test_user_{suffix}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Test {suffix.title()} User"
        }
    
    async def test_backend_health(self) -> bool:
        """Test if backend is healthy and responsive"""
        try:
            logger.info("Testing backend health...")
            async with self.session.get(f"{self.base_url}/healthz") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Backend health check passed: {data}")
                    return True
                else:
                    logger.error(f"Backend health check failed with status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return False
    
    async def register_user(self, user_data: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
        """Register a single user and measure response time"""
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.api_base}/auth/register",
                json=user_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                result = {
                    "success": response.status in [200, 201],
                    "status_code": response.status,
                    "response_time": response_time,
                    "user_email": user_data["email"],
                    "error": None
                }
                
                if response.status in [200, 201]:
                    try:
                        response_data = await response.json()
                        result["response_data"] = response_data
                        logger.info(f"User {user_data['email']} registered successfully in {response_time:.2f}s")
                    except Exception as e:
                        result["error"] = f"Failed to parse response JSON: {e}"
                else:
                    try:
                        error_data = await response.json()
                        result["error"] = error_data
                        logger.error(f"Registration failed for {user_data['email']}: {error_data}")
                    except:
                        result["error"] = f"HTTP {response.status}"
                        logger.error(f"Registration failed for {user_data['email']}: HTTP {response.status}")
                
                return result
                
        except asyncio.TimeoutError:
            end_time = time.time()
            response_time = end_time - start_time
            result = {
                "success": False,
                "status_code": 408,
                "response_time": response_time,
                "user_email": user_data["email"],
                "error": "Request timeout"
            }
            logger.error(f"Registration timeout for {user_data['email']} after {response_time:.2f}s")
            return result
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            result = {
                "success": False,
                "status_code": 0,
                "response_time": response_time,
                "user_email": user_data["email"],
                "error": str(e)
            }
            logger.error(f"Registration error for {user_data['email']}: {e}")
            return result
    
    async def test_single_user_registration(self) -> Dict[str, Any]:
        """Test single user registration functionality"""
        logger.info("=== Testing Single User Registration ===")
        
        user_data = self.generate_test_user("single")
        result = await self.register_user(user_data)
        
        test_result = {
            "passed": result["success"],
            "response_time": result["response_time"],
            "status_code": result["status_code"],
            "error": result.get("error"),
            "user_email": result["user_email"]
        }
        
        if test_result["passed"]:
            logger.info(f"✅ Single user registration test PASSED in {result['response_time']:.2f}s")
        else:
            logger.error(f"❌ Single user registration test FAILED: {result.get('error')}")
        
        return test_result
    
    async def test_concurrent_registrations(self, num_users: int = 20, batch_size: int = 5) -> Dict[str, Any]:
        """Test concurrent user registrations to reproduce original timeout scenario"""
        logger.info(f"=== Testing Concurrent Registrations ({num_users} users, batch size {batch_size}) ===")
        
        # Generate test users
        users = [self.generate_test_user(f"concurrent_{i}") for i in range(num_users)]
        
        # Track results
        all_results = []
        successful_registrations = 0
        failed_registrations = 0
        timeout_errors = 0
        response_times = []
        
        # Process users in batches to simulate realistic concurrent load
        for batch_start in range(0, num_users, batch_size):
            batch_end = min(batch_start + batch_size, num_users)
            batch_users = users[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: users {batch_start+1}-{batch_end}")
            
            # Create concurrent tasks for this batch
            tasks = [self.register_user(user) for user in batch_users]
            
            # Execute batch concurrently
            batch_start_time = time.time()
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time
            
            logger.info(f"Batch completed in {batch_duration:.2f}s")
            
            # Process batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_registrations += 1
                    all_results.append({
                        "success": False,
                        "error": str(result),
                        "response_time": 0
                    })
                else:
                    all_results.append(result)
                    if result["success"]:
                        successful_registrations += 1
                        response_times.append(result["response_time"])
                    else:
                        failed_registrations += 1
                        if "timeout" in str(result.get("error", "")).lower():
                            timeout_errors += 1
            
            # Small delay between batches to avoid overwhelming the server
            if batch_end < num_users:
                await asyncio.sleep(0.5)
        
        # Calculate statistics
        total_requests = len(all_results)
        success_rate = (successful_registrations / total_requests) * 100 if total_requests > 0 else 0
        
        stats = {}
        if response_times:
            stats = {
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            }
        
        test_result = {
            "total_requests": total_requests,
            "successful_registrations": successful_registrations,
            "failed_registrations": failed_registrations,
            "timeout_errors": timeout_errors,
            "success_rate": success_rate,
            "response_time_stats": stats,
            "all_results": all_results,
            "passed": timeout_errors == 0 and success_rate >= 90  # Pass if no timeouts and >90% success
        }
        
        if test_result["passed"]:
            logger.info(f"✅ Concurrent registration test PASSED")
            logger.info(f"   Success rate: {success_rate:.1f}% ({successful_registrations}/{total_requests})")
            logger.info(f"   Timeout errors: {timeout_errors}")
            if stats:
                logger.info(f"   Avg response time: {stats['avg_response_time']:.2f}s")
                logger.info(f"   P95 response time: {stats['p95_response_time']:.2f}s")
        else:
            logger.error(f"❌ Concurrent registration test FAILED")
            logger.error(f"   Success rate: {success_rate:.1f}% ({successful_registrations}/{total_requests})")
            logger.error(f"   Timeout errors: {timeout_errors}")
            logger.error(f"   Failed registrations: {failed_registrations}")
        
        return test_result
    
    async def validate_connection_pool_settings(self) -> Dict[str, Any]:
        """Validate that the optimized connection pool settings are being applied"""
        logger.info("=== Validating Connection Pool Settings ===")
        
        # Test multiple rapid requests to check pool behavior
        rapid_requests = 10
        tasks = []
        
        for i in range(rapid_requests):
            user_data = self.generate_test_user(f"pool_test_{i}")
            tasks.append(self.register_user(user_data, timeout=10))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_requests = sum(1 for r in results if not isinstance(r, Exception) and r.get("success", False))
        failed_requests = rapid_requests - successful_requests
        
        # Check for connection pool exhaustion indicators
        pool_exhaustion_errors = 0
        for result in results:
            if isinstance(result, Exception):
                continue
            error = result.get("error", "")
            if any(indicator in str(error).lower() for indicator in [
                "connection pool", "wait queue", "timeout", "connection refused"
            ]):
                pool_exhaustion_errors += 1
        
        validation_result = {
            "rapid_requests_sent": rapid_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "avg_time_per_request": total_time / rapid_requests,
            "pool_exhaustion_errors": pool_exhaustion_errors,
            "passed": pool_exhaustion_errors == 0 and successful_requests >= (rapid_requests * 0.8)
        }
        
        if validation_result["passed"]:
            logger.info(f"✅ Connection pool validation PASSED")
            logger.info(f"   {successful_requests}/{rapid_requests} requests successful")
            logger.info(f"   No pool exhaustion errors detected")
        else:
            logger.error(f"❌ Connection pool validation FAILED")
            logger.error(f"   {successful_requests}/{rapid_requests} requests successful")
            logger.error(f"   Pool exhaustion errors: {pool_exhaustion_errors}")
        
        return validation_result
    
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification tests"""
        logger.info("🚀 Starting MongoDB Connection Optimization Verification")
        logger.info("=" * 60)
        
        # Check backend health first
        if not await self.test_backend_health():
            self.results["errors"].append("Backend health check failed")
            return self.results
        
        try:
            # Test 1: Single user registration
            self.results["single_user_test"] = await self.test_single_user_registration()
            
            # Test 2: Concurrent registrations (main test for timeout issues)
            self.results["concurrent_test"] = await self.test_concurrent_registrations(
                num_users=25,  # Increased to better test concurrent load
                batch_size=8   # Larger batches to simulate real concurrent usage
            )
            
            # Test 3: Connection pool validation
            self.results["connection_pool_validation"] = await self.validate_connection_pool_settings()
            
            # Generate performance metrics summary
            self.results["performance_metrics"] = self._generate_performance_summary()
            
            # Generate recommendations
            self.results["recommendations"] = self._generate_recommendations()
            
        except Exception as e:
            logger.error(f"Verification failed with error: {e}")
            self.results["errors"].append(f"Verification error: {e}")
        
        return self.results
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance metrics summary"""
        summary = {
            "single_user_performance": {},
            "concurrent_performance": {},
            "overall_assessment": "unknown"
        }
        
        # Single user performance
        single_test = self.results.get("single_user_test", {})
        if single_test.get("passed"):
            summary["single_user_performance"] = {
                "response_time": single_test.get("response_time", 0),
                "status": "good" if single_test.get("response_time", 0) < 2.0 else "slow"
            }
        
        # Concurrent performance
        concurrent_test = self.results.get("concurrent_test", {})
        if concurrent_test.get("response_time_stats"):
            stats = concurrent_test["response_time_stats"]
            summary["concurrent_performance"] = {
                "avg_response_time": stats.get("avg_response_time", 0),
                "p95_response_time": stats.get("p95_response_time", 0),
                "success_rate": concurrent_test.get("success_rate", 0),
                "timeout_errors": concurrent_test.get("timeout_errors", 0)
            }
        
        # Overall assessment
        single_passed = single_test.get("passed", False)
        concurrent_passed = concurrent_test.get("passed", False)
        pool_passed = self.results.get("connection_pool_validation", {}).get("passed", False)
        
        if single_passed and concurrent_passed and pool_passed:
            summary["overall_assessment"] = "excellent"
        elif single_passed and concurrent_passed:
            summary["overall_assessment"] = "good"
        elif single_passed:
            summary["overall_assessment"] = "fair"
        else:
            summary["overall_assessment"] = "poor"
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        single_test = self.results.get("single_user_test", {})
        concurrent_test = self.results.get("concurrent_test", {})
        pool_test = self.results.get("connection_pool_validation", {})
        
        # Check single user performance
        if not single_test.get("passed"):
            recommendations.append("❌ Single user registration is failing - check basic MongoDB connectivity")
        elif single_test.get("response_time", 0) > 3.0:
            recommendations.append("⚠️ Single user registration is slow - consider optimizing database queries")
        
        # Check concurrent performance
        if not concurrent_test.get("passed"):
            timeout_errors = concurrent_test.get("timeout_errors", 0)
            success_rate = concurrent_test.get("success_rate", 0)
            
            if timeout_errors > 0:
                recommendations.append(f"❌ {timeout_errors} timeout errors detected - MongoDB connection optimizations may need further tuning")
            
            if success_rate < 90:
                recommendations.append(f"❌ Low success rate ({success_rate:.1f}%) - investigate connection pool settings and server capacity")
        else:
            recommendations.append("✅ Concurrent registration timeout issues appear to be resolved")
        
        # Check connection pool
        if not pool_test.get("passed"):
            recommendations.append("❌ Connection pool validation failed - verify pool size and timeout settings")
        else:
            recommendations.append("✅ Connection pool is handling concurrent requests effectively")
        
        # Performance recommendations
        stats = concurrent_test.get("response_time_stats", {})
        if stats:
            avg_time = stats.get("avg_response_time", 0)
            p95_time = stats.get("p95_response_time", 0)
            
            if avg_time > 5.0:
                recommendations.append("⚠️ Average response time is high - consider further database optimizations")
            elif avg_time < 2.0:
                recommendations.append("✅ Excellent average response time performance")
            
            if p95_time > 10.0:
                recommendations.append("⚠️ P95 response time is high - some requests are still slow")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - MongoDB connection optimizations are working effectively")
        
        return recommendations

def save_results(results: Dict[str, Any], filename: str = None):
    """Save test results to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mongodb_optimization_verification_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {filename}")
    return filename

async def main():
    """Main verification function"""
    async with MongoDBOptimizationVerifier() as verifier:
        results = await verifier.run_comprehensive_verification()
        
        # Save results
        filename = save_results(results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 MONGODB CONNECTION OPTIMIZATION VERIFICATION SUMMARY")
        print("=" * 60)
        
        print(f"🕐 Test completed at: {results['timestamp']}")
        print()
        
        # Single user test
        single_test = results.get("single_user_test", {})
        status = "✅ PASSED" if single_test.get("passed") else "❌ FAILED"
        print(f"🔸 Single User Registration: {status}")
        if single_test.get("response_time"):
            print(f"   Response time: {single_test['response_time']:.2f}s")
        
        # Concurrent test
        concurrent_test = results.get("concurrent_test", {})
        status = "✅ PASSED" if concurrent_test.get("passed") else "❌ FAILED"
        print(f"🔸 Concurrent Registrations: {status}")
        if concurrent_test.get("success_rate") is not None:
            print(f"   Success rate: {concurrent_test['success_rate']:.1f}%")
            print(f"   Timeout errors: {concurrent_test.get('timeout_errors', 0)}")
        
        # Connection pool test
        pool_test = results.get("connection_pool_validation", {})
        status = "✅ PASSED" if pool_test.get("passed") else "❌ FAILED"
        print(f"🔸 Connection Pool Validation: {status}")
        
        # Overall assessment
        assessment = results.get("performance_metrics", {}).get("overall_assessment", "unknown")
        print(f"\n🎯 Overall Assessment: {assessment.upper()}")
        
        # Recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Errors
        errors = results.get("errors", [])
        if errors:
            print(f"\n❌ Errors:")
            for error in errors:
                print(f"   {error}")
        
        print(f"\n📄 Detailed results saved to: {filename}")
        print("=" * 60)
        
        return results

if __name__ == "__main__":
    asyncio.run(main())