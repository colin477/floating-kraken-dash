"""
Pantry management router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.models.responses import SuccessResponse
from app.models.pantry import (
    PantryItemCreate,
    PantryItemUpdate,
    PantryItemResponse,
    PantryItemsListResponse,
    ExpiringItemsResponse,
    PantryStatsResponse,
    PantryCategory
)
from app.crud.pantry import (
    create_pantry_item,
    get_pantry_items,
    get_pantry_item_by_id,
    update_pantry_item,
    delete_pantry_item,
    get_expiring_items,
    get_pantry_stats,
    search_pantry_items,
    create_pantry_indexes
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_pantry_indexes()


@router.get("/", response_model=PantryItemsListResponse)
async def get_user_pantry_items(
    category: Optional[PantryCategory] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field (name, created_at, expiration_date, etc.)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all pantry items for the authenticated user"""
    user_id = str(current_user["_id"])
    
    result = await get_pantry_items(
        user_id=user_id,
        category=category,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pantry items"
        )
    
    return result


@router.post("/", response_model=PantryItemResponse, status_code=status.HTTP_201_CREATED)
async def add_pantry_item(
    item_data: PantryItemCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Add new pantry item for the authenticated user"""
    user_id = str(current_user["_id"])
    
    result = await create_pantry_item(user_id=user_id, item_data=item_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create pantry item. Item with this name may already exist."
        )
    
    return result


@router.get("/{item_id}", response_model=PantryItemResponse)
async def get_pantry_item(
    item_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get specific pantry item by ID"""
    user_id = str(current_user["_id"])
    
    result = await get_pantry_item_by_id(user_id=user_id, item_id=item_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pantry item not found"
        )
    
    return result


@router.put("/{item_id}", response_model=PantryItemResponse)
async def update_pantry_item_endpoint(
    item_id: str,
    update_data: PantryItemUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update pantry item by ID"""
    user_id = str(current_user["_id"])
    
    result = await update_pantry_item(user_id=user_id, item_id=item_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pantry item not found or no changes made"
        )
    
    return result


@router.delete("/{item_id}")
async def delete_pantry_item_endpoint(
    item_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete pantry item by ID"""
    user_id = str(current_user["_id"])
    
    success = await delete_pantry_item(user_id=user_id, item_id=item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pantry item not found"
        )
    
    return SuccessResponse(message="Pantry item deleted successfully")


@router.get("/expiring/items", response_model=ExpiringItemsResponse)
async def get_expiring_pantry_items(
    days_threshold: int = Query(7, ge=1, le=30, description="Days threshold for expiring soon"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get items expiring soon or already expired"""
    user_id = str(current_user["_id"])
    
    result = await get_expiring_items(user_id=user_id, days_threshold=days_threshold)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expiring items"
        )
    
    return result


@router.get("/stats/overview", response_model=PantryStatsResponse)
async def get_pantry_statistics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get pantry statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_pantry_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pantry statistics"
        )
    
    return result


@router.get("/search/items", response_model=List[PantryItemResponse])
async def search_pantry_items_endpoint(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(get_current_active_user)
):
    """Search pantry items by name"""
    user_id = str(current_user["_id"])
    
    results = await search_pantry_items(user_id=user_id, search_term=q, limit=limit)
    
    return results