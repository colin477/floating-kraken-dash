"""
Pydantic models for shopping list management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from enum import Enum


class ShoppingListStatus(str, Enum):
    """Enumeration for shopping list status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ShoppingListCategory(str, Enum):
    """Enumeration for shopping list categories"""
    PRODUCE = "produce"
    DAIRY = "dairy"
    MEAT = "meat"
    SEAFOOD = "seafood"
    GRAINS = "grains"
    CANNED_GOODS = "canned_goods"
    FROZEN = "frozen"
    BEVERAGES = "beverages"
    SNACKS = "snacks"
    CONDIMENTS = "condiments"
    SPICES = "spices"
    BAKING = "baking"
    HOUSEHOLD = "household"
    PERSONAL_CARE = "personal_care"
    OTHER = "other"


class ShoppingListItemStatus(str, Enum):
    """Enumeration for individual item status"""
    PENDING = "pending"
    PURCHASED = "purchased"
    UNAVAILABLE = "unavailable"
    SUBSTITUTED = "substituted"


class ShoppingItem(BaseModel):
    """Model for individual shopping list items"""
    id: str = Field(..., description="Unique identifier for the shopping item")
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    quantity: float = Field(..., gt=0, description="Quantity needed")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement")
    category: ShoppingListCategory = Field(..., description="Item category for organization")
    estimated_price: Optional[float] = Field(None, ge=0, description="Estimated price per unit")
    actual_price: Optional[float] = Field(None, ge=0, description="Actual price paid")
    store: Optional[str] = Field(None, max_length=100, description="Preferred store for this item")
    status: ShoppingListItemStatus = Field(default=ShoppingListItemStatus.PENDING, description="Item status")
    notes: Optional[str] = Field(None, max_length=200, description="Additional notes")
    meal_plan_id: Optional[str] = Field(None, description="Reference to meal plan if generated from one")
    recipe_ids: List[str] = Field(default=[], description="Recipe IDs that need this ingredient")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level (1=low, 5=high)")
    substitution_notes: Optional[str] = Field(None, max_length=200, description="Notes about substitutions")
    purchased_at: Optional[datetime] = Field(None, description="When item was purchased")

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

    @validator('unit')
    def validate_unit(cls, v):
        """Ensure unit is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Unit cannot be empty')
        return v.strip()


class ShoppingList(BaseModel):
    """Main shopping list model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    title: str = Field(..., min_length=1, max_length=200, description="Shopping list title")
    description: Optional[str] = Field(None, max_length=1000, description="Shopping list description")
    status: ShoppingListStatus = Field(default=ShoppingListStatus.ACTIVE, description="List status")
    items: List[ShoppingItem] = Field(default=[], description="List of shopping items")
    stores: List[str] = Field(default=[], description="Stores to visit for this list")
    total_estimated_cost: float = Field(default=0.0, ge=0, description="Total estimated cost")
    total_actual_cost: float = Field(default=0.0, ge=0, description="Total actual cost spent")
    budget_limit: Optional[float] = Field(None, gt=0, description="Budget limit for this list")
    meal_plan_id: Optional[str] = Field(None, description="Reference to meal plan if generated from one")
    shopping_date: Optional[date] = Field(None, description="Planned shopping date")
    completed_at: Optional[datetime] = Field(None, description="When shopping was completed")
    tags: List[str] = Field(default=[], description="Tags for organization")
    shared_with: List[str] = Field(default=[], description="User IDs this list is shared with")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="List creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="List last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Shopping list title cannot be empty')
        return v.strip()

    @validator('shopping_date')
    def validate_shopping_date(cls, v):
        """Ensure shopping date is not too far in the past"""
        if v and v < date.today() - timedelta(days=30):
            raise ValueError('Shopping date cannot be more than 30 days in the past')
        return v

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


class ShoppingListCreate(BaseModel):
    """Schema for creating new shopping lists"""
    title: str = Field(..., min_length=1, max_length=200, description="Shopping list title")
    description: Optional[str] = Field(None, max_length=1000, description="Shopping list description")
    items: List[ShoppingItem] = Field(default=[], description="Initial list of shopping items")
    stores: List[str] = Field(default=[], description="Stores to visit for this list")
    budget_limit: Optional[float] = Field(None, gt=0, description="Budget limit for this list")
    shopping_date: Optional[date] = Field(None, description="Planned shopping date")
    tags: List[str] = Field(default=[], description="Tags for organization")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Shopping list title cannot be empty')
        return v.strip()

    @validator('shopping_date')
    def validate_shopping_date(cls, v):
        """Ensure shopping date is not too far in the past"""
        if v and v < date.today() - timedelta(days=30):
            raise ValueError('Shopping date cannot be more than 30 days in the past')
        return v

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


