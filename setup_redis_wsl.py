#!/usr/bin/env python3
"""
Complete Redis WSL2 setup script for Windows application connectivity
"""

import subprocess
import os
import time
import sys

def run_wsl_command(command, check=True):
    """Run a command in WSL2 Ubuntu"""
    try:
        full_command = f"wsl -d Ubuntu -- {command}"
        print(f"Running: {full_command}")
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        if check and result.returncode != 0:
            print(f"Command failed: {result.stderr}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def get_wsl_ip():
    """Get WSL2 IP address"""
    print("Getting WSL2 IP address...")
    ip_output = run_wsl_command("hostname -I", check=False)
    if ip_output:
        ip = ip_output.split()[0]  # Get first IP
        print(f"WSL2 IP: {ip}")
        return ip
    
    # Alternative method
    ip_output = run_wsl_command("ip route show default | awk '{print $3}'", check=False)
    if ip_output:
        print(f"WSL2 IP (alternative): {ip_output}")
        return ip_output
    
    print("Could not determine WSL2 IP address")
    return None

def setup_redis():
    """Setup Redis in WSL2"""
    print("Setting up Redis in WSL2...")
    
    # Stop any existing Redis instances
    print("Stopping existing Redis instances...")
    run_wsl_command("sudo pkill redis-server", check=False)
    run_wsl_command("sudo systemctl stop redis-server", check=False)
    
    # Backup original config
    print("Backing up Redis configuration...")
    run_wsl_command("sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup", check=False)
    
    # Configure Redis to bind to all interfaces
    print("Configuring Redis to bind to all interfaces...")
    commands = [
        "sudo sed -i 's/^bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf",
        "sudo sed -i 's/^# bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf",
        "sudo sed -i 's/^bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf",
        "sudo sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf",
        "sudo sed -i 's/^# protected-mode yes/protected-mode no/' /etc/redis/redis.conf"
    ]
    
    for cmd in commands:
        run_wsl_command(cmd, check=False)
    
    # Enable Redis service
    print("Enabling Redis service...")
    run_wsl_command("sudo systemctl enable redis-server", check=False)
    
    # Start Redis
    print("Starting Redis server...")
    run_wsl_command("sudo systemctl start redis-server", check=False)
    
    # Wait a moment for Redis to start
    time.sleep(3)
    
    # Test Redis locally in WSL
    print("Testing Redis locally in WSL...")
    result = run_wsl_command("redis-cli ping", check=False)
    if result and "PONG" in result:
        print("✅ Redis is running locally in WSL")
        return True
    else:
        print("❌ Redis is not responding locally in WSL")
        return False

def test_redis_connectivity(wsl_ip):
    """Test Redis connectivity from Windows"""
    print(f"Testing Redis connectivity from Windows to {wsl_ip}:6379...")
    
    try:
        import redis
        # Test connection to WSL Redis
        client = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_connect_timeout=5)
        result = client.ping()
        if result:
            print("✅ Redis connection from Windows successful!")
            return True
        else:
            print("❌ Redis ping failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def update_backend_env(wsl_ip):
    """Update backend .env file with WSL2 Redis URL"""
    print("Updating backend .env file...")
    
    env_path = "backend/.env"
    env_example_path = "backend/.env.example"
    
    # Read current .env or create from example
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    elif os.path.exists(env_example_path):
        with open(env_example_path, 'r') as f:
            lines = f.readlines()
    else:
        print("No .env or .env.example file found")
        return False
    
    # Update Redis URL
    new_lines = []
    redis_url_updated = False
    
    for line in lines:
        if line.startswith('REDIS_URL='):
            new_lines.append(f'REDIS_URL=redis://{wsl_ip}:6379\n')
            redis_url_updated = True
            print(f"Updated REDIS_URL to redis://{wsl_ip}:6379")
        else:
            new_lines.append(line)
    
    # Add Redis URL if not found
    if not redis_url_updated:
        new_lines.append(f'REDIS_URL=redis://{wsl_ip}:6379\n')
        print(f"Added REDIS_URL=redis://{wsl_ip}:6379")
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Backend .env updated with Redis URL: redis://{wsl_ip}:6379")
    return True

def main():
    """Main setup function"""
    print("🚀 Starting Redis WSL2 setup for Windows application connectivity...")
    
    # Step 1: Setup Redis in WSL2
    if not setup_redis():
        print("❌ Redis setup failed")
        return False
    
    # Step 2: Get WSL2 IP address
    wsl_ip = get_wsl_ip()
    if not wsl_ip:
        print("❌ Could not get WSL2 IP address")
        return False
    
    # Step 3: Test connectivity
    if not test_redis_connectivity(wsl_ip):
        print("❌ Redis connectivity test failed")
        return False
    
    # Step 4: Update backend configuration
    if not update_backend_env(wsl_ip):
        print("❌ Failed to update backend configuration")
        return False
    
    print("\n🎉 Redis WSL2 setup completed successfully!")
    print(f"📍 WSL2 IP: {wsl_ip}")
    print(f"🔗 Redis URL: redis://{wsl_ip}:6379")
    print("\n📋 Next steps:")
    print("1. Restart your backend application to use the new Redis configuration")
    print("2. Test Redis-dependent features (rate limiting, caching, token blacklisting)")
    print("3. Verify that Redis warnings are resolved in backend logs")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)