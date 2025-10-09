"""
Comprehensive nutritional analysis models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId


class NutrientUnit(str, Enum):
    """Enumeration for nutrient units"""
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "μg"
    KILOGRAM = "kg"
    INTERNATIONAL_UNIT = "IU"
    CALORIE = "kcal"
    KILOJOULE = "kJ"
    PERCENT_DV = "%DV"


class AllergenType(str, Enum):
    """Enumeration for common allergens"""
    MILK = "milk"
    EGGS = "eggs"
    FISH = "fish"
    SHELLFISH = "shellfish"
    TREE_NUTS = "tree_nuts"
    PEANUTS = "peanuts"
    WHEAT = "wheat"
    SOYBEANS = "soybeans"
    SESAME = "sesame"


class NutritionalGoalType(str, Enum):
    """Enumeration for nutritional goal types"""
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_GAIN = "muscle_gain"
    HEART_HEALTHY = "heart_healthy"
    LOW_SODIUM = "low_sodium"
    HIGH_PROTEIN = "high_protein"
    LOW_CARB = "low_carb"
    HIGH_FIBER = "high_fiber"
    DIABETIC_FRIENDLY = "diabetic_friendly"
    CUSTOM = "custom"


class NutrientInfo(BaseModel):
    """Model for individual nutrient information"""
    name: str = Field(..., description="Nutrient name")
    amount: float = Field(..., ge=0, description="Amount of nutrient")
    unit: NutrientUnit = Field(..., description="Unit of measurement")
    daily_value_percentage: Optional[float] = Field(None, ge=0, le=200, description="Percentage of daily value")
    source_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence in the data source")


class MacroNutrients(BaseModel):
    """Model for macronutrients"""
    calories: Optional[NutrientInfo] = Field(None, description="Calories")
    protein: Optional[NutrientInfo] = Field(None, description="Protein")
    carbohydrates: Optional[NutrientInfo] = Field(None, description="Total carbohydrates")
    dietary_fiber: Optional[NutrientInfo] = Field(None, description="Dietary fiber")
    sugars: Optional[NutrientInfo] = Field(None, description="Total sugars")
    added_sugars: Optional[NutrientInfo] = Field(None, description="Added sugars")
    total_fat: Optional[NutrientInfo] = Field(None, description="Total fat")
    saturated_fat: Optional[NutrientInfo] = Field(None, description="Saturated fat")
    trans_fat: Optional[NutrientInfo] = Field(None, description="Trans fat")
    monounsaturated_fat: Optional[NutrientInfo] = Field(None, description="Monounsaturated fat")
    polyunsaturated_fat: Optional[NutrientInfo] = Field(None, description="Polyunsaturated fat")
    cholesterol: Optional[NutrientInfo] = Field(None, description="Cholesterol")
    sodium: Optional[NutrientInfo] = Field(None, description="Sodium")


class Vitamins(BaseModel):
    """Model for vitamins"""
    vitamin_a: Optional[NutrientInfo] = Field(None, description="Vitamin A")
    vitamin_c: Optional[NutrientInfo] = Field(None, description="Vitamin C")
    vitamin_d: Optional[NutrientInfo] = Field(None, description="Vitamin D")
    vitamin_e: Optional[NutrientInfo] = Field(None, description="Vitamin E")
    vitamin_k: Optional[NutrientInfo] = Field(None, description="Vitamin K")
    thiamin: Optional[NutrientInfo] = Field(None, description="Thiamin (B1)")
    riboflavin: Optional[NutrientInfo] = Field(None, description="Riboflavin (B2)")
    niacin: Optional[NutrientInfo] = Field(None, description="Niacin (B3)")
    vitamin_b6: Optional[NutrientInfo] = Field(None, description="Vitamin B6")
    folate: Optional[NutrientInfo] = Field(None, description="Folate")
    vitamin_b12: Optional[NutrientInfo] = Field(None, description="Vitamin B12")
    biotin: Optional[NutrientInfo] = Field(None, description="Biotin")
    pantothenic_acid: Optional[NutrientInfo] = Field(None, description="Pantothenic acid")


class Minerals(BaseModel):
    """Model for minerals"""
    calcium: Optional[NutrientInfo] = Field(None, description="Calcium")
    iron: Optional[NutrientInfo] = Field(None, description="Iron")
    magnesium: Optional[NutrientInfo] = Field(None, description="Magnesium")
    phosphorus: Optional[NutrientInfo] = Field(None, description="Phosphorus")
    potassium: Optional[NutrientInfo] = Field(None, description="Potassium")
    zinc: Optional[NutrientInfo] = Field(None, description="Zinc")
    copper: Optional[NutrientInfo] = Field(None, description="Copper")
    manganese: Optional[NutrientInfo] = Field(None, description="Manganese")
    selenium: Optional[NutrientInfo] = Field(None, description="Selenium")
    chromium: Optional[NutrientInfo] = Field(None, description="Chromium")
    molybdenum: Optional[NutrientInfo] = Field(None, description="Molybdenum")


class ComprehensiveNutrition(BaseModel):
    """Comprehensive nutritional information model"""
    macronutrients: MacroNutrients = Field(default_factory=MacroNutrients, description="Macronutrients")
    vitamins: Vitamins = Field(default_factory=Vitamins, description="Vitamins")
    minerals: Minerals = Field(default_factory=Minerals, description="Minerals")
    allergens: List[AllergenType] = Field(default=[], description="Detected allergens")
    additional_nutrients: Dict[str, NutrientInfo] = Field(default={}, description="Additional nutrients not in standard categories")
    nutrition_density_score: Optional[float] = Field(None, ge=0, le=100, description="Overall nutrition density score")
    glycemic_index: Optional[int] = Field(None, ge=0, le=100, description="Estimated glycemic index")
    glycemic_load: Optional[float] = Field(None, ge=0, description="Estimated glycemic load")


class IngredientNutrition(BaseModel):
    """Nutritional information for a single ingredient"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    ingredient_name: str = Field(..., description="Name of the ingredient")
    usda_fdc_id: Optional[str] = Field(None, description="USDA Food Data Central ID")
    serving_size: float = Field(..., gt=0, description="Serving size amount")
    serving_unit: str = Field(..., description="Serving size unit")
    nutrition_per_serving: ComprehensiveNutrition = Field(..., description="Nutrition per serving")
    nutrition_per_100g: Optional[ComprehensiveNutrition] = Field(None, description="Nutrition per 100g")
    data_source: str = Field(..., description="Source of nutritional data")
    data_quality_score: float = Field(..., ge=0, le=1, description="Quality score of the data")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class RecipeNutritionAnalysis(BaseModel):
    """Comprehensive nutritional analysis for a recipe"""
    recipe_id: str = Field(..., description="Recipe ID")
    total_nutrition: ComprehensiveNutrition = Field(..., description="Total nutrition for entire recipe")
    nutrition_per_serving: ComprehensiveNutrition = Field(..., description="Nutrition per serving")
    ingredient_contributions: List[Dict[str, Any]] = Field(default=[], description="Nutritional contribution of each ingredient")
    analysis_confidence: float = Field(..., ge=0, le=1, description="Confidence in the analysis")
    missing_ingredients: List[str] = Field(default=[], description="Ingredients without nutritional data")
    estimated_ingredients: List[str] = Field(default=[], description="Ingredients with estimated nutritional data")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When analysis was performed")
    data_sources: List[str] = Field(default=[], description="Sources used for nutritional data")


