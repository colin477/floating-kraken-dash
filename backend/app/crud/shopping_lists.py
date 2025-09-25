"""
CRUD operations for shopping list management
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database import get_collection
from app.models.shopping_lists import (
    ShoppingList,
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingListResponse,
    ShoppingListsListResponse,
    ShoppingListStatsResponse,
    ShoppingItem,
    ShoppingItemUpdate,
    BulkItemUpdateRequest,
    BulkItemUpdateResponse,
    ShoppingListStatus,
    ShoppingListItemStatus,
    ShoppingListCategory
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_shopping_list_indexes():
    """
    Create database indexes for shopping lists collection
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        # Create indexes for efficient querying
        await shopping_lists_collection.create_index([("user_id", 1)])
        await shopping_lists_collection.create_index([("user_id", 1), ("status", 1)])
        await shopping_lists_collection.create_index([("user_id", 1), ("shopping_date", 1)])
        await shopping_lists_collection.create_index([("created_at", -1)])
        await shopping_lists_collection.create_index([("tags", 1)])
        
        logger.info("Created shopping list indexes")
        return True
    except Exception as e:
        logger.error(f"Error creating shopping list indexes: {e}")
        return False


async def create_shopping_list(user_id: str, shopping_list_data: ShoppingListCreate) -> Optional[ShoppingListResponse]:
    """
    Create a new shopping list for a user
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_data: Shopping list creation data
        
    Returns:
        Created ShoppingListResponse object if successful, None otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        # Process items and assign IDs
        processed_items = []
        total_estimated_cost = 0.0
        
        for item_data in shopping_list_data.items:
            item_dict = item_data.dict()
            item_dict["id"] = str(uuid.uuid4())
            item_dict["purchased_at"] = None
            processed_items.append(item_dict)
            
            # Add to estimated cost
            if item_data.estimated_price:
                total_estimated_cost += item_data.estimated_price * item_data.quantity
        
        # Create shopping list document
        shopping_list_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "title": shopping_list_data.title,
            "description": shopping_list_data.description,
            "status": ShoppingListStatus.ACTIVE,
            "items": processed_items,
            "stores": shopping_list_data.stores,
            "total_estimated_cost": round(total_estimated_cost, 2),
            "total_actual_cost": 0.0,
            "budget_limit": shopping_list_data.budget_limit,
            "meal_plan_id": None,
            "shopping_date": datetime.combine(shopping_list_data.shopping_date, datetime.min.time()) if shopping_list_data.shopping_date else None,
            "completed_at": None,
            "tags": shopping_list_data.tags,
            "shared_with": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert shopping list into database
        result = await shopping_lists_collection.insert_one(shopping_list_doc)
        
        # Return the created shopping list
        created_shopping_list = await shopping_lists_collection.find_one({"_id": result.inserted_id})
        if created_shopping_list:
            # Convert ObjectId to string for the response
            created_shopping_list["id"] = str(created_shopping_list["_id"])
            del created_shopping_list["_id"]
            
            # Ensure all required computed fields are present with defaults
            created_shopping_list.setdefault("items_count", 0)
            created_shopping_list.setdefault("purchased_items_count", 0)
            created_shopping_list.setdefault("completion_percentage", 0.0)
            created_shopping_list.setdefault("budget_used_percentage", None)
            
            return ShoppingListResponse(**created_shopping_list)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating shopping list for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating shopping list for user {user_id}: {e}")
        return None


async def get_shopping_lists(
    user_id: str,
    status: Optional[ShoppingListStatus] = None,
    tags: Optional[List[str]] = None,
    store: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Optional[ShoppingListsListResponse]:
    """
    Get shopping lists for a user with filtering and pagination
    
    Args:
        user_id: User's ObjectId as string
        status: Filter by shopping list status
        tags: Filter by tags
        store: Filter by store
        start_date: Filter by shopping date (from)
        end_date: Filter by shopping date (to)
        page: Page number (1-based)
        page_size: Number of items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        ShoppingListsListResponse with paginated results
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        
        if status:
            query_filter["status"] = status
            
        if tags:
            query_filter["tags"] = {"$in": tags}
            
        if store:
            query_filter["stores"] = {"$in": [store]}
            
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query_filter["shopping_date"] = date_filter
        
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Build sort criteria
        sort_direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count
        total_count = await shopping_lists_collection.count_documents(query_filter)
        
        # Get paginated results
        cursor = shopping_lists_collection.find(query_filter).sort(sort_criteria).skip(skip).limit(page_size)
        shopping_lists = await cursor.to_list(length=page_size)
        
        # Convert to response objects
        shopping_list_responses = []
        for shopping_list in shopping_lists:
            shopping_list["id"] = str(shopping_list["_id"])
            del shopping_list["_id"]
            
            # Ensure all required computed fields are present with defaults
            shopping_list.setdefault("items_count", 0)
            shopping_list.setdefault("purchased_items_count", 0)
            shopping_list.setdefault("completion_percentage", 0.0)
            shopping_list.setdefault("budget_used_percentage", None)
            
            shopping_list_responses.append(ShoppingListResponse(**shopping_list))
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return ShoppingListsListResponse(
            shopping_lists=shopping_list_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting shopping lists for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting shopping lists for user {user_id}: {e}")
        return None


async def get_shopping_list_by_id(user_id: str, shopping_list_id: str) -> Optional[ShoppingListResponse]:
    """
    Get a specific shopping list by ID
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        
    Returns:
        ShoppingListResponse object if found, None otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return None
            
        shopping_list = await shopping_lists_collection.find_one({
            "_id": ObjectId(shopping_list_id),
            "user_id": user_id
        })
        
        if shopping_list:
            shopping_list["id"] = str(shopping_list["_id"])
            del shopping_list["_id"]
            
            # Ensure all required computed fields are present with defaults
            shopping_list.setdefault("items_count", 0)
            shopping_list.setdefault("purchased_items_count", 0)
            shopping_list.setdefault("completion_percentage", 0.0)
            shopping_list.setdefault("budget_used_percentage", None)
            
            return ShoppingListResponse(**shopping_list)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting shopping list {shopping_list_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting shopping list {shopping_list_id} for user {user_id}: {e}")
        return None


async def update_shopping_list(user_id: str, shopping_list_id: str, update_data: ShoppingListUpdate) -> Optional[ShoppingListResponse]:
    """
    Update an existing shopping list
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        update_data: Shopping list update data
        
    Returns:
        Updated ShoppingListResponse object if successful, None otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            if field == "items" and value:
                # Process items and ensure they have IDs
                processed_items = []
                total_estimated_cost = 0.0
                total_actual_cost = 0.0
                
                for item in value:
                    item_dict = item.dict()
                    if not item_dict.get("id"):
                        item_dict["id"] = str(uuid.uuid4())
                    
                    processed_items.append(item_dict)
                    
                    # Calculate costs
                    if item.estimated_price:
                        total_estimated_cost += item.estimated_price * item.quantity
                    if item.actual_price:
                        total_actual_cost += item.actual_price * item.quantity
                
                update_doc[field] = processed_items
                update_doc["total_estimated_cost"] = round(total_estimated_cost, 2)
                update_doc["total_actual_cost"] = round(total_actual_cost, 2)
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update
            return await get_shopping_list_by_id(user_id, shopping_list_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # If status is being changed to completed, set completed_at
        if update_data.status == ShoppingListStatus.COMPLETED:
            update_doc["completed_at"] = datetime.utcnow()
        
        # Update shopping list
        result = await shopping_lists_collection.update_one(
            {"_id": ObjectId(shopping_list_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated shopping list
        return await get_shopping_list_by_id(user_id, shopping_list_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating shopping list {shopping_list_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating shopping list {shopping_list_id} for user {user_id}: {e}")
        return None


async def delete_shopping_list(user_id: str, shopping_list_id: str) -> bool:
    """
    Delete a shopping list
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return False
        
        result = await shopping_lists_collection.delete_one({
            "_id": ObjectId(shopping_list_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting shopping list {shopping_list_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting shopping list {shopping_list_id} for user {user_id}: {e}")
        return False


async def update_shopping_item(user_id: str, shopping_list_id: str, item_id: str, update_data: ShoppingItemUpdate) -> Optional[ShoppingListResponse]:
    """
    Update a specific item in a shopping list
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        item_id: Shopping item's ID
        update_data: Item update data
        
    Returns:
        Updated ShoppingListResponse object if successful, None otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return None
        
        # Build update fields for the specific item
        update_fields = {}
        for field, value in update_data.dict(exclude_none=True).items():
            update_fields[f"items.$.{field}"] = value
        
        if not update_fields:
            return await get_shopping_list_by_id(user_id, shopping_list_id)
        
        # Add purchased_at timestamp if status is being changed to purchased
        if update_data.status == ShoppingListItemStatus.PURCHASED:
            update_fields["items.$.purchased_at"] = datetime.utcnow()
        
        # Update the specific item
        result = await shopping_lists_collection.update_one(
            {
                "_id": ObjectId(shopping_list_id),
                "user_id": user_id,
                "items.id": item_id
            },
            {
                "$set": {
                    **update_fields,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return None
        
        # Recalculate totals if price was updated
        if update_data.actual_price is not None:
            await recalculate_shopping_list_totals(user_id, shopping_list_id)
        
        # Return updated shopping list
        return await get_shopping_list_by_id(user_id, shopping_list_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating shopping item {item_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating shopping item {item_id} for user {user_id}: {e}")
        return None


async def bulk_update_shopping_items(user_id: str, shopping_list_id: str, bulk_request: BulkItemUpdateRequest) -> Optional[BulkItemUpdateResponse]:
    """
    Bulk update multiple shopping list items
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        bulk_request: Bulk update request data
        
    Returns:
        BulkItemUpdateResponse with results
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return None
        
        updated_count = 0
        failed_count = 0
        errors = []
        
        # Update each item individually
        for item_id in bulk_request.item_ids:
            try:
                result = await update_shopping_item(user_id, shopping_list_id, item_id, bulk_request.updates)
                if result:
                    updated_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Failed to update item {item_id}")
            except Exception as e:
                failed_count += 1
                errors.append(f"Error updating item {item_id}: {str(e)}")
        
        return BulkItemUpdateResponse(
            updated_count=updated_count,
            failed_count=failed_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error bulk updating shopping items for user {user_id}: {e}")
        return None


async def recalculate_shopping_list_totals(user_id: str, shopping_list_id: str) -> bool:
    """
    Recalculate total costs for a shopping list
    
    Args:
        user_id: User's ObjectId as string
        shopping_list_id: Shopping list's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        if not ObjectId.is_valid(shopping_list_id):
            return False
        
        # Get the shopping list
        shopping_list = await shopping_lists_collection.find_one({
            "_id": ObjectId(shopping_list_id),
            "user_id": user_id
        })
        
        if not shopping_list:
            return False
        
        # Calculate totals
        total_estimated_cost = 0.0
        total_actual_cost = 0.0
        
        for item in shopping_list.get("items", []):
            quantity = item.get("quantity", 0)
            estimated_price = item.get("estimated_price", 0)
            actual_price = item.get("actual_price", 0)
            
            if estimated_price:
                total_estimated_cost += estimated_price * quantity
            if actual_price:
                total_actual_cost += actual_price * quantity
        
        # Update the totals
        result = await shopping_lists_collection.update_one(
            {"_id": ObjectId(shopping_list_id), "user_id": user_id},
            {
                "$set": {
                    "total_estimated_cost": round(total_estimated_cost, 2),
                    "total_actual_cost": round(total_actual_cost, 2),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        logger.error(f"Error recalculating totals for shopping list {shopping_list_id}: {e}")
        return False


async def get_shopping_list_stats(user_id: str) -> Optional[ShoppingListStatsResponse]:
    """
    Get shopping list statistics for a user
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        ShoppingListStatsResponse with statistics
    """
    try:
        shopping_lists_collection = await get_collection("shopping_lists")
        
        # Get all shopping lists for the user
        shopping_lists = await shopping_lists_collection.find({"user_id": user_id}).to_list(length=None)
        
        if not shopping_lists:
            return ShoppingListStatsResponse(
                total_lists=0,
                active_lists=0,
                completed_lists=0,
                total_items=0,
                total_spent=0.0,
                average_list_cost=None,
                most_shopped_store=None,
                most_purchased_category=None,
                budget_adherence_rate=None,
                completion_rate=None
            )
        
        # Calculate statistics
        total_lists = len(shopping_lists)
        active_lists = len([sl for sl in shopping_lists if sl.get("status") == ShoppingListStatus.ACTIVE])
        completed_lists = len([sl for sl in shopping_lists if sl.get("status") == ShoppingListStatus.COMPLETED])
        
        # Calculate totals
        total_items = 0
        total_spent = 0.0
        store_counts = {}
        category_counts = {}
        completion_rates = []
        
        for shopping_list in shopping_lists:
            items = shopping_list.get("items", [])
            total_items += len(items)
            total_spent += shopping_list.get("total_actual_cost", 0)
            
            # Count stores
            for store in shopping_list.get("stores", []):
                store_counts[store] = store_counts.get(store, 0) + 1
            
            # Count categories and calculate completion rate
            purchased_items = 0
            for item in items:
                category = item.get("category")
                if category:
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                if item.get("status") == ShoppingListItemStatus.PURCHASED:
                    purchased_items += 1
            
            if items:
                completion_rates.append((purchased_items / len(items)) * 100)
        
        # Calculate averages and most common values
        average_list_cost = total_spent / completed_lists if completed_lists > 0 else None
        most_shopped_store = max(store_counts, key=store_counts.get) if store_counts else None
        most_purchased_category = max(category_counts, key=category_counts.get) if category_counts else None
        
        # Calculate budget adherence rate
        lists_with_budget = [sl for sl in shopping_lists if sl.get("budget_limit") and sl.get("total_actual_cost")]
        if lists_with_budget:
            within_budget = len([sl for sl in lists_with_budget 
                               if sl.get("total_actual_cost", 0) <= sl.get("budget_limit", 0)])
            budget_adherence_rate = (within_budget / len(lists_with_budget)) * 100
        else:
            budget_adherence_rate = None
        
        # Calculate average completion rate
        average_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else None
        
        return ShoppingListStatsResponse(
            total_lists=total_lists,
            active_lists=active_lists,
            completed_lists=completed_lists,
            total_items=total_items,
            total_spent=round(total_spent, 2),
            average_list_cost=round(average_list_cost, 2) if average_list_cost else None,
            most_shopped_store=most_shopped_store,
            most_purchased_category=most_purchased_category,
            budget_adherence_rate=round(budget_adherence_rate, 1) if budget_adherence_rate else None,
            completion_rate=round(average_completion_rate, 1) if average_completion_rate else None
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting shopping list stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting shopping list stats for user {user_id}: {e}")
        return None