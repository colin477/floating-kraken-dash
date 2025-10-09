"""
Recipe normalization service for converting scraped recipe data to database schema
"""

import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.recipes import (
    RecipeCreate, 
    RecipeIngredient, 
    RecipeNutrition, 
    DifficultyLevel, 
    MealType, 
    DietaryRestriction
)
from app.services.recipe_validator import recipe_validator

# Configure logging
logger = logging.getLogger(__name__)


class RecipeNormalizerService:
    """Service for normalizing scraped recipe data to database schema"""
    
    def __init__(self):
        # Unit conversion mappings
        self.unit_conversions = {
            # Volume conversions to standard units
            'cups': 'cup',
            'c': 'cup',
            'cup': 'cup',
            'tablespoons': 'tbsp',
            'tablespoon': 'tbsp',
            'tbsp': 'tbsp',
            'tbs': 'tbsp',
            'teaspoons': 'tsp',
            'teaspoon': 'tsp',
            'tsp': 'tsp',
            'fluid ounces': 'fl oz',
            'fl oz': 'fl oz',
            'ounces': 'oz',
            'oz': 'oz',
            'pints': 'pint',
            'pint': 'pint',
            'quarts': 'quart',
            'quart': 'quart',
            'gallons': 'gallon',
            'gallon': 'gallon',
            'liters': 'liter',
            'liter': 'liter',
            'l': 'liter',
            'milliliters': 'ml',
            'ml': 'ml',
            
            # Weight conversions
            'pounds': 'lb',
            'pound': 'lb',
            'lbs': 'lb',
            'lb': 'lb',
            'grams': 'g',
            'gram': 'g',
            'g': 'g',
            'kilograms': 'kg',
            'kilogram': 'kg',
            'kg': 'kg',
            
            # Count units
            'pieces': 'piece',
            'piece': 'piece',
            'items': 'item',
            'item': 'item',
            'cloves': 'clove',
            'clove': 'clove',
            'slices': 'slice',
            'slice': 'slice',
            'strips': 'strip',
            'strip': 'strip',
            'leaves': 'leaf',
            'leaf': 'leaf',
            'sprigs': 'sprig',
            'sprig': 'sprig',
            'stalks': 'stalk',
            'stalk': 'stalk',
            'bunches': 'bunch',
            'bunch': 'bunch',
            'packages': 'package',
            'package': 'package',
            'cans': 'can',
            'can': 'can',
            'bottles': 'bottle',
            'bottle': 'bottle',
            'jars': 'jar',
            'jar': 'jar',
            'boxes': 'box',
            'box': 'box',
            'bags': 'bag',
            'bag': 'bag',
        }
        
        # Dietary restriction detection keywords
        self.dietary_keywords = {
            DietaryRestriction.VEGETARIAN: [
                'vegetarian', 'veggie', 'no meat', 'meatless'
            ],
            DietaryRestriction.VEGAN: [
                'vegan', 'plant-based', 'dairy-free', 'egg-free'
            ],
            DietaryRestriction.GLUTEN_FREE: [
                'gluten-free', 'gluten free', 'gf', 'celiac'
            ],
            DietaryRestriction.DAIRY_FREE: [
                'dairy-free', 'dairy free', 'lactose-free', 'no dairy'
            ],
            DietaryRestriction.NUT_FREE: [
                'nut-free', 'nut free', 'no nuts', 'allergy-friendly'
            ],
            DietaryRestriction.LOW_CARB: [
                'low-carb', 'low carb', 'keto', 'ketogenic', 'atkins'
            ],
            DietaryRestriction.KETO: [
                'keto', 'ketogenic', 'ketosis'
            ],
            DietaryRestriction.PALEO: [
                'paleo', 'paleolithic', 'caveman diet'
            ],
            DietaryRestriction.HALAL: [
                'halal', 'islamic'
            ],
            DietaryRestriction.KOSHER: [
                'kosher', 'jewish'
            ]
        }
        
        # Common ingredient categories for better organization
        self.ingredient_categories = {
            'proteins': [
                'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp',
                'turkey', 'lamb', 'eggs', 'tofu', 'beans', 'lentils'
            ],
            'vegetables': [
                'onion', 'garlic', 'tomato', 'carrot', 'celery', 'pepper',
                'broccoli', 'spinach', 'lettuce', 'cucumber', 'potato'
            ],
            'grains': [
                'rice', 'pasta', 'bread', 'flour', 'oats', 'quinoa', 'barley'
            ],
            'dairy': [
                'milk', 'cheese', 'butter', 'cream', 'yogurt', 'sour cream'
            ],
            'spices': [
                'salt', 'pepper', 'paprika', 'cumin', 'oregano', 'basil',
                'thyme', 'rosemary', 'cinnamon', 'ginger'
            ]
        }
    
    async def normalize_recipe(self, scraped_data: Dict[str, Any]) -> Optional[RecipeCreate]:
        """
        Normalize scraped recipe data to RecipeCreate schema
        
        Args:
            scraped_data: Raw scraped recipe data
            
        Returns:
            RecipeCreate object if successful, None otherwise
        """
        try:
            # Extract and validate basic information
            title = self._normalize_title(scraped_data.get('title', ''))
            if not title:
                logger.error("Recipe title is required")
                return None
            
            description = self._normalize_description(scraped_data.get('description', ''))
            
            # Normalize ingredients
            ingredients = await self._normalize_ingredients(scraped_data.get('ingredients', []))
            if not ingredients:
                logger.error("Recipe must have at least one ingredient")
                return None
            
            # Normalize instructions
            instructions = self._normalize_instructions(scraped_data.get('instructions', []))
            if not instructions:
                logger.error("Recipe must have at least one instruction")
                return None
            
            # Normalize times
            prep_time = self._normalize_time(scraped_data.get('prep_time'))
            cook_time = self._normalize_time(scraped_data.get('cook_time'))
            
            # Normalize servings
            servings = self._normalize_servings(scraped_data.get('servings', 4))
            
            # Normalize difficulty
            difficulty = self._normalize_difficulty(scraped_data.get('difficulty', 'medium'))
            
            # Normalize tags and categories
            tags = self._normalize_tags(scraped_data.get('tags', []))
            meal_types = self._normalize_meal_types(scraped_data.get('meal_types', []))
            
            # Detect dietary restrictions
            dietary_restrictions = await self._detect_dietary_restrictions(
                title, description, ingredients, instructions, tags
            )
            
            # Normalize nutrition info
            nutrition_info = self._normalize_nutrition(scraped_data.get('nutrition_info'))
            
            # Normalize URLs
            photo_url = self._normalize_url(scraped_data.get('photo_url'))
            source_url = self._normalize_url(scraped_data.get('source_url'))
            
            # Create RecipeCreate object
            recipe_create = RecipeCreate(
                title=title,
                description=description,
                ingredients=ingredients,
                instructions=instructions,
                prep_time=prep_time,
                cook_time=cook_time,
                servings=servings,
                difficulty=difficulty,
                tags=tags,
                meal_types=meal_types,
                dietary_restrictions=dietary_restrictions,
                nutrition_info=nutrition_info,
                photo_url=photo_url,
                source_url=source_url
            )
            
            # Validate the normalized recipe
            validation_result = await recipe_validator.validate_recipe(recipe_create)
            
            if not validation_result.is_valid:
                logger.warning(f"Recipe validation issues: {validation_result.safety_issues + validation_result.practicality_issues}")
                
                # Apply automatic fixes for common issues
                recipe_create = await self._apply_validation_fixes(recipe_create, validation_result)
            
            logger.info(f"Successfully normalized recipe: {title}")
            return recipe_create
            
        except Exception as e:
            logger.error(f"Error normalizing recipe: {e}")
            return None
    
    def _normalize_title(self, title: str) -> str:
        """Normalize recipe title"""
        if not title:
            return ''
        
        # Clean and format title
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)  # Remove extra whitespace
        title = title.title()  # Title case
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['recipe:', 'recipe for', 'how to make']
        for prefix in prefixes_to_remove:
            if title.lower().startswith(prefix):
                title = title[len(prefix):].strip()
        
        return title[:200]  # Limit length
    
    def _normalize_description(self, description: str) -> Optional[str]:
        """Normalize recipe description"""
        if not description:
            return None
        
        description = description.strip()
        description = re.sub(r'\s+', ' ', description)  # Remove extra whitespace
        
        return description[:1000] if description else None  # Limit length
    
    async def _normalize_ingredients(self, ingredients_data: List[Dict[str, Any]]) -> List[RecipeIngredient]:
        """Normalize ingredients list"""
        normalized_ingredients = []
        
        for ingredient_data in ingredients_data:
            try:
                # Extract ingredient information
                name = ingredient_data.get('name', '').strip()
                if not name:
                    continue
                
                quantity = float(ingredient_data.get('quantity', 1.0))
                unit = ingredient_data.get('unit', 'piece').strip()
                notes = ingredient_data.get('notes')
                
                # Normalize unit
                unit = self._normalize_unit(unit)
                
                # Clean ingredient name
                name = self._clean_ingredient_name(name)
                
                # Create RecipeIngredient
                ingredient = RecipeIngredient(
                    name=name,
                    quantity=quantity,
                    unit=unit,
                    notes=notes
                )
                
                normalized_ingredients.append(ingredient)
                
            except Exception as e:
                logger.warning(f"Error normalizing ingredient {ingredient_data}: {e}")
                continue
        
        return normalized_ingredients
    
    def _normalize_instructions(self, instructions_data: List[str]) -> List[str]:
        """Normalize cooking instructions"""
        normalized_instructions = []
        
        for instruction in instructions_data:
            if not instruction or not instruction.strip():
                continue
            
            # Clean instruction text
            instruction = instruction.strip()
            instruction = re.sub(r'\s+', ' ', instruction)  # Remove extra whitespace
            
            # Ensure instruction ends with period
            if not instruction.endswith('.'):
                instruction += '.'
            
            # Capitalize first letter
            instruction = instruction[0].upper() + instruction[1:] if instruction else instruction
            
            normalized_instructions.append(instruction)
        
        return normalized_instructions
    
    def _normalize_time(self, time_value: Any) -> Optional[int]:
        """Normalize time value to minutes"""
        if not time_value:
            return None
        
        try:
            if isinstance(time_value, (int, float)):
                return max(0, int(time_value))
            
            if isinstance(time_value, str):
                # Extract number from string
                number_match = re.search(r'(\d+)', time_value)
                if number_match:
                    return max(0, int(number_match.group(1)))
            
            return None
            
        except Exception:
            return None
    
    def _normalize_servings(self, servings_value: Any) -> int:
        """Normalize servings value"""
        try:
            if isinstance(servings_value, (int, float)):
                return max(1, min(int(servings_value), 20))
            
            if isinstance(servings_value, str):
                number_match = re.search(r'(\d+)', servings_value)
                if number_match:
                    return max(1, min(int(number_match.group(1)), 20))
            
            return 4  # Default servings
            
        except Exception:
            return 4
    
    def _normalize_difficulty(self, difficulty_value: Any) -> DifficultyLevel:
        """Normalize difficulty level"""
        if not difficulty_value:
            return DifficultyLevel.MEDIUM
        
        difficulty_str = str(difficulty_value).lower()
        
        if any(word in difficulty_str for word in ['easy', 'simple', 'basic', 'beginner']):
            return DifficultyLevel.EASY
        elif any(word in difficulty_str for word in ['hard', 'difficult', 'complex', 'advanced', 'expert']):
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.MEDIUM
    
    def _normalize_tags(self, tags_data: List[str]) -> List[str]:
        """Normalize recipe tags"""
        normalized_tags = []
        
        for tag in tags_data:
            if not tag or not tag.strip():
                continue
            
            # Clean and normalize tag
            tag = tag.strip().lower()
            tag = re.sub(r'[^\w\s-]', '', tag)  # Remove special characters
            tag = re.sub(r'\s+', '-', tag)  # Replace spaces with hyphens
            
            if len(tag) > 2 and tag not in normalized_tags:  # Avoid duplicates and very short tags
                normalized_tags.append(tag)
        
        return normalized_tags[:10]  # Limit number of tags
    
    def _normalize_meal_types(self, meal_types_data: List[str]) -> List[MealType]:
        """Normalize meal types"""
        normalized_meal_types = []
        
        meal_type_mapping = {
            'breakfast': MealType.BREAKFAST,
            'lunch': MealType.LUNCH,
            'dinner': MealType.DINNER,
            'snack': MealType.SNACK,
            'dessert': MealType.DESSERT,
            'appetizer': MealType.APPETIZER,
            'beverage': MealType.BEVERAGE,
        }
        
        for meal_type in meal_types_data:
            if not meal_type:
                continue
            
            meal_type_lower = meal_type.lower()
            for key, enum_value in meal_type_mapping.items():
                if key in meal_type_lower and enum_value not in normalized_meal_types:
                    normalized_meal_types.append(enum_value)
                    break
        
        return normalized_meal_types
    
    async def _detect_dietary_restrictions(
        self, 
        title: str, 
        description: Optional[str], 
        ingredients: List[RecipeIngredient],
        instructions: List[str],
        tags: List[str]
    ) -> List[DietaryRestriction]:
        """Detect dietary restrictions from recipe content"""
        detected_restrictions = []
        
        # Combine all text for analysis
        all_text = ' '.join([
            title or '',
            description or '',
            ' '.join(tags),
            ' '.join(instructions)
        ]).lower()
        
        # Add ingredient names
        ingredient_names = ' '.join([ing.name.lower() for ing in ingredients])
        all_text += ' ' + ingredient_names
        
        # Check for dietary restriction keywords
        for restriction, keywords in self.dietary_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                detected_restrictions.append(restriction)
        
        # Additional logic for ingredient-based detection
        meat_ingredients = ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'bacon', 'ham']
        dairy_ingredients = ['milk', 'cheese', 'butter', 'cream', 'yogurt']
        gluten_ingredients = ['flour', 'wheat', 'bread', 'pasta']
        
        has_meat = any(meat in ingredient_names for meat in meat_ingredients)
        has_dairy = any(dairy in ingredient_names for dairy in dairy_ingredients)
        has_gluten = any(gluten in ingredient_names for gluten in gluten_ingredients)
        
        # If no meat detected and not already marked, could be vegetarian
        if not has_meat and DietaryRestriction.VEGETARIAN not in detected_restrictions:
            # Only add if there are clear vegetarian indicators
            if any(keyword in all_text for keyword in ['vegetarian', 'veggie', 'plant']):
                detected_restrictions.append(DietaryRestriction.VEGETARIAN)
        
        # If no dairy detected and marked as dairy-free
        if not has_dairy and any(keyword in all_text for keyword in ['dairy-free', 'lactose-free']):
            if DietaryRestriction.DAIRY_FREE not in detected_restrictions:
                detected_restrictions.append(DietaryRestriction.DAIRY_FREE)
        
        # If no gluten detected and marked as gluten-free
        if not has_gluten and any(keyword in all_text for keyword in ['gluten-free', 'gf']):
            if DietaryRestriction.GLUTEN_FREE not in detected_restrictions:
                detected_restrictions.append(DietaryRestriction.GLUTEN_FREE)
        
        return detected_restrictions
    
    def _normalize_nutrition(self, nutrition_data: Optional[Dict[str, Any]]) -> Optional[RecipeNutrition]:
        """Normalize nutrition information"""
        if not nutrition_data:
            return None
        
        try:
            nutrition = RecipeNutrition(
                calories_per_serving=self._extract_numeric_value(nutrition_data.get('calories_per_serving')),
                protein_g=self._extract_numeric_value(nutrition_data.get('protein_g')),
                carbs_g=self._extract_numeric_value(nutrition_data.get('carbs_g')),
                fat_g=self._extract_numeric_value(nutrition_data.get('fat_g')),
                fiber_g=self._extract_numeric_value(nutrition_data.get('fiber_g')),
                sugar_g=self._extract_numeric_value(nutrition_data.get('sugar_g')),
                sodium_mg=self._extract_numeric_value(nutrition_data.get('sodium_mg'))
            )
            
            # Only return if at least one field has a value
            if any([
                nutrition.calories_per_serving,
                nutrition.protein_g,
                nutrition.carbs_g,
                nutrition.fat_g
            ]):
                return nutrition
            
            return None
            
        except Exception as e:
            logger.warning(f"Error normalizing nutrition data: {e}")
            return None
    
    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize URL"""
        if not url:
            return None
        
        url = url.strip()
        if url.startswith('http://') or url.startswith('https://'):
            return url[:500]  # Limit length
        
        return None
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalize measurement unit"""
        unit = unit.lower().strip()
        return self.unit_conversions.get(unit, unit)
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name"""
        # Remove common prefixes and suffixes
        name = re.sub(r'^(fresh|dried|ground|chopped|diced|sliced|minced)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(fresh|dried|ground|chopped|diced|sliced|minced)$', '', name, flags=re.IGNORECASE)
        
        # Remove parenthetical notes (keep them in notes field if needed)
        name = re.sub(r'\([^)]*\)', '', name)
        
        # Clean whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name.title()
    
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """Extract numeric value from various formats"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value) if value >= 0 else None
            
            if isinstance(value, str):
                # Extract first number from string
                number_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if number_match:
                    return float(number_match.group(1))
            
            return None
            
        except Exception:
            return None
    
    async def _apply_validation_fixes(
        self, 
        recipe: RecipeCreate, 
        validation_result
    ) -> RecipeCreate:
        """Apply automatic fixes for common validation issues"""
        try:
            # Fix missing seasoning instructions
            if any('seasoning' in issue.lower() for issue in validation_result.practicality_issues):
                if not any('season' in instruction.lower() for instruction in recipe.instructions):
                    recipe.instructions.append("Season with salt and pepper to taste.")
            
            # Fix very short instruction lists
            if len(recipe.instructions) < 3:
                if not any('serve' in instruction.lower() for instruction in recipe.instructions):
                    recipe.instructions.append("Serve immediately and enjoy.")
            
            # Add default meal type if none specified
            if not recipe.meal_types:
                # Try to infer from title or tags
                title_lower = recipe.title.lower()
                if any(word in title_lower for word in ['breakfast', 'morning', 'pancake', 'cereal']):
                    recipe.meal_types = [MealType.BREAKFAST]
                elif any(word in title_lower for word in ['dessert', 'cake', 'cookie', 'pie']):
                    recipe.meal_types = [MealType.DESSERT]
                elif any(word in title_lower for word in ['snack', 'dip', 'chip']):
                    recipe.meal_types = [MealType.SNACK]
                else:
                    recipe.meal_types = [MealType.DINNER]  # Default
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error applying validation fixes: {e}")
            return recipe
    
    def get_supported_units(self) -> List[str]:
        """Get list of supported measurement units"""
        return list(set(self.unit_conversions.values()))
    
    def convert_unit(self, quantity: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between measurement units (basic conversions)"""
        # This is a simplified conversion - in a real app you'd want more comprehensive conversions
        try:
            from_unit = self._normalize_unit(from_unit)
            to_unit = self._normalize_unit(to_unit)
            
            if from_unit == to_unit:
                return quantity
            
            # Basic volume conversions (all to ml first, then to target)
            volume_to_ml = {
                'tsp': 4.92892,
                'tbsp': 14.7868,
                'cup': 236.588,
                'fl oz': 29.5735,
                'pint': 473.176,
                'quart': 946.353,
                'liter': 1000,
                'ml': 1
            }
            
            if from_unit in volume_to_ml and to_unit in volume_to_ml:
                ml_value = quantity * volume_to_ml[from_unit]
                return ml_value / volume_to_ml[to_unit]
            
            # Basic weight conversions (all to grams first, then to target)
            weight_to_g = {
                'g': 1,
                'kg': 1000,
                'oz': 28.3495,
                'lb': 453.592
            }
            
            if from_unit in weight_to_g and to_unit in weight_to_g:
                g_value = quantity * weight_to_g[from_unit]
                return g_value / weight_to_g[to_unit]
            
            return None  # Cannot convert
            
        except Exception as e:
            logger.error(f"Error converting units: {e}")
            return None


# Global recipe normalizer service instance
recipe_normalizer = RecipeNormalizerService()