class ShoppingListUpdate(BaseModel):
    """Schema for updating existing shopping lists"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Shopping list title")
    description: Optional[str] = Field(None, max_length=1000, description="Shopping list description")
    status: Optional[ShoppingListStatus] = Field(None, description="List status")
    items: Optional[List[ShoppingItem]] = Field(None, description="List of shopping items")
    stores: Optional[List[str]] = Field(None, description="Stores to visit for this list")
    budget_limit: Optional[float] = Field(None, gt=0, description="Budget limit for this list")
    shopping_date: Optional[date] = Field(None, description="Planned shopping date")
    tags: Optional[List[str]] = Field(None, description="Tags for organization")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Shopping list title cannot be empty')
        return v.strip() if v else v

    @validator('shopping_date')
    def validate_shopping_date(cls, v):
        """Ensure shopping date is not too far in the past"""
        if v and v < date.today() - timedelta(days=30):
            raise ValueError('Shopping date cannot be more than 30 days in the past')
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


class ShoppingListResponse(BaseModel):
    """Schema for shopping list response"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    status: ShoppingListStatus
    items: List[ShoppingItem]
    stores: List[str]
    total_estimated_cost: float
    total_actual_cost: float
    budget_limit: Optional[float]
    meal_plan_id: Optional[str]
    shopping_date: Optional[date]
    completed_at: Optional[datetime]
    tags: List[str]
    shared_with: List[str]
    created_at: datetime
    updated_at: datetime
    items_count: Optional[int] = Field(None, description="Total number of items")
    purchased_items_count: Optional[int] = Field(None, description="Number of purchased items")
    completion_percentage: Optional[float] = Field(None, description="Percentage of items purchased")
    budget_used_percentage: Optional[float] = Field(None, description="Percentage of budget used")

    model_config = {"from_attributes": True}

    @validator('items_count', pre=False, always=True)
    def calculate_items_count(cls, v, values):
        """Calculate total number of items"""
        items = values.get('items', [])
        return len(items) if items else 0

    @validator('purchased_items_count', pre=False, always=True)
    def calculate_purchased_items_count(cls, v, values):
        """Calculate number of purchased items"""
        items = values.get('items', [])
        if items:
            return len([item for item in items if item.status == ShoppingListItemStatus.PURCHASED])
        return 0

    @validator('completion_percentage', pre=False, always=True)
    def calculate_completion_percentage(cls, v, values):
        """Calculate completion percentage"""
        items = values.get('items', [])
        if items:
            purchased = len([item for item in items if item.status == ShoppingListItemStatus.PURCHASED])
            return round((purchased / len(items)) * 100, 1)
        return 0.0

    @validator('budget_used_percentage', pre=False, always=True)
    def calculate_budget_used_percentage(cls, v, values):
        """Calculate budget used percentage"""
        budget_limit = values.get('budget_limit')
        total_actual_cost = values.get('total_actual_cost', 0)
        if budget_limit and budget_limit > 0:
            return round((total_actual_cost / budget_limit) * 100, 1)
        return None


class ShoppingListsListResponse(BaseModel):
    """Schema for listing shopping lists with pagination"""
    shopping_lists: List[ShoppingListResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ShoppingItemUpdate(BaseModel):
    """Schema for updating individual shopping items"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Item name")
    quantity: Optional[float] = Field(None, gt=0, description="Quantity needed")
    unit: Optional[str] = Field(None, min_length=1, max_length=50, description="Unit of measurement")
    category: Optional[ShoppingListCategory] = Field(None, description="Item category")
    estimated_price: Optional[float] = Field(None, ge=0, description="Estimated price per unit")
    actual_price: Optional[float] = Field(None, ge=0, description="Actual price paid")
    store: Optional[str] = Field(None, max_length=100, description="Preferred store")
    status: Optional[ShoppingListItemStatus] = Field(None, description="Item status")
    notes: Optional[str] = Field(None, max_length=200, description="Additional notes")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level")
    substitution_notes: Optional[str] = Field(None, max_length=200, description="Substitution notes")

    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Item name cannot be empty')
        return v.strip() if v else v

    @validator('quantity')
    def validate_quantity(cls, v):
        """Ensure quantity is positive"""
        if v is not None and v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @validator('unit')
    def validate_unit(cls, v):
        """Ensure unit is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Unit cannot be empty')
        return v.strip() if v else v


class ShoppingListStatsResponse(BaseModel):
    """Schema for shopping list statistics"""
    total_lists: int
    active_lists: int
    completed_lists: int
    total_items: int
    total_spent: float
    average_list_cost: Optional[float]
    most_shopped_store: Optional[str]
    most_purchased_category: Optional[str]
    budget_adherence_rate: Optional[float] = Field(None, description="Percentage of lists within budget")
    completion_rate: Optional[float] = Field(None, description="Average completion rate of lists")


class BulkItemUpdateRequest(BaseModel):
    """Schema for bulk updating shopping list items"""
    item_ids: List[str] = Field(..., description="List of item IDs to update")
    updates: ShoppingItemUpdate = Field(..., description="Updates to apply to all items")


class BulkItemUpdateResponse(BaseModel):
    """Schema for bulk update response"""
    updated_count: int
    failed_count: int
    errors: List[str] = Field(default=[], description="Any errors that occurred")