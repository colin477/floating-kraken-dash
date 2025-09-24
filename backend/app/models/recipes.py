"""
Pydantic models for recipe management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum


class DifficultyLevel(str, Enum):
    """Enumeration for recipe difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MealType(str, Enum):
    """Enumeration for meal types"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    APPETIZER = "appetizer"
    BEVERAGE = "beverage"


class DietaryRestriction(str, Enum):
    """Enumeration for dietary restrictions"""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    LOW_CARB = "low_carb"
    KETO = "keto"
    PALEO = "paleo"
    HALAL = "halal"
    KOSHER = "kosher"


class RecipeIngredient(BaseModel):
    """Model for recipe ingredients"""
    name: str = Field(..., min_length=1, max_length=200, description="Ingredient name")
    quantity: float = Field(..., gt=0, description="Ingredient quantity")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement")
    notes: Optional[str] = Field(None, max_length=200, description="Additional notes about the ingredient")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Ingredient name cannot be empty')
        return v.strip()

    @validator('unit')
    def validate_unit(cls, v):
        """Ensure unit is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Ingredient unit cannot be empty')
        return v.strip()


class RecipeNutrition(BaseModel):
    """Model for recipe nutritional information"""
    calories_per_serving: Optional[int] = Field(None, ge=0, description="Calories per serving")
    protein_g: Optional[float] = Field(None, ge=0, description="Protein in grams")
    carbs_g: Optional[float] = Field(None, ge=0, description="Carbohydrates in grams")
    fat_g: Optional[float] = Field(None, ge=0, description="Fat in grams")
    fiber_g: Optional[float] = Field(None, ge=0, description="Fiber in grams")
    sugar_g: Optional[float] = Field(None, ge=0, description="Sugar in grams")
    sodium_mg: Optional[float] = Field(None, ge=0, description="Sodium in milligrams")


