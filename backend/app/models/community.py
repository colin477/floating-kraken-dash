"""
Pydantic models for community features
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum


class PostType(str, Enum):
    """Enumeration for community post types"""
    RECIPE = "recipe"
    TIP = "tip"
    SAVINGS_STORY = "savings_story"
    GENERAL = "general"


class TargetType(str, Enum):
    """Enumeration for like target types"""
    POST = "post"
    COMMENT = "comment"


class CommunityPost(BaseModel):
    """Main community post model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, max_length=5000, description="Post content/body")
    post_type: PostType = Field(..., description="Type of community post")
    recipe_id: Optional[str] = Field(None, description="Reference to recipe if post_type is recipe")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    likes_count: int = Field(default=0, ge=0, description="Number of likes")
    comments_count: int = Field(default=0, ge=0, description="Number of comments")
    is_public: bool = Field(default=True, description="Visibility setting")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Post creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Post last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Post title cannot be empty')
        return v.strip()

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Post content cannot be empty')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if not v:
            return []
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    @validator('recipe_id')
    def validate_recipe_id(cls, v, values):
        """Ensure recipe_id is provided when post_type is recipe"""
        post_type = values.get('post_type')
        if post_type == PostType.RECIPE and not v:
            raise ValueError('recipe_id is required when post_type is recipe')
        return v


class Comment(BaseModel):
    """Model for community post comments"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    post_id: str = Field(..., description="Reference to the community post")
    user_id: str = Field(..., description="Reference to user who made the comment")
    content: str = Field(..., min_length=1, max_length=1000, description="Comment text")
    parent_comment_id: Optional[str] = Field(None, description="Reference to parent comment for nested comments/replies")
    likes_count: int = Field(default=0, ge=0, description="Number of likes on this comment")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Comment creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Comment last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()


class Like(BaseModel):
    """Model for likes on posts and comments"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to user who liked")
    target_type: TargetType = Field(..., description="Type of target being liked")
    target_id: str = Field(..., description="ID of the post or comment being liked")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Like creation timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class CommunityPostCreate(BaseModel):
    """Schema for creating new community posts"""
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, max_length=5000, description="Post content/body")
    post_type: PostType = Field(..., description="Type of community post")
    recipe_id: Optional[str] = Field(None, description="Reference to recipe if post_type is recipe")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    is_public: bool = Field(default=True, description="Visibility setting")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Post title cannot be empty')
        return v.strip()

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Post content cannot be empty')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if not v:
            return []
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    @validator('recipe_id')
    def validate_recipe_id(cls, v, values):
        """Ensure recipe_id is provided when post_type is recipe"""
        post_type = values.get('post_type')
        if post_type == PostType.RECIPE and not v:
            raise ValueError('recipe_id is required when post_type is recipe')
        return v


class CommunityPostUpdate(BaseModel):
    """Schema for updating existing community posts"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Post title")
    content: Optional[str] = Field(None, min_length=1, max_length=5000, description="Post content/body")
    post_type: Optional[PostType] = Field(None, description="Type of community post")
    recipe_id: Optional[str] = Field(None, description="Reference to recipe if post_type is recipe")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_public: Optional[bool] = Field(None, description="Visibility setting")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Post title cannot be empty')
        return v.strip() if v else v

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Post content cannot be empty')
        return v.strip() if v else v

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if v is not None:
            if not v:
                return []
            cleaned_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    cleaned_tags.append(tag.strip().lower())
            return list(set(cleaned_tags))  # Remove duplicates
        return v


class CommunityPostResponse(BaseModel):
    """Schema for community post response"""
    id: str
    user_id: str
    title: str
    content: str
    post_type: PostType
    recipe_id: Optional[str]
    tags: List[str]
    likes_count: int
    comments_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    user_display_name: Optional[str] = Field(None, description="Display name of the post author")
    user_avatar_url: Optional[str] = Field(None, description="Avatar URL of the post author")
    is_liked_by_user: Optional[bool] = Field(None, description="Whether current user has liked this post")
    recipe_title: Optional[str] = Field(None, description="Title of associated recipe if applicable")

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    """Schema for creating new comments"""
    content: str = Field(..., min_length=1, max_length=1000, description="Comment text")
    parent_comment_id: Optional[str] = Field(None, description="Reference to parent comment for nested comments/replies")

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()


class CommentUpdate(BaseModel):
    """Schema for updating existing comments"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000, description="Comment text")

    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip() if v else v


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: str
    post_id: str
    user_id: str
    content: str
    parent_comment_id: Optional[str]
    likes_count: int
    created_at: datetime
    updated_at: datetime
    user_display_name: Optional[str] = Field(None, description="Display name of the comment author")
    user_avatar_url: Optional[str] = Field(None, description="Avatar URL of the comment author")
    is_liked_by_user: Optional[bool] = Field(None, description="Whether current user has liked this comment")
    replies: Optional[List['CommentResponse']] = Field(None, description="Nested replies to this comment")

    model_config = {"from_attributes": True}


class LikeCreate(BaseModel):
    """Schema for creating new likes"""
    target_type: TargetType = Field(..., description="Type of target being liked")
    target_id: str = Field(..., description="ID of the post or comment being liked")


class LikeResponse(BaseModel):
    """Schema for like response"""
    id: str
    user_id: str
    target_type: TargetType
    target_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunityPostsListResponse(BaseModel):
    """Schema for listing community posts with pagination"""
    posts: List[CommunityPostResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class CommentsListResponse(BaseModel):
    """Schema for listing comments with pagination"""
    comments: List[CommentResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class CommunityStatsResponse(BaseModel):
    """Schema for community statistics"""
    total_posts: int
    total_comments: int
    total_likes: int
    posts_by_type: Dict[str, int]
    most_active_users: List[Dict[str, Any]]
    trending_tags: List[Dict[str, Any]]
    recent_activity_count: int = Field(..., description="Activity in the last 24 hours")


# Enable forward references for nested CommentResponse
CommentResponse.model_rebuild()