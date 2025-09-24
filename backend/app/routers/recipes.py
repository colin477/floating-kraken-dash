"""
Recipe management router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.models.responses import SuccessResponse
from app.models.recipes import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipesListResponse,
    RecipeSearchResponse,
    RecipeStatsResponse,
    DifficultyLevel,
    MealType,
    DietaryRestriction
)
from app.crud.recipes import (
    create_recipe,
    get_recipes,
    get_recipe_by_id,
    update_recipe,
    delete_recipe,
    search_recipes,
    get_recipe_stats,
    get_recipes_by_ingredients,
    create_recipe_indexes
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_recipe_indexes()


@router.get("/", response_model=RecipesListResponse)
async def get_user_recipes(
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    meal_type: Optional[MealType] = Query(None, description="Filter by meal type"),
    dietary_restrictions: Optional[List[DietaryRestriction]] = Query(None, description="Filter by dietary restrictions"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    max_prep_time: Optional[int] = Query(None, ge=0, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=0, description="Maximum cook time in minutes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Recipes per page"),
    sort_by: str = Query("created_at", description="Sort field (title, created_at, prep_time, cook_time, difficulty)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's recipes with filtering by source/tags"""
    user_id = str(current_user["_id"])
    
    result = await get_recipes(
        user_id=user_id,
        difficulty=difficulty,
        meal_type=meal_type,
        dietary_restrictions=dietary_restrictions,
        tags=tags,
        max_prep_time=max_prep_time,
        max_cook_time=max_cook_time,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipes"
        )
    
    return result


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_recipe(
    recipe_data: RecipeCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create new recipe"""
    user_id = str(current_user["_id"])
    
    result = await create_recipe(user_id=user_id, recipe_data=recipe_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create recipe"
        )
    
    return result


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get specific recipe"""
    user_id = str(current_user["_id"])
    
    result = await get_recipe_by_id(user_id=user_id, recipe_id=recipe_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return result


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe_endpoint(
    recipe_id: str,
    update_data: RecipeUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update recipe"""
    user_id = str(current_user["_id"])
    
    result = await update_recipe(user_id=user_id, recipe_id=recipe_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or no changes made"
        )
    
    return result


@router.delete("/{recipe_id}")
async def delete_recipe_endpoint(
    recipe_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete recipe"""
    user_id = str(current_user["_id"])
    
    success = await delete_recipe(user_id=user_id, recipe_id=recipe_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return SuccessResponse(message="Recipe deleted successfully")


@router.get("/search/recipes", response_model=RecipeSearchResponse)
async def search_user_recipes(
    q: str = Query(..., min_length=1, description="Search term"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    meal_type: Optional[MealType] = Query(None, description="Filter by meal type"),
    dietary_restrictions: Optional[List[DietaryRestriction]] = Query(None, description="Filter by dietary restrictions"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    max_prep_time: Optional[int] = Query(None, ge=0, description="Maximum prep time in minutes"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(get_current_active_user)
):
    """Search recipes by title, description, and tags"""
    user_id = str(current_user["_id"])
    
    result = await search_recipes(
        user_id=user_id,
        search_term=q,
        difficulty=difficulty,
        meal_type=meal_type,
        dietary_restrictions=dietary_restrictions,
        tags=tags,
        max_prep_time=max_prep_time,
        limit=limit
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search recipes"
        )
    
    return result


@router.get("/my-recipes/all", response_model=RecipesListResponse)
async def get_my_recipes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Recipes per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all user's recipes (alias for main endpoint)"""
    user_id = str(current_user["_id"])
    
    result = await get_recipes(
        user_id=user_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipes"
        )
    
    return result


@router.get("/stats/overview", response_model=RecipeStatsResponse)
async def get_recipe_statistics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get recipe statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_recipe_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipe statistics"
        )
    
    return result


@router.get("/by-ingredients/search", response_model=List[RecipeResponse])
async def get_recipes_by_ingredients_endpoint(
    ingredients: List[str] = Query(..., description="List of ingredient names to search for"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get recipes that contain specific ingredients"""
    user_id = str(current_user["_id"])
    
    results = await get_recipes_by_ingredients(
        user_id=user_id,
        ingredient_names=ingredients,
        limit=limit
    )
    
    return results


@router.post("/from-photo")
async def analyze_meal_photo():
    """Analyze meal photo and generate recipe"""
    # TODO: Implement meal photo analysis logic with AI/ML service
    # This would integrate with image recognition and recipe generation AI
    return SuccessResponse(message="Meal photo analysis feature coming soon - requires AI/ML integration")


@router.post("/from-link")
async def extract_recipe_from_link():
    """Extract recipe from URL"""
    # TODO: Implement recipe extraction from link logic
    # This would involve web scraping and structured data extraction
    return SuccessResponse(message="Recipe extraction from URL feature coming soon - requires web scraping integration")