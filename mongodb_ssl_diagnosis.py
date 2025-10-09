#!/usr/bin/env python3
"""
MongoDB SSL Connection Diagnostic Script
Analyzes SSL handshake failures with MongoDB Atlas
"""

import os
import sys
import ssl
import socket
import asyncio
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import structlog

# Setup logging
logger = structlog.get_logger(__name__)

class MongoDBSSLDiagnostic:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI", "")
        self.database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
    def analyze_pymongo_version(self):
        """Analyze PyMongo version compatibility"""
        try:
            import pymongo
            version = pymongo.version
            print(f"✓ PyMongo Version: {version}")
            
            # Check for known SSL issues
            if version.startswith("4.6"):
                print("⚠️  PyMongo 4.6.x has known SSL/TLS compatibility issues with some MongoDB Atlas configurations")
                print("   Recommendation: Consider upgrading to PyMongo 4.7+ or downgrading to 4.5.x")
            elif version.startswith("4.7") or version.startswith("4.8"):
                print("✓ PyMongo version appears compatible with MongoDB Atlas SSL/TLS")
            else:
                print(f"⚠️  PyMongo version {version} compatibility unknown - check MongoDB compatibility matrix")
                
        except ImportError:
            print("❌ PyMongo not installed")
            
    def analyze_connection_string(self):
        """Analyze MongoDB connection string format"""
        if not self.mongodb_uri:
            print("❌ MONGODB_URI environment variable not set")
            return False
            
        print(f"MongoDB URI: {self.mongodb_uri[:50]}...")
        
        # Parse URI
        try:
            parsed = urlparse(self.mongodb_uri)
            print(f"✓ Scheme: {parsed.scheme}")
            print(f"✓ Hostname: {parsed.hostname}")
            print(f"✓ Port: {parsed.port or 27017}")
            
            # Check for Atlas
            if ".mongodb.net" in parsed.hostname:
                print("✓ Detected MongoDB Atlas connection")
                return True
            else:
                print("⚠️  Not a MongoDB Atlas connection - SSL issues may be different")
                return False
                
        except Exception as e:
            print(f"❌ Error parsing MongoDB URI: {e}")
            return False
    
    def check_ssl_context(self):
        """Check system SSL context and capabilities"""
        print("\n=== SSL Context Analysis ===")
        
        try:
            # Check default SSL context
            context = ssl.create_default_context()
            print(f"✓ Default SSL context created")
            print(f"✓ SSL version: {ssl.OPENSSL_VERSION}")
            print(f"✓ Supported protocols: {context.protocol}")
            
            # Check TLS versions
            print(f"✓ Minimum TLS version: {context.minimum_version}")
            print(f"✓ Maximum TLS version: {context.maximum_version}")
            
            # Check cipher suites
            if hasattr(context, 'get_ciphers'):
                ciphers = context.get_ciphers()
                print(f"✓ Available cipher suites: {len(ciphers)}")
            
        except Exception as e:
            print(f"❌ SSL context error: {e}")
    
    def test_socket_connection(self):
        """Test raw socket connection to MongoDB Atlas nodes"""
        print("\n=== Socket Connection Test ===")
        
        if not self.mongodb_uri:
            print("❌ No MongoDB URI to test")
            return
            
        try:
            parsed = urlparse(self.mongodb_uri)
            hostname = parsed.hostname
            port = parsed.port or 27017
            
            # Test the main hostname
            print(f"Testing connection to {hostname}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            try:
                result = sock.connect_ex((hostname, port))
                if result == 0:
                    print(f"✓ Socket connection successful to {hostname}:{port}")
                else:
                    print(f"❌ Socket connection failed to {hostname}:{port} - Error: {result}")
            finally:
                sock.close()
                
        except Exception as e:
            print(f"❌ Socket test error: {e}")
    
    def test_ssl_handshake(self):
        """Test SSL handshake with MongoDB Atlas"""
        print("\n=== SSL Handshake Test ===")
        
        if not self.mongodb_uri:
            print("❌ No MongoDB URI to test")
            return
            
        try:
            parsed = urlparse(self.mongodb_uri)
            hostname = parsed.hostname
            port = parsed.port or 27017
            
            print(f"Testing SSL handshake with {hostname}:{port}")
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Test SSL connection
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    print(f"✓ SSL handshake successful")
                    print(f"✓ SSL version: {ssock.version()}")
                    print(f"✓ Cipher: {ssock.cipher()}")
                    
        except ssl.SSLError as e:
            print(f"❌ SSL handshake failed: {e}")
            if "TLSV1_ALERT_INTERNAL_ERROR" in str(e):
                print("⚠️  This is the exact error reported - TLS internal error")
                print("   Possible causes:")
                print("   1. PyMongo version incompatibility")
                print("   2. System SSL/TLS configuration issues")
                print("   3. MongoDB Atlas cluster configuration")
        except Exception as e:
            print(f"❌ SSL test error: {e}")
    
    async def test_pymongo_connection(self):
        """Test PyMongo connection with various SSL configurations"""
        print("\n=== PyMongo Connection Test ===")
        
        if not self.mongodb_uri:
            print("❌ No MongoDB URI to test")
            return
            
        # Test configurations
        test_configs = [
            {"name": "Default (Auto SSL)", "options": {}},
            {"name": "Explicit SSL", "options": {"tls": True}},
            {"name": "SSL + Allow Invalid Certs", "options": {"tls": True, "tlsAllowInvalidCertificates": True}},
            {"name": "SSL + Insecure", "options": {"tls": True, "tlsInsecure": True}},
        ]
        
        for config in test_configs:
            print(f"\nTesting: {config['name']}")
            try:
                client = AsyncIOMotorClient(self.mongodb_uri, **config['options'])
                
                # Test connection with timeout
                await asyncio.wait_for(client.admin.command('ping'), timeout=10)
                print(f"✓ {config['name']} - Connection successful")
                
                client.close()
                
            except asyncio.TimeoutError:
                print(f"❌ {config['name']} - Connection timeout")
            except Exception as e:
                print(f"❌ {config['name']} - Error: {e}")
                if "TLSV1_ALERT_INTERNAL_ERROR" in str(e):
                    print("   ⚠️  TLS internal error detected")
    
    def check_environment_variables(self):
        """Check relevant environment variables"""
        print("\n=== Environment Variables ===")
        
        env_vars = [
            "MONGODB_URI",
            "DATABASE_NAME", 
            "MONGODB_TLS_ENABLED",
            "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES",
            "MONGODB_MAX_POOL_SIZE",
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            "MONGODB_CONNECT_TIMEOUT_MS",
            "MONGODB_SOCKET_TIMEOUT_MS"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                if "URI" in var and value:
                    # Mask sensitive URI
                    masked = value[:20] + "..." + value[-10:] if len(value) > 30 else value
                    print(f"✓ {var}: {masked}")
                else:
                    print(f"✓ {var}: {value}")
            else:
                print(f"⚠️  {var}: Not set")
    
    async def run_diagnosis(self):
        """Run complete diagnosis"""
        print("=== MongoDB SSL Connection Diagnosis ===\n")
        
        # Basic checks
        self.analyze_pymongo_version()
        self.check_environment_variables()
        
        # Connection analysis
        is_atlas = self.analyze_connection_string()
        
        if is_atlas:
            self.check_ssl_context()
            self.test_socket_connection()
            self.test_ssl_handshake()
            await self.test_pymongo_connection()
        
        print("\n=== Diagnosis Complete ===")

async def main():
    """Main diagnostic function"""
    diagnostic = MongoDBSSLDiagnostic()
    await diagnostic.run_diagnosis()

if __name__ == "__main__":
    asyncio.run(main())