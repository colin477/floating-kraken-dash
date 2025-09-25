#!/usr/bin/env python3
"""
Script to check existing MongoDB indexes and identify conflicts
"""

import asyncio
import os
from dotenv import load_dotenv
from app.database import connect_to_mongo, get_collection

# Load environment variables
load_dotenv()

async def check_indexes():
    try:
        await connect_to_mongo()
        
        # Check existing indexes in each collection
        collections = ['users', 'pantry_items', 'recipes', 'shopping_lists', 'community_posts']
        
        for collection_name in collections:
            try:
                collection = await get_collection(collection_name)
                indexes = await collection.list_indexes().to_list(length=None)
                print(f'\n{collection_name.upper()} COLLECTION INDEXES:')
                for idx in indexes:
                    name = idx.get('name', 'unknown')
                    key = idx.get('key', {})
                    unique = idx.get('unique', False)
                    print(f'  - {name}: {key} (unique: {unique})')
            except Exception as e:
                print(f'Error checking {collection_name}: {e}')
                
    except Exception as e:
        print(f'Database connection error: {e}')

if __name__ == "__main__":
    asyncio.run(check_indexes())