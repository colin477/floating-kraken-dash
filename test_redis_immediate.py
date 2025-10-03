#!/usr/bin/env python3
"""
Immediate Redis Test and Fix
"""

import redis
import subprocess
import time

def test_redis_connection(host, port=6379):
    """Test Redis connection"""
    try:
        r = redis.Redis(host=host, port=port, decode_responses=True, socket_timeout=3)
        response = r.ping()
        return response
    except Exception as e:
        print(f"Connection failed to {host}:{port} - {e}")
        return False

def get_wsl_ip():
    """Get WSL IP using PowerShell"""
    try:
        result = subprocess.run(
            'powershell -Command "(wsl hostname -I).Trim()"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split()[0]
    except:
        pass
    return None

def start_redis_wsl():
    """Start Redis in WSL"""
    commands = [
        'wsl -d Ubuntu -- sudo pkill redis-server',
        'wsl -d Ubuntu -- sudo redis-server /etc/redis/redis.conf --daemonize yes'
    ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, timeout=10)
            time.sleep(1)
        except:
            pass

print("🔥 Immediate Redis Test and Fix")
print("=" * 40)

# Test current Redis URL from .env
current_ip = "172.20.240.1"
print(f"1. Testing current Redis IP: {current_ip}")
if test_redis_connection(current_ip):
    print("   ✅ Current Redis connection works!")
    print(f"   Redis is accessible at {current_ip}:6379")
    exit(0)
else:
    print("   ❌ Current Redis connection failed")

# Get current WSL IP
print("\n2. Getting current WSL2 IP...")
wsl_ip = get_wsl_ip()
if wsl_ip:
    print(f"   Current WSL2 IP: {wsl_ip}")
    
    if wsl_ip != current_ip:
        print(f"   ⚠️ IP changed from {current_ip} to {wsl_ip}")
    
    # Test new IP
    print(f"\n3. Testing Redis at new IP: {wsl_ip}")
    if test_redis_connection(wsl_ip):
        print("   ✅ Redis works with new IP!")
        
        # Update .env file
        print("\n4. Updating backend/.env...")
        with open("backend/.env", "r") as f:
            content = f.read()
        
        new_content = content.replace(
            f"REDIS_URL=redis://{current_ip}:6379",
            f"REDIS_URL=redis://{wsl_ip}:6379"
        )
        
        with open("backend/.env", "w") as f:
            f.write(new_content)
        
        print(f"   ✅ Updated REDIS_URL to redis://{wsl_ip}:6379")
        print("\n🎉 Redis fix completed!")
        print("   Restart your backend server to use the updated Redis URL.")
        exit(0)
    else:
        print("   ❌ Redis not responding at new IP either")
else:
    print("   ❌ Failed to get WSL2 IP")

# Try to start Redis
print("\n5. Attempting to start Redis in WSL2...")
start_redis_wsl()
time.sleep(3)

# Test again
if wsl_ip and test_redis_connection(wsl_ip):
    print("   ✅ Redis started successfully!")
    
    # Update .env file
    print("\n6. Updating backend/.env...")
    with open("backend/.env", "r") as f:
        content = f.read()
    
    new_content = content.replace(
        f"REDIS_URL=redis://{current_ip}:6379",
        f"REDIS_URL=redis://{wsl_ip}:6379"
    )
    
    with open("backend/.env", "w") as f:
        f.write(new_content)
    
    print(f"   ✅ Updated REDIS_URL to redis://{wsl_ip}:6379")
    print("\n🎉 Redis fix completed!")
    print("   Restart your backend server to use Redis.")
else:
    print("   ❌ Failed to start Redis or connection still failing")
    print("\n💥 Manual intervention required:")
    print("   1. Check WSL2 Ubuntu is running")
    print("   2. Install Redis: sudo apt install redis-server")
    print("   3. Configure Redis to bind to 0.0.0.0")
    print("   4. Start Redis service")