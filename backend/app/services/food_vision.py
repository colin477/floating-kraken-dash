"""
Food detection service using Google Vision API
"""

import logging
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from io import BytesIO
import requests
from PIL import Image

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    vision = None

from app.models.recipes import RecipeIngredient, RecipeCreate, DifficultyLevel, MealType
from app.utils.category_mapper import category_mapper

# Configure logging
logger = logging.getLogger(__name__)

class FoodVisionService:
    """Food detection service for analyzing meal photos"""
    
    def __init__(self):
        self.client = None
        self.enabled = os.getenv('OCR_ENABLED', 'false').lower() == 'true'
        self.fallback_enabled = os.getenv('OCR_FALLBACK_ENABLED', 'true').lower() == 'true'
        self.demo_mode = False
        self.credentials_configured = False
        
        # Check if Google Vision API credentials are configured
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if project_id and credentials_path:
            self.credentials_configured = True
            logger.info("Google Vision API credentials are configured for food detection")
        else:
            logger.info("Google Vision API credentials not configured - using demo mode")
            self.demo_mode = True
        
        if self.enabled and GOOGLE_VISION_AVAILABLE and self.credentials_configured:
            try:
                # Initialize Google Vision client
                self.client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API client initialized successfully for food detection")
                self.demo_mode = False
            except Exception as e:
                logger.error(f"Failed to initialize Google Vision API client: {e}")
                logger.info("Falling back to demo mode")
                self.demo_mode = True
                if not self.fallback_enabled:
                    raise
        elif self.enabled and not GOOGLE_VISION_AVAILABLE:
            logger.warning("Google Vision API package not available - using demo mode")
            self.demo_mode = True
        elif not self.enabled:
            logger.info("Food detection is disabled - using demo mode when needed")
            self.demo_mode = True
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current food vision service status"""
        return {
            "enabled": self.enabled,
            "demo_mode": self.demo_mode,
            "fallback_enabled": self.fallback_enabled,
            "credentials_configured": self.credentials_configured,
            "google_vision_available": GOOGLE_VISION_AVAILABLE,
            "client_initialized": self.client is not None
        }
    
    async def analyze_meal_photo(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze meal photo to detect food items and generate recipe
        
        Args:
            image_data: Raw image data as bytes
            
        Returns:
            Dictionary containing detected food items and generated recipe
        """
        if not self.enabled:
            logger.warning("Food detection is disabled, skipping analysis")
            return None
        
        # If in demo mode, return mock analysis
        if self.demo_mode:
            logger.info("Using demo mode - returning mock food analysis")
            return await self._get_demo_food_analysis()
        
        if not self.client:
            logger.error("Food vision client not initialized")
            if self.fallback_enabled:
                logger.info("Falling back to demo mode")
                return await self._get_demo_food_analysis()
            return None
        
        try:
            # Process with Google Vision API
            image = vision.Image(content=image_data)
            
            # Use label detection to identify food items
            label_response = self.client.label_detection(image=image)
            
            # Use object localization for more detailed food detection
            object_response = self.client.object_localization(image=image)
            
            if label_response.error.message:
                logger.error(f"Google Vision API label detection error: {label_response.error.message}")
                if self.fallback_enabled:
                    return await self._get_demo_food_analysis()
                return None
            
            if object_response.error.message:
                logger.error(f"Google Vision API object detection error: {object_response.error.message}")
                # Continue with just label detection
            
            # Process detected labels and objects
            detected_foods = self._process_vision_results(label_response, object_response)
            
            # Generate recipe from detected foods
            recipe_data = await self._generate_recipe_from_foods(detected_foods)
            
            return {
                "detected_foods": detected_foods,
                "recipe": recipe_data,
                "confidence_score": self._calculate_overall_confidence(detected_foods),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error analyzing meal photo: {e}")
            if self.fallback_enabled:
                logger.info("Food analysis failed, falling back to demo mode")
                return await self._get_demo_food_analysis()
            return None
    
    def _process_vision_results(self, label_response, object_response) -> List[Dict[str, Any]]:
        """Process Google Vision API results to extract food items"""
        detected_foods = []
        food_keywords = {
            'pasta', 'spaghetti', 'noodles', 'rice', 'bread', 'chicken', 'beef', 'pork', 'fish',
            'salmon', 'tuna', 'shrimp', 'vegetables', 'tomato', 'onion', 'garlic', 'pepper',
            'mushroom', 'broccoli', 'carrot', 'potato', 'cheese', 'sauce', 'oil', 'butter',
            'herbs', 'basil', 'parsley', 'oregano', 'salad', 'lettuce', 'cucumber', 'avocado',
            'egg', 'bacon', 'ham', 'turkey', 'beans', 'corn', 'spinach', 'zucchini', 'eggplant',
            'bell pepper', 'chili', 'lime', 'lemon', 'apple', 'banana', 'strawberry', 'blueberry'
        }
        
        # Process labels
        for label in label_response.label_annotations:
            label_desc = label.description.lower()
            confidence = label.score
            
            # Check if label is food-related
            if any(keyword in label_desc for keyword in food_keywords) or confidence > 0.8:
                detected_foods.append({
                    "name": label.description,
                    "confidence": confidence,
                    "type": "label",
                    "category": self._categorize_food_item(label.description)
                })
        
        # Process objects
        if hasattr(object_response, 'localized_object_annotations'):
            for obj in object_response.localized_object_annotations:
                obj_name = obj.name.lower()
                confidence = obj.score
                
                # Check if object is food-related
                if any(keyword in obj_name for keyword in food_keywords) or 'food' in obj_name:
                    detected_foods.append({
                        "name": obj.name,
                        "confidence": confidence,
                        "type": "object",
                        "category": self._categorize_food_item(obj.name),
                        "bounding_box": {
                            "vertices": [(vertex.x, vertex.y) for vertex in obj.bounding_poly.normalized_vertices]
                        }
                    })
        
        # Sort by confidence and remove duplicates
        detected_foods = sorted(detected_foods, key=lambda x: x['confidence'], reverse=True)
        unique_foods = []
        seen_names = set()
        
        for food in detected_foods:
            normalized_name = food['name'].lower().strip()
            if normalized_name not in seen_names:
                unique_foods.append(food)
                seen_names.add(normalized_name)
        
        return unique_foods[:10]  # Return top 10 detected foods
    
    def _categorize_food_item(self, item_name: str) -> str:
        """Categorize food item using existing category mapper"""
        try:
            pantry_category = category_mapper.map_category(
                receipt_category=None,
                item_name=item_name
            )
            return pantry_category.value
        except Exception as e:
            logger.debug(f"Error categorizing food item '{item_name}': {e}")
            return "other"
    
    def _calculate_overall_confidence(self, detected_foods: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for the analysis"""
        if not detected_foods:
            return 0.0
        
        # Weight confidence by position (higher confidence items get more weight)
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for i, food in enumerate(detected_foods):
            weight = 1.0 / (i + 1)  # Decreasing weight for lower confidence items
            total_weighted_confidence += food['confidence'] * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    async def _generate_recipe_from_foods(self, detected_foods: List[Dict[str, Any]]) -> RecipeCreate:
        """Generate a recipe based on detected food items"""
        if not detected_foods:
            return await self._get_fallback_recipe()
        
        # Extract main ingredients from detected foods
        main_ingredients = []
        for food in detected_foods[:6]:  # Use top 6 detected foods
            # Estimate quantities based on typical recipe proportions
            quantity, unit = self._estimate_ingredient_quantity(food['name'], food['category'])
            
            main_ingredients.append(RecipeIngredient(
                name=food['name'].title(),
                quantity=quantity,
                unit=unit,
                notes=f"Detected with {food['confidence']:.1%} confidence"
            ))
        
        # Generate recipe title based on main ingredients
        title = self._generate_recipe_title(detected_foods)
        
        # Generate cooking instructions
        instructions = self._generate_cooking_instructions(detected_foods)
        
        # Determine meal type and difficulty
        meal_type = self._determine_meal_type(detected_foods)
        difficulty = self._determine_difficulty(detected_foods)
        
        # Estimate cooking times
        prep_time, cook_time = self._estimate_cooking_times(detected_foods)
        
        return RecipeCreate(
            title=title,
            description=f"AI-generated recipe based on photo analysis of your meal",
            ingredients=main_ingredients,
            instructions=instructions,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=4,  # Default serving size
            difficulty=difficulty,
            tags=["ai-generated", "photo-analysis"],
            meal_types=[meal_type] if meal_type else [],
            source_url=None
        )
    
    def _estimate_ingredient_quantity(self, ingredient_name: str, category: str) -> Tuple[float, str]:
        """Estimate quantity and unit for an ingredient"""
        ingredient_lower = ingredient_name.lower()
        
        # Quantity estimation based on ingredient type
        if any(meat in ingredient_lower for meat in ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna']):
            return (1.0, 'lb')
        elif any(veg in ingredient_lower for veg in ['tomato', 'onion', 'pepper', 'mushroom']):
            return (2.0, 'pieces')
        elif any(grain in ingredient_lower for grain in ['pasta', 'rice', 'noodles']):
            return (8.0, 'oz')
        elif any(dairy in ingredient_lower for dairy in ['cheese', 'milk', 'butter']):
            return (0.5, 'cup')
        elif any(herb in ingredient_lower for herb in ['basil', 'parsley', 'oregano']):
            return (2.0, 'tbsp')
        elif 'oil' in ingredient_lower:
            return (2.0, 'tbsp')
        elif any(sauce in ingredient_lower for sauce in ['sauce', 'dressing']):
            return (0.25, 'cup')
        else:
            return (1.0, 'cup')  # Default
    
    def _generate_recipe_title(self, detected_foods: List[Dict[str, Any]]) -> str:
        """Generate a recipe title based on detected foods"""
        if not detected_foods:
            return "Analyzed Dish"
        
        # Get the most confident food items
        main_foods = [food['name'] for food in detected_foods[:3]]
        
        # Create title based on main ingredients
        if len(main_foods) >= 2:
            return f"{main_foods[0]} and {main_foods[1]} Dish"
        else:
            return f"{main_foods[0]} Recipe"
    
    def _generate_cooking_instructions(self, detected_foods: List[Dict[str, Any]]) -> List[str]:
        """Generate cooking instructions based on detected foods"""
        instructions = [
            "Prepare all ingredients according to the quantities listed above",
            "Heat oil in a large pan or skillet over medium heat"
        ]
        
        # Add specific instructions based on detected foods
        has_meat = any('chicken' in food['name'].lower() or 'beef' in food['name'].lower() 
                      for food in detected_foods)
        has_vegetables = any('vegetable' in food['name'].lower() or 'tomato' in food['name'].lower() 
                           for food in detected_foods)
        has_pasta = any('pasta' in food['name'].lower() or 'noodle' in food['name'].lower() 
                       for food in detected_foods)
        
        if has_meat:
            instructions.append("Cook the meat until properly done and golden brown")
        
        if has_vegetables:
            instructions.append("Add vegetables and cook until tender")
        
        if has_pasta:
            instructions.append("Cook pasta according to package directions and combine with other ingredients")
        
        instructions.extend([
            "Season with salt, pepper, and any herbs or spices to taste",
            "Cook for an additional 2-3 minutes to blend flavors",
            "Serve hot and enjoy!"
        ])
        
        return instructions
    
    def _determine_meal_type(self, detected_foods: List[Dict[str, Any]]) -> Optional[MealType]:
        """Determine meal type based on detected foods"""
        food_names = [food['name'].lower() for food in detected_foods]
        
        # Breakfast indicators
        if any(item in ' '.join(food_names) for item in ['egg', 'bacon', 'toast', 'pancake', 'cereal']):
            return MealType.BREAKFAST
        
        # Dessert indicators
        if any(item in ' '.join(food_names) for item in ['cake', 'cookie', 'ice cream', 'chocolate']):
            return MealType.DESSERT
        
        # Default to dinner for substantial meals
        if any(item in ' '.join(food_names) for item in ['chicken', 'beef', 'pasta', 'rice']):
            return MealType.DINNER
        
        return MealType.LUNCH  # Default fallback
    
    def _determine_difficulty(self, detected_foods: List[Dict[str, Any]]) -> DifficultyLevel:
        """Determine recipe difficulty based on detected foods"""
        # Simple heuristic: more ingredients = higher difficulty
        if len(detected_foods) <= 3:
            return DifficultyLevel.EASY
        elif len(detected_foods) <= 6:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD
    
    def _estimate_cooking_times(self, detected_foods: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Estimate prep and cook times based on detected foods"""
        food_names = [food['name'].lower() for food in detected_foods]
        
        # Base times
        prep_time = 10
        cook_time = 15
        
        # Adjust based on ingredients
        if any(meat in ' '.join(food_names) for meat in ['chicken', 'beef', 'pork']):
            cook_time += 15
        
        if any(grain in ' '.join(food_names) for grain in ['pasta', 'rice']):
            cook_time += 10
        
        if len(detected_foods) > 5:
            prep_time += 10
        
        return prep_time, cook_time
    
    async def _get_demo_food_analysis(self) -> Dict[str, Any]:
        """Generate demo food analysis for testing purposes"""
        demo_foods = [
            {"name": "Pasta", "confidence": 0.95, "type": "label", "category": "grains"},
            {"name": "Tomato Sauce", "confidence": 0.88, "type": "label", "category": "condiments"},
            {"name": "Ground Beef", "confidence": 0.82, "type": "label", "category": "meat"},
            {"name": "Onion", "confidence": 0.76, "type": "label", "category": "produce"},
            {"name": "Garlic", "confidence": 0.71, "type": "label", "category": "produce"},
            {"name": "Parmesan Cheese", "confidence": 0.68, "type": "label", "category": "dairy"}
        ]
        
        recipe_data = await self._generate_recipe_from_foods(demo_foods)
        
        return {
            "detected_foods": demo_foods,
            "recipe": recipe_data,
            "confidence_score": 0.83,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_fallback_recipe(self) -> RecipeCreate:
        """Generate a fallback recipe when no foods are detected"""
        return RecipeCreate(
            title="Simple Meal",
            description="A basic recipe template - please customize with your ingredients",
            ingredients=[
                RecipeIngredient(name="Main ingredient", quantity=1.0, unit="piece"),
                RecipeIngredient(name="Seasoning", quantity=1.0, unit="tsp"),
                RecipeIngredient(name="Oil", quantity=1.0, unit="tbsp")
            ],
            instructions=[
                "Prepare your main ingredient",
                "Heat oil in a pan",
                "Cook the main ingredient until done",
                "Season to taste",
                "Serve hot"
            ],
            prep_time=10,
            cook_time=15,
            servings=2,
            difficulty=DifficultyLevel.EASY,
            tags=["basic", "template"],
            meal_types=[MealType.LUNCH]
        )

# Global food vision service instance
food_vision_service = FoodVisionService()