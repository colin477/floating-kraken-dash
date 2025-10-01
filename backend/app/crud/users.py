from ..database import get_collection

async def create_user_indexes():
    """Create indexes for the users collection"""
    users_collection = await get_collection("users")
    await users_collection.create_index("email", unique=True)