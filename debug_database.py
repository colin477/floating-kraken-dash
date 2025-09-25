#!/usr/bin/env python3
"""
Debug script to check database contents
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_collection

async def debug_database():
    """Check database contents"""
    try:
        # Check profiles collection
        profiles_collection = await get_collection("profiles")
        
        print("🔍 Checking profiles collection...")
        profiles = await profiles_collection.find({}).to_list(length=10)
        
        print(f"Found {len(profiles)} profiles:")
        for i, profile in enumerate(profiles):
            print(f"\nProfile {i+1}:")
            print(f"  _id: {profile.get('_id')}")
            print(f"  user_id: {profile.get('user_id')}")
            print(f"  family_members: {profile.get('family_members', [])}")
            print(f"  dietary_restrictions: {profile.get('dietary_restrictions', [])}")
            print(f"  weekly_budget: {profile.get('weekly_budget')}")
            
            # Check if family members have the required age field
            family_members = profile.get('family_members', [])
            for j, member in enumerate(family_members):
                print(f"    Family member {j+1}: {member}")
                if 'age' not in member:
                    print(f"    ❌ Missing 'age' field in family member {j+1}")
                elif member['age'] is None:
                    print(f"    ❌ 'age' field is None in family member {j+1}")
        
        # Check users collection
        users_collection = await get_collection("users")
        print(f"\n🔍 Checking users collection...")
        users = await users_collection.find({}).to_list(length=5)
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  User: {user.get('email')} (ID: {user.get('_id')})")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_database())