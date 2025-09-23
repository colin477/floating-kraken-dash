"""
Leftover management router
"""

from fastapi import APIRouter
from app.models.responses import SuccessResponse

router = APIRouter()

@router.post("/suggestions")
async def get_leftover_suggestions():
    """Get leftover recipe suggestions based on ingredients"""
    # TODO: Implement leftover suggestions logic
    return SuccessResponse(message="Get leftover suggestions endpoint - to be implemented")