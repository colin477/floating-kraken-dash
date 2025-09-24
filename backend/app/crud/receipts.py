"""
CRUD operations for receipt processing
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, DESCENDING

from app.database import get_collection
from app.models.receipts import (
    Receipt,
    ReceiptCreate,
    ReceiptUpdate,
    ReceiptResponse,
    ReceiptsListResponse,
    ReceiptProcessingResponse,
    AddToPantryResponse,
    ReceiptStatsResponse,
    ReceiptItem,
    ReceiptItemCategory,
    ReceiptProcessingStatus
)
from app.models.pantry import PantryItemCreate, PantryCategory, PantryUnit
from app.crud.pantry import create_pantry_item

# Configure logging
logger = logging.getLogger(__name__)


async def create_receipt_indexes():
    """
    Create database indexes for receipts collection
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        # Get existing indexes
        existing_indexes = await receipts_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Create index on user_id for efficient user queries
        if "user_id_index" not in existing_index_names:
            try:
                await receipts_collection.create_index(
                    [("user_id", ASCENDING)],
                    name="user_id_index"
                )
                logger.info("Created index on receipts.user_id")
            except Exception as e:
                logger.error(f"Error creating user_id index: {e}")
        
        # Create index on receipt_date for date-based queries
        if "receipt_date_index" not in existing_index_names:
            try:
                await receipts_collection.create_index(
                    [("receipt_date", DESCENDING)],
                    name="receipt_date_index"
                )
                logger.info("Created index on receipts.receipt_date")
            except Exception as e:
                logger.error(f"Error creating receipt_date index: {e}")
        
        # Create compound index for user and store queries
        if "user_id_store_index" not in existing_index_names:
            try:
                await receipts_collection.create_index(
                    [("user_id", ASCENDING), ("store_name", ASCENDING)],
                    name="user_id_store_index"
                )
                logger.info("Created compound index on receipts.user_id and store_name")
            except Exception as e:
                logger.error(f"Error creating user_id_store index: {e}")
        
        # Create compound index for user and processing status
        if "user_id_status_index" not in existing_index_names:
            try:
                await receipts_collection.create_index(
                    [("user_id", ASCENDING), ("processing_status", ASCENDING)],
                    name="user_id_status_index"
                )
                logger.info("Created compound index on receipts.user_id and processing_status")
            except Exception as e:
                logger.error(f"Error creating user_id_status index: {e}")
                
        return True
    except Exception as e:
        logger.error(f"Error creating receipt indexes: {e}")
        return False


def _convert_receipt_response(receipt_doc: dict) -> ReceiptResponse:
    """
    Convert database document to ReceiptResponse
    """
    # Convert ObjectId to string
    receipt_doc["_id"] = str(receipt_doc["_id"])
    
    return ReceiptResponse(
        id=receipt_doc["_id"],
        user_id=receipt_doc["user_id"],
        store_name=receipt_doc["store_name"],
        receipt_date=receipt_doc["receipt_date"],
        total_amount=receipt_doc["total_amount"],
        items=receipt_doc.get("items", []),
        photo_url=receipt_doc.get("photo_url"),
        processing_status=receipt_doc.get("processing_status", ReceiptProcessingStatus.PENDING),
        processed_at=receipt_doc.get("processed_at"),
        created_at=receipt_doc["created_at"],
        updated_at=receipt_doc["updated_at"]
    )


