"""
Recipe management router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import Optional, List
import time
import logging
from urllib.parse import urlparse
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
from app.models.meal_analysis import (
    MealAnalysisResponse,
    MealPhotoUploadRequest,
    MealPhotoUploadResponse,
    DetectedFood,
    FoodDetectionType
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
from app.services.food_vision import food_vision_service
from app.services.ai_recipe_generator import ai_recipe_generator
from app.services.recipe_nutrition_service import recipe_nutrition_service
from app.utils.auth import get_current_active_user
from app.middleware.onboarding import require_onboarding_complete
from app.models.ai_recipes import (
    RecipeGenerationRequest,
    RecipeGenerationResponse,
    RecipeGenerationSource,
    BulkRecipeGenerationRequest,
    BulkRecipeGenerationResponse
)
from app.models.recipe_import import (
    RecipeUrlImportRequest,
    RecipeImportResponse,
    RecipeImportStatus,
    RecipeImportPreview,
    RecipeUrlValidationRequest,
    RecipeUrlValidationResponse
)
from app.services.recipe_scraper import recipe_scraper
from app.services.recipe_normalizer import recipe_normalizer

# Configure logging
logger = logging.getLogger(__name__)

# Recipe import functionality is now available

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
    current_user: dict = Depends(require_onboarding_complete)
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
    calculate_nutrition: bool = Query(default=True, description="Automatically calculate nutritional information"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Create new recipe with optional automatic nutrition calculation"""
    user_id = str(current_user["_id"])
    
    result = await create_recipe(user_id=user_id, recipe_data=recipe_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create recipe"
        )
    
    # Automatically calculate nutrition if requested
    if calculate_nutrition:
        try:
            # Convert RecipeResponse to Recipe model for analysis
            from app.models.recipes import Recipe, RecipeIngredient
            recipe_model = Recipe(
                id=result.id,
                user_id=result.user_id,
                title=result.title,
                description=result.description,
                ingredients=[RecipeIngredient(**ing.dict()) for ing in result.ingredients],
                instructions=result.instructions,
                prep_time=result.prep_time,
                cook_time=result.cook_time,
                servings=result.servings,
                difficulty=result.difficulty,
                tags=result.tags,
                meal_types=result.meal_types,
                dietary_restrictions=result.dietary_restrictions,
                nutrition_info=result.nutrition_info,
                photo_url=result.photo_url,
                source_url=result.source_url,
                created_at=result.created_at,
                updated_at=result.updated_at
            )
            
            # Perform nutrition analysis in background (don't block response)
            import asyncio
            asyncio.create_task(recipe_nutrition_service.analyze_recipe_nutrition(recipe_model))
            logger.info(f"Started background nutrition analysis for recipe: {result.id}")
            
        except Exception as e:
            logger.warning(f"Failed to start nutrition analysis for recipe {result.id}: {e}")
    
    return result


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
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
    current_user: dict = Depends(require_onboarding_complete)
):
    """Get recipes that contain specific ingredients"""
    user_id = str(current_user["_id"])
    
    results = await get_recipes_by_ingredients(
        user_id=user_id,
        ingredient_names=ingredients,
        limit=limit
    )
    
    return results


