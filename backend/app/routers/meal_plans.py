"""
Meal planning router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import date
from app.models.responses import SuccessResponse
from app.models.meal_plans import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    MealPlansListResponse,
    MealPlanGenerationRequest,
    MealPlanGenerationResponse,
    MealPlanStatsResponse,
    MealPlanStatus,
    MealType,
    DayOfWeek
)
from app.crud.meal_plans import (
    create_meal_plan,
    get_meal_plans,
    get_meal_plan_by_id,
    update_meal_plan,
    delete_meal_plan,
    generate_meal_plan,
    get_meal_plan_stats,
    create_meal_plan_indexes
)
from app.utils.auth import get_current_active_user
from app.middleware.onboarding import require_onboarding_complete

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_meal_plan_indexes()


@router.get("/", response_model=MealPlansListResponse)
async def get_user_meal_plans(
    status: Optional[MealPlanStatus] = Query(None, description="Filter by meal plan status"),
    start_date: Optional[date] = Query(None, description="Filter by week starting date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by week starting date (to)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Meal plans per page"),
    sort_by: str = Query("created_at", description="Sort field (created_at, week_starting, title, etc.)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get user's meal plans with filtering by status and date range"""
    user_id = str(current_user["_id"])
    
    result = await get_meal_plans(
        user_id=user_id,
        status=status,
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
            detail="Failed to retrieve meal plans"
        )
    
    return result


@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_new_meal_plan(
    meal_plan_data: MealPlanCreate,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Create new meal plan"""
    user_id = str(current_user["_id"])
    
    result = await create_meal_plan(user_id=user_id, meal_plan_data=meal_plan_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create meal plan"
        )
    
    return result


@router.get("/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get specific meal plan"""
    user_id = str(current_user["_id"])
    
    result = await get_meal_plan_by_id(user_id=user_id, meal_plan_id=meal_plan_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    return result


@router.put("/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan_endpoint(
    meal_plan_id: str,
    update_data: MealPlanUpdate,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Update meal plan"""
    user_id = str(current_user["_id"])
    
    result = await update_meal_plan(user_id=user_id, meal_plan_id=meal_plan_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found or no changes made"
        )
    
    return result


@router.delete("/{meal_plan_id}")
async def delete_meal_plan_endpoint(
    meal_plan_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Delete meal plan"""
    user_id = str(current_user["_id"])
    
    success = await delete_meal_plan(user_id=user_id, meal_plan_id=meal_plan_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    return SuccessResponse(message="Meal plan deleted successfully")


@router.post("/generate", response_model=MealPlanGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_ai_meal_plan(
    generation_request: MealPlanGenerationRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Generate AI-powered meal plan based on user preferences and pantry items
    
    This endpoint creates a comprehensive meal plan with:
    - Planned meals for specified days and meal types
    - Shopping list with estimated costs
    - Budget consideration
    - Dietary restrictions and preferences
    """
    user_id = str(current_user["_id"])
    
    result = await generate_meal_plan(user_id=user_id, generation_request=generation_request)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate meal plan. Please try again."
        )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meal plan generation failed: {result.generation_notes}"
        )
    
    return result


@router.get("/stats/overview", response_model=MealPlanStatsResponse)
async def get_meal_plan_statistics(
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get meal plan statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_meal_plan_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meal plan statistics"
        )
    
    return result


@router.get("/current/active", response_model=List[MealPlanResponse])
async def get_current_active_meal_plans(
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get currently active meal plans for the user"""
    user_id = str(current_user["_id"])
    
    result = await get_meal_plans(
        user_id=user_id,
        status=MealPlanStatus.ACTIVE,
        page=1,
        page_size=10,
        sort_by="week_starting",
        sort_order="desc"
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active meal plans"
        )
    
    return result.meal_plans


@router.put("/{meal_plan_id}/status", response_model=MealPlanResponse)
async def update_meal_plan_status(
    meal_plan_id: str,
    new_status: MealPlanStatus,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Update meal plan status (draft, active, completed, archived)"""
    user_id = str(current_user["_id"])
    
    update_data = MealPlanUpdate(status=new_status)
    result = await update_meal_plan(user_id=user_id, meal_plan_id=meal_plan_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    return result


@router.get("/{meal_plan_id}/shopping-list", response_model=List[dict])
async def get_meal_plan_shopping_list(
    meal_plan_id: str,
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get shopping list for a specific meal plan"""
    user_id = str(current_user["_id"])
    
    meal_plan = await get_meal_plan_by_id(user_id=user_id, meal_plan_id=meal_plan_id)
    
    if meal_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    return [item.dict() for item in meal_plan.shopping_list]


@router.post("/{meal_plan_id}/duplicate", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_meal_plan(
    meal_plan_id: str,
    new_week_starting: date = Query(..., description="Week starting date for the duplicated plan"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Duplicate an existing meal plan for a new week"""
    user_id = str(current_user["_id"])
    
    # Get the original meal plan
    original_plan = await get_meal_plan_by_id(user_id=user_id, meal_plan_id=meal_plan_id)
    
    if original_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    # Create new meal plan based on the original
    new_plan_data = MealPlanCreate(
        title=f"{original_plan.title} (Copy)",
        description=f"Duplicated from week of {original_plan.week_starting}",
        week_starting=new_week_starting,
        budget_target=original_plan.budget_target,
        preferences=original_plan.preferences_used
    )
    
    # Create the new meal plan
    new_plan = await create_meal_plan(user_id=user_id, meal_plan_data=new_plan_data)
    
    if new_plan is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate meal plan"
        )
    
    # Copy meals and shopping list from original
    update_data = MealPlanUpdate(
        meals=original_plan.meals,
        shopping_list=original_plan.shopping_list,
        total_estimated_cost=original_plan.total_estimated_cost
    )
    
    updated_plan = await update_meal_plan(user_id=user_id, meal_plan_id=new_plan.id, update_data=update_data)
    
    if updated_plan is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to copy meal plan content"
        )
    
    return updated_plan


@router.get("/templates/suggestions", response_model=List[dict])
async def get_meal_plan_template_suggestions(
    meal_types: List[MealType] = Query(default=[MealType.DINNER], description="Meal types to get suggestions for"),
    dietary_restrictions: List[str] = Query(default=[], description="Dietary restrictions to consider"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get meal plan template suggestions based on user preferences"""
    # Mock template suggestions - in production, this would be more sophisticated
    templates = [
        {
            "id": "family_friendly",
            "title": "Family Friendly Week",
            "description": "Easy meals that kids and adults will love",
            "meal_types": [mt.value for mt in meal_types],
            "estimated_cost": 85.00,
            "prep_time_avg": 25
        },
        {
            "id": "quick_easy",
            "title": "Quick & Easy",
            "description": "30-minute meals for busy weeknights",
            "meal_types": [mt.value for mt in meal_types],
            "estimated_cost": 75.00,
            "prep_time_avg": 20
        },
        {
            "id": "healthy_balanced",
            "title": "Healthy & Balanced",
            "description": "Nutritious meals with balanced macros",
            "meal_types": [mt.value for mt in meal_types],
            "estimated_cost": 95.00,
            "prep_time_avg": 35
        },
        {
            "id": "budget_conscious",
            "title": "Budget Conscious",
            "description": "Delicious meals that won't break the bank",
            "meal_types": [mt.value for mt in meal_types],
            "estimated_cost": 60.00,
            "prep_time_avg": 30
        }
    ]
    
    # Filter based on dietary restrictions if provided
    if dietary_restrictions:
        # In production, this would filter templates based on actual dietary compatibility
        pass
    
    return templates