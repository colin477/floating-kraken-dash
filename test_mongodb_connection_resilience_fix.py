#!/usr/bin/env python3
"""
Test MongoDB Connection Resilience Fix
Validates that the DNS resolution issues have been resolved
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
import structlog

# Load environment variables
load_dotenv('backend/.env')

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class ConnectionResilienceTest:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "performance_metrics": {},
            "error_analysis": {},
            "recommendations": []
        }

    def log_test_result(self, test_name: str, success: bool, details: str, duration: float = 0, error: str = None):
        """Log test result"""
        result = {
            "success": success,
            "details": details,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            result["error"] = error
            
        self.results["test_results"][test_name] = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details} ({duration:.3f}s)")
        if error:
            print(f"   Error: {error}")

    async def test_resilient_database_import(self):
        """Test that resilient database module can be imported"""
        try:
            from app.database_resilience_fix import (
                resilient_db,
                connect_to_mongo_resilient,
                check_connection_health_resilient
            )
            self.log_test_result(
                "resilient_module_import", 
                True, 
                "Resilient database module imported successfully"
            )
            return True
        except Exception as e:
            self.log_test_result(
                "resilient_module_import", 
                False, 
                "Failed to import resilient database module", 
                error=str(e)
            )
            return False

    async def test_resilient_connection(self):
        """Test resilient MongoDB connection"""
        try:
            from app.database_resilience_fix import connect_to_mongo_resilient, resilient_db
            
            start_time = time.time()
            await connect_to_mongo_resilient()
            duration = time.time() - start_time
            
            # Verify connection is established
            if resilient_db.client is not None and resilient_db.database is not None:
                # Test with a simple operation
                collections = await resilient_db.database.list_collection_names()
                
                self.log_test_result(
                    "resilient_connection",
                    True,
                    f"Resilient connection established, found {len(collections)} collections",
                    duration
                )
                return True
            else:
                self.log_test_result(
                    "resilient_connection",
                    False,
                    "Connection established but client/database not available",
                    duration
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "resilient_connection", 
                False, 
                "Resilient connection failed", 
                duration=time.time() - start_time,
                error=str(e)
            )
            return False

    async def test_resilient_health_check(self):
        """Test resilient health check functionality"""
        try:
            from app.database_resilience_fix import check_connection_health_resilient
            
            start_time = time.time()
            is_healthy = await check_connection_health_resilient()
            duration = time.time() - start_time
            
            self.log_test_result(
                "resilient_health_check", 
                is_healthy, 
                f"Health check {'passed' if is_healthy else 'failed'}",
                duration
            )
            return is_healthy
            
        except Exception as e:
            self.log_test_result(
                "resilient_health_check", 
                False, 
                "Health check threw exception", 
                duration=time.time() - start_time,
                error=str(e)
            )
            return False

    async def test_legacy_database_integration(self):
        """Test that legacy database functions work with resilience"""
        try:
            from app.database import connect_to_mongo, check_connection_health, get_collection
            
            # Test connection
            start_time = time.time()
            await connect_to_mongo()
            connect_duration = time.time() - start_time
            
            # Test health check
            start_time = time.time()
            is_healthy = await check_connection_health()
            health_duration = time.time() - start_time
            
            # Test collection access
            start_time = time.time()
            users_collection = await get_collection("users")
            collection_duration = time.time() - start_time
            
            if is_healthy and users_collection:
                total_duration = connect_duration + health_duration + collection_duration
                self.log_test_result(
                    "legacy_integration", 
                    True, 
                    f"Legacy integration successful (connect: {connect_duration:.3f}s, health: {health_duration:.3f}s, collection: {collection_duration:.3f}s)",
                    total_duration
                )
                return True
            else:
                self.log_test_result(
                    "legacy_integration", 
                    False, 
                    f"Legacy integration failed - healthy: {is_healthy}, collection: {users_collection is not None}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "legacy_integration", 
                False, 
                "Legacy integration threw exception", 
                error=str(e)
            )
            return False

    async def test_connection_stability(self):
        """Test connection stability over multiple operations"""
        try:
            from app.database import get_collection, check_connection_health
            
            operations_count = 10
            successful_operations = 0
            total_duration = 0
            
            for i in range(operations_count):
                try:
                    start_time = time.time()
                    
                    # Alternate between health checks and collection access
                    if i % 2 == 0:
                        is_healthy = await check_connection_health()
                        if is_healthy:
                            successful_operations += 1
                    else:
                        collection = await get_collection("users")
                        if collection:
                            successful_operations += 1
                    
                    operation_duration = time.time() - start_time
                    total_duration += operation_duration
                    
                    # Small delay between operations
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Operation {i+1} failed: {e}")
            
            success_rate = successful_operations / operations_count
            avg_duration = total_duration / operations_count
            
            self.log_test_result(
                "connection_stability", 
                success_rate >= 0.9,  # 90% success rate required
                f"Stability test: {successful_operations}/{operations_count} operations successful ({success_rate:.1%}), avg duration: {avg_duration:.3f}s",
                total_duration
            )
            
            # Store performance metrics
            self.results["performance_metrics"]["stability_test"] = {
                "operations_count": operations_count,
                "successful_operations": successful_operations,
                "success_rate": success_rate,
                "average_duration": avg_duration,
                "total_duration": total_duration
            }
            
            return success_rate >= 0.9
            
        except Exception as e:
            self.log_test_result(
                "connection_stability", 
                False, 
                "Stability test threw exception", 
                error=str(e)
            )
            return False

    async def test_error_recovery(self):
        """Test error recovery capabilities"""
        try:
            from app.database_resilience_fix import resilient_db
            
            # Simulate connection issues by temporarily closing the client
            original_client = resilient_db.client
            
            # Force connection to be marked as unhealthy
            resilient_db._connection_healthy = False
            
            # Test recovery
            start_time = time.time()
            recovered = await resilient_db.health_check_with_resilience()
            recovery_duration = time.time() - start_time
            
            self.log_test_result(
                "error_recovery", 
                recovered, 
                f"Error recovery {'successful' if recovered else 'failed'}",
                recovery_duration
            )
            
            return recovered
            
        except Exception as e:
            self.log_test_result(
                "error_recovery", 
                False, 
                "Error recovery test threw exception", 
                error=str(e)
            )
            return False

    async def analyze_connection_performance(self):
        """Analyze connection performance metrics"""
        try:
            from app.database import check_connection_health
            
            # Perform multiple health checks to measure performance
            durations = []
            for i in range(5):
                start_time = time.time()
                await check_connection_health()
                duration = time.time() - start_time
                durations.append(duration)
                await asyncio.sleep(0.5)  # Wait between checks
            
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            self.results["performance_metrics"]["health_check_performance"] = {
                "average_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "measurements": durations
            }
            
            # Performance is good if average is under 2 seconds
            performance_good = avg_duration < 2.0
            
            self.log_test_result(
                "performance_analysis", 
                performance_good, 
                f"Performance analysis: avg {avg_duration:.3f}s, min {min_duration:.3f}s, max {max_duration:.3f}s",
                avg_duration
            )
            
            return performance_good
            
        except Exception as e:
            self.log_test_result(
                "performance_analysis", 
                False, 
                "Performance analysis failed", 
                error=str(e)
            )
            return False

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n💡 Generating Recommendations...")
        
        failed_tests = [name for name, result in self.results["test_results"].items() if not result["success"]]
        
        if not failed_tests:
            self.results["recommendations"].append("All tests passed! MongoDB connection resilience is working correctly.")
            print("✅ All tests passed! Connection resilience is working correctly.")
        else:
            print(f"❌ {len(failed_tests)} test(s) failed:")
            for test in failed_tests:
                print(f"   - {test}")
                
            if "resilient_module_import" in failed_tests:
                self.results["recommendations"].append("Fix resilient database module import issues")
                
            if "resilient_connection" in failed_tests:
                self.results["recommendations"].append("Debug resilient connection establishment")
                
            if "connection_stability" in failed_tests:
                self.results["recommendations"].append("Investigate connection stability issues")
                
            if "error_recovery" in failed_tests:
                self.results["recommendations"].append("Improve error recovery mechanisms")

        # Performance recommendations
        perf_metrics = self.results["performance_metrics"]
        if "health_check_performance" in perf_metrics:
            avg_duration = perf_metrics["health_check_performance"]["average_duration"]
            if avg_duration > 1.0:
                self.results["recommendations"].append(f"Health check performance could be improved (current avg: {avg_duration:.3f}s)")

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mongodb_resilience_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Results saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")

    async def run_all_tests(self):
        """Run all resilience tests"""
        print("🚀 Starting MongoDB Connection Resilience Tests...")
        print("=" * 70)
        
        # Run tests in order
        await self.test_resilient_database_import()
        await self.test_resilient_connection()
        await self.test_resilient_health_check()
        await self.test_legacy_database_integration()
        await self.test_connection_stability()
        await self.test_error_recovery()
        await self.analyze_connection_performance()
        
        # Generate recommendations and save results
        self.generate_recommendations()
        self.save_results()
        
        print("\n" + "=" * 70)
        print("🏁 Resilience Tests Complete!")
        
        # Return overall success
        failed_tests = [name for name, result in self.results["test_results"].items() if not result["success"]]
        return len(failed_tests) == 0

async def main():
    """Main function"""
    test_runner = ConnectionResilienceTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! MongoDB connection resilience fix is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the results and recommendations.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)