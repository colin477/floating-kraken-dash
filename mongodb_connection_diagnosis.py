#!/usr/bin/env python3
"""
MongoDB Connection Timeout and SSL Handshake Failure Diagnosis Script

This script analyzes the specific MongoDB connection issues preventing user signup:
1. Connection timeout with exponential backoff (3s, 6s, 12s, 24s)
2. SSL handshake failures with "connection forcibly closed by remote host"
3. ConnectionFailure after 5 retry attempts
4. 503 Service Unavailable responses

Focus areas:
- SSL/TLS configuration validation
- Connection timeout settings analysis
- Connection pooling parameter review
- MongoDB Atlas cluster connectivity testing
"""

import asyncio
import os
import ssl
import time
import json
from datetime import datetime
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect
import structlog

# Setup logging
logger = structlog.get_logger(__name__)

class MongoDBConnectionDiagnostic:
    """Comprehensive MongoDB connection diagnostic tool"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI", "")
        self.database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment_analysis": {},
            "connection_tests": {},
            "ssl_analysis": {},
            "pool_analysis": {},
            "recommendations": []
        }
    
    def analyze_environment_config(self) -> Dict[str, Any]:
        """Analyze current environment configuration"""
        config = {
            "mongodb_uri_present": bool(self.mongodb_uri),
            "mongodb_uri_type": "atlas" if ".mongodb.net" in self.mongodb_uri else "local",
            "ssl_tls_enabled": os.getenv("MONGODB_TLS_ENABLED", "").lower() == "true",
            "ssl_allow_invalid_certs": os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "").lower() == "true",
            "timeouts": {
                "server_selection": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "30000")),
                "connect": int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "30000")),
                "socket": int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "30000"))
            },
            "pool_settings": {
                "max_pool_size": int(os.getenv("MONGODB_MAX_POOL_SIZE", "150")),
                "min_pool_size": int(os.getenv("MONGODB_MIN_POOL_SIZE", "20")),
                "wait_queue_timeout": int(os.getenv("MONGODB_WAIT_QUEUE_TIMEOUT_MS", "15000")),
                "max_idle_time": int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000"))
            },
            "retry_settings": {
                "max_retries": int(os.getenv("MONGODB_MAX_RETRIES", "4")),
                "retry_delay": float(os.getenv("MONGODB_RETRY_DELAY", "3.0"))
            }
        }
        
        # Identify potential issues
        issues = []
        
        # Issue 1: SSL/TLS configuration mismatch
        if config["mongodb_uri_type"] == "atlas" and not config["ssl_tls_enabled"]:
            issues.append("CRITICAL: MongoDB Atlas requires SSL/TLS but MONGODB_TLS_ENABLED=false")
        
        # Issue 2: Invalid certificate handling in production
        if config["ssl_allow_invalid_certs"] and config["mongodb_uri_type"] == "atlas":
            issues.append("WARNING: MONGODB_TLS_ALLOW_INVALID_CERTIFICATES=true may cause SSL handshake issues with Atlas")
        
        # Issue 3: Aggressive timeout settings
        if config["timeouts"]["connect"] < 20000:
            issues.append("WARNING: connectTimeoutMS < 20s may be too aggressive for Atlas connections")
        
        # Issue 4: Pool size issues
        if config["pool_settings"]["max_pool_size"] > 100:
            issues.append("WARNING: maxPoolSize > 100 may overwhelm Atlas free tier")
        
        config["identified_issues"] = issues
        return config
    
    async def test_basic_connection(self) -> Dict[str, Any]:
        """Test basic MongoDB connection with current settings"""
        test_result = {
            "success": False,
            "error": None,
            "connection_time": None,
            "server_info": None,
            "ssl_info": None
        }
        
        try:
            start_time = time.time()
            
            # Import DatabasePoolConfig to use same settings as app
            import sys
            sys.path.append('backend')
            from app.middleware.performance import DatabasePoolConfig
            connection_options = DatabasePoolConfig.get_connection_options()
            
            logger.info("Testing connection with current app settings", options=connection_options)
            
            client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            # Test connection with ping
            await asyncio.wait_for(
                client.admin.command('ping'),
                timeout=connection_options.get('serverSelectionTimeoutMS', 30000) / 1000
            )
            
            connection_time = time.time() - start_time
            test_result["connection_time"] = connection_time
            test_result["success"] = True
            
            # Get server info
            try:
                server_info = await client.server_info()
                test_result["server_info"] = {
                    "version": server_info.get("version"),
                    "git_version": server_info.get("gitVersion"),
                    "openssl": server_info.get("openssl", {})
                }
            except Exception as e:
                test_result["server_info_error"] = str(e)
            
            await client.close()
            
        except asyncio.TimeoutError as e:
            test_result["error"] = f"Connection timeout: {e}"
            test_result["error_type"] = "timeout"
        except ConnectionFailure as e:
            test_result["error"] = f"Connection failure: {e}"
            test_result["error_type"] = "connection_failure"
            
            # Check for SSL-specific errors
            error_str = str(e).lower()
            if any(ssl_indicator in error_str for ssl_indicator in ['ssl', 'tls', 'certificate', 'handshake']):
                test_result["ssl_error"] = True
        except Exception as e:
            test_result["error"] = f"Unexpected error: {e}"
            test_result["error_type"] = "unexpected"
        
        return test_result
    
    async def test_ssl_configurations(self) -> Dict[str, Any]:
        """Test different SSL/TLS configurations"""
        ssl_tests = {}
        
        # Test configurations to try
        test_configs = [
            {
                "name": "minimal_ssl",
                "description": "Minimal SSL configuration for Atlas",
                "options": {
                    "tls": True,
                    "authSource": "admin",
                    "serverSelectionTimeoutMS": 30000,
                    "connectTimeoutMS": 30000,
                    "socketTimeoutMS": 30000
                }
            },
            {
                "name": "strict_ssl",
                "description": "Strict SSL without invalid certificates",
                "options": {
                    "tls": True,
                    "authSource": "admin",
                    "serverSelectionTimeoutMS": 30000,
                    "connectTimeoutMS": 30000,
                    "socketTimeoutMS": 30000,
                    "retryWrites": True,
                    "retryReads": True
                }
            },
            {
                "name": "relaxed_ssl",
                "description": "Relaxed SSL with invalid certificates allowed",
                "options": {
                    "tls": True,
                    "tlsAllowInvalidCertificates": True,
                    "authSource": "admin",
                    "serverSelectionTimeoutMS": 30000,
                    "connectTimeoutMS": 30000,
                    "socketTimeoutMS": 30000
                }
            }
        ]
        
        for config in test_configs:
            test_result = {
                "success": False,
                "error": None,
                "connection_time": None
            }
            
            try:
                start_time = time.time()
                client = AsyncIOMotorClient(self.mongodb_uri, **config["options"])
                
                await asyncio.wait_for(
                    client.admin.command('ping'),
                    timeout=30
                )
                
                test_result["connection_time"] = time.time() - start_time
                test_result["success"] = True
                await client.close()
                
            except Exception as e:
                test_result["error"] = str(e)
                test_result["error_type"] = type(e).__name__
            
            ssl_tests[config["name"]] = {
                "description": config["description"],
                "options": config["options"],
                "result": test_result
            }
        
        return ssl_tests
    
    async def analyze_connection_patterns(self) -> Dict[str, Any]:
        """Analyze connection patterns and retry behavior"""
        pattern_analysis = {
            "retry_attempts": [],
            "connection_stability": {},
            "pool_behavior": {}
        }
        
        # Test retry pattern (simulate the exponential backoff)
        retry_delays = [3, 6, 12, 24]  # As mentioned in the logs
        
        for i, delay in enumerate(retry_delays):
            attempt_result = {
                "attempt": i + 1,
                "delay": delay,
                "success": False,
                "error": None,
                "connection_time": None
            }
            
            try:
                start_time = time.time()
                
                # Use minimal connection options for this test
                client = AsyncIOMotorClient(
                    self.mongodb_uri,
                    tls=True,
                    authSource="admin",
                    serverSelectionTimeoutMS=10000,  # Shorter timeout for testing
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )
                
                await asyncio.wait_for(client.admin.command('ping'), timeout=10)
                
                attempt_result["connection_time"] = time.time() - start_time
                attempt_result["success"] = True
                await client.close()
                break  # Success, no need to continue
                
            except Exception as e:
                attempt_result["error"] = str(e)
                attempt_result["error_type"] = type(e).__name__
                
                # Wait for the retry delay if not the last attempt
                if i < len(retry_delays) - 1:
                    await asyncio.sleep(delay)
            
            pattern_analysis["retry_attempts"].append(attempt_result)
        
        return pattern_analysis
    
    def generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        env_config = self.results.get("environment_analysis", {})
        
        # SSL/TLS recommendations
        if env_config.get("ssl_allow_invalid_certs"):
            recommendations.append(
                "CRITICAL: Set MONGODB_TLS_ALLOW_INVALID_CERTIFICATES=false for production. "
                "Invalid certificate handling can cause SSL handshake failures with MongoDB Atlas."
            )
        
        # Connection pool recommendations
        pool_settings = env_config.get("pool_settings", {})
        if pool_settings.get("max_pool_size", 0) > 100:
            recommendations.append(
                "Reduce MONGODB_MAX_POOL_SIZE to 50-100 for Atlas free tier to prevent connection exhaustion."
            )
        
        # Timeout recommendations
        timeouts = env_config.get("timeouts", {})
        if timeouts.get("connect", 0) < 20000:
            recommendations.append(
                "Increase MONGODB_CONNECT_TIMEOUT_MS to at least 20000ms for stable Atlas connections."
            )
        
        # Retry logic recommendations
        recommendations.append(
            "Implement exponential backoff with jitter to prevent thundering herd problems during retries."
        )
        
        recommendations.append(
            "Add connection health checks and circuit breaker pattern to prevent cascading failures."
        )
        
        recommendations.append(
            "Monitor connection pool metrics to identify connection leaks or exhaustion."
        )
        
        return recommendations
    
    async def run_full_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnosis and return results"""
        print("🔍 Starting MongoDB Connection Diagnosis...")
        
        # 1. Analyze environment configuration
        print("📋 Analyzing environment configuration...")
        self.results["environment_analysis"] = self.analyze_environment_config()
        
        # 2. Test basic connection
        print("🔌 Testing basic connection...")
        self.results["connection_tests"]["basic"] = await self.test_basic_connection()
        
        # 3. Test SSL configurations
        print("🔒 Testing SSL/TLS configurations...")
        self.results["ssl_analysis"] = await self.test_ssl_configurations()
        
        # 4. Analyze connection patterns
        print("📊 Analyzing connection patterns...")
        self.results["pool_analysis"] = await self.analyze_connection_patterns()
        
        # 5. Generate recommendations
        print("💡 Generating recommendations...")
        self.results["recommendations"] = self.generate_recommendations()
        
        return self.results

