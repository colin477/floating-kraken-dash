"""
CRUD operations for community post management
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database import get_collection
from app.models.community import (
    CommunityPost,
    CommunityPostCreate,
    CommunityPostUpdate,
    CommunityPostResponse,
    CommunityPostsListResponse,
    CommunityStatsResponse,
    PostType,
    Comment,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentsListResponse,
    Like,
    LikeCreate,
    LikeResponse,
    TargetType
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_community_indexes():
    """
    Create database indexes for community collections
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        community_comments_collection = await get_collection("community_comments")
        community_likes_collection = await get_collection("community_likes")
        
        # Create indexes for community posts
        await community_posts_collection.create_index([("user_id", 1)])
        await community_posts_collection.create_index([("user_id", 1), ("post_type", 1)])
        await community_posts_collection.create_index([("post_type", 1)])
        await community_posts_collection.create_index([("is_public", 1)])
        await community_posts_collection.create_index([("created_at", -1)])
        await community_posts_collection.create_index([("likes_count", -1)])
        await community_posts_collection.create_index([("tags", 1)])
        await community_posts_collection.create_index([("recipe_id", 1)])
        
        # Create indexes for community comments
        await community_comments_collection.create_index([("post_id", 1)])
        await community_comments_collection.create_index([("user_id", 1)])
        await community_comments_collection.create_index([("parent_comment_id", 1)])
        await community_comments_collection.create_index([("post_id", 1), ("created_at", -1)])
        await community_comments_collection.create_index([("user_id", 1), ("created_at", -1)])
        await community_comments_collection.create_index([("created_at", -1)])
        
        # Create indexes for community likes
        await community_likes_collection.create_index([("user_id", 1)])
        await community_likes_collection.create_index([("target_type", 1)])
        await community_likes_collection.create_index([("target_id", 1)])
        await community_likes_collection.create_index([("user_id", 1), ("target_type", 1), ("target_id", 1)], unique=True)
        await community_likes_collection.create_index([("target_type", 1), ("target_id", 1)])
        await community_likes_collection.create_index([("created_at", -1)])
        
        logger.info("Created community post, comment, and like indexes")
        return True
    except Exception as e:
        logger.error(f"Error creating community indexes: {e}")
        return False


