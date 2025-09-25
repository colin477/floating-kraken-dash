"""
CRUD operations for meal plan management
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError
import random

from app.database import get_collection
from app.models.meal_plans import (
    MealPlan,
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    MealPlansListResponse,
    MealPlanGenerationRequest,
    MealPlanGenerationResponse,
    MealPlanStatsResponse,
    PlannedMeal,
    ShoppingListItem,
    MealType,
    DayOfWeek,
    MealPlanStatus
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_meal_plan_indexes():
    """
    Create database indexes for meal plans collection
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        # Create indexes for efficient querying
        await meal_plans_collection.create_index([("user_id", 1)])
        await meal_plans_collection.create_index([("user_id", 1), ("week_starting", 1)])
        await meal_plans_collection.create_index([("user_id", 1), ("status", 1)])
        await meal_plans_collection.create_index([("created_at", -1)])
        
        logger.info("Created meal plan indexes")
        return True
    except Exception as e:
        logger.error(f"Error creating meal plan indexes: {e}")
        return False


async def create_meal_plan(user_id: str, meal_plan_data: MealPlanCreate) -> Optional[MealPlanResponse]:
    """
    Create a new meal plan for a user
    
    Args:
        user_id: User's ObjectId as string
        meal_plan_data: Meal plan creation data
        
    Returns:
        Created MealPlanResponse object if successful, None otherwise
    """
    try:
        logger.info(f"Creating meal plan for user {user_id} with data: {meal_plan_data}")
        meal_plans_collection = await get_collection("meal_plans")
        logger.info("Got meal_plans collection")
        
        # Create meal plan document (convert types for MongoDB compatibility)
        meal_plan_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "title": meal_plan_data.title,
            "description": meal_plan_data.description,
            "week_starting": datetime.combine(meal_plan_data.week_starting, datetime.min.time()),  # Convert date to datetime
            "status": MealPlanStatus.DRAFT.value,  # Convert enum to string
            "meals": [],
            "shopping_list": [],
            "total_estimated_cost": 0.0,
            "budget_target": meal_plan_data.budget_target,
            "preferences_used": meal_plan_data.preferences or {},
            "generation_notes": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        logger.info(f"Created meal plan document: {meal_plan_doc}")
        
        # Insert meal plan into database
        result = await meal_plans_collection.insert_one(meal_plan_doc)
        logger.info(f"Inserted meal plan with ID: {result.inserted_id}")
        
        # Return the created meal plan
        created_meal_plan = await meal_plans_collection.find_one({"_id": result.inserted_id})
        logger.info(f"Retrieved created meal plan: {created_meal_plan}")
        
        if created_meal_plan:
            # Convert ObjectId to string for the response
            created_meal_plan["id"] = str(created_meal_plan["_id"])
            del created_meal_plan["_id"]
            
            # Convert datetime back to date for the response model
            if isinstance(created_meal_plan["week_starting"], datetime):
                created_meal_plan["week_starting"] = created_meal_plan["week_starting"].date()
            
            # Ensure all required fields are present with defaults
            created_meal_plan.setdefault("meals_count", 0)
            created_meal_plan.setdefault("shopping_items_count", 0)
            created_meal_plan.setdefault("days_covered", [])
            
            logger.info(f"About to create MealPlanResponse with: {created_meal_plan}")
            response = MealPlanResponse(**created_meal_plan)
            logger.info(f"Successfully created MealPlanResponse: {response}")
            return response
        
        logger.error("Failed to retrieve created meal plan from database")
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating meal plan for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating meal plan for user {user_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None


async def get_meal_plans(
    user_id: str,
    status: Optional[MealPlanStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Optional[MealPlansListResponse]:
    """
    Get meal plans for a user with filtering and pagination
    
    Args:
        user_id: User's ObjectId as string
        status: Filter by meal plan status
        start_date: Filter by week starting date (from)
        end_date: Filter by week starting date (to)
        page: Page number (1-based)
        page_size: Number of items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        MealPlansListResponse with paginated results
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        
        if status:
            query_filter["status"] = status
            
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query_filter["week_starting"] = date_filter
        
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Build sort criteria
        sort_direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count
        total_count = await meal_plans_collection.count_documents(query_filter)
        
        # Get paginated results
        cursor = meal_plans_collection.find(query_filter).sort(sort_criteria).skip(skip).limit(page_size)
        meal_plans = await cursor.to_list(length=page_size)
        
        # Convert to response objects
        meal_plan_responses = []
        for meal_plan in meal_plans:
            meal_plan["id"] = str(meal_plan["_id"])
            del meal_plan["_id"]
            
            # Convert datetime back to date for the response model
            if isinstance(meal_plan["week_starting"], datetime):
                meal_plan["week_starting"] = meal_plan["week_starting"].date()
            
            # Ensure all required fields are present with defaults
            meal_plan.setdefault("meals_count", 0)
            meal_plan.setdefault("shopping_items_count", 0)
            meal_plan.setdefault("days_covered", [])
            
            meal_plan_responses.append(MealPlanResponse(**meal_plan))
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return MealPlansListResponse(
            meal_plans=meal_plan_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting meal plans for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting meal plans for user {user_id}: {e}")
        return None


async def get_meal_plan_by_id(user_id: str, meal_plan_id: str) -> Optional[MealPlanResponse]:
    """
    Get a specific meal plan by ID
    
    Args:
        user_id: User's ObjectId as string
        meal_plan_id: Meal plan's ObjectId as string
        
    Returns:
        MealPlanResponse object if found, None otherwise
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        if not ObjectId.is_valid(meal_plan_id):
            return None
            
        meal_plan = await meal_plans_collection.find_one({
            "_id": ObjectId(meal_plan_id),
            "user_id": user_id
        })
        
        if meal_plan:
            meal_plan["id"] = str(meal_plan["_id"])
            del meal_plan["_id"]
            
            # Convert datetime back to date for the response model
            if isinstance(meal_plan["week_starting"], datetime):
                meal_plan["week_starting"] = meal_plan["week_starting"].date()
            
            # Ensure all required fields are present with defaults
            meal_plan.setdefault("meals_count", 0)
            meal_plan.setdefault("shopping_items_count", 0)
            meal_plan.setdefault("days_covered", [])
            
            return MealPlanResponse(**meal_plan)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting meal plan {meal_plan_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting meal plan {meal_plan_id} for user {user_id}: {e}")
        return None


async def update_meal_plan(user_id: str, meal_plan_id: str, update_data: MealPlanUpdate) -> Optional[MealPlanResponse]:
    """
    Update an existing meal plan
    
    Args:
        user_id: User's ObjectId as string
        meal_plan_id: Meal plan's ObjectId as string
        update_data: Meal plan update data
        
    Returns:
        Updated MealPlanResponse object if successful, None otherwise
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        if not ObjectId.is_valid(meal_plan_id):
            return None
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            if field == "meals" and value:
                # Convert PlannedMeal objects to dicts (handle both objects and dicts)
                update_doc[field] = [meal.dict() if hasattr(meal, 'dict') else meal for meal in value]
            elif field == "shopping_list" and value:
                # Convert ShoppingListItem objects to dicts (handle both objects and dicts)
                update_doc[field] = [item.dict() if hasattr(item, 'dict') else item for item in value]
            else:
                update_doc[field] = value
        
        if not update_doc:
            # No fields to update
            return await get_meal_plan_by_id(user_id, meal_plan_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update meal plan
        result = await meal_plans_collection.update_one(
            {"_id": ObjectId(meal_plan_id), "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated meal plan
        return await get_meal_plan_by_id(user_id, meal_plan_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating meal plan {meal_plan_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating meal plan {meal_plan_id} for user {user_id}: {e}")
        return None


async def delete_meal_plan(user_id: str, meal_plan_id: str) -> bool:
    """
    Delete a meal plan
    
    Args:
        user_id: User's ObjectId as string
        meal_plan_id: Meal plan's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        if not ObjectId.is_valid(meal_plan_id):
            return False
        
        result = await meal_plans_collection.delete_one({
            "_id": ObjectId(meal_plan_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0
        
    except PyMongoError as e:
        logger.error(f"Database error deleting meal plan {meal_plan_id} for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting meal plan {meal_plan_id} for user {user_id}: {e}")
        return False


async def generate_meal_plan(user_id: str, generation_request: MealPlanGenerationRequest) -> Optional[MealPlanGenerationResponse]:
    """
    Generate an AI-powered meal plan (mock implementation for now)
    
    Args:
        user_id: User's ObjectId as string
        generation_request: Meal plan generation parameters
        
    Returns:
        MealPlanGenerationResponse if successful, None otherwise
    """
    try:
        # Mock AI meal plan generation
        # In a real implementation, this would integrate with AI services
        
        # Get user's pantry items and recipes for context
        pantry_collection = await get_collection("pantry_items")
        recipes_collection = await get_collection("recipes")
        
        pantry_items = await pantry_collection.find({"user_id": user_id}).to_list(length=100)
        user_recipes = await recipes_collection.find({"user_id": user_id}).to_list(length=50)
        
        # Generate mock meals
        mock_recipes = [
            {"title": "Chicken Stir Fry", "prep_time": 15, "cook_time": 20, "ingredients": ["chicken", "vegetables", "soy sauce"]},
            {"title": "Pasta Primavera", "prep_time": 10, "cook_time": 15, "ingredients": ["pasta", "vegetables", "olive oil"]},
            {"title": "Beef Tacos", "prep_time": 20, "cook_time": 15, "ingredients": ["ground beef", "tortillas", "cheese"]},
            {"title": "Salmon with Rice", "prep_time": 10, "cook_time": 25, "ingredients": ["salmon", "rice", "vegetables"]},
            {"title": "Vegetable Curry", "prep_time": 15, "cook_time": 30, "ingredients": ["vegetables", "curry paste", "coconut milk"]},
            {"title": "Grilled Chicken Salad", "prep_time": 20, "cook_time": 15, "ingredients": ["chicken", "lettuce", "tomatoes"]},
            {"title": "Spaghetti Bolognese", "prep_time": 15, "cook_time": 45, "ingredients": ["pasta", "ground beef", "tomato sauce"]}
        ]
        
        planned_meals = []
        shopping_items = []
        total_cost = 0.0
        
        # Generate meals for requested days and meal types
        for day in generation_request.days:
            for meal_type in generation_request.meal_types:
                recipe = random.choice(mock_recipes)
                meal_id = str(uuid.uuid4())
                
                planned_meal = PlannedMeal(
                    id=meal_id,
                    day=day,
                    meal_type=meal_type,
                    recipe_id=None,  # Mock - would reference actual recipe
                    recipe_title=recipe["title"],
                    servings=generation_request.servings_per_meal,
                    estimated_prep_time=recipe["prep_time"],
                    estimated_cook_time=recipe["cook_time"],
                    notes=f"Generated meal for {day.value} {meal_type.value}",
                    ingredients_needed=[{"name": ing, "quantity": 1, "unit": "serving"} for ing in recipe["ingredients"]]
                )
                planned_meals.append(planned_meal)
                
                # Generate shopping list items
                for ingredient in recipe["ingredients"]:
                    item_id = str(uuid.uuid4())
                    estimated_price = random.uniform(2.0, 8.0)
                    total_cost += estimated_price
                    
                    shopping_item = ShoppingListItem(
                        id=item_id,
                        name=ingredient,
                        quantity=1.0,
                        unit="item",
                        category="other",
                        estimated_price=estimated_price,
                        store="Local Grocery",
                        purchased=False,
                        meal_ids=[meal_id],
                        notes=f"For {recipe['title']}"
                    )
                    shopping_items.append(shopping_item)
        
        # Create the meal plan
        meal_plan_title = f"AI Generated Plan - Week of {generation_request.week_starting.strftime('%B %d, %Y')}"
        
        meal_plan_create = MealPlanCreate(
            title=meal_plan_title,
            description="AI-generated meal plan based on your preferences and pantry items",
            week_starting=generation_request.week_starting,
            budget_target=generation_request.budget_target,
            preferences={
                "meal_types": [mt.value for mt in generation_request.meal_types],
                "days": [d.value for d in generation_request.days],
                "servings_per_meal": generation_request.servings_per_meal,
                "use_pantry_items": generation_request.use_pantry_items,
                "dietary_restrictions": generation_request.dietary_restrictions,
                "cuisine_preferences": generation_request.cuisine_preferences
            }
        )
        
        # Create the meal plan
        created_meal_plan = await create_meal_plan(user_id, meal_plan_create)
        if not created_meal_plan:
            return None
        
        # Update with generated meals and shopping list
        update_data = MealPlanUpdate(
            meals=planned_meals,
            shopping_list=shopping_items,
            total_estimated_cost=round(total_cost, 2),
            status=MealPlanStatus.ACTIVE
        )
        
        updated_meal_plan = await update_meal_plan(user_id, created_meal_plan.id, update_data)
        if not updated_meal_plan:
            return None
        
        # Generate response
        warnings = []
        if generation_request.budget_target and total_cost > generation_request.budget_target:
            warnings.append(f"Generated plan exceeds budget target by ${total_cost - generation_request.budget_target:.2f}")
        
        return MealPlanGenerationResponse(
            meal_plan_id=updated_meal_plan.id,
            title=meal_plan_title,
            meals_generated=len(planned_meals),
            shopping_items_generated=len(shopping_items),
            total_estimated_cost=round(total_cost, 2),
            generation_notes=f"Generated {len(planned_meals)} meals for {len(generation_request.days)} days. Used mock AI logic - integrate with real AI service for production.",
            success=True,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error generating meal plan for user {user_id}: {e}")
        return None


async def get_meal_plan_stats(user_id: str) -> Optional[MealPlanStatsResponse]:
    """
    Get meal plan statistics for a user
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        MealPlanStatsResponse with statistics
    """
    try:
        meal_plans_collection = await get_collection("meal_plans")
        
        # Get all meal plans for the user
        meal_plans = await meal_plans_collection.find({"user_id": user_id}).to_list(length=None)
        
        if not meal_plans:
            return MealPlanStatsResponse(
                total_meal_plans=0,
                active_meal_plans=0,
                completed_meal_plans=0,
                average_weekly_cost=None,
                most_planned_meal_type=None,
                most_planned_day=None,
                total_meals_planned=0,
                budget_adherence_rate=None
            )
        
        # Calculate statistics
        total_meal_plans = len(meal_plans)
        active_meal_plans = len([mp for mp in meal_plans if mp.get("status") == MealPlanStatus.ACTIVE])
        completed_meal_plans = len([mp for mp in meal_plans if mp.get("status") == MealPlanStatus.COMPLETED])
        
        # Calculate average weekly cost
        costs = [mp.get("total_estimated_cost", 0) for mp in meal_plans if mp.get("total_estimated_cost", 0) > 0]
        average_weekly_cost = sum(costs) / len(costs) if costs else None
        
        # Count meal types and days
        meal_type_counts = {}
        day_counts = {}
        total_meals_planned = 0
        
        for meal_plan in meal_plans:
            meals = meal_plan.get("meals", [])
            total_meals_planned += len(meals)
            
            for meal in meals:
                meal_type = meal.get("meal_type")
                day = meal.get("day")
                
                if meal_type:
                    meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1
                if day:
                    day_counts[day] = day_counts.get(day, 0) + 1
        
        most_planned_meal_type = max(meal_type_counts, key=meal_type_counts.get) if meal_type_counts else None
        most_planned_day = max(day_counts, key=day_counts.get) if day_counts else None
        
        # Calculate budget adherence rate
        plans_with_budget = [mp for mp in meal_plans if mp.get("budget_target") and mp.get("total_estimated_cost")]
        if plans_with_budget:
            within_budget = len([mp for mp in plans_with_budget 
                               if mp.get("total_estimated_cost", 0) <= mp.get("budget_target", 0)])
            budget_adherence_rate = (within_budget / len(plans_with_budget)) * 100
        else:
            budget_adherence_rate = None
        
        return MealPlanStatsResponse(
            total_meal_plans=total_meal_plans,
            active_meal_plans=active_meal_plans,
            completed_meal_plans=completed_meal_plans,
            average_weekly_cost=round(average_weekly_cost, 2) if average_weekly_cost else None,
            most_planned_meal_type=most_planned_meal_type,
            most_planned_day=most_planned_day,
            total_meals_planned=total_meals_planned,
            budget_adherence_rate=round(budget_adherence_rate, 1) if budget_adherence_rate else None
        )
        
    except PyMongoError as e:
        logger.error(f"Database error getting meal plan stats for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting meal plan stats for user {user_id}: {e}")
        return None