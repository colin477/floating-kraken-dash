"""
CRUD operations for user profile management
"""

import uuid
import logging
from typing import Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database import get_collection
from app.models.profiles import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    FamilyMember,
    FamilyMemberCreate,
    FamilyMemberUpdate
)

# Configure logging
logger = logging.getLogger(__name__)


async def create_profile(user_id: str, profile_data: UserProfileCreate) -> Optional[UserProfile]:
    """
    Create a new profile for a user
    
    Args:
        user_id: User's ObjectId as string
        profile_data: Profile creation data
        
    Returns:
        Created UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Check if user already has a profile
        existing_profile = await profiles_collection.find_one({"user_id": user_id})
        if existing_profile:
            logger.warning(f"Profile already exists for user_id: {user_id}")
            return None
        
        # Convert FamilyMemberCreate objects to FamilyMember objects with generated IDs
        family_members = []
        for member_data in profile_data.family_members:
            member = FamilyMember(
                id=str(uuid.uuid4()),
                name=member_data.name,
                age=member_data.age,
                allergies=member_data.allergies,
                dietary_restrictions=member_data.dietary_restrictions
            )
            family_members.append(member.dict())
        
        # Create profile document
        profile_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "dietary_restrictions": profile_data.dietary_restrictions,
            "allergies": profile_data.allergies,
            "taste_preferences": profile_data.taste_preferences,
            "meal_preferences": profile_data.meal_preferences,
            "kitchen_equipment": profile_data.kitchen_equipment,
            "weekly_budget": profile_data.weekly_budget,
            "zip_code": profile_data.zip_code,
            "family_members": family_members,
            "preferred_grocers": profile_data.preferred_grocers,
            "subscription": profile_data.subscription,
            "trial_ends_at": profile_data.trial_ends_at,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert profile into database
        result = await profiles_collection.insert_one(profile_doc)
        
        # Return the created profile
        created_profile = await profiles_collection.find_one({"_id": result.inserted_id})
        if created_profile:
            # Convert ObjectId to string for the response
            created_profile["_id"] = str(created_profile["_id"])
            return UserProfile(**created_profile)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error creating profile for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating profile for user {user_id}: {e}")
        return None


async def get_profile_by_user_id(user_id: str) -> Optional[UserProfile]:
    """
    Find profile by user_id
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        UserProfile object if found, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        profile = await profiles_collection.find_one({"user_id": user_id})
        if profile:
            # Convert ObjectId to string for the response
            profile["_id"] = str(profile["_id"])
            return UserProfile(**profile)
        
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting profile for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}")
        return None


async def update_profile(user_id: str, update_data: UserProfileUpdate) -> Optional[UserProfile]:
    """
    Update existing profile by user_id
    
    Args:
        user_id: User's ObjectId as string
        update_data: Profile update data
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Build update document excluding None values
        update_doc = {}
        for field, value in update_data.dict(exclude_none=True).items():
            update_doc[field] = value
        
        if not update_doc:
            # No fields to update
            return await get_profile_by_user_id(user_id)
        
        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update profile
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating profile for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        return None


async def add_family_member(user_id: str, member_data: FamilyMemberCreate) -> Optional[UserProfile]:
    """
    Add a new family member to user's profile
    
    Args:
        user_id: User's ObjectId as string
        member_data: Family member creation data
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Create family member with unique ID
        member = FamilyMember(
            id=str(uuid.uuid4()),
            name=member_data.name,
            age=member_data.age,
            allergies=member_data.allergies,
            dietary_restrictions=member_data.dietary_restrictions
        )
        
        # Add family member to profile
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {"family_members": member.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error adding family member for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error adding family member for user {user_id}: {e}")
        return None


async def update_family_member(user_id: str, member_id: str, member_data: FamilyMemberUpdate) -> Optional[UserProfile]:
    """
    Update specific family member by member_id
    
    Args:
        user_id: User's ObjectId as string
        member_id: Family member's unique ID
        member_data: Family member update data
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Build update document for family member fields excluding None values
        update_fields = {}
        for field, value in member_data.dict(exclude_none=True).items():
            update_fields[f"family_members.$.{field}"] = value
        
        if not update_fields:
            # No fields to update
            return await get_profile_by_user_id(user_id)
        
        # Add updated_at timestamp
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update specific family member
        result = await profiles_collection.update_one(
            {"user_id": user_id, "family_members.id": member_id},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating family member {member_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating family member {member_id} for user {user_id}: {e}")
        return None


async def delete_family_member(user_id: str, member_id: str) -> Optional[UserProfile]:
    """
    Remove family member by member_id from user's profile
    
    Args:
        user_id: User's ObjectId as string
        member_id: Family member's unique ID
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Remove family member from profile
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {
                "$pull": {"family_members": {"id": member_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error deleting family member {member_id} for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error deleting family member {member_id} for user {user_id}: {e}")
        return None