"""
Pydantic models for user profiles and family member management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class FamilyMember(BaseModel):
    """Embedded model for family members within user profiles"""
    id: str = Field(..., description="Unique identifier for the family member")
    name: str = Field(..., min_length=1, max_length=100, description="Family member's name")
    age: int = Field(..., ge=0, le=150, description="Family member's age")
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    dietary_restrictions: List[str] = Field(default_factory=list, description="List of dietary restrictions")
    loved_foods: List[str] = Field(default_factory=list, description="List of foods they love")
    disliked_foods: List[str] = Field(default_factory=list, description="List of foods they dislike")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class FamilyMemberCreate(BaseModel):
    """Schema for creating new family members"""
    name: str = Field(..., min_length=1, max_length=100, description="Family member's name")
    age: int = Field(..., ge=0, le=150, description="Family member's age")
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    dietary_restrictions: List[str] = Field(default_factory=list, description="List of dietary restrictions")
    loved_foods: List[str] = Field(default_factory=list, description="List of foods they love")
    disliked_foods: List[str] = Field(default_factory=list, description="List of foods they dislike")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class FamilyMemberUpdate(BaseModel):
    """Schema for updating existing family members"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Family member's name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Family member's age")
    allergies: Optional[List[str]] = Field(None, description="List of allergies")
    dietary_restrictions: Optional[List[str]] = Field(None, description="List of dietary restrictions")
    loved_foods: Optional[List[str]] = Field(None, description="List of foods they love")
    disliked_foods: Optional[List[str]] = Field(None, description="List of foods they dislike")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class UserProfile(BaseModel):
    """Main user profile model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    dietary_restrictions: List[str] = Field(default_factory=list, description="User's dietary restrictions")
    allergies: List[str] = Field(default_factory=list, description="User's allergies")
    taste_preferences: List[str] = Field(default_factory=list, description="User's taste preferences")
    meal_preferences: List[str] = Field(default_factory=list, description="User's meal preferences")
    kitchen_equipment: List[str] = Field(default_factory=list, description="Available kitchen equipment")
    weekly_budget: Optional[float] = Field(None, gt=0, description="Weekly meal budget")
    zip_code: Optional[str] = Field(None, description="User's zip code for local grocery stores")
    family_members: List[FamilyMember] = Field(default_factory=list, description="List of family members")
    preferred_grocers: List[str] = Field(default_factory=list, description="Preferred grocery stores")
    subscription: str = Field(default="free", description="Subscription tier")
    trial_ends_at: Optional[datetime] = Field(None, description="Trial subscription end date")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Profile last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('subscription')
    def validate_subscription(cls, v):
        """Validate subscription tier"""
        allowed_subscriptions = ["free", "basic", "premium"]
        if v not in allowed_subscriptions:
            raise ValueError(f'Subscription must be one of: {", ".join(allowed_subscriptions)}')
        return v

    @validator('weekly_budget')
    def validate_budget(cls, v):
        """Ensure budget is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError('Weekly budget must be positive')
        return v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        """Validate zip code format (5 digits)"""
        if v is not None:
            if not v.isdigit() or len(v) != 5:
                raise ValueError('Zip code must be exactly 5 digits')
        return v


class UserProfileCreate(BaseModel):
    """Schema for creating new user profiles"""
    dietary_restrictions: List[str] = Field(default_factory=list, description="User's dietary restrictions")
    allergies: List[str] = Field(default_factory=list, description="User's allergies")
    taste_preferences: List[str] = Field(default_factory=list, description="User's taste preferences")
    meal_preferences: List[str] = Field(default_factory=list, description="User's meal preferences")
    kitchen_equipment: List[str] = Field(default_factory=list, description="Available kitchen equipment")
    weekly_budget: Optional[float] = Field(None, gt=0, description="Weekly meal budget")
    zip_code: Optional[str] = Field(None, description="User's zip code for local grocery stores")
    family_members: List[FamilyMemberCreate] = Field(default_factory=list, description="List of family members")
    preferred_grocers: List[str] = Field(default_factory=list, description="Preferred grocery stores")
    subscription: str = Field(default="free", description="Subscription tier")
    trial_ends_at: Optional[datetime] = Field(None, description="Trial subscription end date")

    @validator('subscription')
    def validate_subscription(cls, v):
        """Validate subscription tier"""
        allowed_subscriptions = ["free", "basic", "premium"]
        if v not in allowed_subscriptions:
            raise ValueError(f'Subscription must be one of: {", ".join(allowed_subscriptions)}')
        return v

    @validator('weekly_budget')
    def validate_budget(cls, v):
        """Ensure budget is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError('Weekly budget must be positive')
        return v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        """Validate zip code format (5 digits)"""
        if v is not None:
            if not v.isdigit() or len(v) != 5:
                raise ValueError('Zip code must be exactly 5 digits')
        return v


class UserProfileUpdate(BaseModel):
    """Schema for updating existing user profiles"""
    dietary_restrictions: Optional[List[str]] = Field(None, description="User's dietary restrictions")
    allergies: Optional[List[str]] = Field(None, description="User's allergies")
    taste_preferences: Optional[List[str]] = Field(None, description="User's taste preferences")
    meal_preferences: Optional[List[str]] = Field(None, description="User's meal preferences")
    kitchen_equipment: Optional[List[str]] = Field(None, description="Available kitchen equipment")
    weekly_budget: Optional[float] = Field(None, gt=0, description="Weekly meal budget")
    zip_code: Optional[str] = Field(None, description="User's zip code for local grocery stores")
    family_members: Optional[List[FamilyMemberUpdate]] = Field(None, description="List of family members")
    preferred_grocers: Optional[List[str]] = Field(None, description="Preferred grocery stores")
    subscription: Optional[str] = Field(None, description="Subscription tier")
    trial_ends_at: Optional[datetime] = Field(None, description="Trial subscription end date")

    @validator('subscription')
    def validate_subscription(cls, v):
        """Validate subscription tier"""
        if v is not None:
            allowed_subscriptions = ["free", "basic", "premium"]
            if v not in allowed_subscriptions:
                raise ValueError(f'Subscription must be one of: {", ".join(allowed_subscriptions)}')
        return v

    @validator('weekly_budget')
    def validate_budget(cls, v):
        """Ensure budget is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError('Weekly budget must be positive')
        return v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        """Validate zip code format (5 digits)"""
        if v is not None:
            if not v.isdigit() or len(v) != 5:
                raise ValueError('Zip code must be exactly 5 digits')
        return v