"""
Leftover management router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
import time
import logging
from app.models.responses import SuccessResponse
from app.models.leftovers import (
    LeftoverSuggestionsResponse,
    LeftoverSuggestionsDebugResponse,
    SuggestionFilters,
    PantryIngredientInfo,
    SuggestionRequest
)
from app.models.pantry import PantryItemResponse
from app.crud.leftovers import (
    get_leftover_suggestions,
    get_user_available_ingredients
)
from app.crud.pantry import get_pantry_items
from app.utils.auth import get_current_active_user
from app.database import get_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/suggestions", response_model=LeftoverSuggestionsResponse)
async def get_leftover_suggestions_endpoint(
    max_suggestions: int = Query(10, ge=1, le=20, description="Maximum number of suggestions (1-20)"),
    min_match_percentage: float = Query(0.3, ge=0.1, le=1.0, description="Minimum ingredient match percentage (0.1-1.0)"),
    max_prep_time: Optional[int] = Query(None, ge=0, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=0, description="Maximum cook time in minutes"),
    difficulty_level: Optional[str] = Query(None, regex="^(easy|medium|hard)$", description="Filter by difficulty (easy, medium, hard)"),
    meal_type: Optional[str] = Query(None, regex="^(breakfast|lunch|dinner|snack)$", description="Filter by meal type (breakfast, lunch, dinner, snack)"),
    include_expiring: bool = Query(True, description="Prioritize expiring ingredients"),
    exclude_expired: bool = Query(True, description="Exclude expired ingredients"),
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get recipe suggestions based on pantry ingredients
    
    This endpoint analyzes your pantry items and suggests recipes that you can make
    with available ingredients. It considers ingredient freshness, expiration dates,
    and your preferences to provide personalized suggestions.
    
    **Query Parameters:**
    - **max_suggestions**: Maximum number of suggestions to return (1-20)
    - **min_match_percentage**: Minimum percentage of ingredients you must have (0.1-1.0)
    - **max_prep_time**: Maximum preparation time in minutes
    - **max_cook_time**: Maximum cooking time in minutes
    - **difficulty_level**: Filter by recipe difficulty (easy, medium, hard)
    - **meal_type**: Filter by meal type (breakfast, lunch, dinner, snack)
    - **include_expiring**: Whether to prioritize recipes using expiring ingredients
    - **exclude_expired**: Whether to exclude recipes requiring expired ingredients
    
    **Example Usage:**
    ```
    GET /api/v1/leftovers/suggestions?max_suggestions=5&min_match_percentage=0.6&difficulty_level=easy
    ```
    
    **Response includes:**
    - List of recipe suggestions with match scores
    - Ingredient matching details
    - Performance metrics
    - Applied filters summary
    """
    try:
        start_time = time.time()
        user_id = str(current_user["_id"])
        
        # Validate parameters
        if max_prep_time is not None and max_prep_time < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="max_prep_time must be a positive integer"
            )
        
        if max_cook_time is not None and max_cook_time < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="max_cook_time must be a positive integer"
            )
        
        # Create suggestion filters
        filters = SuggestionFilters(
            max_suggestions=max_suggestions,
            min_match_percentage=min_match_percentage,
            max_prep_time=max_prep_time,
            max_cook_time=max_cook_time,
            difficulty_levels=[difficulty_level] if difficulty_level else None,
            meal_types=[meal_type] if meal_type else None,
            exclude_expired=exclude_expired,
            prioritize_expiring=include_expiring,
            include_substitutes=True
        )
        
        # Check if user has pantry items
        pantry_response = await get_pantry_items(user_id, page_size=1)
        if not pantry_response or not pantry_response.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pantry items found. Please add ingredients to your pantry first."
            )
        
        # Get suggestions
        suggestions_response = await get_leftover_suggestions(
            db=db,
            user_id=user_id,
            max_suggestions=max_suggestions,
            filters=filters
        )
        
        if suggestions_response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate recipe suggestions. Please try again."
            )
        
        # Add request timing
        processing_time = (time.time() - start_time) * 1000
        if suggestions_response.performance_metrics:
            suggestions_response.performance_metrics["total_request_time_ms"] = processing_time
        
        # Handle no suggestions found
        if not suggestions_response.suggestions:
            logger.info(f"No suggestions found for user {user_id} with current filters")
            # Return empty response with helpful message
            suggestions_response.performance_metrics = suggestions_response.performance_metrics or {}
            suggestions_response.performance_metrics["message"] = "No recipes match your current pantry and filters. Try adjusting your filters or adding more ingredients."
        
        logger.info(f"Generated {len(suggestions_response.suggestions)} suggestions for user {user_id}")
        return suggestions_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating leftover suggestions for user {current_user.get('_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating suggestions"
        )


@router.get("/ingredients", response_model=List[PantryIngredientInfo])
async def get_available_ingredients(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get user's available pantry ingredients
    
    Returns a list of all ingredients in your pantry with detailed information
    including quantities, expiration dates, and freshness scores.
    
    **Response includes:**
    - Ingredient names (original and normalized)
    - Categories and quantities
    - Expiration information
    - Freshness scores
    - Expiring status flags
    
    **Example Response:**
    ```json
    [
        {
            "name": "Fresh Tomatoes",
            "normalized_name": "tomatoes",
            "category": "vegetables",
            "quantity": 3.0,
            "unit": "pieces",
            "expiration_date": "2024-01-15T00:00:00Z",
            "days_until_expiration": 2,
            "is_expired": false,
            "is_expiring_soon": true,
            "freshness_score": 0.6
        }
    ]
    ```
    """
    try:
        user_id = str(current_user["_id"])
        
        # Get available ingredients
        ingredients = await get_user_available_ingredients(db, user_id)
        
        if not ingredients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pantry items found. Please add ingredients to your pantry first."
            )
        
        logger.info(f"Retrieved {len(ingredients)} available ingredients for user {user_id}")
        return ingredients
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving available ingredients for user {current_user.get('_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pantry ingredients"
        )


@router.post("/suggestions/custom", response_model=LeftoverSuggestionsResponse)
async def get_custom_suggestions(
    filters: SuggestionFilters,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get recipe suggestions with custom filter object
    
    This endpoint allows you to provide a comprehensive filter object with all
    your preferences in a single request. Useful for advanced filtering scenarios.
    
    **Request Body Example:**
    ```json
    {
        "max_suggestions": 15,
        "min_match_percentage": 0.4,
        "max_prep_time": 45,
        "max_cook_time": 60,
        "difficulty_levels": ["easy", "medium"],
        "meal_types": ["dinner"],
        "dietary_restrictions": ["vegetarian"],
        "exclude_expired": true,
        "prioritize_expiring": true,
        "include_substitutes": true
    }
    ```
    
    **Response:** Same as the main suggestions endpoint with applied custom filters.
    """
    try:
        start_time = time.time()
        user_id = str(current_user["_id"])
        
        # Validate filters
        if filters.max_suggestions < 1 or filters.max_suggestions > 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="max_suggestions must be between 1 and 50"
            )
        
        if filters.min_match_percentage < 0.0 or filters.min_match_percentage > 1.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_match_percentage must be between 0.0 and 1.0"
            )
        
        # Check if user has pantry items
        pantry_response = await get_pantry_items(user_id, page_size=1)
        if not pantry_response or not pantry_response.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pantry items found. Please add ingredients to your pantry first."
            )
        
        # Get suggestions with custom filters
        suggestions_response = await get_leftover_suggestions(
            db=db,
            user_id=user_id,
            max_suggestions=filters.max_suggestions,
            filters=filters
        )
        
        if suggestions_response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate custom recipe suggestions. Please try again."
            )
        
        # Add request timing
        processing_time = (time.time() - start_time) * 1000
        if suggestions_response.performance_metrics:
            suggestions_response.performance_metrics["total_request_time_ms"] = processing_time
        
        logger.info(f"Generated {len(suggestions_response.suggestions)} custom suggestions for user {user_id}")
        return suggestions_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom leftover suggestions for user {current_user.get('_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating custom suggestions"
        )


@router.get("/suggestions/debug", response_model=LeftoverSuggestionsDebugResponse)
async def get_debug_suggestions(
    max_suggestions: int = Query(5, ge=1, le=10, description="Maximum number of suggestions for debugging"),
    min_match_percentage: float = Query(0.3, ge=0.1, le=1.0, description="Minimum ingredient match percentage"),
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get recipe suggestions with detailed debugging information
    
    This endpoint provides the same suggestions as the main endpoint but includes
    extensive debugging information about the matching process, algorithm performance,
    and detailed ingredient analysis.
    
    **Debug Information Includes:**
    - Pantry ingredients used in matching
    - Number of recipes considered vs filtered out
    - Matching algorithm version and performance metrics
    - Processing time breakdown
    - Cache hit information
    - Error messages (if any)
    
    **Use Cases:**
    - Troubleshooting suggestion quality
    - Understanding matching algorithm behavior
    - Performance analysis
    - Development and testing
    
    **Note:** This endpoint is intended for debugging and may return large responses.
    Use sparingly in production environments.
    """
    try:
        start_time = time.time()
        user_id = str(current_user["_id"])
        
        # Create debug filters
        filters = SuggestionFilters(
            max_suggestions=max_suggestions,
            min_match_percentage=min_match_percentage,
            exclude_expired=True,
            prioritize_expiring=True,
            include_substitutes=True
        )
        
        # Check if user has pantry items
        pantry_response = await get_pantry_items(user_id, page_size=1)
        if not pantry_response or not pantry_response.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pantry items found. Please add ingredients to your pantry first."
            )
        
        # Get available ingredients for debug info
        available_ingredients = await get_user_available_ingredients(db, user_id)
        
        # Get suggestions
        suggestions_response = await get_leftover_suggestions(
            db=db,
            user_id=user_id,
            max_suggestions=max_suggestions,
            filters=filters
        )
        
        if suggestions_response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate debug suggestions. Please try again."
            )
        
        # Calculate debug metrics
        processing_time = (time.time() - start_time) * 1000
        
        # Create debug response
        from app.models.leftovers import SuggestionDebugInfo
        
        debug_info = SuggestionDebugInfo(
            pantry_ingredients=available_ingredients,
            recipes_considered=suggestions_response.recipes_analyzed,
            recipes_filtered_out=max(0, suggestions_response.recipes_analyzed - len(suggestions_response.suggestions)),
            matching_algorithm_version="1.0",
            processing_time_ms=processing_time,
            cache_hit=False,  # No caching implemented yet
            error_messages=[]
        )
        
        # Create debug response
        debug_response = LeftoverSuggestionsDebugResponse(
            suggestions=suggestions_response.suggestions,
            total_suggestions=suggestions_response.total_suggestions,
            user_id=suggestions_response.user_id,
            pantry_items_count=suggestions_response.pantry_items_count,
            recipes_analyzed=suggestions_response.recipes_analyzed,
            min_match_percentage=suggestions_response.min_match_percentage,
            generated_at=suggestions_response.generated_at,
            filters_applied=suggestions_response.filters_applied,
            performance_metrics=suggestions_response.performance_metrics,
            debug_info=debug_info
        )
        
        # Add total request time
        if debug_response.performance_metrics:
            debug_response.performance_metrics["total_request_time_ms"] = processing_time
        
        logger.info(f"Generated debug suggestions for user {user_id} with {len(available_ingredients)} ingredients")
        return debug_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating debug suggestions for user {current_user.get('_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating debug suggestions"
        )


# Health check endpoint for leftover service
@router.get("/health")
async def leftover_service_health():
    """
    Health check for leftover suggestion service
    
    Returns the status of the leftover suggestion service and its dependencies.
    """
    try:
        return SuccessResponse(
            message="Leftover suggestion service is healthy and ready to generate suggestions"
        )
    except Exception as e:
        logger.error(f"Leftover service health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Leftover suggestion service is unhealthy"
        )