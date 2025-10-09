"""
Nutrition analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
import time
import logging

from app.models.responses import SuccessResponse
from app.models.nutrition import (
    IngredientLookupRequest,
    IngredientLookupResponse,
    BulkIngredientAnalysisRequest,
    BulkIngredientAnalysisResponse,
    RecipeNutritionRequest,
    RecipeNutritionResponse,
    NutritionServiceStatus
)
from app.models.recipes import RecipeResponse
from app.services.nutrition_lookup_service import nutrition_lookup_service
from app.services.recipe_nutrition_service import recipe_nutrition_service
from app.services.usda_nutrition_service import usda_nutrition_service
from app.crud.recipes import get_recipe_by_id
from app.utils.auth import get_current_active_user
from app.middleware.onboarding import require_onboarding_complete

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingredient-lookup", response_model=IngredientLookupResponse)
async def lookup_ingredient_nutrition(
    request_data: IngredientLookupRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Look up nutritional information for a single ingredient
    
    This endpoint searches for nutritional data using the USDA Food Data Central API
    with fallback to estimated values for common ingredients.
    
    **Features:**
    - USDA Food Data Central integration
    - Intelligent ingredient name matching
    - Quantity and unit-specific calculations
    - Caching for improved performance
    - Fallback nutritional estimates
    
    **Example Request:**
    ```json
    {
        "ingredient_name": "chicken breast",
        "quantity": 150,
        "unit": "g",
        "preparation_method": "grilled"
    }
    ```
    """
    start_time = time.time()
    
    try:
        result = await nutrition_lookup_service.lookup_ingredient(request_data)
        
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        logger.info(f"Ingredient lookup completed for '{request_data.ingredient_name}' - Success: {result.success}")
        return result
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error in ingredient lookup: {e}")
        
        return IngredientLookupResponse(
            success=False,
            ingredient_name=request_data.ingredient_name,
            matches=[],
            best_match=None,
            confidence_score=0.0,
            data_source="Error",
            processing_time_ms=processing_time,
            error_message=f"Lookup failed: {str(e)}"
        )


