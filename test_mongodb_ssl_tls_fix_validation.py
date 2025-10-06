#!/usr/bin/env python3
"""
Comprehensive test suite for MongoDB SSL/TLS fix validation
Tests the fix implemented in backend/app/middleware/performance.py
"""

import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import tempfile
import subprocess

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

class MongoDBSSLTLSFixValidator:
    """Comprehensive validator for MongoDB SSL/TLS fix"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "environment_info": {},
            "test_details": []
        }
        self.original_env = {}
        
    def backup_environment(self):
        """Backup current environment variables"""
        env_vars = [
            "MONGODB_URI",
            "MONGODB_TLS_ENABLED",
            "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES",
            "MONGODB_MAX_POOL_SIZE",
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS"
        ]
        
        for var in env_vars:
            self.original_env[var] = os.getenv(var)
            
        self.test_results["environment_info"]["original_env"] = self.original_env.copy()
    
    def restore_environment(self):
        """Restore original environment variables"""
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    def set_test_environment(self, env_vars: Dict[str, Optional[str]]):
        """Set specific environment variables for testing"""
        for var, value in env_vars.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    async def test_connection_with_config(self, test_name: str, env_vars: Dict[str, Optional[str]], 
                                        expected_tls: bool, should_succeed: bool = True) -> Dict[str, Any]:
        """Test MongoDB connection with specific configuration"""
        print(f"\n🧪 Testing: {test_name}")
        
        test_result = {
            "test_name": test_name,
            "env_vars": env_vars,
            "expected_tls": expected_tls,
            "should_succeed": should_succeed,
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Set test environment
            self.set_test_environment(env_vars)
            
            # Get connection options from the fix
            connection_options = DatabasePoolConfig.get_connection_options()
            test_result["details"]["connection_options"] = connection_options
            
            # Verify SSL/TLS configuration matches expectations
            actual_tls = connection_options.get("tls", False)
            if actual_tls != expected_tls:
                test_result["errors"].append(
                    f"SSL/TLS mismatch: expected {expected_tls}, got {actual_tls}"
                )
                test_result["status"] = "FAILED"
                return test_result
            
            # Test actual MongoDB connection if URI is available
            mongodb_uri = os.getenv("MONGODB_URI")
            if mongodb_uri:
                print(f"   📡 Testing connection to: {mongodb_uri[:50]}...")
                
                # Create client with the fix's configuration
                client = AsyncIOMotorClient(mongodb_uri, **connection_options)
                
                # Test connection with timeout
                start_time = time.time()
                try:
                    # Attempt to connect and ping
                    await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
                    connection_time = time.time() - start_time
                    
                    test_result["details"]["connection_successful"] = True
                    test_result["details"]["connection_time_seconds"] = round(connection_time, 3)
                    
                    # Test basic database operations
                    db = client.test_db
                    collection = db.test_collection
                    
                    # Insert test document
                    test_doc = {"test": "ssl_tls_fix_validation", "timestamp": datetime.now()}
                    insert_result = await collection.insert_one(test_doc)
                    
                    # Read back the document
                    found_doc = await collection.find_one({"_id": insert_result.inserted_id})
                    
                    # Clean up test document
                    await collection.delete_one({"_id": insert_result.inserted_id})
                    
                    if found_doc:
                        test_result["details"]["database_operations"] = "SUCCESS"
                        print(f"   ✅ Database operations successful")
                    else:
                        test_result["warnings"].append("Could not verify database operations")
                    
                    print(f"   ✅ Connection successful in {connection_time:.3f}s")
                    
                except asyncio.TimeoutError:
                    test_result["errors"].append("Connection timeout after 10 seconds")
                    test_result["details"]["connection_successful"] = False
                    print(f"   ❌ Connection timeout")
                    
                except ServerSelectionTimeoutError as e:
                    test_result["errors"].append(f"Server selection timeout: {str(e)}")
                    test_result["details"]["connection_successful"] = False
                    print(f"   ❌ Server selection timeout: {e}")
                    
                except Exception as e:
                    test_result["errors"].append(f"Connection error: {str(e)}")
                    test_result["details"]["connection_successful"] = False
                    print(f"   ❌ Connection error: {e}")
                
                finally:
                    client.close()
            else:
                test_result["warnings"].append("No MONGODB_URI available for connection testing")
                print(f"   ⚠️  No MONGODB_URI - testing configuration only")
            
            # Determine test status
            if test_result["errors"]:
                test_result["status"] = "FAILED"
            elif test_result["warnings"]:
                test_result["status"] = "WARNING"
            else:
                test_result["status"] = "PASSED"
                
            print(f"   📊 Result: {test_result['status']}")
            
        except Exception as e:
            test_result["errors"].append(f"Test execution error: {str(e)}")
            test_result["status"] = "FAILED"
            print(f"   💥 Test execution error: {e}")
        
        finally:
            # Always restore environment
            self.restore_environment()
        
        return test_result
    
    async def test_atlas_auto_detection(self) -> Dict[str, Any]:
        """Test MongoDB Atlas auto-detection functionality"""
        print(f"\n🔍 Testing Atlas Auto-Detection")
        
        test_cases = [
            {
                "name": "Atlas URI Detection - cluster0.mongodb.net",
                "uri": "mongodb+srv://user:pass@cluster0.mongodb.net/dbname",
                "expected_atlas": True
            },
            {
                "name": "Atlas URI Detection - custom.mongodb.net", 
                "uri": "mongodb+srv://user:pass@custom-cluster.mongodb.net/dbname",
                "expected_atlas": True
            },
            {
                "name": "Local URI Detection - localhost",
                "uri": "mongodb://localhost:27017/dbname",
                "expected_atlas": False
            },
            {
                "name": "Local URI Detection - 127.0.0.1",
                "uri": "mongodb://127.0.0.1:27017/dbname",
                "expected_atlas": False
            },
            {
                "name": "Empty URI",
                "uri": "",
                "expected_atlas": False
            }
        ]
        
        results = []
        for case in test_cases:
            print(f"   🧪 {case['name']}")
            
            # Test the detection function directly
            is_atlas = DatabasePoolConfig._is_mongodb_atlas_uri(case['uri'])
            
            result = {
                "test_name": case['name'],
                "uri": case['uri'],
                "expected_atlas": case['expected_atlas'],
                "detected_atlas": is_atlas,
                "status": "PASSED" if is_atlas == case['expected_atlas'] else "FAILED"
            }
            
            print(f"      Expected: {case['expected_atlas']}, Got: {is_atlas} - {result['status']}")
            results.append(result)
        
        return {
            "test_name": "Atlas Auto-Detection",
            "status": "PASSED" if all(r['status'] == 'PASSED' for r in results) else "FAILED",
            "details": results
        }
    
    async def test_signup_workflow_simulation(self) -> Dict[str, Any]:
        """Simulate the sign-up workflow that was failing"""
        print(f"\n👤 Testing Sign-up Workflow Simulation")
        
        test_result = {
            "test_name": "Sign-up Workflow Simulation",
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Test the configuration that would be used during sign-up
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                test_result["warnings"].append("No MONGODB_URI for sign-up simulation")
                test_result["status"] = "WARNING"
                return test_result
            
            # Get connection options (this is what the app would use)
            connection_options = DatabasePoolConfig.get_connection_options()
            test_result["details"]["connection_options"] = connection_options
            
            # Simulate multiple concurrent connections (like during sign-up load)
            print(f"   🔄 Simulating concurrent connections...")
            
            async def simulate_signup_connection():
                """Simulate a single sign-up connection"""
                client = AsyncIOMotorClient(mongodb_uri, **connection_options)
                try:
                    # Simulate auth operations
                    await client.admin.command('ping')
                    
                    # Simulate user creation operations
                    db = client.floating_kraken_dash
                    users_collection = db.users
                    
                    # Test document insertion (like creating a user)
                    test_user = {
                        "email": f"test_{int(time.time())}@example.com",
                        "created_at": datetime.now(),
                        "test_signup": True
                    }
                    
                    result = await users_collection.insert_one(test_user)
                    
                    # Clean up
                    await users_collection.delete_one({"_id": result.inserted_id})
                    
                    return True
                    
                except Exception as e:
                    print(f"      ❌ Signup simulation error: {e}")
                    return False
                finally:
                    client.close()
            
            # Run multiple concurrent simulations
            tasks = [simulate_signup_connection() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_connections = sum(1 for r in results if r is True)
            failed_connections = len(results) - successful_connections
            
            test_result["details"]["total_simulations"] = len(results)
            test_result["details"]["successful_connections"] = successful_connections
            test_result["details"]["failed_connections"] = failed_connections
            
            if failed_connections == 0:
                test_result["status"] = "PASSED"
                print(f"   ✅ All {successful_connections} sign-up simulations successful")
            else:
                test_result["status"] = "FAILED"
                test_result["errors"].append(f"{failed_connections} out of {len(results)} simulations failed")
                print(f"   ❌ {failed_connections} sign-up simulations failed")
            
        except Exception as e:
            test_result["errors"].append(f"Sign-up simulation error: {str(e)}")
            test_result["status"] = "FAILED"
            print(f"   💥 Sign-up simulation error: {e}")
        
        return test_result
    
    async def run_comprehensive_tests(self):
        """Run all SSL/TLS fix validation tests"""
        print("🚀 Starting MongoDB SSL/TLS Fix Validation")
        print("=" * 60)
        
        # Backup environment
        self.backup_environment()
        
        try:
            # Test 1: Current environment (should work)
            test1 = await self.test_connection_with_config(
                "Current Environment Configuration",
                {},  # Use current environment
                expected_tls=DatabasePoolConfig._is_mongodb_atlas_uri(os.getenv("MONGODB_URI", "")),
                should_succeed=True
            )
            self.test_results["test_details"].append(test1)
            
            # Test 2: Atlas auto-detection (no MONGODB_TLS_ENABLED)
            mongodb_uri = os.getenv("MONGODB_URI", "")
            if DatabasePoolConfig._is_mongodb_atlas_uri(mongodb_uri):
                test2 = await self.test_connection_with_config(
                    "Atlas Auto-Detection (No TLS Env Var)",
                    {"MONGODB_TLS_ENABLED": None},  # Remove the env var
                    expected_tls=True,  # Should auto-detect Atlas and enable TLS
                    should_succeed=True
                )
                self.test_results["test_details"].append(test2)
            
            # Test 3: Explicit TLS enabled
            test3 = await self.test_connection_with_config(
                "Explicit TLS Enabled",
                {"MONGODB_TLS_ENABLED": "true"},
                expected_tls=True,
                should_succeed=True
            )
            self.test_results["test_details"].append(test3)
            
            # Test 4: Explicit TLS disabled (for non-Atlas)
            if not DatabasePoolConfig._is_mongodb_atlas_uri(mongodb_uri):
                test4 = await self.test_connection_with_config(
                    "Explicit TLS Disabled (Non-Atlas)",
                    {"MONGODB_TLS_ENABLED": "false"},
                    expected_tls=False,
                    should_succeed=True
                )
                self.test_results["test_details"].append(test4)
            
            # Test 5: Invalid TLS env var (should fallback to Atlas detection)
            test5 = await self.test_connection_with_config(
                "Invalid TLS Env Var (Fallback Test)",
                {"MONGODB_TLS_ENABLED": "invalid_value"},
                expected_tls=DatabasePoolConfig._is_mongodb_atlas_uri(mongodb_uri),
                should_succeed=True
            )
            self.test_results["test_details"].append(test5)
            
            # Test 6: Atlas auto-detection functionality
            atlas_test = await self.test_atlas_auto_detection()
            self.test_results["test_details"].append(atlas_test)
            
            # Test 7: Sign-up workflow simulation
            signup_test = await self.test_signup_workflow_simulation()
            self.test_results["test_details"].append(signup_test)
            
            # Calculate summary
            for test in self.test_results["test_details"]:
                self.test_results["test_summary"]["total_tests"] += 1
                if test["status"] == "PASSED":
                    self.test_results["test_summary"]["passed"] += 1
                elif test["status"] == "FAILED":
                    self.test_results["test_summary"]["failed"] += 1
                elif test["status"] == "WARNING":
                    self.test_results["test_summary"]["warnings"] += 1
            
        finally:
            # Always restore environment
            self.restore_environment()
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        summary = self.test_results["test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test in self.test_results["test_details"]:
            status_icon = {"PASSED": "✅", "FAILED": "❌", "WARNING": "⚠️"}.get(test["status"], "❓")
            print(f"{status_icon} {test['test_name']}: {test['status']}")
            
            if test.get("errors"):
                for error in test["errors"]:
                    print(f"   ❌ {error}")
            
            if test.get("warnings"):
                for warning in test["warnings"]:
                    print(f"   ⚠️  {warning}")
        
        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT:")
        if summary['failed'] == 0:
            print("✅ MongoDB SSL/TLS fix is working correctly!")
            print("✅ Sign-up workflow should no longer experience SSL handshake failures")
            print("✅ Atlas auto-detection is functioning properly")
        else:
            print("❌ Issues detected with MongoDB SSL/TLS fix")
            print("❌ Sign-up workflow may still experience problems")
        
        return summary['failed'] == 0

async def main():
    """Main test execution"""
    validator = MongoDBSSLTLSFixValidator()
    
    try:
        # Run comprehensive tests
        results = await validator.run_comprehensive_tests()
        
        # Print summary
        success = validator.print_summary()
        
        # Save detailed results
        results_file = f"mongodb_ssl_tls_fix_validation_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())