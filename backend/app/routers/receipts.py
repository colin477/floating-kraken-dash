"""
Receipt processing router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import Optional, List
from datetime import date
from app.models.responses import SuccessResponse
from app.utils.cloud_storage import cloud_storage_service
from app.utils.category_mapper import category_mapper
from app.models.receipts import (
    ReceiptCreate,
    ReceiptUpdate,
    ReceiptResponse,
    ReceiptsListResponse,
    ReceiptProcessingResponse,
    AddToPantryRequest,
    AddToPantryResponse,
    ReceiptStatsResponse,
    ReceiptUploadRequest,
    ReceiptProcessingStatus
)
from app.crud.receipts import (
    create_receipt,
    get_receipts,
    get_receipt_by_id,
    update_receipt,
    delete_receipt,
    process_receipt_image,
    add_receipt_items_to_pantry,
    get_receipt_stats,
    create_receipt_indexes
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Create database indexes on startup"""
    await create_receipt_indexes()


@router.post("/upload", response_model=ReceiptProcessingResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a receipt image file and process it with enhanced validation"""
    from app.utils.file_validator import validate_image_file, sanitize_filename
    from app.utils.storage_metrics import storage_metrics, storage_operation_timer
    import time
    
    user_id = str(current_user["_id"])
    original_filename = file.filename or "receipt.jpg"
    
    # Read file content once
    file_content = await file.read()
    file_size = len(file_content)
    
    # Record upload attempt
    storage_metrics.record_upload_attempt(user_id, original_filename, file_size)
    
    try:
        # Enhanced file validation
        is_valid, validation_message, validation_details = validate_image_file(
            file_content, original_filename
        )
        
        if not is_valid:
            storage_metrics.record_validation_failure(
                user_id, original_filename, file_size, validation_message
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {validation_message}"
            )
        
        # Sanitize filename for safe storage
        safe_filename = sanitize_filename(original_filename)
        
        # Upload file to cloud storage or local fallback with timing
        upload_start_time = time.time()
        
        async with storage_operation_timer():
            file_url = await cloud_storage_service.upload_file(
                file_content=file_content,
                filename=safe_filename,
                content_type=file.content_type or "image/jpeg",
                user_id=user_id
            )
        
        upload_duration = time.time() - upload_start_time
        
        if not file_url:
            storage_metrics.record_upload_failure(
                user_id, safe_filename, file_size, "storage_service_error",
                "Failed to upload file to storage"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Record successful upload
        storage_type = cloud_storage_service.get_storage_type(file_url)
        storage_metrics.record_upload_success(
            user_id, safe_filename, file_size, storage_type, upload_duration
        )
        
        # Create receipt record with file URL
        from datetime import date
        create_data = ReceiptCreate(
            store_name="Unknown Store",  # Will be extracted from OCR
            receipt_date=date.today(),  # Use today's date as default, will be updated from OCR
            total_amount=0.0,  # Will be extracted from OCR
            photo_url=file_url
        )
        
        receipt = await create_receipt(user_id=user_id, receipt_data=create_data)
        
        if receipt is None:
            # Clean up uploaded file if receipt creation failed
            await cloud_storage_service.delete_file(file_url)
            storage_metrics.record_upload_failure(
                user_id, safe_filename, file_size, "database_error",
                "Failed to create receipt record"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create receipt"
            )
        
        # Process the receipt immediately
        result = await process_receipt_image(user_id=user_id, receipt_id=receipt.id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process receipt image"
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Clean up uploaded file on error
        if 'file_url' in locals():
            await cloud_storage_service.delete_file(file_url)
        
        # Record the failure
        storage_metrics.record_upload_failure(
            user_id, original_filename, file_size, "unexpected_error", str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )


@router.get("/", response_model=ReceiptsListResponse)
async def get_user_receipts(
    store_name: Optional[str] = Query(None, description="Filter by store name"),
    start_date: Optional[date] = Query(None, description="Filter receipts from this date"),
    end_date: Optional[date] = Query(None, description="Filter receipts until this date"),
    processing_status: Optional[ReceiptProcessingStatus] = Query(None, description="Filter by processing status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Receipts per page"),
    sort_by: str = Query("receipt_date", description="Sort field (receipt_date, created_at, total_amount, etc.)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all receipts for the authenticated user"""
    user_id = str(current_user["_id"])
    
    result = await get_receipts(
        user_id=user_id,
        store_name=store_name,
        start_date=start_date,
        end_date=end_date,
        processing_status=processing_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipts"
        )
    
    return result


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get specific receipt by ID"""
    user_id = str(current_user["_id"])
    
    result = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return result


@router.put("/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt_endpoint(
    receipt_id: str,
    update_data: ReceiptUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update receipt by ID"""
    user_id = str(current_user["_id"])
    
    result = await update_receipt(user_id=user_id, receipt_id=receipt_id, update_data=update_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found or no changes made"
        )
    
    return result


@router.delete("/{receipt_id}")
async def delete_receipt_endpoint(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete receipt by ID"""
    user_id = str(current_user["_id"])
    
    success = await delete_receipt(user_id=user_id, receipt_id=receipt_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return SuccessResponse(message="Receipt deleted successfully")


@router.post("/{receipt_id}/process", response_model=ReceiptProcessingResponse)
async def process_receipt(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Process receipt image to extract items using AI"""
    user_id = str(current_user["_id"])
    
    # First check if receipt exists
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Check if already processed
    if receipt.processing_status == ReceiptProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt has already been processed"
        )
    
    # Check if currently processing
    if receipt.processing_status == ReceiptProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt is currently being processed"
        )
    
    result = await process_receipt_image(user_id=user_id, receipt_id=receipt_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process receipt"
        )
    
    return result