@router.post("/bulk-ingredient-analysis", response_model=BulkIngredientAnalysisResponse)
async def analyze_bulk_ingredients(
    request_data: BulkIngredientAnalysisRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Analyze nutritional information for multiple ingredients in bulk
    
    This endpoint processes multiple ingredients simultaneously and can optionally
    combine their nutritional profiles into a single summary.
    
    **Features:**
    - Concurrent processing for efficiency
    - Optional combined nutrition summary
    - Individual results for each ingredient
    - Rate limiting to prevent API abuse
    
    **Use Cases:**
    - Analyze all ingredients in a recipe
    - Get nutrition for shopping list items
    - Compare multiple ingredient options
    
    **Example Request:**
    ```json
    {
        "ingredients": [
            {"ingredient_name": "chicken breast", "quantity": 150, "unit": "g"},
            {"ingredient_name": "broccoli", "quantity": 100, "unit": "g"},
            {"ingredient_name": "rice", "quantity": 75, "unit": "g"}
        ],
        "combine_results": true
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Validate request size
        if len(request_data.ingredients) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 ingredients allowed per request"
            )
        
        result = await nutrition_lookup_service.bulk_ingredient_analysis(request_data)
        
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        logger.info(f"Bulk ingredient analysis completed - {result.successful_lookups}/{result.total_processed} successful")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error in bulk ingredient analysis: {e}")
        
        return BulkIngredientAnalysisResponse(
            success=False,
            individual_results=[],
            combined_nutrition=None,
            total_processed=len(request_data.ingredients),
            successful_lookups=0,
            processing_time_ms=processing_time
        )


@router.get("/recipes/{recipe_id}/nutrition", response_model=RecipeNutritionResponse)
async def get_recipe_nutrition_analysis(
    recipe_id: str,
    force_refresh: bool = Query(default=False, description="Force refresh of cached analysis"),
    include_detailed_breakdown: bool = Query(default=True, description="Include detailed ingredient breakdown"),
    apply_user_goals: bool = Query(default=True, description="Apply user's nutritional goals"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Get comprehensive nutritional analysis for a recipe
    
    This endpoint analyzes all ingredients in a recipe and provides detailed
    nutritional information including macronutrients, vitamins, minerals,
    dietary compliance, and health warnings.
    
    **Features:**
    - Complete nutritional breakdown per serving
    - Ingredient contribution analysis
    - Dietary restriction compliance checking
    - Nutritional warnings and recommendations
    - Health and nutrition density scoring
    - Caching for improved performance
    
    **Analysis Includes:**
    - Macronutrients (calories, protein, carbs, fat, fiber, etc.)
    - Vitamins (A, C, D, E, K, B-complex)
    - Minerals (calcium, iron, magnesium, etc.)
    - Allergen detection
    - Dietary restriction compliance
    - Nutritional warnings (high sodium, etc.)
    - Health score (0-100)
    """
    start_time = time.time()
    user_id = str(current_user["_id"])
    
    try:
        # Get the recipe
        recipe = await get_recipe_by_id(user_id=user_id, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Convert RecipeResponse to Recipe model for analysis
        from app.models.recipes import Recipe, RecipeIngredient
        recipe_model = Recipe(
            id=recipe.id,
            user_id=recipe.user_id,
            title=recipe.title,
            description=recipe.description,
            ingredients=[RecipeIngredient(**ing.dict()) for ing in recipe.ingredients],
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            servings=recipe.servings,
            difficulty=recipe.difficulty,
            tags=recipe.tags,
            meal_types=recipe.meal_types,
            dietary_restrictions=recipe.dietary_restrictions,
            nutrition_info=recipe.nutrition_info,
            photo_url=recipe.photo_url,
            source_url=recipe.source_url,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at
        )
        
        # Perform nutritional analysis
        nutrition_analysis = await recipe_nutrition_service.analyze_recipe_nutrition(
            recipe=recipe_model,
            force_refresh=force_refresh,
            include_detailed_breakdown=include_detailed_breakdown
        )
        
        if not nutrition_analysis:
            processing_time = (time.time() - start_time) * 1000
            return RecipeNutritionResponse(
                success=False,
                recipe_id=recipe_id,
                nutrition_analysis=None,
                dietary_analysis=None,
                processing_time_ms=processing_time,
                error_message="Failed to analyze recipe nutrition"
            )
        
        # Perform dietary analysis
        dietary_analysis = await recipe_nutrition_service.analyze_dietary_compliance(
            recipe=recipe_model,
            nutrition_analysis=nutrition_analysis
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Recipe nutrition analysis completed for '{recipe.title}' - Confidence: {nutrition_analysis.analysis_confidence:.2f}")
        
        return RecipeNutritionResponse(
            success=True,
            recipe_id=recipe_id,
            nutrition_analysis=nutrition_analysis,
            dietary_analysis=dietary_analysis,
            processing_time_ms=processing_time,
            cache_used=not force_refresh
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error analyzing recipe nutrition: {e}")
        
        return RecipeNutritionResponse(
            success=False,
            recipe_id=recipe_id,
            nutrition_analysis=None,
            dietary_analysis=None,
            processing_time_ms=processing_time,
            error_message=f"Analysis failed: {str(e)}"
        )


@router.post("/recipes/{recipe_id}/nutrition", response_model=RecipeNutritionResponse)
async def analyze_recipe_nutrition(
    recipe_id: str,
    request_data: RecipeNutritionRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Analyze recipe nutrition with custom options
    
    This endpoint provides the same functionality as the GET endpoint but allows
    for more detailed configuration through the request body.
    """
    start_time = time.time()
    user_id = str(current_user["_id"])
    
    try:
        # Get the recipe
        recipe = await get_recipe_by_id(user_id=user_id, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Convert to Recipe model
        from app.models.recipes import Recipe, RecipeIngredient
        recipe_model = Recipe(
            id=recipe.id,
            user_id=recipe.user_id,
            title=recipe.title,
            description=recipe.description,
            ingredients=[RecipeIngredient(**ing.dict()) for ing in recipe.ingredients],
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            servings=recipe.servings,
            difficulty=recipe.difficulty,
            tags=recipe.tags,
            meal_types=recipe.meal_types,
            dietary_restrictions=recipe.dietary_restrictions,
            nutrition_info=recipe.nutrition_info,
            photo_url=recipe.photo_url,
            source_url=recipe.source_url,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at
        )
        
        # Perform analysis with custom options
        nutrition_analysis = await recipe_nutrition_service.analyze_recipe_nutrition(
            recipe=recipe_model,
            force_refresh=request_data.force_refresh,
            include_detailed_breakdown=request_data.include_detailed_breakdown
        )
        
        if not nutrition_analysis:
            processing_time = (time.time() - start_time) * 1000
            return RecipeNutritionResponse(
                success=False,
                recipe_id=recipe_id,
                nutrition_analysis=None,
                dietary_analysis=None,
                processing_time_ms=processing_time,
                error_message="Failed to analyze recipe nutrition"
            )
        
        # Perform dietary analysis
        dietary_analysis = await recipe_nutrition_service.analyze_dietary_compliance(
            recipe=recipe_model,
            nutrition_analysis=nutrition_analysis
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecipeNutritionResponse(
            success=True,
            recipe_id=recipe_id,
            nutrition_analysis=nutrition_analysis,
            dietary_analysis=dietary_analysis,
            processing_time_ms=processing_time,
            cache_used=not request_data.force_refresh
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error analyzing recipe nutrition: {e}")
        
        return RecipeNutritionResponse(
            success=False,
            recipe_id=recipe_id,
            nutrition_analysis=None,
            dietary_analysis=None,
            processing_time_ms=processing_time,
            error_message=f"Analysis failed: {str(e)}"
        )


@router.get("/service-status", response_model=Dict[str, Any])
async def get_nutrition_service_status(
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Get the current status of all nutrition services
    
    This endpoint provides information about the availability and performance
    of the nutrition analysis services, including API connectivity, cache
    performance, and service health metrics.
    
    **Status Information:**
    - USDA API connectivity and rate limits
    - Cache performance metrics
    - Service availability and errors
    - Processing statistics
    """
    try:
        # Get status from all services
        usda_status = usda_nutrition_service.get_service_status()
        lookup_status = nutrition_lookup_service.get_service_status()
        
        return {
            "nutrition_services": {
                "usda_food_data_central": usda_status.dict(),
                "nutrition_lookup_service": lookup_status.dict()
            },
            "overall_status": {
                "healthy": usda_status.is_available or lookup_status.is_available,
                "primary_data_source": "USDA Food Data Central" if usda_status.is_available else "Fallback Database",
                "cache_enabled": lookup_status.cache_enabled,
                "demo_mode": not usda_status.api_key_configured
            },
            "capabilities": {
                "ingredient_lookup": True,
                "bulk_analysis": True,
                "recipe_analysis": True,
                "dietary_compliance": True,
                "nutritional_warnings": True,
                "allergen_detection": True,
                "health_scoring": True
            },
            "supported_nutrients": {
                "macronutrients": [
                    "calories", "protein", "carbohydrates", "dietary_fiber",
                    "sugars", "total_fat", "saturated_fat", "trans_fat", "cholesterol", "sodium"
                ],
                "vitamins": [
                    "vitamin_a", "vitamin_c", "vitamin_d", "vitamin_e", "vitamin_k",
                    "thiamin", "riboflavin", "niacin", "vitamin_b6", "folate", "vitamin_b12"
                ],
                "minerals": [
                    "calcium", "iron", "magnesium", "phosphorus", "potassium",
                    "zinc", "copper", "manganese", "selenium"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting nutrition service status: {e}")
        return {
            "nutrition_services": {},
            "overall_status": {
                "healthy": False,
                "error": str(e)
            },
            "capabilities": {},
            "supported_nutrients": {}
        }


@router.post("/clear-cache")
async def clear_nutrition_cache(
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Clear expired nutrition cache entries
    
    This endpoint clears expired cache entries to free up storage space
    and ensure data freshness. Only expired entries are removed.
    """
    try:
        await nutrition_lookup_service.clear_expired_cache()
        
        logger.info("Nutrition cache cleared successfully")
        return SuccessResponse(message="Expired nutrition cache entries cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing nutrition cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/search-ingredients")
async def search_ingredients(
    query: str = Query(..., min_length=2, description="Ingredient search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Search for ingredients in the USDA database
    
    This endpoint searches the USDA Food Data Central database for ingredients
    matching the provided query. Useful for ingredient selection and validation.
    
    **Features:**
    - Fuzzy string matching
    - Ranked results by relevance
    - Basic ingredient information
    - Data source indicators
    """
    try:
        async with usda_nutrition_service:
            results = await usda_nutrition_service.search_ingredients(query, limit)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching ingredients: {e}")
        return {
            "success": False,
            "query": query,
            "results": [],
            "total_found": 0,
            "error": str(e)
        }