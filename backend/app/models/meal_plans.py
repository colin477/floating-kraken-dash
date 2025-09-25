"""
Pydantic models for meal planning
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from enum import Enum


class MealType(str, Enum):
    """Enumeration for meal types"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DayOfWeek(str, Enum):
    """Enumeration for days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class MealPlanStatus(str, Enum):
    """Enumeration for meal plan status"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PlannedMeal(BaseModel):
    """Model for individual planned meals"""
    id: str = Field(..., description="Unique identifier for the planned meal")
    day: DayOfWeek = Field(..., description="Day of the week")
    meal_type: MealType = Field(..., description="Type of meal")
    recipe_id: Optional[str] = Field(None, description="Reference to recipe if using existing recipe")
    recipe_title: str = Field(..., description="Title of the recipe/meal")
    servings: int = Field(..., gt=0, description="Number of servings planned")
    estimated_prep_time: Optional[int] = Field(None, ge=0, description="Estimated prep time in minutes")
    estimated_cook_time: Optional[int] = Field(None, ge=0, description="Estimated cook time in minutes")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes for this meal")
    ingredients_needed: List[Dict[str, Any]] = Field(default=[], description="Ingredients needed for this meal")

    @validator('servings')
    def validate_servings(cls, v):
        """Ensure servings is positive"""
        if v <= 0:
            raise ValueError('Servings must be positive')
        return v


class ShoppingListItem(BaseModel):
    """Model for shopping list items"""
    id: str = Field(..., description="Unique identifier for the shopping list item")
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    quantity: float = Field(..., gt=0, description="Quantity needed")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement")
    category: str = Field(..., description="Item category for organization")
    estimated_price: Optional[float] = Field(None, ge=0, description="Estimated price")
    store: Optional[str] = Field(None, max_length=100, description="Preferred store for this item")
    purchased: bool = Field(default=False, description="Whether item has been purchased")
    meal_ids: List[str] = Field(default=[], description="IDs of meals that need this ingredient")
    notes: Optional[str] = Field(None, max_length=200, description="Additional notes")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Item name cannot be empty')
        return v.strip()

    @validator('quantity')
    def validate_quantity(cls, v):
        """Ensure quantity is positive"""
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class MealPlan(BaseModel):
    """Main meal plan model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    title: str = Field(..., min_length=1, max_length=200, description="Meal plan title")
    description: Optional[str] = Field(None, max_length=1000, description="Meal plan description")
    week_starting: date = Field(..., description="Start date of the week this plan covers")
    status: MealPlanStatus = Field(default=MealPlanStatus.DRAFT, description="Current status of the meal plan")
    meals: List[PlannedMeal] = Field(default=[], description="List of planned meals")
    shopping_list: List[ShoppingListItem] = Field(default=[], description="Generated shopping list")
    total_estimated_cost: float = Field(default=0.0, ge=0, description="Total estimated cost")
    budget_target: Optional[float] = Field(None, gt=0, description="Target budget for this meal plan")
    preferences_used: Dict[str, Any] = Field(default={}, description="User preferences used in generation")
    generation_notes: Optional[str] = Field(None, description="Notes from AI generation process")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Meal plan creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Meal plan last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Meal plan title cannot be empty')
        return v.strip()

    @validator('week_starting')
    def validate_week_starting(cls, v):
        """Ensure week starting date is not too far in the past or future"""
        today = date.today()
        # Allow plans up to 12 weeks in the past or 24 weeks in the future (more permissive for testing)
        if v < today - timedelta(days=84) or v > today + timedelta(days=168):
            raise ValueError('Week starting date must be within reasonable range')
        return v


class MealPlanCreate(BaseModel):
    """Schema for creating new meal plans"""
    title: str = Field(..., min_length=1, max_length=200, description="Meal plan title")
    description: Optional[str] = Field(None, max_length=1000, description="Meal plan description")
    week_starting: date = Field(..., description="Start date of the week this plan covers")
    budget_target: Optional[float] = Field(None, gt=0, description="Target budget for this meal plan")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Specific preferences for this plan")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Meal plan title cannot be empty')
        return v.strip()

    @validator('week_starting')
    def validate_week_starting(cls, v):
        """Ensure week starting date is not too far in the past or future"""
        today = date.today()
        # Allow plans up to 12 weeks in the past or 24 weeks in the future (more permissive for testing)
        if v < today - timedelta(days=84) or v > today + timedelta(days=168):
            raise ValueError('Week starting date must be within reasonable range')
        return v


class MealPlanUpdate(BaseModel):
    """Schema for updating existing meal plans"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Meal plan title")
    description: Optional[str] = Field(None, max_length=1000, description="Meal plan description")
    status: Optional[MealPlanStatus] = Field(None, description="Current status of the meal plan")
    meals: Optional[List[PlannedMeal]] = Field(None, description="List of planned meals")
    shopping_list: Optional[List[ShoppingListItem]] = Field(None, description="Generated shopping list")
    total_estimated_cost: Optional[float] = Field(None, ge=0, description="Total estimated cost")
    budget_target: Optional[float] = Field(None, gt=0, description="Target budget for this meal plan")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Meal plan title cannot be empty')
        return v.strip() if v else v


