#!/usr/bin/env python3
"""
Direct Redis WSL2 fix - simple and focused approach
"""

import subprocess
import os
import time

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except:
        return False, "", "timeout"

def main():
    print("🔧 Direct Redis WSL2 Fix")
    print("=" * 30)
    
    # Step 1: Get WSL IP using simple method
    print("1. Getting WSL IP...")
    success, ip_output, _ = run_cmd('wsl -d Ubuntu -- hostname -I')
    if success and ip_output:
        wsl_ip = ip_output.split()[0]
        print(f"   WSL IP: {wsl_ip}")
    else:
        print("   ❌ Could not get WSL IP")
        return False
    
    # Step 2: Stop Redis
    print("2. Stopping Redis...")
    run_cmd('wsl -d Ubuntu -- sudo pkill redis-server')
    run_cmd('wsl -d Ubuntu -- sudo systemctl stop redis-server')
    time.sleep(2)
    
    # Step 3: Configure Redis
    print("3. Configuring Redis...")
    commands = [
        'wsl -d Ubuntu -- sudo sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf',
        'wsl -d Ubuntu -- sudo sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf'
    ]
    
    for cmd in commands:
        run_cmd(cmd)
    
    # Step 4: Start Redis
    print("4. Starting Redis...")
    success, _, _ = run_cmd('wsl -d Ubuntu -- sudo systemctl start redis-server')
    time.sleep(3)
    
    # Step 5: Test Redis in WSL
    print("5. Testing Redis in WSL...")
    success, output, _ = run_cmd('wsl -d Ubuntu -- redis-cli ping')
    if success and "PONG" in output:
        print("   ✅ Redis working in WSL")
    else:
        print("   ❌ Redis not working in WSL")
        return False
    
    # Step 6: Test from Windows
    print("6. Testing from Windows...")
    try:
        import redis
        client = redis.Redis(host=wsl_ip, port=6379, socket_connect_timeout=3)
        if client.ping():
            print("   ✅ Redis accessible from Windows")
        else:
            print("   ❌ Redis not accessible from Windows")
            return False
    except Exception as e:
        print(f"   ❌ Redis test failed: {e}")
        return False
    
    # Step 7: Update backend .env
    print("7. Updating backend .env...")
    env_path = "backend/.env"
    
    # Read existing .env or create from example
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    elif os.path.exists("backend/.env.example"):
        with open("backend/.env.example", 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add Redis URL
    new_lines = []
    redis_updated = False
    
    for line in lines:
        if line.startswith('REDIS_URL='):
            new_lines.append(f'REDIS_URL=redis://{wsl_ip}:6379\n')
            redis_updated = True
        else:
            new_lines.append(line)
    
    if not redis_updated:
        new_lines.append(f'REDIS_URL=redis://{wsl_ip}:6379\n')
    
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"   ✅ Updated REDIS_URL=redis://{wsl_ip}:6379")
    
    print("\n🎉 Redis setup complete!")
    print(f"Redis URL: redis://{wsl_ip}:6379")
    print("\nNext: Restart your backend to use Redis")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup failed")
            exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
        exit(1)