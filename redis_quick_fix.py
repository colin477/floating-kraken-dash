#!/usr/bin/env python3
"""
Quick Redis Fix - Direct approach
"""

import subprocess
import time
import redis
import os

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""

print("🔥 Quick Redis Fix Starting...")

# Step 1: Kill any existing Redis processes
print("1. Stopping existing Redis processes...")
run_cmd('wsl -d Ubuntu -- sudo pkill redis-server')
time.sleep(2)

# Step 2: Get WSL IP
print("2. Getting WSL2 IP...")
success, wsl_ip = run_cmd('wsl -d Ubuntu -- hostname -I')
if success and wsl_ip:
    wsl_ip = wsl_ip.split()[0]
    print(f"   WSL2 IP: {wsl_ip}")
else:
    print("   ❌ Failed to get WSL IP")
    exit(1)

# Step 3: Fix Redis config
print("3. Fixing Redis configuration...")
run_cmd('wsl -d Ubuntu -- sudo sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf')
run_cmd('wsl -d Ubuntu -- sudo sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf')

# Step 4: Start Redis directly
print("4. Starting Redis server...")
success, _ = run_cmd('wsl -d Ubuntu -- sudo redis-server /etc/redis/redis.conf --daemonize yes')
time.sleep(3)

# Step 5: Test local connection
print("5. Testing local Redis connection...")
success, output = run_cmd('wsl -d Ubuntu -- redis-cli ping')
if success and "PONG" in output:
    print("   ✅ Redis responding locally")
else:
    print("   ❌ Redis not responding locally")
    exit(1)

# Step 6: Update backend .env
print("6. Updating backend/.env...")
env_path = "backend/.env"
redis_url = f"redis://{wsl_ip}:6379"

# Read existing .env
env_content = ""
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        env_content = f.read()

# Update Redis URL
if "REDIS_URL=" in env_content:
    lines = env_content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('REDIS_URL='):
            lines[i] = f'REDIS_URL={redis_url}'
    env_content = '\n'.join(lines)
else:
    env_content += f'\nREDIS_URL={redis_url}\n'

# Write updated .env
with open(env_path, 'w') as f:
    f.write(env_content)

print(f"   Updated REDIS_URL={redis_url}")

# Step 7: Test Windows connection
print("7. Testing Redis from Windows...")
try:
    r = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_timeout=5)
    if r.ping():
        print("   ✅ Redis connection successful!")
        
        # Test operations
        r.set("test", "success")
        if r.get("test") == "success":
            print("   ✅ Redis read/write working!")
            r.delete("test")
        else:
            print("   ❌ Redis read/write failed")
    else:
        print("   ❌ Redis ping failed")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

print("\n🎉 Redis fix completed successfully!")
print(f"✅ Redis running at: {wsl_ip}:6379")
print("✅ Backend .env updated")
print("✅ Connection test passed")
print("\nRestart your backend server to use Redis.")