#!/usr/bin/env python3
"""
MongoDB SSL/TLS Regression Diagnosis Script
Validates assumptions about SSL connection failures after previous fixes
"""

import os
import sys
import ssl
import socket
import asyncio
import json
from datetime import datetime
from urllib.parse import urlparse
import logging

# Add the backend app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
    from dotenv import load_dotenv
    from app.middleware.performance import DatabasePoolConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBSSLRegressionDiagnosis:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "diagnosis_type": "SSL_REGRESSION_ANALYSIS",
            "tests": {}
        }
        
    def log_test_result(self, test_name: str, success: bool, details: dict):
        """Log test result"""
        self.results["tests"][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"\n{status} {test_name}")
        for key, value in details.items():
            print(f"  {key}: {value}")

    def test_environment_variable_loading(self):
        """Test 1: Validate environment variable loading"""
        print("=== Test 1: Environment Variable Loading ===")
        
        # Load environment variables
        load_dotenv(os.path.join('backend', '.env'))
        
        required_vars = [
            'MONGODB_URI',
            'MONGODB_TLS_ENABLED',
            'MONGODB_TLS_ALLOW_INVALID_CERTIFICATES',
            'MONGODB_SERVER_SELECTION_TIMEOUT_MS',
            'MONGODB_CONNECT_TIMEOUT_MS',
            'MONGODB_SOCKET_TIMEOUT_MS'
        ]
        
        env_status = {}
        all_loaded = True
        
        for var in required_vars:
            value = os.getenv(var)
            env_status[var] = value if value else "NOT_SET"
            if not value:
                all_loaded = False
        
        # Check if MongoDB URI is Atlas
        mongodb_uri = os.getenv('MONGODB_URI', '')
        is_atlas = '.mongodb.net' in mongodb_uri.lower()
        env_status['IS_ATLAS_URI'] = is_atlas
        env_status['URI_MASKED'] = mongodb_uri[:50] + "..." if len(mongodb_uri) > 50 else mongodb_uri
        
        self.log_test_result("environment_variable_loading", all_loaded, env_status)
        return all_loaded

    def test_database_pool_config_generation(self):
        """Test 2: Validate DatabasePoolConfig options generation"""
        print("\n=== Test 2: DatabasePoolConfig Options Generation ===")
        
        try:
            # Get connection options using the current configuration
            options = DatabasePoolConfig.get_connection_options()
            
            # Check for required SSL/TLS options
            has_tls = 'tls' in options and options['tls'] is True
            has_timeouts = all(key in options for key in [
                'serverSelectionTimeoutMS',
                'connectTimeoutMS', 
                'socketTimeoutMS'
            ])
            
            config_details = {
                'has_tls_enabled': has_tls,
                'has_required_timeouts': has_timeouts,
                'tls_allow_invalid_certs': options.get('tlsAllowInvalidCertificates', False),
                'server_selection_timeout': options.get('serverSelectionTimeoutMS'),
                'connect_timeout': options.get('connectTimeoutMS'),
                'socket_timeout': options.get('socketTimeoutMS'),
                'max_pool_size': options.get('maxPoolSize'),
                'auth_source': options.get('authSource', 'NOT_SET')
            }
            
            success = has_tls and has_timeouts
            self.log_test_result("database_pool_config_generation", success, config_details)
            return success, options
            
        except Exception as e:
            self.log_test_result("database_pool_config_generation", False, {
                'error': str(e),
                'error_type': type(e).__name__
            })
            return False, {}

    def test_direct_ssl_handshake(self):
        """Test 3: Direct SSL handshake with MongoDB Atlas"""
        print("\n=== Test 3: Direct SSL Handshake Test ===")
        
        mongodb_uri = os.getenv('MONGODB_URI', '')
        if not mongodb_uri:
            self.log_test_result("direct_ssl_handshake", False, {
                'error': 'No MongoDB URI found'
            })
            return False
        
        try:
            # Parse hostname from URI
            if mongodb_uri.startswith('mongodb+srv://'):
                # Extract hostname from SRV URI
                uri_parts = mongodb_uri.split('@')[1].split('/')[0]
                hostname = uri_parts.split('?')[0]  # Remove query parameters
            else:
                parsed = urlparse(mongodb_uri.replace('mongodb://', 'http://'))
                hostname = parsed.hostname
            
            print(f"Testing SSL handshake with: {hostname}:27017")
            
            # Test different SSL contexts
            contexts_to_test = [
                ("Default SSL Context", ssl.create_default_context()),
                ("No Certificate Verification", ssl.create_default_context()),
                ("TLS 1.2+ Only", ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
            ]
            
            # Configure contexts
            contexts_to_test[1][1].check_hostname = False
            contexts_to_test[1][1].verify_mode = ssl.CERT_NONE
            
            contexts_to_test[2][1].check_hostname = False
            contexts_to_test[2][1].verify_mode = ssl.CERT_NONE
            contexts_to_test[2][1].minimum_version = ssl.TLSVersion.TLSv1_2
            
            handshake_results = {}
            successful_context = None
            
            for context_name, context in contexts_to_test:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    
                    ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
                    ssl_sock.connect((hostname, 27017))
                    
                    handshake_results[context_name] = {
                        'success': True,
                        'ssl_version': ssl_sock.version(),
                        'cipher': ssl_sock.cipher()[0] if ssl_sock.cipher() else 'Unknown'
                    }
                    
                    if not successful_context:
                        successful_context = context_name
                    
                    ssl_sock.close()
                    
                except Exception as e:
                    handshake_results[context_name] = {
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
            
            success = successful_context is not None
            handshake_results['successful_context'] = successful_context
            
            self.log_test_result("direct_ssl_handshake", success, handshake_results)
            return success
            
        except Exception as e:
            self.log_test_result("direct_ssl_handshake", False, {
                'error': str(e),
                'error_type': type(e).__name__
            })
            return False

    def test_pymongo_connection_with_current_config(self):
        """Test 4: PyMongo connection using current configuration"""
        print("\n=== Test 4: PyMongo Connection with Current Config ===")
        
        mongodb_uri = os.getenv('MONGODB_URI', '')
        if not mongodb_uri:
            self.log_test_result("pymongo_current_config", False, {
                'error': 'No MongoDB URI found'
            })
            return False
        
        try:
            # Get current configuration options
            _, options = self.test_database_pool_config_generation()
            
            # Test connection with current options
            client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # Short timeout for quick test
                **options
            )
            
            # Try to get server info
            server_info = client.server_info()
            client.close()
            
            connection_details = {
                'mongodb_version': server_info.get('version', 'Unknown'),
                'connection_successful': True,
                'options_used': str(options)
            }
            
            self.log_test_result("pymongo_current_config", True, connection_details)
            return True
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'is_ssl_error': 'SSL' in str(e) or 'TLS' in str(e),
                'is_timeout_error': 'timeout' in str(e).lower(),
                'options_attempted': str(options) if 'options' in locals() else 'Failed to get options'
            }
            
            self.log_test_result("pymongo_current_config", False, error_details)
            return False

    async def test_motor_connection_with_current_config(self):
        """Test 5: Motor (async) connection using current configuration"""
        print("\n=== Test 5: Motor Connection with Current Config ===")
        
        mongodb_uri = os.getenv('MONGODB_URI', '')
        if not mongodb_uri:
            self.log_test_result("motor_current_config", False, {
                'error': 'No MongoDB URI found'
            })
            return False
        
        try:
            # Get current configuration options
            _, options = self.test_database_pool_config_generation()
            
            # Test async connection with current options
            client = AsyncIOMotorClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # Short timeout for quick test
                **options
            )
            
            # Try to get server info
            server_info = await client.server_info()
            client.close()
            
            connection_details = {
                'mongodb_version': server_info.get('version', 'Unknown'),
                'connection_successful': True,
                'async_driver': 'Motor',
                'options_used': str(options)
            }
            
            self.log_test_result("motor_current_config", True, connection_details)
            return True
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'is_ssl_error': 'SSL' in str(e) or 'TLS' in str(e),
                'is_timeout_error': 'timeout' in str(e).lower(),
                'options_attempted': str(options) if 'options' in locals() else 'Failed to get options'
            }
            
            self.log_test_result("motor_current_config", False, error_details)
            return False

    def test_system_ssl_info(self):
        """Test 6: System SSL/TLS information"""
        print("\n=== Test 6: System SSL/TLS Information ===")
        
        try:
            ssl_info = {
                'python_version': sys.version,
                'ssl_version': ssl.OPENSSL_VERSION,
                'ssl_version_info': ssl.OPENSSL_VERSION_INFO,
                'supported_protocols': [],
                'default_ca_certs': ssl.get_default_verify_paths()._asdict()
            }
            
            # Check supported protocols
            for protocol in ['TLSv1', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']:
                try:
                    getattr(ssl, f'PROTOCOL_{protocol}')
                    ssl_info['supported_protocols'].append(protocol)
                except AttributeError:
                    pass
            
            # Check if we can create a default context
            try:
                context = ssl.create_default_context()
                ssl_info['default_context_protocol'] = str(context.protocol)
                ssl_info['default_verify_mode'] = str(context.verify_mode)
            except Exception as e:
                ssl_info['default_context_error'] = str(e)
            
            self.log_test_result("system_ssl_info", True, ssl_info)
            return True
            
        except Exception as e:
            self.log_test_result("system_ssl_info", False, {
                'error': str(e),
                'error_type': type(e).__name__
            })
            return False

    async def run_all_tests(self):
        """Run all diagnostic tests"""
        print("MongoDB SSL/TLS Regression Diagnosis")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print("=" * 60)
        
        # Run tests in sequence
        test_results = []
        
        test_results.append(self.test_environment_variable_loading())
        test_results.append(self.test_database_pool_config_generation()[0])
        test_results.append(self.test_system_ssl_info())
        test_results.append(self.test_direct_ssl_handshake())
        test_results.append(self.test_pymongo_connection_with_current_config())
        test_results.append(await self.test_motor_connection_with_current_config())
        
        # Summary
        print("\n" + "=" * 60)
        print("DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - SSL configuration appears to be working")
            print("   The issue may be intermittent or context-specific")
        elif passed_tests == 0:
            print("🚨 ALL TESTS FAILED - Major SSL configuration issue detected")
        else:
            print("⚠️  PARTIAL FAILURE - Some SSL components working, others failing")
        
        # Specific recommendations
        print("\n" + "=" * 60)
        print("DIAGNOSTIC RECOMMENDATIONS")
        print("=" * 60)
        
        if not test_results[0]:  # Environment variables
            print("🔧 CRITICAL: Environment variables not loading properly")
            print("   - Check .env file location and format")
            print("   - Verify load_dotenv() is called before database connection")
        
        if not test_results[1]:  # Database pool config
            print("🔧 CRITICAL: DatabasePoolConfig not generating proper SSL options")
            print("   - Check DatabasePoolConfig.get_connection_options() method")
            print("   - Verify SSL/TLS environment variables are being processed")
        
        if not test_results[3]:  # Direct SSL handshake
            print("🔧 NETWORK: Direct SSL handshake failing")
            print("   - Check network connectivity to MongoDB Atlas")
            print("   - Verify firewall/proxy settings")
            print("   - Consider DNS resolution issues")
        
        if not test_results[4] or not test_results[5]:  # PyMongo/Motor connections
            print("🔧 DRIVER: MongoDB driver connection issues")
            print("   - Check PyMongo/Motor version compatibility")
            print("   - Verify SSL options format and values")
            print("   - Consider connection string parameters")
        
        # Save results to file
        results_file = f"mongodb_ssl_regression_diagnosis_{int(datetime.now().timestamp())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results

async def main():
    """Main diagnostic function"""
    diagnosis = MongoDBSSLRegressionDiagnosis()
    results = await diagnosis.run_all_tests()
    
    # Return exit code based on results
    if all(test['success'] for test in results['tests'].values()):
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed

if __name__ == "__main__":
    asyncio.run(main())