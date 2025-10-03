#!/usr/bin/env python3
"""
Final Redis test - comprehensive check and setup
"""

import subprocess
import os
import time

def run_cmd_quick(cmd):
    """Run command with short timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""

def main():
    print("🔍 Final Redis Test")
    print("=" * 25)
    
    # Quick test: Get WSL IP
    print("Getting WSL IP...")
    success, output = run_cmd_quick('wsl -d Ubuntu -- hostname -I')
    if success and output:
        wsl_ip = output.split()[0]
        print(f"WSL IP: {wsl_ip}")
    else:
        print("❌ Could not get WSL IP")
        return False
    
    # Test Redis from Windows directly
    print("Testing Redis from Windows...")
    try:
        import redis
        
        # Try connecting to WSL Redis
        client = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_connect_timeout=3)
        result = client.ping()
        
        if result:
            print("✅ Redis is accessible from Windows!")
            
            # Test operations
            client.set("test", "working")
            value = client.get("test")
            if value == "working":
                print("✅ Redis operations working")
                client.delete("test")
            
            # Update backend .env
            print("Updating backend .env...")
            redis_url = f"redis://{wsl_ip}:6379"
            
            env_path = "backend/.env"
            if os.path.exists("backend/.env.example") and not os.path.exists(env_path):
                # Copy from example
                with open("backend/.env.example", 'r') as f:
                    content = f.read()
                with open(env_path, 'w') as f:
                    f.write(content)
            
            # Update Redis URL
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                updated = False
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
                
                print(f"✅ Updated REDIS_URL={redis_url}")
            else:
                # Create new .env
                with open(env_path, 'w') as f:
                    f.write(f'REDIS_URL={redis_url}\n')
                print(f"✅ Created .env with REDIS_URL={redis_url}")
            
            print("\n🎉 Redis setup complete!")
            print(f"Redis URL: {redis_url}")
            print("Restart your backend to use Redis.")
            return True
            
        else:
            print("❌ Redis ping failed")
            return False
            
    except ImportError:
        print("❌ Redis library not available")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        
        # Try to configure and start Redis
        print("Attempting to configure Redis...")
        
        commands = [
            'wsl -d Ubuntu -- sudo pkill redis-server',
            'wsl -d Ubuntu -- sudo sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf',
            'wsl -d Ubuntu -- sudo sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf',
            'wsl -d Ubuntu -- sudo systemctl start redis-server'
        ]
        
        for cmd in commands:
            run_cmd_quick(cmd)
        
        time.sleep(3)
        
        # Try again
        try:
            client = redis.Redis(host=wsl_ip, port=6379, decode_responses=True, socket_connect_timeout=3)
            if client.ping():
                print("✅ Redis now working after configuration!")
                
                # Update .env
                redis_url = f"redis://{wsl_ip}:6379"
                env_path = "backend/.env"
                
                if not os.path.exists(env_path) and os.path.exists("backend/.env.example"):
                    with open("backend/.env.example", 'r') as f:
                        content = f.read()
                    with open(env_path, 'w') as f:
                        f.write(content)
                
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    if 'REDIS_URL=' in content:
                        # Replace existing
                        lines = content.split('\n')
                        new_lines = []
                        for line in lines:
                            if line.startswith('REDIS_URL='):
                                new_lines.append(f'REDIS_URL={redis_url}')
                            else:
                                new_lines.append(line)
                        content = '\n'.join(new_lines)
                    else:
                        # Add new
                        content += f'\nREDIS_URL={redis_url}\n'
                    
                    with open(env_path, 'w') as f:
                        f.write(content)
                else:
                    with open(env_path, 'w') as f:
                        f.write(f'REDIS_URL={redis_url}\n')
                
                print(f"✅ Updated REDIS_URL={redis_url}")
                print("\n🎉 Redis setup complete!")
                print("Restart your backend to use Redis.")
                return True
            else:
                print("❌ Redis still not working")
                return False
        except Exception as e2:
            print(f"❌ Still failed: {e2}")
            return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Redis setup failed")
        print("Manual steps needed:")
        print("1. wsl -d Ubuntu -- sudo systemctl start redis-server")
        print("2. wsl -d Ubuntu -- sudo sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf")
        print("3. wsl -d Ubuntu -- sudo systemctl restart redis-server")