@router.post("/from-photo", response_model=MealAnalysisResponse)
async def analyze_meal_photo(
    file: UploadFile = File(...),
    generate_recipe: bool = Query(default=True, description="Whether to generate a recipe from detected foods"),
    current_user: dict = Depends(require_onboarding_complete)
):
    """Analyze meal photo and generate recipe using AI/ML"""
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Analyze the meal photo using Google Vision API
        analysis_result = await food_vision_service.analyze_meal_photo(file_content)
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze meal photo"
            )
        
        # Convert detected foods to response format
        detected_foods = []
        for food in analysis_result.get("detected_foods", []):
            detected_foods.append(DetectedFood(
                name=food["name"],
                confidence=food["confidence"],
                detection_type=FoodDetectionType(food["type"]),
                category=food["category"],
                bounding_box=food.get("bounding_box"),
                notes=f"Detected via {food['type']} detection"
            ))
        
        recipe_response = None
        if generate_recipe and analysis_result.get("recipe"):
            # Create the recipe in the database
            user_id = str(current_user["_id"])
            recipe_data = analysis_result["recipe"]
            
            created_recipe = await create_recipe(user_id=user_id, recipe_data=recipe_data)
            if created_recipe:
                recipe_response = created_recipe
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return MealAnalysisResponse(
            success=True,
            detected_foods=detected_foods,
            recipe=recipe_response,
            confidence_score=analysis_result.get("confidence_score", 0.0),
            processing_time_ms=processing_time,
            metadata={
                "analysis_timestamp": analysis_result.get("analysis_timestamp"),
                "service_status": food_vision_service.get_service_status(),
                "file_info": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size_bytes": len(file_content)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        # Return error response with fallback demo data if service fails
        return MealAnalysisResponse(
            success=False,
            detected_foods=[],
            recipe=None,
            confidence_score=0.0,
            processing_time_ms=processing_time,
            error_message=f"Analysis failed: {str(e)}",
            metadata={
                "service_status": food_vision_service.get_service_status(),
                "error_type": type(e).__name__
            }
        )


@router.post("/generate-from-ingredients", response_model=RecipeGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_recipe_from_ingredients(
    request_data: RecipeGenerationRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Generate a new recipe from available ingredients using AI
    
    This endpoint uses AI to create original recipes based on the ingredients you have available.
    It's perfect for when existing recipe suggestions don't match well enough with your pantry items.
    
    **Features:**
    - AI-powered recipe generation using OpenAI GPT
    - Considers dietary restrictions and preferences
    - Validates recipe safety and practicality
    - Automatically saves generated recipes to your collection
    - Provides confidence scoring and quality metrics
    
    **Use Cases:**
    - Generate recipes when leftover suggestions aren't sufficient
    - Create new dishes from unusual ingredient combinations
    - Get recipe ideas for specific dietary needs
    - Explore creative cooking possibilities
    
    **Example Request:**
    ```json
    {
        "ingredients": ["chicken breast", "broccoli", "rice", "soy sauce"],
        "cuisine_preference": "Asian",
        "meal_type": "dinner",
        "dietary_restrictions": ["gluten_free"],
        "difficulty_preference": "easy",
        "servings": 4,
        "max_prep_time": 30,
        "max_cook_time": 45
    }
    ```
    """
    start_time = time.time()
    user_id = str(current_user["_id"])
    
    try:
        # Generate recipe using AI service
        generated_recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=request_data.ingredients,
            cuisine_preference=request_data.cuisine_preference,
            meal_type=request_data.meal_type,
            dietary_restrictions=request_data.dietary_restrictions,
            difficulty_preference=request_data.difficulty_preference,
            servings=request_data.servings,
            max_prep_time=request_data.max_prep_time,
            max_cook_time=request_data.max_cook_time
        )
        
        if not generated_recipe:
            processing_time = (time.time() - start_time) * 1000
            return RecipeGenerationResponse(
                success=False,
                recipe=None,
                generation_source=RecipeGenerationSource.INGREDIENTS,
                confidence_score=0.0,
                ingredient_match_percentage=0.0,
                processing_time_ms=processing_time,
                ai_model_used=ai_recipe_generator.model,
                error_message="Failed to generate recipe from ingredients",
                fallback_used=ai_recipe_generator.demo_mode,
                metadata={
                    "service_status": ai_recipe_generator.get_service_status(),
                    "request_ingredients": request_data.ingredients
                }
            )
        
        # Save the generated recipe to the database
        saved_recipe = await create_recipe(user_id=user_id, recipe_data=generated_recipe)
        
        if not saved_recipe:
            processing_time = (time.time() - start_time) * 1000
            return RecipeGenerationResponse(
                success=False,
                recipe=None,
                generation_source=RecipeGenerationSource.INGREDIENTS,
                confidence_score=0.0,
                ingredient_match_percentage=0.0,
                processing_time_ms=processing_time,
                ai_model_used=ai_recipe_generator.model,
                error_message="Generated recipe could not be saved to database",
                fallback_used=ai_recipe_generator.demo_mode
            )
        
        # Start background nutrition analysis for AI-generated recipe
        try:
            from app.models.recipes import Recipe, RecipeIngredient
            recipe_model = Recipe(
                id=saved_recipe.id,
                user_id=saved_recipe.user_id,
                title=saved_recipe.title,
                description=saved_recipe.description,
                ingredients=[RecipeIngredient(**ing.dict()) for ing in saved_recipe.ingredients],
                instructions=saved_recipe.instructions,
                prep_time=saved_recipe.prep_time,
                cook_time=saved_recipe.cook_time,
                servings=saved_recipe.servings,
                difficulty=saved_recipe.difficulty,
                tags=saved_recipe.tags,
                meal_types=saved_recipe.meal_types,
                dietary_restrictions=saved_recipe.dietary_restrictions,
                nutrition_info=saved_recipe.nutrition_info,
                photo_url=saved_recipe.photo_url,
                source_url=saved_recipe.source_url,
                created_at=saved_recipe.created_at,
                updated_at=saved_recipe.updated_at
            )
            
            import asyncio
            asyncio.create_task(recipe_nutrition_service.analyze_recipe_nutrition(recipe_model))
            logger.info(f"Started background nutrition analysis for AI-generated recipe: {saved_recipe.id}")
            
        except Exception as e:
            logger.warning(f"Failed to start nutrition analysis for AI-generated recipe {saved_recipe.id}: {e}")
        
        # Calculate ingredient match percentage
        recipe_ingredient_names = [ing.name.lower() for ing in generated_recipe.ingredients]
        request_ingredient_names = [ing.lower() for ing in request_data.ingredients]
        
        matches = sum(1 for req_ing in request_ingredient_names
                     if any(req_ing in recipe_ing for recipe_ing in recipe_ingredient_names))
        ingredient_match_percentage = (matches / len(request_data.ingredients)) * 100 if request_data.ingredients else 0
        
        # Calculate confidence score based on various factors
        confidence_score = 0.8  # Base confidence for AI generation
        
        # Adjust based on ingredient match
        if ingredient_match_percentage >= 80:
            confidence_score += 0.15
        elif ingredient_match_percentage >= 60:
            confidence_score += 0.1
        elif ingredient_match_percentage >= 40:
            confidence_score += 0.05
        
        # Adjust based on demo mode usage
        if ai_recipe_generator.demo_mode:
            confidence_score *= 0.7
        
        # Cap at 1.0
        confidence_score = min(confidence_score, 1.0)
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecipeGenerationResponse(
            success=True,
            recipe=saved_recipe,
            generation_source=RecipeGenerationSource.INGREDIENTS,
            confidence_score=confidence_score,
            ingredient_match_percentage=ingredient_match_percentage,
            processing_time_ms=processing_time,
            ai_model_used=ai_recipe_generator.model,
            recipe_quality_score=confidence_score,
            safety_validated=True,
            nutritional_balance_score=0.8 if generated_recipe.nutrition_info else None,
            fallback_used=ai_recipe_generator.demo_mode,
            metadata={
                "service_status": ai_recipe_generator.get_service_status(),
                "request_ingredients": request_data.ingredients,
                "generated_ingredients_count": len(generated_recipe.ingredients),
                "cuisine_preference": request_data.cuisine_preference,
                "meal_type": request_data.meal_type.value if request_data.meal_type else None,
                "difficulty": generated_recipe.difficulty.value
            }
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error generating recipe from ingredients for user {user_id}: {e}")
        
        return RecipeGenerationResponse(
            success=False,
            recipe=None,
            generation_source=RecipeGenerationSource.INGREDIENTS,
            confidence_score=0.0,
            ingredient_match_percentage=0.0,
            processing_time_ms=processing_time,
            ai_model_used=ai_recipe_generator.model,
            error_message=f"An unexpected error occurred: {str(e)}",
            fallback_used=ai_recipe_generator.demo_mode,
            metadata={
                "service_status": ai_recipe_generator.get_service_status(),
                "error_type": type(e).__name__
            }
        )


@router.post("/generate-bulk-from-ingredients", response_model=BulkRecipeGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_bulk_recipes_from_ingredients(
    request_data: BulkRecipeGenerationRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Generate multiple recipes from the same set of ingredients
    
    This endpoint creates several different recipe variations using the same base ingredients,
    perfect for meal planning or exploring different cooking options with what you have.
    
    **Features:**
    - Generate 2-5 different recipes from the same ingredients
    - Control variety level (diverse, similar, or themed)
    - Apply consistent preferences across all recipes
    - Batch processing for efficiency
    
    **Variety Options:**
    - **diverse**: Generate completely different types of dishes
    - **similar**: Generate variations of similar dishes
    - **themed**: Generate recipes around a specific theme or cuisine
    """
    start_time = time.time()
    user_id = str(current_user["_id"])
    
    try:
        generated_responses = []
        successful_count = 0
        
        # Base preferences from request
        base_prefs = request_data.base_preferences or RecipeGenerationRequest(
            ingredients=request_data.ingredients
        )
        
        for i in range(request_data.recipe_count):
            try:
                # Modify preferences for variety
                modified_prefs = base_prefs.copy()
                
                if request_data.variety_preference == "diverse":
                    # Vary meal types and cuisines for diversity
                    meal_types = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER, MealType.SNACK]
                    cuisines = ["Italian", "Asian", "Mexican", "Mediterranean", "American"]
                    
                    if i < len(meal_types):
                        modified_prefs.meal_type = meal_types[i]
                    if i < len(cuisines):
                        modified_prefs.cuisine_preference = cuisines[i]
                        
                elif request_data.variety_preference == "themed" and base_prefs.cuisine_preference:
                    # Keep same cuisine but vary meal types
                    meal_types = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]
                    if i < len(meal_types):
                        modified_prefs.meal_type = meal_types[i]
                
                # Generate individual recipe
                recipe_response = await generate_recipe_from_ingredients(modified_prefs, current_user)
                generated_responses.append(recipe_response)
                
                if recipe_response.success:
                    successful_count += 1
                    
            except Exception as e:
                logger.error(f"Error generating recipe {i+1} in bulk request: {e}")
                # Add failed response
                generated_responses.append(RecipeGenerationResponse(
                    success=False,
                    recipe=None,
                    generation_source=RecipeGenerationSource.INGREDIENTS,
                    confidence_score=0.0,
                    ingredient_match_percentage=0.0,
                    processing_time_ms=0.0,
                    error_message=f"Failed to generate recipe {i+1}: {str(e)}"
                ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return BulkRecipeGenerationResponse(
            success=successful_count > 0,
            recipes=generated_responses,
            total_requested=request_data.recipe_count,
            total_generated=successful_count,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error in bulk recipe generation for user {user_id}: {e}")
        
        return BulkRecipeGenerationResponse(
            success=False,
            recipes=[],
            total_requested=request_data.recipe_count,
            total_generated=0,
            processing_time_ms=processing_time
        )


@router.get("/ai-service-status")
async def get_ai_service_status(
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Get the current status of the AI recipe generation service
    
    This endpoint provides information about the AI service availability,
    configuration, and performance metrics.
    """
    try:
        service_status = ai_recipe_generator.get_service_status()
        
        return {
            "service_name": "AI Recipe Generator",
            "status": service_status,
            "capabilities": {
                "recipe_generation": True,
                "ingredient_based_generation": True,
                "bulk_generation": True,
                "cuisine_preferences": True,
                "dietary_restrictions": True,
                "nutritional_analysis": service_status.get("openai_available", False),
                "recipe_validation": True
            },
            "supported_features": [
                "Generate recipes from ingredient lists",
                "Apply cuisine and dietary preferences",
                "Bulk recipe generation",
                "Recipe quality validation",
                "Nutritional information estimation",
                "Cooking time estimation",
                "Difficulty assessment"
            ],
            "limitations": {
                "max_ingredients": 20,
                "max_bulk_recipes": 5,
                "demo_mode_active": service_status.get("demo_mode", True),
                "requires_openai_key": not service_status.get("api_key_configured", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting AI service status: {e}")
        return {
            "service_name": "AI Recipe Generator",
            "status": {"enabled": False, "error": str(e)},
            "capabilities": {},
            "supported_features": [],
            "limitations": {"service_unavailable": True}
        }


@router.post("/from-link", response_model=RecipeImportResponse, status_code=status.HTTP_201_CREATED)
async def import_recipe_from_url(
    request_data: RecipeUrlImportRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Import recipe from URL using web scraping
    
    This endpoint extracts recipe data from popular recipe websites and imports it
    into the user's recipe collection. It supports structured data extraction
    (JSON-LD, microdata, RDFa) with fallback HTML parsing.
    
    **Supported Sites:**
    - AllRecipes.com
    - Food.com
    - Food Network
    - Bon Appétit
    - Serious Eats
    - Epicurious
    - And many more...
    
    **Features:**
    - Automatic recipe data extraction
    - Ingredient parsing and normalization
    - Duplicate detection
    - Recipe validation and quality scoring
    - Custom tag addition
    
    **Example Request:**
    ```json
    {
        "url": "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/",
        "override_duplicate": false,
        "custom_tags": ["family-favorite", "comfort-food"]
    }
    ```
    """
    start_time = time.time()
    user_id = str(current_user["_id"])
    
    try:
        # Validate URL format and domain
        url = request_data.url
        domain = urlparse(url).netloc.lower().replace('www.', '')
        
        # Check if domain is supported
        is_supported = recipe_scraper.is_supported_url(url)
        if not is_supported:
            logger.warning(f"Unsupported domain for URL: {url}")
        
        # Check for duplicates first (unless override is specified)
        if not request_data.override_duplicate:
            existing_recipe = await _check_recipe_duplicate_by_url(user_id, url)
            if existing_recipe:
                processing_time = (time.time() - start_time) * 1000
                return RecipeImportResponse(
                    success=False,
                    status=RecipeImportStatus.DUPLICATE,
                    recipe=None,
                    preview=None,
                    source_url=url,
                    processing_time_ms=processing_time,
                    data_quality_score=0.0,
                    completeness_score=0.0,
                    error_message="Recipe already exists in your collection",
                    is_duplicate=True,
                    existing_recipe_id=existing_recipe.id,
                    metadata={
                        "domain": domain,
                        "duplicate_check_performed": True
                    }
                )
        
        # Scrape recipe data from URL
        logger.info(f"Starting recipe scraping for URL: {url}")
        scraped_data = await recipe_scraper.scrape_recipe(url)
        
        if not scraped_data:
            processing_time = (time.time() - start_time) * 1000
            return RecipeImportResponse(
                success=False,
                status=RecipeImportStatus.FAILED,
                recipe=None,
                preview=None,
                source_url=url,
                processing_time_ms=processing_time,
                data_quality_score=0.0,
                completeness_score=0.0,
                error_message="Failed to extract recipe data from URL. The page may not contain a recipe or the site may not be supported.",
                metadata={
                    "domain": domain,
                    "scraping_attempted": True,
                    "is_supported_domain": is_supported
                }
            )
        
        # Normalize scraped data to our schema
        logger.info(f"Normalizing scraped recipe data")
        normalized_recipe = await recipe_normalizer.normalize_recipe(scraped_data)
        
        if not normalized_recipe:
            processing_time = (time.time() - start_time) * 1000
            return RecipeImportResponse(
                success=False,
                status=RecipeImportStatus.VALIDATION_ERROR,
                recipe=None,
                preview=None,
                source_url=url,
                processing_time_ms=processing_time,
                data_quality_score=0.0,
                completeness_score=0.0,
                error_message="Failed to normalize recipe data. The extracted data may be incomplete or invalid.",
                metadata={
                    "domain": domain,
                    "scraping_method": scraped_data.get('scraping_method', 'unknown'),
                    "normalization_failed": True
                }
            )
        
        # Add custom tags if provided
        if request_data.custom_tags:
            existing_tags = set(normalized_recipe.tags)
            existing_tags.update(request_data.custom_tags)
            normalized_recipe.tags = list(existing_tags)
        
        # Create preview data
        preview = RecipeImportPreview(
            title=normalized_recipe.title,
            description=normalized_recipe.description,
            ingredients_count=len(normalized_recipe.ingredients),
            instructions_count=len(normalized_recipe.instructions),
            prep_time=normalized_recipe.prep_time,
            cook_time=normalized_recipe.cook_time,
            servings=normalized_recipe.servings,
            difficulty=normalized_recipe.difficulty.value,
            meal_types=[mt.value for mt in normalized_recipe.meal_types],
            dietary_restrictions=[dr.value for dr in normalized_recipe.dietary_restrictions],
            tags=normalized_recipe.tags,
            photo_url=normalized_recipe.photo_url,
            source_domain=domain,
            scraping_method=scraped_data.get('scraping_method', 'unknown'),
            confidence_score=_calculate_confidence_score(scraped_data, normalized_recipe)
        )
        
        # Save recipe to database
        logger.info(f"Saving imported recipe to database")
        saved_recipe = await create_recipe(user_id=user_id, recipe_data=normalized_recipe)
        
        if not saved_recipe:
            processing_time = (time.time() - start_time) * 1000
            return RecipeImportResponse(
                success=False,
                status=RecipeImportStatus.FAILED,
                recipe=None,
                preview=preview,
                source_url=url,
                processing_time_ms=processing_time,
                data_quality_score=preview.confidence_score,
                completeness_score=_calculate_completeness_score(normalized_recipe),
                error_message="Failed to save recipe to database",
                metadata={
                    "domain": domain,
                    "scraping_method": scraped_data.get('scraping_method', 'unknown'),
                    "database_save_failed": True
                }
            )
        
        # Start background nutrition analysis for imported recipe
        try:
            from app.models.recipes import Recipe, RecipeIngredient
            recipe_model = Recipe(
                id=saved_recipe.id,
                user_id=saved_recipe.user_id,
                title=saved_recipe.title,
                description=saved_recipe.description,
                ingredients=[RecipeIngredient(**ing.dict()) for ing in saved_recipe.ingredients],
                instructions=saved_recipe.instructions,
                prep_time=saved_recipe.prep_time,
                cook_time=saved_recipe.cook_time,
                servings=saved_recipe.servings,
                difficulty=saved_recipe.difficulty,
                tags=saved_recipe.tags,
                meal_types=saved_recipe.meal_types,
                dietary_restrictions=saved_recipe.dietary_restrictions,
                nutrition_info=saved_recipe.nutrition_info,
                photo_url=saved_recipe.photo_url,
                source_url=saved_recipe.source_url,
                created_at=saved_recipe.created_at,
                updated_at=saved_recipe.updated_at
            )
            
            import asyncio
            asyncio.create_task(recipe_nutrition_service.analyze_recipe_nutrition(recipe_model))
            logger.info(f"Started background nutrition analysis for imported recipe: {saved_recipe.id}")
            
        except Exception as e:
            logger.warning(f"Failed to start nutrition analysis for imported recipe {saved_recipe.id}: {e}")
        
        # Calculate quality metrics
        data_quality_score = preview.confidence_score
        completeness_score = _calculate_completeness_score(normalized_recipe)
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Successfully imported recipe '{normalized_recipe.title}' from {url}")
        
        return RecipeImportResponse(
            success=True,
            status=RecipeImportStatus.SUCCESS,
            recipe=saved_recipe,
            preview=preview,
            source_url=url,
            processing_time_ms=processing_time,
            data_quality_score=data_quality_score,
            completeness_score=completeness_score,
            metadata={
                "domain": domain,
                "scraping_method": scraped_data.get('scraping_method', 'unknown'),
                "is_supported_domain": is_supported,
                "custom_tags_added": len(request_data.custom_tags) if request_data.custom_tags else 0,
                "scraped_at": scraped_data.get('scraped_at'),
                "ingredients_parsed": len(normalized_recipe.ingredients),
                "instructions_parsed": len(normalized_recipe.instructions)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error importing recipe from {request_data.url}: {e}")
        
        return RecipeImportResponse(
            success=False,
            status=RecipeImportStatus.FAILED,
            recipe=None,
            preview=None,
            source_url=request_data.url,
            processing_time_ms=processing_time,
            data_quality_score=0.0,
            completeness_score=0.0,
            error_message=f"An unexpected error occurred: {str(e)}",
            metadata={
                "error_type": type(e).__name__,
                "domain": urlparse(request_data.url).netloc.lower().replace('www.', '') if request_data.url else 'unknown'
            }
        )


@router.post("/validate-url", response_model=RecipeUrlValidationResponse)
async def validate_recipe_url(
    request_data: RecipeUrlValidationRequest,
    current_user: dict = Depends(require_onboarding_complete)
):
    """
    Validate recipe URL before import
    
    This endpoint checks if a URL is valid for recipe import without actually
    importing the recipe. It verifies domain support, accessibility, and
    provides an estimate of extraction confidence.
    
    **Use Cases:**
    - Pre-validate URLs before import
    - Check domain support
    - Estimate import success probability
    - Provide user feedback on URL quality
    """
    start_time = time.time()
    
    try:
        url = request_data.url
        domain = urlparse(url).netloc.lower().replace('www.', '')
        
        # Check if domain is supported
        is_supported = recipe_scraper.is_supported_url(url)
        
        # Basic URL accessibility check
        is_accessible = False
        page_title = None
        has_recipe_data = None
        estimated_confidence = None
        validation_issues = []
        warnings = []
        
        try:
            # Try to fetch the page (with timeout)
            response = await recipe_scraper._fetch_webpage(url)
            if response:
                is_accessible = True
                
                # Try to extract basic page info
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get page title
                title_elem = soup.find('title')
                if title_elem:
                    page_title = title_elem.get_text(strip=True)
                
                # Check for recipe indicators
                recipe_indicators = [
                    'recipe', 'ingredient', 'instruction', 'cooking', 'preparation',
                    'prep time', 'cook time', 'servings', 'yield'
                ]
                
                page_text = soup.get_text().lower()
                recipe_score = sum(1 for indicator in recipe_indicators if indicator in page_text)
                has_recipe_data = recipe_score >= 3
                
                # Estimate confidence based on various factors
                confidence_factors = []
                
                # Domain support factor
                if is_supported:
                    confidence_factors.append(0.4)
                else:
                    confidence_factors.append(0.2)
                    warnings.append("Domain is not in the list of fully supported sites")
                
                # Recipe data presence factor
                if has_recipe_data:
                    confidence_factors.append(0.3)
                else:
                    confidence_factors.append(0.1)
                    validation_issues.append("Page may not contain recipe data")
                
                # Structured data factor
                if 'application/ld+json' in response.text or 'itemtype' in response.text:
                    confidence_factors.append(0.3)
                else:
                    confidence_factors.append(0.1)
                    warnings.append("No structured data detected - may rely on HTML parsing")
                
                estimated_confidence = sum(confidence_factors)
                
        except Exception as e:
            logger.warning(f"Error checking URL accessibility: {e}")
            validation_issues.append(f"Unable to access URL: {str(e)}")
        
        # Additional validation checks
        if not is_supported and not validation_issues:
            warnings.append("Domain is not officially supported but import may still work")
        
        if not is_accessible:
            validation_issues.append("URL is not accessible or returned an error")
        
        is_valid = is_accessible and (is_supported or has_recipe_data)
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecipeUrlValidationResponse(
            is_valid=is_valid,
            is_supported=is_supported,
            domain=domain,
            is_accessible=is_accessible,
            validation_issues=validation_issues,
            warnings=warnings,
            page_title=page_title,
            has_recipe_data=has_recipe_data,
            estimated_confidence=estimated_confidence,
            response_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error validating URL {request_data.url}: {e}")
        
        return RecipeUrlValidationResponse(
            is_valid=False,
            is_supported=False,
            domain=urlparse(request_data.url).netloc.lower().replace('www.', '') if request_data.url else 'unknown',
            is_accessible=False,
            validation_issues=[f"Validation failed: {str(e)}"],
            warnings=[],
            response_time_ms=processing_time
        )


async def _check_recipe_duplicate_by_url(user_id: str, url: str) -> Optional[RecipeResponse]:
    """Check if recipe with same source URL already exists"""
    try:
        from app.database import get_collection
        recipes_collection = await get_collection("recipes")
        
        existing_recipe = await recipes_collection.find_one({
            "user_id": user_id,
            "source_url": url
        })
        
        if existing_recipe:
            from app.crud.recipes import _convert_recipe_response
            return _convert_recipe_response(existing_recipe)
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking recipe duplicate: {e}")
        return None


def _calculate_confidence_score(scraped_data: dict, normalized_recipe) -> float:
    """Calculate confidence score for scraped recipe data"""
    try:
        score = 0.0
        
        # Base score based on scraping method
        scraping_method = scraped_data.get('scraping_method', 'unknown')
        if scraping_method == 'json-ld':
            score += 0.4
        elif scraping_method == 'microdata':
            score += 0.3
        elif scraping_method == 'rdfa':
            score += 0.25
        else:
            score += 0.1
        
        # Data completeness factors
        if normalized_recipe.title:
            score += 0.1
        if normalized_recipe.ingredients:
            score += 0.2
        if normalized_recipe.instructions:
            score += 0.2
        if normalized_recipe.prep_time or normalized_recipe.cook_time:
            score += 0.1
        if normalized_recipe.nutrition_info:
            score += 0.1
        if normalized_recipe.photo_url:
            score += 0.05
        
        # Quality factors
        if len(normalized_recipe.ingredients) >= 3:
            score += 0.05
        if len(normalized_recipe.instructions) >= 3:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
        
    except Exception as e:
        logger.error(f"Error calculating confidence score: {e}")
        return 0.5  # Default moderate confidence


def _calculate_completeness_score(recipe) -> float:
    """Calculate data completeness score"""
    try:
        total_fields = 10
        completed_fields = 0
        
        # Required fields
        if recipe.title:
            completed_fields += 1
        if recipe.ingredients:
            completed_fields += 1
        if recipe.instructions:
            completed_fields += 1
        if recipe.servings:
            completed_fields += 1
        
        # Optional but important fields
        if recipe.description:
            completed_fields += 1
        if recipe.prep_time:
            completed_fields += 1
        if recipe.cook_time:
            completed_fields += 1
        if recipe.meal_types:
            completed_fields += 1
        if recipe.nutrition_info:
            completed_fields += 1
        if recipe.photo_url:
            completed_fields += 1
        
        return completed_fields / total_fields
        
    except Exception as e:
        logger.error(f"Error calculating completeness score: {e}")
        return 0.5  # Default moderate completeness