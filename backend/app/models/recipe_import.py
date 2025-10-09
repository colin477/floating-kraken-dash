"""
Pydantic models for recipe URL import functionality
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.recipes import RecipeResponse


class RecipeImportStatus(str, Enum):
    """Status of recipe import operation"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"
    UNSUPPORTED_SITE = "unsupported_site"
    DUPLICATE = "duplicate"


class RecipeUrlImportRequest(BaseModel):
    """Request model for importing recipe from URL"""
    url: str = Field(..., description="Recipe URL to import")
    override_duplicate: bool = Field(default=False, description="Whether to import even if recipe already exists")
    custom_tags: Optional[List[str]] = Field(default=[], description="Additional tags to add to imported recipe")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v or not v.strip():
            raise ValueError('URL is required')
        
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        
        return v
    
    @validator('custom_tags')
    def validate_custom_tags(cls, v):
        """Clean and validate custom tags"""
        if not v:
            return []
        
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        
        return list(set(cleaned_tags))  # Remove duplicates


class RecipeImportPreview(BaseModel):
    """Preview of recipe data before import"""
    title: str = Field(..., description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients_count: int = Field(..., description="Number of ingredients")
    instructions_count: int = Field(..., description="Number of instructions")
    prep_time: Optional[int] = Field(None, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, description="Cooking time in minutes")
    servings: int = Field(..., description="Number of servings")
    difficulty: str = Field(..., description="Recipe difficulty level")
    meal_types: List[str] = Field(default=[], description="Meal types")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    tags: List[str] = Field(default=[], description="Recipe tags")
    photo_url: Optional[str] = Field(None, description="Recipe photo URL")
    source_domain: str = Field(..., description="Source website domain")
    scraping_method: str = Field(..., description="Method used to extract recipe data")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in extracted data quality")


class RecipeImportResponse(BaseModel):
    """Response model for recipe import operation"""
    success: bool = Field(..., description="Whether import was successful")
    status: RecipeImportStatus = Field(..., description="Import operation status")
    recipe: Optional[RecipeResponse] = Field(None, description="Imported recipe if successful")
    preview: Optional[RecipeImportPreview] = Field(None, description="Recipe preview data")
    
    # Import metadata
    source_url: str = Field(..., description="Original recipe URL")
    import_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When import was completed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    # Quality metrics
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall data quality score")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Data completeness score")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if import failed")
    validation_issues: List[str] = Field(default=[], description="Recipe validation issues found")
    warnings: List[str] = Field(default=[], description="Import warnings")
    
    # Duplicate detection
    is_duplicate: bool = Field(default=False, description="Whether recipe is a duplicate")
    existing_recipe_id: Optional[str] = Field(None, description="ID of existing duplicate recipe")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Additional import metadata")


class RecipeUrlValidationRequest(BaseModel):
    """Request model for validating recipe URL before import"""
    url: str = Field(..., description="Recipe URL to validate")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v or not v.strip():
            raise ValueError('URL is required')
        
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        
        return v


class RecipeUrlValidationResponse(BaseModel):
    """Response model for recipe URL validation"""
    is_valid: bool = Field(..., description="Whether URL is valid for import")
    is_supported: bool = Field(..., description="Whether domain is supported")
    domain: str = Field(..., description="Extracted domain")
    is_accessible: bool = Field(..., description="Whether URL is accessible")
    
    # Validation details
    validation_issues: List[str] = Field(default=[], description="Validation issues found")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    
    # Preview information (if accessible)
    page_title: Optional[str] = Field(None, description="Page title if accessible")
    has_recipe_data: Optional[bool] = Field(None, description="Whether page appears to contain recipe data")
    estimated_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Estimated extraction confidence")
    
    # Metadata
    response_time_ms: float = Field(..., description="Validation response time")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")