@router.post("/{receipt_id}/add-to-pantry", response_model=AddToPantryResponse)
async def add_receipt_items_to_pantry_endpoint(
    receipt_id: str,
    request_data: AddToPantryRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Add selected receipt items to user's pantry"""
    import logging
    logger = logging.getLogger(__name__)
    
    user_id = str(current_user["_id"])
    
    try:
        logger.info(f"Adding receipt items to pantry for user {user_id}, receipt {receipt_id}")
        logger.info(f"Request data: {request_data.dict()}")
        
        # First check if receipt exists and is processed
        receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
        if receipt is None:
            logger.error(f"Receipt {receipt_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found"
            )
        
        logger.info(f"Receipt found: {receipt.store_name}, status: {receipt.processing_status}, items: {len(receipt.items)}")
        
        if receipt.processing_status != ReceiptProcessingStatus.COMPLETED:
            logger.error(f"Receipt {receipt_id} not processed (status: {receipt.processing_status})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt must be processed before adding items to pantry"
            )
        
        if not receipt.items:
            logger.error(f"Receipt {receipt_id} has no items")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt has no items to add to pantry"
            )
        
        # Validate selected item indices
        max_index = len(receipt.items) - 1
        invalid_indices = [idx for idx in request_data.selected_items if idx < 0 or idx > max_index]
        if invalid_indices:
            logger.error(f"Invalid item indices {invalid_indices} for receipt {receipt_id} with {len(receipt.items)} items")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid item indices: {invalid_indices}. Receipt has {len(receipt.items)} items (indices 0-{max_index})"
            )
        
        logger.info(f"Adding {len(request_data.selected_items)} items to pantry: indices {request_data.selected_items}")
        
        result = await add_receipt_items_to_pantry(
            user_id=user_id,
            receipt_id=receipt_id,
            selected_items=request_data.selected_items,
            expiration_days=request_data.expiration_days or 7
        )
        
        if result is None:
            logger.error(f"Failed to add receipt items to pantry for user {user_id}, receipt {receipt_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add items to pantry"
            )
        
        logger.info(f"Successfully added {result.items_added} items to pantry, {result.items_failed} failed")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error adding receipt items to pantry: {str(e)}", exc_info=True)
        logger.error(f"User: {user_id}, Receipt: {receipt_id}, Request: {request_data.dict()}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/stats/overview", response_model=ReceiptStatsResponse)
async def get_receipt_statistics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get receipt statistics overview"""
    user_id = str(current_user["_id"])
    
    result = await get_receipt_stats(user_id=user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipt statistics"
        )
    
    return result


# Legacy endpoints for backward compatibility (these were in the original placeholder)
@router.post("/process")
async def process_receipt_legacy():
    """Legacy endpoint - redirects to new pattern"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been moved. Use POST /receipts/{receipt_id}/process instead"
    )


@router.post("/confirm")
async def confirm_receipt_items_legacy():
    """Legacy endpoint - redirects to new pattern"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been moved. Use POST /receipts/{receipt_id}/add-to-pantry instead"
    )


# File upload endpoint for receipt images (future enhancement)
@router.post("/{receipt_id}/upload-image")
async def upload_receipt_image(
    receipt_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload receipt image file (placeholder for future implementation)"""
    user_id = str(current_user["_id"])
    
    # Check if receipt exists
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # For now, just return success - in the future, this would:
    # 1. Save the file to cloud storage (S3, etc.)
    # 2. Update the receipt with the photo_url
    # 3. Optionally trigger automatic processing
    
    return SuccessResponse(
        message=f"Receipt image upload placeholder - file {file.filename} would be processed"
    )


