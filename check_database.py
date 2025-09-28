#!/usr/bin/env python3
"""
Check what's in the users database
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import get_collection

async def check_users():
    try:
        users_collection = await get_collection('users')
        users = await users_collection.find({}).to_list(length=20)
        print('Users in database:')
        for user in users:
            email = user.get('email', 'no email')
            created = user.get('created_at', 'no date')
            print(f'  - {email} (created: {created})')
        print(f'Total users: {len(users)}')
        
        # Check specific emails
        test_emails = ['test@example.com', 'brandnew12345@example.com', 'strongpass@example.com']
        for email in test_emails:
            user = await users_collection.find_one({'email': email})
            exists = 'EXISTS' if user else 'NOT FOUND'
            print(f'Email {email}: {exists}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(check_users())