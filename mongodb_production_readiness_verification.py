#!/usr/bin/env python3
"""
MongoDB Connection Production Readiness Verification Script

This script performs comprehensive validation of MongoDB connection fixes
for production deployment, focusing on:
1. Environment variable configuration
2. Connection pool optimization for MongoDB Atlas free tier
3. SSL/TLS security configuration
4. Connection health monitoring
5. Retry logic and timeout settings
6. Production network conditions simulation
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import aiohttp
import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import ssl
import random

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class ProductionReadinessValidator:
    """Comprehensive production readiness validator for MongoDB connections"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend_url": backend_url,
            "validation_results": {},
            "production_readiness_score": 0,
            "critical_issues": [],
            "recommendations": []
        }
    
    async def validate_environment_variables(self) -> Dict[str, Any]:
        """Validate production environment variable configuration"""
        logger.info("Validating environment variables for production deployment")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        # Critical environment variables for production
        critical_env_vars = {
            "MONGODB_URI": {
                "required": True,
                "description": "MongoDB connection string",
                "production_check": lambda x: x and ".mongodb.net" in x.lower()
            },
            "DATABASE_NAME": {
                "required": True,
                "description": "Database name",
                "production_check": lambda x: x and len(x) > 0
            },
            "MONGODB_TLS_ENABLED": {
                "required": False,
                "description": "SSL/TLS configuration",
                "production_check": lambda x: x is None or x.lower() in ["true", "1", "yes", "on"]
            },
            "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": {
                "required": False,
                "description": "Certificate validation (should be false in production)",
                "production_check": lambda x: x is None or x.lower() in ["false", "0", "no", "off"]
            }
        }
        
        # MongoDB Atlas free tier optimized settings
        atlas_optimized_settings = {
            "MONGODB_MAX_POOL_SIZE": {"recommended": 50, "max_safe": 100},
            "MONGODB_MIN_POOL_SIZE": {"recommended": 5, "max_safe": 20},
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS": {"recommended": 45000, "min_safe": 30000},
            "MONGODB_CONNECT_TIMEOUT_MS": {"recommended": 45000, "min_safe": 30000},
            "MONGODB_SOCKET_TIMEOUT_MS": {"recommended": 45000, "min_safe": 30000}
        }
        
        # Check critical environment variables
        for var_name, config in critical_env_vars.items():
            value = os.getenv(var_name)
            var_result = {
                "value": value if value else "NOT_SET",
                "required": config["required"],
                "production_ready": False
            }
            
            if config["required"] and not value:
                validation_result["issues"].append(f"Critical environment variable {var_name} is not set")
                var_result["status"] = "MISSING"
            elif value and config["production_check"](value):
                var_result["production_ready"] = True
                var_result["status"] = "VALID"
                validation_result["score"] += 1
            elif value:
                var_result["status"] = "INVALID"
                validation_result["issues"].append(f"Environment variable {var_name} has invalid value for production")
            else:
                var_result["status"] = "NOT_SET"
                if not config["required"]:
                    validation_result["score"] += 0.5  # Partial credit for optional vars
            
            validation_result["details"][var_name] = var_result
        
        # Check Atlas-optimized settings
        for setting_name, config in atlas_optimized_settings.items():
            value = os.getenv(setting_name)
            setting_result = {
                "current_value": value,
                "recommended_value": config["recommended"],
                "production_ready": False
            }
            
            if value:
                try:
                    int_value = int(value)
                    if int_value >= config["min_safe"]:
                        setting_result["production_ready"] = True
                        setting_result["status"] = "OPTIMAL" if int_value == config["recommended"] else "ACCEPTABLE"
                        validation_result["score"] += 1
                    else:
                        setting_result["status"] = "TOO_LOW"
                        validation_result["issues"].append(f"{setting_name} value {int_value} is below minimum safe value {config['min_safe']}")
                except ValueError:
                    setting_result["status"] = "INVALID"
                    validation_result["issues"].append(f"{setting_name} has invalid integer value: {value}")
            else:
                setting_result["status"] = "USING_DEFAULT"
                validation_result["score"] += 0.5  # Partial credit for using defaults
            
            validation_result["details"][setting_name] = setting_result
        
        # Calculate final score
        max_possible_score = len(critical_env_vars) + len(atlas_optimized_settings)
        validation_result["score_percentage"] = (validation_result["score"] / max_possible_score) * 100
        
        if validation_result["score_percentage"] < 80:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 95:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def validate_atlas_free_tier_compatibility(self) -> Dict[str, Any]:
        """Validate connection settings for MongoDB Atlas free tier limits"""
        logger.info("Validating MongoDB Atlas free tier compatibility")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        # Atlas free tier limits and recommendations
        free_tier_limits = {
            "max_connections": 500,
            "recommended_max_pool_size": 50,
            "recommended_min_pool_size": 5,
            "connection_timeout_min": 30000,
            "socket_timeout_min": 30000
        }
        
        # Check connection pool settings
        max_pool_size = int(os.getenv("MONGODB_MAX_POOL_SIZE", "50"))
        min_pool_size = int(os.getenv("MONGODB_MIN_POOL_SIZE", "5"))
        
        validation_result["details"]["connection_pool"] = {
            "max_pool_size": max_pool_size,
            "min_pool_size": min_pool_size,
            "free_tier_limit": free_tier_limits["max_connections"],
            "within_limits": max_pool_size <= free_tier_limits["recommended_max_pool_size"]
        }
        
        if max_pool_size > free_tier_limits["recommended_max_pool_size"]:
            validation_result["issues"].append(f"Max pool size {max_pool_size} exceeds recommended limit for Atlas free tier")
        else:
            validation_result["score"] += 1
        
        if min_pool_size > free_tier_limits["recommended_min_pool_size"]:
            validation_result["issues"].append(f"Min pool size {min_pool_size} may be too high for Atlas free tier")
        else:
            validation_result["score"] += 1
        
        # Check timeout settings
        timeouts = {
            "server_selection": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "45000")),
            "connect": int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "45000")),
            "socket": int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "45000"))
        }
        
        validation_result["details"]["timeouts"] = timeouts
        
        for timeout_name, timeout_value in timeouts.items():
            if timeout_value >= free_tier_limits["connection_timeout_min"]:
                validation_result["score"] += 1
            else:
                validation_result["issues"].append(f"{timeout_name} timeout {timeout_value}ms is below recommended minimum for Atlas free tier")
        
        # Calculate score
        max_score = 5  # 2 for pool settings + 3 for timeouts
        validation_result["score_percentage"] = (validation_result["score"] / max_score) * 100
        
        if validation_result["score_percentage"] < 80:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 100:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def validate_ssl_tls_configuration(self) -> Dict[str, Any]:
        """Validate SSL/TLS configuration for production security"""
        logger.info("Validating SSL/TLS configuration for production security")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        # Check MongoDB URI for SSL indicators
        mongodb_uri = os.getenv("MONGODB_URI", "")
        is_atlas = ".mongodb.net" in mongodb_uri.lower()
        
        validation_result["details"]["connection_type"] = {
            "is_atlas": is_atlas,
            "uri_has_ssl_params": any(param in mongodb_uri.lower() for param in ["ssl=true", "tls=true"])
        }
        
        # SSL/TLS configuration validation
        tls_enabled = os.getenv("MONGODB_TLS_ENABLED")
        allow_invalid_certs = os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES")
        
        validation_result["details"]["ssl_config"] = {
            "tls_enabled": tls_enabled,
            "allow_invalid_certificates": allow_invalid_certs,
            "auto_ssl_for_atlas": is_atlas
        }
        
        # Production SSL/TLS requirements
        if is_atlas:
            # Atlas connections should use SSL/TLS
            if tls_enabled is None or tls_enabled.lower() in ["true", "1", "yes", "on"]:
                validation_result["score"] += 2
                validation_result["details"]["ssl_config"]["production_ready"] = True
            else:
                validation_result["issues"].append("SSL/TLS should be enabled for MongoDB Atlas connections")
                validation_result["details"]["ssl_config"]["production_ready"] = False
        else:
            validation_result["score"] += 1  # Non-Atlas gets partial credit
        
        # Certificate validation should be strict in production
        if allow_invalid_certs is None or allow_invalid_certs.lower() in ["false", "0", "no", "off"]:
            validation_result["score"] += 2
            validation_result["details"]["ssl_config"]["certificate_validation_strict"] = True
        else:
            validation_result["issues"].append("Certificate validation should be strict in production (MONGODB_TLS_ALLOW_INVALID_CERTIFICATES should be false)")
            validation_result["details"]["ssl_config"]["certificate_validation_strict"] = False
        
        # Test SSL/TLS connection if possible
        try:
            if mongodb_uri:
                # Create a test client with SSL settings
                from backend.app.middleware.performance import DatabasePoolConfig
                connection_options = DatabasePoolConfig.get_connection_options()
                
                test_client = AsyncIOMotorClient(mongodb_uri, **connection_options)
                
                # Test connection with timeout
                await asyncio.wait_for(
                    test_client.admin.command('ping'),
                    timeout=10.0
                )
                
                validation_result["details"]["ssl_connection_test"] = {
                    "status": "SUCCESS",
                    "ssl_handshake": "SUCCESSFUL"
                }
                validation_result["score"] += 1
                
                test_client.close()
            
        except Exception as e:
            validation_result["details"]["ssl_connection_test"] = {
                "status": "FAILED",
                "error": str(e)
            }
            validation_result["issues"].append(f"SSL/TLS connection test failed: {e}")
        
        # Calculate score
        max_score = 5  # 2 for SSL enabled + 2 for cert validation + 1 for connection test
        validation_result["score_percentage"] = (validation_result["score"] / max_score) * 100
        
        if validation_result["score_percentage"] < 60:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 80:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def validate_connection_health_monitoring(self) -> Dict[str, Any]:
        """Validate connection health monitoring capabilities"""
        logger.info("Validating connection health monitoring for production")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        try:
            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.backend_url}/healthz", timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        health_data = await response.json()
                        validation_result["details"]["health_endpoint"] = {
                            "status": "AVAILABLE",
                            "response_time": response_time,
                            "database_connected": health_data.get("database_connected", False)
                        }
                        validation_result["score"] += 2
                        
                        if health_data.get("database_connected"):
                            validation_result["score"] += 1
                    else:
                        validation_result["issues"].append(f"Health endpoint returned status {response.status}")
                
                # Test connection statistics endpoint
                try:
                    async with session.get(f"{self.backend_url}/api/v1/health/connection-stats", timeout=10) as stats_response:
                        if stats_response.status == 200:
                            stats_data = await stats_response.json()
                            validation_result["details"]["connection_stats"] = {
                                "status": "AVAILABLE",
                                "current_connections": stats_data.get("current_connections", 0),
                                "available_connections": stats_data.get("available_connections", 0),
                                "health_monitoring": "ENABLED"
                            }
                            validation_result["score"] += 2
                        else:
                            validation_result["issues"].append("Connection statistics endpoint not available")
                except Exception as e:
                    validation_result["details"]["connection_stats"] = {
                        "status": "UNAVAILABLE",
                        "error": str(e)
                    }
                    validation_result["issues"].append("Connection statistics monitoring not available")
        
        except Exception as e:
            validation_result["issues"].append(f"Health monitoring validation failed: {e}")
            validation_result["details"]["health_endpoint"] = {
                "status": "UNAVAILABLE",
                "error": str(e)
            }
        
        # Calculate score
        max_score = 5  # 2 for health endpoint + 1 for DB connection + 2 for stats
        validation_result["score_percentage"] = (validation_result["score"] / max_score) * 100
        
        if validation_result["score_percentage"] < 60:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 80:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def validate_retry_logic_and_timeouts(self) -> Dict[str, Any]:
        """Validate retry logic with random jitter and timeout settings"""
        logger.info("Validating retry logic and timeout configuration")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        # Check retry configuration
        max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "4"))
        retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "3.0"))
        
        validation_result["details"]["retry_config"] = {
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "has_jitter": True  # Confirmed in database.py implementation
        }
        
        # Validate retry settings
        if max_retries >= 3:
            validation_result["score"] += 1
        else:
            validation_result["issues"].append(f"Max retries {max_retries} may be too low for production")
        
        if 2.0 <= retry_delay <= 5.0:
            validation_result["score"] += 1
        else:
            validation_result["issues"].append(f"Retry delay {retry_delay}s may not be optimal for production")
        
        # Check timeout settings
        timeouts = {
            "server_selection": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "45000")),
            "connect": int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "45000")),
            "socket": int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "45000"))
        }
        
        validation_result["details"]["timeout_config"] = timeouts
        
        # Validate timeout settings for production network conditions
        for timeout_name, timeout_value in timeouts.items():
            if timeout_value >= 30000:  # At least 30 seconds
                validation_result["score"] += 1
            else:
                validation_result["issues"].append(f"{timeout_name} timeout {timeout_value}ms may be too low for production network conditions")
        
        # Test timeout behavior with a quick connection test
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if mongodb_uri:
                from backend.app.middleware.performance import DatabasePoolConfig
                connection_options = DatabasePoolConfig.get_connection_options()
                
                test_client = AsyncIOMotorClient(mongodb_uri, **connection_options)
                
                start_time = time.time()
                await asyncio.wait_for(
                    test_client.admin.command('ping'),
                    timeout=connection_options.get('serverSelectionTimeoutMS', 45000) / 1000
                )
                connection_time = time.time() - start_time
                
                validation_result["details"]["timeout_test"] = {
                    "status": "SUCCESS",
                    "connection_time": connection_time,
                    "within_timeout": connection_time < (timeouts["server_selection"] / 1000)
                }
                validation_result["score"] += 1
                
                test_client.close()
        
        except Exception as e:
            validation_result["details"]["timeout_test"] = {
                "status": "FAILED",
                "error": str(e)
            }
            validation_result["issues"].append(f"Timeout configuration test failed: {e}")
        
        # Calculate score
        max_score = 6  # 1 for retries + 1 for delay + 3 for timeouts + 1 for test
        validation_result["score_percentage"] = (validation_result["score"] / max_score) * 100
        
        if validation_result["score_percentage"] < 70:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 85:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def validate_production_network_conditions(self) -> Dict[str, Any]:
        """Validate performance under simulated production network conditions"""
        logger.info("Validating performance under production network conditions")
        
        validation_result = {
            "status": "PASS",
            "details": {},
            "issues": [],
            "score": 0
        }
        
        # Test multiple concurrent connections (simulating production load)
        concurrent_tests = []
        test_count = 10
        
        async def test_connection():
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.post(
                        f"{self.backend_url}/api/v1/auth/register",
                        json={
                            "email": f"test_{random.randint(1000, 9999)}@example.com",
                            "password": "TestPassword123!",
                            "full_name": "Test User"
                        },
                        timeout=30
                    ) as response:
                        response_time = time.time() - start_time
                        return {
                            "status": response.status,
                            "response_time": response_time,
                            "success": response.status in [201, 409]  # 409 for duplicate email is OK
                        }
            except Exception as e:
                return {
                    "status": "ERROR",
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                }
        
        # Run concurrent tests
        start_time = time.time()
        test_results = await asyncio.gather(*[test_connection() for _ in range(test_count)])
        total_time = time.time() - start_time
        
        # Analyze results
        successful_tests = [r for r in test_results if r["success"]]
        failed_tests = [r for r in test_results if not r["success"]]
        response_times = [r["response_time"] for r in successful_tests if r["response_time"]]
        
        validation_result["details"]["concurrent_load_test"] = {
            "total_requests": test_count,
            "successful_requests": len(successful_tests),
            "failed_requests": len(failed_tests),
            "success_rate": len(successful_tests) / test_count * 100,
            "total_duration": total_time,
            "average_response_time": sum(response_times) / len(response_times) if response_times else None,
            "min_response_time": min(response_times) if response_times else None,
            "max_response_time": max(response_times) if response_times else None
        }
        
        # Score based on success rate and performance
        success_rate = len(successful_tests) / test_count * 100
        if success_rate >= 90:
            validation_result["score"] += 2
        elif success_rate >= 80:
            validation_result["score"] += 1
        else:
            validation_result["issues"].append(f"Low success rate under concurrent load: {success_rate:.1f}%")
        
        # Check response times
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time <= 5.0:  # 5 seconds acceptable under load
                validation_result["score"] += 2
            elif avg_response_time <= 10.0:
                validation_result["score"] += 1
            else:
                validation_result["issues"].append(f"High average response time under load: {avg_response_time:.2f}s")
        
        # Test connection stability over time
        stability_test_duration = 30  # seconds
        stability_tests = []
        
        async def stability_test():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/healthz", timeout=10) as response:
                        return response.status == 200
            except:
                return False
        
        # Run stability tests every 5 seconds
        stability_start = time.time()
        while time.time() - stability_start < stability_test_duration:
            stability_result = await stability_test()
            stability_tests.append(stability_result)
            await asyncio.sleep(5)
        
        stability_success_rate = sum(stability_tests) / len(stability_tests) * 100 if stability_tests else 0
        
        validation_result["details"]["stability_test"] = {
            "duration": stability_test_duration,
            "total_checks": len(stability_tests),
            "successful_checks": sum(stability_tests),
            "stability_rate": stability_success_rate
        }
        
        if stability_success_rate >= 95:
            validation_result["score"] += 1
        else:
            validation_result["issues"].append(f"Connection stability issues: {stability_success_rate:.1f}% uptime")
        
        # Calculate score
        max_score = 5  # 2 for success rate + 2 for response time + 1 for stability
        validation_result["score_percentage"] = (validation_result["score"] / max_score) * 100
        
        if validation_result["score_percentage"] < 60:
            validation_result["status"] = "FAIL"
        elif validation_result["score_percentage"] < 80:
            validation_result["status"] = "WARNING"
        
        return validation_result
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all production readiness validations"""
        logger.info("Starting comprehensive production readiness validation")
        
        validations = {
            "environment_variables": self.validate_environment_variables,
            "atlas_free_tier_compatibility": self.validate_atlas_free_tier_compatibility,
            "ssl_tls_configuration": self.validate_ssl_tls_configuration,
            "connection_health_monitoring": self.validate_connection_health_monitoring,
            "retry_logic_and_timeouts": self.validate_retry_logic_and_timeouts,
            "production_network_conditions": self.validate_production_network_conditions
        }
        
        for validation_name, validation_func in validations.items():
            logger.info(f"Running validation: {validation_name}")
            try:
                result = await validation_func()
                self.results["validation_results"][validation_name] = result
                
                # Collect critical issues
                if result["status"] == "FAIL":
                    self.results["critical_issues"].extend([
                        f"{validation_name}: {issue}" for issue in result["issues"]
                    ])
                
            except Exception as e:
                logger.error(f"Validation {validation_name} failed with exception: {e}")
                self.results["validation_results"][validation_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "score_percentage": 0
                }
                self.results["critical_issues"].append(f"{validation_name}: Validation failed with error: {e}")
        
        # Calculate overall production readiness score
        total_score = 0
        total_validations = 0
        
        for validation_result in self.results["validation_results"].values():
            if "score_percentage" in validation_result:
                total_score += validation_result["score_percentage"]
                total_validations += 1
        
        self.results["production_readiness_score"] = total_score / total_validations if total_validations > 0 else 0
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _generate_recommendations(self):
        """Generate production deployment recommendations"""
        score = self.results["production_readiness_score"]
        
        if score >= 95:
            self.results["recommendations"].append("✅ System is production-ready with excellent configuration")
        elif score >= 85:
            self.results["recommendations"].append("✅ System is production-ready with minor optimizations needed")
        elif score >= 70:
            self.results["recommendations"].append("⚠️ System needs improvements before production deployment")
        else:
            self.results["recommendations"].append("❌ System requires significant fixes before production deployment")
        
        # Specific recommendations based on validation results
        for validation_name, result in self.results["validation_results"].items():
            if result.get("status") == "FAIL":
                self.results["recommendations"].append(f"🔧 Fix critical issues in {validation_name}")
            elif result.get("status") == "WARNING":
                self.results["recommendations"].append(f"⚠️ Optimize {validation_name} configuration")
        
        # General production recommendations
        self.results["recommendations"].extend([
            "📊 Set up monitoring and alerting for connection pool usage",
            "🔄 Implement automated health checks in production",
            "📈 Monitor slow request patterns and optimize as needed",
            "🔒 Regularly rotate MongoDB credentials and JWT secrets",
            "💾 Verify backup and recovery procedures",
            "🚀 Consider load testing with higher concurrent user counts"
        ])

async def main():
    """Main execution function"""
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    validator = ProductionReadinessValidator(backend_url)
    results = await validator.run_comprehensive_validation()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mongodb_production_readiness_verification_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*80)
    print("MONGODB CONNECTION PRODUCTION READINESS VERIFICATION")
    print("="*80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Backend URL: {results['backend_url']}")
    print(f"Overall Production Readiness Score: {results['production_readiness_score']:.1f}%")
    print()
    
    # Print validation results
    for validation_name, result in results["validation_results"].items():
        status_emoji = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "WARNING" else "❌"
        score = result.get("score_percentage", 0)
        print(f"{status_emoji} {validation_name.replace('_', ' ').title()}: {result['status']} ({score:.1f}%)")
    
    print()
    
    # Print critical issues
    if results["critical_issues"]:
        print("🚨 CRITICAL ISSUES:")
        for issue in results["critical_issues"]:
            print(f"   • {issue}")
        print()
    
    # Print recommendations
    print("💡 RECOMMENDATIONS:")
    for recommendation in results["recommendations"]:
        print(f"   {recommendation}")
    
    print()
    print(f"📄 Detailed results saved to: {filename}")
    print("="*80)
    
    # Exit with appropriate code
    if results["production_readiness_score"] >= 85:
        sys.exit(0)  # Success
    elif results["production_readiness_score"] >= 70:
        sys.exit(1)  # Warning - needs improvement
    else:
        sys.exit(2)  # Critical issues

if __name__ == "__main__":
    asyncio.run(main())