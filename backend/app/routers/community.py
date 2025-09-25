"""
Community features router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.models.responses import SuccessResponse
from app.models.community import (
    CommunityPostCreate,
    CommunityPostUpdate,
    CommunityPostResponse,
    CommunityPostsListResponse,
    CommunityStatsResponse,
    PostType,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentsListResponse,
    LikeCreate,
    LikeResponse,
    TargetType
)
from app.crud.community import (
    create_community_post,
    get_community_posts,
    get_community_post,
    update_community_post,
    delete_community_post,
    get_user_posts,
    increment_post_likes,
    decrement_post_likes,
    get_community_stats,
    get_user_community_stats,
    create_community_indexes,
    create_comment,
    get_comment,
    get_post_comments,
    get_comment_replies,
    update_comment,
    delete_comment,
    create_like,
    delete_like,
    get_user_like,
    get_target_likes
)
from app.utils.auth import get_current_active_user
from app.database import get_database

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_community_indexes()


@router.post("/posts/", response_model=CommunityPostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_community_post(
    post_data: CommunityPostCreate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create new community post"""
    user_id = str(current_user["_id"])
    
    result = await create_community_post(db=db, post_data=post_data, user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create community post"
        )
    
    return result


@router.get("/posts/", response_model=CommunityPostsListResponse)
async def get_community_posts_list(
    skip: int = Query(0, ge=0, description="Number of posts to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of posts to return"),
    post_type: Optional[PostType] = Query(None, description="Filter by post type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db = Depends(get_database)
):
    """Get community posts with filtering by type and user"""
    
    result = await get_community_posts(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        post_type=post_type
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve community posts"
        )
    
    return result


@router.get("/posts/{post_id}", response_model=CommunityPostResponse)
async def get_community_post_by_id(
    post_id: str,
    db = Depends(get_database)
):
    """Get specific community post by ID"""
    
    result = await get_community_post(db=db, post_id=post_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community post not found"
        )
    
    return result


@router.put("/posts/{post_id}", response_model=CommunityPostResponse)
async def update_community_post_endpoint(
    post_id: str,
    update_data: CommunityPostUpdate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update community post (owner only)"""
    user_id = str(current_user["_id"])
    
    result = await update_community_post(
        db=db,
        post_id=post_id,
        post_data=update_data,
        user_id=user_id
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community post not found or you don't have permission to update it"
        )
    
    return result


@router.delete("/posts/{post_id}")
async def delete_community_post_endpoint(
    post_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete community post (owner only)"""
    user_id = str(current_user["_id"])
    
    success = await delete_community_post(db=db, post_id=post_id, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community post not found or you don't have permission to delete it"
        )
    
    return SuccessResponse(message="Community post deleted successfully")


@router.get("/users/{user_id}/posts", response_model=CommunityPostsListResponse)
async def get_posts_by_user(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of posts to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of posts to return"),
    db = Depends(get_database)
):
    """Get posts by specific user"""
    
    result = await get_user_posts(db=db, user_id=user_id, skip=skip, limit=limit)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user posts"
        )
    
    return result


@router.post("/posts/{post_id}/like")
async def like_community_post(
    post_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Like a community post"""
    user_id = str(current_user["_id"])
    
    # First check if the post exists
    post = await get_community_post(db=db, post_id=post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community post not found"
        )
    
    # Increment the likes count
    success = await increment_post_likes(db=db, post_id=post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like the post"
        )
    
    return SuccessResponse(message="Post liked successfully")


@router.delete("/posts/{post_id}/like")
async def unlike_community_post(
    post_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Unlike a community post"""
    user_id = str(current_user["_id"])
    
    # First check if the post exists
    post = await get_community_post(db=db, post_id=post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community post not found"
        )
    
    # Decrement the likes count
    success = await decrement_post_likes(db=db, post_id=post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlike the post"
        )
    
    return SuccessResponse(message="Post unliked successfully")


@router.get("/stats/overview", response_model=CommunityStatsResponse)
async def get_community_statistics(
    db = Depends(get_database)
):
    """Get overall community statistics"""
    
    result = await get_community_stats(db=db)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve community statistics"
        )
    
    return result


# ============================================================================
# COMMENT API ENDPOINTS
# ============================================================================

@router.post("/posts/{post_id}/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_on_post(
    post_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create new comment on a post"""
    user_id = str(current_user["_id"])
    
    result = await create_comment(db=db, comment_data=comment_data, user_id=user_id, post_id=post_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or failed to create comment"
        )
    
    return result


@router.get("/posts/{post_id}/comments/", response_model=CommentsListResponse)
async def get_comments_for_post(
    post_id: str,
    skip: int = Query(0, ge=0, description="Number of comments to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of comments to return"),
    db = Depends(get_database)
):
    """Get comments for a post with pagination"""
    
    result = await get_post_comments(db=db, post_id=post_id, skip=skip, limit=limit)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or failed to retrieve comments"
        )
    
    return result


@router.post("/comments/{comment_id}/replies/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_reply_to_comment(
    comment_id: str,
    reply_data: CommentCreate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create reply to a comment"""
    user_id = str(current_user["_id"])
    
    # Get the parent comment to find the post_id
    parent_comment = await get_comment(db=db, comment_id=comment_id)
    if parent_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found"
        )
    
    # Set the parent_comment_id in the reply data
    reply_data.parent_comment_id = comment_id
    
    result = await create_comment(
        db=db,
        comment_data=reply_data,
        user_id=user_id,
        post_id=parent_comment.post_id
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create reply"
        )
    
    return result


@router.get("/comments/{comment_id}/replies/", response_model=CommentsListResponse)
async def get_replies_to_comment(
    comment_id: str,
    skip: int = Query(0, ge=0, description="Number of replies to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of replies to return"),
    db = Depends(get_database)
):
    """Get replies to a comment with pagination"""
    
    result = await get_comment_replies(db=db, parent_comment_id=comment_id, skip=skip, limit=limit)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or failed to retrieve replies"
        )
    
    return result


