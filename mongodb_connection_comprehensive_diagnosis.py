#!/usr/bin/env python3
"""
Comprehensive MongoDB Connection Diagnosis Script
Validates network connectivity, DNS resolution, SSL/TLS, and connection parameters
"""

import asyncio
import socket
import ssl
import time
import os
import sys
import json
from datetime import datetime
from urllib.parse import urlparse
import subprocess
import platform

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

class MongoDBDiagnostics:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI", "")
        self.database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "network_tests": {},
            "dns_tests": {},
            "ssl_tests": {},
            "mongodb_tests": {},
            "recommendations": []
        }
        
    def log_result(self, category, test_name, success, details, error=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            result["error"] = str(error)
            
        if category not in self.results:
            self.results[category] = {}
        self.results[category][test_name] = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if error:
            print(f"   Error: {error}")

    def get_system_info(self):
        """Collect system information"""
        print("\n🔍 Collecting System Information...")
        
        try:
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn()
            }
            
            # Get network interfaces
            try:
                import psutil
                interfaces = {}
                for interface, addrs in psutil.net_if_addrs().items():
                    interfaces[interface] = [addr.address for addr in addrs]
                system_info["network_interfaces"] = interfaces
            except ImportError:
                system_info["network_interfaces"] = "psutil not available"
            
            self.results["system_info"] = system_info
            print(f"✅ System: {system_info['platform']}")
            print(f"✅ Python: {system_info['python_version']}")
            print(f"✅ Hostname: {system_info['hostname']}")
            
        except Exception as e:
            self.log_result("system_info", "system_collection", False, "Failed to collect system info", e)

    def test_dns_resolution(self):
        """Test DNS resolution for MongoDB Atlas hostname"""
        print("\n🌐 Testing DNS Resolution...")
        
        if not self.mongodb_uri:
            self.log_result("dns_tests", "uri_validation", False, "MongoDB URI not found in environment")
            return
            
        try:
            # Parse MongoDB URI to extract hostname
            parsed = urlparse(self.mongodb_uri.replace("mongodb+srv://", "https://"))
            hostname = parsed.hostname
            
            if not hostname:
                self.log_result("dns_tests", "hostname_extraction", False, "Could not extract hostname from URI")
                return
                
            self.log_result("dns_tests", "hostname_extraction", True, f"Extracted hostname: {hostname}")
            
            # Test DNS resolution
            try:
                start_time = time.time()
                ip_addresses = socket.gethostbyname_ex(hostname)
                resolution_time = time.time() - start_time
                
                self.log_result("dns_tests", "dns_resolution", True, 
                              f"Resolved to {len(ip_addresses[2])} IPs in {resolution_time:.3f}s: {ip_addresses[2]}")
                
                # Test each IP for connectivity
                for i, ip in enumerate(ip_addresses[2][:3]):  # Test first 3 IPs
                    self.test_tcp_connectivity(ip, 27017, f"ip_{i+1}")
                    
            except socket.gaierror as e:
                self.log_result("dns_tests", "dns_resolution", False, f"DNS resolution failed for {hostname}", e)
                self.results["recommendations"].append("Check DNS configuration and network connectivity")
                
        except Exception as e:
            self.log_result("dns_tests", "dns_parsing", False, "Failed to parse MongoDB URI", e)

    def test_tcp_connectivity(self, host, port, test_suffix=""):
        """Test TCP connectivity to a specific host and port"""
        test_name = f"tcp_connectivity_{test_suffix}" if test_suffix else "tcp_connectivity"
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout
            
            result = sock.connect_ex((host, port))
            connect_time = time.time() - start_time
            sock.close()
            
            if result == 0:
                self.log_result("network_tests", test_name, True, 
                              f"TCP connection to {host}:{port} successful in {connect_time:.3f}s")
            else:
                self.log_result("network_tests", test_name, False, 
                              f"TCP connection to {host}:{port} failed with code {result}")
                
        except Exception as e:
            self.log_result("network_tests", test_name, False, 
                          f"TCP connection test to {host}:{port} failed", e)

    def test_ssl_connectivity(self):
        """Test SSL/TLS connectivity to MongoDB Atlas"""
        print("\n🔒 Testing SSL/TLS Connectivity...")
        
        if not self.mongodb_uri:
            return
            
        try:
            # Parse hostname from URI
            parsed = urlparse(self.mongodb_uri.replace("mongodb+srv://", "https://"))
            hostname = parsed.hostname
            
            if not hostname:
                return
                
            # Test SSL connection
            try:
                context = ssl.create_default_context()
                
                start_time = time.time()
                with socket.create_connection((hostname, 27017), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        ssl_time = time.time() - start_time
                        cert = ssock.getpeercert()
                        
                        self.log_result("ssl_tests", "ssl_handshake", True, 
                                      f"SSL handshake successful in {ssl_time:.3f}s")
                        
                        # Check certificate details
                        if cert:
                            subject = dict(x[0] for x in cert['subject'])
                            issuer = dict(x[0] for x in cert['issuer'])
                            
                            self.log_result("ssl_tests", "certificate_validation", True, 
                                          f"Certificate valid - Subject: {subject.get('commonName', 'Unknown')}, "
                                          f"Issuer: {issuer.get('organizationName', 'Unknown')}")
                        else:
                            self.log_result("ssl_tests", "certificate_validation", False, 
                                          "No certificate information available")
                            
            except ssl.SSLError as e:
                self.log_result("ssl_tests", "ssl_handshake", False, "SSL handshake failed", e)
                self.results["recommendations"].append("Check SSL/TLS configuration and certificate validation")
                
            except Exception as e:
                self.log_result("ssl_tests", "ssl_connection", False, "SSL connection test failed", e)
                
        except Exception as e:
            self.log_result("ssl_tests", "ssl_setup", False, "SSL test setup failed", e)

    async def test_mongodb_connection(self):
        """Test MongoDB connection with various configurations"""
        print("\n🍃 Testing MongoDB Connection...")
        
        if not self.mongodb_uri:
            self.log_result("mongodb_tests", "uri_check", False, "MongoDB URI not configured")
            return
            
        # Test 1: Basic connection with current settings
        await self.test_connection_config("basic", {})
        
        # Test 2: Connection with increased timeouts
        await self.test_connection_config("increased_timeouts", {
            'serverSelectionTimeoutMS': 60000,
            'connectTimeoutMS': 60000,
            'socketTimeoutMS': 60000
        })
        
        # Test 3: Connection with SSL explicitly disabled (for testing)
        await self.test_connection_config("no_ssl", {
            'tls': False,
            'ssl': False
        })
        
        # Test 4: Connection with minimal pool size
        await self.test_connection_config("minimal_pool", {
            'maxPoolSize': 1,
            'minPoolSize': 0,
            'serverSelectionTimeoutMS': 30000
        })

    async def test_connection_config(self, config_name, extra_options):
        """Test MongoDB connection with specific configuration"""
        try:
            # Base connection options
            connection_options = {
                'retryWrites': True,
                'w': 'majority',
                'appName': 'EZ_Eatin_Diagnostics'
            }
            
            # Add extra options
            connection_options.update(extra_options)
            
            start_time = time.time()
            client = AsyncIOMotorClient(self.mongodb_uri, **connection_options)
            
            # Test connection with ping
            await asyncio.wait_for(client.admin.command('ping'), timeout=30)
            connect_time = time.time() - start_time
            
            # Get server info
            server_info = await client.server_info()
            
            # Test database access
            db = client[self.database_name]
            collections = await db.list_collection_names()
            
            client.close()
            
            self.log_result("mongodb_tests", f"connection_{config_name}", True, 
                          f"Connection successful in {connect_time:.3f}s - "
                          f"MongoDB {server_info.get('version', 'Unknown')}, "
                          f"{len(collections)} collections")
            
        except asyncio.TimeoutError as e:
            self.log_result("mongodb_tests", f"connection_{config_name}", False, 
                          "Connection timeout", e)
            
        except ConnectionFailure as e:
            self.log_result("mongodb_tests", f"connection_{config_name}", False, 
                          "Connection failure", e)
            
        except Exception as e:
            self.log_result("mongodb_tests", f"connection_{config_name}", False, 
                          "Unexpected connection error", e)

    def test_network_tools(self):
        """Test network connectivity using system tools"""
        print("\n🔧 Testing Network Tools...")
        
        if not self.mongodb_uri:
            return
            
        try:
            # Parse hostname from URI
            parsed = urlparse(self.mongodb_uri.replace("mongodb+srv://", "https://"))
            hostname = parsed.hostname
            
            if not hostname:
                return
                
            # Test ping (if available)
            try:
                if platform.system().lower() == "windows":
                    result = subprocess.run(['ping', '-n', '4', hostname], 
                                          capture_output=True, text=True, timeout=30)
                else:
                    result = subprocess.run(['ping', '-c', '4', hostname], 
                                          capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.log_result("network_tests", "ping_test", True, 
                                  f"Ping successful to {hostname}")
                else:
                    self.log_result("network_tests", "ping_test", False, 
                                  f"Ping failed to {hostname}: {result.stderr}")
                    
            except Exception as e:
                self.log_result("network_tests", "ping_test", False, 
                              f"Ping test failed", e)
                
            # Test nslookup (if available)
            try:
                result = subprocess.run(['nslookup', hostname], 
                                      capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    self.log_result("network_tests", "nslookup_test", True, 
                                  f"nslookup successful for {hostname}")
                else:
                    self.log_result("network_tests", "nslookup_test", False, 
                                  f"nslookup failed for {hostname}")
                    
            except Exception as e:
                self.log_result("network_tests", "nslookup_test", False, 
                              "nslookup test failed", e)
                
        except Exception as e:
            self.log_result("network_tests", "network_tools_setup", False, 
                          "Network tools test setup failed", e)

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n💡 Generating Recommendations...")
        
        # Check for DNS issues
        dns_failed = any(not test.get("success", True) for test in self.results.get("dns_tests", {}).values())
        if dns_failed:
            self.results["recommendations"].append("DNS resolution issues detected - check network configuration and DNS servers")
        
        # Check for network connectivity issues
        network_failed = any(not test.get("success", True) for test in self.results.get("network_tests", {}).values())
        if network_failed:
            self.results["recommendations"].append("Network connectivity issues detected - check firewall and network configuration")
        
        # Check for SSL issues
        ssl_failed = any(not test.get("success", True) for test in self.results.get("ssl_tests", {}).values())
        if ssl_failed:
            self.results["recommendations"].append("SSL/TLS issues detected - check certificate validation and SSL configuration")
        
        # Check for MongoDB connection issues
        mongodb_failed = any(not test.get("success", True) for test in self.results.get("mongodb_tests", {}).values())
        if mongodb_failed:
            self.results["recommendations"].append("MongoDB connection issues detected - check credentials and connection parameters")
        
        # Print recommendations
        if self.results["recommendations"]:
            print("\n🎯 Recommendations:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"{i}. {rec}")
        else:
            print("\n✅ All tests passed - no specific recommendations")

    def save_results(self):
        """Save diagnostic results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mongodb_connection_diagnosis_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Results saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")

    async def run_all_tests(self):
        """Run all diagnostic tests"""
        print("🚀 Starting MongoDB Connection Diagnostics...")
        print("=" * 60)
        
        # Run all tests
        self.get_system_info()
        self.test_dns_resolution()
        self.test_ssl_connectivity()
        self.test_network_tools()
        await self.test_mongodb_connection()
        
        # Generate recommendations and save results
        self.generate_recommendations()
        self.save_results()
        
        print("\n" + "=" * 60)
        print("🏁 Diagnostics Complete!")

async def main():
    """Main function"""
    diagnostics = MongoDBDiagnostics()
    await diagnostics.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())