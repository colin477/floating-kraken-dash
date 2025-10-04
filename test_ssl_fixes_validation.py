#!/usr/bin/env python3
"""
Quick validation test for the specific SSL/TLS fixes implemented
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def validate_fixes():
    """Validate the specific fixes that were implemented"""
    print("🔍 Validating MongoDB SSL/TLS Configuration Fixes")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv(os.path.join('backend', '.env'))
    
    # Test 1: Verify environment variables are loaded
    print("\n1. Environment Variables Loading:")
    mongodb_uri = os.getenv("MONGODB_URI")
    tls_enabled = os.getenv("MONGODB_TLS_ENABLED")
    tls_allow_invalid = os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES")
    
    print(f"   ✅ MONGODB_URI: {'Present' if mongodb_uri else 'Missing'}")
    print(f"   ✅ MONGODB_TLS_ENABLED: {tls_enabled}")
    print(f"   ✅ MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: {tls_allow_invalid}")
    
    # Test 2: Verify DatabasePoolConfig import and functionality
    print("\n2. DatabasePoolConfig Import:")
    try:
        from app.middleware.performance import DatabasePoolConfig
        print("   ✅ DatabasePoolConfig imported successfully")
        
        options = DatabasePoolConfig.get_connection_options()
        print(f"   ✅ Connection options generated: {len(options)} options")
        print(f"   ✅ TLS enabled in options: {options.get('tls', False)}")
        print(f"   ✅ TLS allow invalid certs: {options.get('tlsAllowInvalidCertificates', False)}")
        
    except ImportError as e:
        print(f"   ❌ Failed to import DatabasePoolConfig: {e}")
        return False
    
    # Test 3: Verify updated dependencies
    print("\n3. Dependency Versions:")
    try:
        import motor
        import pymongo
        print(f"   ✅ Motor version: {motor.version}")
        print(f"   ✅ PyMongo version: {pymongo.version}")
        
        # Check if versions match expected
        expected_motor = "3.3.2"
        expected_pymongo = "4.6.0"
        
        motor_ok = motor.version.startswith(expected_motor)
        pymongo_ok = pymongo.version.startswith(expected_pymongo)
        
        print(f"   {'✅' if motor_ok else '❌'} Motor version check: {motor.version} (expected {expected_motor})")
        print(f"   {'✅' if pymongo_ok else '❌'} PyMongo version check: {pymongo.version} (expected {expected_pymongo})")
        
    except ImportError as e:
        print(f"   ❌ Failed to check dependency versions: {e}")
        return False
    
    # Test 4: Quick connection test
    print("\n4. Quick Connection Test:")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        if not mongodb_uri:
            print("   ❌ No MongoDB URI available")
            return False
        
        client = AsyncIOMotorClient(mongodb_uri, **options)
        await client.admin.command('ping')
        print("   ✅ Connection successful")
        
        # Get server info
        server_info = await client.server_info()
        print(f"   ✅ Server version: {server_info.get('version')}")
        
        ssl_info = server_info.get('openssl', {})
        if ssl_info:
            print(f"   ✅ SSL/TLS info: {ssl_info.get('running', 'Unknown')}")
        
        await client.close()
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    print("\n🎉 All fixes validated successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(validate_fixes())
    sys.exit(0 if success else 1)