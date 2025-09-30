"""
Onboarding middleware to ensure users complete onboarding before accessing protected features
"""

from fastapi import HTTPException, status, Depends
from app.utils.auth import get_current_active_user
from app.crud.profiles import get_onboarding_status


async def require_onboarding_complete(current_user: dict = Depends(get_current_active_user)) -> dict:
    """
    Dependency to ensure user has completed onboarding before accessing protected routes
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        dict: Current user if onboarding is complete
        
    Raises:
        HTTPException: 403 if onboarding is not complete
    """
    try:
        user_id = str(current_user["_id"])
        
        # Check onboarding status
        status_info = await get_onboarding_status(user_id)
        
        if not status_info.get("onboarding_completed", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Onboarding required",
                    "message": "Please complete your account setup to access this feature",
                    "onboarding_status": status_info
                }
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # If we can't check onboarding status, allow access but log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to check onboarding status for user {user_id}: {e}")
        return current_user