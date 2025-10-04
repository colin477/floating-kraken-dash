#!/usr/bin/env python3
"""
MongoDB SSL/TLS Connection Diagnosis Script
Identifies specific SSL/TLS handshake issues with MongoDB Atlas
"""

import os
import asyncio
import ssl
import socket
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MongoDB connection details
MONGODB_URI = "mongodb+srv://colin_db_user:FnaPFUQh6aAjhfiR@cluster0.vcpyxwh.mongodb.net/ez_eatin?retryWrites=true&w=majority&appName=Cluster0"
REPLICA_SET_HOSTS = [
    "ac-86ptaq4-shard-00-00.vcpyxwh.mongodb.net",
    "ac-86ptaq4-shard-00-01.vcpyxwh.mongodb.net", 
    "ac-86ptaq4-shard-00-02.vcpyxwh.mongodb.net"
]

def print_environment_info():
    """Print current environment information"""
    print("=== ENVIRONMENT DIAGNOSIS ===")
    print(f"Python Version: {os.sys.version}")
    print(f"OpenSSL Version: {ssl.OPENSSL_VERSION}")
    
    try:
        import pymongo
        print(f"PyMongo Version: {pymongo.version}")
    except ImportError:
        print("PyMongo: Not available")
    
    try:
        import motor
        print(f"Motor Version: {motor.version}")
    except ImportError:
        print("Motor: Not available")
    
    print(f"SSL Default Context Protocol: {ssl.create_default_context().protocol}")
    print(f"SSL Supported Protocols: {ssl.get_default_verify_paths()}")
    print()

def test_basic_ssl_connectivity():
    """Test basic SSL connectivity to MongoDB Atlas hosts"""
    print("=== BASIC SSL CONNECTIVITY TEST ===")
    
    for host in REPLICA_SET_HOSTS:
        print(f"Testing SSL connection to {host}:27017...")
        try:
            # Test basic TCP connection
            start_time = time.time()
            sock = socket.create_connection((host, 27017), timeout=10)
            tcp_time = time.time() - start_time
            print(f"  ✓ TCP connection successful ({tcp_time:.2f}s)")
            
            # Test SSL handshake
            start_time = time.time()
            context = ssl.create_default_context()
            ssl_sock = context.wrap_socket(sock, server_hostname=host)
            ssl_time = time.time() - start_time
            print(f"  ✓ SSL handshake successful ({ssl_time:.2f}s)")
            print(f"  SSL Version: {ssl_sock.version()}")
            print(f"  Cipher: {ssl_sock.cipher()}")
            
            ssl_sock.close()
            
        except socket.timeout:
            print(f"  ✗ Connection timeout to {host}")
        except ssl.SSLError as e:
            print(f"  ✗ SSL Error: {e}")
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
        print()

async def test_motor_connections():
    """Test various Motor connection configurations"""
    print("=== MOTOR CONNECTION TESTS ===")
    
    # Test 1: Basic connection (current failing case)
    print("Test 1: Basic Motor connection with short timeout")
    try:
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("  ✓ Basic connection successful")
        client.close()
    except Exception as e:
        print(f"  ✗ Basic connection failed: {e}")
        print(f"  Error type: {type(e).__name__}")
    
    # Test 2: Connection with extended timeouts
    print("\nTest 2: Motor connection with extended timeouts")
    try:
        client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        await client.admin.command('ping')
        print("  ✓ Extended timeout connection successful")
        client.close()
    except Exception as e:
        print(f"  ✗ Extended timeout connection failed: {e}")
        print(f"  Error type: {type(e).__name__}")
    
    # Test 3: Connection with TLS options (Motor 3.2.0 syntax)
    print("\nTest 3: Motor connection with TLS options")
    try:
        client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        await client.admin.command('ping')
        print("  ✓ TLS connection successful")
        client.close()
    except Exception as e:
        print(f"  ✗ TLS connection failed: {e}")
        print(f"  Error type: {type(e).__name__}")
    
    # Test 4: Connection with TLS and additional options
    print("\nTest 4: Motor connection with comprehensive TLS options")
    try:
        client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsInsecure=True,
            maxPoolSize=10,
            minPoolSize=1
        )
        await client.admin.command('ping')
        print("  ✓ Comprehensive TLS connection successful")
        client.close()
    except Exception as e:
        print(f"  ✗ Comprehensive TLS connection failed: {e}")
        print(f"  Error type: {type(e).__name__}")

