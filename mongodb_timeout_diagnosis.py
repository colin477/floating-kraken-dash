#!/usr/bin/env python3
"""
MongoDB Connection Timeout Diagnostic Script

This script analyzes the MongoDB connection timeout issues by:
1. Testing connection parameters and timeouts
2. Validating SSL/TLS configuration
3. Checking network connectivity
4. Analyzing retry logic effectiveness
5. Identifying potential configuration conflicts
"""

import os
import sys
import asyncio
import time
import ssl
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

logger = structlog.get_logger(__name__)

class MongoDBTimeoutDiagnostic:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment_config": {},
            "connection_tests": {},
            "timeout_analysis": {},
            "ssl_tls_analysis": {},
            "recommendations": []
        }
    
    def analyze_environment_config(self):
        """Analyze current environment configuration"""
        print("🔍 Analyzing Environment Configuration...")
        
        config = {
            "MONGODB_URI": self.mongodb_uri[:50] + "..." if len(self.mongodb_uri) > 50 else self.mongodb_uri,
            "DATABASE_NAME": self.database_name,
            "MONGODB_TLS_ENABLED": os.getenv("MONGODB_TLS_ENABLED"),
            "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES"),
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS": os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS"),
            "MONGODB_CONNECT_TIMEOUT_MS": os.getenv("MONGODB_CONNECT_TIMEOUT_MS"),
            "MONGODB_SOCKET_TIMEOUT_MS": os.getenv("MONGODB_SOCKET_TIMEOUT_MS"),
            "MONGODB_MAX_RETRIES": os.getenv("MONGODB_MAX_RETRIES"),
            "MONGODB_RETRY_DELAY": os.getenv("MONGODB_RETRY_DELAY"),
            "is_atlas_connection": ".mongodb.net" in self.mongodb_uri.lower()
        }
        
        self.results["environment_config"] = config
        
        # Print configuration analysis
        print(f"  📋 MongoDB URI: {config['MONGODB_URI']}")
        print(f"  📋 Database: {config['DATABASE_NAME']}")
        print(f"  📋 Atlas Connection: {config['is_atlas_connection']}")
        print(f"  📋 TLS Enabled: {config['MONGODB_TLS_ENABLED']}")
        print(f"  📋 Allow Invalid Certs: {config['MONGODB_TLS_ALLOW_INVALID_CERTIFICATES']}")
        print(f"  📋 Server Selection Timeout: {config['MONGODB_SERVER_SELECTION_TIMEOUT_MS']}ms")
        print(f"  📋 Connect Timeout: {config['MONGODB_CONNECT_TIMEOUT_MS']}ms")
        print(f"  📋 Socket Timeout: {config['MONGODB_SOCKET_TIMEOUT_MS']}ms")
        print(f"  📋 Max Retries: {config['MONGODB_MAX_RETRIES']}")
        print(f"  📋 Retry Delay: {config['MONGODB_RETRY_DELAY']}s")
        
        return config
    
    def _get_connection_options(self):
        """Get connection options using the same logic as the application"""
        # Import the actual DatabasePoolConfig to use same logic
        sys.path.append('backend')
        from app.middleware.performance import DatabasePoolConfig
        return DatabasePoolConfig.get_connection_options()
    
    async def test_basic_connection(self):
        """Test basic MongoDB connection without retries"""
        print("\n🔌 Testing Basic Connection...")
        
        test_results = {
            "success": False,
            "error": None,
            "duration": 0,
            "server_info": None
        }
        
        try:
            start_time = time.time()
            
            # Get connection options
            connection_options = self._get_connection_options()
            print(f"  📋 Connection Options: {connection_options}")
            
            # Create client
            client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            # Test connection with ping
            await asyncio.wait_for(
                client.admin.command('ping'),
                timeout=connection_options.get('serverSelectionTimeoutMS', 30000) / 1000
            )
            
            # Get server info
            server_info = await client.server_info()
            test_results["server_info"] = {
                "version": server_info.get('version'),
                "openssl": server_info.get('openssl', {}).get('running') if 'openssl' in server_info else None
            }
            
            test_results["success"] = True
            test_results["duration"] = time.time() - start_time
            
            print(f"  ✅ Connection successful in {test_results['duration']:.2f}s")
            print(f"  📋 MongoDB Version: {test_results['server_info']['version']}")
            if test_results['server_info']['openssl']:
                print(f"  📋 TLS Version: {test_results['server_info']['openssl']}")
            
            client.close()
            
        except asyncio.TimeoutError as e:
            test_results["error"] = f"Timeout: {str(e)}"
            test_results["duration"] = time.time() - start_time
            print(f"  ❌ Connection timeout after {test_results['duration']:.2f}s")
            
        except Exception as e:
            test_results["error"] = str(e)
            test_results["duration"] = time.time() - start_time
            print(f"  ❌ Connection failed: {str(e)}")
        
        self.results["connection_tests"]["basic"] = test_results
        return test_results
    
    async def test_retry_mechanism(self):
        """Test the retry mechanism with different timeout values"""
        print("\n🔄 Testing Retry Mechanism...")
        
        retry_tests = []
        timeout_values = [5000, 10000, 15000, 30000]  # Different timeout values in ms
        
        for timeout_ms in timeout_values:
            print(f"  🧪 Testing with {timeout_ms}ms timeout...")
            
            test_result = {
                "timeout_ms": timeout_ms,
                "attempts": 0,
                "success": False,
                "total_duration": 0,
                "errors": []
            }
            
            start_time = time.time()
            max_retries = 3
            retry_delay = 2.0
            
            for attempt in range(max_retries + 1):
                test_result["attempts"] = attempt + 1
                
                try:
                    # Create client with specific timeout
                    connection_options = self._get_connection_options()
                    connection_options["serverSelectionTimeoutMS"] = timeout_ms
                    connection_options["connectTimeoutMS"] = timeout_ms
                    
                    client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
                    
                    # Test connection
                    await asyncio.wait_for(
                        client.admin.command('ping'),
                        timeout=timeout_ms / 1000
                    )
                    
                    test_result["success"] = True
                    test_result["total_duration"] = time.time() - start_time
                    print(f"    ✅ Success on attempt {attempt + 1}")
                    client.close()
                    break
                    
                except Exception as e:
                    error_msg = f"Attempt {attempt + 1}: {str(e)}"
                    test_result["errors"].append(error_msg)
                    print(f"    ❌ {error_msg}")
                    
                    if attempt < max_retries:
                        print(f"    ⏳ Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
            
            test_result["total_duration"] = time.time() - start_time
            retry_tests.append(test_result)
            
            if not test_result["success"]:
                print(f"    ❌ Failed after {test_result['attempts']} attempts in {test_result['total_duration']:.2f}s")
        
        self.results["connection_tests"]["retry_mechanism"] = retry_tests
        return retry_tests
    
    async def analyze_ssl_tls_config(self):
        """Analyze SSL/TLS configuration issues"""
        print("\n🔒 Analyzing SSL/TLS Configuration...")
        
        ssl_analysis = {
            "tls_enabled": os.getenv("MONGODB_TLS_ENABLED", "").lower() == "true",
            "allow_invalid_certs": os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "").lower() == "true",
            "is_atlas": ".mongodb.net" in self.mongodb_uri.lower(),
            "ssl_tests": []
        }
        
        # Test different SSL configurations
        ssl_configs = [
            {"name": "Current Config", "tls": ssl_analysis["tls_enabled"], "allow_invalid": ssl_analysis["allow_invalid_certs"]},
            {"name": "Force TLS On", "tls": True, "allow_invalid": False},
            {"name": "TLS with Invalid Certs", "tls": True, "allow_invalid": True},
            {"name": "TLS Off (if not Atlas)", "tls": False, "allow_invalid": False}
        ]
        
        for config in ssl_configs:
            if config["name"] == "TLS Off (if not Atlas)" and ssl_analysis["is_atlas"]:
                continue  # Skip TLS off test for Atlas
                
            print(f"  🧪 Testing: {config['name']}")
            
            test_result = {
                "config_name": config["name"],
                "tls_enabled": config["tls"],
                "allow_invalid_certs": config["allow_invalid"],
                "success": False,
                "error": None,
                "duration": 0
            }
            
            try:
                start_time = time.time()
                
                # Build connection options
                connection_options = {
                    "serverSelectionTimeoutMS": 10000,
                    "connectTimeoutMS": 10000,
                    "socketTimeoutMS": 10000
                }
                
                if config["tls"]:
                    connection_options["tls"] = True
                    if config["allow_invalid"]:
                        connection_options["tlsAllowInvalidCertificates"] = True
                    if ssl_analysis["is_atlas"]:
                        connection_options["authSource"] = "admin"
                
                client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
                
                # Test connection
                await asyncio.wait_for(
                    client.admin.command('ping'),
                    timeout=10
                )
                
                test_result["success"] = True
                test_result["duration"] = time.time() - start_time
                print(f"    ✅ Success in {test_result['duration']:.2f}s")
                
                client.close()
                
            except Exception as e:
                test_result["error"] = str(e)
                test_result["duration"] = time.time() - start_time
                print(f"    ❌ Failed: {str(e)}")
            
            ssl_analysis["ssl_tests"].append(test_result)
        
        self.results["ssl_tls_analysis"] = ssl_analysis
        return ssl_analysis
    
    def generate_recommendations(self):
        """Generate recommendations based on analysis"""
        print("\n💡 Generating Recommendations...")
        
        recommendations = []
        
        # Analyze basic connection results
        basic_test = self.results["connection_tests"].get("basic", {})
        if not basic_test.get("success"):
            if "timeout" in basic_test.get("error", "").lower():
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Timeout Configuration",
                    "issue": "Basic connection is timing out",
                    "recommendation": "Increase timeout values: serverSelectionTimeoutMS, connectTimeoutMS, and socketTimeoutMS to 60000ms (60 seconds)",
                    "action": "Update environment variables or connection options"
                })
        
        # Analyze retry mechanism
        retry_tests = self.results["connection_tests"].get("retry_mechanism", [])
        successful_timeouts = [test for test in retry_tests if test.get("success")]
        
        if not successful_timeouts:
            recommendations.append({
                "priority": "HIGH",
                "category": "Network Connectivity",
                "issue": "All timeout values failed - possible network or DNS issue",
                "recommendation": "Check network connectivity to MongoDB Atlas, verify DNS resolution, and check firewall settings",
                "action": "Test network connectivity outside the application"
            })
        elif len(successful_timeouts) < len(retry_tests):
            min_working_timeout = min(test["timeout_ms"] for test in successful_timeouts)
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Timeout Optimization",
                "issue": f"Connection succeeds with {min_working_timeout}ms timeout but fails with lower values",
                "recommendation": f"Set minimum timeout values to {min_working_timeout}ms for reliable connections",
                "action": f"Update MONGODB_SERVER_SELECTION_TIMEOUT_MS to {min_working_timeout}"
            })
        
        # Analyze SSL/TLS configuration
        ssl_analysis = self.results.get("ssl_tls_analysis", {})
        ssl_tests = ssl_analysis.get("ssl_tests", [])
        current_config_test = next((test for test in ssl_tests if test["config_name"] == "Current Config"), None)
        
        if current_config_test and not current_config_test.get("success"):
            # Find working SSL config
            working_configs = [test for test in ssl_tests if test.get("success")]
            if working_configs:
                best_config = working_configs[0]
                recommendations.append({
                    "priority": "HIGH",
                    "category": "SSL/TLS Configuration",
                    "issue": "Current SSL/TLS configuration is failing",
                    "recommendation": f"Use working configuration: TLS={best_config['tls_enabled']}, Allow Invalid Certs={best_config['allow_invalid_certs']}",
                    "action": f"Update MONGODB_TLS_ENABLED={str(best_config['tls_enabled']).lower()}, MONGODB_TLS_ALLOW_INVALID_CERTIFICATES={str(best_config['allow_invalid_certs']).lower()}"
                })
        
        # Check environment configuration issues
        env_config = self.results.get("environment_config", {})
        if env_config.get("MONGODB_MAX_RETRIES") is None:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Retry Configuration",
                "issue": "MONGODB_MAX_RETRIES not set - using default of 3",
                "recommendation": "Explicitly set MONGODB_MAX_RETRIES=4 for better reliability",
                "action": "Add MONGODB_MAX_RETRIES=4 to .env file"
            })
        
        if env_config.get("MONGODB_RETRY_DELAY") is None:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Retry Configuration", 
                "issue": "MONGODB_RETRY_DELAY not set - using default of 2.0s",
                "recommendation": "Explicitly set MONGODB_RETRY_DELAY=3.0 for better spacing between retries",
                "action": "Add MONGODB_RETRY_DELAY=3.0 to .env file"
            })
        
        # Check for potential connection pool issues
        if env_config.get("is_atlas_connection") and not ssl_analysis.get("tls_enabled"):
            recommendations.append({
                "priority": "HIGH",
                "category": "Atlas Configuration",
                "issue": "MongoDB Atlas connection detected but TLS not explicitly enabled",
                "recommendation": "Explicitly enable TLS for Atlas connections",
                "action": "Set MONGODB_TLS_ENABLED=true in .env file"
            })
        
        self.results["recommendations"] = recommendations
        
        # Print recommendations
        for rec in recommendations:
            priority_emoji = "🚨" if rec["priority"] == "HIGH" else "⚠️" if rec["priority"] == "MEDIUM" else "ℹ️"
            print(f"  {priority_emoji} {rec['priority']} - {rec['category']}")
            print(f"    Issue: {rec['issue']}")
            print(f"    Recommendation: {rec['recommendation']}")
            print(f"    Action: {rec['action']}")
            print()
        
        return recommendations
    
    async def run_diagnosis(self):
        """Run complete diagnosis"""
        print("🔍 MongoDB Connection Timeout Diagnosis")
        print("=" * 50)
        
        # Analyze environment
        self.analyze_environment_config()
        
        # Test basic connection
        await self.test_basic_connection()
        
        # Test retry mechanism
        await self.test_retry_mechanism()
        
        # Analyze SSL/TLS
        await self.analyze_ssl_tls_config()
        
        # Generate recommendations
        self.generate_recommendations()
        
        print("\n📊 Diagnosis Complete!")
        print("=" * 50)
        
        return self.results

async def main():
    """Main diagnostic function"""
    diagnostic = MongoDBTimeoutDiagnostic()
    results = await diagnostic.run_diagnosis()
    
    # Save results to file
    import json
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"mongodb_timeout_diagnosis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {filename}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())