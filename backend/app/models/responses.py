"""
Pydantic response models for API endpoints
"""

from pydantic import BaseModel, validator
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

class OnboardingStatusResponse(BaseModel):
    """Response model for onboarding status check"""
    onboarding_completed: bool
    has_profile: bool
    user_id: str
    current_step: Optional[str] = None
    plan_selected: bool = False
    profile_completed: bool = False
    setup_level: Optional[str] = None
    plan_type: Optional[str] = None

class PlanSelectionRequest(BaseModel):
    """Request model for plan selection during onboarding"""
    plan_type: str
    setup_level: str
    trial_ends_at: Optional[datetime] = None
    
    @validator('plan_type')
    def validate_plan_type(cls, v):
        """Validate plan type"""
        allowed_plans = ["free", "basic", "premium"]
        if v not in allowed_plans:
            raise ValueError(f'Plan type must be one of: {", ".join(allowed_plans)}')
        return v
    
    @validator('setup_level')
    def validate_setup_level(cls, v):
        """Validate setup level"""
        allowed_levels = ["basic", "medium", "full"]
        if v not in allowed_levels:
            raise ValueError(f'Setup level must be one of: {", ".join(allowed_levels)}')
        return v

class ProfileOnboardingComplete(BaseModel):
    """Request model for marking onboarding as complete"""
    onboarding_completed: bool = True