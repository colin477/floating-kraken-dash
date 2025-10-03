#!/usr/bin/env python3
"""
Complete Redis WSL2 Fix Script
Fixes Redis connectivity issues in WSL2 and updates backend configuration
"""

import subprocess
import os
import re
import time
import redis
from pathlib import Path

def run_wsl_command(command, timeout=10):
    """Run a command in WSL2 Ubuntu with timeout"""
    try:
        full_command = f'wsl -d Ubuntu -- bash -c "{command}"'
        result = subprocess.run(
            full_command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e)

def get_wsl_ip():
    """Get WSL2 IP address"""
    success, output, error = run_wsl_command("hostname -I")
    if success and output:
        # Get the first IP address
        ip = output.split()[0] if output.split() else None
        return ip
    return None

def fix_redis_config():
    """Fix Redis configuration to bind to all interfaces"""
    print("🔧 Fixing Redis configuration...")
    
    # Stop Redis service
    print("  Stopping Redis service...")
    run_wsl_command("sudo systemctl stop redis-server")
    run_wsl_command("sudo pkill redis-server")
    time.sleep(2)
    
    # Backup original config
    run_wsl_command("sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup")
    
    # Update bind configuration
    print("  Updating bind configuration...")
    run_wsl_command("sudo sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf")
    
    # Ensure protected mode is off for external connections
    run_wsl_command("sudo sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf")
    
    # Set daemonize to yes
    run_wsl_command("sudo sed -i 's/^daemonize no/daemonize yes/' /etc/redis/redis.conf")
    
    return True

def start_redis():
    """Start Redis service"""
    print("🚀 Starting Redis service...")
    
    # Try systemctl first
    success, _, _ = run_wsl_command("sudo systemctl start redis-server")
    if success:
        time.sleep(2)
        # Check if it's running
        success, _, _ = run_wsl_command("sudo systemctl is-active redis-server")
        if success:
            print("  ✅ Redis started via systemctl")
            return True
    
    # If systemctl fails, try direct redis-server
    print("  Trying direct redis-server start...")
    success, _, _ = run_wsl_command("sudo redis-server /etc/redis/redis.conf --daemonize yes")
    time.sleep(2)
    
    # Check if Redis is responding
    success, output, _ = run_wsl_command("redis-cli ping")
    if success and "PONG" in output:
        print("  ✅ Redis started directly")
        return True
    
    print("  ❌ Failed to start Redis")
    return False

def test_redis_local():
    """Test Redis locally in WSL2"""
    print("🧪 Testing Redis locally in WSL2...")
    success, output, error = run_wsl_command("redis-cli ping")
    if success and "PONG" in output:
        print("  ✅ Redis responding locally")
        return True
    else:
        print(f"  ❌ Redis not responding locally: {error}")
        return False

def update_backend_env(wsl_ip):
    """Update backend .env file with correct Redis URL"""
    print(f"📝 Updating backend/.env with Redis URL: redis://{wsl_ip}:6379")
    
    env_path = Path("backend/.env")
    
    # Read current .env file
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Update or add Redis URL
    redis_url = f"redis://{wsl_ip}:6379"
    
    if "REDIS_URL=" in env_content:
        # Replace existing REDIS_URL
        env_content = re.sub(r'REDIS_URL=.*', f'REDIS_URL={redis_url}', env_content)
    else:
        # Add REDIS_URL
        env_content += f"\nREDIS_URL={redis_url}\n"
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"  ✅ Updated backend/.env with REDIS_URL={redis_url}")
    return True

def test_redis_from_windows(wsl_ip):
    """Test Redis connectivity from Windows"""
    print(f"🌐 Testing Redis connectivity from Windows to {wsl_ip}:6379...")
    
    try:
        # Test with redis-py
        r = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_timeout=5)
        response = r.ping()
        if response:
            print("  ✅ Redis connection successful from Windows!")
            
            # Test basic operations
            r.set("test_key", "test_value")
            value = r.get("test_key")
            if value == "test_value":
                print("  ✅ Redis read/write operations working!")
                r.delete("test_key")
                return True
            else:
                print("  ❌ Redis read/write operations failed")
                return False
        else:
            print("  ❌ Redis ping failed")
            return False
    except redis.ConnectionError as e:
        print(f"  ❌ Redis connection failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def main():
    """Main fix function"""
    print("🔥 Redis WSL2 Complete Fix Script")
    print("=" * 50)
    
    # Step 1: Get WSL2 IP
    print("\n1️⃣ Getting WSL2 IP address...")
    wsl_ip = get_wsl_ip()
    if not wsl_ip:
        print("❌ Failed to get WSL2 IP address")
        return False
    print(f"  ✅ WSL2 IP: {wsl_ip}")
    
    # Step 2: Fix Redis configuration
    print("\n2️⃣ Fixing Redis configuration...")
    if not fix_redis_config():
        print("❌ Failed to fix Redis configuration")
        return False
    
    # Step 3: Start Redis
    print("\n3️⃣ Starting Redis service...")
    if not start_redis():
        print("❌ Failed to start Redis service")
        return False
    
    # Step 4: Test Redis locally
    print("\n4️⃣ Testing Redis locally...")
    if not test_redis_local():
        print("❌ Redis local test failed")
        return False
    
    # Step 5: Update backend .env
    print("\n5️⃣ Updating backend configuration...")
    if not update_backend_env(wsl_ip):
        print("❌ Failed to update backend .env")
        return False
    
    # Step 6: Test from Windows
    print("\n6️⃣ Testing Redis from Windows...")
    if not test_redis_from_windows(wsl_ip):
        print("❌ Redis Windows connectivity test failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Redis WSL2 fix completed successfully!")
    print(f"✅ Redis is running at: {wsl_ip}:6379")
    print("✅ Backend .env updated")
    print("✅ Connection test passed")
    print("\nYou can now restart your backend server to use Redis.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Redis fix failed. Check the output above for details.")
            exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)