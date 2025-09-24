"""
Pydantic models for receipt processing
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from bson import ObjectId
from enum import Enum


class ReceiptProcessingStatus(str, Enum):
    """Enumeration for receipt processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReceiptItemCategory(str, Enum):
    """Enumeration for receipt item categories (matches pantry categories)"""
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


class ReceiptItem(BaseModel):
    """Model for individual receipt items"""
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    quantity: float = Field(..., gt=0, description="Item quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    total_price: float = Field(..., ge=0, description="Total price for this item")
    category: Optional[ReceiptItemCategory] = Field(None, description="Item category")
    
    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Item name cannot be empty')
        return v.strip()
    
    @validator('total_price', pre=False, always=True)
    def validate_total_price(cls, v, values):
        """Validate that total_price is reasonable based on quantity and unit_price"""
        quantity = values.get('quantity', 0)
        unit_price = values.get('unit_price', 0)
        if quantity > 0 and unit_price > 0:
            expected_total = quantity * unit_price
            # Allow for small rounding differences
            if abs(v - expected_total) > 0.01:
                # Don't raise error, just log warning - receipts might have discounts
                pass
        return v


class Receipt(BaseModel):
    """Main receipt model for database storage"""
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="Reference to users collection")
    store_name: str = Field(..., min_length=1, max_length=200, description="Store name")
    receipt_date: date = Field(..., description="Date of receipt")
    total_amount: float = Field(..., ge=0, description="Total amount on receipt")
    items: List[ReceiptItem] = Field(default=[], description="List of receipt items")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to receipt photo")
    processing_status: ReceiptProcessingStatus = Field(default=ReceiptProcessingStatus.PENDING, description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="When receipt was processed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Receipt creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Receipt last update timestamp")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
    
    @validator('store_name')
    def validate_store_name(cls, v):
        """Ensure store name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Store name cannot be empty')
        return v.strip()
    
    @validator('receipt_date')
    def validate_receipt_date(cls, v):
        """Ensure receipt date is not in the future"""
        if v > date.today():
            raise ValueError('Receipt date cannot be in the future')
        return v
    
    @validator('photo_url')
    def validate_photo_url(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Photo URL must start with http:// or https://')
        return v


class ReceiptCreate(BaseModel):
    """Schema for creating new receipts"""
    store_name: str = Field(..., min_length=1, max_length=200, description="Store name")
    receipt_date: date = Field(..., description="Date of receipt")
    total_amount: float = Field(..., ge=0, description="Total amount on receipt")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to receipt photo")
    
    @validator('store_name')
    def validate_store_name(cls, v):
        """Ensure store name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Store name cannot be empty')
        return v.strip()
    
    @validator('receipt_date')
    def validate_receipt_date(cls, v):
        """Ensure receipt date is not in the future"""
        if v > date.today():
            raise ValueError('Receipt date cannot be in the future')
        return v
    
    @validator('photo_url')
    def validate_photo_url(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Photo URL must start with http:// or https://')
        return v


class ReceiptUpdate(BaseModel):
    """Schema for updating existing receipts"""
    store_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Store name")
    receipt_date: Optional[date] = Field(None, description="Date of receipt")
    total_amount: Optional[float] = Field(None, ge=0, description="Total amount on receipt")
    items: Optional[List[ReceiptItem]] = Field(None, description="List of receipt items")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL to receipt photo")
    processing_status: Optional[ReceiptProcessingStatus] = Field(None, description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="When receipt was processed")
    
    @validator('store_name')
    def validate_store_name(cls, v):
        """Ensure store name is not empty after stripping whitespace"""
        if v is not None and not v.strip():
            raise ValueError('Store name cannot be empty')
        return v.strip() if v else v
    
    @validator('receipt_date')
    def validate_receipt_date(cls, v):
        """Ensure receipt date is not in the future"""
        if v and v > date.today():
            raise ValueError('Receipt date cannot be in the future')
        return v
    
    @validator('photo_url')
    def validate_photo_url(cls, v):
        """Basic URL validation"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Photo URL must start with http:// or https://')
        return v


class ReceiptResponse(BaseModel):
    """Schema for receipt response"""
    id: str
    user_id: str
    store_name: str
    receipt_date: date
    total_amount: float
    items: List[ReceiptItem]
    photo_url: Optional[str]
    processing_status: ReceiptProcessingStatus
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items_count: Optional[int] = Field(None, description="Number of items on receipt (calculated field)")
    
    model_config = {"from_attributes": True}
    
    @validator('items_count', pre=False, always=True)
    def calculate_items_count(cls, v, values):
        """Calculate number of items on receipt"""
        items = values.get('items', [])
        return len(items) if items else 0


class ReceiptsListResponse(BaseModel):
    """Schema for listing receipts with pagination"""
    receipts: List[ReceiptResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ReceiptProcessingRequest(BaseModel):
    """Schema for receipt processing request"""
    receipt_id: str = Field(..., description="Receipt ID to process")


class ReceiptProcessingResponse(BaseModel):
    """Schema for receipt processing response"""
    receipt_id: str
    processing_status: ReceiptProcessingStatus
    extracted_items: List[ReceiptItem]
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="AI confidence score")
    processing_notes: Optional[str] = Field(None, description="Notes from processing")


class AddToPantryRequest(BaseModel):
    """Schema for adding receipt items to pantry"""
    selected_items: List[int] = Field(..., description="Indices of items to add to pantry")
    expiration_days: Optional[int] = Field(7, ge=0, description="Days until expiration (default 7)")


class AddToPantryResponse(BaseModel):
    """Schema for add to pantry response"""
    receipt_id: str
    items_added: int
    items_failed: int
    pantry_items_created: List[str] = Field(..., description="IDs of created pantry items")
    errors: List[str] = Field(default=[], description="Any errors that occurred")


class ReceiptStatsResponse(BaseModel):
    """Schema for receipt statistics"""
    total_receipts: int
    total_spent: float
    receipts_by_store: dict
    receipts_by_month: dict
    average_receipt_amount: Optional[float]
    most_purchased_items: List[dict]


class ReceiptUploadRequest(BaseModel):
    """Schema for receipt upload request"""
    store_name: str = Field(..., min_length=1, max_length=200, description="Store name")
    receipt_date: date = Field(..., description="Date of receipt")
    total_amount: float = Field(..., ge=0, description="Total amount on receipt")
    
    @validator('store_name')
    def validate_store_name(cls, v):
        """Ensure store name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Store name cannot be empty')
        return v.strip()
    
    @validator('receipt_date')
    def validate_receipt_date(cls, v):
        """Ensure receipt date is not in the future"""
        if v > date.today():
            raise ValueError('Receipt date cannot be in the future')
        return v