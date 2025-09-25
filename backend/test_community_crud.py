"""
Test script for Community CRUD operations (Comments and Likes)
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongo, close_mongo_connection
from app.crud.community import (
    create_community_post,
    create_comment,
    get_comment,
    get_post_comments,
    get_comment_replies,
    update_comment,
    delete_comment,
    create_like,
    delete_like,
    get_user_like,
    get_target_likes,
    increment_comment_likes,
    decrement_comment_likes
)
from app.models.community import (
    CommunityPostCreate,
    CommentCreate,
    CommentUpdate,
    LikeCreate,
    PostType,
    TargetType
)

async def test_community_crud():
    """Test Community CRUD operations for comments and likes"""
    try:
        # Connect to database
        await connect_to_mongo()
        print("✅ Connected to database")
        
        # Test data
        test_user_id = "test_user_123"
        test_user_id_2 = "test_user_456"
        
        # 1. Create a test post first
        print("\n🧪 Testing Post Creation...")
        post_data = CommunityPostCreate(
            title="Test Post for Comments",
            content="This is a test post to test comments and likes",
            post_type=PostType.GENERAL,
            tags=["test", "crud"]
        )
        
        test_post = await create_community_post(None, post_data, test_user_id)
        if test_post:
            print(f"✅ Created test post: {test_post.id}")
            post_id = test_post.id
        else:
            print("❌ Failed to create test post")
            return
        
        # 2. Test Comment CRUD Operations
        print("\n🧪 Testing Comment CRUD Operations...")
        
        # Create comment
        comment_data = CommentCreate(
            content="This is a test comment on the post"
        )
        
        test_comment = await create_comment(None, comment_data, test_user_id, post_id)
        if test_comment:
            print(f"✅ Created comment: {test_comment.id}")
            comment_id = test_comment.id
        else:
            print("❌ Failed to create comment")
            return
        
        # Get comment
        retrieved_comment = await get_comment(None, comment_id)
        if retrieved_comment and retrieved_comment.content == comment_data.content:
            print("✅ Retrieved comment successfully")
        else:
            print("❌ Failed to retrieve comment")
        
        # Get post comments
        post_comments = await get_post_comments(None, post_id, skip=0, limit=10)
        if post_comments and len(post_comments.comments) > 0:
            print(f"✅ Retrieved {len(post_comments.comments)} comments for post")
        else:
            print("❌ Failed to retrieve post comments")
        
        # Create a reply comment
        reply_data = CommentCreate(
            content="This is a reply to the first comment",
            parent_comment_id=comment_id
        )
        
        reply_comment = await create_comment(None, reply_data, test_user_id_2, post_id)
        if reply_comment:
            print(f"✅ Created reply comment: {reply_comment.id}")
            reply_id = reply_comment.id
        else:
            print("❌ Failed to create reply comment")
            return
        
        # Get comment replies
        comment_replies = await get_comment_replies(None, comment_id, skip=0, limit=10)
        if comment_replies and len(comment_replies.comments) > 0:
            print(f"✅ Retrieved {len(comment_replies.comments)} replies for comment")
        else:
            print("❌ Failed to retrieve comment replies")
        
        # Update comment
        update_data = CommentUpdate(content="Updated comment content")
        updated_comment = await update_comment(None, comment_id, update_data, test_user_id)
        if updated_comment and updated_comment.content == "Updated comment content":
            print("✅ Updated comment successfully")
        else:
            print("❌ Failed to update comment")
        
        # 3. Test Like CRUD Operations
        print("\n🧪 Testing Like CRUD Operations...")
        
        # Create like on post
        post_like_data = LikeCreate(
            target_type=TargetType.POST,
            target_id=post_id
        )
        
        post_like = await create_like(None, post_like_data, test_user_id)
        if post_like:
            print(f"✅ Created like on post: {post_like.id}")
        else:
            print("❌ Failed to create like on post")
        
        # Create like on comment
        comment_like_data = LikeCreate(
            target_type=TargetType.COMMENT,
            target_id=comment_id
        )
        
        comment_like = await create_like(None, comment_like_data, test_user_id_2)
        if comment_like:
            print(f"✅ Created like on comment: {comment_like.id}")
        else:
            print("❌ Failed to create like on comment")
        
        # Get user like
        user_post_like = await get_user_like(None, test_user_id, TargetType.POST, post_id)
        if user_post_like:
            print("✅ Retrieved user like on post")
        else:
            print("❌ Failed to retrieve user like on post")
        
        # Get target likes
        post_likes = await get_target_likes(None, TargetType.POST, post_id, skip=0, limit=10)
        if post_likes and len(post_likes) > 0:
            print(f"✅ Retrieved {len(post_likes)} likes for post")
        else:
            print("❌ Failed to retrieve post likes")
        
        # 4. Test Comment Interaction Functions
        print("\n🧪 Testing Comment Interaction Functions...")
        
        # Test increment comment likes
        increment_result = await increment_comment_likes(None, comment_id)
        if increment_result:
            print("✅ Incremented comment likes")
        else:
            print("❌ Failed to increment comment likes")
        
        # Test decrement comment likes
        decrement_result = await decrement_comment_likes(None, comment_id)
        if decrement_result:
            print("✅ Decremented comment likes")
        else:
            print("❌ Failed to decrement comment likes")
        
        # 5. Test Delete Operations
        print("\n🧪 Testing Delete Operations...")
        
        # Delete like
        delete_like_result = await delete_like(None, test_user_id, TargetType.POST, post_id)
        if delete_like_result:
            print("✅ Deleted like successfully")
        else:
            print("❌ Failed to delete like")
        
        # Delete comment (this should also delete replies)
        delete_comment_result = await delete_comment(None, comment_id, test_user_id)
        if delete_comment_result:
            print("✅ Deleted comment successfully")
        else:
            print("❌ Failed to delete comment")
        
        print("\n🎉 All Community CRUD tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database connection
        await close_mongo_connection()
        print("✅ Disconnected from database")

if __name__ == "__main__":
    asyncio.run(test_community_crud())