class NutritionalGoal(BaseModel):
    """Model for user nutritional goals"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="User ID")
    goal_type: NutritionalGoalType = Field(..., description="Type of nutritional goal")
    target_calories: Optional[int] = Field(None, gt=0, description="Target daily calories")
    target_protein_g: Optional[float] = Field(None, ge=0, description="Target daily protein in grams")
    target_carbs_g: Optional[float] = Field(None, ge=0, description="Target daily carbohydrates in grams")
    target_fat_g: Optional[float] = Field(None, ge=0, description="Target daily fat in grams")
    target_fiber_g: Optional[float] = Field(None, ge=0, description="Target daily fiber in grams")
    target_sodium_mg: Optional[float] = Field(None, ge=0, description="Target daily sodium in mg")
    custom_targets: Dict[str, float] = Field(default={}, description="Custom nutrient targets")
    is_active: bool = Field(default=True, description="Whether this goal is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Goal creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Goal last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class NutritionalWarning(BaseModel):
    """Model for nutritional warnings"""
    warning_type: str = Field(..., description="Type of warning")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    message: str = Field(..., description="Warning message")
    affected_nutrients: List[str] = Field(default=[], description="Nutrients that triggered the warning")
    recommendation: Optional[str] = Field(None, description="Recommendation to address the warning")


class DietaryAnalysis(BaseModel):
    """Comprehensive dietary analysis"""
    recipe_id: str = Field(..., description="Recipe ID")
    dietary_restrictions_met: List[str] = Field(default=[], description="Dietary restrictions this recipe meets")
    dietary_restrictions_violated: List[str] = Field(default=[], description="Dietary restrictions this recipe violates")
    allergens_present: List[AllergenType] = Field(default=[], description="Allergens present in the recipe")
    nutritional_warnings: List[NutritionalWarning] = Field(default=[], description="Nutritional warnings")
    health_score: float = Field(..., ge=0, le=100, description="Overall health score")
    sustainability_score: Optional[float] = Field(None, ge=0, le=100, description="Environmental sustainability score")
    goal_alignment: Dict[str, float] = Field(default={}, description="How well recipe aligns with user goals")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class MealPlanNutritionSummary(BaseModel):
    """Nutritional summary for meal plans"""
    meal_plan_id: str = Field(..., description="Meal plan ID")
    daily_nutrition: Dict[str, ComprehensiveNutrition] = Field(default={}, description="Nutrition by day")
    weekly_totals: ComprehensiveNutrition = Field(..., description="Weekly nutrition totals")
    weekly_averages: ComprehensiveNutrition = Field(..., description="Weekly nutrition averages")
    goal_progress: Dict[str, float] = Field(default={}, description="Progress towards nutritional goals")
    recommendations: List[str] = Field(default=[], description="Nutritional recommendations")
    balance_score: float = Field(..., ge=0, le=100, description="Overall nutritional balance score")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class IngredientLookupRequest(BaseModel):
    """Request model for ingredient nutritional lookup"""
    ingredient_name: str = Field(..., min_length=1, description="Name of the ingredient")
    quantity: Optional[float] = Field(None, gt=0, description="Quantity of ingredient")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    brand: Optional[str] = Field(None, description="Brand name if specific")
    preparation_method: Optional[str] = Field(None, description="Preparation method (raw, cooked, etc.)")


class IngredientLookupResponse(BaseModel):
    """Response model for ingredient nutritional lookup"""
    success: bool = Field(..., description="Whether lookup was successful")
    ingredient_name: str = Field(..., description="Ingredient name")
    matches: List[IngredientNutrition] = Field(default=[], description="Matching ingredients with nutrition data")
    best_match: Optional[IngredientNutrition] = Field(None, description="Best matching ingredient")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in the match")
    data_source: str = Field(..., description="Primary data source used")
    fallback_used: bool = Field(default=False, description="Whether fallback estimation was used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if lookup failed")


class RecipeNutritionRequest(BaseModel):
    """Request model for recipe nutritional analysis"""
    recipe_id: str = Field(..., description="Recipe ID to analyze")
    force_refresh: bool = Field(default=False, description="Force refresh of cached data")
    include_detailed_breakdown: bool = Field(default=True, description="Include detailed ingredient breakdown")
    apply_user_goals: bool = Field(default=True, description="Apply user's nutritional goals to analysis")


class RecipeNutritionResponse(BaseModel):
    """Response model for recipe nutritional analysis"""
    success: bool = Field(..., description="Whether analysis was successful")
    recipe_id: str = Field(..., description="Recipe ID")
    nutrition_analysis: Optional[RecipeNutritionAnalysis] = Field(None, description="Nutritional analysis")
    dietary_analysis: Optional[DietaryAnalysis] = Field(None, description="Dietary analysis")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cache_used: bool = Field(default=False, description="Whether cached data was used")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class BulkIngredientAnalysisRequest(BaseModel):
    """Request model for bulk ingredient analysis"""
    ingredients: List[IngredientLookupRequest] = Field(..., min_items=1, max_items=50, description="List of ingredients to analyze")
    combine_results: bool = Field(default=False, description="Whether to combine results into single nutrition profile")


class BulkIngredientAnalysisResponse(BaseModel):
    """Response model for bulk ingredient analysis"""
    success: bool = Field(..., description="Whether analysis was successful")
    individual_results: List[IngredientLookupResponse] = Field(default=[], description="Individual ingredient results")
    combined_nutrition: Optional[ComprehensiveNutrition] = Field(None, description="Combined nutrition if requested")
    total_processed: int = Field(..., description="Total ingredients processed")
    successful_lookups: int = Field(..., description="Number of successful lookups")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


class NutritionCacheEntry(BaseModel):
    """Model for nutrition data cache entries"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    cache_key: str = Field(..., description="Unique cache key")
    ingredient_name: str = Field(..., description="Ingredient name")
    nutrition_data: IngredientNutrition = Field(..., description="Cached nutrition data")
    hit_count: int = Field(default=1, description="Number of times this cache entry was used")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    expires_at: datetime = Field(..., description="Cache expiration timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Cache creation timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class NutritionServiceStatus(BaseModel):
    """Model for nutrition service status"""
    service_name: str = Field(..., description="Name of the service")
    is_available: bool = Field(..., description="Whether service is available")
    api_key_configured: bool = Field(..., description="Whether API key is configured")
    cache_enabled: bool = Field(..., description="Whether caching is enabled")
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate percentage")
    total_lookups: int = Field(default=0, description="Total number of lookups performed")
    successful_lookups: int = Field(default=0, description="Number of successful lookups")
    failed_lookups: int = Field(default=0, description="Number of failed lookups")
    average_response_time_ms: Optional[float] = Field(None, description="Average response time")
    last_api_call: Optional[datetime] = Field(None, description="Timestamp of last API call")
    error_message: Optional[str] = Field(None, description="Last error message if any")