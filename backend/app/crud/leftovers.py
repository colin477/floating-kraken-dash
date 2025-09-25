"""
CRUD operations for leftover suggestion management
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, DESCENDING

from app.database import get_collection
from app.models.leftovers import (
    LeftoverSuggestion,
    LeftoverSuggestionsResponse,
    IngredientMatch,
    MatchType,
    SuggestionFilters,
    PantryIngredientInfo,
    IngredientSubstitute
)
from app.models.recipes import RecipeResponse
from app.models.pantry import PantryItemResponse
from app.crud.pantry import get_pantry_items
from app.crud.recipes import get_recipes

# Configure logging
logger = logging.getLogger(__name__)

# Common ingredient substitutes mapping
INGREDIENT_SUBSTITUTES = {
    "butter": ["margarine", "oil", "coconut oil"],
    "oil": ["butter", "margarine", "coconut oil"],
    "milk": ["almond milk", "soy milk", "coconut milk", "oat milk"],
    "cream": ["milk", "half and half", "coconut cream"],
    "sugar": ["honey", "maple syrup", "brown sugar", "stevia"],
    "flour": ["almond flour", "coconut flour", "whole wheat flour"],
    "eggs": ["egg substitute", "flax eggs", "chia eggs"],
    "cheese": ["nutritional yeast", "vegan cheese"],
    "yogurt": ["sour cream", "greek yogurt", "coconut yogurt"],
    "onion": ["shallot", "green onion", "onion powder"],
    "garlic": ["garlic powder", "shallot", "onion"],
    "tomato": ["tomatoes", "cherry tomatoes", "roma tomatoes"],
    "chicken": ["turkey", "tofu", "tempeh"],
    "beef": ["turkey", "chicken", "mushrooms", "lentils"],
    "rice": ["quinoa", "cauliflower rice", "pasta"],
    "pasta": ["rice", "quinoa", "zucchini noodles"],
    "bread": ["tortilla", "pita", "crackers"],
    "lemon": ["lime", "vinegar", "lemon juice"],
    "lime": ["lemon", "vinegar", "lime juice"]
}

# Ingredient categories for fuzzy matching
INGREDIENT_CATEGORIES = {
    "cheese": ["cheddar", "mozzarella", "parmesan", "swiss", "gouda", "feta", "brie"],
    "tomato": ["cherry tomatoes", "roma tomatoes", "grape tomatoes", "beefsteak tomatoes"],
    "onion": ["yellow onion", "white onion", "red onion", "sweet onion"],
    "pepper": ["bell pepper", "red pepper", "green pepper", "yellow pepper"],
    "mushroom": ["button mushrooms", "shiitake", "portobello", "cremini"],
    "lettuce": ["romaine", "iceberg", "spinach", "arugula", "mixed greens"],
    "oil": ["olive oil", "vegetable oil", "canola oil", "coconut oil"],
    "vinegar": ["white vinegar", "apple cider vinegar", "balsamic vinegar"],
    "herbs": ["basil", "oregano", "thyme", "rosemary", "parsley", "cilantro"],
    "spices": ["salt", "pepper", "paprika", "cumin", "garlic powder", "onion powder"]
}


async def get_user_available_ingredients(db, user_id: str) -> List[PantryIngredientInfo]:
    """
    Get all available ingredients from user's pantry
    
    Args:
        db: Database connection (not used in current implementation)
        user_id: User's ObjectId as string
        
    Returns:
        List of PantryIngredientInfo objects
    """
    try:
        # Get pantry items using existing CRUD function
        pantry_response = await get_pantry_items(user_id, page_size=1000)  # Get all items
        
        if not pantry_response or not pantry_response.items:
            logger.info(f"No pantry items found for user {user_id}")
            return []
        
        available_ingredients = []
        today = date.today()
        
        for item in pantry_response.items:
            # Calculate freshness and expiration info
            days_until_expiration = item.days_until_expiration
            is_expired = days_until_expiration is not None and days_until_expiration < 0
            is_expiring_soon = days_until_expiration is not None and 0 <= days_until_expiration <= 7
            
            # Calculate freshness score
            freshness_score = 1.0
            if days_until_expiration is not None:
                if days_until_expiration < 0:
                    freshness_score = 0.0  # Expired
                elif days_until_expiration <= 3:
                    freshness_score = 0.3  # Expiring very soon
                elif days_until_expiration <= 7:
                    freshness_score = 0.6  # Expiring soon
                elif days_until_expiration <= 14:
                    freshness_score = 0.8  # Good
                # else: freshness_score = 1.0 (fresh)
            
            ingredient_info = PantryIngredientInfo(
                name=item.name,
                normalized_name=normalize_ingredient_name(item.name),
                category=item.category,
                quantity=item.quantity,
                unit=item.unit,
                expiration_date=item.expiration_date,
                days_until_expiration=days_until_expiration,
                is_expired=is_expired,
                is_expiring_soon=is_expiring_soon,
                freshness_score=freshness_score
            )
            available_ingredients.append(ingredient_info)
        
        logger.info(f"Found {len(available_ingredients)} available ingredients for user {user_id}")
        return available_ingredients
        
    except Exception as e:
        logger.error(f"Error getting available ingredients for user {user_id}: {e}")
        return []


def normalize_ingredient_name(ingredient: str) -> str:
    """
    Normalize ingredient names for better matching
    
    Args:
        ingredient: Raw ingredient name
        
    Returns:
        Normalized ingredient name
    """
    if not ingredient:
        return ""
    
    # Convert to lowercase
    normalized = ingredient.lower().strip()
    
    # Remove common prefixes and suffixes
    prefixes_to_remove = ["fresh", "dried", "frozen", "canned", "organic", "raw"]
    suffixes_to_remove = ["chopped", "diced", "sliced", "minced", "grated", "shredded"]
    
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix + " "):
            normalized = normalized[len(prefix) + 1:]
    
    for suffix in suffixes_to_remove:
        if normalized.endswith(" " + suffix):
            normalized = normalized[:-len(suffix) - 1]
    
    # Remove extra whitespace and punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Handle plurals (simple approach)
    if normalized.endswith('s') and len(normalized) > 3:
        singular = normalized[:-1]
        # Check if singular form makes sense (avoid removing 's' from words like 'grass')
        if not singular.endswith('s'):
            normalized = singular
    
    return normalized


def find_ingredient_substitutes(ingredient: str) -> List[IngredientSubstitute]:
    """
    Find common substitutes for ingredients
    
    Args:
        ingredient: Ingredient name to find substitutes for
        
    Returns:
        List of IngredientSubstitute objects
    """
    normalized_ingredient = normalize_ingredient_name(ingredient)
    substitutes = []
    
    # Check direct substitutes
    if normalized_ingredient in INGREDIENT_SUBSTITUTES:
        for substitute in INGREDIENT_SUBSTITUTES[normalized_ingredient]:
            substitutes.append(IngredientSubstitute(
                original_ingredient=ingredient,
                substitute_ingredient=substitute,
                substitution_ratio=1.0,
                confidence=0.8,
                notes=f"Common substitute for {ingredient}"
            ))
    
    # Check category-based substitutes
    for category, items in INGREDIENT_CATEGORIES.items():
        if normalized_ingredient in [normalize_ingredient_name(item) for item in items]:
            for item in items:
                if normalize_ingredient_name(item) != normalized_ingredient:
                    substitutes.append(IngredientSubstitute(
                        original_ingredient=ingredient,
                        substitute_ingredient=item,
                        substitution_ratio=1.0,
                        confidence=0.6,
                        notes=f"Same category substitute ({category})"
                    ))
    
    return substitutes


def calculate_ingredient_match(
    required_ingredient: str,
    available_ingredients: List[PantryIngredientInfo],
    include_substitutes: bool = True
) -> IngredientMatch:
    """
    Calculate how well a required ingredient matches available ingredients
    
    Args:
        required_ingredient: Required ingredient name from recipe
        available_ingredients: List of available pantry ingredients
        include_substitutes: Whether to consider substitutes
        
    Returns:
        IngredientMatch object with best match found
    """
    required_normalized = normalize_ingredient_name(required_ingredient)
    best_match = None
    best_confidence = 0.0
    
    # Try exact match first
    for available in available_ingredients:
        if available.normalized_name == required_normalized:
            return IngredientMatch(
                required_ingredient=required_ingredient,
                available_ingredient=available.name,
                match_type=MatchType.EXACT,
                match_confidence=1.0,
                is_matched=True,
                quantity_available=available.quantity,
                unit=available.unit,
                notes="Exact ingredient match"
            )
    
    # Try fuzzy matching
    for available in available_ingredients:
        # Check if one ingredient name contains the other
        if (required_normalized in available.normalized_name or 
            available.normalized_name in required_normalized):
            confidence = 0.8
            if confidence > best_confidence:
                best_match = IngredientMatch(
                    required_ingredient=required_ingredient,
                    available_ingredient=available.name,
                    match_type=MatchType.FUZZY,
                    match_confidence=confidence,
                    is_matched=True,
                    quantity_available=available.quantity,
                    unit=available.unit,
                    notes="Fuzzy ingredient match"
                )
                best_confidence = confidence
    
    # Try category matching
    if not best_match or best_confidence < 0.7:
        for category, items in INGREDIENT_CATEGORIES.items():
            required_in_category = any(
                required_normalized in normalize_ingredient_name(item) or
                normalize_ingredient_name(item) in required_normalized
                for item in items
            )
            
            if required_in_category:
                for available in available_ingredients:
                    available_in_category = any(
                        available.normalized_name in normalize_ingredient_name(item) or
                        normalize_ingredient_name(item) in available.normalized_name
                        for item in items
                    )
                    
                    if available_in_category:
                        confidence = 0.6
                        if confidence > best_confidence:
                            best_match = IngredientMatch(
                                required_ingredient=required_ingredient,
                                available_ingredient=available.name,
                                match_type=MatchType.CATEGORY,
                                match_confidence=confidence,
                                is_matched=True,
                                quantity_available=available.quantity,
                                unit=available.unit,
                                notes=f"Category match ({category})"
                            )
                            best_confidence = confidence
    
    # Try substitute matching
    if include_substitutes and (not best_match or best_confidence < 0.6):
        substitutes = find_ingredient_substitutes(required_ingredient)
        for substitute in substitutes:
            substitute_normalized = normalize_ingredient_name(substitute.substitute_ingredient)
            for available in available_ingredients:
                if available.normalized_name == substitute_normalized:
                    confidence = substitute.confidence * 0.8  # Reduce confidence for substitutes
                    if confidence > best_confidence:
                        best_match = IngredientMatch(
                            required_ingredient=required_ingredient,
                            available_ingredient=available.name,
                            match_type=MatchType.SUBSTITUTE,
                            match_confidence=confidence,
                            is_matched=True,
                            quantity_available=available.quantity,
                            unit=available.unit,
                            notes=f"Substitute match: {substitute.notes}"
                        )
                        best_confidence = confidence
    
    # Return best match or no match
    if best_match:
        return best_match
    else:
        return IngredientMatch(
            required_ingredient=required_ingredient,
            available_ingredient=None,
            match_type=MatchType.EXACT,
            match_confidence=0.0,
            is_matched=False,
            notes="No matching ingredient found"
        )


def calculate_recipe_match_score(
    recipe_ingredients: List[str],
    available_ingredients: List[PantryIngredientInfo],
    include_substitutes: bool = True
) -> Tuple[float, List[IngredientMatch], List[IngredientMatch]]:
    """
    Calculate how well a recipe matches available ingredients
    
    Args:
        recipe_ingredients: List of required ingredient names
        available_ingredients: List of available pantry ingredients
        include_substitutes: Whether to consider substitutes
        
    Returns:
        Tuple of (match_percentage, matched_ingredients, missing_ingredients)
    """
    if not recipe_ingredients:
        return 0.0, [], []
    
    matched_ingredients = []
    missing_ingredients = []
    
    for ingredient_name in recipe_ingredients:
        match = calculate_ingredient_match(
            ingredient_name,
            available_ingredients,
            include_substitutes
        )
        
        if match.is_matched:
            matched_ingredients.append(match)
        else:
            missing_ingredients.append(match)
    
    # Calculate match percentage
    total_ingredients = len(recipe_ingredients)
    matched_count = len(matched_ingredients)
    match_percentage = (matched_count / total_ingredients) * 100.0
    
    return match_percentage, matched_ingredients, missing_ingredients


async def filter_recipes_by_availability(
    db,
    available_ingredients: List[PantryIngredientInfo],
    user_id: str,
    min_match_percentage: float = 0.3,
    filters: Optional[SuggestionFilters] = None
) -> List[RecipeResponse]:
    """
    Filter recipes based on ingredient availability
    
    Args:
        db: Database connection (not used in current implementation)
        available_ingredients: List of available pantry ingredients
        user_id: User's ObjectId as string
        min_match_percentage: Minimum match percentage required
        filters: Additional filters to apply
        
    Returns:
        List of filtered RecipeResponse objects
    """
    try:
        # Get user's recipes
        recipes_response = await get_recipes(
            user_id=user_id,
            page_size=1000,  # Get all recipes
            difficulty=filters.difficulty_levels[0] if filters and filters.difficulty_levels else None,
            max_prep_time=filters.max_prep_time if filters else None,
            max_cook_time=filters.max_cook_time if filters else None
        )
        
        if not recipes_response or not recipes_response.recipes:
            logger.info(f"No recipes found for user {user_id}")
            return []
        
        filtered_recipes = []
        
        for recipe in recipes_response.recipes:
            # Extract ingredient names from recipe
            ingredient_names = [ing.name for ing in recipe.ingredients]
            
            # Calculate match score
            match_percentage, matched, missing = calculate_recipe_match_score(
                ingredient_names,
                available_ingredients,
                include_substitutes=filters.include_substitutes if filters else True
            )
            
            # Check if recipe meets minimum match percentage
            if match_percentage >= min_match_percentage * 100:
                # Apply additional filters
                if filters:
                    # Check meal types
                    if filters.meal_types and not any(
                        meal_type in recipe.meal_types for meal_type in filters.meal_types
                    ):
                        continue
                    
                    # Check dietary restrictions
                    if filters.dietary_restrictions and not all(
                        restriction in recipe.dietary_restrictions 
                        for restriction in filters.dietary_restrictions
                    ):
                        continue
                    
                    # Check if recipe uses expired ingredients (if exclude_expired is True)
                    if filters.exclude_expired:
                        uses_expired = any(
                            match.available_ingredient and 
                            any(ing.is_expired for ing in available_ingredients 
                                if ing.name == match.available_ingredient)
                            for match in matched
                        )
                        if uses_expired:
                            continue
                
                filtered_recipes.append(recipe)
        
        logger.info(f"Filtered {len(filtered_recipes)} recipes from {len(recipes_response.recipes)} total recipes")
        return filtered_recipes
        
    except Exception as e:
        logger.error(f"Error filtering recipes by availability for user {user_id}: {e}")
        return []


def calculate_suggestion_priority_score(
    recipe: RecipeResponse,
    match_percentage: float,
    matched_ingredients: List[IngredientMatch],
    available_ingredients: List[PantryIngredientInfo],
    filters: Optional[SuggestionFilters] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate priority score for a recipe suggestion
    
    Args:
        recipe: Recipe to score
        match_percentage: Ingredient match percentage
        matched_ingredients: List of matched ingredients
        available_ingredients: List of available pantry ingredients
        filters: Suggestion filters
        
    Returns:
        Tuple of (priority_score, score_breakdown)
    """
    score_breakdown = {}
    
    # Base score from match percentage (0-50 points)
    base_score = match_percentage * 0.5
    score_breakdown["match_percentage"] = base_score
    
    # Difficulty bonus (easier recipes get higher scores)
    difficulty_bonus = 0.0
    if recipe.difficulty == "easy":
        difficulty_bonus = 15.0
    elif recipe.difficulty == "medium":
        difficulty_bonus = 10.0
    else:  # hard
        difficulty_bonus = 5.0
    score_breakdown["difficulty_bonus"] = difficulty_bonus
    
    # Time bonus (quicker recipes get higher scores)
    time_bonus = 0.0
    total_time = (recipe.prep_time or 0) + (recipe.cook_time or 0)
    if total_time <= 30:
        time_bonus = 15.0
    elif total_time <= 60:
        time_bonus = 10.0
    elif total_time <= 90:
        time_bonus = 5.0
    score_breakdown["time_bonus"] = time_bonus
    
    # Freshness bonus (using fresh ingredients)
    freshness_bonus = 0.0
    if matched_ingredients:
        total_freshness = 0.0
        for match in matched_ingredients:
            if match.available_ingredient:
                for ing in available_ingredients:
                    if ing.name == match.available_ingredient:
                        total_freshness += ing.freshness_score
                        break
        avg_freshness = total_freshness / len(matched_ingredients)
        freshness_bonus = avg_freshness * 10.0
    score_breakdown["freshness_bonus"] = freshness_bonus
    
    # Expiration urgency bonus (using expiring ingredients)
    expiration_bonus = 0.0
    if filters and filters.prioritize_expiring:
        expiring_count = 0
        for match in matched_ingredients:
            if match.available_ingredient:
                for ing in available_ingredients:
                    if ing.name == match.available_ingredient and ing.is_expiring_soon:
                        expiring_count += 1
                        break
        if expiring_count > 0:
            expiration_bonus = min(expiring_count * 5.0, 20.0)
    score_breakdown["expiration_bonus"] = expiration_bonus
    
    # Recipe popularity bonus (based on servings - more servings = more popular)
    popularity_bonus = min(recipe.servings * 2.0, 10.0)
    score_breakdown["popularity_bonus"] = popularity_bonus
    
    # Calculate total score
    total_score = (
        base_score + 
        difficulty_bonus + 
        time_bonus + 
        freshness_bonus + 
        expiration_bonus + 
        popularity_bonus
    )
    
    return total_score, score_breakdown


