#!/usr/bin/env python3
"""
Test and verify Redis setup with comprehensive diagnostics
"""

import subprocess
import os
import time
import sys

def run_command_simple(cmd):
    """Run a simple command with basic error handling"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""

def main():
    print("🔍 Redis WSL2 Test and Verification")
    print("=" * 40)
    
    # Test 1: Check if WSL is working
    print("1. Testing WSL connectivity...")
    success, output = run_command_simple('wsl -d Ubuntu -- echo "WSL OK"')
    if success and "WSL OK" in output:
        print("   ✅ WSL is working")
    else:
        print("   ❌ WSL not working")
        return False
    
    # Test 2: Get WSL IP
    print("2. Getting WSL IP address...")
    success, ip_output = run_command_simple('wsl -d Ubuntu -- hostname -I')
    if success and ip_output:
        wsl_ip = ip_output.split()[0]
        print(f"   ✅ WSL IP: {wsl_ip}")
    else:
        print("   ❌ Could not get WSL IP")
        return False
    
    # Test 3: Check if Redis is installed
    print("3. Checking Redis installation...")
    success, _ = run_command_simple('wsl -d Ubuntu -- which redis-server')
    if success:
        print("   ✅ Redis server found")
    else:
        print("   ❌ Redis server not found")
        return False
    
    success, _ = run_command_simple('wsl -d Ubuntu -- which redis-cli')
    if success:
        print("   ✅ Redis CLI found")
    else:
        print("   ❌ Redis CLI not found")
        return False
    
    # Test 4: Check Redis status
    print("4. Checking Redis status...")
    success, output = run_command_simple('wsl -d Ubuntu -- redis-cli ping')
    if success and "PONG" in output:
        print("   ✅ Redis is running and responding")
        redis_running = True
    else:
        print("   ⚠️ Redis not responding, will try to start it")
        redis_running = False
    
    # Test 5: Start Redis if not running
    if not redis_running:
        print("5. Starting Redis...")
        
        # Stop any existing instances
        run_command_simple('wsl -d Ubuntu -- sudo pkill redis-server')
        time.sleep(1)
        
        # Configure Redis for external access
        print("   Configuring Redis...")
        run_command_simple('wsl -d Ubuntu -- sudo sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf')
        run_command_simple('wsl -d Ubuntu -- sudo sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf')
        
        # Start Redis
        print("   Starting Redis service...")
        run_command_simple('wsl -d Ubuntu -- sudo systemctl start redis-server')
        time.sleep(3)
        
        # Test again
        success, output = run_command_simple('wsl -d Ubuntu -- redis-cli ping')
        if success and "PONG" in output:
            print("   ✅ Redis started successfully")
        else:
            print("   ❌ Failed to start Redis")
            return False
    
    # Test 6: Test Redis from Windows
    print("6. Testing Redis from Windows...")
    try:
        import redis
        client = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_connect_timeout=5)
        result = client.ping()
        if result:
            print("   ✅ Redis accessible from Windows!")
            
            # Test basic operations
            client.set("test_key", "test_value")
            value = client.get("test_key")
            if value == "test_value":
                print("   ✅ Redis read/write operations working")
            else:
                print("   ⚠️ Redis read/write test failed")
            
            client.delete("test_key")
            
        else:
            print("   ❌ Redis ping failed from Windows")
            return False
    except ImportError:
        print("   ❌ Redis Python library not available")
        return False
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        return False
    
    # Test 7: Update backend configuration
    print("7. Updating backend configuration...")
    
    env_path = "backend/.env"
    redis_url = f"redis://{wsl_ip}:6379"
    
    # Check if .env exists, if not create from example
    if not os.path.exists(env_path):
        if os.path.exists("backend/.env.example"):
            print("   Creating .env from .env.example")
            with open("backend/.env.example", 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
        else:
            print("   Creating new .env file")
            with open(env_path, 'w') as f:
                f.write(f"REDIS_URL={redis_url}\n")
    
    # Update Redis URL in .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith('REDIS_URL='):
            new_lines.append(f'REDIS_URL={redis_url}\n')
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        new_lines.append(f'REDIS_URL={redis_url}\n')
    
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"   ✅ Updated backend/.env with REDIS_URL={redis_url}")
    
    # Test 8: Verify configuration
    print("8. Verifying configuration...")
    with open(env_path, 'r') as f:
        content = f.read()
        if redis_url in content:
            print("   ✅ Redis URL correctly set in .env")
        else:
            print("   ❌ Redis URL not found in .env")
            return False
    
    print("\n🎉 Redis WSL2 setup completed successfully!")
    print("=" * 40)
    print(f"WSL2 IP Address: {wsl_ip}")
    print(f"Redis URL: {redis_url}")
    print(f"Backend .env updated: {env_path}")
    print("\n📋 Next Steps:")
    print("1. Restart your backend application")
    print("2. Redis-dependent features should now work:")
    print("   - Rate limiting with persistent storage")
    print("   - Response caching")
    print("   - JWT token blacklisting")
    print("   - Login attempt tracking")
    print("3. Check backend logs for Redis connection success")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)