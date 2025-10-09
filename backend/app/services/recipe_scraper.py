
"""
Recipe web scraping service for extracting recipes from popular recipe websites
"""

import logging
import re
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import extruct
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models.recipes import RecipeCreate, RecipeIngredient, RecipeNutrition, DifficultyLevel, MealType, DietaryRestriction

# Configure logging
logger = logging.getLogger(__name__)


class RecipeScraperService:
    """Service for scraping recipes from various websites"""
    
    def __init__(self):
        # Configure requests session with retries and proper headers
        self.session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Supported recipe websites
        self.supported_domains = {
            'allrecipes.com',
            'food.com',
            'foodnetwork.com',
            'bonappetit.com',
            'seriouseats.com',
            'epicurious.com',
            'delish.com',
            'tasteofhome.com',
            'simplyrecipes.com',
            'thekitchn.com',
            'cooking.nytimes.com',
            'bbc.co.uk',
            'jamieoliver.com',
            'recipetineats.com',
            'minimalistbaker.com',
            'budgetbytes.com'
        }
        
        # Common recipe schema types
        self.recipe_schema_types = [
            'Recipe',
            'recipe',
            'http://schema.org/Recipe',
            'https://schema.org/Recipe'
        ]
    
    async def scrape_recipe(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape recipe from URL using structured data and fallback HTML parsing
        
        Args:
            url: Recipe URL to scrape
            
        Returns:
            Dictionary with recipe data if successful, None otherwise
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                logger.error(f"Invalid URL: {url}")
                return None
            
            # Check if domain is supported
            domain = self._extract_domain(url)
            if not self._is_supported_domain(domain):
                logger.warning(f"Domain {domain} may not be fully supported")
            
            # Fetch webpage content
            response = await self._fetch_webpage(url)
            if not response:
                return None
            
            # Try structured data extraction first
            recipe_data = await self._extract_structured_data(response.text, url)
            
            # If structured data fails, try HTML parsing
            if not recipe_data:
                recipe_data = await self._extract_from_html(response.text, url, domain)
            
            if recipe_data:
                # Add metadata
                recipe_data['source_url'] = url
                recipe_data['scraped_at'] = datetime.utcnow().isoformat()
                recipe_data['scraping_method'] = recipe_data.get('scraping_method', 'unknown')
                
                logger.info(f"Successfully scraped recipe from {url}")
                return recipe_data
            
            logger.error(f"Failed to extract recipe data from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping recipe from {url}: {e}")
            return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc.lower().replace('www.', '')
        except Exception:
            return ''
    
    def _is_supported_domain(self, domain: str) -> bool:
        """Check if domain is in supported list"""
        return domain in self.supported_domains
    
    async def _fetch_webpage(self, url: str) -> Optional[requests.Response]:
        """Fetch webpage content with error handling"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.get(url, timeout=30)
            )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    async def _extract_structured_data(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract recipe from structured data (JSON-LD, microdata, RDFa)"""
        try:
            # Extract all structured data
            data = extruct.extract(html_content, base_url=url)
            
            # Check JSON-LD first (most reliable)
            if 'json-ld' in data:
                recipe_data = self._find_recipe_in_jsonld(data['json-ld'])
                if recipe_data:
                    recipe_data['scraping_method'] = 'json-ld'
                    return recipe_data
            
            # Check microdata
            if 'microdata' in data:
                recipe_data = self._find_recipe_in_microdata(data['microdata'])
                if recipe_data:
                    recipe_data['scraping_method'] = 'microdata'
                    return recipe_data
            
            # Check RDFa
            if 'rdfa' in data:
                recipe_data = self._find_recipe_in_rdfa(data['rdfa'])
                if recipe_data:
                    recipe_data['scraping_method'] = 'rdfa'
                    return recipe_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return None
    
    def _find_recipe_in_jsonld(self, json_ld_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """Find recipe in JSON-LD data"""
        try:
            for item in json_ld_data:
                if isinstance(item, dict):
                    # Handle @graph structure
                    if '@graph' in item:
                        for graph_item in item['@graph']:
                            if self._is_recipe_type(graph_item.get('@type')):
                                return self._parse_recipe_jsonld(graph_item)
                    
                    # Handle direct recipe
                    elif self._is_recipe_type(item.get('@type')):
                        return self._parse_recipe_jsonld(item)
                    
                    # Handle nested recipes
                    elif 'recipe' in item:
                        recipe_item = item['recipe']
                        if isinstance(recipe_item, dict) and self._is_recipe_type(recipe_item.get('@type')):
                            return self._parse_recipe_jsonld(recipe_item)
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing JSON-LD recipe data: {e}")
            return None
    
    def _find_recipe_in_microdata(self, microdata: List[Dict]) -> Optional[Dict[str, Any]]:
        """Find recipe in microdata"""
        try:
            for item in microdata:
                if isinstance(item, dict) and self._is_recipe_type(item.get('type')):
                    return self._parse_recipe_microdata(item)
            return None
        except Exception as e:
            logger.error(f"Error parsing microdata recipe: {e}")
            return None
    
    def _find_recipe_in_rdfa(self, rdfa_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """Find recipe in RDFa data"""
        try:
            for item in rdfa_data:
                if isinstance(item, dict) and self._is_recipe_type(item.get('@type')):
                    return self._parse_recipe_rdfa(item)
            return None
        except Exception as e:
            logger.error(f"Error parsing RDFa recipe: {e}")
            return None
    
    def _is_recipe_type(self, type_value: Any) -> bool:
        """Check if type indicates a recipe"""
        if not type_value:
            return False
        
        if isinstance(type_value, str):
            return type_value in self.recipe_schema_types
        
        if isinstance(type_value, list):
            return any(t in self.recipe_schema_types for t in type_value)
        
        return False
    
    def _parse_recipe_jsonld(self, recipe_data: Dict) -> Dict[str, Any]:
        """Parse recipe from JSON-LD format"""
        try:
            parsed_recipe = {}
            
            # Basic information
            parsed_recipe['title'] = self._extract_text(recipe_data.get('name', ''))
            parsed_recipe['description'] = self._extract_text(recipe_data.get('description', ''))
            
            # Instructions
            instructions = self._extract_instructions_jsonld(recipe_data.get('recipeInstructions', []))
            parsed_recipe['instructions'] = instructions
            
            # Ingredients
            ingredients = self._extract_ingredients_jsonld(recipe_data.get('recipeIngredient', []))
            parsed_recipe['ingredients'] = ingredients
            
            # Times
            parsed_recipe['prep_time'] = self._parse_duration(recipe_data.get('prepTime'))
            parsed_recipe['cook_time'] = self._parse_duration(recipe_data.get('cookTime'))
            
            # Servings/Yield
            yield_value = recipe_data.get('recipeYield') or recipe_data.get('yield')
            parsed_recipe['servings'] = self._parse_servings(yield_value)
            
            # Category and cuisine
            parsed_recipe['meal_types'] = self._extract_meal_types(recipe_data.get('recipeCategory', []))
            parsed_recipe['tags'] = self._extract_tags(recipe_data)
            
            # Nutrition
            nutrition = recipe_data.get('nutrition')
            if nutrition:
                parsed_recipe['nutrition_info'] = self._parse_nutrition_jsonld(nutrition)
            
            # Image
            image = recipe_data.get('image')
            if image:
                parsed_recipe['photo_url'] = self._extract_image_url(image)
            
            # Difficulty (estimate based on instructions and ingredients)
            parsed_recipe['difficulty'] = self._estimate_difficulty(instructions, ingredients)
            
            return parsed_recipe
            
        except Exception as e:
            logger.error(f"Error parsing JSON-LD recipe: {e}")
            return {}
    
    def _parse_recipe_microdata(self, recipe_data: Dict) -> Dict[str, Any]:
        """Parse recipe from microdata format"""
        try:
            parsed_recipe = {}
            properties = recipe_data.get('properties', {})
            
            # Basic information
            parsed_recipe['title'] = self._extract_text(properties.get('name', [''])[0])
            parsed_recipe['description'] = self._extract_text(properties.get('description', [''])[0])
            
            # Instructions
            instructions = self._extract_instructions_microdata(properties.get('recipeInstructions', []))
            parsed_recipe['instructions'] = instructions
            
            # Ingredients
            ingredients = self._extract_ingredients_microdata(properties.get('recipeIngredient', []))
            parsed_recipe['ingredients'] = ingredients
            
            # Times
            parsed_recipe['prep_time'] = self._parse_duration(properties.get('prepTime', [''])[0])
            parsed_recipe['cook_time'] = self._parse_duration(properties.get('cookTime', [''])[0])
            
            # Servings
            yield_value = properties.get('recipeYield', [''])[0] or properties.get('yield', [''])[0]
            parsed_recipe['servings'] = self._parse_servings(yield_value)
            
            # Category
            parsed_recipe['meal_types'] = self._extract_meal_types(properties.get('recipeCategory', []))
            parsed_recipe['tags'] = self._extract_tags_microdata(properties)
            
            # Difficulty
            parsed_recipe['difficulty'] = self._estimate_difficulty(instructions, ingredients)
            
            return parsed_recipe
            
        except Exception as e:
            logger.error(f"Error parsing microdata recipe: {e}")
            return {}
    
    def _parse_recipe_rdfa(self, recipe_data: Dict) -> Dict[str, Any]:
        """Parse recipe from RDFa format"""
        # Similar to microdata parsing but with RDFa structure
        return self._parse_recipe_microdata(recipe_data)
    
    async def _extract_from_html(self, html_content: str, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Extract recipe using HTML parsing as fallback"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try domain-specific extractors
            if domain in ['allrecipes.com']:
                return self._extract_allrecipes(soup)
            elif domain in ['food.com']:
                return self._extract_food_com(soup)
            elif domain in ['foodnetwork.com']:
                return self._extract_foodnetwork(soup)
            else:
                # Generic HTML extraction
                return self._extract_generic_html(soup)
            
        except Exception as e:
            logger.error(f"Error extracting from HTML: {e}")
            return None
    
    def _extract_allrecipes(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract recipe from AllRecipes.com"""
        try:
            recipe = {}
            
            # Title
            title_elem = soup.find('h1', class_='recipe-summary__h1')
            if title_elem:
                recipe['title'] = title_elem.get_text(strip=True)
            
            # Description
            desc_elem = soup.find('div', class_='recipe-summary__description')
            if desc_elem:
                recipe['description'] = desc_elem.get_text(strip=True)
            
            # Ingredients
            ingredients = []
            ingredient_elems = soup.find_all('span', class_='recipe-ingred_txt')
            for elem in ingredient_elems:
                text = elem.get_text(strip=True)
                if text:
                    ingredient = self._parse_ingredient_text(text)
                    if ingredient:
                        ingredients.append(ingredient)
            recipe['ingredients'] = ingredients
            
            # Instructions
            instructions = []
            instruction_elems = soup.find_all('span', class_='recipe-directions__list--item')
            for elem in instruction_elems:
                text = elem.get_text(strip=True)
                if text:
                    instructions.append(text)
            recipe['instructions'] = instructions
            
            # Times
            prep_time_elem = soup.find('time', {'itemprop': 'prepTime'})
            if prep_time_elem:
                recipe['prep_time'] = self._parse_duration(prep_time_elem.get('datetime'))
            
            cook_time_elem = soup.find('time', {'itemprop': 'cookTime'})
            if cook_time_elem:
                recipe['cook_time'] = self._parse_duration(cook_time_elem.get('datetime'))
            
            # Servings
            servings_elem = soup.find('span', {'id': 'makes-value'})
            if servings_elem:
                recipe['servings'] = self._parse_servings(servings_elem.get_text(strip=True))
            
            recipe['difficulty'] = self._estimate_difficulty(instructions, ingredients)
            recipe['scraping_method'] = 'html_allrecipes'
            
            return recipe if recipe.get('title') and recipe.get('ingredients') else None
            
        except Exception as e:
            logger.error(f"Error extracting AllRecipes recipe: {e}")
            return None
    
    def _extract_food_com(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract recipe from Food.com"""
        # Similar implementation for Food.com
        return self._extract_generic_html(soup)
    
    def _extract_foodnetwork(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract recipe from Food Network"""
        # Similar implementation for Food Network
        return self._extract_generic_html(soup)
    
    def _extract_generic_html(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Generic HTML extraction for unsupported sites"""
        try:
            recipe = {}
            
            # Try to find title
            title_selectors = [
                'h1[itemprop="name"]',
                'h1.recipe-title',
                'h1.entry-title',
                '.recipe-header h1',
                'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    recipe['title'] = title_elem.get_text(strip=True)
                    break
            
            # Try to find ingredients
            ingredients = []
            ingredient_selectors = [
                '[itemprop="recipeIngredient"]',
                '.recipe-ingredient',
                '.ingredient',
                '.ingredients li'
            ]
            
            for selector in ingredient_selectors:
                ingredient_elems = soup.select(selector)
                if ingredient_elems:
                    for elem in ingredient_elems:
                        text = elem.get_text(strip=True)
                        if text:
                            ingredient = self._parse_ingredient_text(text)
                            if ingredient:
                                ingredients.append(ingredient)
                    break
            
            recipe['ingredients'] = ingredients
            
            # Try to find instructions
            instructions = []
            instruction_selectors = [
                '[itemprop="recipeInstructions"]',
                '.recipe-instruction',
                '.instruction',
                '.directions li',
                '.method li'
            ]
            
            for selector in instruction_selectors:
                instruction_elems = soup.select(selector)
                if instruction_elems:
                    for elem in instruction_elems:
                        text = elem.get_text(strip=True)
                        if text:
                            instructions.append(text)
                    break
            
            recipe['instructions'] = instructions
            
            # Estimate difficulty and set defaults
            recipe['difficulty'] = self._estimate_difficulty(instructions, ingredients)
            recipe['servings'] = 4  # Default servings
            recipe['scraping_method'] = 'html_generic'
            
            return recipe if recipe.get('title') and recipe.get('ingredients') else None
            
        except Exception as e:
            logger.error(f"Error in generic HTML extraction: {e}")
            return None
    
    def _extract_text(self, value: Any) -> str:
        """Extract text from various data types"""
        if isinstance(value, str):
            return value.strip()
        elif isinstance(value, list) and value:
            return str(value[0]).strip()
        elif isinstance(value, dict) and 'text' in value:
            return value['text'].strip()
        return ''
    
    def _extract_instructions_jsonld(self, instructions_data: List) -> List[str]:
        """Extract instructions from JSON-LD format"""
        instructions = []
        
        for instruction in instructions_data:
            if isinstance(instruction, str):
                instructions.append(instruction.strip())
            elif isinstance(instruction, dict):
                text = instruction.get('text') or instruction.get('name') or instruction.get('@value', '')
                if text:
                    instructions.append(str(text).strip())
        
        return [inst for inst in instructions if inst]
    
    def _extract_instructions_microdata(self, instructions_data: List) -> List[str]:
        """Extract instructions from microdata format"""
        instructions = []
        
        for instruction in instructions_data:
            if isinstance(instruction, str):
                instructions.append(instruction.strip())
            elif isinstance(instruction, dict):
                properties = instruction.get('properties', {})
                text = properties.get('text', [''])[0] or properties.get('name', [''])[0]
                if text:
                    instructions.append(str(text).strip())
        
        return [inst for inst in instructions if inst]
    
    def _extract_ingredients_jsonld(self, ingredients_data: List) -> List[Dict[str, Any]]:
        """Extract ingredients from JSON-LD format"""
        ingredients = []
        
        for ingredient_text in ingredients_data:
            if isinstance(ingredient_text, str):
                ingredient = self._parse_ingredient_text(ingredient_text)
                if ingredient:
                    ingredients.append(ingredient)
        
        return ingredients
    
    def _extract_ingredients_microdata(self, ingredients_data: List) -> List[Dict[str, Any]]:
        """Extract ingredients from microdata format"""
        ingredients = []
        
        for ingredient in ingredients_data:
            if isinstance(ingredient, str):
                parsed = self._parse_ingredient_text(ingredient)
                if parsed:
                    ingredients.append(parsed)
        
        return ingredients
    
    def _parse_ingredient_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse ingredient text into structured format"""
        try:
            text = text.strip()
            if not text:
                return None
            
            # Common patterns for ingredient parsing
            # Pattern: "2 cups flour" or "1/2 teaspoon salt"
            pattern = r'^(\d+(?:\s*\d+/\d+|\.\d+)?)\s+(\w+(?:\s+\w+)?)\s+(.+)$'
            match = re.match(pattern, text)
            
            if match:
                quantity_str, unit, name = match.groups()
                
                # Parse quantity (handle fractions)
                quantity = self._parse_quantity(quantity_str)
                
                return {
                    'name': name.strip(),
                    'quantity': quantity,
                    'unit': unit.strip(),
                    'notes': None
                }
            else:
                # If no quantity/unit pattern, treat as ingredient name only
                return {
                    'name': text,
                    'quantity': 1.0,
                    'unit': 'piece',
                    'notes': None
                }
        
        except Exception as e:
            logger.error(f"Error parsing ingredient text '{text}': {e}")
            return None
    
    def _parse_quantity(self, quantity_str: str) -> float:
        """Parse quantity string including fractions"""
        try:
            quantity_str = quantity_str.strip()
            
            # Handle fractions like "1/2" or "1 1/2"
            if '/' in quantity_str:
                parts = quantity_str.split()
                if len(parts) == 1:
                    # Simple fraction like "1/2"
                    num, denom = parts[0].split('/')
                    return float(num) / float(denom)
                elif len(parts) == 2:
                    # Mixed number like "1 1/2"
                    whole = float(parts[0])
                    num, denom = parts[1].split('/')
                    return whole + (float(num) / float(denom))
            
            # Regular number
            return float(quantity_str)
            
        except Exception:
            return 1.0  # Default quantity
    
    def _parse_duration(self, duration_str: Any) -> Optional[int]:
        """Parse duration string to minutes"""
        if not duration_str:
            return None
        
        try:
            duration_str = str(duration_str).lower()
            
            # ISO 8601 duration format (PT15M, PT1H30M)
            if duration_str.startswith('pt'):
                minutes = 0
                # Extract hours
                hour_match = re.search(r'(\d+)h', duration_str)
                if hour_match:
                    minutes += int(hour_match.group(1)) * 60
                
                # Extract minutes
                min_match = re.search(r'(\d+)m', duration_str)
                if min_match:
                    minutes += int(min_match.group(1))
                
                return minutes if minutes > 0 else None
            
            # Text format (15 minutes, 1 hour 30 minutes)
            total_minutes = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)', duration_str)
            if hour_match:
                total_minutes += int(hour_match.group(1)) * 60
            
            # Extract minutes
            min_match = re.search(r'(\d+)\s*(?:minute|min|m)', duration_str)
            if min_match:
                total_minutes += int(min_match.group(1))
            
            # If no specific unit, assume it's minutes
            if total_minutes == 0:
                number_match = re.search(r'(\d+)', duration_str)
                if number_match:
                    total_minutes = int(number_match.group(1))
            
            return total_minutes if total_minutes > 0 else None
            
        except Exception as e:
            logger.error(f"Error parsing duration '{duration_str}': {e}")
            return None
    
    def _parse_servings(self, servings_str: Any) -> int:
        """Parse servings string to integer"""
        if not servings_str:
            return 4  # Default servings
        
        try:
            servings_str = str(servings_str).lower()
            
            # Extract first number found
            number_match = re.search(r'(\d+)', servings_str)
            if number_match:
                servings = int(number_match.group(1))
                return max(1, min(servings, 20))  # Clamp between 1 and 20
            
            return 4  # Default
            
        except Exception:
            return 4  # Default
    
    def _extract_meal_types(self, categories: Any) -> List[str]:
        """Extract meal types from recipe categories"""
        if not categories:
            return []
        
        if isinstance(categories, str):
            categories = [categories]
        
        meal_types = []
        category_mapping = {
            'breakfast': MealType.BREAKFAST,
            'lunch': MealType.LUNCH,
            'dinner': MealType.DINNER,
            'dessert': MealType.DESSERT,
            'snack': MealType.SNACK,
            'appetizer': MealType.APPETIZER,
            'beverage': MealType.BEVERAGE,
        }
        
        for category in categories:
            category_lower = str(category).lower()
            for key, meal_type in category_mapping.items():
                if key in category_lower:
                    meal_types.append(meal_type.value)
                    break
        
        return list(set(meal_types))  # Remove duplicates
    
    def _extract_tags(self, recipe_data: Dict) -> List[str]:
        """Extract tags from recipe data"""
        tags = []
        
        # Extract from various fields
        for field in ['keywords', 'recipeCuisine', 'recipeCategory']:
            value = recipe_data.get(field)
            if value:
                if isinstance(value, str):
                    tags.extend([tag.strip().lower() for tag in value.split(',')])
                elif isinstance(value, list):
                    tags.extend([str(tag).strip().lower() for tag in value])
        
        return list(set([tag for tag in tags if tag]))  # Remove duplicates and empty
    
    def _extract_tags_microdata(self, properties: Dict) -> List[str]:
        """Extract tags from microdata properties"""
        tags = []
        
        for field in ['keywords', 'recipeCuisine', 'recipeCategory']:
            values = properties.get(field, [])
            for value in values:
                if isinstance(value, str):
                    tags.extend([tag.strip().lower() for tag in value.split(',')])
        
        return list(set([tag for tag in tags if tag]))
    
    def _parse_nutrition_jsonld(self, nutrition_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse nutrition information from JSON-LD"""
        try:
            nutrition = {}
            
            # Map common nutrition fields
            field_mapping = {
                'calories': 'calories_per_serving',
                'protein': 'protein_g',
                'carbohydrate': 'carbs_g',
                'fat': 'fat_g',
                'fiber': 'fiber_g',
                'sugar': 'sugar_g',
                'sodium': 'sodium_mg'
            }
            
            for source_field, target_field in field_mapping.items():
                value = nutrition_data.get(source_field)
                if value:
                    # Extract numeric value
                    if isinstance(value, (int, float)):
                        nutrition[target_field] = float(value)
                    elif isinstance(value, str):
                        number_match = re.search(r'(\d+(?:\.\d+)?)', value)
                        if number_match:
                            nutrition[target_field] = float(number_match.group(1))
            
            return nutrition if nutrition else None
            
        except Exception as e:
            logger.error(f"Error parsing nutrition data: {e}")
            return None
    
    def _extract_image_url(self, image_data: Any) -> Optional[str]:
        """Extract image URL from various formats"""
        try:
            if isinstance(image_data, str):
                return image_data
            elif isinstance(image_data, list) and image_data:
                return str(image_data[0])
            elif isinstance(image_data, dict):
                return image_data.get('url') or image_data.get('@id')
            return None
        except Exception:
            return None
    
    def _estimate_difficulty(self, instructions: List[str], ingredients: List[Dict]) -> str:
        """Estimate recipe difficulty based on instructions and ingredients"""
        try:
            score = 0
            
            # Factor 1: Number of ingredients
            ingredient_count = len(ingredients)
            if ingredient_count > 15:
                score += 2
            elif ingredient_count > 10:
                score += 1
            
            # Factor 2: Number of instructions
            instruction_count = len(instructions)
            if instruction_count > 10:
                score += 2
            elif instruction_count > 6:
                score += 1
            
            # Factor 3: Complex cooking techniques
            complex_techniques = [
                'braise', 'confit', 'sous vide', 'flambé', 'tempering',
                'fold', 'whip', 'emulsify', 'reduce', 'deglaze'
            ]
            
            instruction_text = ' '.join(instructions).lower()
            for technique in complex_techniques:
                if technique in instruction_text:
                    score += 1
            
            # Factor 4: Multiple cooking methods
            cooking_methods = ['bake', 'fry', 'sauté', 'boil', 'grill', 'roast']
            methods_used = sum(1 for method in cooking_methods if method in instruction_text)
            if methods_used > 2:
                score += 1
            
            # Determine difficulty level
            if score >= 4:
                return DifficultyLevel.HARD.value
            elif score >= 2:
                return DifficultyLevel.MEDIUM.value
            else:
                return DifficultyLevel.EASY.value
                
        except Exception as e:
            logger.error(f"Error estimating difficulty: {e}")
            return DifficultyLevel.MEDIUM.value  # Default to medium
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported recipe domains"""
        return list(self.supported_domains)
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported domain"""
        try:
            domain = self._extract_domain(url)
            return self._is_supported_domain(domain)
        except Exception:
            return False


# Global recipe scraper service instance
recipe_scraper = RecipeScraperService()