def rank_suggestions_by_priority(suggestions: List[LeftoverSuggestion]) -> List[LeftoverSuggestion]:
    """
    Rank suggestions by various priority factors
    
    Args:
        suggestions: List of LeftoverSuggestion objects
        
    Returns:
        Sorted list of suggestions by priority score (highest first)
    """
    return sorted(suggestions, key=lambda x: x.priority_score, reverse=True)


async def get_leftover_suggestions(
    db,
    user_id: str,
    max_suggestions: int = 10,
    filters: Optional[SuggestionFilters] = None
) -> Optional[LeftoverSuggestionsResponse]:
    """
    Main function to get recipe suggestions based on available pantry ingredients
    
    Args:
        db: Database connection
        user_id: User's ObjectId as string
        max_suggestions: Maximum number of suggestions to return
        filters: Optional filters to apply
        
    Returns:
        LeftoverSuggestionsResponse if successful, None otherwise
    """
    try:
        start_time = datetime.utcnow()
        
        # Use provided filters or create default
        if not filters:
            filters = SuggestionFilters(max_suggestions=max_suggestions)
        
        # Get available ingredients from pantry
        available_ingredients = await get_user_available_ingredients(db, user_id)
        
        if not available_ingredients:
            logger.warning(f"No pantry items found for user {user_id}")
            return LeftoverSuggestionsResponse(
                suggestions=[],
                total_suggestions=0,
                user_id=user_id,
                pantry_items_count=0,
                recipes_analyzed=0,
                min_match_percentage=filters.min_match_percentage,
                filters_applied=filters.dict()
            )
        
        # Filter recipes by availability
        filtered_recipes = await filter_recipes_by_availability(
            db,
            available_ingredients,
            user_id,
            filters.min_match_percentage,
            filters
        )
        
        if not filtered_recipes:
            logger.info(f"No recipes match availability criteria for user {user_id}")
            return LeftoverSuggestionsResponse(
                suggestions=[],
                total_suggestions=0,
                user_id=user_id,
                pantry_items_count=len(available_ingredients),
                recipes_analyzed=0,
                min_match_percentage=filters.min_match_percentage,
                filters_applied=filters.dict()
            )
        
        # Generate suggestions
        suggestions = []
        
        for recipe in filtered_recipes:
            # Extract ingredient names
            ingredient_names = [ing.name for ing in recipe.ingredients]
            
            # Calculate match details
            match_percentage, matched_ingredients, missing_ingredients = calculate_recipe_match_score(
                ingredient_names,
                available_ingredients,
                filters.include_substitutes
            )
            
            # Calculate priority score
            priority_score, score_breakdown = calculate_suggestion_priority_score(
                recipe,
                match_percentage,
                matched_ingredients,
                available_ingredients,
                filters
            )
            
            # Create suggestion reason
            reason_parts = []
            if match_percentage >= 80:
                reason_parts.append("High ingredient match")
            elif match_percentage >= 60:
                reason_parts.append("Good ingredient match")
            else:
                reason_parts.append("Partial ingredient match")
            
            if any(ing.is_expiring_soon for match in matched_ingredients 
                   for ing in available_ingredients 
                   if ing.name == match.available_ingredient):
                reason_parts.append("uses expiring ingredients")
            
            if recipe.difficulty == "easy":
                reason_parts.append("easy to prepare")
            
            suggestion_reason = ", ".join(reason_parts).capitalize()
            
            # Create suggestion
            suggestion = LeftoverSuggestion(
                recipe=recipe,
                match_score=priority_score,
                match_percentage=match_percentage,
                matched_ingredients=matched_ingredients,
                missing_ingredients=missing_ingredients,
                total_ingredients=len(ingredient_names),
                available_ingredients_count=len(matched_ingredients),
                missing_ingredients_count=len(missing_ingredients),
                suggestion_reason=suggestion_reason,
                priority_score=priority_score,
                estimated_prep_time=recipe.prep_time,
                difficulty_bonus=score_breakdown.get("difficulty_bonus", 0.0),
                freshness_bonus=score_breakdown.get("freshness_bonus", 0.0),
                expiration_urgency=score_breakdown.get("expiration_bonus", 0.0)
            )
            
            suggestions.append(suggestion)
        
        # Rank suggestions by priority
        ranked_suggestions = rank_suggestions_by_priority(suggestions)
        
        # Limit to max suggestions
        final_suggestions = ranked_suggestions[:filters.max_suggestions]
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        logger.info(f"Generated {len(final_suggestions)} suggestions for user {user_id} in {processing_time:.2f}ms")
        
        return LeftoverSuggestionsResponse(
            suggestions=final_suggestions,
            total_suggestions=len(final_suggestions),
            user_id=user_id,
            pantry_items_count=len(available_ingredients),
            recipes_analyzed=len(filtered_recipes),
            min_match_percentage=filters.min_match_percentage,
            filters_applied=filters.dict(),
            performance_metrics={
                "processing_time_ms": processing_time,
                "total_recipes_considered": len(filtered_recipes),
                "suggestions_generated": len(suggestions)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating leftover suggestions for user {user_id}: {e}")
        return None