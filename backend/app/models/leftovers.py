"""
Pydantic models for leftover suggestion management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.recipes import RecipeResponse


class MatchType(str, Enum):
    """Enumeration for ingredient match types"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    CATEGORY = "category"
    SUBSTITUTE = "substitute"


class IngredientMatch(BaseModel):
    """Model for individual ingredient matching details"""
    required_ingredient: str = Field(..., description="Required ingredient name from recipe")
    available_ingredient: Optional[str] = Field(None, description="Available ingredient name from pantry")
    match_type: MatchType = Field(..., description="Type of match found")
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the match (0-1)")
    is_matched: bool = Field(..., description="Whether this ingredient is available")
    quantity_available: Optional[float] = Field(None, description="Available quantity in pantry")
    quantity_required: Optional[float] = Field(None, description="Required quantity for recipe")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    notes: Optional[str] = Field(None, description="Additional notes about the match")


class LeftoverSuggestion(BaseModel):
    """Model for individual recipe suggestions"""
    recipe: RecipeResponse = Field(..., description="The suggested recipe")
    match_score: float = Field(..., ge=0.0, le=100.0, description="Overall match score (0-100)")
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of ingredients available")
    matched_ingredients: List[IngredientMatch] = Field(..., description="List of matched ingredients")
    missing_ingredients: List[IngredientMatch] = Field(..., description="List of missing ingredients")
    total_ingredients: int = Field(..., description="Total number of ingredients in recipe")
    available_ingredients_count: int = Field(..., description="Number of available ingredients")
    missing_ingredients_count: int = Field(..., description="Number of missing ingredients")
    suggestion_reason: str = Field(..., description="Explanation of why this recipe was suggested")
    priority_score: float = Field(..., ge=0.0, description="Priority ranking score")
    estimated_prep_time: Optional[int] = Field(None, description="Estimated preparation time")
    difficulty_bonus: float = Field(default=0.0, description="Bonus points for recipe difficulty")
    freshness_bonus: float = Field(default=0.0, description="Bonus points for using fresh ingredients")
    expiration_urgency: float = Field(default=0.0, description="Urgency score based on ingredient expiration")


class LeftoverSuggestionsResponse(BaseModel):
    """Response model for leftover suggestions API"""
    suggestions: List[LeftoverSuggestion] = Field(..., description="List of recipe suggestions")
    total_suggestions: int = Field(..., description="Total number of suggestions found")
    user_id: str = Field(..., description="User ID for whom suggestions were generated")
    pantry_items_count: int = Field(..., description="Number of pantry items considered")
    recipes_analyzed: int = Field(..., description="Number of recipes analyzed")
    min_match_percentage: float = Field(..., description="Minimum match percentage used for filtering")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when suggestions were generated")
    filters_applied: Dict[str, Any] = Field(default={}, description="Filters applied during suggestion generation")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics for the suggestion process")


class SuggestionFilters(BaseModel):
    """Model for filtering suggestion parameters"""
    max_suggestions: int = Field(default=10, ge=1, le=50, description="Maximum number of suggestions to return")
    min_match_percentage: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum match percentage required")
    max_prep_time: Optional[int] = Field(None, ge=0, description="Maximum preparation time in minutes")
    max_cook_time: Optional[int] = Field(None, ge=0, description="Maximum cooking time in minutes")
    difficulty_levels: Optional[List[str]] = Field(None, description="Allowed difficulty levels")
    meal_types: Optional[List[str]] = Field(None, description="Preferred meal types")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Required dietary restrictions")
    exclude_expired: bool = Field(default=True, description="Whether to exclude recipes requiring expired ingredients")
    prioritize_expiring: bool = Field(default=True, description="Whether to prioritize recipes using expiring ingredients")
    include_substitutes: bool = Field(default=True, description="Whether to consider ingredient substitutes")


class IngredientSubstitute(BaseModel):
    """Model for ingredient substitution information"""
    original_ingredient: str = Field(..., description="Original ingredient name")
    substitute_ingredient: str = Field(..., description="Substitute ingredient name")
    substitution_ratio: float = Field(default=1.0, description="Ratio for substitution (substitute/original)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in substitution quality")
    notes: Optional[str] = Field(None, description="Notes about the substitution")


class PantryIngredientInfo(BaseModel):
    """Model for pantry ingredient information used in suggestions"""
    name: str = Field(..., description="Ingredient name")
    normalized_name: str = Field(..., description="Normalized ingredient name for matching")
    category: str = Field(..., description="Ingredient category")
    quantity: float = Field(..., description="Available quantity")
    unit: str = Field(..., description="Unit of measurement")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date")
    days_until_expiration: Optional[int] = Field(None, description="Days until expiration")
    is_expired: bool = Field(default=False, description="Whether the ingredient is expired")
    is_expiring_soon: bool = Field(default=False, description="Whether the ingredient is expiring soon")
    freshness_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Freshness score (1.0 = fresh, 0.0 = expired)")


class SuggestionRequest(BaseModel):
    """Model for leftover suggestion requests"""
    user_id: str = Field(..., description="User ID requesting suggestions")
    filters: Optional[SuggestionFilters] = Field(default_factory=SuggestionFilters, description="Suggestion filters")
    include_debug_info: bool = Field(default=False, description="Whether to include debug information in response")
    force_refresh: bool = Field(default=False, description="Whether to force refresh of cached data")


class SuggestionDebugInfo(BaseModel):
    """Model for debug information in suggestions"""
    pantry_ingredients: List[PantryIngredientInfo] = Field(..., description="Pantry ingredients used")
    recipes_considered: int = Field(..., description="Number of recipes considered")
    recipes_filtered_out: int = Field(..., description="Number of recipes filtered out")
    matching_algorithm_version: str = Field(default="1.0", description="Version of matching algorithm used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether cached results were used")
    error_messages: List[str] = Field(default=[], description="Any error messages during processing")


class LeftoverSuggestionsDebugResponse(LeftoverSuggestionsResponse):
    """Extended response model with debug information"""
    debug_info: Optional[SuggestionDebugInfo] = Field(None, description="Debug information")


# Validation functions
@validator('match_confidence', 'freshness_score', pre=True)
def validate_score_range(cls, v):
    """Ensure scores are within valid range"""
    if v is not None and (v < 0.0 or v > 1.0):
        raise ValueError('Score must be between 0.0 and 1.0')
    return v


@validator('match_score', 'match_percentage', pre=True)
def validate_percentage_range(cls, v):
    """Ensure percentages are within valid range"""
    if v is not None and (v < 0.0 or v > 100.0):
        raise ValueError('Percentage must be between 0.0 and 100.0')
    return v