class MealPlanResponse(BaseModel):
    """Schema for meal plan response"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    week_starting: date
    status: MealPlanStatus
    meals: List[PlannedMeal]
    shopping_list: List[ShoppingListItem]
    total_estimated_cost: float
    budget_target: Optional[float]
    preferences_used: Dict[str, Any]
    generation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    meals_count: Optional[int] = Field(None, description="Total number of planned meals")
    shopping_items_count: Optional[int] = Field(None, description="Total number of shopping list items")
    days_covered: Optional[List[str]] = Field(None, description="Days of the week covered by this plan")

    model_config = {"from_attributes": True}

    @validator('meals_count', pre=False, always=True)
    def calculate_meals_count(cls, v, values):
        """Calculate total number of planned meals"""
        if v is not None:
            return v
        meals = values.get('meals', [])
        return len(meals) if meals else 0

    @validator('shopping_items_count', pre=False, always=True)
    def calculate_shopping_items_count(cls, v, values):
        """Calculate total number of shopping list items"""
        if v is not None:
            return v
        shopping_list = values.get('shopping_list', [])
        return len(shopping_list) if shopping_list else 0

    @validator('days_covered', pre=False, always=True)
    def calculate_days_covered(cls, v, values):
        """Calculate which days are covered by planned meals"""
        if v is not None:
            return v
        meals = values.get('meals', [])
        if meals:
            try:
                days = list(set(meal.day if hasattr(meal, 'day') else meal.get('day') for meal in meals))
                return sorted([day for day in days if day])
            except:
                return []
        return []


class MealPlansListResponse(BaseModel):
    """Schema for listing meal plans with pagination"""
    meal_plans: List[MealPlanResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class MealPlanGenerationRequest(BaseModel):
    """Schema for AI meal plan generation request"""
    week_starting: date = Field(..., description="Start date of the week")
    budget_target: Optional[float] = Field(None, gt=0, description="Target budget")
    meal_types: List[MealType] = Field(default=[MealType.DINNER], description="Types of meals to plan")
    days: List[DayOfWeek] = Field(default=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
                                          DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY, 
                                          DayOfWeek.SUNDAY], description="Days to plan meals for")
    servings_per_meal: int = Field(default=4, gt=0, description="Default servings per meal")
    use_pantry_items: bool = Field(default=True, description="Whether to prioritize pantry items")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions to consider")
    cuisine_preferences: List[str] = Field(default=[], description="Preferred cuisines")
    avoid_ingredients: List[str] = Field(default=[], description="Ingredients to avoid")
    max_prep_time: Optional[int] = Field(None, gt=0, description="Maximum prep time per meal in minutes")
    difficulty_preference: Optional[str] = Field(None, description="Preferred difficulty level")

    @validator('week_starting')
    def validate_week_starting(cls, v):
        """Ensure week starting date is reasonable"""
        today = date.today()
        # Allow plans up to 12 weeks in the past or 24 weeks in the future (more permissive for testing)
        if v < today - timedelta(days=84) or v > today + timedelta(days=168):
            raise ValueError('Week starting date must be within reasonable range')
        return v


class MealPlanGenerationResponse(BaseModel):
    """Schema for AI meal plan generation response"""
    meal_plan_id: str
    title: str
    meals_generated: int
    shopping_items_generated: int
    total_estimated_cost: float
    generation_notes: str
    success: bool
    warnings: List[str] = Field(default=[], description="Any warnings during generation")


class MealPlanStatsResponse(BaseModel):
    """Schema for meal plan statistics"""
    total_meal_plans: int
    active_meal_plans: int
    completed_meal_plans: int
    average_weekly_cost: Optional[float]
    most_planned_meal_type: Optional[str]
    most_planned_day: Optional[str]
    total_meals_planned: int
    budget_adherence_rate: Optional[float] = Field(None, description="Percentage of plans within budget")