class Recipe(BaseModel):
    """Main recipe model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    title: str = Field(..., min_length=1, max_length=200, description="Recipe title")
    description: Optional[str] = Field(None, max_length=1000, description="Recipe description")
    ingredients: List[RecipeIngredient] = Field(..., min_items=1, description="List of recipe ingredients")
    instructions: List[str] = Field(..., min_items=1, description="List of cooking instructions")
    prep_time: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")
    servings: int = Field(..., gt=0, description="Number of servings")
    difficulty: DifficultyLevel = Field(..., description="Recipe difficulty level")
    tags: List[str] = Field(default=[], description="Recipe tags for categorization")
    meal_types: List[MealType] = Field(default=[], description="Meal types this recipe is suitable for")
    dietary_restrictions: List[DietaryRestriction] = Field(default=[], description="Dietary restrictions this recipe meets")
    nutrition_info: Optional[RecipeNutrition] = Field(None, description="Nutritional information")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to recipe photo")
    source_url: Optional[str] = Field(None, max_length=500, description="Original source URL if imported")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Recipe creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Recipe last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Recipe title cannot be empty')
        return v.strip()

    @validator('instructions')
    def validate_instructions(cls, v):
        """Ensure all instructions are non-empty"""
        if not v:
            raise ValueError('Recipe must have at least one instruction')
        cleaned_instructions = []
        for instruction in v:
            if isinstance(instruction, str) and instruction.strip():
                cleaned_instructions.append(instruction.strip())
        if not cleaned_instructions:
            raise ValueError('All instructions cannot be empty')
        return cleaned_instructions

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if not v:
            return []
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    @validator('photo_url', 'source_url')
    def validate_urls(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class RecipeCreate(BaseModel):
    """Schema for creating new recipes"""
    title: str = Field(..., min_length=1, max_length=200, description="Recipe title")
    description: Optional[str] = Field(None, max_length=1000, description="Recipe description")
    ingredients: List[RecipeIngredient] = Field(..., min_items=1, description="List of recipe ingredients")
    instructions: List[str] = Field(..., min_items=1, description="List of cooking instructions")
    prep_time: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")
    servings: int = Field(..., gt=0, description="Number of servings")
    difficulty: DifficultyLevel = Field(..., description="Recipe difficulty level")
    tags: List[str] = Field(default=[], description="Recipe tags for categorization")
    meal_types: List[MealType] = Field(default=[], description="Meal types this recipe is suitable for")
    dietary_restrictions: List[DietaryRestriction] = Field(default=[], description="Dietary restrictions this recipe meets")
    nutrition_info: Optional[RecipeNutrition] = Field(None, description="Nutritional information")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to recipe photo")
    source_url: Optional[str] = Field(None, max_length=500, description="Original source URL if imported")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Recipe title cannot be empty')
        return v.strip()

    @validator('instructions')
    def validate_instructions(cls, v):
        """Ensure all instructions are non-empty"""
        if not v:
            raise ValueError('Recipe must have at least one instruction')
        cleaned_instructions = []
        for instruction in v:
            if isinstance(instruction, str) and instruction.strip():
                cleaned_instructions.append(instruction.strip())
        if not cleaned_instructions:
            raise ValueError('All instructions cannot be empty')
        return cleaned_instructions

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if not v:
            return []
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    @validator('photo_url', 'source_url')
    def validate_urls(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class RecipeUpdate(BaseModel):
    """Schema for updating existing recipes"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Recipe title")
    description: Optional[str] = Field(None, max_length=1000, description="Recipe description")
    ingredients: Optional[List[RecipeIngredient]] = Field(None, min_items=1, description="List of recipe ingredients")
    instructions: Optional[List[str]] = Field(None, min_items=1, description="List of cooking instructions")
    prep_time: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")
    servings: Optional[int] = Field(None, gt=0, description="Number of servings")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Recipe difficulty level")
    tags: Optional[List[str]] = Field(None, description="Recipe tags for categorization")
    meal_types: Optional[List[MealType]] = Field(None, description="Meal types this recipe is suitable for")
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(None, description="Dietary restrictions this recipe meets")
    nutrition_info: Optional[RecipeNutrition] = Field(None, description="Nutritional information")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to recipe photo")
    source_url: Optional[str] = Field(None, max_length=500, description="Original source URL if imported")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Recipe title cannot be empty')
        return v.strip() if v else v

    @validator('instructions')
    def validate_instructions(cls, v):
        """Ensure all instructions are non-empty"""
        if v is not None:
            if not v:
                raise ValueError('Recipe must have at least one instruction')
            cleaned_instructions = []
            for instruction in v:
                if isinstance(instruction, str) and instruction.strip():
                    cleaned_instructions.append(instruction.strip())
            if not cleaned_instructions:
                raise ValueError('All instructions cannot be empty')
            return cleaned_instructions
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if v is not None:
            if not v:
                return []
            cleaned_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    cleaned_tags.append(tag.strip().lower())
            return list(set(cleaned_tags))  # Remove duplicates
        return v

    @validator('photo_url', 'source_url')
    def validate_urls(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class RecipeResponse(BaseModel):
    """Schema for recipe response"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    ingredients: List[RecipeIngredient]
    instructions: List[str]
    prep_time: Optional[int]
    cook_time: Optional[int]
    total_time: Optional[int] = Field(None, description="Total time (prep + cook) in minutes")
    servings: int
    difficulty: DifficultyLevel
    tags: List[str]
    meal_types: List[MealType]
    dietary_restrictions: List[DietaryRestriction]
    nutrition_info: Optional[RecipeNutrition]
    photo_url: Optional[str]
    source_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @validator('total_time', pre=False, always=True)
    def calculate_total_time(cls, v, values):
        """Calculate total time from prep and cook times"""
        prep_time = values.get('prep_time', 0) or 0
        cook_time = values.get('cook_time', 0) or 0
        if prep_time > 0 or cook_time > 0:
            return prep_time + cook_time
        return None


class RecipesListResponse(BaseModel):
    """Schema for listing recipes with pagination"""
    recipes: List[RecipeResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class RecipeSearchResponse(BaseModel):
    """Schema for recipe search results"""
    recipes: List[RecipeResponse]
    total_count: int
    search_term: str
    filters_applied: Dict[str, Any]


class RecipeStatsResponse(BaseModel):
    """Schema for recipe statistics"""
    total_recipes: int
    recipes_by_difficulty: Dict[str, int]
    recipes_by_meal_type: Dict[str, int]
    average_prep_time: Optional[float]
    average_cook_time: Optional[float]
    most_used_tags: List[Dict[str, Any]]