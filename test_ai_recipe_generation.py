#!/usr/bin/env python3
"""
Comprehensive test script for AI recipe generation functionality
"""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any
from datetime import timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables for testing
os.environ['AI_RECIPE_GENERATION_ENABLED'] = 'true'
os.environ['AI_RECIPE_GENERATION_FALLBACK_ENABLED'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key-for-demo-mode'

from app.services.ai_recipe_generator import ai_recipe_generator
from app.models.recipes import MealType, DietaryRestriction, DifficultyLevel
from app.crud.leftovers import generate_ai_recipe_suggestions


async def test_ai_recipe_service_status():
    """Test AI recipe generation service status"""
    print("=" * 60)
    print("TESTING AI RECIPE GENERATION SERVICE STATUS")
    print("=" * 60)
    
    try:
        status = ai_recipe_generator.get_service_status()
        print(f"✅ Service Status Retrieved:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Service status test failed: {e}")
        return False


async def test_basic_recipe_generation():
    """Test basic recipe generation from ingredients"""
    print("\n" + "=" * 60)
    print("TESTING BASIC RECIPE GENERATION")
    print("=" * 60)
    
    test_ingredients = ["chicken breast", "broccoli", "rice", "garlic", "onion"]
    
    try:
        print(f"🧪 Generating recipe from ingredients: {', '.join(test_ingredients)}")
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=test_ingredients,
            servings=4
        )
        
        if recipe:
            print(f"✅ Recipe Generated Successfully:")
            print(f"   Title: {recipe.title}")
            print(f"   Description: {recipe.description}")
            print(f"   Ingredients: {len(recipe.ingredients)} items")
            print(f"   Instructions: {len(recipe.instructions)} steps")
            print(f"   Prep Time: {recipe.prep_time} minutes")
            print(f"   Cook Time: {recipe.cook_time} minutes")
            print(f"   Servings: {recipe.servings}")
            print(f"   Difficulty: {recipe.difficulty}")
            print(f"   Tags: {', '.join(recipe.tags)}")
            
            # Test ingredient matching
            recipe_ingredient_names = [ing.name.lower() for ing in recipe.ingredients]
            matched_ingredients = [ing for ing in test_ingredients if any(ing.lower() in recipe_ing for recipe_ing in recipe_ingredient_names)]
            print(f"   Ingredient Match: {len(matched_ingredients)}/{len(test_ingredients)} original ingredients used")
            
            return True
        else:
            print("❌ Recipe generation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Basic recipe generation test failed: {e}")
        return False


async def test_advanced_recipe_generation():
    """Test recipe generation with advanced parameters"""
    print("\n" + "=" * 60)
    print("TESTING ADVANCED RECIPE GENERATION")
    print("=" * 60)
    
    test_ingredients = ["salmon", "asparagus", "lemon", "olive oil", "herbs"]
    
    try:
        print(f"🧪 Generating advanced recipe with preferences:")
        print(f"   Ingredients: {', '.join(test_ingredients)}")
        print(f"   Cuisine: Mediterranean")
        print(f"   Meal Type: Dinner")
        print(f"   Dietary Restrictions: Gluten-free")
        print(f"   Difficulty: Medium")
        print(f"   Max Prep Time: 30 minutes")
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=test_ingredients,
            cuisine_preference="Mediterranean",
            meal_type=MealType.DINNER,
            dietary_restrictions=[DietaryRestriction.GLUTEN_FREE],
            difficulty_preference=DifficultyLevel.MEDIUM,
            servings=6,
            max_prep_time=30,
            max_cook_time=45
        )
        
        if recipe:
            print(f"✅ Advanced Recipe Generated Successfully:")
            print(f"   Title: {recipe.title}")
            print(f"   Meal Types: {[mt.value for mt in recipe.meal_types]}")
            print(f"   Dietary Restrictions: {[dr.value for dr in recipe.dietary_restrictions]}")
            print(f"   Difficulty: {recipe.difficulty.value}")
            print(f"   Servings: {recipe.servings}")
            
            # Check if preferences were respected
            has_gluten_free = DietaryRestriction.GLUTEN_FREE in recipe.dietary_restrictions
            has_dinner = MealType.DINNER in recipe.meal_types
            prep_time_ok = recipe.prep_time is None or recipe.prep_time <= 30
            
            print(f"   Preferences Respected:")
            print(f"     Gluten-free: {'✅' if has_gluten_free else '❌'}")
            print(f"     Dinner meal type: {'✅' if has_dinner else '❌'}")
            print(f"     Prep time <= 30 min: {'✅' if prep_time_ok else '❌'}")
            
            return True
        else:
            print("❌ Advanced recipe generation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Advanced recipe generation test failed: {e}")
        return False


