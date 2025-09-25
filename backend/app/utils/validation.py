"""
Comprehensive input validation utilities for API endpoints
"""

import re
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from pydantic import BaseModel, validator
import structlog

logger = structlog.get_logger(__name__)

# Validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?1?-?\.?\s?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$')
NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\'\.]{2,50}$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
INGREDIENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\'\.,()&/]{1,100}$')
RECIPE_TITLE_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\'\.,()&/!?]{1,200}$')

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),
    re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
    re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
    re.compile(r'<embed[^>]*>', re.IGNORECASE),
    re.compile(r'vbscript:', re.IGNORECASE),
    re.compile(r'data:text/html', re.IGNORECASE),
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    re.compile(r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b', re.IGNORECASE),
    re.compile(r'[\'";]', re.IGNORECASE),
    re.compile(r'--', re.IGNORECASE),
    re.compile(r'/\*.*?\*/', re.IGNORECASE | re.DOTALL),
]

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing dangerous content
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If input contains dangerous content
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Check length
    if len(value) > max_length:
        raise ValidationError(f"Input too long. Maximum {max_length} characters allowed")
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(value):
            logger.warning(f"Dangerous pattern detected in input: {value[:100]}...")
            raise ValidationError("Input contains potentially dangerous content")
    
    # Check for SQL injection patterns (even though we use MongoDB)
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            logger.warning(f"SQL injection pattern detected in input: {value[:100]}...")
            raise ValidationError("Input contains potentially malicious content")
    
    # Basic HTML entity encoding for safety
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&#x27;')
    
    return value.strip()

def validate_email(email: str) -> str:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email is required")
    
    email = email.strip().lower()
    
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address too long")
    
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")
    
    # Additional checks
    local, domain = email.split('@')
    if len(local) > 64:  # RFC 5321 limit
        raise ValidationError("Email local part too long")
    
    return email

def validate_name(name: str, field_name: str = "Name") -> str:
    """
    Validate name fields (first name, last name, etc.)
    
    Args:
        name: Name to validate
        field_name: Name of the field for error messages
        
    Returns:
        Sanitized name
        
    Raises:
        ValidationError: If name format is invalid
    """
    if not name:
        raise ValidationError(f"{field_name} is required")
    
    name = sanitize_string(name, 50)
    
    if not NAME_PATTERN.match(name):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    if len(name) < 2:
        raise ValidationError(f"{field_name} must be at least 2 characters long")
    
    return name.title()

def validate_phone(phone: str) -> Optional[str]:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Normalized phone number or None if empty
        
    Raises:
        ValidationError: If phone format is invalid
    """
    if not phone:
        return None
    
    phone = re.sub(r'[^\d+]', '', phone)  # Remove all non-digit characters except +
    
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("Invalid phone number format")
    
    return phone

def validate_ingredient_name(name: str) -> str:
    """
    Validate ingredient name
    
    Args:
        name: Ingredient name to validate
        
    Returns:
        Sanitized ingredient name
        
    Raises:
        ValidationError: If name format is invalid
    """
    if not name:
        raise ValidationError("Ingredient name is required")
    
    name = sanitize_string(name, 100)
    
    if not INGREDIENT_NAME_PATTERN.match(name):
        raise ValidationError("Ingredient name contains invalid characters")
    
    return name.strip()

def validate_recipe_title(title: str) -> str:
    """
    Validate recipe title
    
    Args:
        title: Recipe title to validate
        
    Returns:
        Sanitized recipe title
        
    Raises:
        ValidationError: If title format is invalid
    """
    if not title:
        raise ValidationError("Recipe title is required")
    
    title = sanitize_string(title, 200)
    
    if not RECIPE_TITLE_PATTERN.match(title):
        raise ValidationError("Recipe title contains invalid characters")
    
    if len(title) < 3:
        raise ValidationError("Recipe title must be at least 3 characters long")
    
    return title.strip()

def validate_quantity(quantity: Union[int, float, str]) -> float:
    """
    Validate quantity values
    
    Args:
        quantity: Quantity to validate
        
    Returns:
        Validated quantity as float
        
    Raises:
        ValidationError: If quantity is invalid
    """
    try:
        qty = float(quantity)
        if qty < 0:
            raise ValidationError("Quantity cannot be negative")
        if qty > 10000:  # Reasonable upper limit
            raise ValidationError("Quantity too large")
        return qty
    except (ValueError, TypeError):
        raise ValidationError("Invalid quantity format")

def validate_url(url: str, field_name: str = "URL") -> Optional[str]:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated URL or None if empty
        
    Raises:
        ValidationError: If URL format is invalid
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValidationError(f"Invalid {field_name} format")
    
    if len(url) > 2048:  # Reasonable URL length limit
        raise ValidationError(f"{field_name} too long")
    
    return url

def validate_text_content(content: str, min_length: int = 1, max_length: int = 5000, field_name: str = "Content") -> str:
    """
    Validate text content (descriptions, instructions, etc.)
    
    Args:
        content: Text content to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
        
    Returns:
        Sanitized content
        
    Raises:
        ValidationError: If content is invalid
    """
    if not content:
        if min_length > 0:
            raise ValidationError(f"{field_name} is required")
        return ""
    
    content = sanitize_string(content, max_length)
    
    if len(content) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long")
    
    return content.strip()

def validate_list_items(items: List[Any], max_items: int = 100, field_name: str = "Items") -> List[Any]:
    """
    Validate list of items
    
    Args:
        items: List to validate
        max_items: Maximum number of items allowed
        field_name: Name of the field for error messages
        
    Returns:
        Validated list
        
    Raises:
        ValidationError: If list is invalid
    """
    if not isinstance(items, list):
        raise ValidationError(f"{field_name} must be a list")
    
    if len(items) > max_items:
        raise ValidationError(f"Too many {field_name.lower()}. Maximum {max_items} allowed")
    
    return items

def validate_object_id(obj_id: str, field_name: str = "ID") -> str:
    """
    Validate MongoDB ObjectId format
    
    Args:
        obj_id: Object ID to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated object ID
        
    Raises:
        ValidationError: If object ID format is invalid
    """
    if not obj_id:
        raise ValidationError(f"{field_name} is required")
    
    # MongoDB ObjectId is 24 character hex string
    if not re.match(r'^[0-9a-fA-F]{24}$', obj_id):
        raise ValidationError(f"Invalid {field_name} format")
    
    return obj_id

def validate_pagination_params(skip: int = 0, limit: int = 20) -> tuple[int, int]:
    """
    Validate pagination parameters
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Validated skip and limit values
        
    Raises:
        ValidationError: If parameters are invalid
    """
    if skip < 0:
        raise ValidationError("Skip parameter cannot be negative")
    
    if skip > 10000:  # Reasonable limit for performance
        raise ValidationError("Skip parameter too large")
    
    if limit < 1:
        raise ValidationError("Limit parameter must be at least 1")
    
    if limit > 100:  # Reasonable limit for performance
        raise ValidationError("Limit parameter too large. Maximum 100 allowed")
    
    return skip, limit

def create_validation_error_response(error: ValidationError) -> HTTPException:
    """
    Create HTTP exception from validation error
    
    Args:
        error: Validation error
        
    Returns:
        HTTP exception
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "Validation Error",
            "message": error.message,
            "field": error.field
        }
    )

# Decorator for automatic validation error handling
def handle_validation_errors(func):
    """
    Decorator to automatically handle validation errors
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e.message}")
            raise create_validation_error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper