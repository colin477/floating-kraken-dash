"""
Recipe validation and quality assurance service
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from app.models.recipes import RecipeCreate, RecipeIngredient, DifficultyLevel, MealType
from app.models.ai_recipes import RecipeValidationResult

# Configure logging
logger = logging.getLogger(__name__)


class RecipeValidatorService:
    """Service for validating and assessing recipe quality"""
    
    def __init__(self):
        # Food safety keywords that should trigger warnings
        self.unsafe_keywords = [
            'raw chicken', 'raw pork', 'raw beef', 'raw fish', 'raw eggs',
            'undercooked', 'rare chicken', 'rare pork', 'pink chicken',
            'room temperature meat', 'thawed meat'
        ]
        
        # Cooking methods that require temperature monitoring
        self.temperature_critical_methods = [
            'grill', 'roast', 'bake', 'fry', 'sauté', 'cook chicken',
            'cook pork', 'cook beef', 'cook fish'
        ]
        
        # Common ingredient substitution ratios
        self.substitution_ratios = {
            'butter_to_oil': 0.75,
            'sugar_to_honey': 0.75,
            'milk_to_almond_milk': 1.0,
            'flour_to_almond_flour': 1.25
        }
        
        # Reasonable quantity ranges for common ingredients
        self.quantity_ranges = {
            'salt': {'min': 0.25, 'max': 2.0, 'unit': 'tsp'},
            'pepper': {'min': 0.125, 'max': 1.0, 'unit': 'tsp'},
            'oil': {'min': 1.0, 'max': 8.0, 'unit': 'tbsp'},
            'butter': {'min': 1.0, 'max': 8.0, 'unit': 'tbsp'},
            'flour': {'min': 0.25, 'max': 4.0, 'unit': 'cup'},
            'sugar': {'min': 1.0, 'max': 2.0, 'unit': 'cup'},
            'milk': {'min': 0.25, 'max': 2.0, 'unit': 'cup'},
            'eggs': {'min': 1, 'max': 6, 'unit': 'piece'}
        }
    
    async def validate_recipe(self, recipe: RecipeCreate) -> RecipeValidationResult:
        """
        Comprehensive recipe validation
        
        Args:
            recipe: Recipe to validate
            
        Returns:
            RecipeValidationResult with validation details
        """
        try:
            safety_score, safety_issues = self._validate_food_safety(recipe)
            practicality_score, practicality_issues = self._validate_practicality(recipe)
            nutrition_score, nutrition_issues = self._validate_nutrition(recipe)
            
            # Calculate overall score
            overall_score = (safety_score * 0.4 + practicality_score * 0.4 + (nutrition_score or 0.8) * 0.2)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                recipe, safety_issues, practicality_issues, nutrition_issues
            )
            
            # Determine recommendation
            recommendation = self._determine_recommendation(overall_score, safety_issues)
            
            is_valid = overall_score >= 0.6 and len(safety_issues) == 0
            
            return RecipeValidationResult(
                is_valid=is_valid,
                safety_score=safety_score,
                practicality_score=practicality_score,
                nutrition_score=nutrition_score,
                safety_issues=safety_issues,
                practicality_issues=practicality_issues,
                nutrition_issues=nutrition_issues,
                improvement_suggestions=improvement_suggestions,
                overall_score=overall_score,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error validating recipe: {e}")
            return RecipeValidationResult(
                is_valid=False,
                safety_score=0.0,
                practicality_score=0.0,
                nutrition_score=None,
                safety_issues=["Validation failed due to system error"],
                practicality_issues=[],
                nutrition_issues=[],
                improvement_suggestions=["Please review recipe manually"],
                overall_score=0.0,
                recommendation="reject"
            )
    
    def _validate_food_safety(self, recipe: RecipeCreate) -> Tuple[float, List[str]]:
        """Validate food safety aspects of the recipe"""
        issues = []
        score = 1.0
        
        # Check for unsafe keywords in instructions
        instructions_text = ' '.join(recipe.instructions).lower()
        for keyword in self.unsafe_keywords:
            if keyword in instructions_text:
                issues.append(f"Potential food safety concern: {keyword}")
                score -= 0.2
        
        # Check for proper cooking instructions for meat/poultry
        has_meat = any(
            meat in ing.name.lower() 
            for ing in recipe.ingredients 
            for meat in ['chicken', 'pork', 'beef', 'fish', 'turkey']
        )
        
        if has_meat:
            has_temperature_instruction = any(
                temp_word in instructions_text 
                for temp_word in ['temperature', 'degrees', '°f', '°c', 'internal temp', 'cooked through']
            )
            
            if not has_temperature_instruction:
                issues.append("Recipe contains meat but lacks temperature guidance")
                score -= 0.3
        
        # Check for proper food handling instructions
        has_raw_ingredients = any(
            'raw' in ing.name.lower() or 'fresh' in ing.name.lower()
            for ing in recipe.ingredients
        )
        
        if has_raw_ingredients and 'wash' not in instructions_text:
            issues.append("Recipe uses raw ingredients but lacks washing instructions")
            score -= 0.1
        
        return max(score, 0.0), issues
    
    def _validate_practicality(self, recipe: RecipeCreate) -> Tuple[float, List[str]]:
        """Validate practical aspects of the recipe"""
        issues = []
        score = 1.0
        
        # Check ingredient quantities
        for ingredient in recipe.ingredients:
            quantity_issue = self._check_ingredient_quantity(ingredient)
            if quantity_issue:
                issues.append(quantity_issue)
                score -= 0.1
        
        # Check cooking times
        if recipe.prep_time and recipe.prep_time > 240:  # 4 hours
            issues.append("Preparation time seems excessive (>4 hours)")
            score -= 0.2
        
        if recipe.cook_time and recipe.cook_time > 480:  # 8 hours
            issues.append("Cooking time seems excessive (>8 hours)")
            score -= 0.2
        
        # Check servings
        if recipe.servings > 20:
            issues.append("Recipe serves unusually large number of people")
            score -= 0.1
        elif recipe.servings < 1:
            issues.append("Recipe must serve at least 1 person")
            score -= 0.3
        
        # Check instruction clarity
        if len(recipe.instructions) < 3:
            issues.append("Recipe has very few instructions - may lack detail")
            score -= 0.2
        
        # Check for missing essential steps
        has_seasoning = any(
            season_word in ' '.join(recipe.instructions).lower()
            for season_word in ['season', 'salt', 'pepper', 'taste']
        )
        
        if not has_seasoning and len(recipe.ingredients) > 3:
            issues.append("Recipe may benefit from seasoning instructions")
            score -= 0.1
        
        return max(score, 0.0), issues
    
    def _validate_nutrition(self, recipe: RecipeCreate) -> Tuple[Optional[float], List[str]]:
        """Validate nutritional aspects of the recipe"""
        if not recipe.nutrition_info:
            return None, []
        
        issues = []
        score = 1.0
        nutrition = recipe.nutrition_info
        
        # Check calorie reasonableness
        if nutrition.calories_per_serving:
            if nutrition.calories_per_serving > 1500:
                issues.append("Very high calorie content per serving")
                score -= 0.3
            elif nutrition.calories_per_serving < 50:
                issues.append("Very low calorie content - may not be filling")
                score -= 0.2
        
        # Check macronutrient balance
        if nutrition.protein_g and nutrition.carbs_g and nutrition.fat_g:
            total_macros = nutrition.protein_g + nutrition.carbs_g + nutrition.fat_g
            if total_macros > 0:
                protein_ratio = nutrition.protein_g / total_macros
                fat_ratio = nutrition.fat_g / total_macros
                
                if protein_ratio < 0.1:
                    issues.append("Recipe is very low in protein")
                    score -= 0.2
                
                if fat_ratio > 0.6:
                    issues.append("Recipe is very high in fat")
                    score -= 0.2
        
        # Check sodium content
        if nutrition.sodium_mg and nutrition.sodium_mg > 2000:
            issues.append("High sodium content - consider reducing salt")
            score -= 0.2
        
        return max(score, 0.0), issues
    
    def _check_ingredient_quantity(self, ingredient: RecipeIngredient) -> Optional[str]:
        """Check if ingredient quantity is reasonable"""
        ingredient_name = ingredient.name.lower()
        
        # Check against known quantity ranges
        for key, ranges in self.quantity_ranges.items():
            if key in ingredient_name:
                if ingredient.unit.lower() in ranges['unit'].lower():
                    if ingredient.quantity < ranges['min']:
                        return f"{ingredient.name}: quantity seems too low ({ingredient.quantity} {ingredient.unit})"
                    elif ingredient.quantity > ranges['max']:
                        return f"{ingredient.name}: quantity seems too high ({ingredient.quantity} {ingredient.unit})"
        
        # General quantity checks
        if ingredient.quantity <= 0:
            return f"{ingredient.name}: quantity must be positive"
        
        if ingredient.quantity > 100 and ingredient.unit.lower() not in ['ml', 'g', 'mg']:
            return f"{ingredient.name}: unusually large quantity ({ingredient.quantity} {ingredient.unit})"
        
        return None
    
    def _generate_improvement_suggestions(
        self, 
        recipe: RecipeCreate, 
        safety_issues: List[str], 
        practicality_issues: List[str], 
        nutrition_issues: List[str]
    ) -> List[str]:
        """Generate suggestions for improving the recipe"""
        suggestions = []
        
        # Safety improvements
        if any('temperature' in issue.lower() for issue in safety_issues):
            suggestions.append("Add internal temperature guidelines for meat (165°F for chicken, 145°F for pork/beef)")
        
        if any('washing' in issue.lower() for issue in safety_issues):
            suggestions.append("Include instructions to wash fresh produce before use")
        
        # Practicality improvements
        if any('time' in issue.lower() for issue in practicality_issues):
            suggestions.append("Consider breaking down long cooking processes into manageable steps")
        
        if any('instructions' in issue.lower() for issue in practicality_issues):
            suggestions.append("Add more detailed step-by-step instructions")
        
        if any('seasoning' in issue.lower() for issue in practicality_issues):
            suggestions.append("Add 'season to taste' instructions with salt and pepper")
        
        # Nutrition improvements
        if any('protein' in issue.lower() for issue in nutrition_issues):
            suggestions.append("Consider adding protein sources like beans, nuts, or lean meat")
        
        if any('sodium' in issue.lower() for issue in nutrition_issues):
            suggestions.append("Reduce salt and use herbs/spices for flavor instead")
        
        if any('calorie' in issue.lower() for issue in nutrition_issues):
            suggestions.append("Consider portion sizes and ingredient substitutions to balance calories")
        
        # General improvements
        if recipe.difficulty == DifficultyLevel.HARD and recipe.prep_time and recipe.prep_time < 30:
            suggestions.append("Prep time may be underestimated for a hard difficulty recipe")
        
        if len(recipe.ingredients) > 15:
            suggestions.append("Consider simplifying the ingredient list for easier preparation")
        
        return suggestions
    
    def _determine_recommendation(self, overall_score: float, safety_issues: List[str]) -> str:
        """Determine overall recommendation for the recipe"""
        if safety_issues:
            return "modify"  # Always recommend modification if there are safety issues
        
        if overall_score >= 0.8:
            return "approve"
        elif overall_score >= 0.6:
            return "modify"
        else:
            return "reject"
    
    async def validate_ingredient_substitution(
        self, 
        original: str, 
        substitute: str, 
        recipe_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate if an ingredient substitution is appropriate
        
        Args:
            original: Original ingredient name
            substitute: Substitute ingredient name
            recipe_context: Context about the recipe (cuisine, dish type, etc.)
            
        Returns:
            Dictionary with substitution validation results
        """
        try:
            # Basic substitution validation
            is_valid = True
            confidence = 0.5
            notes = []
            
            original_lower = original.lower()
            substitute_lower = substitute.lower()
            
            # Check for obvious incompatible substitutions
            incompatible_pairs = [
                (['meat', 'chicken', 'beef', 'pork'], ['fruit', 'apple', 'banana']),
                (['flour', 'wheat'], ['liquid', 'milk', 'water']),
                (['sugar', 'sweet'], ['salt', 'salty'])
            ]
            
            for orig_group, sub_group in incompatible_pairs:
                if (any(word in original_lower for word in orig_group) and 
                    any(word in substitute_lower for word in sub_group)):
                    is_valid = False
                    confidence = 0.1
                    notes.append("Incompatible ingredient types")
                    break
            
            # Check for good substitutions
            good_substitutions = {
                'butter': ['margarine', 'oil', 'coconut oil'],
                'milk': ['almond milk', 'soy milk', 'oat milk'],
                'sugar': ['honey', 'maple syrup', 'stevia'],
                'flour': ['almond flour', 'coconut flour']
            }
            
            for orig_key, substitutes in good_substitutions.items():
                if orig_key in original_lower:
                    if any(sub in substitute_lower for sub in substitutes):
                        confidence = 0.8
                        notes.append("Common and well-tested substitution")
                        break
            
            return {
                'is_valid': is_valid,
                'confidence': confidence,
                'notes': notes,
                'recommended_ratio': 1.0,  # Default 1:1 ratio
                'flavor_impact': 'minimal' if confidence > 0.7 else 'moderate',
                'texture_impact': 'minimal' if confidence > 0.7 else 'moderate'
            }
            
        except Exception as e:
            logger.error(f"Error validating ingredient substitution: {e}")
            return {
                'is_valid': False,
                'confidence': 0.0,
                'notes': ["Validation failed"],
                'recommended_ratio': 1.0,
                'flavor_impact': 'unknown',
                'texture_impact': 'unknown'
            }


# Global recipe validator service instance
recipe_validator = RecipeValidatorService()