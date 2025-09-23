"""
CRUD operations for pantry management
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, DESCENDING

from app.database import get_collection
from app.models.pantry import (
    PantryItem,
    PantryItemCreate,
    PantryItemUpdate,
    PantryItemResponse,
    PantryItemsListResponse,
    ExpiringItemsResponse,
    PantryStatsResponse,
    PantryCategory
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_pantry_indexes():
    """
    Create database indexes for pantry_items collection
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        # Get existing indexes
        existing_indexes = await pantry_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Create compound index on user_id and name for uniqueness
        if "user_id_name_unique" not in existing_index_names:
            try:
                await pantry_collection.create_index(
                    [("user_id", ASCENDING), ("name", ASCENDING)],
                    unique=True,
                    name="user_id_name_unique"
                )
                logger.info("Created unique compound index on pantry_items.user_id and name")
            except Exception as e:
                logger.error(f"Error creating unique compound index: {e}")
        
        # Create index on user_id for efficient user queries
        if "user_id_index" not in existing_index_names:
            try:
                await pantry_collection.create_index(
                    [("user_id", ASCENDING)],
                    name="user_id_index"
                )
                logger.info("Created index on pantry_items.user_id")
            except Exception as e:
                logger.error(f"Error creating user_id index: {e}")
        
        # Create index on expiration_date for expiring items queries
        if "expiration_date_index" not in existing_index_names:
            try:
                await pantry_collection.create_index(
                    [("expiration_date", ASCENDING)],
                    name="expiration_date_index"
                )
                logger.info("Created index on pantry_items.expiration_date")
            except Exception as e:
                logger.error(f"Error creating expiration_date index: {e}")
        
        # Create compound index for user and category queries
        if "user_id_category_index" not in existing_index_names:
            try:
                await pantry_collection.create_index(
                    [("user_id", ASCENDING), ("category", ASCENDING)],
                    name="user_id_category_index"
                )
                logger.info("Created compound index on pantry_items.user_id and category")
            except Exception as e:
                logger.error(f"Error creating user_id_category index: {e}")
                
        return True
    except Exception as e:
        logger.error(f"Error creating pantry indexes: {e}")
        return False


def _convert_pantry_item_response(item_doc: dict) -> PantryItemResponse:
    """
    Convert database document to PantryItemResponse
    """
    # Convert ObjectId to string
    item_doc["_id"] = str(item_doc["_id"])
    
    # Calculate days until expiration
    days_until_expiration = None
    if item_doc.get("expiration_date"):
        today = date.today()
        if isinstance(item_doc["expiration_date"], datetime):
            exp_date = item_doc["expiration_date"].date()
        else:
            exp_date = item_doc["expiration_date"]
        delta = exp_date - today
        days_until_expiration = delta.days
    
    return PantryItemResponse(
        id=item_doc["_id"],
        user_id=item_doc["user_id"],
        name=item_doc["name"],
        category=item_doc["category"],
        quantity=item_doc["quantity"],
        unit=item_doc["unit"],
        expiration_date=item_doc.get("expiration_date"),
        purchase_date=item_doc.get("purchase_date"),
        notes=item_doc.get("notes"),
        created_at=item_doc["created_at"],
        updated_at=item_doc["updated_at"],
        days_until_expiration=days_until_expiration
    )


