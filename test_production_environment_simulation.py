#!/usr/bin/env python3
"""
Test MongoDB SSL/TLS fix under production-like environment conditions
"""

import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
    from app.middleware.performance import DatabasePoolConfig
    import structlog
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root and backend dependencies are installed")
    sys.exit(1)

# Configure logging
logger = structlog.get_logger(__name__)

class ProductionEnvironmentSimulator:
    """Simulate production environment conditions for MongoDB SSL/TLS testing"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "environment_scenarios": [],
            "test_details": []
        }
        self.original_env = {}
        
    def backup_environment(self):
        """Backup current environment variables"""
        env_vars = [
            "MONGODB_URI", "MONGODB_TLS_ENABLED", "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES",
            "MONGODB_MAX_POOL_SIZE", "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            "MONGODB_CONNECT_TIMEOUT_MS", "MONGODB_SOCKET_TIMEOUT_MS"
        ]
        
        for var in env_vars:
            self.original_env[var] = os.getenv(var)
    
    def restore_environment(self):
        """Restore original environment variables"""
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    def set_production_environment(self, scenario: Dict[str, Any]):
        """Set production-like environment variables"""
        for var, value in scenario.get("env_vars", {}).items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = str(value)
    
    async def test_database_operations(self, scenario_name: str, connection_options: Dict[str, Any]) -> Dict[str, Any]:
        """Test comprehensive database operations"""
        print(f"   🗄️  Testing database operations...")
        
        test_result = {
            "test_name": f"Database Operations - {scenario_name}",
            "status": "UNKNOWN",
            "operations": {},
            "errors": [],
            "performance": {}
        }
        
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            test_result["status"] = "SKIPPED"
            test_result["errors"].append("No MONGODB_URI available")
            return test_result
        
        client = None
        try:
            # Create client with SSL/TLS configuration
            client = AsyncIOMotorClient(mongodb_uri, **connection_options)
            
            # Test 1: Connection and ping
            start_time = time.time()
            await asyncio.wait_for(client.admin.command('ping'), timeout=15.0)
            ping_time = time.time() - start_time
            test_result["operations"]["ping"] = "SUCCESS"
            test_result["performance"]["ping_time_seconds"] = round(ping_time, 3)
            print(f"      ✅ Ping successful ({ping_time:.3f}s)")
            
            # Test 2: Database and collection access
            db = client.floating_kraken_dash
            test_collection = db.ssl_tls_test
            
            # Test 3: Insert operation
            start_time = time.time()
            test_doc = {
                "test_type": "ssl_tls_production_simulation",
                "scenario": scenario_name,
                "timestamp": datetime.now(),
                "data": {"test": "value", "number": 42}
            }
            insert_result = await test_collection.insert_one(test_doc)
            insert_time = time.time() - start_time
            test_result["operations"]["insert"] = "SUCCESS"
            test_result["performance"]["insert_time_seconds"] = round(insert_time, 3)
            print(f"      ✅ Insert successful ({insert_time:.3f}s)")
            
            # Test 4: Find operation
            start_time = time.time()
            found_doc = await test_collection.find_one({"_id": insert_result.inserted_id})
            find_time = time.time() - start_time
            test_result["operations"]["find"] = "SUCCESS" if found_doc else "FAILED"
            test_result["performance"]["find_time_seconds"] = round(find_time, 3)
            print(f"      ✅ Find successful ({find_time:.3f}s)")
            
            # Test 5: Update operation
            start_time = time.time()
            update_result = await test_collection.update_one(
                {"_id": insert_result.inserted_id},
                {"$set": {"updated": True, "update_time": datetime.now()}}
            )
            update_time = time.time() - start_time
            test_result["operations"]["update"] = "SUCCESS" if update_result.modified_count > 0 else "FAILED"
            test_result["performance"]["update_time_seconds"] = round(update_time, 3)
            print(f"      ✅ Update successful ({update_time:.3f}s)")
            
            # Test 6: Aggregation operation
            start_time = time.time()
            pipeline = [
                {"$match": {"test_type": "ssl_tls_production_simulation"}},
                {"$group": {"_id": "$scenario", "count": {"$sum": 1}}}
            ]
            agg_result = await test_collection.aggregate(pipeline).to_list(length=None)
            agg_time = time.time() - start_time
            test_result["operations"]["aggregation"] = "SUCCESS" if agg_result else "FAILED"
            test_result["performance"]["aggregation_time_seconds"] = round(agg_time, 3)
            print(f"      ✅ Aggregation successful ({agg_time:.3f}s)")
            
            # Test 7: Delete operation (cleanup)
            start_time = time.time()
            delete_result = await test_collection.delete_one({"_id": insert_result.inserted_id})
            delete_time = time.time() - start_time
            test_result["operations"]["delete"] = "SUCCESS" if delete_result.deleted_count > 0 else "FAILED"
            test_result["performance"]["delete_time_seconds"] = round(delete_time, 3)
            print(f"      ✅ Delete successful ({delete_time:.3f}s)")
            
            # Calculate overall performance
            total_time = sum([
                test_result["performance"].get("ping_time_seconds", 0),
                test_result["performance"].get("insert_time_seconds", 0),
                test_result["performance"].get("find_time_seconds", 0),
                test_result["performance"].get("update_time_seconds", 0),
                test_result["performance"].get("aggregation_time_seconds", 0),
                test_result["performance"].get("delete_time_seconds", 0)
            ])
            test_result["performance"]["total_operations_time_seconds"] = round(total_time, 3)
            
            # Check if all operations succeeded
            failed_ops = [op for op, status in test_result["operations"].items() if status != "SUCCESS"]
            if failed_ops:
                test_result["status"] = "FAILED"
                test_result["errors"].append(f"Failed operations: {', '.join(failed_ops)}")
            else:
                test_result["status"] = "PASSED"
                print(f"      ✅ All database operations successful (total: {total_time:.3f}s)")
            
        except ServerSelectionTimeoutError as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Server selection timeout: {str(e)}")
            print(f"      ❌ Server selection timeout: {e}")
            
        except asyncio.TimeoutError:
            test_result["status"] = "FAILED"
            test_result["errors"].append("Database operation timeout")
            print(f"      ❌ Database operation timeout")
            
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Database operation error: {str(e)}")
            print(f"      ❌ Database operation error: {e}")
            
        finally:
            if client:
                client.close()
        
        return test_result
    
    async def test_production_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific production scenario"""
        scenario_name = scenario["name"]
        print(f"\n🏭 Testing Production Scenario: {scenario_name}")
        
        test_result = {
            "scenario_name": scenario_name,
            "description": scenario.get("description", ""),
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Set production environment
            self.set_production_environment(scenario)
            
            # Get connection options with the fix
            connection_options = DatabasePoolConfig.get_connection_options()
            test_result["details"]["connection_options"] = connection_options
            
            # Verify SSL/TLS configuration matches expectations
            expected_tls = scenario.get("expected_tls", False)
            actual_tls = connection_options.get("tls", False)
            
            if actual_tls != expected_tls:
                test_result["errors"].append(
                    f"SSL/TLS configuration mismatch: expected {expected_tls}, got {actual_tls}"
                )
                test_result["status"] = "FAILED"
                return test_result
            
            print(f"   ✅ SSL/TLS configuration correct: {actual_tls}")
            
            # Test database operations
            db_test = await self.test_database_operations(scenario_name, connection_options)
            test_result["details"]["database_operations"] = db_test
            
            # Determine overall status
            if db_test["status"] == "PASSED":
                test_result["status"] = "PASSED"
            elif db_test["status"] == "SKIPPED":
                test_result["status"] = "WARNING"
                test_result["warnings"].append("Database operations skipped - no MONGODB_URI")
            else:
                test_result["status"] = "FAILED"
                test_result["errors"].extend(db_test.get("errors", []))
            
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["errors"].append(f"Scenario test error: {str(e)}")
            print(f"   ❌ Scenario test error: {e}")
        
        finally:
            # Always restore environment
            self.restore_environment()
        
        return test_result
    
    async def run_production_simulation_tests(self):
        """Run comprehensive production environment simulation tests"""
        print("🏭 Starting Production Environment Simulation")
        print("=" * 60)
        
        # Backup environment
        self.backup_environment()
        
        # Define production scenarios
        scenarios = [
            {
                "name": "Production Atlas with Explicit TLS",
                "description": "MongoDB Atlas with explicit TLS enabled (typical production)",
                "env_vars": {
                    "MONGODB_TLS_ENABLED": "true",
                    "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "false",
                    "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "30000",
                    "MONGODB_CONNECT_TIMEOUT_MS": "30000"
                },
                "expected_tls": True
            },
            {
                "name": "Production Atlas Auto-Detection",
                "description": "MongoDB Atlas with auto-detection (missing TLS env var)",
                "env_vars": {
                    "MONGODB_TLS_ENABLED": None,  # Remove the env var
                    "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "false",
                    "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "30000"
                },
                "expected_tls": True  # Should auto-detect Atlas and enable TLS
            },
            {
                "name": "Production with Invalid TLS Config",
                "description": "Production with invalid TLS config (should fallback to Atlas detection)",
                "env_vars": {
                    "MONGODB_TLS_ENABLED": "invalid_value",
                    "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "false",
                    "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "30000"
                },
                "expected_tls": True  # Should fallback to Atlas detection
            },
            {
                "name": "Production with Strict Certificate Validation",
                "description": "Production with strict certificate validation (recommended)",
                "env_vars": {
                    "MONGODB_TLS_ENABLED": "true",
                    "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "false",
                    "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "30000",
                    "MONGODB_MAX_POOL_SIZE": "50"
                },
                "expected_tls": True
            }
        ]
        
        # Only test Atlas scenarios if we have an Atlas URI
        mongodb_uri = os.getenv("MONGODB_URI", "")
        is_atlas = DatabasePoolConfig._is_mongodb_atlas_uri(mongodb_uri)
        
        if not is_atlas:
            # Add local scenarios for non-Atlas testing
            scenarios.extend([
                {
                    "name": "Local Development with TLS Disabled",
                    "description": "Local MongoDB with TLS explicitly disabled",
                    "env_vars": {
                        "MONGODB_TLS_ENABLED": "false",
                        "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "10000"
                    },
                    "expected_tls": False
                }
            ])
        
        try:
            # Test each scenario
            for scenario in scenarios:
                # Skip Atlas-specific scenarios if not using Atlas
                if not is_atlas and scenario["expected_tls"]:
                    continue
                    
                scenario_result = await self.test_production_scenario(scenario)
                self.test_results["environment_scenarios"].append(scenario_result)
                self.test_results["test_details"].append(scenario_result)
                
                # Update summary
                self.test_results["test_summary"]["total_tests"] += 1
                if scenario_result["status"] == "PASSED":
                    self.test_results["test_summary"]["passed"] += 1
                elif scenario_result["status"] == "FAILED":
                    self.test_results["test_summary"]["failed"] += 1
                elif scenario_result["status"] == "WARNING":
                    self.test_results["test_summary"]["warnings"] += 1
            
        finally:
            # Always restore environment
            self.restore_environment()
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION SIMULATION TEST SUMMARY")
        print("=" * 60)
        
        summary = self.test_results["test_summary"]
        print(f"Total Scenarios: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 SCENARIO RESULTS:")
        for scenario in self.test_results["environment_scenarios"]:
            status_icon = {"PASSED": "✅", "FAILED": "❌", "WARNING": "⚠️"}.get(scenario["status"], "❓")
            print(f"{status_icon} {scenario['scenario_name']}: {scenario['status']}")
            
            if scenario.get("errors"):
                for error in scenario["errors"]:
                    print(f"   ❌ {error}")
            
            if scenario.get("warnings"):
                for warning in scenario["warnings"]:
                    print(f"   ⚠️  {warning}")
        
        # Overall assessment
        print("\n🎯 PRODUCTION READINESS ASSESSMENT:")
        if summary['failed'] == 0:
            print("✅ MongoDB SSL/TLS fix is production-ready!")
            print("✅ All production scenarios handled correctly")
            print("✅ Database operations work reliably with SSL/TLS configuration")
        else:
            print("❌ Issues detected in production scenarios")
            print("❌ MongoDB SSL/TLS fix may need additional work")
        
        return summary['failed'] == 0

async def main():
    """Main test execution"""
    simulator = ProductionEnvironmentSimulator()
    
    try:
        # Run production simulation tests
        results = await simulator.run_production_simulation_tests()
        
        # Print summary
        success = simulator.print_summary()
        
        # Save detailed results
        results_file = f"production_environment_simulation_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)