@router.get("/{receipt_id}/image-url")
async def get_receipt_image_url(
    receipt_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get secure URL for receipt image access"""
    user_id = str(current_user["_id"])
    
    # Check if receipt exists and belongs to user
    receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if not receipt.photo_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt has no image"
        )
    
    # Generate secure URL (presigned for S3, or return local path)
    secure_url = await cloud_storage_service.generate_presigned_url(
        receipt.photo_url,
        expiration=3600  # 1 hour
    )
    
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure image URL"
        )
    
    return {
        "receipt_id": receipt_id,
        "image_url": secure_url,
        "expires_in": 3600,
        "storage_type": cloud_storage_service.get_storage_type(receipt.photo_url)
    }


@router.get("/{receipt_id}/suggest-recipes")
async def get_receipt_recipe_suggestions(
    receipt_id: str,
    max_suggestions: int = Query(10, ge=1, le=20, description="Maximum number of suggestions (1-20)"),
    min_match_percentage: float = Query(0.3, ge=0.1, le=1.0, description="Minimum ingredient match percentage (0.1-1.0)"),
    max_prep_time: Optional[int] = Query(None, ge=0, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=0, description="Maximum cook time in minutes"),
    difficulty_level: Optional[str] = Query(None, regex="^(easy|medium|hard)$", description="Filter by difficulty (easy, medium, hard)"),
    meal_type: Optional[str] = Query(None, regex="^(breakfast|lunch|dinner|snack)$", description="Filter by meal type (breakfast, lunch, dinner, snack)"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get recipe suggestions based on receipt items
    
    This endpoint takes a processed receipt and generates recipe suggestions
    based on the items found in that receipt, using the same algorithm as
    the leftover suggestions but with receipt items instead of pantry items.
    
    **Requirements:**
    - Receipt must exist and belong to the authenticated user
    - Receipt must be processed (status = completed)
    - Receipt must have items extracted
    
    **Query Parameters:**
    - **max_suggestions**: Maximum number of suggestions to return (1-20)
    - **min_match_percentage**: Minimum percentage of ingredients you must have (0.1-1.0)
    - **max_prep_time**: Maximum preparation time in minutes
    - **max_cook_time**: Maximum cooking time in minutes
    - **difficulty_level**: Filter by recipe difficulty (easy, medium, hard)
    - **meal_type**: Filter by meal type (breakfast, lunch, dinner, snack)
    
    **Example Usage:**
    ```
    GET /api/v1/receipts/507f1f77bcf86cd799439011/suggest-recipes?max_suggestions=5&difficulty_level=easy
    ```
    
    **Response:** Same format as leftover suggestions but based on receipt items
    """
    try:
        from app.models.leftovers import SuggestionFilters, PantryIngredientInfo
        from app.crud.leftovers import get_leftover_suggestions
        from app.database import get_database
        
        user_id = str(current_user["_id"])
        
        # First check if receipt exists and belongs to user
        receipt = await get_receipt_by_id(user_id=user_id, receipt_id=receipt_id)
        if receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found"
            )
        
        # Check if receipt is processed
        if receipt.processing_status != ReceiptProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt must be processed before generating recipe suggestions"
            )
        
        # Check if receipt has items
        if not receipt.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt has no items to generate suggestions from"
            )
        
        # Convert receipt items to PantryIngredientInfo format for the suggestions algorithm
        from datetime import date, timedelta
        
        # Create mock pantry ingredients from receipt items
        mock_pantry_ingredients = []
        for item in receipt.items:
            # Create a mock pantry ingredient with good freshness (since it was just purchased)
            mock_ingredient = PantryIngredientInfo(
                name=item.name,
                normalized_name=item.name.lower().strip(),
                category=item.category.value if item.category else "other",
                quantity=item.quantity,
                unit="piece",  # Default unit
                expiration_date=date.today() + timedelta(days=7),  # Assume 7 days freshness
                days_until_expiration=7,
                is_expired=False,
                is_expiring_soon=False,
                freshness_score=1.0  # Fresh items from receipt
            )
            mock_pantry_ingredients.append(mock_ingredient)
        
        # Create suggestion filters
        filters = SuggestionFilters(
            max_suggestions=max_suggestions,
            min_match_percentage=min_match_percentage,
            max_prep_time=max_prep_time,
            max_cook_time=max_cook_time,
            difficulty_levels=[difficulty_level] if difficulty_level else None,
            meal_types=[meal_type] if meal_type else None,
            exclude_expired=False,  # Receipt items are fresh
            prioritize_expiring=False,  # Receipt items are fresh
            include_substitutes=True
        )
        
        # Get database connection
        db = await get_database()
        
        # Use a modified version of the leftover suggestions algorithm
        # We'll temporarily replace the user's pantry with receipt items
        suggestions_response = await _get_receipt_based_suggestions(
            db=db,
            user_id=user_id,
            receipt_items=mock_pantry_ingredients,
            max_suggestions=max_suggestions,
            filters=filters
        )
        
        if suggestions_response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate recipe suggestions from receipt items"
            )
        
        # Add receipt context to the response
        suggestions_response.receipt_id = receipt_id
        suggestions_response.receipt_store = receipt.store_name
        suggestions_response.receipt_date = receipt.receipt_date
        
        return suggestions_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recipe suggestions for receipt {receipt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating recipe suggestions"
        )


