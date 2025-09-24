"""
Receipt processing router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import Optional, List
from datetime import date
from app.models.responses import SuccessResponse
from app.models.receipts import (
    ReceiptCreate,
    ReceiptUpdate,
    ReceiptResponse,
    ReceiptsListResponse,
    ReceiptProcessingResponse,
    AddToPantryRequest,
    AddToPantryResponse,
    ReceiptStatsResponse,
    ReceiptUploadRequest,
    ReceiptProcessingStatus
)
from app.crud.receipts import (
    create_receipt,
    get_receipts,
    get_receipt_by_id,
    update_receipt,
    delete_receipt,
    process_receipt_image,
    add_receipt_items_to_pantry,
    get_receipt_stats,
    create_receipt_indexes
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_receipt_indexes()


@router.post("/upload", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    receipt_data: ReceiptUploadRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a new receipt for processing"""
    user_id = str(current_user["_id"])
    
    # Convert ReceiptUploadRequest to ReceiptCreate
    create_data = ReceiptCreate(
        store_name=receipt_data.store_name,
        receipt_date=receipt_data.receipt_date,
        total_amount=receipt_data.total_amount,
        photo_url=None  # For now, we'll handle file uploads separately
    )
    
    result = await create_receipt(user_id=user_id, receipt_data=create_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create receipt"
        )
    
    return result


@router.get("/", response_model=ReceiptsListResponse)
async def get_user_receipts(
    store_name: Optional[str] = Query(None, description="Filter by store name"),
    start_date: Optional[date] = Query(None, description="Filter receipts from this date"),
    end_date: Optional[date] = Query(None, description="Filter receipts until this date"),
    processing_status: Optional[ReceiptProcessingStatus] = Query(None, description="Filter by processing status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Receipts per page"),
    sort_by: str = Query("receipt_date", description="Sort field (receipt_date, created_at, total_amount, etc.)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all receipts for the authenticated user"""
    user_id = str(current_user["_id"])
    
    result = await get_receipts(
        user_id=user_id,
        store_name=store_name,
        start_date=start_date,
        end_date=end_date,
        processing_status=processing_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipts"
        )
    
    return result


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get specific receipt by ID"""
    user_id = str(current_user["_id"])
    
    result = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return result


@router.put("/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt_endpoint(
    receipt_id: str,
    update_data: ReceiptUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update receipt by ID"""
    user_id = str(current_user["_id"])
    
    result = await update_receipt(user_id=user_id, receipt_id=receipt_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found or no changes made"
        )
    
    return result


@router.delete("/{receipt_id}")
async def delete_receipt_endpoint(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete receipt by ID"""
    user_id = str(current_user["_id"])
    
    success = await delete_receipt(user_id=user_id, receipt_id=receipt_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return SuccessResponse(message="Receipt deleted successfully")


@router.post("/{receipt_id}/process", response_model=ReceiptProcessingResponse)
async def process_receipt(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Process receipt image to extract items using AI"""
    user_id = str(current_user["_id"])
    
    # First check if receipt exists
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Check if already processed
    if receipt.processing_status == ReceiptProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt has already been processed"
        )
    
    # Check if currently processing
    if receipt.processing_status == ReceiptProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt is currently being processed"
        )
    
    result = await process_receipt_image(user_id=user_id, receipt_id=receipt_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process receipt"
        )
    
    return result


@router.post("/{receipt_id}/add-to-pantry", response_model=AddToPantryResponse)
async def add_receipt_items_to_pantry_endpoint(
    receipt_id: str,
    request_data: AddToPantryRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Add selected receipt items to user's pantry"""
    user_id = str(current_user["_id"])
    
    # First check if receipt exists and is processed
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if receipt.processing_status != ReceiptProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt must be processed before adding items to pantry"
        )
    
    if not receipt.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt has no items to add to pantry"
        )
    
    result = await add_receipt_items_to_pantry(
        user_id=user_id,
        receipt_id=receipt_id,
        selected_items=request_data.selected_items,
        expiration_days=request_data.expiration_days or 7
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add items to pantry"
        )
    
    return result


@router.get("/stats/overview", response_model=ReceiptStatsResponse)
async def get_receipt_statistics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get receipt statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_receipt_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipt statistics"
        )
    
    return result


# Legacy endpoints for backward compatibility (these were in the original placeholder)
@router.post("/process")
async def process_receipt_legacy():
    """Legacy endpoint - redirects to new pattern"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been moved. Use POST /receipts/{receipt_id}/process instead"
    )


@router.post("/confirm")
async def confirm_receipt_items_legacy():
    """Legacy endpoint - redirects to new pattern"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been moved. Use POST /receipts/{receipt_id}/add-to-pantry instead"
    )


# File upload endpoint for receipt images (future enhancement)
@router.post("/{receipt_id}/upload-image")
async def upload_receipt_image(
    receipt_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload receipt image file (placeholder for future implementation)"""
    user_id = str(current_user["_id"])
    
    # Check if receipt exists
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # For now, just return success - in the future, this would:
    # 1. Save the file to cloud storage (S3, etc.)
    # 2. Update the receipt with the photo_url
    # 3. Optionally trigger automatic processing
    
    return SuccessResponse(
        message=f"Receipt image upload placeholder - file {file.filename} would be processed"
    )