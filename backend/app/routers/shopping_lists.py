"""
Shopping list management router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import date
from app.models.responses import SuccessResponse
from app.models.shopping_lists import (
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingListResponse,
    ShoppingListsListResponse,
    ShoppingListStatsResponse,
    ShoppingItemUpdate,
    BulkItemUpdateRequest,
    BulkItemUpdateResponse,
    ShoppingListStatus,
    ShoppingListCategory
)
from app.crud.shopping_lists import (
    create_shopping_list,
    get_shopping_lists,
    get_shopping_list_by_id,
    update_shopping_list,
    delete_shopping_list,
    update_shopping_item,
    bulk_update_shopping_items,
    get_shopping_list_stats,
    create_shopping_list_indexes
)
from app.utils.auth import get_current_active_user
from app.middleware.onboarding import require_onboarding_complete

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_shopping_list_indexes()


@router.get("/", response_model=ShoppingListsListResponse)
async def get_user_shopping_lists(
    status: Optional[ShoppingListStatus] = Query(None, description="Filter by shopping list status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    store: Optional[str] = Query(None, description="Filter by store"),
    start_date: Optional[date] = Query(None, description="Filter by shopping date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by shopping date (to)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Shopping lists per page"),
    sort_by: str = Query("created_at", description="Sort field (created_at, shopping_date, title, etc.)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get user's shopping lists with filtering and pagination"""
    user_id = str(current_user["_id"])
    
    result = await get_shopping_lists(
        user_id=user_id,
        status=status,
        tags=tags,
        store=store,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shopping lists"
        )
    
    return result


