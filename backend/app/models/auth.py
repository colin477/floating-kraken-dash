"""
Pydantic models for authentication and user management
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class User(BaseModel):
    """User model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    password_hash: str
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: str
    email: str
    full_name: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response with token and user info"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class GoogleOAuthRequest(BaseModel):
    """Schema for Google OAuth token verification request"""
    id_token: str = Field(..., description="Google ID token from frontend")


class GoogleOAuthCallback(BaseModel):
    """Schema for Google OAuth callback data"""
    code: str = Field(..., description="Authorization code from Google")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class GoogleUserInfo(BaseModel):
    """Schema for Google user profile information"""
    email: EmailStr
    name: str
    picture: Optional[str] = None
    email_verified: bool = True
    google_id: str = Field(..., description="Google user ID")