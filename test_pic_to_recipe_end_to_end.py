#!/usr/bin/env python3
"""
Comprehensive end-to-end test script for pic-to-recipe workflow
Tests the complete flow from meal photo upload through AI recipe generation
"""

import asyncio
import json
import sys
import os
import time
import requests
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables for testing
os.environ['OCR_ENABLED'] = 'true'
os.environ['OCR_FALLBACK_ENABLED'] = 'true'
os.environ['AI_RECIPE_GENERATION_ENABLED'] = 'true'
os.environ['AI_RECIPE_GENERATION_FALLBACK_ENABLED'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key-for-demo-mode'
os.environ['GOOGLE_CLOUD_PROJECT_ID'] = 'test-project'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'test-credentials.json'

from app.services.food_vision import food_vision_service
from app.services.ai_recipe_generator import ai_recipe_generator
from app.services.recipe_validator import recipe_validator
from app.models.recipes import RecipeCreate, MealType, DietaryRestriction, DifficultyLevel


class PicToRecipeEndToEndTester:
    """Comprehensive tester for pic-to-recipe workflow"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_results = []
        self.start_time = time.time()
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Log test result with details"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    def create_test_meal_image(self, width: int = 800, height: int = 600) -> bytes:
        """Create a test meal image for testing"""
        # Create a simple test image that looks like a meal
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Draw some food-like shapes
        # Pasta (yellow oval)
        draw.ellipse([100, 200, 300, 400], fill='#FFD700', outline='#FFA500', width=3)
        
        # Tomato sauce (red circle)
        draw.ellipse([350, 150, 500, 300], fill='#FF6347', outline='#DC143C', width=2)
        
        # Meat (brown rectangle)
        draw.rectangle([200, 350, 400, 450], fill='#8B4513', outline='#654321', width=2)
        
        # Vegetables (green circles)
        draw.ellipse([500, 300, 600, 400], fill='#32CD32', outline='#228B22', width=2)
        draw.ellipse([550, 200, 650, 300], fill='#32CD32', outline='#228B22', width=2)
        
        # Add some text to make it more realistic
        try:
            # Try to add text (may fail if font not available)
            draw.text((50, 50), "Delicious Pasta Dish", fill='black')
        except:
            pass
        
        # Convert to bytes
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()

    async def test_food_vision_service_status(self) -> bool:
        """Test food vision service status and configuration"""
        try:
            status = food_vision_service.get_service_status()
            
            expected_keys = ['enabled', 'demo_mode', 'fallback_enabled', 'credentials_configured', 
                           'google_vision_available', 'client_initialized']
            
            missing_keys = [key for key in expected_keys if key not in status]
            
            self.log_test_result(
                "Food Vision Service Status",
                len(missing_keys) == 0,
                {
                    "status": status,
                    "missing_keys": missing_keys,
                    "demo_mode": status.get('demo_mode', True),
                    "enabled": status.get('enabled', False)
                }
            )
            
            return len(missing_keys) == 0
            
        except Exception as e:
            self.log_test_result(
                "Food Vision Service Status",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def test_ai_recipe_generator_status(self) -> bool:
        """Test AI recipe generator service status"""
        try:
            status = ai_recipe_generator.get_service_status()
            
            expected_keys = ['enabled', 'demo_mode', 'fallback_enabled', 'api_key_configured', 
                           'openai_available', 'model', 'client_initialized']
            
            missing_keys = [key for key in expected_keys if key not in status]
            
            self.log_test_result(
                "AI Recipe Generator Status",
                len(missing_keys) == 0,
                {
                    "status": status,
                    "missing_keys": missing_keys,
                    "demo_mode": status.get('demo_mode', True),
                    "enabled": status.get('enabled', False),
                    "model": status.get('model', 'unknown')
                }
            )
            
            return len(missing_keys) == 0
            
        except Exception as e:
            self.log_test_result(
                "AI Recipe Generator Status",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def test_food_vision_analysis(self) -> bool:
        """Test food vision analysis with test image"""
        try:
            # Create test image
            test_image = self.create_test_meal_image()
            
            # Analyze the image
            analysis_result = await food_vision_service.analyze_meal_photo(test_image)
            
            if not analysis_result:
                self.log_test_result(
                    "Food Vision Analysis",
                    False,
                    {"error": "No analysis result returned"}
                )
                return False
            
            # Validate analysis result structure
            expected_keys = ['detected_foods', 'recipe', 'confidence_score', 'analysis_timestamp']
            missing_keys = [key for key in expected_keys if key not in analysis_result]
            
            detected_foods = analysis_result.get('detected_foods', [])
            recipe_data = analysis_result.get('recipe')
            confidence_score = analysis_result.get('confidence_score', 0.0)
            
            success = (
                len(missing_keys) == 0 and
                isinstance(detected_foods, list) and
                len(detected_foods) > 0 and
                isinstance(confidence_score, (int, float)) and
                0.0 <= confidence_score <= 1.0
            )
            
            self.log_test_result(
                "Food Vision Analysis",
                success,
                {
                    "missing_keys": missing_keys,
                    "detected_foods_count": len(detected_foods),
                    "confidence_score": confidence_score,
                    "has_recipe": recipe_data is not None,
                    "detected_foods": [food.get('name', 'Unknown') for food in detected_foods[:3]],
                    "service_mode": "demo" if food_vision_service.demo_mode else "live"
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "Food Vision Analysis",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def test_ai_recipe_generation(self) -> bool:
        """Test AI recipe generation from ingredients"""
        try:
            test_ingredients = ["pasta", "tomato sauce", "ground beef", "onion", "garlic", "cheese"]
            
            # Generate recipe
            recipe = await ai_recipe_generator.generate_recipe_from_ingredients(
                ingredients=test_ingredients,
                cuisine_preference="Italian",
                meal_type=MealType.DINNER,
                dietary_restrictions=[],
                difficulty_preference=DifficultyLevel.MEDIUM,
                servings=4
            )
            
            if not recipe:
                self.log_test_result(
                    "AI Recipe Generation",
                    False,
                    {"error": "No recipe generated"}
                )
                return False
            
            # Validate recipe structure
            success = (
                hasattr(recipe, 'title') and recipe.title and
                hasattr(recipe, 'ingredients') and len(recipe.ingredients) > 0 and
                hasattr(recipe, 'instructions') and len(recipe.instructions) > 0 and
                hasattr(recipe, 'servings') and recipe.servings > 0
            )
            
            # Check ingredient matching
            recipe_ingredient_names = [ing.name.lower() for ing in recipe.ingredients]
            matched_ingredients = [ing for ing in test_ingredients 
                                 if any(ing.lower() in recipe_ing for recipe_ing in recipe_ingredient_names)]
            
            self.log_test_result(
                "AI Recipe Generation",
                success,
                {
                    "recipe_title": recipe.title,
                    "ingredients_count": len(recipe.ingredients),
                    "instructions_count": len(recipe.instructions),
                    "servings": recipe.servings,
                    "difficulty": recipe.difficulty.value if hasattr(recipe.difficulty, 'value') else str(recipe.difficulty),
                    "matched_ingredients": len(matched_ingredients),
                    "total_test_ingredients": len(test_ingredients),
                    "match_percentage": f"{len(matched_ingredients)/len(test_ingredients)*100:.1f}%",
                    "tags": recipe.tags[:5] if hasattr(recipe, 'tags') else [],
                    "service_mode": "demo" if ai_recipe_generator.demo_mode else "live"
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "AI Recipe Generation",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def test_recipe_validation(self) -> bool:
        """Test recipe validation functionality"""
        try:
            # Create a test recipe
            from app.models.recipes import RecipeIngredient
            
            test_recipe = RecipeCreate(
                title="Test Pasta Recipe",
                description="A test recipe for validation",
                ingredients=[
                    RecipeIngredient(name="Pasta", quantity=8.0, unit="oz"),
                    RecipeIngredient(name="Tomato Sauce", quantity=1.0, unit="cup"),
                    RecipeIngredient(name="Ground Beef", quantity=1.0, unit="lb"),
                    RecipeIngredient(name="Onion", quantity=1.0, unit="piece"),
                    RecipeIngredient(name="Garlic", quantity=2.0, unit="cloves")
                ],
                instructions=[
                    "Cook pasta according to package directions",
                    "Brown ground beef in a large pan",
                    "Add onion and garlic, cook until softened",
                    "Add tomato sauce and simmer",
                    "Combine with cooked pasta and serve"
                ],
                prep_time=15,
                cook_time=25,
                servings=4,
                difficulty=DifficultyLevel.EASY,
                tags=["test", "pasta", "beef"],
                meal_types=[MealType.DINNER]
            )
            
            # Validate the recipe
            validation_result = await recipe_validator.validate_recipe(test_recipe)
            
            success = (
                hasattr(validation_result, 'is_valid') and
                hasattr(validation_result, 'overall_score') and
                hasattr(validation_result, 'safety_score') and
                hasattr(validation_result, 'practicality_score') and
                isinstance(validation_result.overall_score, (int, float)) and
                0.0 <= validation_result.overall_score <= 1.0
            )
            
            self.log_test_result(
                "Recipe Validation",
                success,
                {
                    "is_valid": validation_result.is_valid if hasattr(validation_result, 'is_valid') else False,
                    "overall_score": validation_result.overall_score if hasattr(validation_result, 'overall_score') else 0.0,
                    "safety_score": validation_result.safety_score if hasattr(validation_result, 'safety_score') else 0.0,
                    "practicality_score": validation_result.practicality_score if hasattr(validation_result, 'practicality_score') else 0.0,
                    "safety_issues_count": len(validation_result.safety_issues) if hasattr(validation_result, 'safety_issues') else 0,
                    "practicality_issues_count": len(validation_result.practicality_issues) if hasattr(validation_result, 'practicality_issues') else 0,
                    "recommendation": validation_result.recommendation if hasattr(validation_result, 'recommendation') else 'unknown'
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "Recipe Validation",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    def test_meal_photo_upload_endpoint(self) -> bool:
        """Test the meal photo upload API endpoint"""
        try:
            # Create test image
            test_image = self.create_test_meal_image()
            
            # Prepare multipart form data
            files = {
                'file': ('test_meal.jpg', test_image, 'image/jpeg')
            }
            
            params = {
                'generate_recipe': 'true'
            }
            
            # Make request to the endpoint
            response = requests.post(
                f"{self.base_url}/recipes/from-photo",
                files=files,
                params=params,
                timeout=60  # Allow time for processing
            )
            
            success = response.status_code == 200
            
            response_data = {}
            if success:
                try:
                    response_data = response.json()
                except:
                    success = False
                    response_data = {"error": "Invalid JSON response"}
            
            self.log_test_result(
                "Meal Photo Upload Endpoint",
                success,
                {
                    "status_code": response.status_code,
                    "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else [],
                    "has_detected_foods": 'detected_foods' in response_data,
                    "has_recipe": 'recipe' in response_data and response_data.get('recipe') is not None,
                    "success_flag": response_data.get('success', False),
                    "confidence_score": response_data.get('confidence_score', 0.0),
                    "processing_time_ms": response_data.get('processing_time_ms', 0.0),
                    "error_message": response_data.get('error_message') if not success else None
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "Meal Photo Upload Endpoint",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    def test_ai_recipe_generation_endpoint(self) -> bool:
        """Test the AI recipe generation API endpoint"""
        try:
            request_data = {
                "ingredients": ["chicken breast", "broccoli", "rice", "soy sauce", "garlic"],
                "cuisine_preference": "Asian",
                "meal_type": "dinner",
                "dietary_restrictions": [],
                "difficulty_preference": "medium",
                "servings": 4,
                "max_prep_time": 30,
                "max_cook_time": 45,
                "include_nutrition": True
            }
            
            response = requests.post(
                f"{self.base_url}/recipes/generate-from-ingredients",
                json=request_data,
                timeout=60
            )
            
            success = response.status_code == 201  # Created status
            
            response_data = {}
            if success:
                try:
                    response_data = response.json()
                except:
                    success = False
                    response_data = {"error": "Invalid JSON response"}
            
            self.log_test_result(
                "AI Recipe Generation Endpoint",
                success,
                {
                    "status_code": response.status_code,
                    "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else [],
                    "success_flag": response_data.get('success', False),
                    "has_recipe": 'recipe' in response_data and response_data.get('recipe') is not None,
                    "confidence_score": response_data.get('confidence_score', 0.0),
                    "ingredient_match_percentage": response_data.get('ingredient_match_percentage', 0.0),
                    "processing_time_ms": response_data.get('processing_time_ms', 0.0),
                    "fallback_used": response_data.get('fallback_used', False),
                    "ai_model_used": response_data.get('ai_model_used', 'unknown'),
                    "error_message": response_data.get('error_message') if not success else None
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "AI Recipe Generation Endpoint",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    def test_ai_service_status_endpoint(self) -> bool:
        """Test the AI service status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/recipes/ai-service-status", timeout=30)
            
            success = response.status_code == 200
            
            response_data = {}
            if success:
                try:
                    response_data = response.json()
                except:
                    success = False
                    response_data = {"error": "Invalid JSON response"}
            
            expected_keys = ['service_name', 'status', 'capabilities', 'supported_features', 'limitations']
            missing_keys = [key for key in expected_keys if key not in response_data]
            
            if missing_keys:
                success = False
            
            self.log_test_result(
                "AI Service Status Endpoint",
                success,
                {
                    "status_code": response.status_code,
                    "missing_keys": missing_keys,
                    "service_name": response_data.get('service_name', 'unknown'),
                    "demo_mode": response_data.get('status', {}).get('demo_mode', True),
                    "capabilities_count": len(response_data.get('capabilities', {})),
                    "supported_features_count": len(response_data.get('supported_features', [])),
                    "limitations": response_data.get('limitations', {}),
                    "error_message": response_data.get('error_message') if not success else None
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "AI Service Status Endpoint",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling scenarios"""
        try:
            error_tests_passed = 0
            total_error_tests = 3
            
            # Test 1: Invalid image upload
            try:
                files = {'file': ('test.txt', b'not an image', 'text/plain')}
                response = requests.post(f"{self.base_url}/recipes/from-photo", files=files, timeout=30)
                if response.status_code == 400:  # Bad request expected
                    error_tests_passed += 1
            except:
                pass
            
            # Test 2: Empty ingredients list for AI generation
            try:
                request_data = {"ingredients": []}
                response = requests.post(f"{self.base_url}/recipes/generate-from-ingredients", json=request_data, timeout=30)
                if response.status_code in [400, 422]:  # Bad request or validation error expected
                    error_tests_passed += 1
            except:
                pass
            
            # Test 3: Oversized image upload
            try:
                # Create a large image (over 10MB)
                large_image = self.create_test_meal_image(3000, 3000)
                files = {'file': ('large_test.jpg', large_image, 'image/jpeg')}
                response = requests.post(f"{self.base_url}/recipes/from-photo", files=files, timeout=30)
                if response.status_code == 400:  # Bad request expected
                    error_tests_passed += 1
            except:
                pass
            
            success = error_tests_passed >= 2  # At least 2 out of 3 error tests should pass
            
            self.log_test_result(
                "Error Handling",
                success,
                {
                    "error_tests_passed": error_tests_passed,
                    "total_error_tests": total_error_tests,
                    "pass_rate": f"{error_tests_passed/total_error_tests*100:.1f}%"
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "Error Handling",
                False,
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all pic-to-recipe tests"""
        print("🚀 STARTING PIC-TO-RECIPE END-TO-END COMPREHENSIVE TESTS")
        print("=" * 80)
        
        # Service status tests
        await self.test_food_vision_service_status()
        await self.test_ai_recipe_generator_status()
        
        # Core functionality tests
        await self.test_food_vision_analysis()
        await self.test_ai_recipe_generation()
        await self.test_recipe_validation()
        
        # API endpoint tests
        self.test_meal_photo_upload_endpoint()
        self.test_ai_recipe_generation_endpoint()
        self.test_ai_service_status_endpoint()
        
        # Error handling tests
        await self.test_error_handling()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("PIC-TO-RECIPE END-TO-END TEST SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"{status}: {result['test_name']}")
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {passed_tests/total_tests*100:.1f}%")
        print(f"  Total Time: {total_time:.2f} seconds")
        
        # Determine overall success
        overall_success = passed_tests >= total_tests * 0.8  # 80% pass rate required
        
        if overall_success:
            print("\n🎉 PIC-TO-RECIPE WORKFLOW IS WORKING CORRECTLY!")
            print("   The system successfully handles meal photo analysis and AI recipe generation.")
        else:
            print("\n⚠️  SOME CRITICAL ISSUES FOUND")
            print("   Please review the failed tests above.")
        
        # Generate detailed report
        report = {
            "test_suite": "Pic-to-Recipe End-to-End Tests",
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "total_time_seconds": total_time,
            "overall_success": overall_success,
            "test_results": self.test_results,
            "system_status": {
                "food_vision_demo_mode": food_vision_service.demo_mode,
                "ai_generator_demo_mode": ai_recipe_generator.demo_mode,
                "backend_url": self.base_url
            }
        }
        
        # Save detailed report
        report_filename = f"pic_to_recipe_test_results_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        return report


async def main():
    """Main test execution function"""
    tester = PicToRecipeEndToEndTester()
    
    try:
        report = await tester.run_all_tests()
        return report['overall_success']
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Failed to run test suite: {e}")
        sys.exit(1)