async def create_receipt(user_id: str, receipt_data: ReceiptCreate) -> Optional[ReceiptResponse]:
    """
    Create a new receipt for a user
    
    Args:
        user_id: User's ObjectId as string
        receipt_data: Receipt creation data
        
    Returns:
        Created ReceiptResponse if successful, None otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        # Convert date to datetime for MongoDB compatibility
        receipt_datetime = None
        if receipt_data.receipt_date:
            receipt_datetime = datetime.combine(receipt_data.receipt_date, datetime.min.time())
        
        # Create receipt document
        receipt_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "store_name": receipt_data.store_name,
            "receipt_date": receipt_datetime,
            "total_amount": receipt_data.total_amount,
            "items": [],
            "photo_url": receipt_data.photo_url,
            "processing_status": ReceiptProcessingStatus.PENDING,
            "processed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert receipt into database
        result = await receipts_collection.insert_one(receipt_doc)
        
        # Return the created receipt
        created_receipt = await receipts_collection.find_one({"_id": result.inserted_id})
        if created_receipt:
            return _convert_receipt_response(created_receipt)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating receipt for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating receipt for user {user_id}: {e}")
        return None


async def get_receipts(
    user_id: str,
    store_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    processing_status: Optional[ReceiptProcessingStatus] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "receipt_date",
    sort_order: str = "desc"
) -> Optional[ReceiptsListResponse]:
    """
    Get receipts for a user with optional filtering and pagination
    
    Args:
        user_id: User's ObjectId as string
        store_name: Optional store name filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        processing_status: Optional processing status filter
        page: Page number (1-based)
        page_size: Number of receipts per page
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        ReceiptsListResponse if successful, None otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        
        if store_name:
            query_filter["store_name"] = {"$regex": store_name, "$options": "i"}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                date_filter["$gte"] = start_datetime
            if end_date:
                end_datetime = datetime.combine(end_date, datetime.max.time())
                date_filter["$lte"] = end_datetime
            query_filter["receipt_date"] = date_filter
        
        if processing_status:
            query_filter["processing_status"] = processing_status
        
        # Build sort criteria
        sort_direction = ASCENDING if sort_order.lower() == "asc" else DESCENDING
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count
        total_count = await receipts_collection.count_documents(query_filter)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get receipts with pagination
        cursor = receipts_collection.find(query_filter).sort(sort_criteria).skip(skip).limit(page_size)
        receipts = await cursor.to_list(length=page_size)
        
        # Convert to response objects
        receipt_responses = [_convert_receipt_response(receipt) for receipt in receipts]
        
        return ReceiptsListResponse(
            receipts=receipt_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting receipts for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting receipts for user {user_id}: {e}")
        return None


async def get_receipt_by_id(user_id: str, receipt_id: str) -> Optional[ReceiptResponse]:
    """
    Get a specific receipt by ID for a user
    
    Args:
        user_id: User's ObjectId as string
        receipt_id: Receipt's ObjectId as string
        
    Returns:
        ReceiptResponse if found, None otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        if not ObjectId.is_valid(receipt_id):
            return None
        
        receipt = await receipts_collection.find_one({
            "_id": ObjectId(receipt_id),
            "user_id": user_id
        })
        
        if receipt:
            return _convert_receipt_response(receipt)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting receipt {receipt_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting receipt {receipt_id} for user {user_id}: {e}")
        return None


async def update_receipt(user_id: str, receipt_id: str, update_data: ReceiptUpdate) -> Optional[ReceiptResponse]:
    """
    Update a receipt for a user
    
    Args:
        user_id: User's ObjectId as string
        receipt_id: Receipt's ObjectId as string
        update_data: Receipt update data
        
    Returns:
        Updated ReceiptResponse if successful, None otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        if not ObjectId.is_valid(receipt_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            # Convert date objects to datetime objects for MongoDB compatibility
            if field == 'receipt_date' and value is not None:
                if hasattr(value, 'date'):  # It's already a datetime
                    update_doc[field] = value
                else:  # It's a date object, convert to datetime
                    update_doc[field] = datetime.combine(value, datetime.min.time())
            elif field == 'items' and value is not None:
                # Convert ReceiptItem objects to dictionaries
                if isinstance(value, list) and len(value) > 0:
                    if hasattr(value[0], 'dict'):
                        update_doc[field] = [item.dict() for item in value]
                    else:
                        update_doc[field] = value
                else:
                    update_doc[field] = value
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update, return current receipt
            return await get_receipt_by_id(user_id, receipt_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update receipt
        result = await receipts_collection.update_one(
            {"_id": ObjectId(receipt_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated receipt
        return await get_receipt_by_id(user_id, receipt_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating receipt {receipt_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating receipt {receipt_id} for user {user_id}: {e}")
        return None


async def delete_receipt(user_id: str, receipt_id: str) -> bool:
    """
    Delete a receipt for a user
    
    Args:
        user_id: User's ObjectId as string
        receipt_id: Receipt's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        if not ObjectId.is_valid(receipt_id):
            return False
        
        result = await receipts_collection.delete_one({
            "_id": ObjectId(receipt_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting receipt {receipt_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting receipt {receipt_id} for user {user_id}: {e}")
        return False


async def process_receipt_image(user_id: str, receipt_id: str) -> Optional[ReceiptProcessingResponse]:
    """
    Process receipt image using AI (mock implementation for now)
    
    Args:
        user_id: User's ObjectId as string
        receipt_id: Receipt's ObjectId as string
        
    Returns:
        ReceiptProcessingResponse if successful, None otherwise
    """
    try:
        # Get the receipt first
        receipt = await get_receipt_by_id(user_id, receipt_id)
        if not receipt:
            return None
        
        # Update status to processing
        await update_receipt(user_id, receipt_id, ReceiptUpdate(
            processing_status=ReceiptProcessingStatus.PROCESSING
        ))
        
        # Mock AI processing - return sample extracted items
        mock_extracted_items = [
            ReceiptItem(
                name="Organic Bananas",
                quantity=2.5,
                unit_price=0.68,
                total_price=1.70,
                category=ReceiptItemCategory.PRODUCE
            ),
            ReceiptItem(
                name="Whole Milk",
                quantity=1.0,
                unit_price=3.49,
                total_price=3.49,
                category=ReceiptItemCategory.DAIRY
            ),
            ReceiptItem(
                name="Bread",
                quantity=1.0,
                unit_price=2.99,
                total_price=2.99,
                category=ReceiptItemCategory.GRAINS
            ),
            ReceiptItem(
                name="Ground Beef",
                quantity=1.2,
                unit_price=5.99,
                total_price=7.19,
                category=ReceiptItemCategory.MEAT
            )
        ]
        
        # Update receipt with extracted items and mark as completed
        await update_receipt(user_id, receipt_id, ReceiptUpdate(
            items=mock_extracted_items,
            processing_status=ReceiptProcessingStatus.COMPLETED,
            processed_at=datetime.utcnow()
        ))
        
        return ReceiptProcessingResponse(
            receipt_id=receipt_id,
            processing_status=ReceiptProcessingStatus.COMPLETED,
            extracted_items=mock_extracted_items,
            confidence_score=0.85,
            processing_notes="Mock AI processing completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error processing receipt {receipt_id} for user {user_id}: {e}")
        
        # Mark as failed
        try:
            await update_receipt(user_id, receipt_id, ReceiptUpdate(
                processing_status=ReceiptProcessingStatus.FAILED
            ))
        except:
            pass
        
        return None


def _map_receipt_category_to_pantry(receipt_category: ReceiptItemCategory) -> PantryCategory:
    """
    Map receipt item category to pantry category
    """
    category_mapping = {
        ReceiptItemCategory.PRODUCE: PantryCategory.PRODUCE,
        ReceiptItemCategory.DAIRY: PantryCategory.DAIRY,
        ReceiptItemCategory.MEAT: PantryCategory.MEAT,
        ReceiptItemCategory.SEAFOOD: PantryCategory.SEAFOOD,
        ReceiptItemCategory.GRAINS: PantryCategory.GRAINS,
        ReceiptItemCategory.CANNED_GOODS: PantryCategory.CANNED_GOODS,
        ReceiptItemCategory.FROZEN: PantryCategory.FROZEN,
        ReceiptItemCategory.BEVERAGES: PantryCategory.BEVERAGES,
        ReceiptItemCategory.SNACKS: PantryCategory.SNACKS,
        ReceiptItemCategory.CONDIMENTS: PantryCategory.CONDIMENTS,
        ReceiptItemCategory.SPICES: PantryCategory.SPICES,
        ReceiptItemCategory.BAKING: PantryCategory.BAKING,
        ReceiptItemCategory.OTHER: PantryCategory.OTHER
    }
    return category_mapping.get(receipt_category, PantryCategory.OTHER)


async def add_receipt_items_to_pantry(
    user_id: str,
    receipt_id: str,
    selected_items: List[int],
    expiration_days: int = 7
) -> Optional[AddToPantryResponse]:
    """
    Add selected receipt items to user's pantry
    
    Args:
        user_id: User's ObjectId as string
        receipt_id: Receipt's ObjectId as string
        selected_items: List of item indices to add to pantry
        expiration_days: Days until expiration (default 7)
        
    Returns:
        AddToPantryResponse if successful, None otherwise
    """
    try:
        # Get the receipt
        receipt = await get_receipt_by_id(user_id, receipt_id)
        if not receipt or not receipt.items:
            return None
        
        pantry_items_created = []
        errors = []
        items_added = 0
        items_failed = 0
        
        # Calculate expiration date
        expiration_date = date.today() + timedelta(days=expiration_days)
        
        for item_index in selected_items:
            if item_index < 0 or item_index >= len(receipt.items):
                errors.append(f"Invalid item index: {item_index}")
                items_failed += 1
                continue
            
            receipt_item = receipt.items[item_index]
            
            try:
                # Create pantry item from receipt item
                pantry_category = _map_receipt_category_to_pantry(receipt_item.category) if receipt_item.category else PantryCategory.OTHER
                
                pantry_item_data = PantryItemCreate(
                    name=receipt_item.name,
                    category=pantry_category,
                    quantity=receipt_item.quantity,
                    unit=PantryUnit.PIECE,  # Default unit, could be improved with better mapping
                    expiration_date=expiration_date,
                    purchase_date=receipt.receipt_date,
                    notes=f"Added from receipt - {receipt.store_name}"
                )
                
                # Create pantry item
                created_item = await create_pantry_item(user_id, pantry_item_data)
                if created_item:
                    pantry_items_created.append(created_item.id)
                    items_added += 1
                else:
                    errors.append(f"Failed to create pantry item for: {receipt_item.name}")
                    items_failed += 1
                    
            except Exception as e:
                logger.error(f"Error adding receipt item to pantry: {e}")
                errors.append(f"Error adding {receipt_item.name}: {str(e)}")
                items_failed += 1
        
        return AddToPantryResponse(
            receipt_id=receipt_id,
            items_added=items_added,
            items_failed=items_failed,
            pantry_items_created=pantry_items_created,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error adding receipt items to pantry for user {user_id}: {e}")
        return None


async def get_receipt_stats(user_id: str) -> Optional[ReceiptStatsResponse]:
    """
    Get receipt statistics for a user
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        ReceiptStatsResponse if successful, None otherwise
    """
    try:
        receipts_collection = await get_collection("receipts")
        
        # Get total receipts count
        total_receipts = await receipts_collection.count_documents({"user_id": user_id})
        
        # Get total spent
        total_spent_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        total_spent_cursor = receipts_collection.aggregate(total_spent_pipeline)
        total_spent_results = await total_spent_cursor.to_list(length=1)
        total_spent = total_spent_results[0]["total"] if total_spent_results else 0.0
        
        # Get receipts by store
        store_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$store_name", "count": {"$sum": 1}, "total_spent": {"$sum": "$total_amount"}}},
            {"$sort": {"count": -1}}
        ]
        store_cursor = receipts_collection.aggregate(store_pipeline)
        store_results = await store_cursor.to_list(length=None)
        receipts_by_store = {
            result["_id"]: {
                "count": result["count"],
                "total_spent": result["total_spent"]
            } for result in store_results
        }
        
        # Get receipts by month
        month_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$receipt_date"},
                    "month": {"$month": "$receipt_date"}
                },
                "count": {"$sum": 1},
                "total_spent": {"$sum": "$total_amount"}
            }},
            {"$sort": {"_id.year": -1, "_id.month": -1}}
        ]
        month_cursor = receipts_collection.aggregate(month_pipeline)
        month_results = await month_cursor.to_list(length=None)
        receipts_by_month = {
            f"{result['_id']['year']}-{result['_id']['month']:02d}": {
                "count": result["count"],
                "total_spent": result["total_spent"]
            } for result in month_results
        }
        
        # Calculate average receipt amount
        average_receipt_amount = total_spent / total_receipts if total_receipts > 0 else 0.0
        
        # Get most purchased items (from processed receipts)
        items_pipeline = [
            {"$match": {"user_id": user_id, "items": {"$exists": True, "$ne": []}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.name",
                "count": {"$sum": 1},
                "total_quantity": {"$sum": "$items.quantity"},
                "total_spent": {"$sum": "$items.total_price"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        items_cursor = receipts_collection.aggregate(items_pipeline)
        items_results = await items_cursor.to_list(length=10)
        most_purchased_items = [
            {
                "name": result["_id"],
                "count": result["count"],
                "total_quantity": result["total_quantity"],
                "total_spent": result["total_spent"]
            } for result in items_results
        ]
        
        return ReceiptStatsResponse(
            total_receipts=total_receipts,
            total_spent=total_spent,
            receipts_by_store=receipts_by_store,
            receipts_by_month=receipts_by_month,
            average_receipt_amount=average_receipt_amount,
            most_purchased_items=most_purchased_items
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting receipt stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting receipt stats for user {user_id}: {e}")
        return None