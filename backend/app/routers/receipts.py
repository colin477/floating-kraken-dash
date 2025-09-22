"""
Receipt processing router
"""

from fastapi import APIRouter
from app.models.responses import SuccessResponse

router = APIRouter()

@router.post("/process")
async def process_receipt():
    """Process receipt image, returns identified items"""
    # TODO: Implement receipt processing logic
    return SuccessResponse(message="Process receipt endpoint - to be implemented")

@router.post("/confirm")
async def confirm_receipt_items():
    """Confirm processed items and add to pantry"""
    # TODO: Implement confirm receipt items logic
    return SuccessResponse(message="Confirm receipt items endpoint - to be implemented")

@router.get("/")
async def get_receipt_history():
    """Get user's receipt history"""
    # TODO: Implement get receipt history logic
    return SuccessResponse(message="Get receipt history endpoint - to be implemented")