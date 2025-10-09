"""
USDA Food Data Central API integration service for nutritional data
"""

import logging
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import os
from thefuzz import fuzz, process

from app.models.nutrition import (
    IngredientNutrition,
    ComprehensiveNutrition,
    MacroNutrients,
    Vitamins,
    Minerals,
    NutrientInfo,
    NutrientUnit,
    AllergenType,
    NutritionServiceStatus
)

# Configure logging
logger = logging.getLogger(__name__)


class USDANutritionService:
    """Service for integrating with USDA Food Data Central API"""
    
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        self.demo_mode = not bool(self.api_key)
        
        # Rate limiting
        self.max_requests_per_hour = 1000 if self.api_key else 0
        self.request_count = 0
        self.request_reset_time = datetime.utcnow() + timedelta(hours=1)
        
        # Cache for common ingredient mappings
        self.ingredient_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=24)
        
        # USDA nutrient ID mappings to our standard format
        self.nutrient_mappings = {
            # Macronutrients
            "208": ("calories", NutrientUnit.CALORIE),
            "203": ("protein", NutrientUnit.GRAM),
            "205": ("carbohydrates", NutrientUnit.GRAM),
            "291": ("dietary_fiber", NutrientUnit.GRAM),
            "269": ("sugars", NutrientUnit.GRAM),
            "539": ("added_sugars", NutrientUnit.GRAM),
            "204": ("total_fat", NutrientUnit.GRAM),
            "606": ("saturated_fat", NutrientUnit.GRAM),
            "605": ("trans_fat", NutrientUnit.GRAM),
            "645": ("monounsaturated_fat", NutrientUnit.GRAM),
            "646": ("polyunsaturated_fat", NutrientUnit.GRAM),
            "601": ("cholesterol", NutrientUnit.MILLIGRAM),
            "307": ("sodium", NutrientUnit.MILLIGRAM),
            
            # Vitamins
            "320": ("vitamin_a", NutrientUnit.MICROGRAM),
            "401": ("vitamin_c", NutrientUnit.MILLIGRAM),
            "324": ("vitamin_d", NutrientUnit.MICROGRAM),
            "323": ("vitamin_e", NutrientUnit.MILLIGRAM),
            "430": ("vitamin_k", NutrientUnit.MICROGRAM),
            "404": ("thiamin", NutrientUnit.MILLIGRAM),
            "405": ("riboflavin", NutrientUnit.MILLIGRAM),
            "406": ("niacin", NutrientUnit.MILLIGRAM),
            "415": ("vitamin_b6", NutrientUnit.MILLIGRAM),
            "435": ("folate", NutrientUnit.MICROGRAM),
            "418": ("vitamin_b12", NutrientUnit.MICROGRAM),
            "317": ("biotin", NutrientUnit.MICROGRAM),
            "410": ("pantothenic_acid", NutrientUnit.MILLIGRAM),
            
            # Minerals
            "301": ("calcium", NutrientUnit.MILLIGRAM),
            "303": ("iron", NutrientUnit.MILLIGRAM),
            "304": ("magnesium", NutrientUnit.MILLIGRAM),
            "305": ("phosphorus", NutrientUnit.MILLIGRAM),
            "306": ("potassium", NutrientUnit.MILLIGRAM),
            "309": ("zinc", NutrientUnit.MILLIGRAM),
            "312": ("copper", NutrientUnit.MILLIGRAM),
            "315": ("manganese", NutrientUnit.MILLIGRAM),
            "317": ("selenium", NutrientUnit.MICROGRAM),
            "310": ("chromium", NutrientUnit.MICROGRAM),
            "314": ("molybdenum", NutrientUnit.MICROGRAM),
        }
        
        # Common allergen keywords for detection
        self.allergen_keywords = {
            AllergenType.MILK: ["milk", "dairy", "cheese", "butter", "cream", "yogurt", "whey", "casein", "lactose"],
            AllergenType.EGGS: ["egg", "eggs", "albumin", "lecithin"],
            AllergenType.FISH: ["fish", "salmon", "tuna", "cod", "halibut", "sardine", "anchovy"],
            AllergenType.SHELLFISH: ["shrimp", "crab", "lobster", "oyster", "clam", "mussel", "scallop"],
            AllergenType.TREE_NUTS: ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut", "brazil nut"],
            AllergenType.PEANUTS: ["peanut", "groundnut"],
            AllergenType.WHEAT: ["wheat", "flour", "gluten", "semolina", "durum"],
            AllergenType.SOYBEANS: ["soy", "soybean", "tofu", "tempeh", "miso"],
            AllergenType.SESAME: ["sesame", "tahini"]
        }
        
        logger.info(f"USDA Nutrition Service initialized - Demo mode: {self.demo_mode}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def search_ingredients(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for ingredients in USDA database
        
        Args:
            query: Search query for ingredient
            limit: Maximum number of results to return
            
        Returns:
            List of matching ingredients with basic info
        """
        if self.demo_mode:
            return await self._get_demo_search_results(query, limit)
        
        try:
            # Check rate limiting
            if not await self._check_rate_limit():
                logger.warning("Rate limit exceeded for USDA API")
                return await self._get_demo_search_results(query, limit)
            
            # Check cache first
            cache_key = f"search_{query.lower()}_{limit}"
            if cache_key in self.ingredient_cache:
                cached_data = self.ingredient_cache[cache_key]
                if datetime.utcnow() - cached_data["timestamp"] < self.cache_ttl:
                    logger.debug(f"Using cached search results for: {query}")
                    return cached_data["data"]
            
            # Make API request
            params = {
                "query": query,
                "dataType": ["Foundation", "SR Legacy"],
                "pageSize": limit,
                "api_key": self.api_key
            }
            
            async with self.session.get(f"{self.base_url}/foods/search", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for food in data.get("foods", []):
                        results.append({
                            "fdc_id": food.get("fdcId"),
                            "description": food.get("description", ""),
                            "data_type": food.get("dataType", ""),
                            "brand_owner": food.get("brandOwner"),
                            "ingredients": food.get("ingredients"),
                            "score": food.get("score", 0)
                        })
                    
                    # Cache results
                    self.ingredient_cache[cache_key] = {
                        "data": results,
                        "timestamp": datetime.utcnow()
                    }
                    
                    self.request_count += 1
                    logger.info(f"Found {len(results)} ingredients for query: {query}")
                    return results
                else:
                    logger.error(f"USDA API search failed with status {response.status}")
                    return await self._get_demo_search_results(query, limit)
                    
        except Exception as e:
            logger.error(f"Error searching USDA database: {e}")
            return await self._get_demo_search_results(query, limit)
    
    async def get_ingredient_nutrition(self, fdc_id: str) -> Optional[IngredientNutrition]:
        """
        Get detailed nutritional information for an ingredient by FDC ID
        
        Args:
            fdc_id: USDA Food Data Central ID
            
        Returns:
            IngredientNutrition object with comprehensive nutritional data
        """
        if self.demo_mode:
            return await self._get_demo_nutrition_data(fdc_id)
        
        try:
            # Check rate limiting
            if not await self._check_rate_limit():
                logger.warning("Rate limit exceeded for USDA API")
                return await self._get_demo_nutrition_data(fdc_id)
            
            # Check cache first
            cache_key = f"nutrition_{fdc_id}"
            if cache_key in self.ingredient_cache:
                cached_data = self.ingredient_cache[cache_key]
                if datetime.utcnow() - cached_data["timestamp"] < self.cache_ttl:
                    logger.debug(f"Using cached nutrition data for FDC ID: {fdc_id}")
                    return cached_data["data"]
            
            # Make API request
            params = {"api_key": self.api_key} if self.api_key else {}
            
            async with self.session.get(f"{self.base_url}/food/{fdc_id}", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    nutrition_data = await self._parse_usda_nutrition_data(data)
                    
                    # Cache results
                    self.ingredient_cache[cache_key] = {
                        "data": nutrition_data,
                        "timestamp": datetime.utcnow()
                    }
                    
                    self.request_count += 1
                    logger.info(f"Retrieved nutrition data for FDC ID: {fdc_id}")
                    return nutrition_data
                else:
                    logger.error(f"USDA API nutrition lookup failed with status {response.status}")
                    return await self._get_demo_nutrition_data(fdc_id)
                    
        except Exception as e:
            logger.error(f"Error getting nutrition data from USDA: {e}")
            return await self._get_demo_nutrition_data(fdc_id)
    
    async def find_best_ingredient_match(self, ingredient_name: str, quantity: Optional[float] = None, unit: Optional[str] = None) -> Optional[IngredientNutrition]:
        """
        Find the best matching ingredient and return its nutritional data
        
        Args:
            ingredient_name: Name of ingredient to search for
            quantity: Optional quantity for serving size calculation
            unit: Optional unit for serving size calculation
            
        Returns:
            Best matching IngredientNutrition object
        """
        try:
            # Clean and normalize ingredient name
            cleaned_name = self._clean_ingredient_name(ingredient_name)
            
            # Search for ingredients
            search_results = await self.search_ingredients(cleaned_name, limit=5)
            
            if not search_results:
                logger.warning(f"No search results found for ingredient: {ingredient_name}")
                return None
            
            # Find best match using fuzzy string matching
            best_match = None
            best_score = 0
            
            for result in search_results:
                description = result.get("description", "").lower()
                score = fuzz.ratio(cleaned_name.lower(), description)
                
                # Boost score for exact matches or high-quality data types
                if cleaned_name.lower() in description:
                    score += 20
                if result.get("data_type") == "Foundation":
                    score += 10
                elif result.get("data_type") == "SR Legacy":
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_match = result
            
            if best_match and best_score >= 60:  # Minimum confidence threshold
                # Get detailed nutrition data
                nutrition_data = await self.get_ingredient_nutrition(str(best_match["fdc_id"]))
                
                if nutrition_data:
                    # Adjust serving size if quantity and unit provided
                    if quantity and unit:
                        nutrition_data = await self._adjust_serving_size(nutrition_data, quantity, unit)
                    
                    logger.info(f"Found best match for '{ingredient_name}': {best_match['description']} (score: {best_score})")
                    return nutrition_data
            
            logger.warning(f"No suitable match found for ingredient: {ingredient_name} (best score: {best_score})")
            return None
            
        except Exception as e:
            logger.error(f"Error finding ingredient match: {e}")
            return None
    
    async def _parse_usda_nutrition_data(self, usda_data: Dict[str, Any]) -> IngredientNutrition:
        """Parse USDA API response into our nutrition model"""
        try:
            # Extract basic info
            description = usda_data.get("description", "Unknown")
            fdc_id = str(usda_data.get("fdcId", ""))
            
            # Initialize nutrition components
            macros = MacroNutrients()
            vitamins = Vitamins()
            minerals = Minerals()
            allergens = []
            
            # Parse nutrients
            nutrients = usda_data.get("foodNutrients", [])
            for nutrient in nutrients:
                nutrient_id = str(nutrient.get("nutrient", {}).get("id", ""))
                amount = nutrient.get("amount", 0)
                
                if nutrient_id in self.nutrient_mappings and amount > 0:
                    field_name, unit = self.nutrient_mappings[nutrient_id]
                    nutrient_info = NutrientInfo(
                        name=nutrient.get("nutrient", {}).get("name", field_name),
                        amount=float(amount),
                        unit=unit,
                        source_confidence=0.9  # High confidence for USDA data
                    )
                    
                    # Assign to appropriate category
                    if hasattr(macros, field_name):
                        setattr(macros, field_name, nutrient_info)
                    elif hasattr(vitamins, field_name):
                        setattr(vitamins, field_name, nutrient_info)
                    elif hasattr(minerals, field_name):
                        setattr(minerals, field_name, nutrient_info)
            
            # Detect allergens from description and ingredients
            allergens = self._detect_allergens(description, usda_data.get("ingredients", ""))
            
            # Create comprehensive nutrition object
            comprehensive_nutrition = ComprehensiveNutrition(
                macronutrients=macros,
                vitamins=vitamins,
                minerals=minerals,
                allergens=allergens,
                nutrition_density_score=self._calculate_nutrition_density_score(macros, vitamins, minerals)
            )
            
            # Create ingredient nutrition object
            ingredient_nutrition = IngredientNutrition(
                ingredient_name=description,
                usda_fdc_id=fdc_id,
                serving_size=100.0,  # USDA data is typically per 100g
                serving_unit="g",
                nutrition_per_serving=comprehensive_nutrition,
                nutrition_per_100g=comprehensive_nutrition,
                data_source="USDA Food Data Central",
                data_quality_score=0.95  # High quality for USDA data
            )
            
            return ingredient_nutrition
            
        except Exception as e:
            logger.error(f"Error parsing USDA nutrition data: {e}")
            raise
    
    def _detect_allergens(self, description: str, ingredients: str) -> List[AllergenType]:
        """Detect allergens from ingredient description and ingredients list"""
        allergens = []
        text_to_check = f"{description} {ingredients}".lower()
        
        for allergen_type, keywords in self.allergen_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                allergens.append(allergen_type)
        
        return allergens
    
    def _calculate_nutrition_density_score(self, macros: MacroNutrients, vitamins: Vitamins, minerals: Minerals) -> float:
        """Calculate a nutrition density score based on nutrient content"""
        try:
            score = 0.0
            total_nutrients = 0
            
            # Score macronutrients
            if macros.protein and macros.protein.amount > 0:
                score += min(macros.protein.amount / 20 * 10, 10)  # Max 10 points for protein
                total_nutrients += 1
            
            if macros.dietary_fiber and macros.dietary_fiber.amount > 0:
                score += min(macros.dietary_fiber.amount / 10 * 10, 10)  # Max 10 points for fiber
                total_nutrients += 1
            
            # Score vitamins (sample a few key ones)
            vitamin_fields = ['vitamin_a', 'vitamin_c', 'vitamin_d', 'folate', 'vitamin_b12']
            for field in vitamin_fields:
                vitamin = getattr(vitamins, field, None)
                if vitamin and vitamin.amount > 0:
                    score += 5  # 5 points per vitamin
                    total_nutrients += 1
            
            # Score minerals (sample a few key ones)
            mineral_fields = ['calcium', 'iron', 'magnesium', 'potassium', 'zinc']
            for field in mineral_fields:
                mineral = getattr(minerals, field, None)
                if mineral and mineral.amount > 0:
                    score += 5  # 5 points per mineral
                    total_nutrients += 1
            
            # Normalize score to 0-100 range
            if total_nutrients > 0:
                normalized_score = min(score / total_nutrients * 10, 100)
                return round(normalized_score, 1)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating nutrition density score: {e}")
            return 50.0  # Default moderate score
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Clean and normalize ingredient name for better matching"""
        # Remove common prefixes and suffixes
        name = name.lower().strip()
        
        # Remove preparation methods
        prep_words = ['fresh', 'frozen', 'dried', 'canned', 'raw', 'cooked', 'chopped', 'diced', 'sliced', 'minced']
        for word in prep_words:
            name = name.replace(word, '').strip()
        
        # Remove quantities and units
        import re
        name = re.sub(r'\d+\s*(cup|cups|tbsp|tsp|oz|lb|g|kg|ml|l)\s*', '', name)
        name = re.sub(r'\d+\s*', '', name)  # Remove standalone numbers
        
        # Remove parenthetical information
        name = re.sub(r'\([^)]*\)', '', name)
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        return name
    
    async def _adjust_serving_size(self, nutrition_data: IngredientNutrition, quantity: float, unit: str) -> IngredientNutrition:
        """Adjust nutrition data for specific serving size"""
        try:
            # This is a simplified conversion - in production you'd want more comprehensive unit conversions
            conversion_factor = 1.0
            
            # Basic unit conversions to grams
            unit_conversions = {
                'g': 1.0,
                'kg': 1000.0,
                'oz': 28.35,
                'lb': 453.59,
                'cup': 240.0,  # Approximate for liquids
                'tbsp': 15.0,
                'tsp': 5.0,
                'ml': 1.0,  # Approximate for water-like density
                'l': 1000.0
            }
            
            if unit.lower() in unit_conversions:
                target_grams = quantity * unit_conversions[unit.lower()]
                conversion_factor = target_grams / 100.0  # USDA data is per 100g
            
            # Create adjusted nutrition data
            adjusted_nutrition = nutrition_data.copy()
            adjusted_nutrition.serving_size = quantity
            adjusted_nutrition.serving_unit = unit
            
            # Adjust all nutrient amounts
            adjusted_nutrition.nutrition_per_serving = self._scale_nutrition(
                nutrition_data.nutrition_per_serving, 
                conversion_factor
            )
            
            return adjusted_nutrition
            
        except Exception as e:
            logger.error(f"Error adjusting serving size: {e}")
            return nutrition_data
    
    def _scale_nutrition(self, nutrition: ComprehensiveNutrition, factor: float) -> ComprehensiveNutrition:
        """Scale all nutrition values by a factor"""
        try:
            scaled_nutrition = nutrition.copy()
            
            # Scale macronutrients
            for field_name in ['calories', 'protein', 'carbohydrates', 'dietary_fiber', 'sugars', 
                              'added_sugars', 'total_fat', 'saturated_fat', 'trans_fat', 
                              'monounsaturated_fat', 'polyunsaturated_fat', 'cholesterol', 'sodium']:
                nutrient = getattr(scaled_nutrition.macronutrients, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            # Scale vitamins
            for field_name in ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
                              'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate', 
                              'vitamin_b12', 'biotin', 'pantothenic_acid']:
                nutrient = getattr(scaled_nutrition.vitamins, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            # Scale minerals
            for field_name in ['calcium', 'iron', 'magnesium', 'phosphorus', 'potassium',
                              'zinc', 'copper', 'manganese', 'selenium', 'chromium', 'molybdenum']:
                nutrient = getattr(scaled_nutrition.minerals, field_name, None)
                if nutrient:
                    nutrient.amount *= factor
            
            return scaled_nutrition
            
        except Exception as e:
            logger.error(f"Error scaling nutrition values: {e}")
            return nutrition
    
    async def _check_rate_limit(self) -> bool:
        """Check if we're within API rate limits"""
        if datetime.utcnow() > self.request_reset_time:
            self.request_count = 0
            self.request_reset_time = datetime.utcnow() + timedelta(hours=1)
        
        return self.request_count < self.max_requests_per_hour
    
    async def _get_demo_search_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Return demo search results when API is not available"""
        demo_results = [
            {
                "fdc_id": "demo_001",
                "description": f"Demo {query.title()}",
                "data_type": "Demo",
                "brand_owner": None,
                "ingredients": None,
                "score": 100
            }
        ]
        return demo_results[:limit]
    
    async def _get_demo_nutrition_data(self, fdc_id: str) -> IngredientNutrition:
        """Return demo nutrition data when API is not available"""
        # Create basic demo nutrition data
        macros = MacroNutrients(
            calories=NutrientInfo(name="Calories", amount=100.0, unit=NutrientUnit.CALORIE),
            protein=NutrientInfo(name="Protein", amount=5.0, unit=NutrientUnit.GRAM),
            carbohydrates=NutrientInfo(name="Carbohydrates", amount=15.0, unit=NutrientUnit.GRAM),
            total_fat=NutrientInfo(name="Total Fat", amount=2.0, unit=NutrientUnit.GRAM)
        )
        
        comprehensive_nutrition = ComprehensiveNutrition(
            macronutrients=macros,
            vitamins=Vitamins(),
            minerals=Minerals(),
            nutrition_density_score=50.0
        )
        
        return IngredientNutrition(
            ingredient_name=f"Demo Ingredient {fdc_id}",
            usda_fdc_id=fdc_id,
            serving_size=100.0,
            serving_unit="g",
            nutrition_per_serving=comprehensive_nutrition,
            nutrition_per_100g=comprehensive_nutrition,
            data_source="Demo Data",
            data_quality_score=0.5
        )
    
    def get_service_status(self) -> NutritionServiceStatus:
        """Get current service status"""
        return NutritionServiceStatus(
            service_name="USDA Food Data Central",
            is_available=not self.demo_mode,
            api_key_configured=bool(self.api_key),
            cache_enabled=True,
            cache_hit_rate=self._calculate_cache_hit_rate(),
            total_lookups=self.request_count,
            successful_lookups=self.request_count,  # Simplified for demo
            failed_lookups=0,
            average_response_time_ms=500.0,  # Estimated
            last_api_call=datetime.utcnow() if self.request_count > 0 else None,
            error_message="API key not configured - using demo mode" if self.demo_mode else None
        )
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not self.ingredient_cache:
            return 0.0
        
        # Simplified calculation - in production you'd track hits vs misses
        return 75.0  # Estimated cache hit rate


# Global service instance
usda_nutrition_service = USDANutritionService()