async def create_community_post(db, post_data: CommunityPostCreate, user_id: str) -> Optional[CommunityPostResponse]:
    """
    Create a new community post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_data: Community post creation data
        user_id: User's ObjectId as string
        
    Returns:
        Created CommunityPostResponse object if successful, None otherwise
    """
    try:
        logger.info(f"Creating community post for user {user_id} with data: {post_data}")
        community_posts_collection = await get_collection("community_posts")
        
        # Create community post document
        post_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "title": post_data.title,
            "content": post_data.content,
            "post_type": post_data.post_type.value,
            "recipe_id": post_data.recipe_id,
            "tags": post_data.tags,
            "likes_count": 0,
            "comments_count": 0,
            "is_public": post_data.is_public,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        logger.info(f"Created community post document: {post_doc}")
        
        # Insert post into database
        result = await community_posts_collection.insert_one(post_doc)
        logger.info(f"Inserted community post with ID: {result.inserted_id}")
        
        # Return the created post
        created_post = await community_posts_collection.find_one({"_id": result.inserted_id})
        logger.info(f"Retrieved created community post: {created_post}")
        
        if created_post:
            # Convert ObjectId to string for the response
            created_post["id"] = str(created_post["_id"])
            del created_post["_id"]
            
            # Convert post_type back to enum
            created_post["post_type"] = PostType(created_post["post_type"])
            
            logger.info(f"About to create CommunityPostResponse with: {created_post}")
            response = CommunityPostResponse(**created_post)
            logger.info(f"Successfully created CommunityPostResponse: {response}")
            return response
        
        logger.error("Failed to retrieve created community post from database")
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating community post for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating community post for user {user_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None


async def get_community_post(db, post_id: str) -> Optional[CommunityPostResponse]:
    """
    Get a specific community post by ID
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        
    Returns:
        CommunityPostResponse object if found, None otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return None
            
        post = await community_posts_collection.find_one({
            "_id": ObjectId(post_id),
            "is_public": True  # Only return public posts for general access
        })
        
        if post:
            post["id"] = str(post["_id"])
            del post["_id"]
            
            # Convert post_type back to enum
            post["post_type"] = PostType(post["post_type"])
            
            return CommunityPostResponse(**post)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting community post {post_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting community post {post_id}: {e}")
        return None


async def get_community_posts(
    db, 
    skip: int = 0, 
    limit: int = 100, 
    user_id: str = None, 
    post_type: PostType = None
) -> Optional[CommunityPostsListResponse]:
    """
    Get community posts with filtering and pagination
    
    Args:
        db: Database connection (unused, kept for compatibility)
        skip: Number of posts to skip for pagination
        limit: Maximum number of posts to return
        user_id: Filter by specific user (optional)
        post_type: Filter by post type (optional)
        
    Returns:
        CommunityPostsListResponse with paginated results
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        # Build query filter
        query_filter = {"is_public": True}  # Only show public posts
        
        if user_id:
            query_filter["user_id"] = user_id
            
        if post_type:
            query_filter["post_type"] = post_type.value
        
        # Get total count
        total_count = await community_posts_collection.count_documents(query_filter)
        
        # Get paginated results, sorted by creation date (newest first)
        cursor = community_posts_collection.find(query_filter).sort([("created_at", -1)]).skip(skip).limit(limit)
        posts = await cursor.to_list(length=limit)
        
        # Convert to response objects
        post_responses = []
        for post in posts:
            post["id"] = str(post["_id"])
            del post["_id"]
            
            # Convert post_type back to enum
            post["post_type"] = PostType(post["post_type"])
            
            post_responses.append(CommunityPostResponse(**post))
        
        # Calculate pagination info
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return CommunityPostsListResponse(
            posts=post_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting community posts: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting community posts: {e}")
        return None


async def update_community_post(db, post_id: str, post_data: CommunityPostUpdate, user_id: str) -> Optional[CommunityPostResponse]:
    """
    Update an existing community post (only by owner)
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        post_data: Community post update data
        user_id: User's ObjectId as string (must be post owner)
        
    Returns:
        Updated CommunityPostResponse object if successful, None otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in post_data.dict(exclude_none=True).items():
            if field == "post_type" and value:
                update_doc[field] = value.value
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update
            return await get_community_post_by_id_and_user(post_id, user_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update post (only if user owns it)
        result = await community_posts_collection.update_one(
            {"_id": ObjectId(post_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated post
        return await get_community_post_by_id_and_user(post_id, user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating community post {post_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating community post {post_id} for user {user_id}: {e}")
        return None


async def delete_community_post(db, post_id: str, user_id: str) -> bool:
    """
    Delete a community post (only by owner)
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        user_id: User's ObjectId as string (must be post owner)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return False
        
        result = await community_posts_collection.delete_one({
            "_id": ObjectId(post_id),
            "user_id": user_id  # Only allow deletion by post owner
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting community post {post_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting community post {post_id} for user {user_id}: {e}")
        return False


async def get_user_posts(db, user_id: str, skip: int = 0, limit: int = 100) -> Optional[CommunityPostsListResponse]:
    """
    Get posts by specific user
    
    Args:
        db: Database connection (unused, kept for compatibility)
        user_id: User's ObjectId as string
        skip: Number of posts to skip for pagination
        limit: Maximum number of posts to return
        
    Returns:
        CommunityPostsListResponse with user's posts
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        # Build query filter for user's posts
        query_filter = {"user_id": user_id}
        
        # Get total count
        total_count = await community_posts_collection.count_documents(query_filter)
        
        # Get paginated results, sorted by creation date (newest first)
        cursor = community_posts_collection.find(query_filter).sort([("created_at", -1)]).skip(skip).limit(limit)
        posts = await cursor.to_list(length=limit)
        
        # Convert to response objects
        post_responses = []
        for post in posts:
            post["id"] = str(post["_id"])
            del post["_id"]
            
            # Convert post_type back to enum
            post["post_type"] = PostType(post["post_type"])
            
            post_responses.append(CommunityPostResponse(**post))
        
        # Calculate pagination info
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return CommunityPostsListResponse(
            posts=post_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting posts for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting posts for user {user_id}: {e}")
        return None


async def increment_post_likes(db, post_id: str) -> bool:
    """
    Increment likes count for a post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return False
        
        result = await community_posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$inc": {"likes_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error incrementing likes for post {post_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error incrementing likes for post {post_id}: {e}")
        return False


async def decrement_post_likes(db, post_id: str) -> bool:
    """
    Decrement likes count for a post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return False
        
        result = await community_posts_collection.update_one(
            {"_id": ObjectId(post_id), "likes_count": {"$gt": 0}},  # Prevent negative counts
            {
                "$inc": {"likes_count": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error decrementing likes for post {post_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error decrementing likes for post {post_id}: {e}")
        return False


async def increment_post_comments(db, post_id: str) -> bool:
    """
    Increment comments count for a post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return False
        
        result = await community_posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$inc": {"comments_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error incrementing comments for post {post_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error incrementing comments for post {post_id}: {e}")
        return False


async def decrement_post_comments(db, post_id: str) -> bool:
    """
    Decrement comments count for a post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Community post's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return False
        
        result = await community_posts_collection.update_one(
            {"_id": ObjectId(post_id), "comments_count": {"$gt": 0}},  # Prevent negative counts
            {
                "$inc": {"comments_count": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error decrementing comments for post {post_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error decrementing comments for post {post_id}: {e}")
        return False


async def get_community_stats(db) -> Optional[CommunityStatsResponse]:
    """
    Get overall community statistics
    
    Args:
        db: Database connection (unused, kept for compatibility)
        
    Returns:
        CommunityStatsResponse with community statistics
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        # Get all public posts
        posts = await community_posts_collection.find({"is_public": True}).to_list(length=None)
        
        if not posts:
            return CommunityStatsResponse(
                total_posts=0,
                total_comments=0,
                total_likes=0,
                posts_by_type={},
                most_active_users=[],
                trending_tags=[],
                recent_activity_count=0
            )
        
        # Calculate basic statistics
        total_posts = len(posts)
        total_comments = sum(post.get("comments_count", 0) for post in posts)
        total_likes = sum(post.get("likes_count", 0) for post in posts)
        
        # Count posts by type
        posts_by_type = {}
        for post in posts:
            post_type = post.get("post_type", "general")
            posts_by_type[post_type] = posts_by_type.get(post_type, 0) + 1
        
        # Count posts by user to find most active users
        user_post_counts = {}
        for post in posts:
            user_id = post.get("user_id")
            if user_id:
                user_post_counts[user_id] = user_post_counts.get(user_id, 0) + 1
        
        # Get top 5 most active users
        most_active_users = []
        for user_id, count in sorted(user_post_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            most_active_users.append({
                "user_id": user_id,
                "post_count": count
            })
        
        # Count tag usage to find trending tags
        tag_counts = {}
        for post in posts:
            for tag in post.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get top 10 trending tags
        trending_tags = []
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            trending_tags.append({
                "tag": tag,
                "usage_count": count
            })
        
        # Count recent activity (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_activity_count = len([
            post for post in posts 
            if post.get("created_at", datetime.min) > twenty_four_hours_ago
        ])
        
        return CommunityStatsResponse(
            total_posts=total_posts,
            total_comments=total_comments,
            total_likes=total_likes,
            posts_by_type=posts_by_type,
            most_active_users=most_active_users,
            trending_tags=trending_tags,
            recent_activity_count=recent_activity_count
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting community stats: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting community stats: {e}")
        return None


async def get_user_community_stats(db, user_id: str) -> Optional[CommunityStatsResponse]:
    """
    Get user-specific community statistics
    
    Args:
        db: Database connection (unused, kept for compatibility)
        user_id: User's ObjectId as string
        
    Returns:
        CommunityStatsResponse with user-specific statistics
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        # Get all posts by the user
        user_posts = await community_posts_collection.find({"user_id": user_id}).to_list(length=None)
        
        if not user_posts:
            return CommunityStatsResponse(
                total_posts=0,
                total_comments=0,
                total_likes=0,
                posts_by_type={},
                most_active_users=[],
                trending_tags=[],
                recent_activity_count=0
            )
        
        # Calculate user-specific statistics
        total_posts = len(user_posts)
        total_comments = sum(post.get("comments_count", 0) for post in user_posts)
        total_likes = sum(post.get("likes_count", 0) for post in user_posts)
        
        # Count posts by type
        posts_by_type = {}
        for post in user_posts:
            post_type = post.get("post_type", "general")
            posts_by_type[post_type] = posts_by_type.get(post_type, 0) + 1
        
        # Count tag usage by the user
        tag_counts = {}
        for post in user_posts:
            for tag in post.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get user's most used tags
        trending_tags = []
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            trending_tags.append({
                "tag": tag,
                "usage_count": count
            })
        
        # Count recent activity (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_activity_count = len([
            post for post in user_posts 
            if post.get("created_at", datetime.min) > twenty_four_hours_ago
        ])
        
        # For user stats, most_active_users will just be the user themselves
        most_active_users = [{
            "user_id": user_id,
            "post_count": total_posts
        }]
        
        return CommunityStatsResponse(
            total_posts=total_posts,
            total_comments=total_comments,
            total_likes=total_likes,
            posts_by_type=posts_by_type,
            most_active_users=most_active_users,
            trending_tags=trending_tags,
            recent_activity_count=recent_activity_count
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting user community stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting user community stats for user {user_id}: {e}")
        return None


# Helper function for internal use
async def get_community_post_by_id_and_user(post_id: str, user_id: str) -> Optional[CommunityPostResponse]:
    """
    Get a specific community post by ID and user (for owner operations)
    
    Args:
        post_id: Community post's ObjectId as string
        user_id: User's ObjectId as string
        
    Returns:
        CommunityPostResponse object if found, None otherwise
    """
    try:
        community_posts_collection = await get_collection("community_posts")
        
        if not ObjectId.is_valid(post_id):
            return None
            
        post = await community_posts_collection.find_one({
            "_id": ObjectId(post_id),
            "user_id": user_id
        })
        
        if post:
            post["id"] = str(post["_id"])
            del post["_id"]
            
            # Convert post_type back to enum
            post["post_type"] = PostType(post["post_type"])
            
            return CommunityPostResponse(**post)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting community post {post_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting community post {post_id} for user {user_id}: {e}")
        return None


# ============================================================================
# COMMENT CRUD OPERATIONS
# ============================================================================

async def create_comment(db, comment_data: CommentCreate, user_id: str, post_id: str) -> Optional[CommentResponse]:
    """
    Create a new comment on a post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_data: Comment creation data
        user_id: User's ObjectId as string
        post_id: Post's ObjectId as string
        
    Returns:
        Created CommentResponse object if successful, None otherwise
    """
    try:
        logger.info(f"Creating comment for user {user_id} on post {post_id}")
        community_comments_collection = await get_collection("community_comments")
        community_posts_collection = await get_collection("community_posts")
        
        # Validate post exists
        if not ObjectId.is_valid(post_id):
            logger.error(f"Invalid post_id: {post_id}")
            return None
            
        post_exists = await community_posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post_exists:
            logger.error(f"Post {post_id} not found")
            return None
        
        # Validate parent comment if provided
        if comment_data.parent_comment_id:
            if not ObjectId.is_valid(comment_data.parent_comment_id):
                logger.error(f"Invalid parent_comment_id: {comment_data.parent_comment_id}")
                return None
                
            parent_comment = await community_comments_collection.find_one({
                "_id": ObjectId(comment_data.parent_comment_id),
                "post_id": post_id
            })
            if not parent_comment:
                logger.error(f"Parent comment {comment_data.parent_comment_id} not found")
                return None
        
        # Create comment document
        comment_doc = {
            "_id": ObjectId(),
            "post_id": post_id,
            "user_id": user_id,
            "content": comment_data.content,
            "parent_comment_id": comment_data.parent_comment_id,
            "likes_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert comment into database
        result = await community_comments_collection.insert_one(comment_doc)
        logger.info(f"Inserted comment with ID: {result.inserted_id}")
        
        # Increment post comments count
        await increment_post_comments(db, post_id)
        
        # Return the created comment
        created_comment = await community_comments_collection.find_one({"_id": result.inserted_id})
        
        if created_comment:
            created_comment["id"] = str(created_comment["_id"])
            del created_comment["_id"]
            
            return CommentResponse(**created_comment)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating comment for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating comment for user {user_id}: {e}")
        return None


async def get_comment(db, comment_id: str) -> Optional[CommentResponse]:
    """
    Get a specific comment by ID
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_id: Comment's ObjectId as string
        
    Returns:
        CommentResponse object if found, None otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(comment_id):
            return None
            
        comment = await community_comments_collection.find_one({"_id": ObjectId(comment_id)})
        
        if comment:
            comment["id"] = str(comment["_id"])
            del comment["_id"]
            
            return CommentResponse(**comment)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting comment {comment_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting comment {comment_id}: {e}")
        return None


async def get_post_comments(db, post_id: str, skip: int = 0, limit: int = 100) -> Optional[CommentsListResponse]:
    """
    Get comments for a specific post
    
    Args:
        db: Database connection (unused, kept for compatibility)
        post_id: Post's ObjectId as string
        skip: Number of comments to skip for pagination
        limit: Maximum number of comments to return
        
    Returns:
        CommentsListResponse with paginated results
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(post_id):
            return None
        
        # Build query filter for top-level comments (no parent)
        query_filter = {"post_id": post_id, "parent_comment_id": None}
        
        # Get total count
        total_count = await community_comments_collection.count_documents(query_filter)
        
        # Get paginated results, sorted by creation date (oldest first for comments)
        cursor = community_comments_collection.find(query_filter).sort([("created_at", 1)]).skip(skip).limit(limit)
        comments = await cursor.to_list(length=limit)
        
        # Convert to response objects
        comment_responses = []
        for comment in comments:
            comment["id"] = str(comment["_id"])
            del comment["_id"]
            
            comment_responses.append(CommentResponse(**comment))
        
        # Calculate pagination info
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return CommentsListResponse(
            comments=comment_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting comments for post {post_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting comments for post {post_id}: {e}")
        return None


async def get_comment_replies(db, parent_comment_id: str, skip: int = 0, limit: int = 100) -> Optional[CommentsListResponse]:
    """
    Get replies to a specific comment
    
    Args:
        db: Database connection (unused, kept for compatibility)
        parent_comment_id: Parent comment's ObjectId as string
        skip: Number of replies to skip for pagination
        limit: Maximum number of replies to return
        
    Returns:
        CommentsListResponse with paginated results
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(parent_comment_id):
            return None
        
        # Build query filter for replies
        query_filter = {"parent_comment_id": parent_comment_id}
        
        # Get total count
        total_count = await community_comments_collection.count_documents(query_filter)
        
        # Get paginated results, sorted by creation date (oldest first for replies)
        cursor = community_comments_collection.find(query_filter).sort([("created_at", 1)]).skip(skip).limit(limit)
        replies = await cursor.to_list(length=limit)
        
        # Convert to response objects
        reply_responses = []
        for reply in replies:
            reply["id"] = str(reply["_id"])
            del reply["_id"]
            
            reply_responses.append(CommentResponse(**reply))
        
        # Calculate pagination info
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return CommentsListResponse(
            comments=reply_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting replies for comment {parent_comment_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting replies for comment {parent_comment_id}: {e}")
        return None


async def update_comment(db, comment_id: str, comment_data: CommentUpdate, user_id: str) -> Optional[CommentResponse]:
    """
    Update an existing comment (only by owner)
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_id: Comment's ObjectId as string
        comment_data: Comment update data
        user_id: User's ObjectId as string (must be comment owner)
        
    Returns:
        Updated CommentResponse object if successful, None otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(comment_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in comment_data.dict(exclude_none=True).items():
            update_doc[field] = value
        
        if not update_doc:
            # No fields to update
            return await get_comment_by_id_and_user(comment_id, user_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update comment (only if user owns it)
        result = await community_comments_collection.update_one(
            {"_id": ObjectId(comment_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated comment
        return await get_comment_by_id_and_user(comment_id, user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating comment {comment_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating comment {comment_id} for user {user_id}: {e}")
        return None


async def delete_comment(db, comment_id: str, user_id: str) -> bool:
    """
    Delete a comment (only by owner)
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_id: Comment's ObjectId as string
        user_id: User's ObjectId as string (must be comment owner)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        community_likes_collection = await get_collection("community_likes")
        
        if not ObjectId.is_valid(comment_id):
            return False
        
        # Get comment to check ownership and get post_id
        comment = await community_comments_collection.find_one({
            "_id": ObjectId(comment_id),
            "user_id": user_id
        })
        
        if not comment:
            return False
        
        post_id = comment["post_id"]
        
        # Delete all replies to this comment
        await community_comments_collection.delete_many({"parent_comment_id": comment_id})
        
        # Delete all likes on this comment
        await community_likes_collection.delete_many({
            "target_type": TargetType.COMMENT.value,
            "target_id": comment_id
        })
        
        # Delete the comment itself
        result = await community_comments_collection.delete_one({
            "_id": ObjectId(comment_id),
            "user_id": user_id
        })
        
        if result.deleted_count > 0:
            # Decrement post comments count
            await decrement_post_comments(db, post_id)
            return True
        
        return False
        
    except PyMongoError as e:
        logger.error(f"Database error deleting comment {comment_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id} for user {user_id}: {e}")
        return False


# ============================================================================
# LIKE CRUD OPERATIONS
# ============================================================================

async def create_like(db, like_data: LikeCreate, user_id: str) -> Optional[LikeResponse]:
    """
    Create a new like on a post or comment
    
    Args:
        db: Database connection (unused, kept for compatibility)
        like_data: Like creation data
        user_id: User's ObjectId as string
        
    Returns:
        Created LikeResponse object if successful, None otherwise
    """
    try:
        logger.info(f"Creating like for user {user_id} on {like_data.target_type} {like_data.target_id}")
        community_likes_collection = await get_collection("community_likes")
        
        # Validate target exists
        if not ObjectId.is_valid(like_data.target_id):
            logger.error(f"Invalid target_id: {like_data.target_id}")
            return None
        
        # Check if target exists based on type
        if like_data.target_type == TargetType.POST:
            community_posts_collection = await get_collection("community_posts")
            target_exists = await community_posts_collection.find_one({"_id": ObjectId(like_data.target_id)})
        elif like_data.target_type == TargetType.COMMENT:
            community_comments_collection = await get_collection("community_comments")
            target_exists = await community_comments_collection.find_one({"_id": ObjectId(like_data.target_id)})
        else:
            logger.error(f"Invalid target_type: {like_data.target_type}")
            return None
        
        if not target_exists:
            logger.error(f"Target {like_data.target_type} {like_data.target_id} not found")
            return None
        
        # Check if user already liked this target
        existing_like = await community_likes_collection.find_one({
            "user_id": user_id,
            "target_type": like_data.target_type.value,
            "target_id": like_data.target_id
        })
        
        if existing_like:
            logger.info(f"User {user_id} already liked {like_data.target_type} {like_data.target_id}")
            # Return existing like
            existing_like["id"] = str(existing_like["_id"])
            del existing_like["_id"]
            existing_like["target_type"] = TargetType(existing_like["target_type"])
            return LikeResponse(**existing_like)
        
        # Create like document
        like_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "target_type": like_data.target_type.value,
            "target_id": like_data.target_id,
            "created_at": datetime.utcnow()
        }
        
        # Insert like into database
        result = await community_likes_collection.insert_one(like_doc)
        logger.info(f"Inserted like with ID: {result.inserted_id}")
        
        # Increment target likes count
        if like_data.target_type == TargetType.POST:
            await increment_post_likes(db, like_data.target_id)
        elif like_data.target_type == TargetType.COMMENT:
            await increment_comment_likes(db, like_data.target_id)
        
        # Return the created like
        created_like = await community_likes_collection.find_one({"_id": result.inserted_id})
        
        if created_like:
            created_like["id"] = str(created_like["_id"])
            del created_like["_id"]
            created_like["target_type"] = TargetType(created_like["target_type"])
            
            return LikeResponse(**created_like)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating like for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating like for user {user_id}: {e}")
        return None


async def delete_like(db, user_id: str, target_type: TargetType, target_id: str) -> bool:
    """
    Remove a like from a post or comment
    
    Args:
        db: Database connection (unused, kept for compatibility)
        user_id: User's ObjectId as string
        target_type: Type of target being unliked
        target_id: ID of the post or comment being unliked
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_likes_collection = await get_collection("community_likes")
        
        if not ObjectId.is_valid(target_id):
            return False
        
        # Delete the like
        result = await community_likes_collection.delete_one({
            "user_id": user_id,
            "target_type": target_type.value,
            "target_id": target_id
        })
        
        if result.deleted_count > 0:
            # Decrement target likes count
            if target_type == TargetType.POST:
                await decrement_post_likes(db, target_id)
            elif target_type == TargetType.COMMENT:
                await decrement_comment_likes(db, target_id)
            
            return True
        
        return False
        
    except PyMongoError as e:
        logger.error(f"Database error deleting like for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting like for user {user_id}: {e}")
        return False


async def get_user_like(db, user_id: str, target_type: TargetType, target_id: str) -> Optional[LikeResponse]:
    """
    Check if user has liked a specific target
    
    Args:
        db: Database connection (unused, kept for compatibility)
        user_id: User's ObjectId as string
        target_type: Type of target being checked
        target_id: ID of the post or comment being checked
        
    Returns:
        LikeResponse object if user has liked the target, None otherwise
    """
    try:
        community_likes_collection = await get_collection("community_likes")
        
        if not ObjectId.is_valid(target_id):
            return None
        
        like = await community_likes_collection.find_one({
            "user_id": user_id,
            "target_type": target_type.value,
            "target_id": target_id
        })
        
        if like:
            like["id"] = str(like["_id"])
            del like["_id"]
            like["target_type"] = TargetType(like["target_type"])
            
            return LikeResponse(**like)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting user like for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting user like for user {user_id}: {e}")
        return None


async def get_target_likes(db, target_type: TargetType, target_id: str, skip: int = 0, limit: int = 100) -> Optional[List[LikeResponse]]:
    """
    Get likes for a specific target
    
    Args:
        db: Database connection (unused, kept for compatibility)
        target_type: Type of target
        target_id: ID of the post or comment
        skip: Number of likes to skip for pagination
        limit: Maximum number of likes to return
        
    Returns:
        List of LikeResponse objects
    """
    try:
        community_likes_collection = await get_collection("community_likes")
        
        if not ObjectId.is_valid(target_id):
            return None
        
        # Get paginated results, sorted by creation date (newest first)
        cursor = community_likes_collection.find({
            "target_type": target_type.value,
            "target_id": target_id
        }).sort([("created_at", -1)]).skip(skip).limit(limit)
        
        likes = await cursor.to_list(length=limit)
        
        # Convert to response objects
        like_responses = []
        for like in likes:
            like["id"] = str(like["_id"])
            del like["_id"]
            like["target_type"] = TargetType(like["target_type"])
            
            like_responses.append(LikeResponse(**like))
        
        return like_responses
        
    except PyMongoError as e:
        logger.error(f"Database error getting likes for {target_type} {target_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting likes for {target_type} {target_id}: {e}")
        return None


# ============================================================================
# COMMENT INTERACTION FUNCTIONS
# ============================================================================

async def increment_comment_likes(db, comment_id: str) -> bool:
    """
    Increment likes count for a comment
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_id: Comment's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(comment_id):
            return False
        
        result = await community_comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {
                "$inc": {"likes_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error incrementing likes for comment {comment_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error incrementing likes for comment {comment_id}: {e}")
        return False


async def decrement_comment_likes(db, comment_id: str) -> bool:
    """
    Decrement likes count for a comment
    
    Args:
        db: Database connection (unused, kept for compatibility)
        comment_id: Comment's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(comment_id):
            return False
        
        result = await community_comments_collection.update_one(
            {"_id": ObjectId(comment_id), "likes_count": {"$gt": 0}},  # Prevent negative counts
            {
                "$inc": {"likes_count": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error decrementing likes for comment {comment_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error decrementing likes for comment {comment_id}: {e}")
        return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_comment_by_id_and_user(comment_id: str, user_id: str) -> Optional[CommentResponse]:
    """
    Get a specific comment by ID and user (for owner operations)
    
    Args:
        comment_id: Comment's ObjectId as string
        user_id: User's ObjectId as string
        
    Returns:
        CommentResponse object if found, None otherwise
    """
    try:
        community_comments_collection = await get_collection("community_comments")
        
        if not ObjectId.is_valid(comment_id):
            return None
            
        comment = await community_comments_collection.find_one({
            "_id": ObjectId(comment_id),
            "user_id": user_id
        })
        
        if comment:
            comment["id"] = str(comment["_id"])
            del comment["_id"]
            
            return CommentResponse(**comment)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting comment {comment_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting comment {comment_id} for user {user_id}: {e}")
        return None