async def _get_receipt_based_suggestions(
    db,
    user_id: str,
    receipt_items: List,
    max_suggestions: int = 10,
    filters = None
):
    """
    Generate recipe suggestions based on receipt items using the leftover suggestions algorithm
    
    This is a modified version of get_leftover_suggestions that works with receipt items
    instead of pantry items.
    """
    try:
        from app.crud.leftovers import (
            filter_recipes_by_availability,
            calculate_recipe_match_score,
            calculate_suggestion_priority_score,
            rank_suggestions_by_priority
        )
        from app.models.leftovers import LeftoverSuggestion, LeftoverSuggestionsResponse
        from datetime import datetime
        
        start_time = datetime.utcnow()
        
        # Use provided filters or create default
        if not filters:
            from app.models.leftovers import SuggestionFilters
            filters = SuggestionFilters(max_suggestions=max_suggestions)
        
        if not receipt_items:
            return LeftoverSuggestionsResponse(
                suggestions=[],
                total_suggestions=0,
                user_id=user_id,
                pantry_items_count=0,
                recipes_analyzed=0,
                min_match_percentage=filters.min_match_percentage,
                filters_applied=filters.dict()
            )
        
        # Filter recipes by availability using receipt items
        filtered_recipes = await filter_recipes_by_availability(
            db,
            receipt_items,
            user_id,
            filters.min_match_percentage,
            filters
        )
        
        if not filtered_recipes:
            return LeftoverSuggestionsResponse(
                suggestions=[],
                total_suggestions=0,
                user_id=user_id,
                pantry_items_count=len(receipt_items),
                recipes_analyzed=0,
                min_match_percentage=filters.min_match_percentage,
                filters_applied=filters.dict()
            )
        
        # Generate suggestions
        suggestions = []
        
        for recipe in filtered_recipes:
            # Extract ingredient names
            ingredient_names = [ing.name for ing in recipe.ingredients]
            
            # Calculate match details
            match_percentage, matched_ingredients, missing_ingredients = calculate_recipe_match_score(
                ingredient_names,
                receipt_items,
                filters.include_substitutes
            )
            
            # Calculate priority score
            priority_score, score_breakdown = calculate_suggestion_priority_score(
                recipe,
                match_percentage,
                matched_ingredients,
                receipt_items,
                filters
            )
            
            # Create suggestion reason
            reason_parts = []
            if match_percentage >= 80:
                reason_parts.append("High ingredient match with receipt items")
            elif match_percentage >= 60:
                reason_parts.append("Good ingredient match with receipt items")
            else:
                reason_parts.append("Partial ingredient match with receipt items")
            
            if recipe.difficulty == "easy":
                reason_parts.append("easy to prepare")
            
            suggestion_reason = ", ".join(reason_parts).capitalize()
            
            # Create suggestion
            suggestion = LeftoverSuggestion(
                recipe=recipe,
                match_score=priority_score,
                match_percentage=match_percentage,
                matched_ingredients=matched_ingredients,
                missing_ingredients=missing_ingredients,
                total_ingredients=len(ingredient_names),
                available_ingredients_count=len(matched_ingredients),
                missing_ingredients_count=len(missing_ingredients),
                suggestion_reason=suggestion_reason,
                priority_score=priority_score,
                estimated_prep_time=recipe.prep_time,
                difficulty_bonus=score_breakdown.get("difficulty_bonus", 0.0),
                freshness_bonus=score_breakdown.get("freshness_bonus", 0.0),
                expiration_urgency=0.0  # Receipt items are fresh
            )
            
            suggestions.append(suggestion)
        
        # Rank suggestions by priority
        ranked_suggestions = rank_suggestions_by_priority(suggestions)
        
        # Limit to max suggestions
        final_suggestions = ranked_suggestions[:filters.max_suggestions]
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return LeftoverSuggestionsResponse(
            suggestions=final_suggestions,
            total_suggestions=len(final_suggestions),
            user_id=user_id,
            pantry_items_count=len(receipt_items),
            recipes_analyzed=len(filtered_recipes),
            min_match_percentage=filters.min_match_percentage,
            filters_applied=filters.dict(),
            performance_metrics={
                "processing_time_ms": processing_time,
                "total_recipes_considered": len(filtered_recipes),
                "suggestions_generated": len(suggestions)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating receipt-based suggestions for user {user_id}: {e}")
        return None