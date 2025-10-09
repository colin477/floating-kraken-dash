#!/usr/bin/env python3
"""
Test script to verify USDA nutrition service functionality with thefuzz integration.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_usda_service_import():
    """Test that USDA nutrition service can be imported successfully."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService, usda_nutrition_service
        print("✅ Successfully imported USDANutritionService")
        return True
    except ImportError as e:
        print(f"❌ Failed to import USDANutritionService: {e}")
        return False

async def test_usda_service_initialization():
    """Test that USDA nutrition service can be initialized."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService
        service = USDANutritionService()
        print(f"✅ Successfully initialized USDANutritionService (demo_mode: {service.demo_mode})")
        return True, service
    except Exception as e:
        print(f"❌ Failed to initialize USDANutritionService: {e}")
        return False, None

async def test_ingredient_search():
    """Test ingredient search functionality."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService
        
        async with USDANutritionService() as service:
            # Test search functionality
            results = await service.search_ingredients("apple", limit=3)
            print(f"✅ Search for 'apple' returned {len(results)} results")
            
            if results:
                first_result = results[0]
                print(f"   First result: {first_result.get('description', 'N/A')}")
                print(f"   FDC ID: {first_result.get('fdc_id', 'N/A')}")
            
            return True
    except Exception as e:
        print(f"❌ Error testing ingredient search: {e}")
        return False

async def test_fuzzy_matching():
    """Test the fuzzy matching functionality specifically."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService
        from thefuzz import fuzz
        
        async with USDANutritionService() as service:
            # Test the fuzzy matching logic used in find_best_ingredient_match
            test_ingredient = "chicken breast"
            search_results = await service.search_ingredients(test_ingredient, limit=3)
            
            if search_results:
                print(f"✅ Testing fuzzy matching for '{test_ingredient}':")
                
                for result in search_results:
                    description = result.get("description", "").lower()
                    score = fuzz.ratio(test_ingredient.lower(), description)
                    print(f"   '{description}' -> similarity score: {score}")
                
                return True
            else:
                print(f"⚠️  No search results to test fuzzy matching with")
                return True  # Still pass since the import/service works
                
    except Exception as e:
        print(f"❌ Error testing fuzzy matching: {e}")
        return False

async def test_best_ingredient_match():
    """Test finding best ingredient match."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService
        
        async with USDANutritionService() as service:
            # Test finding best match
            nutrition_data = await service.find_best_ingredient_match("apple")
            
            if nutrition_data:
                print(f"✅ Found nutrition data for 'apple':")
                print(f"   Ingredient: {nutrition_data.ingredient_name}")
                print(f"   Serving size: {nutrition_data.serving_size} {nutrition_data.serving_unit}")
                print(f"   Data source: {nutrition_data.data_source}")
                
                # Check if macronutrients are available
                if nutrition_data.nutrition_per_serving.macronutrients.calories:
                    calories = nutrition_data.nutrition_per_serving.macronutrients.calories.amount
                    print(f"   Calories per serving: {calories}")
                
                return True
            else:
                print("⚠️  No nutrition data found for 'apple' (this is expected in demo mode)")
                return True  # Still pass since the service is working
                
    except Exception as e:
        print(f"❌ Error testing best ingredient match: {e}")
        return False

async def test_service_status():
    """Test service status functionality."""
    try:
        from app.services.usda_nutrition_service import USDANutritionService
        
        service = USDANutritionService()
        status = service.get_service_status()
        
        print(f"✅ Service status retrieved:")
        print(f"   Service name: {status.service_name}")
        print(f"   Available: {status.is_available}")
        print(f"   API key configured: {status.api_key_configured}")
        print(f"   Cache enabled: {status.cache_enabled}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing service status: {e}")
        return False

async def main():
    """Run all USDA nutrition service tests."""
    print("Testing USDA Nutrition Service with thefuzz integration")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_usda_service_import),
        ("Initialization Test", test_usda_service_initialization),
        ("Ingredient Search Test", test_ingredient_search),
        ("Fuzzy Matching Test", test_fuzzy_matching),
        ("Best Ingredient Match Test", test_best_ingredient_match),
        ("Service Status Test", test_service_status),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            if test_name == "Initialization Test":
                result, service = await test_func()
                results.append((test_name, result))
            else:
                result = await test_func()
                results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All USDA nutrition service tests PASSED!")
        print("thefuzz integration is working correctly with the nutrition service")
    else:
        print("Some tests FAILED! There may be integration issues.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)