#!/usr/bin/env python3
"""
Comprehensive MongoDB SSL/TLS Connection Diagnosis Script
"""

import os
import sys
import asyncio
import ssl
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

async def diagnose_mongodb_ssl():
    """Comprehensive MongoDB SSL/TLS diagnosis"""
    
    print("=" * 60)
    print("MONGODB SSL/TLS CONNECTION DIAGNOSIS")
    print("=" * 60)
    
    # 1. Environment Variables Check
    print("\n1. ENVIRONMENT VARIABLES CHECK")
    print("-" * 40)
    
    # Try loading from backend/.env
    backend_env_path = Path(__file__).parent / "backend" / ".env"
    if backend_env_path.exists():
        print(f"✓ Found .env file at: {backend_env_path}")
        
        # Load environment variables manually
        env_vars = {}
        with open(backend_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        # Check MongoDB SSL/TLS variables
        ssl_vars = [
            'MONGODB_URI',
            'MONGODB_TLS_ENABLED',
            'MONGODB_TLS_ALLOW_INVALID_CERTIFICATES',
            'MONGODB_SERVER_SELECTION_TIMEOUT_MS',
            'MONGODB_CONNECT_TIMEOUT_MS',
            'MONGODB_SOCKET_TIMEOUT_MS'
        ]
        
        for var in ssl_vars:
            value = env_vars.get(var, "NOT SET")
            status = "✓" if value != "NOT SET" else "✗"
            print(f"{status} {var}: {value}")
    else:
        print(f"✗ No .env file found at: {backend_env_path}")
    
    # 2. Python SSL Configuration
    print("\n2. PYTHON SSL CONFIGURATION")
    print("-" * 40)
    print(f"✓ OpenSSL Version: {ssl.OPENSSL_VERSION}")
    print(f"✓ Python SSL Module: {ssl}")
    
    # Check SSL context defaults
    try:
        context = ssl.create_default_context()
        print(f"✓ Default SSL Context: {context}")
        print(f"✓ SSL Context Protocol: {context.protocol}")
        print(f"✓ SSL Context Options: {context.options}")
        print(f"✓ SSL Context Verify Mode: {context.verify_mode}")
    except Exception as e:
        print(f"✗ SSL Context Error: {e}")
    
    # 3. MongoDB Driver Versions
    print("\n3. MONGODB DRIVER VERSIONS")
    print("-" * 40)
    try:
        import pymongo
        print(f"✓ PyMongo Version: {pymongo.version}")
    except ImportError as e:
        print(f"✗ PyMongo Import Error: {e}")
    
    try:
        import motor
        print(f"✓ Motor Version: {motor.version}")
    except ImportError as e:
        print(f"✗ Motor Import Error: {e}")
    
    # 4. Connection Configuration Test
    print("\n4. CONNECTION CONFIGURATION TEST")
    print("-" * 40)
    
    try:
        # Try to import and test DatabasePoolConfig
        from app.middleware.performance import DatabasePoolConfig
        
        # Set environment variables for testing
        os.environ.update(env_vars)
        
        options = DatabasePoolConfig.get_connection_options()
        print("✓ DatabasePoolConfig.get_connection_options():")
        for key, value in options.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"✗ DatabasePoolConfig Error: {e}")
    
    # 5. MongoDB Connection Test
    print("\n5. MONGODB CONNECTION TEST")
    print("-" * 40)
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        # Get MongoDB URI from env vars
        mongodb_uri = env_vars.get('MONGODB_URI')
        if not mongodb_uri:
            print("✗ MONGODB_URI not found in environment variables")
            return
        
        print(f"✓ MongoDB URI: {mongodb_uri[:50]}...")
        
        # Test connection with current configuration
        options = DatabasePoolConfig.get_connection_options()
        
        print("✓ Testing connection with SSL/TLS options...")
        client = AsyncIOMotorClient(mongodb_uri, **options)
        
        # Test ping with timeout
        await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
        print("✓ MongoDB connection successful!")
        
        # Get server info
        server_info = await client.server_info()
        print(f"✓ MongoDB Server Version: {server_info.get('version', 'Unknown')}")
        
        client.close()
        
    except asyncio.TimeoutError:
        print("✗ MongoDB connection timeout - SSL handshake may be failing")
    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")
        if "SSL" in str(e) or "TLS" in str(e):
            print("  → This appears to be an SSL/TLS related error")
    
    # 6. Network Connectivity Test
    print("\n6. NETWORK CONNECTIVITY TEST")
    print("-" * 40)
    
    try:
        import socket
        
        # Extract hostname from MongoDB URI
        if mongodb_uri and "mongodb+srv://" in mongodb_uri:
            # Parse hostname from URI
            uri_parts = mongodb_uri.split("@")[1].split("/")[0]
            hostname = uri_parts.split("?")[0]
            
            print(f"✓ Testing connectivity to: {hostname}")
            
            # Test DNS resolution
            try:
                ip = socket.gethostbyname(hostname)
                print(f"✓ DNS Resolution: {hostname} → {ip}")
            except Exception as e:
                print(f"✗ DNS Resolution Error: {e}")
            
            # Test TCP connection
            try:
                sock = socket.create_connection((hostname, 27017), timeout=5)
                sock.close()
                print("✓ TCP Connection: Port 27017 is reachable")
            except Exception as e:
                print(f"✗ TCP Connection Error: {e}")
                
    except Exception as e:
        print(f"✗ Network test error: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(diagnose_mongodb_ssl())