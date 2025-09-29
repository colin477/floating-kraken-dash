import os
from urllib.parse import urlparse, parse_qs
import ssl

# Parse the MongoDB URI
uri = 'mongodb+srv://colin_db_user:FnaPFUQh6aAjhfiR@cluster0.vcpyxwh.mongodb.net/ez_eatin?retryWrites=true&w=majority&appName=Cluster0'
parsed = urlparse(uri)
print('=== MongoDB Connection Analysis ===')
print(f'Scheme: {parsed.scheme}')
print(f'Hostname: {parsed.hostname}')
print(f'Port: {parsed.port}')
print(f'Database: {parsed.path.lstrip("/")}')
print(f'Query params: {dict(parse_qs(parsed.query))}')
print()

# Check SSL context and TLS version support
print('=== SSL/TLS Environment Analysis ===')
print(f'Python SSL version: {ssl.OPENSSL_VERSION}')
print(f'Default SSL context protocol: {ssl.create_default_context().protocol}')
print()

# Check pymongo and motor versions
try:
    import pymongo
    print(f'PyMongo version: {pymongo.version}')
except ImportError:
    print('PyMongo not available')

try:
    import motor
    print(f'Motor version: {motor.version}')
except ImportError:
    print('Motor not available')

# Test basic SSL connection to MongoDB Atlas
print('\n=== Testing SSL Connection ===')
try:
    import socket
    import ssl
    
    # Extract hostname from URI
    hostname = 'cluster0.vcpyxwh.mongodb.net'
    port = 27017
    
    # Create SSL context
    context = ssl.create_default_context()
    
    # Test connection
    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f'SSL connection successful to {hostname}:{port}')
            print(f'SSL version: {ssock.version()}')
            print(f'Cipher: {ssock.cipher()}')
            
except Exception as e:
    print(f'SSL connection failed: {e}')