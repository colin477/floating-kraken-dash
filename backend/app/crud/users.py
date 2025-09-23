"""
CRUD operations for user management
"""

from typing import Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.database import get_collection
from app.models.auth import User, UserCreate
from app.utils.auth import hash_password


async def create_user_indexes():
    """
    Create database indexes for users collection
    """
    try:
        users_collection = await get_collection("users")
        # Create unique index on email
        await users_collection.create_index("email", unique=True)
        return True
    except Exception as e:
        print(f"Error creating user indexes: {e}")
        return False


async def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user by email address
    
    Args:
        email: User's email address
        
    Returns:
        User document if found, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        user = await users_collection.find_one({"email": email})
        return user
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Get user by ID
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        User document if found, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        if not ObjectId.is_valid(user_id):
            return None
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


async def create_user(user_data: UserCreate) -> Optional[dict]:
    """
    Create a new user
    
    Args:
        user_data: User creation data
        
    Returns:
        Created user document if successful, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        
        # Check if user already exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            return None
        
        # Hash the password
        password_hash = hash_password(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert user into database
        result = await users_collection.insert_one(user_doc)
        
        # Return the created user
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        return created_user
        
    except DuplicateKeyError:
        # Email already exists
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """
    Update user information
    
    Args:
        user_id: User's ObjectId as string
        update_data: Dictionary of fields to update
        
    Returns:
        Updated user document if successful, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        
        if not ObjectId.is_valid(user_id):
            return None
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated user
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        return updated_user
        
    except Exception as e:
        print(f"Error updating user: {e}")
        return None


async def delete_user(user_id: str) -> bool:
    """
    Delete a user (soft delete by setting is_active to False)
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        users_collection = await get_collection("users")
        
        if not ObjectId.is_valid(user_id):
            return False
        
        # Soft delete by setting is_active to False
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user with email and password
    
    Args:
        email: User's email address
        password: Plain text password
        
    Returns:
        User document if authentication successful, None otherwise
    """
    try:
        from app.utils.auth import verify_password
        
        # Get user by email
        user = await get_user_by_email(email)
        if not user:
            return None
        
        # Check if user is active
        if not user.get("is_active", True):
            return None
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return None
        
        return user
        
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


async def update_user_last_login(user_id: str) -> bool:
    """
    Update user's last login timestamp
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        users_collection = await get_collection("users")
        
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        print(f"Error updating last login: {e}")
        return False