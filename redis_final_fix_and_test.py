#!/usr/bin/env python3
"""
Final Redis Fix and Test Script
Handles WSL2 Redis connectivity with timeout handling
"""

import redis
import subprocess
import time
import os
import signal

def run_command_with_timeout(cmd, timeout=15):
    """Run command with timeout"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_redis_connection(host, port=6379, timeout=3):
    """Test Redis connection with timeout"""
    try:
        r = redis.Redis(host=host, port=port, decode_responses=True, socket_timeout=timeout)
        return r.ping()
    except:
        return False

def get_wsl_ip():
    """Get WSL2 IP with multiple methods"""
    methods = [
        'powershell -Command "(wsl hostname -I).Trim()"',
        'wsl -- hostname -I',
        'wsl -d Ubuntu -- hostname -I'
    ]
    
    for method in methods:
        success, output, _ = run_command_with_timeout(method, 10)
        if success and output:
            ip = output.split()[0] if output.split() else None
            if ip and ip != '127.0.0.1':
                return ip
    return None

def fix_and_start_redis():
    """Fix Redis configuration and start service"""
    commands = [
        'wsl -d Ubuntu -- sudo pkill redis-server',
        'wsl -d Ubuntu -- sudo sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf',
        'wsl -d Ubuntu -- sudo sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf',
        'wsl -d Ubuntu -- sudo redis-server /etc/redis/redis.conf --daemonize yes'
    ]
    
    for cmd in commands:
        run_command_with_timeout(cmd, 10)
        time.sleep(1)

def update_env_file(new_ip):
    """Update backend/.env with new Redis URL"""
    env_path = "backend/.env"
    if not os.path.exists(env_path):
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace Redis URL
    import re
    new_content = re.sub(
        r'REDIS_URL=redis://[^:]+:6379',
        f'REDIS_URL=redis://{new_ip}:6379',
        content
    )
    
    with open(env_path, 'w') as f:
        f.write(new_content)
    
    return True

def main():
    print("🔥 Final Redis Fix and Test")
    print("=" * 40)
    
    # Test current Redis connection
    current_ip = "172.20.240.1"
    print(f"1. Testing current Redis at {current_ip}:6379...")
    
    if test_redis_connection(current_ip):
        print("   ✅ Redis is already working!")
        return True
    else:
        print("   ❌ Redis connection failed")
    
    # Get WSL2 IP
    print("\n2. Getting WSL2 IP address...")
    wsl_ip = get_wsl_ip()
    
    if not wsl_ip:
        print("   ❌ Failed to get WSL2 IP - WSL2 may not be running")
        print("   💡 Try: wsl --shutdown && wsl")
        return False
    
    print(f"   WSL2 IP: {wsl_ip}")
    
    # Test Redis at WSL IP
    print(f"\n3. Testing Redis at WSL2 IP {wsl_ip}:6379...")
    if test_redis_connection(wsl_ip):
        print("   ✅ Redis is working at WSL2 IP!")
        
        # Update .env file
        if wsl_ip != current_ip:
            print("\n4. Updating backend/.env...")
            if update_env_file(wsl_ip):
                print(f"   ✅ Updated REDIS_URL to redis://{wsl_ip}:6379")
            else:
                print("   ❌ Failed to update .env file")
        
        return True
    else:
        print("   ❌ Redis not responding at WSL2 IP")
    
    # Try to fix and start Redis
    print("\n5. Attempting to fix and start Redis...")
    fix_and_start_redis()
    time.sleep(3)
    
    # Test again
    print(f"\n6. Testing Redis after fix attempt...")
    if test_redis_connection(wsl_ip):
        print("   ✅ Redis is now working!")
        
        # Update .env file
        print("\n7. Updating backend/.env...")
        if update_env_file(wsl_ip):
            print(f"   ✅ Updated REDIS_URL to redis://{wsl_ip}:6379")
        else:
            print("   ❌ Failed to update .env file")
        
        # Final test with operations
        print("\n8. Testing Redis operations...")
        try:
            r = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_timeout=3)
            r.set("test_key", "success")
            if r.get("test_key") == "success":
                print("   ✅ Redis read/write operations working!")
                r.delete("test_key")
                
                print("\n" + "=" * 40)
                print("🎉 Redis fix completed successfully!")
                print(f"✅ Redis running at: {wsl_ip}:6379")
                print("✅ Backend .env updated")
                print("✅ Connection and operations tested")
                print("\n📝 Next steps:")
                print("   1. Restart your backend server")
                print("   2. Test your application")
                return True
            else:
                print("   ❌ Redis read/write operations failed")
        except Exception as e:
            print(f"   ❌ Redis operations test failed: {e}")
    else:
        print("   ❌ Redis still not working after fix attempt")
    
    print("\n💥 Redis fix failed. Manual steps required:")
    print("   1. wsl --shutdown")
    print("   2. wsl")
    print("   3. sudo apt update && sudo apt install redis-server")
    print("   4. sudo systemctl start redis-server")
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)