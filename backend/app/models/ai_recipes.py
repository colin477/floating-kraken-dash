"""
Pydantic models for AI recipe generation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.recipes import (
    RecipeResponse, 
    DifficultyLevel, 
    MealType, 
    DietaryRestriction
)


class RecipeGenerationSource(str, Enum):
    """Source of recipe generation request"""
    INGREDIENTS = "ingredients"
    PANTRY = "pantry"
    RECEIPT = "receipt"
    CUSTOM = "custom"


class RecipeGenerationRequest(BaseModel):
    """Request model for AI recipe generation"""
    ingredients: List[str] = Field(..., min_items=1, max_items=20, description="List of available ingredients")
    cuisine_preference: Optional[str] = Field(None, max_length=50, description="Preferred cuisine type (e.g., Italian, Asian, Mexican)")
    meal_type: Optional[MealType] = Field(None, description="Preferred meal type")
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(default=[], description="Dietary restrictions to follow")
    difficulty_preference: Optional[DifficultyLevel] = Field(None, description="Preferred difficulty level")
    servings: int = Field(default=4, ge=1, le=12, description="Number of servings")
    max_prep_time: Optional[int] = Field(None, ge=5, le=180, description="Maximum prep time in minutes")
    max_cook_time: Optional[int] = Field(None, ge=5, le=300, description="Maximum cook time in minutes")
    exclude_ingredients: Optional[List[str]] = Field(default=[], description="Ingredients to avoid")
    include_nutrition: bool = Field(default=True, description="Whether to include nutritional information")
    
    @validator('ingredients')
    def validate_ingredients(cls, v):
        """Ensure ingredients are not empty and clean them"""
        if not v:
            raise ValueError('At least one ingredient is required')
        
        cleaned_ingredients = []
        for ingredient in v:
            if isinstance(ingredient, str) and ingredient.strip():
                cleaned_ingredients.append(ingredient.strip().title())
        
        if not cleaned_ingredients:
            raise ValueError('All ingredients cannot be empty')
        
        return cleaned_ingredients
    
    @validator('exclude_ingredients')
    def validate_exclude_ingredients(cls, v):
        """Clean exclude ingredients list"""
        if not v:
            return []
        
        cleaned = []
        for ingredient in v:
            if isinstance(ingredient, str) and ingredient.strip():
                cleaned.append(ingredient.strip().title())
        
        return cleaned


class RecipeGenerationResponse(BaseModel):
    """Response model for AI recipe generation"""
    success: bool = Field(..., description="Whether recipe generation was successful")
    recipe: Optional[RecipeResponse] = Field(None, description="Generated recipe if successful")
    generation_source: RecipeGenerationSource = Field(..., description="Source of the generation request")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the generated recipe")
    ingredient_match_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of requested ingredients used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    ai_model_used: Optional[str] = Field(None, description="AI model used for generation")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the recipe was generated")
    
    # Quality metrics
    recipe_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall recipe quality score")
    safety_validated: bool = Field(default=True, description="Whether recipe passed food safety validation")
    nutritional_balance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nutritional balance score")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    fallback_used: bool = Field(default=False, description="Whether fallback/demo mode was used")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata about the generation process")


class BulkRecipeGenerationRequest(BaseModel):
    """Request model for generating multiple recipes from the same ingredients"""
    ingredients: List[str] = Field(..., min_items=1, max_items=20, description="List of available ingredients")
    recipe_count: int = Field(default=3, ge=1, le=5, description="Number of different recipes to generate")
    variety_preference: str = Field(default="diverse", pattern="^(diverse|similar|themed)$", description="Type of variety in generated recipes")
    base_preferences: Optional[RecipeGenerationRequest] = Field(None, description="Base preferences to apply to all recipes")


class BulkRecipeGenerationResponse(BaseModel):
    """Response model for bulk recipe generation"""
    success: bool = Field(..., description="Whether bulk generation was successful")
    recipes: List[RecipeGenerationResponse] = Field(..., description="List of generated recipes")
    total_requested: int = Field(..., description="Total number of recipes requested")
    total_generated: int = Field(..., description="Total number of recipes successfully generated")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the bulk generation was completed")


class RecipeValidationResult(BaseModel):
    """Result of recipe validation"""
    is_valid: bool = Field(..., description="Whether the recipe is valid")
    safety_score: float = Field(..., ge=0.0, le=1.0, description="Food safety score")
    practicality_score: float = Field(..., ge=0.0, le=1.0, description="Recipe practicality score")
    nutrition_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nutritional balance score")
    
    # Validation issues
    safety_issues: List[str] = Field(default=[], description="Food safety concerns identified")
    practicality_issues: List[str] = Field(default=[], description="Practicality issues identified")
    nutrition_issues: List[str] = Field(default=[], description="Nutritional concerns identified")
    
    # Suggestions for improvement
    improvement_suggestions: List[str] = Field(default=[], description="Suggestions to improve the recipe")
    
    # Overall assessment
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall recipe quality score")
    recommendation: str = Field(..., description="Recommendation for the recipe (approve, modify, reject)")


class RecipeEnhancementRequest(BaseModel):
    """Request to enhance an existing recipe with AI"""
    recipe_id: str = Field(..., description="ID of the recipe to enhance")
    enhancement_type: str = Field(..., pattern="^(nutrition|instructions|variations|tips)$", description="Type of enhancement requested")
    specific_requests: Optional[List[str]] = Field(default=[], description="Specific enhancement requests")


class RecipeEnhancementResponse(BaseModel):
    """Response for recipe enhancement"""
    success: bool = Field(..., description="Whether enhancement was successful")
    original_recipe: RecipeResponse = Field(..., description="Original recipe")
    enhanced_recipe: Optional[RecipeResponse] = Field(None, description="Enhanced recipe if successful")
    enhancement_type: str = Field(..., description="Type of enhancement applied")
    changes_made: List[str] = Field(default=[], description="List of changes made to the recipe")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if enhancement failed")


class IngredientSubstitutionRequest(BaseModel):
    """Request for ingredient substitution suggestions"""
    original_ingredient: str = Field(..., description="Original ingredient to substitute")
    recipe_context: Optional[str] = Field(None, description="Context of the recipe (cuisine, dish type, etc.)")
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(default=[], description="Dietary restrictions to consider")
    available_ingredients: Optional[List[str]] = Field(default=[], description="Available ingredients to use as substitutes")


class IngredientSubstitution(BaseModel):
    """Individual ingredient substitution"""
    substitute_ingredient: str = Field(..., description="Substitute ingredient name")
    substitution_ratio: float = Field(..., gt=0, description="Ratio for substitution (substitute amount / original amount)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this substitution")
    flavor_impact: str = Field(..., pattern="^(minimal|slight|moderate|significant)$", description="Expected impact on flavor")
    texture_impact: str = Field(..., pattern="^(minimal|slight|moderate|significant)$", description="Expected impact on texture")
    notes: Optional[str] = Field(None, description="Additional notes about the substitution")


class IngredientSubstitutionResponse(BaseModel):
    """Response for ingredient substitution suggestions"""
    success: bool = Field(..., description="Whether substitution suggestions were generated successfully")
    original_ingredient: str = Field(..., description="Original ingredient")
    substitutions: List[IngredientSubstitution] = Field(default=[], description="List of possible substitutions")
    best_substitution: Optional[IngredientSubstitution] = Field(None, description="Recommended best substitution")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")


class RecipeGenerationStats(BaseModel):
    """Statistics for recipe generation service"""
    total_recipes_generated: int = Field(..., description="Total number of recipes generated")
    successful_generations: int = Field(..., description="Number of successful generations")
    failed_generations: int = Field(..., description="Number of failed generations")
    average_processing_time_ms: float = Field(..., description="Average processing time in milliseconds")
    average_confidence_score: float = Field(..., description="Average confidence score")
    most_common_cuisines: List[Dict[str, Any]] = Field(default=[], description="Most commonly requested cuisines")
    most_common_ingredients: List[Dict[str, Any]] = Field(default=[], description="Most commonly used ingredients")
    service_uptime_percentage: float = Field(..., description="Service uptime percentage")
    demo_mode_usage_percentage: float = Field(..., description="Percentage of requests served by demo mode")