"""
Test script for the nutritional analysis system
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.nutrition_lookup_service import nutrition_lookup_service
from app.services.recipe_nutrition_service import recipe_nutrition_service
from app.models.nutrition import IngredientLookupRequest
from app.models.recipes import Recipe, RecipeIngredient, DifficultyLevel


async def test_ingredient_lookup():
    """Test ingredient nutritional lookup"""
    print("🔍 Testing ingredient lookup...")
    
    # Test common ingredients
    test_ingredients = [
        {"ingredient_name": "chicken breast", "quantity": 150, "unit": "g"},
        {"ingredient_name": "broccoli", "quantity": 100, "unit": "g"},
        {"ingredient_name": "rice", "quantity": 75, "unit": "g"},
        {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"}
    ]
    
    for ingredient_data in test_ingredients:
        request = IngredientLookupRequest(**ingredient_data)
        result = await nutrition_lookup_service.lookup_ingredient(request)
        
        print(f"  📊 {ingredient_data['ingredient_name']}: {'✅ Success' if result.success else '❌ Failed'}")
        if result.success and result.best_match:
            nutrition = result.best_match.nutrition_per_serving
            if nutrition.macronutrients.calories:
                print(f"    Calories: {nutrition.macronutrients.calories.amount:.1f}")
            if nutrition.macronutrients.protein:
                print(f"    Protein: {nutrition.macronutrients.protein.amount:.1f}g")
            print(f"    Data source: {result.data_source}")
        else:
            print(f"    Error: {result.error_message}")
        print()


async def test_recipe_analysis():
    """Test complete recipe nutritional analysis"""
    print("🍽️ Testing recipe analysis...")
    
    # Create a test recipe
    test_recipe = Recipe(
        id="test_recipe_001",
        user_id="test_user",
        title="Grilled Chicken with Broccoli and Rice",
        description="A healthy and balanced meal",
        ingredients=[
            RecipeIngredient(name="chicken breast", quantity=150, unit="g"),
            RecipeIngredient(name="broccoli", quantity=100, unit="g"),
            RecipeIngredient(name="brown rice", quantity=75, unit="g"),
            RecipeIngredient(name="olive oil", quantity=1, unit="tbsp"),
            RecipeIngredient(name="salt", quantity=0.5, unit="tsp"),
            RecipeIngredient(name="black pepper", quantity=0.25, unit="tsp")
        ],
        instructions=[
            "Season chicken breast with salt and pepper",
            "Heat olive oil in a pan and grill chicken until cooked through",
            "Steam broccoli until tender",
            "Cook rice according to package instructions",
            "Serve chicken with broccoli and rice"
        ],
        servings=1,
        difficulty=DifficultyLevel.EASY,
        prep_time=10,
        cook_time=20
    )
    
    # Analyze recipe nutrition
    analysis = await recipe_nutrition_service.analyze_recipe_nutrition(test_recipe)
    
    if analysis:
        print("  ✅ Recipe analysis successful!")
        print(f"  📈 Analysis confidence: {analysis.analysis_confidence:.2f}")
        print(f"  🥘 Ingredients analyzed: {len(analysis.ingredient_contributions)}")
        print(f"  ❓ Missing ingredients: {len(analysis.missing_ingredients)}")
        
        # Display nutrition per serving
        nutrition = analysis.nutrition_per_serving
        print("\n  📊 Nutrition per serving:")
        if nutrition.macronutrients.calories:
            print(f"    Calories: {nutrition.macronutrients.calories.amount:.0f}")
        if nutrition.macronutrients.protein:
            print(f"    Protein: {nutrition.macronutrients.protein.amount:.1f}g")
        if nutrition.macronutrients.carbohydrates:
            print(f"    Carbs: {nutrition.macronutrients.carbohydrates.amount:.1f}g")
        if nutrition.macronutrients.total_fat:
            print(f"    Fat: {nutrition.macronutrients.total_fat.amount:.1f}g")
        
        # Display dietary analysis
        dietary_analysis = await recipe_nutrition_service.analyze_dietary_compliance(test_recipe, analysis)
        print(f"\n  🏥 Health score: {dietary_analysis.health_score:.1f}/100")
        print(f"  ⚠️  Nutritional warnings: {len(dietary_analysis.nutritional_warnings)}")
        print(f"  🚫 Allergens detected: {len(dietary_analysis.allergens_present)}")
        
        if analysis.missing_ingredients:
            print(f"\n  ❌ Missing nutrition data for: {', '.join(analysis.missing_ingredients)}")
        
    else:
        print("  ❌ Recipe analysis failed!")


async def test_service_status():
    """Test service status"""
    print("🔧 Testing service status...")
    
    lookup_status = nutrition_lookup_service.get_service_status()
    print(f"  📡 Nutrition Lookup Service: {'✅ Available' if lookup_status.is_available else '❌ Unavailable'}")
    print(f"  🔑 API Key configured: {'✅ Yes' if lookup_status.api_key_configured else '❌ No (Demo mode)'}")
    print(f"  💾 Cache enabled: {'✅ Yes' if lookup_status.cache_enabled else '❌ No'}")


async def main():
    """Run all tests"""
    print("🧪 Starting Nutritional Analysis System Tests\n")
    print("=" * 50)
    
    try:
        await test_service_status()
        print("\n" + "=" * 50)
        
        await test_ingredient_lookup()
        print("=" * 50)
        
        await test_recipe_analysis()
        print("\n" + "=" * 50)
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())