async def create_pantry_item(user_id: str, item_data: PantryItemCreate) -> Optional[PantryItemResponse]:
    """
    Create a new pantry item for a user
    
    Args:
        user_id: User's ObjectId as string
        item_data: Pantry item creation data
        
    Returns:
        Created PantryItemResponse if successful, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        # Check if item with same name already exists for this user
        existing_item = await pantry_collection.find_one({
            "user_id": user_id,
            "name": item_data.name
        })
        if existing_item:
            logger.warning(f"Pantry item '{item_data.name}' already exists for user {user_id}")
            return None
        
        # Create pantry item document
        # Convert date objects to datetime objects for MongoDB compatibility
        expiration_datetime = None
        if item_data.expiration_date:
            expiration_datetime = datetime.combine(item_data.expiration_date, datetime.min.time())
        
        purchase_datetime = None
        if item_data.purchase_date:
            purchase_datetime = datetime.combine(item_data.purchase_date, datetime.min.time())
        
        item_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "name": item_data.name,
            "category": item_data.category,
            "quantity": item_data.quantity,
            "unit": item_data.unit,
            "expiration_date": expiration_datetime,
            "purchase_date": purchase_datetime,
            "notes": item_data.notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert item into database
        result = await pantry_collection.insert_one(item_doc)
        
        # Return the created item
        created_item = await pantry_collection.find_one({"_id": result.inserted_id})
        if created_item:
            return _convert_pantry_item_response(created_item)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating pantry item for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating pantry item for user {user_id}: {e}")
        return None


async def get_pantry_items(
    user_id: str,
    category: Optional[PantryCategory] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> Optional[PantryItemsListResponse]:
    """
    Get pantry items for a user with optional filtering and pagination
    
    Args:
        user_id: User's ObjectId as string
        category: Optional category filter
        page: Page number (1-based)
        page_size: Number of items per page
        sort_by: Field to sort by (name, created_at, expiration_date, etc.)
        sort_order: Sort order (asc or desc)
        
    Returns:
        PantryItemsListResponse if successful, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        if category:
            query_filter["category"] = category
        
        # Build sort criteria
        sort_direction = ASCENDING if sort_order.lower() == "asc" else DESCENDING
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count
        total_count = await pantry_collection.count_documents(query_filter)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get items with pagination
        cursor = pantry_collection.find(query_filter).sort(sort_criteria).skip(skip).limit(page_size)
        items = await cursor.to_list(length=page_size)
        
        # Convert to response objects
        item_responses = [_convert_pantry_item_response(item) for item in items]
        
        return PantryItemsListResponse(
            items=item_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting pantry items for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting pantry items for user {user_id}: {e}")
        return None


async def get_pantry_item_by_id(user_id: str, item_id: str) -> Optional[PantryItemResponse]:
    """
    Get a specific pantry item by ID for a user
    
    Args:
        user_id: User's ObjectId as string
        item_id: Pantry item's ObjectId as string
        
    Returns:
        PantryItemResponse if found, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        if not ObjectId.is_valid(item_id):
            return None
        
        item = await pantry_collection.find_one({
            "_id": ObjectId(item_id),
            "user_id": user_id
        })
        
        if item:
            return _convert_pantry_item_response(item)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting pantry item {item_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting pantry item {item_id} for user {user_id}: {e}")
        return None


async def update_pantry_item(user_id: str, item_id: str, update_data: PantryItemUpdate) -> Optional[PantryItemResponse]:
    """
    Update a pantry item for a user
    
    Args:
        user_id: User's ObjectId as string
        item_id: Pantry item's ObjectId as string
        update_data: Pantry item update data
        
    Returns:
        Updated PantryItemResponse if successful, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        if not ObjectId.is_valid(item_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            # Convert date objects to datetime objects for MongoDB compatibility
            if field in ['expiration_date', 'purchase_date'] and value is not None:
                if hasattr(value, 'date'):  # It's already a datetime
                    update_doc[field] = value
                else:  # It's a date object, convert to datetime
                    update_doc[field] = datetime.combine(value, datetime.min.time())
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update, return current item
            return await get_pantry_item_by_id(user_id, item_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update item
        result = await pantry_collection.update_one(
            {"_id": ObjectId(item_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated item
        return await get_pantry_item_by_id(user_id, item_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating pantry item {item_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating pantry item {item_id} for user {user_id}: {e}")
        return None


async def delete_pantry_item(user_id: str, item_id: str) -> bool:
    """
    Delete a pantry item for a user
    
    Args:
        user_id: User's ObjectId as string
        item_id: Pantry item's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        if not ObjectId.is_valid(item_id):
            return False
        
        result = await pantry_collection.delete_one({
            "_id": ObjectId(item_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting pantry item {item_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting pantry item {item_id} for user {user_id}: {e}")
        return False


async def get_expiring_items(user_id: str, days_threshold: int = 7) -> Optional[ExpiringItemsResponse]:
    """
    Get items that are expiring soon or have already expired
    
    Args:
        user_id: User's ObjectId as string
        days_threshold: Number of days to consider as "expiring soon"
        
    Returns:
        ExpiringItemsResponse if successful, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)
        
        # Convert dates to datetime objects for MongoDB compatibility
        today_datetime = datetime.combine(today, datetime.min.time())
        threshold_datetime = datetime.combine(threshold_date, datetime.min.time())
        
        # Get items expiring soon (within threshold)
        expiring_soon_cursor = pantry_collection.find({
            "user_id": user_id,
            "expiration_date": {
                "$gte": today_datetime,
                "$lte": threshold_datetime
            }
        }).sort("expiration_date", ASCENDING)
        
        expiring_soon_items = await expiring_soon_cursor.to_list(length=None)
        
        # Get expired items
        expired_cursor = pantry_collection.find({
            "user_id": user_id,
            "expiration_date": {"$lt": today_datetime}
        }).sort("expiration_date", DESCENDING)
        
        expired_items = await expired_cursor.to_list(length=None)
        
        # Convert to response objects
        expiring_soon_responses = [_convert_pantry_item_response(item) for item in expiring_soon_items]
        expired_responses = [_convert_pantry_item_response(item) for item in expired_items]
        
        return ExpiringItemsResponse(
            expiring_soon=expiring_soon_responses,
            expired=expired_responses,
            days_threshold=days_threshold
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting expiring items for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting expiring items for user {user_id}: {e}")
        return None


async def get_pantry_stats(user_id: str) -> Optional[PantryStatsResponse]:
    """
    Get pantry statistics for a user
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        PantryStatsResponse if successful, None otherwise
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        # Get total items count
        total_items = await pantry_collection.count_documents({"user_id": user_id})
        
        # Get items by category
        category_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_cursor = pantry_collection.aggregate(category_pipeline)
        category_results = await category_cursor.to_list(length=None)
        items_by_category = {result["_id"]: result["count"] for result in category_results}
        
        # Get expiring items counts
        today = date.today()
        threshold_date = today + timedelta(days=7)
        
        # Convert dates to datetime objects for MongoDB compatibility
        today_datetime = datetime.combine(today, datetime.min.time())
        threshold_datetime = datetime.combine(threshold_date, datetime.min.time())
        
        expiring_soon_count = await pantry_collection.count_documents({
            "user_id": user_id,
            "expiration_date": {
                "$gte": today_datetime,
                "$lte": threshold_datetime
            }
        })
        
        expired_count = await pantry_collection.count_documents({
            "user_id": user_id,
            "expiration_date": {"$lt": today_datetime}
        })
        
        return PantryStatsResponse(
            total_items=total_items,
            items_by_category=items_by_category,
            expiring_soon_count=expiring_soon_count,
            expired_count=expired_count,
            total_value_estimate=None  # Could be implemented later with price data
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting pantry stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting pantry stats for user {user_id}: {e}")
        return None


async def search_pantry_items(user_id: str, search_term: str, limit: int = 20) -> List[PantryItemResponse]:
    """
    Search pantry items by name for a user
    
    Args:
        user_id: User's ObjectId as string
        search_term: Search term to match against item names
        limit: Maximum number of results to return
        
    Returns:
        List of matching PantryItemResponse objects
    """
    try:
        pantry_collection = await get_collection("pantry_items")
        
        # Use regex search for partial matching (case-insensitive)
        cursor = pantry_collection.find({
            "user_id": user_id,
            "name": {"$regex": search_term, "$options": "i"}
        }).limit(limit).sort("name", ASCENDING)
        
        items = await cursor.to_list(length=limit)
        
        return [_convert_pantry_item_response(item) for item in items]
        
    except PyMongoError as e:
        logger.error(f"Database error searching pantry items for user {user_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching pantry items for user {user_id}: {e}")
        return []