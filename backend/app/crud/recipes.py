"""
CRUD operations for recipe management
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, DESCENDING

from app.database import get_collection
from app.models.recipes import (
    Recipe,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipesListResponse,
    RecipeSearchResponse,
    RecipeStatsResponse,
    DifficultyLevel,
    MealType,
    DietaryRestriction
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_recipe_indexes():
    """
    Create database indexes for recipes collection
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Get existing indexes
        existing_indexes = await recipes_collection.list_indexes().to_list(length=None)
        existing_index_names = {idx['name'] for idx in existing_indexes}
        
        # Create index on user_id for efficient user queries
        if "user_id_index" not in existing_index_names:
            try:
                await recipes_collection.create_index(
                    [("user_id", ASCENDING)],
                    name="user_id_index"
                )
                logger.info("Created index on recipes.user_id")
            except Exception as e:
                logger.error(f"Error creating user_id index: {e}")
        
        # Create text index for search functionality
        if "text_search_index" not in existing_index_names:
            try:
                await recipes_collection.create_index(
                    [("title", "text"), ("description", "text"), ("tags", "text")],
                    name="text_search_index"
                )
                logger.info("Created text search index on recipes")
            except Exception as e:
                logger.error(f"Error creating text search index: {e}")
        
        # Create compound index for user and difficulty queries
        if "user_id_difficulty_index" not in existing_index_names:
            try:
                await recipes_collection.create_index(
                    [("user_id", ASCENDING), ("difficulty", ASCENDING)],
                    name="user_id_difficulty_index"
                )
                logger.info("Created compound index on recipes.user_id and difficulty")
            except Exception as e:
                logger.error(f"Error creating user_id_difficulty index: {e}")
        
        # Create compound index for user and tags queries
        if "user_id_tags_index" not in existing_index_names:
            try:
                await recipes_collection.create_index(
                    [("user_id", ASCENDING), ("tags", ASCENDING)],
                    name="user_id_tags_index"
                )
                logger.info("Created compound index on recipes.user_id and tags")
            except Exception as e:
                logger.error(f"Error creating user_id_tags index: {e}")
        
        # Create compound index for user and meal_types queries
        if "user_id_meal_types_index" not in existing_index_names:
            try:
                await recipes_collection.create_index(
                    [("user_id", ASCENDING), ("meal_types", ASCENDING)],
                    name="user_id_meal_types_index"
                )
                logger.info("Created compound index on recipes.user_id and meal_types")
            except Exception as e:
                logger.error(f"Error creating user_id_meal_types index: {e}")
                
        return True
    except Exception as e:
        logger.error(f"Error creating recipe indexes: {e}")
        return False


def _convert_recipe_response(recipe_doc: dict) -> RecipeResponse:
    """
    Convert database document to RecipeResponse
    """
    # Convert ObjectId to string
    recipe_doc["_id"] = str(recipe_doc["_id"])
    
    return RecipeResponse(
        id=recipe_doc["_id"],
        user_id=recipe_doc["user_id"],
        title=recipe_doc["title"],
        description=recipe_doc.get("description"),
        ingredients=recipe_doc["ingredients"],
        instructions=recipe_doc["instructions"],
        prep_time=recipe_doc.get("prep_time"),
        cook_time=recipe_doc.get("cook_time"),
        servings=recipe_doc["servings"],
        difficulty=recipe_doc["difficulty"],
        tags=recipe_doc.get("tags", []),
        meal_types=recipe_doc.get("meal_types", []),
        dietary_restrictions=recipe_doc.get("dietary_restrictions", []),
        nutrition_info=recipe_doc.get("nutrition_info"),
        photo_url=recipe_doc.get("photo_url"),
        source_url=recipe_doc.get("source_url"),
        created_at=recipe_doc["created_at"],
        updated_at=recipe_doc["updated_at"]
    )


