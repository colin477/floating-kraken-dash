#!/usr/bin/env python3
"""
Quick test for AI recipe generation functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables for testing
os.environ['AI_RECIPE_GENERATION_ENABLED'] = 'true'
os.environ['AI_RECIPE_GENERATION_FALLBACK_ENABLED'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key-for-demo-mode'

async def quick_test():
    """Quick test of AI recipe generation"""
    try:
        from app.services.ai_recipe_generator import ai_recipe_generator
        
        print("🧪 Quick AI Recipe Generation Test")
        print("=" * 50)
        
        # Test service status
        status = ai_recipe_generator.get_service_status()
        print(f"Service Status:")
        print(f"  Enabled: {status['enabled']}")
        print(f"  Demo Mode: {status['demo_mode']}")
        print(f"  OpenAI Available: {status['openai_available']}")
        
        # Test basic recipe generation
        print(f"\n🍳 Generating recipe from ingredients...")
        test_ingredients = ["chicken", "rice", "broccoli"]
        
        recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
            ingredients=test_ingredients,
            servings=4
        )
        
        if recipe:
            print(f"✅ Recipe Generated Successfully!")
            print(f"  Title: {recipe.title}")
            print(f"  Description: {recipe.description}")
            print(f"  Ingredients: {len(recipe.ingredients)} items")
            print(f"  Instructions: {len(recipe.instructions)} steps")
            print(f"  Tags: {', '.join(recipe.tags)}")
            return True
        else:
            print(f"❌ Recipe generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        sys.exit(1)