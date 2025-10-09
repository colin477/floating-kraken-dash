"""
Pydantic models for meal photo analysis
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.recipes import RecipeCreate, RecipeResponse


class FoodDetectionType(str, Enum):
    """Enumeration for food detection types"""
    LABEL = "label"
    OBJECT = "object"
    TEXT = "text"


class DetectedFood(BaseModel):
    """Model for individual detected food items"""
    name: str = Field(..., description="Name of the detected food item")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for detection (0-1)")
    detection_type: FoodDetectionType = Field(..., description="Type of detection used")
    category: str = Field(..., description="Food category")
    bounding_box: Optional[Dict[str, Any]] = Field(None, description="Bounding box coordinates if available")
    notes: Optional[str] = Field(None, description="Additional notes about the detection")

    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is within valid range"""
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class MealAnalysisRequest(BaseModel):
    """Request model for meal photo analysis"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(None, description="URL to image file")
    analysis_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Additional analysis options"
    )
    generate_recipe: bool = Field(default=True, description="Whether to generate a recipe from detected foods")
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="User preferences for recipe generation"
    )

    @validator('image_data', 'image_url')
    def validate_image_source(cls, v, values):
        """Ensure at least one image source is provided"""
        if not v and not values.get('image_data') and not values.get('image_url'):
            raise ValueError('Either image_data or image_url must be provided')
        return v


class MealAnalysisResponse(BaseModel):
    """Response model for meal photo analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    detected_foods: List[DetectedFood] = Field(..., description="List of detected food items")
    recipe: Optional[RecipeResponse] = Field(None, description="Generated recipe based on detected foods")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score for the analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the analysis was performed")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Ensure confidence score is within valid range"""
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v


class MealAnalysisStats(BaseModel):
    """Statistics for meal photo analysis"""
    total_analyses: int = Field(..., description="Total number of analyses performed")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    average_confidence: float = Field(..., description="Average confidence score")
    average_processing_time_ms: float = Field(..., description="Average processing time in milliseconds")
    most_detected_foods: List[Dict[str, Any]] = Field(..., description="Most commonly detected food items")
    generated_recipes_count: int = Field(..., description="Number of recipes generated from analyses")


class FoodClassificationResult(BaseModel):
    """Result of food classification"""
    food_name: str = Field(..., description="Classified food name")
    category: str = Field(..., description="Food category")
    subcategory: Optional[str] = Field(None, description="Food subcategory")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    nutritional_info: Optional[Dict[str, Any]] = Field(None, description="Basic nutritional information")
    common_preparations: List[str] = Field(default=[], description="Common ways this food is prepared")
    typical_ingredients: List[str] = Field(default=[], description="Typical ingredients used with this food")


class IngredientMapping(BaseModel):
    """Mapping between detected food and recipe ingredient"""
    detected_food: str = Field(..., description="Name of detected food item")
    recipe_ingredient: str = Field(..., description="Mapped recipe ingredient name")
    quantity: float = Field(..., gt=0, description="Estimated quantity")
    unit: str = Field(..., description="Unit of measurement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping confidence")
    mapping_reason: str = Field(..., description="Reason for this mapping")


class RecipeGenerationRequest(BaseModel):
    """Request for generating recipe from detected foods"""
    detected_foods: List[DetectedFood] = Field(..., min_items=1, description="List of detected food items")
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="User preferences for recipe generation"
    )
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions to consider")
    cuisine_style: Optional[str] = Field(None, description="Preferred cuisine style")
    difficulty_preference: Optional[str] = Field(None, description="Preferred difficulty level")
    serving_size: int = Field(default=4, gt=0, description="Desired number of servings")


class RecipeGenerationResponse(BaseModel):
    """Response for recipe generation"""
    recipe: RecipeCreate = Field(..., description="Generated recipe")
    ingredient_mappings: List[IngredientMapping] = Field(..., description="How detected foods were mapped to ingredients")
    generation_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in generated recipe")
    generation_notes: List[str] = Field(default=[], description="Notes about the recipe generation process")
    alternative_suggestions: List[str] = Field(default=[], description="Alternative recipe suggestions")


class MealPhotoUploadRequest(BaseModel):
    """Request model for meal photo upload"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the image")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    generate_recipe: bool = Field(default=True, description="Whether to generate recipe immediately")
    analysis_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Analysis options"
    )

    @validator('content_type')
    def validate_content_type(cls, v):
        """Ensure content type is a valid image type"""
        valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
        if v.lower() not in valid_types:
            raise ValueError(f'Content type must be one of: {", ".join(valid_types)}')
        return v

    @validator('file_size')
    def validate_file_size(cls, v):
        """Ensure file size is within limits"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f'File size must be less than {max_size} bytes')
        return v


class MealPhotoUploadResponse(BaseModel):
    """Response model for meal photo upload"""
    success: bool = Field(..., description="Whether upload was successful")
    photo_id: Optional[str] = Field(None, description="Unique identifier for the uploaded photo")
    photo_url: Optional[str] = Field(None, description="URL to access the uploaded photo")
    analysis_result: Optional[MealAnalysisResponse] = Field(None, description="Analysis result if requested")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the photo was uploaded")
    error_message: Optional[str] = Field(None, description="Error message if upload failed")


class BatchMealAnalysisRequest(BaseModel):
    """Request for analyzing multiple meal photos"""
    photo_urls: List[str] = Field(..., min_items=1, max_items=10, description="List of photo URLs to analyze")
    analysis_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Analysis options applied to all photos"
    )
    generate_recipes: bool = Field(default=True, description="Whether to generate recipes for all photos")


class BatchMealAnalysisResponse(BaseModel):
    """Response for batch meal analysis"""
    results: List[MealAnalysisResponse] = Field(..., description="Analysis results for each photo")
    total_photos: int = Field(..., description="Total number of photos processed")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    batch_processing_time_ms: float = Field(..., description="Total batch processing time")
    batch_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When batch processing started")