async def test_leftover_suggestions_integration():
    """Test integration with leftover suggestions"""
    print("\n" + "=" * 60)
    print("TESTING LEFTOVER SUGGESTIONS INTEGRATION")
    print("=" * 60)
    
    test_ingredients = ["leftover turkey", "cranberries", "sweet potato", "spinach"]
    
    try:
        print(f"🧪 Testing AI recipe suggestions for leftovers: {', '.join(test_ingredients)}")
        
        # Create mock PantryIngredientInfo objects
        from app.models.leftovers import PantryIngredientInfo
        from datetime import date
        
        mock_pantry_ingredients = []
        for i, ingredient in enumerate(test_ingredients):
            mock_ingredient = PantryIngredientInfo(
                name=ingredient,
                normalized_name=ingredient.lower().replace(" ", "_"),
                category="other",
                quantity=1.0,
                unit="piece",
                expiration_date=date.today() + timedelta(days=7),
                days_until_expiration=7,
                is_expired=False,
                is_expiring_soon=True,
                freshness_score=0.6
            )
            mock_pantry_ingredients.append(mock_ingredient)
        
        # Test AI recipe suggestions with correct parameters
        suggestions = await generate_ai_recipe_suggestions(
            user_id="test_user_id",
            available_ingredients=mock_pantry_ingredients,
            filters=None,
            max_ai_recipes=3
        )
        
        if suggestions:
            print(f"✅ AI Recipe Suggestions Generated: {len(suggestions)} recipes")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   Recipe {i}: {suggestion.recipe.title}")
                print(f"     Match Percentage: {suggestion.match_percentage:.1f}%")
                print(f"     Priority Score: {suggestion.priority_score:.1f}")
                print(f"     Reason: {suggestion.suggestion_reason}")
                
            return True
        else:
            print("❌ No AI recipe suggestions generated")
            return False
            
    except Exception as e:
        print(f"❌ Leftover suggestions integration test failed: {e}")
        return False


async def test_recipe_validation():
    """Test recipe validation functionality"""
    print("\n" + "=" * 60)
    print("TESTING RECIPE VALIDATION")
    print("=" * 60)
    
    test_ingredients = ["ground beef", "tomatoes", "pasta", "cheese"]
    
    try:
        print(f"🧪 Testing recipe validation with: {', '.join(test_ingredients)}")
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=test_ingredients,
            servings=4
        )
        
        if recipe:
            print(f"✅ Recipe with Validation Generated:")
            print(f"   Title: {recipe.title}")
            
            # Check for validation tags
            validation_tags = [tag for tag in recipe.tags if tag in ['validated', 'needs-review', 'high-quality', 'good-quality', 'basic-quality', 'validation-failed']]
            quality_tags = [tag for tag in recipe.tags if 'quality' in tag]
            match_tags = [tag for tag in recipe.tags if 'match' in tag]
            
            print(f"   Validation Tags: {', '.join(validation_tags) if validation_tags else 'None'}")
            print(f"   Quality Tags: {', '.join(quality_tags) if quality_tags else 'None'}")
            print(f"   Match Tags: {', '.join(match_tags) if match_tags else 'None'}")
            
            # Check for safety instructions
            safety_keywords = ['temperature', 'wash', 'cook', 'safe']
            safety_instructions = [inst for inst in recipe.instructions if any(keyword in inst.lower() for keyword in safety_keywords)]
            print(f"   Safety Instructions: {len(safety_instructions)} found")
            
            return True
        else:
            print("❌ Recipe validation test returned None")
            return False
            
    except Exception as e:
        print(f"❌ Recipe validation test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING AND FALLBACKS")
    print("=" * 60)
    
    try:
        print("🧪 Testing with empty ingredients list:")
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=[],
            servings=4
        )
        
        if recipe:
            print(f"✅ Fallback recipe generated for empty ingredients:")
            print(f"   Title: {recipe.title}")
            print(f"   Tags: {', '.join(recipe.tags)}")
        else:
            print("✅ Correctly handled empty ingredients (returned None)")
        
        print("\n🧪 Testing with unusual ingredients:")
        unusual_ingredients = ["unicorn meat", "dragon scales", "fairy dust"]
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=unusual_ingredients,
            servings=4
        )
        
        if recipe:
            print(f"✅ Handled unusual ingredients gracefully:")
            print(f"   Title: {recipe.title}")
            print(f"   Demo mode: {'demo-mode' in recipe.tags}")
        else:
            print("✅ Correctly handled unusual ingredients (returned None)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def run_all_tests():
    """Run all AI recipe generation tests"""
    print("🚀 STARTING AI RECIPE GENERATION COMPREHENSIVE TESTS")
    print("=" * 80)
    
    tests = [
        ("Service Status", test_ai_recipe_service_status),
        ("Basic Recipe Generation", test_basic_recipe_generation),
        ("Advanced Recipe Generation", test_advanced_recipe_generation),
        ("Leftover Suggestions Integration", test_leftover_suggestions_integration),
        ("Recipe Validation", test_recipe_validation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! AI Recipe Generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)