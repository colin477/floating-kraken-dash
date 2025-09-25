"""
Test script for Sprint 5 implementation - Meal Plans and Shopping Lists
"""

import asyncio
import sys
import os
from datetime import date, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongo, close_mongo_connection
from app.models.meal_plans import MealPlanCreate, MealPlanGenerationRequest, MealType, DayOfWeek
from app.models.shopping_lists import ShoppingListCreate, ShoppingItem, ShoppingListCategory, ShoppingListItemStatus
from app.crud.meal_plans import create_meal_plan, generate_meal_plan, get_meal_plans
from app.crud.shopping_lists import create_shopping_list, get_shopping_lists


async def test_meal_plan_functionality():
    """Test meal plan CRUD operations"""
    print("🍽️ Testing Meal Plan Functionality...")
    
    # Test user ID (mock)
    test_user_id = "507f1f77bcf86cd799439011"
    
    try:
        # Test 1: Create a basic meal plan
        print("  ✅ Test 1: Creating basic meal plan...")
        meal_plan_data = MealPlanCreate(
            title="Test Weekly Meal Plan",
            description="A test meal plan for Sprint 5",
            week_starting=date.today() + timedelta(days=7),
            budget_target=100.0,
            preferences={"test": True}
        )
        
        created_meal_plan = await create_meal_plan(test_user_id, meal_plan_data)
        if created_meal_plan:
            print(f"    ✅ Created meal plan: {created_meal_plan.title}")
            meal_plan_id = created_meal_plan.id
        else:
            print("    ❌ Failed to create meal plan")
            return False
        
        # Test 2: Generate AI meal plan
        print("  ✅ Test 2: Generating AI meal plan...")
        generation_request = MealPlanGenerationRequest(
            week_starting=date.today() + timedelta(days=14),
            budget_target=80.0,
            meal_types=[MealType.DINNER],
            days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY],
            servings_per_meal=4,
            use_pantry_items=True,
            dietary_restrictions=["vegetarian"],
            cuisine_preferences=["italian", "mexican"]
        )
        
        generated_plan = await generate_meal_plan(test_user_id, generation_request)
        if generated_plan and generated_plan.success:
            print(f"    ✅ Generated meal plan: {generated_plan.title}")
            print(f"    📊 Generated {generated_plan.meals_generated} meals and {generated_plan.shopping_items_generated} shopping items")
            print(f"    💰 Total estimated cost: ${generated_plan.total_estimated_cost}")
        else:
            print("    ❌ Failed to generate meal plan")
            return False
        
        # Test 3: Get meal plans
        print("  ✅ Test 3: Retrieving meal plans...")
        meal_plans_list = await get_meal_plans(test_user_id, page=1, page_size=10)
        if meal_plans_list:
            print(f"    ✅ Retrieved {meal_plans_list.total_count} meal plans")
        else:
            print("    ❌ Failed to retrieve meal plans")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error in meal plan testing: {e}")
        return False


async def test_shopping_list_functionality():
    """Test shopping list CRUD operations"""
    print("🛒 Testing Shopping List Functionality...")
    
    # Test user ID (mock)
    test_user_id = "507f1f77bcf86cd799439011"
    
    try:
        # Test 1: Create a shopping list with items
        print("  ✅ Test 1: Creating shopping list with items...")
        
        # Create some test shopping items
        test_items = [
            ShoppingItem(
                id="item1",
                name="Chicken Breast",
                quantity=2.0,
                unit="lbs",
                category=ShoppingListCategory.MEAT,
                estimated_price=8.99,
                store="Local Grocery",
                status=ShoppingListItemStatus.PENDING,
                notes="Organic preferred"
            ),
            ShoppingItem(
                id="item2",
                name="Broccoli",
                quantity=1.0,
                unit="head",
                category=ShoppingListCategory.PRODUCE,
                estimated_price=2.49,
                store="Local Grocery",
                status=ShoppingListItemStatus.PENDING
            ),
            ShoppingItem(
                id="item3",
                name="Rice",
                quantity=1.0,
                unit="bag",
                category=ShoppingListCategory.GRAINS,
                estimated_price=3.99,
                store="Local Grocery",
                status=ShoppingListItemStatus.PENDING
            )
        ]
        
        shopping_list_data = ShoppingListCreate(
            title="Test Weekly Shopping",
            description="A test shopping list for Sprint 5",
            items=test_items,
            stores=["Local Grocery", "Walmart"],
            budget_limit=50.0,
            shopping_date=date.today() + timedelta(days=2),
            tags=["weekly", "test"]
        )
        
        created_shopping_list = await create_shopping_list(test_user_id, shopping_list_data)
        if created_shopping_list:
            print(f"    ✅ Created shopping list: {created_shopping_list.title}")
            print(f"    📊 Items: {created_shopping_list.items_count}")
            print(f"    💰 Estimated cost: ${created_shopping_list.total_estimated_cost}")
            shopping_list_id = created_shopping_list.id
        else:
            print("    ❌ Failed to create shopping list")
            return False
        
        # Test 2: Get shopping lists
        print("  ✅ Test 2: Retrieving shopping lists...")
        shopping_lists_result = await get_shopping_lists(test_user_id, page=1, page_size=10)
        if shopping_lists_result:
            print(f"    ✅ Retrieved {shopping_lists_result.total_count} shopping lists")
        else:
            print("    ❌ Failed to retrieve shopping lists")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error in shopping list testing: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Sprint 5 Implementation Tests...")
    print("=" * 50)
    
    try:
        # Connect to database
        print("📡 Connecting to database...")
        await connect_to_mongo()
        print("✅ Database connected successfully")
        
        # Run tests
        meal_plan_success = await test_meal_plan_functionality()
        shopping_list_success = await test_shopping_list_functionality()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"  Meal Plans: {'✅ PASSED' if meal_plan_success else '❌ FAILED'}")
        print(f"  Shopping Lists: {'✅ PASSED' if shopping_list_success else '❌ FAILED'}")
        
        if meal_plan_success and shopping_list_success:
            print("\n🎉 All Sprint 5 tests PASSED! Implementation is ready.")
            return True
        else:
            print("\n⚠️  Some tests FAILED. Please check the implementation.")
            return False
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    
    finally:
        # Close database connection
        await close_mongo_connection()
        print("📡 Database connection closed")


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)