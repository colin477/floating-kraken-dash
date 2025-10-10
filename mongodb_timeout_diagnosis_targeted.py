#!/usr/bin/env python3
"""
Targeted MongoDB Connection Timeout Diagnosis Script

This script focuses on the two most likely sources of timeout issues:
1. Environment Variable Configuration Issues
2. SSL/TLS Handshake Failures

Based on error patterns:
- "MongoDB connection timeout on attempt X. Retrying in Y seconds"
- "Connection timeout after 5 attempts"
- "Unexpected error during user registration: Connection timeout after 5 attempts"
- 503 Service Unavailable responses
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

class TargetedMongoDBDiagnostic:
    """Focused diagnostic for the two most likely timeout causes"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "diagnosis_focus": "Environment Variables & SSL/TLS Issues",
            "environment_validation": {},
            "ssl_handshake_tests": {},
            "connection_attempts": [],
            "recommendations": []
        }
    
    def validate_environment_configuration(self) -> Dict[str, Any]:
        """Validate critical environment variables for production deployment"""
        validation = {
            "critical_variables": {},
            "configuration_issues": [],
            "production_readiness": "UNKNOWN"
        }
        
        # Check critical environment variables
        critical_vars = {
            "MONGODB_URI": os.getenv("MONGODB_URI"),
            "DATABASE_NAME": os.getenv("DATABASE_NAME"),
            "MONGODB_TLS_ENABLED": os.getenv("MONGODB_TLS_ENABLED"),
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS": os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS"),
            "MONGODB_CONNECT_TIMEOUT_MS": os.getenv("MONGODB_CONNECT_TIMEOUT_MS"),
            "MONGODB_SOCKET_TIMEOUT_MS": os.getenv("MONGODB_SOCKET_TIMEOUT_MS")
        }
        
        for var_name, var_value in critical_vars.items():
            validation["critical_variables"][var_name] = {
                "present": var_value is not None,
                "value": var_value if var_value else "NOT_SET",
                "masked_value": self._mask_sensitive_value(var_name, var_value)
            }
        
        # Identify configuration issues
        issues = []
        
        # Issue 1: Missing MongoDB URI
        if not critical_vars["MONGODB_URI"]:
            issues.append({
                "severity": "CRITICAL",
                "issue": "MONGODB_URI not set",
                "impact": "Application cannot connect to database",
                "fix": "Set MONGODB_URI environment variable with MongoDB Atlas connection string"
            })
        elif critical_vars["MONGODB_URI"]:
            # Validate URI format
            uri = critical_vars["MONGODB_URI"]
            if not uri.startswith("mongodb"):
                issues.append({
                    "severity": "CRITICAL",
                    "issue": "Invalid MONGODB_URI format",
                    "impact": "Connection will fail",
                    "fix": "Use proper MongoDB connection string format"
                })
            elif ".mongodb.net" in uri and critical_vars["MONGODB_TLS_ENABLED"] == "false":
                issues.append({
                    "severity": "CRITICAL",
                    "issue": "MongoDB Atlas requires SSL/TLS but MONGODB_TLS_ENABLED=false",
                    "impact": "SSL handshake will fail",
                    "fix": "Set MONGODB_TLS_ENABLED=true or remove (auto-detected for Atlas)"
                })
        
        # Issue 2: Missing database name
        if not critical_vars["DATABASE_NAME"]:
            issues.append({
                "severity": "HIGH",
                "issue": "DATABASE_NAME not set",
                "impact": "Will use default database name",
                "fix": "Set DATABASE_NAME environment variable"
            })
        
        # Issue 3: Aggressive timeout settings
        connect_timeout = critical_vars["MONGODB_CONNECT_TIMEOUT_MS"]
        if connect_timeout and int(connect_timeout) < 30000:
            issues.append({
                "severity": "MEDIUM",
                "issue": f"MONGODB_CONNECT_TIMEOUT_MS too low ({connect_timeout}ms)",
                "impact": "May cause premature timeouts in production",
                "fix": "Increase to at least 30000ms (30 seconds)"
            })
        
        validation["configuration_issues"] = issues
        
        # Determine production readiness
        critical_issues = [i for i in issues if i["severity"] == "CRITICAL"]
        if critical_issues:
            validation["production_readiness"] = "NOT_READY"
        elif issues:
            validation["production_readiness"] = "NEEDS_ATTENTION"
        else:
            validation["production_readiness"] = "READY"
        
        return validation
    
    def _mask_sensitive_value(self, var_name: str, value: str) -> str:
        """Mask sensitive values for logging"""
        if not value:
            return "NOT_SET"
        
        if var_name == "MONGODB_URI" and value:
            # Mask password in URI
            if "://" in value and "@" in value:
                parts = value.split("://")
                if len(parts) == 2:
                    protocol = parts[0]
                    rest = parts[1]
                    if "@" in rest:
                        auth_part, host_part = rest.split("@", 1)
                        if ":" in auth_part:
                            username, _ = auth_part.split(":", 1)
                            return f"{protocol}://{username}:***@{host_part}"
            return value[:20] + "***"
        
        return value
    
    async def test_ssl_handshake_scenarios(self) -> Dict[str, Any]:
        """Test specific SSL/TLS handshake scenarios that cause timeouts"""
        mongodb_uri = os.getenv("MONGODB_URI", "")
        
        if not mongodb_uri:
            return {
                "error": "Cannot test SSL handshake - MONGODB_URI not set",
                "tests": {}
            }
        
        ssl_tests = {}
        
        # Test scenarios that commonly cause SSL handshake timeouts
        test_scenarios = [
            {
                "name": "production_ssl_strict",
                "description": "Production SSL with strict certificate validation",
                "options": {
                    "tls": True,
                    "authSource": "admin",
                    "serverSelectionTimeoutMS": 15000,  # Shorter for testing
                    "connectTimeoutMS": 15000,
                    "socketTimeoutMS": 15000,
                    "retryWrites": True,
                    "retryReads": True
                }
            },
            {
                "name": "ssl_with_longer_timeout",
                "description": "SSL with extended timeouts for slow networks",
                "options": {
                    "tls": True,
                    "authSource": "admin",
                    "serverSelectionTimeoutMS": 60000,  # 60 seconds
                    "connectTimeoutMS": 60000,
                    "socketTimeoutMS": 60000,
                    "retryWrites": True,
                    "retryReads": True
                }
            },
            {
                "name": "minimal_ssl",
                "description": "Minimal SSL configuration",
                "options": {
                    "tls": True,
                    "serverSelectionTimeoutMS": 30000,
                    "connectTimeoutMS": 30000
                }
            }
        ]
        
        for scenario in test_scenarios:
            test_result = await self._test_connection_scenario(mongodb_uri, scenario)
            ssl_tests[scenario["name"]] = {
                "description": scenario["description"],
                "options": scenario["options"],
                "result": test_result
            }
        
        return {"tests": ssl_tests}
    
    async def _test_connection_scenario(self, uri: str, scenario: Dict) -> Dict[str, Any]:
        """Test a specific connection scenario"""
        result = {
            "success": False,
            "error": None,
            "error_type": None,
            "connection_time": None,
            "ssl_handshake_success": False,
            "server_info": None
        }
        
        try:
            start_time = time.time()
            
            client = AsyncIOMotorClient(uri, **scenario["options"])
            
            # Test connection with ping
            await asyncio.wait_for(
                client.admin.command('ping'),
                timeout=scenario["options"].get("serverSelectionTimeoutMS", 30000) / 1000
            )
            
            connection_time = time.time() - start_time
            result["connection_time"] = connection_time
            result["success"] = True
            result["ssl_handshake_success"] = True
            
            # Get server info if possible
            try:
                server_info = await client.server_info()
                result["server_info"] = {
                    "version": server_info.get("version"),
                    "openssl": server_info.get("openssl", {}).get("running", "Unknown")
                }
            except Exception:
                pass
            
            await client.close()
            
        except asyncio.TimeoutError as e:
            result["error"] = f"Connection timeout: {e}"
            result["error_type"] = "timeout"
        except ConnectionFailure as e:
            result["error"] = f"Connection failure: {e}"
            result["error_type"] = "connection_failure"
            
            # Check for SSL-specific errors
            error_str = str(e).lower()
            if any(ssl_indicator in error_str for ssl_indicator in ['ssl', 'tls', 'certificate', 'handshake']):
                result["ssl_handshake_success"] = False
                result["error_type"] = "ssl_handshake_failure"
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            result["error_type"] = "unexpected"
        
        return result
    
    async def simulate_production_connection_attempts(self) -> List[Dict[str, Any]]:
        """Simulate the exact connection retry pattern from the logs"""
        mongodb_uri = os.getenv("MONGODB_URI", "")
        
        if not mongodb_uri:
            return [{
                "error": "Cannot simulate connection attempts - MONGODB_URI not set"
            }]
        
        # Simulate the exact retry pattern: 3s, 6s, 12s, 24s delays
        retry_delays = [3.0, 6.0, 12.0, 24.0]
        max_retries = 4
        
        attempts = []
        
        # Import the actual DatabasePoolConfig to use same settings
        try:
            import sys
            sys.path.append('backend')
            from app.middleware.performance import DatabasePoolConfig
            connection_options = DatabasePoolConfig.get_connection_options()
        except Exception as e:
            # Fallback to basic options
            connection_options = {
                "tls": True,
                "authSource": "admin",
                "serverSelectionTimeoutMS": 45000,
                "connectTimeoutMS": 45000,
                "socketTimeoutMS": 45000
            }
        
        for attempt in range(max_retries + 1):
            attempt_result = {
                "attempt": attempt + 1,
                "delay_before": retry_delays[attempt - 1] if attempt > 0 else 0,
                "success": False,
                "error": None,
                "connection_time": None,
                "timeout_reached": False
            }
            
            try:
                start_time = time.time()
                
                client = AsyncIOMotorClient(mongodb_uri, **connection_options)
                
                # Test with the same timeout as the app
                timeout_seconds = connection_options.get('serverSelectionTimeoutMS', 45000) / 1000
                await asyncio.wait_for(
                    client.admin.command('ping'),
                    timeout=timeout_seconds
                )
                
                connection_time = time.time() - start_time
                attempt_result["connection_time"] = connection_time
                attempt_result["success"] = True
                
                await client.close()
                break  # Success, stop retrying
                
            except asyncio.TimeoutError as e:
                attempt_result["error"] = f"Timeout after {timeout_seconds}s: {e}"
                attempt_result["timeout_reached"] = True
            except Exception as e:
                attempt_result["error"] = f"Connection error: {e}"
            
            attempts.append(attempt_result)
            
            # Wait for retry delay if not the last attempt
            if attempt < max_retries:
                await asyncio.sleep(retry_delays[attempt])
        
        return attempts
    
    def generate_targeted_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific recommendations for the identified issues"""
        recommendations = []
        
        env_validation = self.results.get("environment_validation", {})
        ssl_tests = self.results.get("ssl_handshake_tests", {}).get("tests", {})
        
        # Environment-based recommendations
        if env_validation.get("production_readiness") == "NOT_READY":
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Environment Configuration",
                "issue": "Missing critical environment variables",
                "recommendation": "Set required environment variables in Render deployment",
                "action_items": [
                    "Set MONGODB_URI with MongoDB Atlas connection string",
                    "Set DATABASE_NAME to production database name",
                    "Verify SSL/TLS settings are appropriate for Atlas"
                ]
            })
        
        # SSL/TLS recommendations
        ssl_failures = [name for name, test in ssl_tests.items() 
                       if not test.get("result", {}).get("success", False)]
        
        if ssl_failures:
            recommendations.append({
                "priority": "HIGH",
                "category": "SSL/TLS Configuration",
                "issue": "SSL handshake failures detected",
                "recommendation": "Fix SSL/TLS configuration for MongoDB Atlas",
                "action_items": [
                    "Ensure MONGODB_TLS_ENABLED=true for Atlas connections",
                    "Verify certificate validation settings",
                    "Check network connectivity to MongoDB Atlas",
                    "Consider increasing connection timeouts for production"
                ]
            })
        
        # Timeout recommendations
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Timeout Configuration",
            "issue": "Production timeout settings may be insufficient",
            "recommendation": "Optimize timeout settings for production deployment",
            "action_items": [
                "Increase MONGODB_CONNECT_TIMEOUT_MS to 60000ms (60 seconds)",
                "Increase MONGODB_SERVER_SELECTION_TIMEOUT_MS to 60000ms",
                "Set MONGODB_SOCKET_TIMEOUT_MS to 60000ms",
                "Add connection health checks and retry logic"
            ]
        })
        
        # Production deployment recommendations
        recommendations.append({
            "priority": "HIGH",
            "category": "Production Deployment",
            "issue": "Render deployment environment considerations",
            "recommendation": "Configure deployment for MongoDB Atlas connectivity",
            "action_items": [
                "Verify Render can reach MongoDB Atlas (network/firewall)",
                "Set environment variables in Render dashboard",
                "Configure health checks with appropriate timeouts",
                "Monitor connection pool usage and adjust as needed"
            ]
        })
        
        return recommendations
    
    async def run_targeted_diagnosis(self) -> Dict[str, Any]:
        """Run focused diagnosis on the two most likely issues"""
        print("🎯 Starting Targeted MongoDB Timeout Diagnosis...")
        print("Focus: Environment Variables & SSL/TLS Handshake Issues")
        
        # 1. Validate environment configuration
        print("\n📋 Validating environment configuration...")
        self.results["environment_validation"] = self.validate_environment_configuration()
        
        # 2. Test SSL handshake scenarios
        print("🔒 Testing SSL/TLS handshake scenarios...")
        self.results["ssl_handshake_tests"] = await self.test_ssl_handshake_scenarios()
        
        # 3. Simulate production connection attempts
        print("🔄 Simulating production connection retry pattern...")
        self.results["connection_attempts"] = await self.simulate_production_connection_attempts()
        
        # 4. Generate targeted recommendations
        print("💡 Generating targeted recommendations...")
        self.results["recommendations"] = self.generate_targeted_recommendations()
        
        return self.results

async def main():
    """Main diagnostic function"""
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv('backend/.env')
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables")
    
    diagnostic = TargetedMongoDBDiagnostic()
    results = await diagnostic.run_targeted_diagnosis()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"mongodb_timeout_diagnosis_targeted_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Targeted diagnosis complete! Results saved to {filename}")
    
    # Print focused summary
    print("\n" + "="*70)
    print("🎯 TARGETED DIAGNOSIS RESULTS")
    print("="*70)
    
    # Environment validation results
    env_validation = results["environment_validation"]
    print(f"\n📋 Environment Configuration: {env_validation['production_readiness']}")
    
    critical_issues = [i for i in env_validation.get("configuration_issues", []) 
                      if i["severity"] == "CRITICAL"]
    
    if critical_issues:
        print("\n🚨 CRITICAL ENVIRONMENT ISSUES:")
        for issue in critical_issues:
            print(f"   • {issue['issue']}")
            print(f"     Impact: {issue['impact']}")
            print(f"     Fix: {issue['fix']}")
    
    # SSL test results
    ssl_tests = results["ssl_handshake_tests"].get("tests", {})
    print(f"\n🔒 SSL/TLS Handshake Tests:")
    for test_name, test_data in ssl_tests.items():
        result = test_data["result"]
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        time_info = f" ({result['connection_time']:.2f}s)" if result.get("connection_time") else ""
        print(f"   • {test_name}: {status}{time_info}")
        if not result["success"] and result.get("error"):
            print(f"     Error: {result['error']}")
    
    # Connection attempts
    attempts = results["connection_attempts"]
    if attempts and not attempts[0].get("error"):
        print(f"\n🔄 Connection Retry Simulation:")
        for attempt in attempts:
            if attempt.get("success"):
                print(f"   • Attempt {attempt['attempt']}: ✅ SUCCESS ({attempt['connection_time']:.2f}s)")
                break
            else:
                print(f"   • Attempt {attempt['attempt']}: ❌ FAILED - {attempt.get('error', 'Unknown error')}")
    
    # Top recommendations
    print(f"\n💡 TOP RECOMMENDATIONS:")
    recommendations = results["recommendations"]
    for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
        print(f"\n{i}. [{rec['priority']}] {rec['category']}")
        print(f"   Issue: {rec['issue']}")
        print(f"   Fix: {rec['recommendation']}")

if __name__ == "__main__":
    asyncio.run(main())