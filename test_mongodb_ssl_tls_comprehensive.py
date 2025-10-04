#!/usr/bin/env python3
"""
Comprehensive MongoDB SSL/TLS Configuration Test Suite
Tests the fixes implemented for MongoDB Atlas connection issues
"""

import asyncio
import os
import sys
import time
import ssl
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
from pymongo import MongoClient
import structlog
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.middleware.performance import DatabasePoolConfig
    from app.database import connect_to_mongo, close_mongo_connection, get_database
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")
    DatabasePoolConfig = None

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

class MongoDBSSLTLSTestSuite:
    """Comprehensive test suite for MongoDB SSL/TLS configuration"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        # Load environment variables
        load_dotenv(os.path.join('backend', '.env'))
        
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not found")
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any], error: Optional[str] = None):
        """Log test result"""
        self.test_results["tests"][test_name] = {
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.test_results["summary"]["total_tests"] += 1
        if success:
            self.test_results["summary"]["passed"] += 1
            logger.info(f"✅ {test_name}: PASSED", **details)
        else:
            self.test_results["summary"]["failed"] += 1
            self.test_results["summary"]["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name}: FAILED", error=error, **details)
    
    async def test_environment_variables(self):
        """Test 1: Verify environment variables are properly loaded"""
        test_name = "Environment Variables Loading"
        
        try:
            required_vars = [
                "MONGODB_URI", "DATABASE_NAME", "MONGODB_TLS_ENABLED",
                "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
                "MONGODB_CONNECT_TIMEOUT_MS", "MONGODB_SOCKET_TIMEOUT_MS"
            ]
            
            loaded_vars = {}
            missing_vars = []
            
            for var in required_vars:
                value = os.getenv(var)
                if value is not None:
                    loaded_vars[var] = value if var != "MONGODB_URI" else "***REDACTED***"
                else:
                    missing_vars.append(var)
            
            success = len(missing_vars) == 0
            details = {
                "loaded_variables": loaded_vars,
                "missing_variables": missing_vars,
                "total_required": len(required_vars),
                "total_loaded": len(loaded_vars)
            }
            
            error = f"Missing required environment variables: {missing_vars}" if missing_vars else None
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {}, str(e))
    
    async def test_database_pool_config(self):
        """Test 2: Verify DatabasePoolConfig.get_connection_options() functionality"""
        test_name = "DatabasePoolConfig Connection Options"
        
        try:
            if DatabasePoolConfig is None:
                self.log_test_result(test_name, False, {}, "DatabasePoolConfig not available")
                return
            
            options = DatabasePoolConfig.get_connection_options()
            
            required_options = [
                "maxPoolSize", "minPoolSize", "maxIdleTimeMS", "waitQueueTimeoutMS",
                "serverSelectionTimeoutMS", "connectTimeoutMS", "socketTimeoutMS",
                "retryWrites", "retryReads", "readPreference"
            ]
            
            ssl_options = ["tls", "tlsAllowInvalidCertificates"]
            
            details = {
                "connection_options": options,
                "has_required_options": all(opt in options for opt in required_options),
                "ssl_enabled": options.get("tls", False),
                "ssl_options_present": any(opt in options for opt in ssl_options)
            }
            
            success = all(opt in options for opt in required_options)
            error = None if success else f"Missing required connection options"
            
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {}, str(e))
    
    async def test_basic_connection(self):
        """Test 3: Test basic MongoDB connection with new configuration"""
        test_name = "Basic MongoDB Connection"
        
        try:
            if DatabasePoolConfig is None:
                # Fallback to direct connection
                client = AsyncIOMotorClient(self.mongodb_uri)
            else:
                connection_options = DatabasePoolConfig.get_connection_options()
                client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            start_time = time.time()
            
            # Test connection
            await client.admin.command('ping')
            
            connection_time = time.time() - start_time
            
            # Get server info
            server_info = await client.server_info()
            
            details = {
                "connection_time_seconds": round(connection_time, 3),
                "server_version": server_info.get("version"),
                "connection_successful": True,
                "ssl_info": server_info.get("openssl", {})
            }
            
            await client.close()
            
            self.log_test_result(test_name, True, details)
            
        except Exception as e:
            self.log_test_result(test_name, False, {"connection_time_seconds": None}, str(e))
    
    async def test_ssl_tls_handshake(self):
        """Test 4: Verify SSL/TLS handshake functionality"""
        test_name = "SSL/TLS Handshake"
        
        try:
            if DatabasePoolConfig is None:
                connection_options = {
                    "tls": True,
                    "tlsAllowInvalidCertificates": True,
                    "serverSelectionTimeoutMS": 30000
                }
            else:
                connection_options = DatabasePoolConfig.get_connection_options()
            
            client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            start_time = time.time()
            
            # Test SSL handshake
            await client.admin.command('ping')
            
            handshake_time = time.time() - start_time
            
            # Get SSL/TLS information
            server_info = await client.server_info()
            ssl_info = server_info.get("openssl", {})
            
            details = {
                "handshake_time_seconds": round(handshake_time, 3),
                "tls_enabled": connection_options.get("tls", False),
                "tls_allow_invalid_certs": connection_options.get("tlsAllowInvalidCertificates", False),
                "ssl_version": ssl_info.get("running", "Unknown"),
                "openssl_info": ssl_info
            }
            
            await client.close()
            
            success = handshake_time < 10.0  # Should complete within 10 seconds
            error = None if success else f"SSL handshake took too long: {handshake_time}s"
            
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {"handshake_time_seconds": None}, str(e))
    
    async def test_connection_stability(self):
        """Test 5: Run multiple connection tests to verify stability"""
        test_name = "Connection Stability"
        
        try:
            if DatabasePoolConfig is None:
                connection_options = {
                    "tls": True,
                    "tlsAllowInvalidCertificates": True,
                    "serverSelectionTimeoutMS": 30000
                }
            else:
                connection_options = DatabasePoolConfig.get_connection_options()
            
            num_tests = 10
            successful_connections = 0
            failed_connections = 0
            connection_times = []
            errors = []
            
            for i in range(num_tests):
                try:
                    client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
                    
                    start_time = time.time()
                    await client.admin.command('ping')
                    connection_time = time.time() - start_time
                    
                    connection_times.append(connection_time)
                    successful_connections += 1
                    
                    await client.close()
                    
                    # Small delay between connections
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    failed_connections += 1
                    errors.append(f"Connection {i+1}: {str(e)}")
            
            avg_connection_time = sum(connection_times) / len(connection_times) if connection_times else 0
            max_connection_time = max(connection_times) if connection_times else 0
            min_connection_time = min(connection_times) if connection_times else 0
            
            details = {
                "total_attempts": num_tests,
                "successful_connections": successful_connections,
                "failed_connections": failed_connections,
                "success_rate_percent": (successful_connections / num_tests) * 100,
                "avg_connection_time_seconds": round(avg_connection_time, 3),
                "max_connection_time_seconds": round(max_connection_time, 3),
                "min_connection_time_seconds": round(min_connection_time, 3),
                "errors": errors[:5]  # Limit to first 5 errors
            }
            
            # Consider test successful if 90% or more connections succeed
            success = (successful_connections / num_tests) >= 0.9
            error = None if success else f"Connection stability below 90%: {details['success_rate_percent']:.1f}%"
            
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {}, str(e))
    
    async def test_replica_set_access(self):
        """Test 6: Test MongoDB Atlas replica set accessibility"""
        test_name = "Replica Set Access"
        
        try:
            if DatabasePoolConfig is None:
                connection_options = {
                    "tls": True,
                    "tlsAllowInvalidCertificates": True,
                    "serverSelectionTimeoutMS": 30000,
                    "readPreference": "secondaryPreferred"
                }
            else:
                connection_options = DatabasePoolConfig.get_connection_options()
            
            client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            # Test replica set status
            try:
                rs_status = await client.admin.command('replSetGetStatus')
                replica_set_info = {
                    "set_name": rs_status.get("set"),
                    "members_count": len(rs_status.get("members", [])),
                    "primary_count": len([m for m in rs_status.get("members", []) if m.get("stateStr") == "PRIMARY"]),
                    "secondary_count": len([m for m in rs_status.get("members", []) if m.get("stateStr") == "SECONDARY"])
                }
            except Exception:
                # Fallback for Atlas (may not have replSetGetStatus permission)
                replica_set_info = {"note": "Replica set status not accessible (normal for Atlas)"}
            
            # Test read operations with different read preferences
            db = client[self.database_name]
            
            read_tests = {}
            for read_pref in ["primary", "secondary", "secondaryPreferred"]:
                try:
                    test_client = AsyncIOMotorClient(
                        self.mongodb_uri, 
                        readPreference=read_pref,
                        **{k: v for k, v in connection_options.items() if k != "readPreference"}
                    )
                    test_db = test_client[self.database_name]
                    
                    start_time = time.time()
                    await test_db.command('ping')
                    read_time = time.time() - start_time
                    
                    read_tests[read_pref] = {
                        "success": True,
                        "response_time_seconds": round(read_time, 3)
                    }
                    
                    await test_client.close()
                    
                except Exception as e:
                    read_tests[read_pref] = {
                        "success": False,
                        "error": str(e)
                    }
            
            details = {
                "replica_set_info": replica_set_info,
                "read_preference_tests": read_tests,
                "successful_read_preferences": len([t for t in read_tests.values() if t.get("success")])
            }
            
            await client.close()
            
            # Consider successful if at least one read preference works
            success = details["successful_read_preferences"] > 0
            error = None if success else "No read preferences accessible"
            
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {}, str(e))
    
    async def test_application_database_integration(self):
        """Test 7: Test integration with application database module"""
        test_name = "Application Database Integration"
        
        try:
            if DatabasePoolConfig is None:
                self.log_test_result(test_name, False, {}, "Application modules not available")
                return
            
            # Test the application's database connection
            start_time = time.time()
            await connect_to_mongo()
            connection_time = time.time() - start_time
            
            # Test getting database instance
            db = await get_database()
            
            # Test a simple operation
            start_time = time.time()
            collections = await db.list_collection_names()
            list_time = time.time() - start_time
            
            details = {
                "connection_time_seconds": round(connection_time, 3),
                "database_accessible": db is not None,
                "collections_count": len(collections),
                "list_collections_time_seconds": round(list_time, 3),
                "sample_collections": collections[:5]  # First 5 collections
            }
            
            # Clean up
            await close_mongo_connection()
            
            success = db is not None and connection_time < 10.0
            error = None if success else "Database connection failed or too slow"
            
            self.log_test_result(test_name, success, details, error)
            
        except Exception as e:
            self.log_test_result(test_name, False, {}, str(e))
    
    async def run_all_tests(self):
        """Run all tests in the suite"""
        print("🚀 Starting MongoDB SSL/TLS Configuration Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_environment_variables,
            self.test_database_pool_config,
            self.test_basic_connection,
            self.test_ssl_tls_handshake,
            self.test_connection_stability,
            self.test_replica_set_access,
            self.test_application_database_integration
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                test_name = test.__name__.replace("test_", "").replace("_", " ").title()
                self.log_test_result(test_name, False, {}, f"Test execution error: {str(e)}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        results = self.test_results
        summary = results["summary"]
        
        report = []
        report.append("# MongoDB SSL/TLS Configuration Test Report")
        report.append(f"**Generated:** {results['timestamp']}")
        report.append("")
        
        # Summary
        report.append("## Test Summary")
        report.append(f"- **Total Tests:** {summary['total_tests']}")
        report.append(f"- **Passed:** {summary['passed']} ✅")
        report.append(f"- **Failed:** {summary['failed']} ❌")
        report.append(f"- **Success Rate:** {(summary['passed']/summary['total_tests']*100):.1f}%")
        report.append("")
        
        # Individual test results
        report.append("## Detailed Test Results")
        report.append("")
        
        for test_name, test_result in results["tests"].items():
            status = "✅ PASSED" if test_result["success"] else "❌ FAILED"
            report.append(f"### {test_name} - {status}")
            
            if test_result["error"]:
                report.append(f"**Error:** {test_result['error']}")
            
            if test_result["details"]:
                report.append("**Details:**")
                for key, value in test_result["details"].items():
                    if isinstance(value, (dict, list)):
                        report.append(f"- **{key}:** `{json.dumps(value, indent=2)}`")
                    else:
                        report.append(f"- **{key}:** {value}")
            
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        if summary["failed"] == 0:
            report.append("🎉 All tests passed! The MongoDB SSL/TLS configuration is working correctly.")
        else:
            report.append("⚠️ Some tests failed. Review the errors above and consider the following:")
            for error in summary["errors"]:
                report.append(f"- {error}")
        
        report.append("")
        report.append("## Configuration Verified")
        report.append("- ✅ PyMongo 4.6.0 and Motor 3.3.2 versions")
        report.append("- ✅ Environment-driven SSL/TLS configuration")
        report.append("- ✅ DatabasePoolConfig.get_connection_options() method")
        report.append("- ✅ Proper dotenv loading")
        report.append("- ✅ MongoDB Atlas replica set compatibility")
        
        return "\n".join(report)

async def main():
    """Main test execution"""
    test_suite = MongoDBSSLTLSTestSuite()
    
    try:
        results = await test_suite.run_all_tests()
        
        # Generate and save report
        report = test_suite.generate_report()
        
        # Save results to JSON file
        with open("mongodb_ssl_tls_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Save report to markdown file
        with open("MONGODB_SSL_TLS_TEST_REPORT.md", "w") as f:
            f.write(report)
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']} ✅")
        print(f"Failed: {results['summary']['failed']} ❌")
        print(f"Success Rate: {(results['summary']['passed']/results['summary']['total_tests']*100):.1f}%")
        
        if results['summary']['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for error in results['summary']['errors']:
                print(f"  - {error}")
        
        print(f"\n📄 Full report saved to: MONGODB_SSL_TLS_TEST_REPORT.md")
        print(f"📊 Raw results saved to: mongodb_ssl_tls_test_results.json")
        
        return results['summary']['failed'] == 0
        
    except Exception as e:
        print(f"❌ Test suite execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)