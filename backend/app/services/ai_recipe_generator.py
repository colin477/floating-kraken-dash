"""
AI-powered recipe generation service using OpenAI GPT
"""

import logging
import os
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from app.models.recipes import (
    RecipeCreate, 
    RecipeIngredient, 
    DifficultyLevel, 
    MealType, 
    DietaryRestriction,
    RecipeNutrition
)
from app.utils.category_mapper import category_mapper
from app.services.recipe_validator import recipe_validator

# Configure logging
logger = logging.getLogger(__name__)


class RecipeGenerationRequest(Enum):
    """Types of recipe generation requests"""
    FROM_INGREDIENTS = "from_ingredients"
    FROM_CUISINE = "from_cuisine"
    FROM_DIETARY_NEEDS = "from_dietary_needs"


class AIRecipeGeneratorService:
    """AI-powered recipe generation service"""
    
    def __init__(self):
        self.client = None
        self.enabled = os.getenv('AI_RECIPE_GENERATION_ENABLED', 'false').lower() == 'true'
        self.fallback_enabled = os.getenv('AI_RECIPE_GENERATION_FALLBACK_ENABLED', 'true').lower() == 'true'
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.demo_mode = False
        self.api_key_configured = False
        
        # Check if OpenAI API key is configured
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != 'your-openai-api-key-here':
            self.api_key_configured = True
            logger.info("OpenAI API key is configured for recipe generation")
        else:
            logger.info("OpenAI API key not configured - using demo mode")
            self.demo_mode = True
        
        if self.enabled and OPENAI_AVAILABLE and self.api_key_configured:
            try:
                # Initialize OpenAI client
                openai.api_key = api_key
                self.client = openai
                logger.info("OpenAI client initialized successfully for recipe generation")
                self.demo_mode = False
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                logger.info("Falling back to demo mode")
                self.demo_mode = True
                if not self.fallback_enabled:
                    raise
        elif self.enabled and not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available - using demo mode")
            self.demo_mode = True
        elif not self.enabled:
            logger.info("AI recipe generation is disabled - using demo mode when needed")
            self.demo_mode = True
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current AI recipe generation service status"""
        return {
            "enabled": self.enabled,
            "demo_mode": self.demo_mode,
            "fallback_enabled": self.fallback_enabled,
            "api_key_configured": self.api_key_configured,
            "openai_available": OPENAI_AVAILABLE,
            "model": self.model,
            "client_initialized": self.client is not None
        }
    
    async def generate_recipe_from_ingredients(
        self,
        ingredients: List[str],
        cuisine_preference: Optional[str] = None,
        meal_type: Optional[MealType] = None,
        dietary_restrictions: Optional[List[DietaryRestriction]] = None,
        difficulty_preference: Optional[DifficultyLevel] = None,
        servings: int = 4,
        max_prep_time: Optional[int] = None,
        max_cook_time: Optional[int] = None
    ) -> Optional[RecipeCreate]:
        """
        Generate a recipe from a list of available ingredients using AI
        
        Args:
            ingredients: List of available ingredient names
            cuisine_preference: Optional cuisine type (e.g., "Italian", "Asian", "Mexican")
            meal_type: Optional meal type preference
            dietary_restrictions: Optional list of dietary restrictions
            difficulty_preference: Optional difficulty level preference
            servings: Number of servings (default: 4)
            max_prep_time: Maximum preparation time in minutes
            max_cook_time: Maximum cooking time in minutes
            
        Returns:
            RecipeCreate object if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("AI recipe generation is disabled, skipping generation")
            return None
        
        # If in demo mode, return mock recipe
        if self.demo_mode:
            logger.info("Using demo mode - returning mock AI-generated recipe")
            return await self._get_demo_recipe_from_ingredients(
                ingredients, cuisine_preference, meal_type, dietary_restrictions
            )
        
        if not self.client:
            logger.error("OpenAI client not initialized")
            if self.fallback_enabled:
                logger.info("Falling back to demo mode")
                return await self._get_demo_recipe_from_ingredients(
                    ingredients, cuisine_preference, meal_type, dietary_restrictions
                )
            return None
        
        try:
            # Build the prompt for recipe generation
            prompt = self._build_recipe_generation_prompt(
                ingredients=ingredients,
                cuisine_preference=cuisine_preference,
                meal_type=meal_type,
                dietary_restrictions=dietary_restrictions,
                difficulty_preference=difficulty_preference,
                servings=servings,
                max_prep_time=max_prep_time,
                max_cook_time=max_cook_time
            )
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            if not response:
                if self.fallback_enabled:
                    return await self._get_demo_recipe_from_ingredients(
                        ingredients, cuisine_preference, meal_type, dietary_restrictions
                    )
                return None
            
            # Parse the AI response into a RecipeCreate object
            recipe = await self._parse_ai_recipe_response(response, ingredients)
            
            if recipe:
                # Add AI-generated tag
                if "ai-generated" not in recipe.tags:
                    recipe.tags.append("ai-generated")
                
                # Validate and enhance the recipe
                recipe = await self._validate_and_enhance_recipe(recipe, ingredients)
                
                return recipe
            
            # If parsing failed, fall back to demo mode
            if self.fallback_enabled:
                return await self._get_demo_recipe_from_ingredients(
                    ingredients, cuisine_preference, meal_type, dietary_restrictions
                )
            return None
                
        except Exception as e:
            logger.error(f"Error generating recipe from ingredients: {e}")
            if self.fallback_enabled:
                logger.info("AI recipe generation failed, falling back to demo mode")
                return await self._get_demo_recipe_from_ingredients(
                    ingredients, cuisine_preference, meal_type, dietary_restrictions
                )
            return None
    
    def _build_recipe_generation_prompt(
        self,
        ingredients: List[str],
        cuisine_preference: Optional[str] = None,
        meal_type: Optional[MealType] = None,
        dietary_restrictions: Optional[List[DietaryRestriction]] = None,
        difficulty_preference: Optional[DifficultyLevel] = None,
        servings: int = 4,
        max_prep_time: Optional[int] = None,
        max_cook_time: Optional[int] = None
    ) -> str:
        """Build a comprehensive prompt for recipe generation"""
        
        prompt = f"""You are a professional chef and recipe developer. Create a complete, practical recipe using the following available ingredients as the main components:

AVAILABLE INGREDIENTS:
{', '.join(ingredients)}

REQUIREMENTS:
- Use as many of the provided ingredients as possible
- Create a recipe for {servings} servings
- The recipe should be practical and achievable in a home kitchen
- Include precise measurements and clear step-by-step instructions
- Ensure food safety guidelines are followed
"""
        
        if cuisine_preference:
            prompt += f"- Style: {cuisine_preference} cuisine\n"
        
        if meal_type:
            prompt += f"- Meal type: {meal_type.value}\n"
        
        if dietary_restrictions:
            restrictions = [r.value.replace('_', ' ') for r in dietary_restrictions]
            prompt += f"- Dietary restrictions: {', '.join(restrictions)}\n"
        
        if difficulty_preference:
            prompt += f"- Difficulty level: {difficulty_preference.value}\n"
        
        if max_prep_time:
            prompt += f"- Maximum prep time: {max_prep_time} minutes\n"
        
        if max_cook_time:
            prompt += f"- Maximum cook time: {max_cook_time} minutes\n"
        
        prompt += """
RESPONSE FORMAT:
Please respond with a JSON object containing the following structure:
{
    "title": "Recipe Name",
    "description": "Brief description of the dish",
    "ingredients": [
        {
            "name": "ingredient name",
            "quantity": 1.0,
            "unit": "cup/tbsp/piece/etc",
            "notes": "optional preparation notes"
        }
    ],
    "instructions": [
        "Step 1: Clear instruction",
        "Step 2: Clear instruction",
        "etc."
    ],
    "prep_time": 15,
    "cook_time": 30,
    "difficulty": "easy/medium/hard",
    "meal_types": ["breakfast/lunch/dinner/snack/dessert"],
    "dietary_restrictions": ["vegetarian/vegan/gluten_free/etc"],
    "nutrition_estimate": {
        "calories_per_serving": 350,
        "protein_g": 25,
        "carbs_g": 40,
        "fat_g": 12
    },
    "tips": "Optional cooking tips or variations"
}

IMPORTANT:
- Only use ingredients that would realistically be available in a typical kitchen alongside the provided ingredients
- Ensure measurements are realistic and practical
- Make sure cooking times are accurate
- Include food safety considerations in instructions where relevant
- The recipe should be complete and executable as written
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API with the recipe generation prompt"""
        try:
            response = await self.client.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional chef and recipe developer. You create practical, delicious recipes that are safe and achievable for home cooks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7,
                top_p=0.9
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    async def _parse_ai_recipe_response(self, response: str, original_ingredients: List[str]) -> Optional[RecipeCreate]:
        """Parse AI response into a RecipeCreate object"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = response
            
            # Parse JSON
            recipe_data = json.loads(json_str)
            
            # Convert ingredients
            ingredients = []
            for ing_data in recipe_data.get('ingredients', []):
                ingredient = RecipeIngredient(
                    name=ing_data.get('name', ''),
                    quantity=float(ing_data.get('quantity', 1.0)),
                    unit=ing_data.get('unit', 'piece'),
                    notes=ing_data.get('notes')
                )
                ingredients.append(ingredient)
            
            # Convert meal types
            meal_types = []
            for mt in recipe_data.get('meal_types', []):
                try:
                    meal_types.append(MealType(mt))
                except ValueError:
                    continue
            
            # Convert dietary restrictions
            dietary_restrictions = []
            for dr in recipe_data.get('dietary_restrictions', []):
                try:
                    dietary_restrictions.append(DietaryRestriction(dr))
                except ValueError:
                    continue
            
            # Convert difficulty
            difficulty = DifficultyLevel.MEDIUM  # default
            try:
                difficulty = DifficultyLevel(recipe_data.get('difficulty', 'medium'))
            except ValueError:
                pass
            
            # Create nutrition info if provided
            nutrition_info = None
            if 'nutrition_estimate' in recipe_data:
                nutrition_data = recipe_data['nutrition_estimate']
                nutrition_info = RecipeNutrition(
                    calories_per_serving=nutrition_data.get('calories_per_serving'),
                    protein_g=nutrition_data.get('protein_g'),
                    carbs_g=nutrition_data.get('carbs_g'),
                    fat_g=nutrition_data.get('fat_g')
                )
            
            # Create recipe
            recipe = RecipeCreate(
                title=recipe_data.get('title', 'AI Generated Recipe'),
                description=recipe_data.get('description', 'Recipe generated from available ingredients'),
                ingredients=ingredients,
                instructions=recipe_data.get('instructions', ['Prepare ingredients and cook as desired']),
                prep_time=recipe_data.get('prep_time'),
                cook_time=recipe_data.get('cook_time'),
                servings=recipe_data.get('servings', 4),
                difficulty=difficulty,
                tags=['ai-generated', 'from-ingredients'],
                meal_types=meal_types,
                dietary_restrictions=dietary_restrictions,
                nutrition_info=nutrition_info
            )
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing AI recipe response: {e}")
            logger.debug(f"Response content: {response}")
            return None
    
    async def _validate_and_enhance_recipe(self, recipe: RecipeCreate, original_ingredients: List[str]) -> RecipeCreate:
        """Validate and enhance the generated recipe using comprehensive validation"""
        try:
            # Ensure minimum requirements
            if not recipe.title:
                recipe.title = "AI Generated Recipe"
            
            if not recipe.instructions:
                recipe.instructions = ["Prepare ingredients according to the recipe", "Cook as directed", "Serve and enjoy"]
            
            if not recipe.ingredients:
                # Create basic ingredients from original list
                recipe.ingredients = [
                    RecipeIngredient(name=ing, quantity=1.0, unit="piece")
                    for ing in original_ingredients[:5]
                ]
            
            # Ensure reasonable cooking times
            if recipe.prep_time and recipe.prep_time > 180:  # 3 hours
                recipe.prep_time = 30
            
            if recipe.cook_time and recipe.cook_time > 300:  # 5 hours
                recipe.cook_time = 45
            
            # Ensure reasonable servings
            if recipe.servings < 1:
                recipe.servings = 4
            elif recipe.servings > 12:
                recipe.servings = 8
            
            # Run comprehensive recipe validation
            try:
                validation_result = await recipe_validator.validate_recipe(recipe)
                
                # Add validation tags
                if validation_result.is_valid:
                    recipe.tags.append("validated")
                else:
                    recipe.tags.append("needs-review")
                
                # Add quality score tag
                if validation_result.overall_score >= 0.8:
                    recipe.tags.append("high-quality")
                elif validation_result.overall_score >= 0.6:
                    recipe.tags.append("good-quality")
                else:
                    recipe.tags.append("basic-quality")
                
                # Apply automatic improvements based on validation
                if validation_result.safety_issues:
                    # Add safety instructions if missing
                    safety_instructions = []
                    if any('temperature' in issue.lower() for issue in validation_result.safety_issues):
                        safety_instructions.append("Cook meat to safe internal temperatures (165°F for chicken, 145°F for pork/beef)")
                    if any('wash' in issue.lower() for issue in validation_result.safety_issues):
                        safety_instructions.append("Wash all fresh produce before use")
                    
                    # Insert safety instructions at the beginning
                    recipe.instructions = safety_instructions + recipe.instructions
                
                if validation_result.practicality_issues:
                    # Add seasoning instruction if missing
                    if any('seasoning' in issue.lower() for issue in validation_result.practicality_issues):
                        recipe.instructions.append("Season with salt and pepper to taste")
                
                logger.info(f"Recipe validation completed - Overall score: {validation_result.overall_score:.2f}, Valid: {validation_result.is_valid}")
                
            except Exception as validation_error:
                logger.error(f"Recipe validation failed: {validation_error}")
                recipe.tags.append("validation-failed")
            
            # Add confidence tag based on ingredient usage
            used_ingredients = [ing.name.lower() for ing in recipe.ingredients]
            original_lower = [ing.lower() for ing in original_ingredients]
            match_count = sum(1 for orig in original_lower if any(orig in used.lower() for used in used_ingredients))
            
            if match_count >= len(original_ingredients) * 0.8:
                recipe.tags.append("high-ingredient-match")
            elif match_count >= len(original_ingredients) * 0.5:
                recipe.tags.append("good-ingredient-match")
            else:
                recipe.tags.append("partial-ingredient-match")
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error validating recipe: {e}")
            return recipe
    
    async def _get_demo_recipe_from_ingredients(
        self,
        ingredients: List[str],
        cuisine_preference: Optional[str] = None,
        meal_type: Optional[MealType] = None,
        dietary_restrictions: Optional[List[DietaryRestriction]] = None
    ) -> RecipeCreate:
        """Generate a demo recipe for testing purposes"""
        
        # Use first few ingredients to create a realistic demo recipe
        main_ingredients = ingredients[:4] if len(ingredients) >= 4 else ingredients
        
        # Create recipe title based on ingredients
        if len(main_ingredients) >= 2:
            title = f"{main_ingredients[0].title()} and {main_ingredients[1].title()} Dish"
        else:
            title = f"{main_ingredients[0].title()} Recipe" if main_ingredients else "Mixed Ingredient Recipe"
        
        if cuisine_preference:
            title = f"{cuisine_preference} {title}"
        
        # Create ingredients list
        recipe_ingredients = []
        for i, ing in enumerate(main_ingredients):
            if i == 0:  # Main ingredient
                recipe_ingredients.append(RecipeIngredient(
                    name=ing.title(),
                    quantity=1.0,
                    unit="lb" if any(meat in ing.lower() for meat in ['chicken', 'beef', 'pork', 'fish']) else "cup",
                    notes="Main ingredient"
                ))
            else:
                recipe_ingredients.append(RecipeIngredient(
                    name=ing.title(),
                    quantity=0.5 if i == 1 else 2.0,
                    unit="cup" if i == 1 else "tbsp",
                    notes=f"Supporting ingredient {i}"
                ))
        
        # Add common ingredients
        recipe_ingredients.extend([
            RecipeIngredient(name="Salt", quantity=1.0, unit="tsp", notes="To taste"),
            RecipeIngredient(name="Black pepper", quantity=0.5, unit="tsp", notes="To taste"),
            RecipeIngredient(name="Olive oil", quantity=2.0, unit="tbsp", notes="For cooking")
        ])
        
        # Create instructions
        instructions = [
            "Prepare all ingredients according to the quantities listed above",
            "Heat olive oil in a large pan over medium heat",
            f"Add {main_ingredients[0]} and cook until properly done",
        ]
        
        if len(main_ingredients) > 1:
            instructions.append(f"Add {main_ingredients[1]} and cook until tender")
        
        if len(main_ingredients) > 2:
            instructions.append(f"Stir in {main_ingredients[2]} and cook for 2-3 minutes")
        
        instructions.extend([
            "Season with salt and pepper to taste",
            "Cook for an additional 2-3 minutes to blend flavors",
            "Serve hot and enjoy your AI-generated recipe!"
        ])
        
        # Determine meal type
        if not meal_type:
            if any(breakfast in ' '.join(main_ingredients).lower() for breakfast in ['egg', 'bacon', 'toast', 'oat']):
                meal_type = MealType.BREAKFAST
            elif any(dessert in ' '.join(main_ingredients).lower() for dessert in ['chocolate', 'sugar', 'cream']):
                meal_type = MealType.DESSERT
            else:
                meal_type = MealType.DINNER
        
        # Create demo nutrition info
        nutrition_info = RecipeNutrition(
            calories_per_serving=350,
            protein_g=25,
            carbs_g=30,
            fat_g=15,
            fiber_g=5,
            sodium_mg=800
        )
        
        return RecipeCreate(
            title=title,
            description=f"AI-generated recipe using {', '.join(main_ingredients[:3])} and other available ingredients. This is a demo recipe created for testing purposes.",
            ingredients=recipe_ingredients,
            instructions=instructions,
            prep_time=15,
            cook_time=25,
            servings=4,
            difficulty=DifficultyLevel.EASY,
            tags=["ai-generated", "demo-mode", "from-ingredients"],
            meal_types=[meal_type] if meal_type else [MealType.DINNER],
            dietary_restrictions=dietary_restrictions or [],
            nutrition_info=nutrition_info
        )


# Global AI recipe generator service instance
ai_recipe_generator = AIRecipeGeneratorService()