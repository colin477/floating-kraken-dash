#!/usr/bin/env python3
"""
Test script to verify MongoDB SSL/TLS connection stability over time
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_connection_stability(duration_seconds=60, interval_seconds=5):
    """Test connection stability over time"""
    print(f"Testing connection stability for {duration_seconds} seconds...")
    print(f"Checking every {interval_seconds} seconds\n")
    
    start_time = time.time()
    test_count = 0
    success_count = 0
    
    while time.time() - start_time < duration_seconds:
        test_count += 1
        try:
            response = requests.get(f"{BASE_URL}/healthz", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("database_connected", False):
                    success_count += 1
                    print(f"✅ Test {test_count}: Database connected - {data['status']}")
                else:
                    print(f"❌ Test {test_count}: Database not connected - {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ Test {test_count}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Test {test_count}: Connection failed - {e}")
        
        time.sleep(interval_seconds)
    
    success_rate = (success_count / test_count) * 100 if test_count > 0 else 0
    print(f"\n=== Connection Stability Results ===")
    print(f"Total tests: {test_count}")
    print(f"Successful connections: {success_count}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("✅ Connection is stable")
        return True
    else:
        print("❌ Connection is unstable")
        return False

def main():
    """Run connection stability test"""
    print("=== MongoDB SSL/TLS Connection Stability Test ===\n")
    
    # Test for 30 seconds with 3-second intervals
    stable = test_connection_stability(duration_seconds=30, interval_seconds=3)
    
    if stable:
        print("\n✅ MongoDB SSL/TLS connection is stable and reliable")
    else:
        print("\n❌ MongoDB SSL/TLS connection shows instability")
        sys.exit(1)

if __name__ == "__main__":
    main()