@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment_by_id(
    comment_id: str,
    db = Depends(get_database)
):
    """Get single comment by ID"""
    
    result = await get_comment(db=db, comment_id=comment_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    return result


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment_endpoint(
    comment_id: str,
    update_data: CommentUpdate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update comment (owner only)"""
    user_id = str(current_user["_id"])
    
    result = await update_comment(
        db=db,
        comment_id=comment_id,
        comment_data=update_data,
        user_id=user_id
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or you don't have permission to update it"
        )
    
    return result


@router.delete("/comments/{comment_id}")
async def delete_comment_endpoint(
    comment_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete comment (owner only)"""
    user_id = str(current_user["_id"])
    
    success = await delete_comment(db=db, comment_id=comment_id, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or you don't have permission to delete it"
        )
    
    return SuccessResponse(message="Comment deleted successfully")


# ============================================================================
# LIKE API ENDPOINTS
# ============================================================================

@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Like a comment"""
    user_id = str(current_user["_id"])
    
    # First check if the comment exists
    comment = await get_comment(db=db, comment_id=comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Create like data
    like_data = LikeCreate(target_type=TargetType.COMMENT, target_id=comment_id)
    
    result = await create_like(db=db, like_data=like_data, user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like the comment"
        )
    
    return SuccessResponse(message="Comment liked successfully")


@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Unlike a comment"""
    user_id = str(current_user["_id"])
    
    # First check if the comment exists
    comment = await get_comment(db=db, comment_id=comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Delete the like
    success = await delete_like(db=db, user_id=user_id, target_type=TargetType.COMMENT, target_id=comment_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found or already removed"
        )
    
    return SuccessResponse(message="Comment unliked successfully")


@router.get("/posts/{post_id}/likes")
async def get_post_likes(
    post_id: str,
    skip: int = Query(0, ge=0, description="Number of likes to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of likes to return"),
    db = Depends(get_database)
):
    """Get likes for a post"""
    
    # First check if the post exists
    post = await get_community_post(db=db, post_id=post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    result = await get_target_likes(db=db, target_type=TargetType.POST, target_id=post_id, skip=skip, limit=limit)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve post likes"
        )
    
    return {"likes": result, "total_count": len(result)}


@router.get("/comments/{comment_id}/likes")
async def get_comment_likes(
    comment_id: str,
    skip: int = Query(0, ge=0, description="Number of likes to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of likes to return"),
    db = Depends(get_database)
):
    """Get likes for a comment"""
    
    # First check if the comment exists
    comment = await get_comment(db=db, comment_id=comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    result = await get_target_likes(db=db, target_type=TargetType.COMMENT, target_id=comment_id, skip=skip, limit=limit)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment likes"
        )
    
    return {"likes": result, "total_count": len(result)}


# ============================================================================
# USER INTERACTION ENDPOINTS
# ============================================================================

@router.get("/posts/{post_id}/user-interaction")
async def get_post_user_interaction(
    post_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Check if current user liked/commented on post"""
    user_id = str(current_user["_id"])
    
    # First check if the post exists
    post = await get_community_post(db=db, post_id=post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Check if user has liked the post
    user_like = await get_user_like(db=db, user_id=user_id, target_type=TargetType.POST, target_id=post_id)
    has_liked = user_like is not None
    
    # Check if user has commented on the post (get first comment to see if any exist)
    user_comments = await get_post_comments(db=db, post_id=post_id, skip=0, limit=1)
    has_commented = user_comments is not None and user_comments.total_count > 0
    
    return {
        "has_liked": has_liked,
        "has_commented": has_commented,
        "like_id": str(user_like.id) if user_like else None
    }


@router.get("/comments/{comment_id}/user-interaction")
async def get_comment_user_interaction(
    comment_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Check if current user liked comment"""
    user_id = str(current_user["_id"])
    
    # First check if the comment exists
    comment = await get_comment(db=db, comment_id=comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check if user has liked the comment
    user_like = await get_user_like(db=db, user_id=user_id, target_type=TargetType.COMMENT, target_id=comment_id)
    has_liked = user_like is not None
    
    return {
        "has_liked": has_liked,
        "like_id": str(user_like.id) if user_like else None
    }


@router.get("/stats/user", response_model=CommunityStatsResponse)
async def get_user_community_statistics(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get current user's community statistics"""
    user_id = str(current_user["_id"])
    
    result = await get_user_community_stats(db=db, user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user community statistics"
        )
    
    return result