@router.post("/", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_new_shopping_list(
    shopping_list_data: ShoppingListCreate,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Create new shopping list"""
    user_id = str(current_user["_id"])
    
    result = await create_shopping_list(user_id=user_id, shopping_list_data=shopping_list_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create shopping list"
        )
    
    return result


@router.get("/{shopping_list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(
    shopping_list_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get specific shopping list"""
    user_id = str(current_user["_id"])
    
    result = await get_shopping_list_by_id(user_id=user_id, shopping_list_id=shopping_list_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    return result


@router.put("/{shopping_list_id}", response_model=ShoppingListResponse)
async def update_shopping_list_endpoint(
    shopping_list_id: str,
    update_data: ShoppingListUpdate,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Update shopping list"""
    user_id = str(current_user["_id"])
    
    result = await update_shopping_list(user_id=user_id, shopping_list_id=shopping_list_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or no changes made"
        )
    
    return result


@router.delete("/{shopping_list_id}")
async def delete_shopping_list_endpoint(
    shopping_list_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Delete shopping list"""
    user_id = str(current_user["_id"])
    
    success = await delete_shopping_list(user_id=user_id, shopping_list_id=shopping_list_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    return SuccessResponse(message="Shopping list deleted successfully")


@router.put("/{shopping_list_id}/items/{item_id}", response_model=ShoppingListResponse)
async def update_shopping_list_item(
    shopping_list_id: str,
    item_id: str,
    update_data: ShoppingItemUpdate,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Update specific item in shopping list"""
    user_id = str(current_user["_id"])
    
    result = await update_shopping_item(
        user_id=user_id,
        shopping_list_id=shopping_list_id,
        item_id=item_id,
        update_data=update_data
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list or item not found"
        )
    
    return result


@router.put("/{shopping_list_id}/items/bulk", response_model=BulkItemUpdateResponse)
async def bulk_update_shopping_list_items(
    shopping_list_id: str,
    bulk_request: BulkItemUpdateRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Bulk update multiple items in shopping list"""
    user_id = str(current_user["_id"])
    
    result = await bulk_update_shopping_items(
        user_id=user_id,
        shopping_list_id=shopping_list_id,
        bulk_request=bulk_request
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    return result


@router.get("/stats/overview", response_model=ShoppingListStatsResponse)
async def get_shopping_list_statistics(
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get shopping list statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_shopping_list_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shopping list statistics"
        )
    
    return result


@router.get("/active/current", response_model=List[ShoppingListResponse])
async def get_active_shopping_lists(
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get currently active shopping lists for the user"""
    user_id = str(current_user["_id"])
    
    result = await get_shopping_lists(
        user_id=user_id,
        status=ShoppingListStatus.ACTIVE,
        page=1,
        page_size=10,
        sort_by="created_at",
        sort_order="desc"
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active shopping lists"
        )
    
    return result.shopping_lists


@router.put("/{shopping_list_id}/status", response_model=ShoppingListResponse)
async def update_shopping_list_status(
    shopping_list_id: str,
    new_status: ShoppingListStatus,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Update shopping list status (active, completed, archived)"""
    user_id = str(current_user["_id"])
    
    update_data = ShoppingListUpdate(status=new_status)
    result = await update_shopping_list(user_id=user_id, shopping_list_id=shopping_list_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    return result


@router.post("/{shopping_list_id}/duplicate", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_shopping_list(
    shopping_list_id: str,
    new_title: Optional[str] = Query(None, description="Title for the duplicated list"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Duplicate an existing shopping list"""
    user_id = str(current_user["_id"])
    
    # Get the original shopping list
    original_list = await get_shopping_list_by_id(user_id=user_id, shopping_list_id=shopping_list_id)
    
    if original_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    # Create new shopping list based on the original
    new_list_data = ShoppingListCreate(
        title=new_title or f"{original_list.title} (Copy)",
        description=f"Duplicated from '{original_list.title}'",
        items=original_list.items,
        stores=original_list.stores,
        budget_limit=original_list.budget_limit,
        shopping_date=None,  # Reset shopping date
        tags=original_list.tags
    )
    
    # Create the new shopping list
    new_list = await create_shopping_list(user_id=user_id, shopping_list_data=new_list_data)
    
    if new_list is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate shopping list"
        )
    
    return new_list


@router.get("/{shopping_list_id}/summary", response_model=dict)
async def get_shopping_list_summary(
    shopping_list_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get shopping list summary with organized items by category and store"""
    user_id = str(current_user["_id"])
    
    shopping_list = await get_shopping_list_by_id(user_id=user_id, shopping_list_id=shopping_list_id)
    
    if shopping_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    # Organize items by category
    items_by_category = {}
    items_by_store = {}
    
    for item in shopping_list.items:
        # Group by category
        category = item.category.value if item.category else "other"
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item.dict())
        
        # Group by store
        store = item.store or "unspecified"
        if store not in items_by_store:
            items_by_store[store] = []
        items_by_store[store].append(item.dict())
    
    return {
        "shopping_list_id": shopping_list.id,
        "title": shopping_list.title,
        "total_items": len(shopping_list.items),
        "purchased_items": shopping_list.purchased_items_count,
        "completion_percentage": shopping_list.completion_percentage,
        "total_estimated_cost": shopping_list.total_estimated_cost,
        "total_actual_cost": shopping_list.total_actual_cost,
        "budget_limit": shopping_list.budget_limit,
        "budget_used_percentage": shopping_list.budget_used_percentage,
        "items_by_category": items_by_category,
        "items_by_store": items_by_store,
        "stores": shopping_list.stores,
        "shopping_date": shopping_list.shopping_date,
        "status": shopping_list.status
    }


@router.get("/templates/common", response_model=List[dict])
async def get_common_shopping_list_templates(
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get common shopping list templates"""
    # Mock templates - in production, these could be user-customizable or AI-generated
    templates = [
        {
            "id": "weekly_groceries",
            "title": "Weekly Groceries",
            "description": "Essential items for weekly grocery shopping",
            "categories": ["produce", "dairy", "meat", "grains", "pantry"],
            "estimated_items": 25
        },
        {
            "id": "quick_essentials",
            "title": "Quick Essentials",
            "description": "Must-have items for a quick grocery run",
            "categories": ["dairy", "produce", "bread"],
            "estimated_items": 10
        },
        {
            "id": "party_supplies",
            "title": "Party Supplies",
            "description": "Everything needed for hosting a party",
            "categories": ["beverages", "snacks", "frozen", "household"],
            "estimated_items": 20
        },
        {
            "id": "healthy_eating",
            "title": "Healthy Eating",
            "description": "Nutritious foods for a healthy lifestyle",
            "categories": ["produce", "lean_proteins", "whole_grains"],
            "estimated_items": 18
        },
        {
            "id": "meal_prep",
            "title": "Meal Prep Basics",
            "description": "Ingredients for weekly meal preparation",
            "categories": ["proteins", "vegetables", "grains", "containers"],
            "estimated_items": 15
        }
    ]
    
    return templates


@router.post("/from-meal-plan/{meal_plan_id}", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_shopping_list_from_meal_plan(
    meal_plan_id: str,
    list_title: Optional[str] = Query(None, description="Custom title for the shopping list"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Create a shopping list from a meal plan's shopping list"""
    user_id = str(current_user["_id"])
    
    # Get the meal plan (we'll need to import this function)
    from app.crud.meal_plans import get_meal_plan_by_id as get_meal_plan
    
    meal_plan = await get_meal_plan(user_id=user_id, meal_plan_id=meal_plan_id)
    
    if meal_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    if not meal_plan.shopping_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meal plan has no shopping list items"
        )
    
    # Convert meal plan shopping list items to shopping list items
    shopping_items = []
    for item in meal_plan.shopping_list:
        shopping_items.append(item)  # They should be compatible
    
    # Create shopping list
    shopping_list_data = ShoppingListCreate(
        title=list_title or f"Shopping for {meal_plan.title}",
        description=f"Generated from meal plan: {meal_plan.title}",
        items=shopping_items,
        budget_limit=meal_plan.budget_target,
        tags=["meal-plan", "generated"]
    )
    
    result = await create_shopping_list(user_id=user_id, shopping_list_data=shopping_list_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shopping list from meal plan"
        )
    
    return result