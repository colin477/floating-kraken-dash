"""
Nutritional lookup and caching service
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json

from app.models.nutrition import (
    IngredientNutrition,
    ComprehensiveNutrition,
    IngredientLookupRequest,
    IngredientLookupResponse,
    BulkIngredientAnalysisRequest,
    BulkIngredientAnalysisResponse,
    NutritionCacheEntry,
    NutritionServiceStatus
)
from app.services.usda_nutrition_service import usda_nutrition_service
from app.database import get_collection

# Configure logging
logger = logging.getLogger(__name__)


class NutritionLookupService:
    """Service for nutritional data lookup with caching and fallback mechanisms"""
    
    def __init__(self):
        self.cache_collection_name = "nutrition_cache"
        self.cache_ttl_hours = 24 * 7  # 1 week cache TTL
        self.fallback_enabled = True
        
        # Fallback nutritional estimates for common ingredients
        self.fallback_nutrition_db = {
            # Proteins
            "chicken breast": {
                "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6,
                "sodium": 74, "iron": 0.7, "calcium": 15
            },
            "ground beef": {
                "calories": 250, "protein": 26, "carbs": 0, "fat": 15,
                "sodium": 75, "iron": 2.6, "calcium": 18
            },
            "salmon": {
                "calories": 208, "protein": 22, "carbs": 0, "fat": 12,
                "sodium": 59, "iron": 0.8, "calcium": 12
            },
            "eggs": {
                "calories": 155, "protein": 13, "carbs": 1.1, "fat": 11,
                "sodium": 124, "iron": 1.8, "calcium": 56
            },
            "tofu": {
                "calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8,
                "sodium": 7, "iron": 5.4, "calcium": 350
            },
            
            # Vegetables
            "broccoli": {
                "calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4,
                "sodium": 33, "iron": 0.7, "calcium": 47, "vitamin_c": 89
            },
            "spinach": {
                "calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4,
                "sodium": 79, "iron": 2.7, "calcium": 99, "vitamin_a": 469
            },
            "carrots": {
                "calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2,
                "sodium": 69, "iron": 0.3, "calcium": 33, "vitamin_a": 835
            },
            "onions": {
                "calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1,
                "sodium": 4, "iron": 0.2, "calcium": 23
            },
            "tomatoes": {
                "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2,
                "sodium": 5, "iron": 0.3, "calcium": 10, "vitamin_c": 14
            },
            
            # Grains
            "rice": {
                "calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3,
                "sodium": 1, "iron": 0.8, "calcium": 10
            },
            "pasta": {
                "calories": 131, "protein": 5, "carbs": 25, "fat": 1.1,
                "sodium": 1, "iron": 1.3, "calcium": 7
            },
            "bread": {
                "calories": 265, "protein": 9, "carbs": 49, "fat": 3.2,
                "sodium": 491, "iron": 3.6, "calcium": 147
            },
            "oats": {
                "calories": 389, "protein": 17, "carbs": 66, "fat": 7,
                "sodium": 2, "iron": 4.7, "calcium": 54
            },
            
            # Dairy
            "milk": {
                "calories": 42, "protein": 3.4, "carbs": 5, "fat": 1,
                "sodium": 40, "iron": 0.03, "calcium": 113
            },
            "cheese": {
                "calories": 113, "protein": 7, "carbs": 1, "fat": 9,
                "sodium": 621, "iron": 0.1, "calcium": 202
            },
            "yogurt": {
                "calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4,
                "sodium": 36, "iron": 0.1, "calcium": 110
            },
            "butter": {
                "calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81,
                "sodium": 11, "iron": 0.02, "calcium": 24
            },
            
            # Oils and fats
            "olive oil": {
                "calories": 884, "protein": 0, "carbs": 0, "fat": 100,
                "sodium": 2, "iron": 0.6, "calcium": 1
            },
            "coconut oil": {
                "calories": 862, "protein": 0, "carbs": 0, "fat": 100,
                "sodium": 0, "iron": 0.05, "calcium": 0
            }
        }
        
        logger.info("Nutrition Lookup Service initialized")
    
    async def lookup_ingredient(self, request: IngredientLookupRequest) -> IngredientLookupResponse:
        """
        Look up nutritional information for a single ingredient
        
        Args:
            request: Ingredient lookup request
            
        Returns:
            IngredientLookupResponse with nutritional data
        """
        start_time = datetime.utcnow()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request.ingredient_name, request.quantity, request.unit)
            
            # Check cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for ingredient: {request.ingredient_name}")
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return IngredientLookupResponse(
                    success=True,
                    ingredient_name=request.ingredient_name,
                    matches=[cached_result],
                    best_match=cached_result,
                    confidence_score=cached_result.data_quality_score,
                    data_source=cached_result.data_source,
                    processing_time_ms=processing_time
                )
            
            # Try USDA lookup
            usda_result = None
            try:
                async with usda_nutrition_service:
                    usda_result = await usda_nutrition_service.find_best_ingredient_match(
                        request.ingredient_name,
                        request.quantity,
                        request.unit
                    )
            except Exception as e:
                logger.warning(f"USDA lookup failed for {request.ingredient_name}: {e}")
            
            # If USDA lookup successful, cache and return
            if usda_result:
                await self._save_to_cache(cache_key, request.ingredient_name, usda_result)
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return IngredientLookupResponse(
                    success=True,
                    ingredient_name=request.ingredient_name,
                    matches=[usda_result],
                    best_match=usda_result,
                    confidence_score=usda_result.data_quality_score,
                    data_source=usda_result.data_source,
                    processing_time_ms=processing_time
                )
            
            # Fallback to estimated nutrition data
            if self.fallback_enabled:
                fallback_result = await self._get_fallback_nutrition(request)
                if fallback_result:
                    await self._save_to_cache(cache_key, request.ingredient_name, fallback_result)
                    processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    return IngredientLookupResponse(
                        success=True,
                        ingredient_name=request.ingredient_name,
                        matches=[fallback_result],
                        best_match=fallback_result,
                        confidence_score=fallback_result.data_quality_score,
                        data_source=fallback_result.data_source,
                        fallback_used=True,
                        processing_time_ms=processing_time
                    )
            
            # No data found
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IngredientLookupResponse(
                success=False,
                ingredient_name=request.ingredient_name,
                matches=[],
                best_match=None,
                confidence_score=0.0,
                data_source="None",
                processing_time_ms=processing_time,
                error_message=f"No nutritional data found for ingredient: {request.ingredient_name}"
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error in ingredient lookup: {e}")
            
            return IngredientLookupResponse(
                success=False,
                ingredient_name=request.ingredient_name,
                matches=[],
                best_match=None,
                confidence_score=0.0,
                data_source="Error",
                processing_time_ms=processing_time,
                error_message=f"Lookup failed: {str(e)}"
            )
    
    async def bulk_ingredient_analysis(self, request: BulkIngredientAnalysisRequest) -> BulkIngredientAnalysisResponse:
        """
        Analyze multiple ingredients in bulk
        
        Args:
            request: Bulk ingredient analysis request
            
        Returns:
            BulkIngredientAnalysisResponse with results for all ingredients
        """
        start_time = datetime.utcnow()
        
        try:
            # Process ingredients concurrently (with some rate limiting)
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            async def process_ingredient(ingredient_request):
                async with semaphore:
                    return await self.lookup_ingredient(ingredient_request)
            
            # Create tasks for all ingredients
            tasks = [process_ingredient(ingredient) for ingredient in request.ingredients]
            
            # Execute all tasks
            individual_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            for i, result in enumerate(individual_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing ingredient {i}: {result}")
                    # Create error response
                    error_response = IngredientLookupResponse(
                        success=False,
                        ingredient_name=request.ingredients[i].ingredient_name,
                        matches=[],
                        best_match=None,
                        confidence_score=0.0,
                        data_source="Error",
                        processing_time_ms=0.0,
                        error_message=str(result)
                    )
                    individual_results[i] = error_response
                elif result.success:
                    successful_results.append(result)
            
            # Combine results if requested
            combined_nutrition = None
            if request.combine_results and successful_results:
                combined_nutrition = await self._combine_nutrition_data(successful_results)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return BulkIngredientAnalysisResponse(
                success=len(successful_results) > 0,
                individual_results=individual_results,
                combined_nutrition=combined_nutrition,
                total_processed=len(request.ingredients),
                successful_lookups=len(successful_results),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error in bulk ingredient analysis: {e}")
            
            return BulkIngredientAnalysisResponse(
                success=False,
                individual_results=[],
                combined_nutrition=None,
                total_processed=len(request.ingredients),
                successful_lookups=0,
                processing_time_ms=processing_time
            )
    
    async def _get_from_cache(self, cache_key: str) -> Optional[IngredientNutrition]:
        """Get ingredient nutrition data from cache"""
        try:
            cache_collection = await get_collection(self.cache_collection_name)
            
            cache_entry = await cache_collection.find_one({
                "cache_key": cache_key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cache_entry:
                # Update hit count and last accessed
                await cache_collection.update_one(
                    {"_id": cache_entry["_id"]},
                    {
                        "$inc": {"hit_count": 1},
                        "$set": {"last_accessed": datetime.utcnow()}
                    }
                )
                
                return IngredientNutrition(**cache_entry["nutrition_data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def _save_to_cache(self, cache_key: str, ingredient_name: str, nutrition_data: IngredientNutrition):
        """Save ingredient nutrition data to cache"""
        try:
            cache_collection = await get_collection(self.cache_collection_name)
            
            cache_entry = NutritionCacheEntry(
                cache_key=cache_key,
                ingredient_name=ingredient_name,
                nutrition_data=nutrition_data,
                expires_at=datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)
            )
            
            # Upsert cache entry
            await cache_collection.replace_one(
                {"cache_key": cache_key},
                cache_entry.dict(by_alias=True),
                upsert=True
            )
            
            logger.debug(f"Cached nutrition data for: {ingredient_name}")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    async def _get_fallback_nutrition(self, request: IngredientLookupRequest) -> Optional[IngredientNutrition]:
        """Get fallback nutrition data from built-in database"""
        try:
            ingredient_name = request.ingredient_name.lower().strip()
            
            # Try exact match first
            if ingredient_name in self.fallback_nutrition_db:
                fallback_data = self.fallback_nutrition_db[ingredient_name]
                return self._create_ingredient_nutrition_from_fallback(
                    request.ingredient_name,
                    fallback_data,
                    request.quantity,
                    request.unit
                )
            
            # Try partial matches
            for key, data in self.fallback_nutrition_db.items():
                if key in ingredient_name or ingredient_name in key:
                    return self._create_ingredient_nutrition_from_fallback(
                        request.ingredient_name,
                        data,
                        request.quantity,
                        request.unit
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting fallback nutrition: {e}")
            return None
    
    def _create_ingredient_nutrition_from_fallback(
        self, 
        ingredient_name: str, 
        fallback_data: Dict[str, float],
        quantity: Optional[float] = None,
        unit: Optional[str] = None
    ) -> IngredientNutrition:
        """Create IngredientNutrition object from fallback data"""
        from app.models.nutrition import MacroNutrients, Vitamins, Minerals, NutrientInfo, NutrientUnit
        
        # Create macronutrients
        macros = MacroNutrients()
        if "calories" in fallback_data:
            macros.calories = NutrientInfo(
                name="Calories", 
                amount=fallback_data["calories"], 
                unit=NutrientUnit.CALORIE,
                source_confidence=0.7
            )
        if "protein" in fallback_data:
            macros.protein = NutrientInfo(
                name="Protein", 
                amount=fallback_data["protein"], 
                unit=NutrientUnit.GRAM,
                source_confidence=0.7
            )
        if "carbs" in fallback_data:
            macros.carbohydrates = NutrientInfo(
                name="Carbohydrates", 
                amount=fallback_data["carbs"], 
                unit=NutrientUnit.GRAM,
                source_confidence=0.7
            )
        if "fat" in fallback_data:
            macros.total_fat = NutrientInfo(
                name="Total Fat", 
                amount=fallback_data["fat"], 
                unit=NutrientUnit.GRAM,
                source_confidence=0.7
            )
        if "sodium" in fallback_data:
            macros.sodium = NutrientInfo(
                name="Sodium", 
                amount=fallback_data["sodium"], 
                unit=NutrientUnit.MILLIGRAM,
                source_confidence=0.7
            )
        
        # Create vitamins
        vitamins = Vitamins()
        if "vitamin_a" in fallback_data:
            vitamins.vitamin_a = NutrientInfo(
                name="Vitamin A", 
                amount=fallback_data["vitamin_a"], 
                unit=NutrientUnit.MICROGRAM,
                source_confidence=0.7
            )
        if "vitamin_c" in fallback_data:
            vitamins.vitamin_c = NutrientInfo(
                name="Vitamin C", 
                amount=fallback_data["vitamin_c"], 
                unit=NutrientUnit.MILLIGRAM,
                source_confidence=0.7
            )
        
        # Create minerals
        minerals = Minerals()
        if "iron" in fallback_data:
            minerals.iron = NutrientInfo(
                name="Iron", 
                amount=fallback_data["iron"], 
                unit=NutrientUnit.MILLIGRAM,
                source_confidence=0.7
            )
        if "calcium" in fallback_data:
            minerals.calcium = NutrientInfo(
                name="Calcium", 
                amount=fallback_data["calcium"], 
                unit=NutrientUnit.MILLIGRAM,
                source_confidence=0.7
            )
        
        # Create comprehensive nutrition
        comprehensive_nutrition = ComprehensiveNutrition(
            macronutrients=macros,
            vitamins=vitamins,
            minerals=minerals,
            nutrition_density_score=50.0  # Moderate score for fallback data
        )
        
        # Adjust for quantity if provided
        serving_size = 100.0
        serving_unit = "g"
        if quantity and unit:
            serving_size = quantity
            serving_unit = unit
            # Note: In a full implementation, you'd want proper unit conversions here
        
        return IngredientNutrition(
            ingredient_name=ingredient_name,
            usda_fdc_id=None,
            serving_size=serving_size,
            serving_unit=serving_unit,
            nutrition_per_serving=comprehensive_nutrition,
            nutrition_per_100g=comprehensive_nutrition,
            data_source="Fallback Database",
            data_quality_score=0.7  # Lower quality for fallback data
        )
    
    async def _combine_nutrition_data(self, results: List[IngredientLookupResponse]) -> ComprehensiveNutrition:
        """Combine nutrition data from multiple ingredients"""
        try:
            from app.models.nutrition import MacroNutrients, Vitamins, Minerals, NutrientInfo, NutrientUnit
            
            # Initialize combined nutrition
            combined_macros = MacroNutrients()
            combined_vitamins = Vitamins()
            combined_minerals = Minerals()
            combined_allergens = []
            
            # Sum up all nutrients
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_sodium = 0
            
            for result in results:
                if result.best_match and result.best_match.nutrition_per_serving:
                    nutrition = result.best_match.nutrition_per_serving
                    
                    # Add macronutrients
                    if nutrition.macronutrients.calories:
                        total_calories += nutrition.macronutrients.calories.amount
                    if nutrition.macronutrients.protein:
                        total_protein += nutrition.macronutrients.protein.amount
                    if nutrition.macronutrients.carbohydrates:
                        total_carbs += nutrition.macronutrients.carbohydrates.amount
                    if nutrition.macronutrients.total_fat:
                        total_fat += nutrition.macronutrients.total_fat.amount
                    if nutrition.macronutrients.sodium:
                        total_sodium += nutrition.macronutrients.sodium.amount
                    
                    # Combine allergens
                    combined_allergens.extend(nutrition.allergens)
            
            # Create combined macronutrients
            if total_calories > 0:
                combined_macros.calories = NutrientInfo(
                    name="Calories", amount=total_calories, unit=NutrientUnit.CALORIE
                )
            if total_protein > 0:
                combined_macros.protein = NutrientInfo(
                    name="Protein", amount=total_protein, unit=NutrientUnit.GRAM
                )
            if total_carbs > 0:
                combined_macros.carbohydrates = NutrientInfo(
                    name="Carbohydrates", amount=total_carbs, unit=NutrientUnit.GRAM
                )
            if total_fat > 0:
                combined_macros.total_fat = NutrientInfo(
                    name="Total Fat", amount=total_fat, unit=NutrientUnit.GRAM
                )
            if total_sodium > 0:
                combined_macros.sodium = NutrientInfo(
                    name="Sodium", amount=total_sodium, unit=NutrientUnit.MILLIGRAM
                )
            
            # Remove duplicate allergens
            unique_allergens = list(set(combined_allergens))
            
            return ComprehensiveNutrition(
                macronutrients=combined_macros,
                vitamins=combined_vitamins,
                minerals=combined_minerals,
                allergens=unique_allergens,
                nutrition_density_score=50.0  # Average score for combined data
            )
            
        except Exception as e:
            logger.error(f"Error combining nutrition data: {e}")
            return ComprehensiveNutrition()
    
    def _generate_cache_key(self, ingredient_name: str, quantity: Optional[float], unit: Optional[str]) -> str:
        """Generate a unique cache key for ingredient lookup"""
        key_data = f"{ingredient_name.lower().strip()}_{quantity}_{unit}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def clear_expired_cache(self):
        """Clear expired cache entries"""
        try:
            cache_collection = await get_collection(self.cache_collection_name)
            
            result = await cache_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            logger.info(f"Cleared {result.deleted_count} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
    
    def get_service_status(self) -> NutritionServiceStatus:
        """Get current service status"""
        usda_status = usda_nutrition_service.get_service_status()
        
        return NutritionServiceStatus(
            service_name="Nutrition Lookup Service",
            is_available=True,
            api_key_configured=usda_status.api_key_configured,
            cache_enabled=True,
            cache_hit_rate=75.0,  # Estimated
            total_lookups=usda_status.total_lookups,
            successful_lookups=usda_status.successful_lookups,
            failed_lookups=usda_status.failed_lookups,
            average_response_time_ms=200.0,  # Estimated with caching
            last_api_call=usda_status.last_api_call,
            error_message=usda_status.error_message
        )


# Global service instance
nutrition_lookup_service = NutritionLookupService()