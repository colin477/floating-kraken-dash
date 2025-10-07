"""
Category mapping utility for standardizing categories between receipt items and pantry system.
Ensures seamless integration between receipt processing and pantry storage.
"""

from typing import Dict, List, Optional, Set
from enum import Enum
import re
from ..models.pantry import PantryCategory
from ..models.receipts import ReceiptItemCategory


class CategoryMapper:
    """
    Handles mapping between receipt item categories and pantry categories.
    Provides standardized category mapping with fallback handling.
    """
    
    # Comprehensive mapping from common receipt item names/categories to pantry categories
    ITEM_NAME_MAPPINGS: Dict[str, PantryCategory] = {
        # Produce
        "apple": PantryCategory.PRODUCE,
        "banana": PantryCategory.PRODUCE,
        "orange": PantryCategory.PRODUCE,
        "grape": PantryCategory.PRODUCE,
        "berry": PantryCategory.PRODUCE,
        "strawberry": PantryCategory.PRODUCE,
        "blueberry": PantryCategory.PRODUCE,
        "raspberry": PantryCategory.PRODUCE,
        "lettuce": PantryCategory.PRODUCE,
        "spinach": PantryCategory.PRODUCE,
        "kale": PantryCategory.PRODUCE,
        "cabbage": PantryCategory.PRODUCE,
        "tomato": PantryCategory.PRODUCE,
        "potato": PantryCategory.PRODUCE,
        "onion": PantryCategory.PRODUCE,
        "carrot": PantryCategory.PRODUCE,
        "celery": PantryCategory.PRODUCE,
        "broccoli": PantryCategory.PRODUCE,
        "cauliflower": PantryCategory.PRODUCE,
        "cucumber": PantryCategory.PRODUCE,
        "pepper": PantryCategory.PRODUCE,
        "avocado": PantryCategory.PRODUCE,
        "lemon": PantryCategory.PRODUCE,
        "lime": PantryCategory.PRODUCE,
        "garlic": PantryCategory.PRODUCE,
        "ginger": PantryCategory.PRODUCE,
        "mushroom": PantryCategory.PRODUCE,
        "zucchini": PantryCategory.PRODUCE,
        "squash": PantryCategory.PRODUCE,
        "corn": PantryCategory.PRODUCE,
        "peas": PantryCategory.PRODUCE,
        
        # Dairy
        "milk": PantryCategory.DAIRY,
        "cheese": PantryCategory.DAIRY,
        "cheddar": PantryCategory.DAIRY,
        "mozzarella": PantryCategory.DAIRY,
        "parmesan": PantryCategory.DAIRY,
        "yogurt": PantryCategory.DAIRY,
        "butter": PantryCategory.DAIRY,
        "cream": PantryCategory.DAIRY,
        "sour cream": PantryCategory.DAIRY,
        "cottage cheese": PantryCategory.DAIRY,
        "egg": PantryCategory.DAIRY,
        "eggs": PantryCategory.DAIRY,
        
        # Meat
        "beef": PantryCategory.MEAT,
        "chicken": PantryCategory.MEAT,
        "pork": PantryCategory.MEAT,
        "turkey": PantryCategory.MEAT,
        "ham": PantryCategory.MEAT,
        "bacon": PantryCategory.MEAT,
        "sausage": PantryCategory.MEAT,
        "ground beef": PantryCategory.MEAT,
        "ground turkey": PantryCategory.MEAT,
        "steak": PantryCategory.MEAT,
        "roast": PantryCategory.MEAT,
        "chop": PantryCategory.MEAT,
        "lamb": PantryCategory.MEAT,
        "deli meat": PantryCategory.MEAT,
        
        # Seafood
        "fish": PantryCategory.SEAFOOD,
        "salmon": PantryCategory.SEAFOOD,
        "tuna": PantryCategory.SEAFOOD,
        "cod": PantryCategory.SEAFOOD,
        "tilapia": PantryCategory.SEAFOOD,
        "shrimp": PantryCategory.SEAFOOD,
        "crab": PantryCategory.SEAFOOD,
        "lobster": PantryCategory.SEAFOOD,
        "scallops": PantryCategory.SEAFOOD,
        "mussels": PantryCategory.SEAFOOD,
        
        # Grains
        "bread": PantryCategory.GRAINS,
        "rice": PantryCategory.GRAINS,
        "pasta": PantryCategory.GRAINS,
        "cereal": PantryCategory.GRAINS,
        "oats": PantryCategory.GRAINS,
        "flour": PantryCategory.GRAINS,
        "wheat": PantryCategory.GRAINS,
        "bagel": PantryCategory.GRAINS,
        "tortilla": PantryCategory.GRAINS,
        "quinoa": PantryCategory.GRAINS,
        "barley": PantryCategory.GRAINS,
        "crackers": PantryCategory.GRAINS,
        
        # Beverages
        "water": PantryCategory.BEVERAGES,
        "juice": PantryCategory.BEVERAGES,
        "soda": PantryCategory.BEVERAGES,
        "coffee": PantryCategory.BEVERAGES,
        "tea": PantryCategory.BEVERAGES,
        "beer": PantryCategory.BEVERAGES,
        "wine": PantryCategory.BEVERAGES,
        "cola": PantryCategory.BEVERAGES,
        "sprite": PantryCategory.BEVERAGES,
        "pepsi": PantryCategory.BEVERAGES,
        "coke": PantryCategory.BEVERAGES,
        
        # Frozen
        "ice cream": PantryCategory.FROZEN,
        "frozen pizza": PantryCategory.FROZEN,
        "frozen vegetables": PantryCategory.FROZEN,
        "frozen fruit": PantryCategory.FROZEN,
        "frozen meals": PantryCategory.FROZEN,
        "popsicle": PantryCategory.FROZEN,
        
        # Canned Goods
        "canned soup": PantryCategory.CANNED_GOODS,
        "canned beans": PantryCategory.CANNED_GOODS,
        "canned corn": PantryCategory.CANNED_GOODS,
        "canned peas": PantryCategory.CANNED_GOODS,
        "canned tomatoes": PantryCategory.CANNED_GOODS,
        "canned": PantryCategory.CANNED_GOODS,
        "tomato sauce": PantryCategory.CANNED_GOODS,
        "pasta sauce": PantryCategory.CANNED_GOODS,
        
        # Snacks
        "chips": PantryCategory.SNACKS,
        "potato chips": PantryCategory.SNACKS,
        "cookies": PantryCategory.SNACKS,
        "candy": PantryCategory.SNACKS,
        "chocolate": PantryCategory.SNACKS,
        "nuts": PantryCategory.SNACKS,
        "popcorn": PantryCategory.SNACKS,
        "granola bar": PantryCategory.SNACKS,
        "trail mix": PantryCategory.SNACKS,
        "pretzels": PantryCategory.SNACKS,
        
        # Condiments
        "ketchup": PantryCategory.CONDIMENTS,
        "mustard": PantryCategory.CONDIMENTS,
        "mayo": PantryCategory.CONDIMENTS,
        "mayonnaise": PantryCategory.CONDIMENTS,
        "dressing": PantryCategory.CONDIMENTS,
        "salad dressing": PantryCategory.CONDIMENTS,
        "bbq sauce": PantryCategory.CONDIMENTS,
        "hot sauce": PantryCategory.CONDIMENTS,
        "soy sauce": PantryCategory.CONDIMENTS,
        "olive oil": PantryCategory.CONDIMENTS,
        "vegetable oil": PantryCategory.CONDIMENTS,
        "vinegar": PantryCategory.CONDIMENTS,
        
        # Spices
        "salt": PantryCategory.SPICES,
        "pepper": PantryCategory.SPICES,
        "basil": PantryCategory.SPICES,
        "oregano": PantryCategory.SPICES,
        "thyme": PantryCategory.SPICES,
        "rosemary": PantryCategory.SPICES,
        "paprika": PantryCategory.SPICES,
        "cumin": PantryCategory.SPICES,
        "chili powder": PantryCategory.SPICES,
        "garlic powder": PantryCategory.SPICES,
        "onion powder": PantryCategory.SPICES,
        
        # Baking
        "sugar": PantryCategory.BAKING,
        "brown sugar": PantryCategory.BAKING,
        "baking powder": PantryCategory.BAKING,
        "baking soda": PantryCategory.BAKING,
        "vanilla": PantryCategory.BAKING,
        "vanilla extract": PantryCategory.BAKING,
        "chocolate chips": PantryCategory.BAKING,
        "cocoa powder": PantryCategory.BAKING,
        "yeast": PantryCategory.BAKING,
    }
    
    # Keywords that help identify categories from item names
    KEYWORD_PATTERNS: Dict[PantryCategory, List[str]] = {
        PantryCategory.PRODUCE: [
            r'\b(fresh|organic|produce)\b',
            r'\b(apple|banana|orange|grape|berry)\b',
            r'\b(lettuce|spinach|kale|cabbage)\b',
            r'\b(tomato|potato|onion|carrot|broccoli)\b',
            r'\b(fruit|vegetable|veggie)\b',
            r'\b(avocado|cucumber|pepper|celery)\b'
        ],
        PantryCategory.DAIRY: [
            r'\b(milk|cheese|yogurt|butter|cream)\b',
            r'\b(dairy|egg|eggs)\b',
            r'\b(cheddar|mozzarella|parmesan)\b',
            r'\b(cottage|sour)\b'
        ],
        PantryCategory.MEAT: [
            r'\b(beef|chicken|pork|turkey|lamb)\b',
            r'\b(meat|deli|sausage|bacon|ham)\b',
            r'\b(ground|steak|breast|thigh|roast)\b'
        ],
        PantryCategory.SEAFOOD: [
            r'\b(fish|salmon|tuna|cod|tilapia)\b',
            r'\b(seafood|shrimp|crab|lobster)\b',
            r'\b(scallops|mussels)\b'
        ],
        PantryCategory.GRAINS: [
            r'\b(bread|pasta|rice|cereal|flour)\b',
            r'\b(grain|wheat|oats|quinoa|barley)\b',
            r'\b(bagel|tortilla|crackers)\b'
        ],
        PantryCategory.FROZEN: [
            r'\b(frozen|ice cream|popsicle)\b',
            r'\bfrozen\s+(vegetables|fruit|meals|pizza)\b'
        ],
        PantryCategory.BEVERAGES: [
            r'\b(soda|juice|water|coffee|tea)\b',
            r'\b(drink|beverage|beer|wine|alcohol)\b',
            r'\b(cola|sprite|pepsi|coke)\b'
        ],
        PantryCategory.SNACKS: [
            r'\b(chips|crackers|cookies|candy)\b',
            r'\b(snack|chocolate|popcorn|granola)\b',
            r'\b(nuts|trail mix|pretzels)\b',
            r'\bpotato\s+chips\b'
        ],
        PantryCategory.CANNED_GOODS: [
            r'\b(canned|can|jar|bottle)\b',
            r'\b(soup|sauce|beans)\b',
            r'\btomato\s+sauce\b',
            r'\bcanned\s+\w+\b'
        ],
        PantryCategory.CONDIMENTS: [
            r'\b(ketchup|mustard|mayo|dressing)\b',
            r'\b(sauce|oil|vinegar)\b',
            r'\b(bbq|hot\s+sauce|soy\s+sauce)\b'
        ],
        PantryCategory.SPICES: [
            r'\b(salt|pepper|spice|herb|seasoning)\b',
            r'\b(basil|oregano|thyme|rosemary)\b',
            r'\b(paprika|cumin|chili\s+powder)\b'
        ],
        PantryCategory.BAKING: [
            r'\b(sugar|flour|baking)\b',
            r'\b(vanilla|chocolate\s+chips|cocoa)\b',
            r'\b(yeast|powder|extract)\b'
        ]
    }
    
    @classmethod
    def map_category(cls, receipt_category: Optional[str] = None, item_name: Optional[str] = None) -> PantryCategory:
        """
        Map a receipt category and/or item name to a standardized pantry category.
        
        Args:
            receipt_category: The category from receipt processing (can be None)
            item_name: The item name to help with categorization (can be None)
            
        Returns:
            PantryCategory: The mapped pantry category
        """
        # First try direct category mapping if receipt category is provided
        if receipt_category:
            normalized_category = receipt_category.lower().strip()
            
            # Try to match receipt category to pantry category
            try:
                # Check if it's already a valid pantry category
                return PantryCategory(normalized_category)
            except ValueError:
                pass
            
            # Try mapping common receipt category names
            category_mappings = {
                "produce": PantryCategory.PRODUCE,
                "fruits": PantryCategory.PRODUCE,
                "vegetables": PantryCategory.PRODUCE,
                "fresh": PantryCategory.PRODUCE,
                "dairy": PantryCategory.DAIRY,
                "meat": PantryCategory.MEAT,
                "seafood": PantryCategory.SEAFOOD,
                "grains": PantryCategory.GRAINS,
                "bread": PantryCategory.GRAINS,
                "pantry": PantryCategory.GRAINS,  # Generic pantry items often grains
                "canned": PantryCategory.CANNED_GOODS,
                "canned_goods": PantryCategory.CANNED_GOODS,
                "frozen": PantryCategory.FROZEN,
                "beverages": PantryCategory.BEVERAGES,
                "drinks": PantryCategory.BEVERAGES,
                "snacks": PantryCategory.SNACKS,
                "condiments": PantryCategory.CONDIMENTS,
                "spices": PantryCategory.SPICES,
                "baking": PantryCategory.BAKING,
                "other": PantryCategory.OTHER
            }
            
            if normalized_category in category_mappings:
                return category_mappings[normalized_category]
        
        # Then try item name mapping
        if item_name:
            normalized_name = item_name.lower().strip()
            
            # Check direct name mapping
            for key, category in cls.ITEM_NAME_MAPPINGS.items():
                if key in normalized_name:
                    return category
            
            # Check pattern matching
            for category, patterns in cls.KEYWORD_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, normalized_name, re.IGNORECASE):
                        return category
        
        # Fallback to OTHER if no mapping found
        return PantryCategory.OTHER
    
    @classmethod
    def normalize_category_for_frontend(cls, category: PantryCategory) -> str:
        """
        Convert a PantryCategory enum to a frontend-compatible string.
        
        Args:
            category: The PantryCategory enum value
            
        Returns:
            str: The category as a string value
        """
        return category.value
    
    @classmethod
    def parse_category_from_frontend(cls, category_str: str) -> PantryCategory:
        """
        Parse a category string from frontend to PantryCategory enum.
        
        Args:
            category_str: The category string from frontend
            
        Returns:
            PantryCategory: The parsed category enum
        """
        try:
            return PantryCategory(category_str)
        except ValueError:
            # Try mapping if direct parsing fails
            return cls.map_category(receipt_category=category_str)


# Convenience instance for easy importing
category_mapper = CategoryMapper()