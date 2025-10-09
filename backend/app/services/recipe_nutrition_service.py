"""
Recipe nutritional analysis service
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from app.models.nutrition import (
    RecipeNutritionAnalysis,
    ComprehensiveNutrition,
    MacroNutrients,
    Vitamins,
    Minerals,
    NutrientInfo,
    NutrientUnit,
    DietaryAnalysis,
    NutritionalWarning,
    AllergenType,
    IngredientLookupRequest
)
from app.models.recipes import Recipe, RecipeIngredient, DietaryRestriction
from app.services.nutrition_lookup_service import nutrition_lookup_service
from app.database import get_collection

# Configure logging
logger = logging.getLogger(__name__)


class RecipeNutritionService:
    """Service for analyzing nutritional content of complete recipes"""
    
    def __init__(self):
        self.analysis_cache_collection = "recipe_nutrition_analysis"
        self.cache_ttl_hours = 24  # Cache recipe analysis for 24 hours
        
        # Dietary restriction validation rules
        self.dietary_restriction_rules = {
            DietaryRestriction.VEGETARIAN: {
                "forbidden_ingredients": [
                    "beef", "pork", "chicken", "turkey", "fish", "salmon", "tuna", 
                    "shrimp", "crab", "lobster", "meat", "bacon", "ham", "sausage"
                ],
                "forbidden_allergens": []
            },
            DietaryRestriction.VEGAN: {
                "forbidden_ingredients": [
                    "beef", "pork", "chicken", "turkey", "fish", "salmon", "tuna",
                    "shrimp", "crab", "lobster", "meat", "bacon", "ham", "sausage",
                    "milk", "cheese", "butter", "cream", "yogurt", "eggs", "honey"
                ],
                "forbidden_allergens": [AllergenType.MILK, AllergenType.EGGS]
            },
            DietaryRestriction.GLUTEN_FREE: {
                "forbidden_ingredients": [
                    "wheat", "flour", "bread", "pasta", "barley", "rye", "oats"
                ],
                "forbidden_allergens": [AllergenType.WHEAT]
            },
            DietaryRestriction.DAIRY_FREE: {
                "forbidden_ingredients": [
                    "milk", "cheese", "butter", "cream", "yogurt", "whey", "casein"
                ],
                "forbidden_allergens": [AllergenType.MILK]
            },
            DietaryRestriction.NUT_FREE: {
                "forbidden_ingredients": [
                    "almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut",
                    "brazil nut", "peanut", "groundnut"
                ],
                "forbidden_allergens": [AllergenType.TREE_NUTS, AllergenType.PEANUTS]
            }
        }
        
        # Nutritional warning thresholds (per serving)
        self.warning_thresholds = {
            "high_sodium": 600,  # mg
            "high_saturated_fat": 13,  # g (20% DV)
            "high_sugar": 25,  # g
            "high_calories": 600,  # kcal
            "low_protein": 5,  # g
            "low_fiber": 2  # g
        }
        
        logger.info("Recipe Nutrition Service initialized")
    
    async def analyze_recipe_nutrition(
        self, 
        recipe: Recipe, 
        force_refresh: bool = False,
        include_detailed_breakdown: bool = True
    ) -> Optional[RecipeNutritionAnalysis]:
        """
        Analyze nutritional content of a complete recipe
        
        Args:
            recipe: Recipe object to analyze
            force_refresh: Force refresh of cached analysis
            include_detailed_breakdown: Include detailed ingredient breakdown
            
        Returns:
            RecipeNutritionAnalysis with comprehensive nutritional data
        """
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_analysis = await self._get_cached_analysis(recipe.id)
                if cached_analysis:
                    logger.debug(f"Using cached nutrition analysis for recipe: {recipe.id}")
                    return cached_analysis
            
            logger.info(f"Starting nutrition analysis for recipe: {recipe.title}")
            
            # Analyze each ingredient
            ingredient_analyses = []
            missing_ingredients = []
            estimated_ingredients = []
            total_nutrition = ComprehensiveNutrition()
            
            for ingredient in recipe.ingredients:
                ingredient_analysis = await self._analyze_ingredient(ingredient)
                
                if ingredient_analysis["success"]:
                    ingredient_analyses.append(ingredient_analysis)
                    
                    # Add to total nutrition
                    total_nutrition = self._add_nutrition(
                        total_nutrition, 
                        ingredient_analysis["nutrition"]
                    )
                    
                    if ingredient_analysis["estimated"]:
                        estimated_ingredients.append(ingredient.name)
                else:
                    missing_ingredients.append(ingredient.name)
                    logger.warning(f"No nutrition data found for ingredient: {ingredient.name}")
            
            # Calculate per-serving nutrition
            nutrition_per_serving = self._scale_nutrition(total_nutrition, 1.0 / recipe.servings)
            
            # Calculate analysis confidence
            confidence = self._calculate_analysis_confidence(
                len(ingredient_analyses),
                len(recipe.ingredients),
                len(estimated_ingredients)
            )
            
            # Create detailed breakdown if requested
            ingredient_contributions = []
            if include_detailed_breakdown:
                ingredient_contributions = self._create_ingredient_breakdown(
                    ingredient_analyses, 
                    total_nutrition
                )
            
            # Determine data sources
            data_sources = list(set([
                analysis["data_source"] for analysis in ingredient_analyses 
                if analysis["success"]
            ]))
            
            # Create analysis object
            analysis = RecipeNutritionAnalysis(
                recipe_id=recipe.id,
                total_nutrition=total_nutrition,
                nutrition_per_serving=nutrition_per_serving,
                ingredient_contributions=ingredient_contributions,
                analysis_confidence=confidence,
                missing_ingredients=missing_ingredients,
                estimated_ingredients=estimated_ingredients,
                data_sources=data_sources
            )
            
            # Cache the analysis
            await self._cache_analysis(recipe.id, analysis)
            
            logger.info(f"Completed nutrition analysis for recipe: {recipe.title} (confidence: {confidence:.2f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing recipe nutrition: {e}")
            return None
    
    async def analyze_dietary_compliance(
        self, 
        recipe: Recipe, 
        nutrition_analysis: RecipeNutritionAnalysis
    ) -> DietaryAnalysis:
        """
        Analyze recipe for dietary compliance and generate warnings
        
        Args:
            recipe: Recipe object
            nutrition_analysis: Nutritional analysis of the recipe
            
        Returns:
            DietaryAnalysis with compliance information and warnings
        """
        try:
            dietary_restrictions_met = []
            dietary_restrictions_violated = []
            allergens_present = []
            nutritional_warnings = []
            
            # Check each dietary restriction
            for restriction in DietaryRestriction:
                if restriction in self.dietary_restriction_rules:
                    compliance = await self._check_dietary_restriction_compliance(
                        recipe, nutrition_analysis, restriction
                    )
                    
                    if compliance["compliant"]:
                        dietary_restrictions_met.append(restriction.value)
                    else:
                        dietary_restrictions_violated.append(restriction.value)
            
            # Collect allergens from nutrition analysis
            for ingredient_contrib in nutrition_analysis.ingredient_contributions:
                if "allergens" in ingredient_contrib:
                    allergens_present.extend(ingredient_contrib["allergens"])
            
            # Remove duplicates
            allergens_present = list(set(allergens_present))
            
            # Generate nutritional warnings
            nutritional_warnings = await self._generate_nutritional_warnings(
                nutrition_analysis.nutrition_per_serving
            )
            
            # Calculate health score
            health_score = self._calculate_health_score(
                nutrition_analysis.nutrition_per_serving,
                len(nutritional_warnings),
                len(allergens_present)
            )
            
            return DietaryAnalysis(
                recipe_id=recipe.id,
                dietary_restrictions_met=dietary_restrictions_met,
                dietary_restrictions_violated=dietary_restrictions_violated,
                allergens_present=allergens_present,
                nutritional_warnings=nutritional_warnings,
                health_score=health_score,
                sustainability_score=None,  # Could be implemented later
                goal_alignment={}  # Would require user goals
            )
            
        except Exception as e:
            logger.error(f"Error analyzing dietary compliance: {e}")
            return DietaryAnalysis(
                recipe_id=recipe.id,
                dietary_restrictions_met=[],
                dietary_restrictions_violated=[],
                allergens_present=[],
                nutritional_warnings=[],
                health_score=50.0
            )
    
    async def _analyze_ingredient(self, ingredient: RecipeIngredient) -> Dict[str, Any]:
        """Analyze nutritional content of a single ingredient"""
        try:
            # Create lookup request
            lookup_request = IngredientLookupRequest(
                ingredient_name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit
            )
            
            # Get nutrition data
            lookup_response = await nutrition_lookup_service.lookup_ingredient(lookup_request)
            
            if lookup_response.success and lookup_response.best_match:
                return {
                    "success": True,
                    "ingredient_name": ingredient.name,
                    "nutrition": lookup_response.best_match.nutrition_per_serving,
                    "data_source": lookup_response.data_source,
                    "confidence": lookup_response.confidence_score,
                    "estimated": lookup_response.fallback_used,
                    "allergens": lookup_response.best_match.nutrition_per_serving.allergens
                }
            else:
                return {
                    "success": False,
                    "ingredient_name": ingredient.name,
                    "error": lookup_response.error_message
                }
                
        except Exception as e:
            logger.error(f"Error analyzing ingredient {ingredient.name}: {e}")
            return {
                "success": False,
                "ingredient_name": ingredient.name,
                "error": str(e)
            }
    
    def _add_nutrition(
        self, 
        base_nutrition: ComprehensiveNutrition, 
        add_nutrition: ComprehensiveNutrition
    ) -> ComprehensiveNutrition:
        """Add nutritional values from one nutrition object to another"""
        try:
            # Create a copy of base nutrition
            result = base_nutrition.copy() if base_nutrition else ComprehensiveNutrition()
            
            # Add macronutrients
            result.macronutrients = self._add_macronutrients(
                result.macronutrients, 
                add_nutrition.macronutrients
            )
            
            # Add vitamins
            result.vitamins = self._add_vitamins(
                result.vitamins, 
                add_nutrition.vitamins
            )
            
            # Add minerals
            result.minerals = self._add_minerals(
                result.minerals, 
                add_nutrition.minerals
            )
            
            # Combine allergens
            combined_allergens = list(set(result.allergens + add_nutrition.allergens))
            result.allergens = combined_allergens
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding nutrition values: {e}")
            return base_nutrition
    
    def _add_macronutrients(self, base: MacroNutrients, add: MacroNutrients) -> MacroNutrients:
        """Add macronutrient values"""
        result = base.copy() if base else MacroNutrients()
        
        # List of macronutrient fields to add
        fields = [
            'calories', 'protein', 'carbohydrates', 'dietary_fiber', 'sugars',
            'added_sugars', 'total_fat', 'saturated_fat', 'trans_fat',
            'monounsaturated_fat', 'polyunsaturated_fat', 'cholesterol', 'sodium'
        ]
        
        for field in fields:
            base_nutrient = getattr(result, field, None)
            add_nutrient = getattr(add, field, None)
            
            if add_nutrient:
                if base_nutrient:
                    base_nutrient.amount += add_nutrient.amount
                else:
                    setattr(result, field, add_nutrient.copy())
        
        return result
    
    def _add_vitamins(self, base: Vitamins, add: Vitamins) -> Vitamins:
        """Add vitamin values"""
        result = base.copy() if base else Vitamins()
        
        fields = [
            'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
            'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate',
            'vitamin_b12', 'biotin', 'pantothenic_acid'
        ]
        
        for field in fields:
            base_nutrient = getattr(result, field, None)
            add_nutrient = getattr(add, field, None)
            
            if add_nutrient:
                if base_nutrient:
                    base_nutrient.amount += add_nutrient.amount
                else:
                    setattr(result, field, add_nutrient.copy())
        
        return result
    
    def _add_minerals(self, base: Minerals, add: Minerals) -> Minerals:
        """Add mineral values"""
        result = base.copy() if base else Minerals()
        
        fields = [
            'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium',
            'zinc', 'copper', 'manganese', 'selenium', 'chromium', 'molybdenum'
        ]
        
        for field in fields:
            base_nutrient = getattr(result, field, None)
            add_nutrient = getattr(add, field, None)
            
            if add_nutrient:
                if base_nutrient:
                    base_nutrient.amount += add_nutrient.amount
                else:
                    setattr(result, field, add_nutrient.copy())
        
        return result
    
    def _scale_nutrition(self, nutrition: ComprehensiveNutrition, factor: float) -> ComprehensiveNutrition:
        """Scale all nutrition values by a factor"""
        try:
            scaled = nutrition.copy()
            
            # Scale macronutrients
            for field_name in ['calories', 'protein', 'carbohydrates', 'dietary_fiber', 
                              'sugars', 'added_sugars', 'total_fat', 'saturated_fat', 
                              'trans_fat', 'monounsaturated_fat', 'polyunsaturated_fat', 
                              'cholesterol', 'sodium']:
                nutrient = getattr(scaled.macronutrients, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            # Scale vitamins
            for field_name in ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 
                              'vitamin_k', 'thiamin', 'riboflavin', 'niacin', 
                              'vitamin_b6', 'folate', 'vitamin_b12', 'biotin', 
                              'pantothenic_acid']:
                nutrient = getattr(scaled.vitamins, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            # Scale minerals
            for field_name in ['calcium', 'iron', 'magnesium', 'phosphorus', 
                              'potassium', 'zinc', 'copper', 'manganese', 
                              'selenium', 'chromium', 'molybdenum']:
                nutrient = getattr(scaled.minerals, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            return scaled
            
        except Exception as e:
            logger.error(f"Error scaling nutrition: {e}")
            return nutrition
    
    def _calculate_analysis_confidence(
        self, 
        successful_ingredients: int, 
        total_ingredients: int, 
        estimated_ingredients: int
    ) -> float:
        """Calculate confidence score for the nutritional analysis"""
        if total_ingredients == 0:
            return 0.0
        
        # Base confidence from ingredient coverage
        coverage_score = successful_ingredients / total_ingredients
        
        # Reduce confidence for estimated ingredients
        estimation_penalty = (estimated_ingredients / total_ingredients) * 0.3
        
        # Final confidence score
        confidence = max(0.0, min(1.0, coverage_score - estimation_penalty))
        
        return round(confidence, 3)
    
    def _create_ingredient_breakdown(
        self, 
        ingredient_analyses: List[Dict[str, Any]], 
        total_nutrition: ComprehensiveNutrition
    ) -> List[Dict[str, Any]]:
        """Create detailed breakdown of ingredient contributions"""
        breakdown = []
        
        total_calories = total_nutrition.macronutrients.calories.amount if total_nutrition.macronutrients.calories else 0
        
        for analysis in ingredient_analyses:
            if analysis["success"]:
                ingredient_nutrition = analysis["nutrition"]
                ingredient_calories = ingredient_nutrition.macronutrients.calories.amount if ingredient_nutrition.macronutrients.calories else 0
                
                # Calculate percentage contribution
                calorie_percentage = (ingredient_calories / total_calories * 100) if total_calories > 0 else 0
                
                breakdown.append({
                    "ingredient_name": analysis["ingredient_name"],
                    "calories": ingredient_calories,
                    "calorie_percentage": round(calorie_percentage, 1),
                    "protein": ingredient_nutrition.macronutrients.protein.amount if ingredient_nutrition.macronutrients.protein else 0,
                    "carbs": ingredient_nutrition.macronutrients.carbohydrates.amount if ingredient_nutrition.macronutrients.carbohydrates else 0,
                    "fat": ingredient_nutrition.macronutrients.total_fat.amount if ingredient_nutrition.macronutrients.total_fat else 0,
                    "allergens": ingredient_nutrition.allergens,
                    "data_source": analysis["data_source"],
                    "confidence": analysis["confidence"],
                    "estimated": analysis["estimated"]
                })
        
        # Sort by calorie contribution
        breakdown.sort(key=lambda x: x["calories"], reverse=True)
        
        return breakdown
    
    async def _check_dietary_restriction_compliance(
        self, 
        recipe: Recipe, 
        nutrition_analysis: RecipeNutritionAnalysis, 
        restriction: DietaryRestriction
    ) -> Dict[str, Any]:
        """Check if recipe complies with a specific dietary restriction"""
        try:
            rules = self.dietary_restriction_rules.get(restriction, {})
            forbidden_ingredients = rules.get("forbidden_ingredients", [])
            forbidden_allergens = rules.get("forbidden_allergens", [])
            
            violations = []
            
            # Check ingredient names
            for ingredient in recipe.ingredients:
                ingredient_name = ingredient.name.lower()
                for forbidden in forbidden_ingredients:
                    if forbidden in ingredient_name:
                        violations.append(f"Contains {forbidden}")
            
            # Check allergens from nutrition analysis
            for contrib in nutrition_analysis.ingredient_contributions:
                allergens = contrib.get("allergens", [])
                for allergen in allergens:
                    if allergen in forbidden_allergens:
                        violations.append(f"Contains allergen: {allergen.value}")
            
            return {
                "compliant": len(violations) == 0,
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Error checking dietary compliance: {e}")
            return {"compliant": False, "violations": [str(e)]}
    
    async def _generate_nutritional_warnings(self, nutrition: ComprehensiveNutrition) -> List[NutritionalWarning]:
        """Generate nutritional warnings based on thresholds"""
        warnings = []
        
        try:
            macros = nutrition.macronutrients
            
            # High sodium warning
            if macros.sodium and macros.sodium.amount > self.warning_thresholds["high_sodium"]:
                warnings.append(NutritionalWarning(
                    warning_type="high_sodium",
                    severity="medium",
                    message=f"High sodium content: {macros.sodium.amount:.0f}mg per serving",
                    affected_nutrients=["sodium"],
                    recommendation="Consider reducing salt or using herbs and spices for flavor"
                ))
            
            # High saturated fat warning
            if macros.saturated_fat and macros.saturated_fat.amount > self.warning_thresholds["high_saturated_fat"]:
                warnings.append(NutritionalWarning(
                    warning_type="high_saturated_fat",
                    severity="medium",
                    message=f"High saturated fat: {macros.saturated_fat.amount:.1f}g per serving",
                    affected_nutrients=["saturated_fat"],
                    recommendation="Consider using leaner proteins or healthier cooking methods"
                ))
            
            # High sugar warning
            if macros.sugars and macros.sugars.amount > self.warning_thresholds["high_sugar"]:
                warnings.append(NutritionalWarning(
                    warning_type="high_sugar",
                    severity="low",
                    message=f"High sugar content: {macros.sugars.amount:.1f}g per serving",
                    affected_nutrients=["sugars"],
                    recommendation="Consider reducing added sugars or using natural sweeteners"
                ))
            
            # High calorie warning
            if macros.calories and macros.calories.amount > self.warning_thresholds["high_calories"]:
                warnings.append(NutritionalWarning(
                    warning_type="high_calories",
                    severity="low",
                    message=f"High calorie content: {macros.calories.amount:.0f} calories per serving",
                    affected_nutrients=["calories"],
                    recommendation="Consider smaller portions or adding more vegetables"
                ))
            
            # Low protein warning
            if macros.protein and macros.protein.amount < self.warning_thresholds["low_protein"]:
                warnings.append(NutritionalWarning(
                    warning_type="low_protein",
                    severity="low",
                    message=f"Low protein content: {macros.protein.amount:.1f}g per serving",
                    affected_nutrients=["protein"],
                    recommendation="Consider adding protein-rich ingredients"
                ))
            
            # Low fiber warning
            if macros.dietary_fiber and macros.dietary_fiber.amount < self.warning_thresholds["low_fiber"]:
                warnings.append(NutritionalWarning(
                    warning_type="low_fiber",
                    severity="low",
                    message=f"Low fiber content: {macros.dietary_fiber.amount:.1f}g per serving",
                    affected_nutrients=["dietary_fiber"],
                    recommendation="Consider adding more vegetables, fruits, or whole grains"
                ))
            
        except Exception as e:
            logger.error(f"Error generating nutritional warnings: {e}")
        
        return warnings
    
    def _calculate_health_score(
        self, 
        nutrition: ComprehensiveNutrition, 
        warning_count: int, 
        allergen_count: int
    ) -> float:
        """Calculate overall health score for the recipe"""
        try:
            score = 100.0  # Start with perfect score
            
            macros = nutrition.macronutrients
            
            # Positive factors
            if macros.protein and macros.protein.amount >= 10:
                score += 5  # Good protein content
            
            if macros.dietary_fiber and macros.dietary_fiber.amount >= 5:
                score += 5  # Good fiber content
            
            # Negative factors
            if macros.sodium and macros.sodium.amount > 800:
                score -= 15  # Very high sodium
            elif macros.sodium and macros.sodium.amount > 600:
                score -= 10  # High sodium
            
            if macros.saturated_fat and macros.saturated_fat.amount > 20:
                score -= 15  # Very high saturated fat
            elif macros.saturated_fat and macros.saturated_fat.amount > 13:
                score -= 10  # High saturated fat
            
            if macros.sugars and macros.sugars.amount > 50:
                score -= 15  # Very high sugar
            elif macros.sugars and macros.sugars.amount > 25:
                score -= 10  # High sugar
            
            # Penalty for warnings and allergens
            score -= warning_count * 5
            score -= allergen_count * 2
            
            # Ensure score is within bounds
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default moderate score
    
    async def _get_cached_analysis(self, recipe_id: str) -> Optional[RecipeNutritionAnalysis]:
        """Get cached nutrition analysis for a recipe"""
        try:
            cache_collection = await get_collection(self.analysis_cache_collection)
            
            cached_entry = await cache_collection.find_one({
                "recipe_id": recipe_id,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cached_entry:
                return RecipeNutritionAnalysis(**cached_entry["analysis_data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return None
    
    async def _cache_analysis(self, recipe_id: str, analysis: RecipeNutritionAnalysis):
        """Cache nutrition analysis for a recipe"""
        try:
            cache_collection = await get_collection(self.analysis_cache_collection)
            
            cache_entry = {
                "recipe_id": recipe_id,
                "analysis_data": analysis.dict(),
                "cached_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)
            }
            
            await cache_collection.replace_one(
                {"recipe_id": recipe_id},
                cache_entry,
                upsert=True
            )
            
            logger.debug(f"Cached nutrition analysis for recipe: {recipe_id}")
            
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")


# Global service instance
recipe_nutrition_service = RecipeNutritionService()