async def main():
    """Main diagnostic function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    diagnostic = MongoDBConnectionDiagnostic()
    results = await diagnostic.run_full_diagnosis()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"mongodb_connection_diagnosis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Diagnosis complete! Results saved to {filename}")
    
    # Print summary
    print("\n" + "="*60)
    print("🚨 CRITICAL ISSUES IDENTIFIED:")
    print("="*60)
    
    env_issues = results["environment_analysis"].get("identified_issues", [])
    for issue in env_issues:
        print(f"• {issue}")
    
    print("\n" + "="*60)
    print("💡 KEY RECOMMENDATIONS:")
    print("="*60)
    
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)
    print("🔍 CONNECTION TEST RESULTS:")
    print("="*60)
    
    basic_test = results["connection_tests"]["basic"]
    if basic_test["success"]:
        print(f"✅ Basic connection: SUCCESS ({basic_test['connection_time']:.2f}s)")
    else:
        print(f"❌ Basic connection: FAILED - {basic_test['error']}")
    
    ssl_tests = results["ssl_analysis"]
    for test_name, test_data in ssl_tests.items():
        result = test_data["result"]
        if result["success"]:
            print(f"✅ {test_name}: SUCCESS ({result['connection_time']:.2f}s)")
        else:
            print(f"❌ {test_name}: FAILED - {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())