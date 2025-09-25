#!/usr/bin/env python3
"""
Script to fix MongoDB index conflicts by updating index creation logic
"""

import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

async def fix_index_conflicts():
    """Fix index conflicts by using existing index names or dropping conflicting ones"""
    try:
        # Connect to MongoDB
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "ez_eatin")
        
        client = AsyncIOMotorClient(mongodb_uri)
        database = client[database_name]
        
        print("Connected to MongoDB. Fixing index conflicts...")
        
        # Fix users collection - use existing email_1 index
        users_collection = database["users"]
        print("\n=== USERS COLLECTION ===")
        indexes = await users_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Existing: {idx['name']}: {idx.get('key', {})}")
        
        # Fix pantry_items collection - use existing user_id_category_index
        pantry_collection = database["pantry_items"]
        print("\n=== PANTRY_ITEMS COLLECTION ===")
        indexes = await pantry_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Existing: {idx['name']}: {idx.get('key', {})}")
        
        # Fix recipes collection - use existing text_search_index
        recipes_collection = database["recipes"]
        print("\n=== RECIPES COLLECTION ===")
        indexes = await recipes_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Existing: {idx['name']}: {idx.get('key', {})}")
        
        # Fix shopping_lists collection - use existing user_id_1
        shopping_lists_collection = database["shopping_lists"]
        print("\n=== SHOPPING_LISTS COLLECTION ===")
        indexes = await shopping_lists_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Existing: {idx['name']}: {idx.get('key', {})}")
        
        # Fix community_posts collection - use existing created_at_-1
        community_posts_collection = database["community_posts"]
        print("\n=== COMMUNITY_POSTS COLLECTION ===")
        indexes = await community_posts_collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"Existing: {idx['name']}: {idx.get('key', {})}")
        
        print("\nIndex analysis complete. The database.py file needs to be updated to use existing index names.")
        
        client.close()
        
    except Exception as e:
        print(f"Error fixing index conflicts: {e}")

if __name__ == "__main__":
    asyncio.run(fix_index_conflicts())