async def create_recipe(user_id: str, recipe_data: RecipeCreate) -> Optional[RecipeResponse]:
    """
    Create a new recipe for a user
    
    Args:
        user_id: User's ObjectId as string
        recipe_data: Recipe creation data
        
    Returns:
        Created RecipeResponse if successful, None otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Create recipe document
        recipe_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "title": recipe_data.title,
            "description": recipe_data.description,
            "ingredients": [ingredient.dict() for ingredient in recipe_data.ingredients],
            "instructions": recipe_data.instructions,
            "prep_time": recipe_data.prep_time,
            "cook_time": recipe_data.cook_time,
            "servings": recipe_data.servings,
            "difficulty": recipe_data.difficulty,
            "tags": recipe_data.tags,
            "meal_types": recipe_data.meal_types,
            "dietary_restrictions": recipe_data.dietary_restrictions,
            "nutrition_info": recipe_data.nutrition_info.dict() if recipe_data.nutrition_info else None,
            "photo_url": recipe_data.photo_url,
            "source_url": recipe_data.source_url,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert recipe into database
        result = await recipes_collection.insert_one(recipe_doc)
        
        # Return the created recipe
        created_recipe = await recipes_collection.find_one({"_id": result.inserted_id})
        if created_recipe:
            return _convert_recipe_response(created_recipe)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating recipe for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating recipe for user {user_id}: {e}")
        return None


async def get_recipes(
    user_id: str,
    difficulty: Optional[DifficultyLevel] = None,
    meal_type: Optional[MealType] = None,
    dietary_restrictions: Optional[List[DietaryRestriction]] = None,
    tags: Optional[List[str]] = None,
    max_prep_time: Optional[int] = None,
    max_cook_time: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Optional[RecipesListResponse]:
    """
    Get recipes for a user with optional filtering and pagination
    
    Args:
        user_id: User's ObjectId as string
        difficulty: Optional difficulty filter
        meal_type: Optional meal type filter
        dietary_restrictions: Optional dietary restrictions filter
        tags: Optional tags filter
        max_prep_time: Optional maximum prep time filter
        max_cook_time: Optional maximum cook time filter
        page: Page number (1-based)
        page_size: Number of recipes per page
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        RecipesListResponse if successful, None otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        
        if difficulty:
            query_filter["difficulty"] = difficulty
        
        if meal_type:
            query_filter["meal_types"] = meal_type
        
        if dietary_restrictions:
            query_filter["dietary_restrictions"] = {"$in": dietary_restrictions}
        
        if tags:
            query_filter["tags"] = {"$in": tags}
        
        if max_prep_time is not None:
            query_filter["prep_time"] = {"$lte": max_prep_time}
        
        if max_cook_time is not None:
            query_filter["cook_time"] = {"$lte": max_cook_time}
        
        # Build sort criteria
        sort_direction = ASCENDING if sort_order.lower() == "asc" else DESCENDING
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count
        total_count = await recipes_collection.count_documents(query_filter)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get recipes with pagination
        cursor = recipes_collection.find(query_filter).sort(sort_criteria).skip(skip).limit(page_size)
        recipes = await cursor.to_list(length=page_size)
        
        # Convert to response objects
        recipe_responses = [_convert_recipe_response(recipe) for recipe in recipes]
        
        return RecipesListResponse(
            recipes=recipe_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting recipes for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting recipes for user {user_id}: {e}")
        return None


async def get_recipe_by_id(user_id: str, recipe_id: str) -> Optional[RecipeResponse]:
    """
    Get a specific recipe by ID for a user
    
    Args:
        user_id: User's ObjectId as string
        recipe_id: Recipe's ObjectId as string
        
    Returns:
        RecipeResponse if found, None otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        if not ObjectId.is_valid(recipe_id):
            return None
        
        recipe = await recipes_collection.find_one({
            "_id": ObjectId(recipe_id),
            "user_id": user_id
        })
        
        if recipe:
            return _convert_recipe_response(recipe)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting recipe {recipe_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting recipe {recipe_id} for user {user_id}: {e}")
        return None


async def update_recipe(user_id: str, recipe_id: str, update_data: RecipeUpdate) -> Optional[RecipeResponse]:
    """
    Update a recipe for a user
    
    Args:
        user_id: User's ObjectId as string
        recipe_id: Recipe's ObjectId as string
        update_data: Recipe update data
        
    Returns:
        Updated RecipeResponse if successful, None otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        if not ObjectId.is_valid(recipe_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            if field == "ingredients" and value is not None:
                update_doc[field] = [ingredient.dict() for ingredient in value]
            elif field == "nutrition_info" and value is not None:
                update_doc[field] = value.dict()
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update, return current recipe
            return await get_recipe_by_id(user_id, recipe_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update recipe
        result = await recipes_collection.update_one(
            {"_id": ObjectId(recipe_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated recipe
        return await get_recipe_by_id(user_id, recipe_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating recipe {recipe_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id} for user {user_id}: {e}")
        return None


async def delete_recipe(user_id: str, recipe_id: str) -> bool:
    """
    Delete a recipe for a user
    
    Args:
        user_id: User's ObjectId as string
        recipe_id: Recipe's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        if not ObjectId.is_valid(recipe_id):
            return False
        
        result = await recipes_collection.delete_one({
            "_id": ObjectId(recipe_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting recipe {recipe_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id} for user {user_id}: {e}")
        return False


async def search_recipes(
    user_id: str,
    search_term: str,
    difficulty: Optional[DifficultyLevel] = None,
    meal_type: Optional[MealType] = None,
    dietary_restrictions: Optional[List[DietaryRestriction]] = None,
    tags: Optional[List[str]] = None,
    max_prep_time: Optional[int] = None,
    limit: int = 20
) -> Optional[RecipeSearchResponse]:
    """
    Search recipes by title, description, and tags for a user
    
    Args:
        user_id: User's ObjectId as string
        search_term: Search term to match against recipe content
        difficulty: Optional difficulty filter
        meal_type: Optional meal type filter
        dietary_restrictions: Optional dietary restrictions filter
        tags: Optional tags filter
        max_prep_time: Optional maximum prep time filter
        limit: Maximum number of results to return
        
    Returns:
        RecipeSearchResponse with matching recipes
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Build query filter - use regex search if text index is not available
        query_filter = {
            "user_id": user_id,
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}},
                {"tags": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        # Apply additional filters
        filters_applied = {"search_term": search_term}
        
        if difficulty:
            query_filter["difficulty"] = difficulty
            filters_applied["difficulty"] = difficulty
        
        if meal_type:
            query_filter["meal_types"] = meal_type
            filters_applied["meal_type"] = meal_type
        
        if dietary_restrictions:
            query_filter["dietary_restrictions"] = {"$in": dietary_restrictions}
            filters_applied["dietary_restrictions"] = dietary_restrictions
        
        if tags:
            query_filter["tags"] = {"$in": tags}
            filters_applied["tags"] = tags
        
        if max_prep_time is not None:
            query_filter["prep_time"] = {"$lte": max_prep_time}
            filters_applied["max_prep_time"] = max_prep_time
        
        # Get total count
        total_count = await recipes_collection.count_documents(query_filter)
        
        # Get recipes sorted by relevance (created_at for now)
        cursor = recipes_collection.find(query_filter).sort("created_at", DESCENDING).limit(limit)
        recipes = await cursor.to_list(length=limit)
        
        # Convert to response objects
        recipe_responses = [_convert_recipe_response(recipe) for recipe in recipes]
        
        return RecipeSearchResponse(
            recipes=recipe_responses,
            total_count=total_count,
            search_term=search_term,
            filters_applied=filters_applied
        )
        
    except PyMongoError as e:
        logger.error(f"Database error searching recipes for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error searching recipes for user {user_id}: {e}")
        return None


async def get_recipe_stats(user_id: str) -> Optional[RecipeStatsResponse]:
    """
    Get recipe statistics for a user
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        RecipeStatsResponse if successful, None otherwise
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Get total recipes count
        total_recipes = await recipes_collection.count_documents({"user_id": user_id})
        
        # Get recipes by difficulty
        difficulty_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        difficulty_cursor = recipes_collection.aggregate(difficulty_pipeline)
        difficulty_results = await difficulty_cursor.to_list(length=None)
        recipes_by_difficulty = {result["_id"]: result["count"] for result in difficulty_results}
        
        # Get recipes by meal type (unwind array first)
        meal_type_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": {"path": "$meal_types", "preserveNullAndEmptyArrays": True}},
            {"$group": {"_id": "$meal_types", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"count": -1}}
        ]
        meal_type_cursor = recipes_collection.aggregate(meal_type_pipeline)
        meal_type_results = await meal_type_cursor.to_list(length=None)
        recipes_by_meal_type = {result["_id"]: result["count"] for result in meal_type_results}
        
        # Get average prep and cook times
        time_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "avg_prep_time": {"$avg": "$prep_time"},
                "avg_cook_time": {"$avg": "$cook_time"}
            }}
        ]
        time_cursor = recipes_collection.aggregate(time_pipeline)
        time_results = await time_cursor.to_list(length=1)
        
        average_prep_time = None
        average_cook_time = None
        if time_results:
            average_prep_time = time_results[0].get("avg_prep_time")
            average_cook_time = time_results[0].get("avg_cook_time")
        
        # Get most used tags
        tags_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": {"path": "$tags", "preserveNullAndEmptyArrays": True}},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        tags_cursor = recipes_collection.aggregate(tags_pipeline)
        tags_results = await tags_cursor.to_list(length=10)
        most_used_tags = [{"tag": result["_id"], "count": result["count"]} for result in tags_results]
        
        return RecipeStatsResponse(
            total_recipes=total_recipes,
            recipes_by_difficulty=recipes_by_difficulty,
            recipes_by_meal_type=recipes_by_meal_type,
            average_prep_time=average_prep_time,
            average_cook_time=average_cook_time,
            most_used_tags=most_used_tags
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting recipe stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting recipe stats for user {user_id}: {e}")
        return None


async def get_recipes_by_ingredients(user_id: str, ingredient_names: List[str], limit: int = 20) -> List[RecipeResponse]:
    """
    Get recipes that contain specific ingredients
    
    Args:
        user_id: User's ObjectId as string
        ingredient_names: List of ingredient names to search for
        limit: Maximum number of results to return
        
    Returns:
        List of matching RecipeResponse objects
    """
    try:
        recipes_collection = await get_collection("recipes")
        
        # Build query to find recipes containing any of the specified ingredients
        query_filter = {
            "user_id": user_id,
            "ingredients.name": {"$in": [name.lower() for name in ingredient_names]}
        }
        
        cursor = recipes_collection.find(query_filter).limit(limit).sort("created_at", DESCENDING)
        recipes = await cursor.to_list(length=limit)
        
        return [_convert_recipe_response(recipe) for recipe in recipes]
        
    except PyMongoError as e:
        logger.error(f"Database error getting recipes by ingredients for user {user_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting recipes by ingredients for user {user_id}: {e}")
        return []