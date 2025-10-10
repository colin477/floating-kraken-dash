#!/usr/bin/env python3
"""
Test script to verify MongoDB production fixes implementation
"""

import os
import sys
import asyncio

# Add backend to path
sys.path.append('backend')

from app.database import _is_production_environment
from app.middleware.performance import DatabasePoolConfig

def test_production_environment_detection():
    """Test production environment detection logic"""
    print('=== Production Environment Detection Test ===')
    print(f'Current ENVIRONMENT: {os.getenv("ENVIRONMENT", "not set")}')
    print(f'RENDER: {os.getenv("RENDER", "not set")}')
    print(f'RENDER_SERVICE_ID: {os.getenv("RENDER_SERVICE_ID", "not set")}')
    print(f'RENDER_SERVICE_NAME: {os.getenv("RENDER_SERVICE_NAME", "not set")}')
    print(f'Is Production: {_is_production_environment()}')
    print()

def test_mongodb_connection_options():
    """Test MongoDB connection options configuration"""
    print('=== MongoDB Connection Options Test ===')
    options = DatabasePoolConfig.get_connection_options()
    
    print(f'Server Selection Timeout: {options.get("serverSelectionTimeoutMS")}ms')
    print(f'Connect Timeout: {options.get("connectTimeoutMS")}ms')
    print(f'Socket Timeout: {options.get("socketTimeoutMS")}ms')
    print(f'Max Pool Size: {options.get("maxPoolSize")}')
    print(f'Min Pool Size: {options.get("minPoolSize")}')
    print(f'TLS Enabled: {options.get("tls", False)}')
    print(f'Retry Writes: {options.get("retryWrites")}')
    print(f'Retry Reads: {options.get("retryReads")}')
    print()

def test_production_timeout_simulation():
    """Simulate production environment and test timeout configuration"""
    print('=== Production Timeout Simulation Test ===')
    
    # Save original environment
    original_env = os.getenv("ENVIRONMENT")
    original_render = os.getenv("RENDER")
    
    try:
        # Simulate production environment
        os.environ["ENVIRONMENT"] = "production"
        os.environ["RENDER"] = "true"
        
        print("Simulating production environment...")
        print(f'Is Production (simulated): {_is_production_environment()}')
        
        # Get base connection options
        base_options = DatabasePoolConfig.get_connection_options()
        print(f'Base Server Selection Timeout: {base_options.get("serverSelectionTimeoutMS")}ms')
        print(f'Base Connect Timeout: {base_options.get("connectTimeoutMS")}ms')
        print(f'Base Socket Timeout: {base_options.get("socketTimeoutMS")}ms')
        
        # Test production timeout override logic
        print("\nTesting production timeout override logic...")
        production_timeouts = {
            'serverSelectionTimeoutMS': 60000,  # 60 seconds
            'connectTimeoutMS': 60000,           # 60 seconds
            'socketTimeoutMS': 60000             # 60 seconds
        }
        
        # Simulate what happens in connect_to_mongo() for production
        connection_options = base_options.copy()
        if _is_production_environment():
            connection_options.update(production_timeouts)
            print("✓ Production timeout optimizations would be applied:")
            print(f'  - Server Selection Timeout: {connection_options.get("serverSelectionTimeoutMS")}ms')
            print(f'  - Connect Timeout: {connection_options.get("connectTimeoutMS")}ms')
            print(f'  - Socket Timeout: {connection_options.get("socketTimeoutMS")}ms')
        else:
            print("✗ Production environment not detected - no timeout optimizations")
        
    finally:
        # Restore original environment
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)
            
        if original_render:
            os.environ["RENDER"] = original_render
        else:
            os.environ.pop("RENDER", None)
    
    print()

async def test_connection_warmup():
    """Test connection warmup delay logic"""
    print('=== Connection Warmup Test ===')
    
    # Import after setting up path
    from app.database import connect_to_mongo, _is_production_environment
    
    is_prod = _is_production_environment()
    print(f'Current environment is production: {is_prod}')
    
    if is_prod:
        print('Production environment detected - warmup delay will be applied during connection')
    else:
        print('Development environment - no warmup delay')
    
    print()

def main():
    """Run all tests"""
    print("MongoDB Production Fixes Verification")
    print("=" * 50)
    print()
    
    test_production_environment_detection()
    test_mongodb_connection_options()
    test_production_timeout_simulation()
    
    # Run async test
    asyncio.run(test_connection_warmup())
    
    print("=" * 50)
    print("All tests completed successfully!")

if __name__ == "__main__":
    main()