def analyze_version_compatibility():
    """Analyze version compatibility issues"""
    print("=== VERSION COMPATIBILITY ANALYSIS ===")
    
    # Current versions
    current_versions = {
        "Python": "3.13.3",
        "OpenSSL": "3.0.16", 
        "PyMongo": "4.5.0",
        "Motor": "3.2.0"
    }
    
    # Documented working versions
    documented_versions = {
        "Python": "3.13",
        "OpenSSL": "3.0.16",
        "PyMongo": "4.6.0", 
        "Motor": "3.3.2"
    }
    
    print("Current vs Documented Working Versions:")
    for component, current in current_versions.items():
        documented = documented_versions.get(component, "N/A")
        status = "✓" if current == documented else "⚠" if documented == "N/A" else "✗"
        print(f"  {status} {component}: {current} (documented: {documented})")
    
    print("\nCompatibility Issues Identified:")
    if current_versions["PyMongo"] != documented_versions["PyMongo"]:
        print(f"  ⚠ PyMongo version mismatch: {current_versions['PyMongo']} vs {documented_versions['PyMongo']}")
        print("    - PyMongo 4.5.0 may have different SSL/TLS handling than 4.6.0")
        print("    - SSL parameter names may have changed between versions")
    
    if current_versions["Motor"] != documented_versions["Motor"]:
        print(f"  ⚠ Motor version mismatch: {current_versions['Motor']} vs {documented_versions['Motor']}")
        print("    - Motor 3.2.0 may have different SSL/TLS API than 3.3.2")
        print("    - SSL context handling may be different")
    
    print()

def analyze_database_implementation():
    """Analyze current database.py implementation vs documented fixes"""
    print("=== DATABASE IMPLEMENTATION ANALYSIS ===")
    
    print("Current database.py configuration:")
    print("  - Uses hardcoded TLS settings: tls=True, tlsAllowInvalidCertificates=True")
    print("  - Does NOT use environment variables for SSL/TLS configuration")
    print("  - Does NOT use extended timeout values from environment")
    print("  - Missing serverSelectionTimeoutMS, connectTimeoutMS, socketTimeoutMS")
    
    print("\nDocumented fixes that are NOT implemented:")
    print("  ✗ Environment variable-based SSL/TLS configuration")
    print("  ✗ Extended timeout values (30000ms)")
    print("  ✗ Conditional TLS configuration based on MONGODB_TLS_ENABLED")
    print("  ✗ SSL-specific error handling and logging")
    
    print("\nEnvironment variables defined but not used:")
    env_vars = [
        "MONGODB_TLS_ENABLED",
        "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", 
        "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
        "MONGODB_CONNECT_TIMEOUT_MS",
        "MONGODB_SOCKET_TIMEOUT_MS"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        print(f"  - {var}={value}")
    
    print()

async def main():
    """Run comprehensive MongoDB SSL/TLS diagnosis"""
    print("MongoDB SSL/TLS Connection Diagnosis")
    print("=" * 50)
    print()
    
    # Step 1: Environment information
    print_environment_info()
    
    # Step 2: Version compatibility analysis
    analyze_version_compatibility()
    
    # Step 3: Database implementation analysis
    analyze_database_implementation()
    
    # Step 4: Basic SSL connectivity test
    test_basic_ssl_connectivity()
    
    # Step 5: Motor connection tests
    await test_motor_connections()
    
    print("=== DIAGNOSIS COMPLETE ===")
    print("Check the output above for specific SSL/TLS issues and recommendations.")

if __name__ == "__main__":
    asyncio.run(main())