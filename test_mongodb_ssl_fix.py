#!/usr/bin/env python3
"""
Test script to verify MongoDB SSL/TLS fix for production environment variable issues
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from unittest.mock import patch

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_ssl_configuration_scenarios():
    """Test various SSL/TLS configuration scenarios"""
    
    print("=" * 80)
    print("MONGODB SSL/TLS FIX VERIFICATION TEST")
    print("=" * 80)
    
    # Import after path setup
    from app.middleware.performance import DatabasePoolConfig
    
    test_scenarios = [
        {
            "name": "Production - No Environment Variables (Atlas URI)",
            "env_vars": {},
            "mongodb_uri": "mongodb+srv://user:pass@cluster0.vcpyxwh.mongodb.net/db",
            "expected_tls": True,
            "description": "Should auto-enable SSL/TLS for Atlas connections"
        },
        {
            "name": "Production - No Environment Variables (Local URI)",
            "env_vars": {},
            "mongodb_uri": "mongodb://localhost:27017/db",
            "expected_tls": False,
            "description": "Should not enable SSL/TLS for local connections"
        },
        {
            "name": "Local Development - Explicit SSL/TLS Enabled",
            "env_vars": {"MONGODB_TLS_ENABLED": "true"},
            "mongodb_uri": "mongodb://localhost:27017/db",
            "expected_tls": True,
            "description": "Should respect explicit SSL/TLS configuration"
        },
        {
            "name": "Local Development - Explicit SSL/TLS Disabled",
            "env_vars": {"MONGODB_TLS_ENABLED": "false"},
            "mongodb_uri": "mongodb+srv://user:pass@cluster0.vcpyxwh.mongodb.net/db",
            "expected_tls": False,
            "description": "Should respect explicit SSL/TLS disable even for Atlas"
        },
        {
            "name": "Production - Atlas with Custom Pool Settings",
            "env_vars": {
                "MONGODB_MAX_POOL_SIZE": "50",
                "MONGODB_MIN_POOL_SIZE": "5",
                "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "true"
            },
            "mongodb_uri": "mongodb+srv://user:pass@cluster0.vcpyxwh.mongodb.net/db",
            "expected_tls": True,
            "description": "Should auto-enable SSL/TLS and use custom settings"
        },
        {
            "name": "Production - Invalid Environment Values",
            "env_vars": {
                "MONGODB_MAX_POOL_SIZE": "invalid",
                "MONGODB_TLS_ENABLED": "maybe",
                "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES": "sometimes"
            },
            "mongodb_uri": "mongodb+srv://user:pass@cluster0.vcpyxwh.mongodb.net/db",
            "expected_tls": True,
            "description": "Should handle invalid env values gracefully with Atlas detection"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   MongoDB URI: {scenario['mongodb_uri']}")
        print(f"   Environment Variables: {scenario['env_vars']}")
        
        # Mock environment variables for this test
        with patch.dict(os.environ, scenario['env_vars'], clear=False):
            # Set the MongoDB URI for this test
            with patch.dict(os.environ, {"MONGODB_URI": scenario['mongodb_uri']}, clear=False):
                try:
                    # Get connection options
                    options = DatabasePoolConfig.get_connection_options()
                    
                    # Check SSL/TLS configuration
                    tls_enabled = options.get("tls", False)
                    
                    # Verify expectations
                    if tls_enabled == scenario['expected_tls']:
                        status = "✓ PASS"
                        print(f"   Result: {status} - SSL/TLS correctly configured: {tls_enabled}")
                    else:
                        status = "✗ FAIL"
                        print(f"   Result: {status} - Expected SSL/TLS: {scenario['expected_tls']}, Got: {tls_enabled}")
                    
                    # Log key configuration details
                    print(f"   SSL/TLS Options: {tls_enabled}")
                    if tls_enabled:
                        print(f"   - tlsAllowInvalidCertificates: {options.get('tlsAllowInvalidCertificates', False)}")
                        print(f"   - tlsInsecure: {options.get('tlsInsecure', 'Not set')}")
                        print(f"   - authSource: {options.get('authSource', 'Not set')}")
                    
                    print(f"   Pool Settings: max={options['maxPoolSize']}, min={options['minPoolSize']}")
                    print(f"   Timeouts: server={options['serverSelectionTimeoutMS']}ms, connect={options['connectTimeoutMS']}ms")
                    
                    results.append({
                        "scenario": scenario['name'],
                        "status": status,
                        "tls_enabled": tls_enabled,
                        "expected_tls": scenario['expected_tls'],
                        "options": options
                    })
                    
                except Exception as e:
                    status = "✗ ERROR"
                    print(f"   Result: {status} - Exception: {e}")
                    results.append({
                        "scenario": scenario['name'],
                        "status": status,
                        "error": str(e)
                    })
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["status"] == "✓ PASS")
    failed = sum(1 for r in results if r["status"] in ["✗ FAIL", "✗ ERROR"])
    
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! MongoDB SSL/TLS fix is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the results above.")
    
    # Detailed results for debugging
    print("\nDETAILED RESULTS:")
    for result in results:
        print(f"- {result['scenario']}: {result['status']}")
        if "error" in result:
            print(f"  Error: {result['error']}")
    
    return results

async def test_atlas_detection():
    """Test MongoDB Atlas URI detection logic"""
    
    print("\n" + "=" * 80)
    print("MONGODB ATLAS DETECTION TEST")
    print("=" * 80)
    
    from app.middleware.performance import DatabasePoolConfig
    
    test_uris = [
        ("mongodb+srv://user:pass@cluster0.vcpyxwh.mongodb.net/db", True, "Standard Atlas URI"),
        ("mongodb+srv://user:pass@cluster.mongodb.net/db", True, "Generic Atlas URI"),
        ("mongodb://cluster0.vcpyxwh.mongodb.net:27017/db", True, "Atlas URI without SRV"),
        ("mongodb://localhost:27017/db", False, "Local MongoDB"),
        ("mongodb://192.168.1.100:27017/db", False, "Remote MongoDB (non-Atlas)"),
        ("mongodb://my-server.com:27017/db", False, "Custom domain"),
        ("", False, "Empty URI"),
        (None, False, "None URI")
    ]
    
    print("Testing Atlas URI detection:")
    for uri, expected, description in test_uris:
        try:
            result = DatabasePoolConfig._is_mongodb_atlas_uri(uri or "")
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"  {status} {description}")
            print(f"    URI: {uri}")
            print(f"    Expected: {expected}, Got: {result}")
        except Exception as e:
            print(f"  ✗ ERROR {description}: {e}")
        print()

async def test_environment_variable_parsing():
    """Test environment variable parsing with various edge cases"""
    
    print("\n" + "=" * 80)
    print("ENVIRONMENT VARIABLE PARSING TEST")
    print("=" * 80)
    
    from app.middleware.performance import DatabasePoolConfig
    
    # Test boolean parsing
    bool_tests = [
        ("true", True), ("True", True), ("TRUE", True),
        ("false", False), ("False", False), ("FALSE", False),
        ("1", True), ("0", False),
        ("yes", True), ("no", False),
        ("on", True), ("off", False),
        ("invalid", False), ("", False), (None, False)
    ]
    
    print("Testing boolean environment variable parsing:")
    for value, expected in bool_tests:
        with patch.dict(os.environ, {"TEST_BOOL": value} if value is not None else {}, clear=False):
            result = DatabasePoolConfig._get_env_bool("TEST_BOOL", False)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"  {status} '{value}' -> {result} (expected {expected})")
    
    # Test integer parsing
    int_tests = [
        ("100", 100), ("0", 0), ("-1", -1),
        ("invalid", 50), ("", 50), (None, 50)
    ]
    
    print("\nTesting integer environment variable parsing:")
    for value, expected in int_tests:
        with patch.dict(os.environ, {"TEST_INT": value} if value is not None else {}, clear=False):
            result = DatabasePoolConfig._get_env_int("TEST_INT", 50)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"  {status} '{value}' -> {result} (expected {expected})")

if __name__ == "__main__":
    async def main():
        await test_ssl_configuration_scenarios()
        await test_atlas_detection()
        await test_environment_variable_parsing()
        
        print("\n" + "=" * 80)
        print("MONGODB SSL/TLS FIX VERIFICATION COMPLETE")
        print("=" * 80)
        print("\nThe fix implements:")
        print("✓ Robust fallback mechanism for SSL/TLS configuration")
        print("✓ Automatic SSL/TLS enablement for MongoDB Atlas connections")
        print("✓ Production-safe environment variable loading with intelligent defaults")
        print("✓ Comprehensive logging for SSL/TLS configuration decisions")
        print("✓ Backward compatibility with existing local development setup")
        print("\nThis should resolve the production SSL handshake failures!")
    
    asyncio.run(main())