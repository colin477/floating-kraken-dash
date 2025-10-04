#!/usr/bin/env python3
"""
Final connection stability test for MongoDB SSL/TLS configuration
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_connection_stability():
    """Test connection stability with multiple attempts"""
    print("🔄 MongoDB Connection Stability Test")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv(os.path.join('backend', '.env'))
    
    try:
        from app.middleware.performance import DatabasePoolConfig
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongodb_uri = os.getenv("MONGODB_URI")
        options = DatabasePoolConfig.get_connection_options()
        
        print(f"Testing with {len(options)} connection options")
        print(f"TLS enabled: {options.get('tls', False)}")
        
        # Test multiple connections
        num_tests = 5
        successful = 0
        failed = 0
        times = []
        
        for i in range(num_tests):
            try:
                print(f"\n🔄 Test {i+1}/{num_tests}:")
                
                start_time = time.time()
                client = AsyncIOMotorClient(mongodb_uri, **options)
                
                # Test ping
                await client.admin.command('ping')
                connection_time = time.time() - start_time
                times.append(connection_time)
                
                print(f"   ✅ Connection successful ({connection_time:.3f}s)")
                successful += 1
                
                # Test a simple operation
                server_info = await client.server_info()
                print(f"   ✅ Server version: {server_info.get('version')}")
                
                # Small delay between tests
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"   ❌ Connection {i+1} failed: {e}")
                failed += 1
        
        # Results
        print("\n" + "=" * 40)
        print("📊 STABILITY TEST RESULTS")
        print("=" * 40)
        print(f"Total tests: {num_tests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/num_tests)*100:.1f}%")
        
        if times:
            print(f"Average connection time: {sum(times)/len(times):.3f}s")
            print(f"Fastest connection: {min(times):.3f}s")
            print(f"Slowest connection: {max(times):.3f}s")
        
        # Determine if stable
        stable = (successful / num_tests) >= 0.8  # 80% success rate
        print(f"\n{'✅' if stable else '❌'} Connection stability: {'STABLE' if stable else 'UNSTABLE'}")
        
        return stable
        
    except Exception as e:
        print(f"❌ Stability test failed: {e}")
        return False

async def main():
    """Main test function"""
    stable = await test_connection_stability()
    
    if stable:
        print("\n🎉 MongoDB SSL/TLS configuration is stable and working correctly!")
    else:
        print("\n⚠️  MongoDB connection stability issues detected.")
    
    return stable

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)