#!/usr/bin/env python3
"""
Check current environment configuration for MongoDB SSL/TLS diagnosis
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print('=== ENVIRONMENT VARIABLES ===')
print(f'MONGODB_URI: {os.getenv("MONGODB_URI", "NOT SET")}')
print(f'MONGODB_TLS_ENABLED: {os.getenv("MONGODB_TLS_ENABLED", "NOT SET")}')
print(f'MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: {os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "NOT SET")}')
print(f'MONGODB_SERVER_SELECTION_TIMEOUT_MS: {os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "NOT SET")}')
print(f'MONGODB_CONNECT_TIMEOUT_MS: {os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "NOT SET")}')
print(f'MONGODB_SOCKET_TIMEOUT_MS: {os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "NOT SET")}')

print('\n=== PYTHON SSL INFO ===')
import ssl
print(f'OpenSSL Version: {ssl.OPENSSL_VERSION}')
print(f'SSL Version: {ssl.ssl_version}')

print('\n=== PYMONGO VERSION ===')
import pymongo
print(f'PyMongo Version: {pymongo.version}')

print('\n=== MOTOR VERSION ===')
import motor
print(f'Motor Version: {motor.version}')

print('\n=== CONNECTION OPTIONS TEST ===')
try:
    from app.middleware.performance import DatabasePoolConfig
    options = DatabasePoolConfig.get_connection_options()
    print('DatabasePoolConfig.get_connection_options():')
    for key, value in options.items():
        print(f'  {key}: {value}')
except Exception as e:
    print(f'Error getting connection options: {e}')