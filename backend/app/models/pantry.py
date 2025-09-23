"""
Pydantic models for pantry management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from bson import ObjectId
from enum import Enum


class PantryCategory(str, Enum):
    """Enumeration for pantry item categories"""
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
    OTHER = "other"


class PantryUnit(str, Enum):
    """Enumeration for pantry item units"""
    PIECE = "piece"
    POUND = "lb"
    OUNCE = "oz"
    GRAM = "g"
    KILOGRAM = "kg"
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    LITER = "L"
    MILLILITER = "ml"
    GALLON = "gal"
    QUART = "qt"
    PINT = "pt"
    FLUID_OUNCE = "fl oz"
    PACKAGE = "package"
    CAN = "can"
    BOTTLE = "bottle"
    BAG = "bag"
    BOX = "box"
    CONTAINER = "container"


class PantryItem(BaseModel):
    """Main pantry item model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    category: PantryCategory = Field(..., description="Item category")
    quantity: float = Field(..., gt=0, description="Item quantity")
    unit: PantryUnit = Field(..., description="Unit of measurement")
    expiration_date: Optional[date] = Field(None, description="Item expiration date")
    purchase_date: Optional[date] = Field(None, description="Item purchase date")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about the item")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Item creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Item last update timestamp")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

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

    @validator('expiration_date')
    def validate_expiration_date(cls, v):
        """Ensure expiration date is not in the past (optional validation)"""
        # Allow past dates for items that might already be expired
        return v

    @validator('purchase_date')
    def validate_purchase_date(cls, v):
        """Ensure purchase date is not in the future"""
        if v and v > date.today():
            raise ValueError('Purchase date cannot be in the future')
        return v


class PantryItemCreate(BaseModel):
    """Schema for creating new pantry items"""
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    category: PantryCategory = Field(..., description="Item category")
    quantity: float = Field(..., gt=0, description="Item quantity")
    unit: PantryUnit = Field(..., description="Unit of measurement")
    expiration_date: Optional[date] = Field(None, description="Item expiration date")
    purchase_date: Optional[date] = Field(None, description="Item purchase date")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about the item")

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

    @validator('purchase_date')
    def validate_purchase_date(cls, v):
        """Ensure purchase date is not in the future"""
        if v and v > date.today():
            raise ValueError('Purchase date cannot be in the future')
        return v


class PantryItemUpdate(BaseModel):
    """Schema for updating existing pantry items"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Item name")
    category: Optional[PantryCategory] = Field(None, description="Item category")
    quantity: Optional[float] = Field(None, gt=0, description="Item quantity")
    unit: Optional[PantryUnit] = Field(None, description="Unit of measurement")
    expiration_date: Optional[date] = Field(None, description="Item expiration date")
    purchase_date: Optional[date] = Field(None, description="Item purchase date")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about the item")

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

    @validator('purchase_date')
    def validate_purchase_date(cls, v):
        """Ensure purchase date is not in the future"""
        if v and v > date.today():
            raise ValueError('Purchase date cannot be in the future')
        return v


class PantryItemResponse(BaseModel):
    """Schema for pantry item response"""
    id: str
    user_id: str
    name: str
    category: PantryCategory
    quantity: float
    unit: PantryUnit
    expiration_date: Optional[date]
    purchase_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    days_until_expiration: Optional[int] = Field(None, description="Days until expiration (calculated field)")

    model_config = {"from_attributes": True}

    @validator('days_until_expiration', pre=False, always=True)
    def calculate_days_until_expiration(cls, v, values):
        """Calculate days until expiration"""
        expiration_date = values.get('expiration_date')
        if expiration_date:
            today = date.today()
            delta = expiration_date - today
            return delta.days
        return None


class PantryItemsListResponse(BaseModel):
    """Schema for listing pantry items with pagination"""
    items: List[PantryItemResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ExpiringItemsResponse(BaseModel):
    """Schema for expiring items response"""
    expiring_soon: List[PantryItemResponse] = Field(..., description="Items expiring within specified days")
    expired: List[PantryItemResponse] = Field(..., description="Items that have already expired")
    days_threshold: int = Field(..., description="Days threshold used for 'expiring soon'")


class PantryStatsResponse(BaseModel):
    """Schema for pantry statistics"""
    total_items: int
    items_by_category: dict
    expiring_soon_count: int
    expired_count: int
    total_value_estimate: Optional[float] = Field(None, description="Estimated total value (if available)")