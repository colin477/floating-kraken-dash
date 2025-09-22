"""
Pydantic response models for API endpoints
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str
    database_connected: bool
    timestamp: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """Standard success response model"""
    message: str
    data: Optional[Dict[str, Any]] = None

class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str

class UserResponse(BaseModel):
    """User information response model"""
    id: str
    email: str
    name: str
    subscription: str
    created_at: datetime
    updated_at: datetime