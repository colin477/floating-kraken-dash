#!/usr/bin/env python3
"""
Test Redis WSL2 connectivity and provide diagnostic information
"""

import subprocess
import sys
import time

def run_command(command, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_wsl_connectivity():
    """Test basic WSL connectivity"""
    print("🔍 Testing WSL connectivity...")
    
    # Test WSL basic connectivity
    code, stdout, stderr = run_command("wsl -d Ubuntu -- echo 'WSL is working'")
    if code == 0:
        print("✅ WSL Ubuntu is accessible")
    else:
        print(f"❌ WSL Ubuntu not accessible: {stderr}")
        return False
    
    return True

def get_wsl_ip():
    """Get WSL IP address using multiple methods"""
    print("🔍 Getting WSL IP address...")
    
    methods = [
        "wsl -d Ubuntu -- hostname -I",
        "wsl -d Ubuntu -- ip route show default | head -1",
        "wsl -d Ubuntu -- cat /etc/resolv.conf | grep nameserver | head -1"
    ]
    
    for method in methods:
        print(f"Trying: {method}")
        code, stdout, stderr = run_command(method)
        if code == 0 and stdout:
            if "hostname -I" in method:
                ip = stdout.split()[0] if stdout.split() else None
                if ip:
                    print(f"✅ WSL IP found: {ip}")
                    return ip
            elif "ip route" in method:
                parts = stdout.split()
                if len(parts) >= 3:
                    ip = parts[2]
                    print(f"✅ WSL Gateway IP: {ip}")
                    return ip
            elif "resolv.conf" in method:
                parts = stdout.split()
                if len(parts) >= 2:
                    ip = parts[1]
                    print(f"✅ WSL DNS IP: {ip}")
                    return ip
    
    print("❌ Could not determine WSL IP")
    return None

def test_redis_in_wsl():
    """Test if Redis is running in WSL"""
    print("🔍 Testing Redis in WSL...")
    
    # Check if Redis is installed
    code, stdout, stderr = run_command("wsl -d Ubuntu -- which redis-server")
    if code != 0:
        print("❌ Redis server not found in WSL")
        return False
    else:
        print("✅ Redis server found in WSL")
    
    # Check if Redis CLI is available
    code, stdout, stderr = run_command("wsl -d Ubuntu -- which redis-cli")
    if code != 0:
        print("❌ Redis CLI not found in WSL")
        return False
    else:
        print("✅ Redis CLI found in WSL")
    
    # Test Redis ping
    code, stdout, stderr = run_command("wsl -d Ubuntu -- redis-cli ping")
    if code == 0 and "PONG" in stdout:
        print("✅ Redis is responding in WSL")
        return True
    else:
        print(f"❌ Redis not responding in WSL: {stderr}")
        return False

def test_redis_from_windows(wsl_ip):
    """Test Redis connectivity from Windows"""
    if not wsl_ip:
        print("❌ No WSL IP provided for testing")
        return False
    
    print(f"🔍 Testing Redis connectivity from Windows to {wsl_ip}:6379...")
    
    try:
        import redis
        client = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_connect_timeout=3)
        result = client.ping()
        if result:
            print("✅ Redis connection from Windows successful!")
            return True
        else:
            print("❌ Redis ping failed from Windows")
            return False
    except ImportError:
        print("❌ Redis Python library not installed")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed from Windows: {e}")
        return False

def check_redis_config():
    """Check Redis configuration"""
    print("🔍 Checking Redis configuration...")
    
    # Check bind configuration
    code, stdout, stderr = run_command("wsl -d Ubuntu -- grep -E '^bind|^# bind' /etc/redis/redis.conf")
    if code == 0:
        print("Redis bind configuration:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"  {line}")
    
    # Check protected mode
    code, stdout, stderr = run_command("wsl -d Ubuntu -- grep -E '^protected-mode|^# protected-mode' /etc/redis/redis.conf")
    if code == 0:
        print("Redis protected-mode configuration:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"  {line}")

def main():
    """Main diagnostic function"""
    print("🚀 Redis WSL2 Connectivity Diagnostic Tool")
    print("=" * 50)
    
    # Test WSL connectivity
    if not test_wsl_connectivity():
        print("❌ WSL connectivity failed. Cannot proceed.")
        return False
    
    print()
    
    # Get WSL IP
    wsl_ip = get_wsl_ip()
    print()
    
    # Check Redis configuration
    check_redis_config()
    print()
    
    # Test Redis in WSL
    redis_in_wsl = test_redis_in_wsl()
    print()
    
    # Test Redis from Windows
    if wsl_ip:
        redis_from_windows = test_redis_from_windows(wsl_ip)
    else:
        redis_from_windows = False
    
    print()
    print("=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"WSL IP Address: {wsl_ip or 'Not found'}")
    print(f"Redis in WSL: {'✅ Working' if redis_in_wsl else '❌ Not working'}")
    print(f"Redis from Windows: {'✅ Working' if redis_from_windows else '❌ Not working'}")
    
    if redis_from_windows:
        print("\n🎉 Redis is fully operational!")
        print(f"Use this Redis URL in your backend: redis://{wsl_ip}:6379")
    else:
        print("\n⚠️ Redis setup needs attention:")
        if not redis_in_wsl:
            print("- Redis is not running properly in WSL")
        if wsl_ip and not redis_from_windows:
            print("- Redis is not accessible from Windows (likely configuration issue)")
        if not wsl_ip:
            print("- Could not determine WSL IP address")
    
    return redis_from_windows

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)