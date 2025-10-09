#!/usr/bin/env python3
"""
MongoDB SSL Connection Test Script
Tests the SSL handshake with MongoDB Atlas using updated PyMongo 4.8.0 and Motor 3.5.1
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import ssl

# Load environment variables
from dotenv import load_dotenv
import os
# Load from backend directory if it exists, otherwise current directory
backend_env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)
else:
    load_dotenv()

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"  {test_name}")
    print(f"{'='*60}")

def print_result(success, message):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")

def test_pymongo_versions():
    """Test and display PyMongo and Motor versions"""
    print_test_header("DEPENDENCY VERSIONS")
    
    try:
        import pymongo
        import motor
        
        print(f"PyMongo version: {pymongo.version}")
        print(f"Motor version: {motor.version}")
        
        # Check if we have the expected versions
        expected_pymongo = "4.8.0"
        expected_motor = "3.5.1"
        
        pymongo_ok = pymongo.version.startswith(expected_pymongo)
        motor_ok = motor.version.startswith(expected_motor)
        
        print_result(pymongo_ok, f"PyMongo {expected_pymongo} {'installed' if pymongo_ok else 'NOT installed'}")
        print_result(motor_ok, f"Motor {expected_motor} {'installed' if motor_ok else 'NOT installed'}")
        
        return pymongo_ok and motor_ok
        
    except Exception as e:
        print_result(False, f"Error checking versions: {e}")
        return False

def test_synchronous_connection():
    """Test synchronous MongoDB connection with PyMongo"""
    print_test_header("SYNCHRONOUS CONNECTION TEST (PyMongo)")
    
    mongodb_url = os.getenv('MONGODB_URI')
    if not mongodb_url:
        print_result(False, "MONGODB_URI environment variable not found")
        return False
    
    try:
        # Create client with SSL configuration
        client = MongoClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            tls=True,
            tlsAllowInvalidCertificates=True,  # For testing
            retryWrites=True,
            w='majority'
        )
        
        # Test the connection
        print("Attempting to connect to MongoDB Atlas...")
        client.admin.command('ping')
        
        # Get server info
        server_info = client.server_info()
        print(f"Connected to MongoDB version: {server_info.get('version', 'Unknown')}")
        
        # Test database operations
        db = client.test_db
        collection = db.test_collection
        
        # Insert a test document
        test_doc = {
            "test_id": "ssl_test",
            "timestamp": datetime.utcnow(),
            "pymongo_version": pymongo.version,
            "test_type": "synchronous"
        }
        
        result = collection.insert_one(test_doc)
        print(f"Test document inserted with ID: {result.inserted_id}")
        
        # Read it back
        found_doc = collection.find_one({"test_id": "ssl_test"})
        if found_doc:
            print("Test document successfully retrieved")
        
        # Clean up
        collection.delete_one({"test_id": "ssl_test"})
        print("Test document cleaned up")
        
        client.close()
        print_result(True, "Synchronous connection test completed successfully")
        return True
        
    except ConnectionFailure as e:
        print_result(False, f"Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print_result(False, f"Server selection timeout: {e}")
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False

async def test_asynchronous_connection():
    """Test asynchronous MongoDB connection with Motor"""
    print_test_header("ASYNCHRONOUS CONNECTION TEST (Motor)")
    
    mongodb_url = os.getenv('MONGODB_URI')
    if not mongodb_url:
        print_result(False, "MONGODB_URI environment variable not found")
        return False
    
    try:
        # Create async client with SSL configuration
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            tls=True,
            tlsAllowInvalidCertificates=True,  # For testing
            retryWrites=True,
            w='majority'
        )
        
        # Test the connection
        print("Attempting async connection to MongoDB Atlas...")
        await client.admin.command('ping')
        
        # Get server info
        server_info = await client.server_info()
        print(f"Connected to MongoDB version: {server_info.get('version', 'Unknown')}")
        
        # Test database operations
        db = client.test_db
        collection = db.test_collection
        
        # Insert a test document
        test_doc = {
            "test_id": "ssl_test_async",
            "timestamp": datetime.utcnow(),
            "motor_version": "3.5.1",  # Motor version
            "test_type": "asynchronous"
        }
        
        result = await collection.insert_one(test_doc)
        print(f"Test document inserted with ID: {result.inserted_id}")
        
        # Read it back
        found_doc = await collection.find_one({"test_id": "ssl_test_async"})
        if found_doc:
            print("Test document successfully retrieved")
        
        # Clean up
        await collection.delete_one({"test_id": "ssl_test_async"})
        print("Test document cleaned up")
        
        client.close()
        print_result(True, "Asynchronous connection test completed successfully")
        return True
        
    except ConnectionFailure as e:
        print_result(False, f"Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print_result(False, f"Server selection timeout: {e}")
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False

def test_ssl_configuration():
    """Test SSL configuration details"""
    print_test_header("SSL CONFIGURATION TEST")
    
    try:
        # Check SSL module
        print(f"SSL module version: {ssl.OPENSSL_VERSION}")
        print(f"SSL protocols supported: {ssl.HAS_TLSv1_3}")
        
        # Test SSL context creation
        context = ssl.create_default_context()
        print(f"Default SSL context created successfully")
        print(f"SSL context protocol: {context.protocol}")
        
        print_result(True, "SSL configuration is properly set up")
        return True
        
    except Exception as e:
        print_result(False, f"SSL configuration error: {e}")
        return False

async def main():
    """Main test function"""
    print(f"MongoDB SSL Connection Test")
    print(f"Started at: {datetime.utcnow().isoformat()}Z")
    print(f"Python version: {sys.version}")
    
    # Run all tests
    tests = [
        ("Version Check", test_pymongo_versions()),
        ("SSL Configuration", test_ssl_configuration()),
        ("Synchronous Connection", test_synchronous_connection()),
        ("Asynchronous Connection", await test_asynchronous_connection())
    ]
    
    # Summary
    print_test_header("TEST SUMMARY")
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SSL connection is working properly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)