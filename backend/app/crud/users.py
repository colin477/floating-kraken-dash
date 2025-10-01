from datetime import datetime
from typing import Optional
from ..database import get_collection
from ..utils.auth import hash_password, verify_password
from ..models.auth import UserCreate
from ..utils.exceptions import EmailAlreadyExistsError, UserCreationError

async def create_user_indexes():
    """Create indexes for the users collection"""
    users_collection = await get_collection("users")
    await users_collection.create_index("email", unique=True)

async def create_user(user_data: UserCreate) -> dict:
    """Creates a new user in the database"""
    users_collection = await get_collection("users")
    
    # Check if email already exists
    if await users_collection.find_one({"email": user_data.email.lower()}):
        raise EmailAlreadyExistsError()

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user document
    user_document = {
        "email": user_data.email.lower(),
        "full_name": user_data.full_name,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "is_active": True,
    }

    try:
        result = await users_collection.insert_one(user_document)
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        return created_user
    except Exception as e:
        raise UserCreationError(f"Failed to create user: {e}")


async def authenticate_user(email: str, password: str, request: object) -> Optional[dict]:
    """Authenticate a user by email and password."""
    users_collection = await get_collection("users")
    user = await users_collection.find_one({"email": email.lower()})

    if user and verify_password(password, user["password_hash"]):
        return user
    return None

async def update_user_last_login(user_id: str):
    """Updates the last_login field for a user."""
    users_collection = await get_collection("users")
    from bson import ObjectId
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": datetime.utcnow()}}
    )