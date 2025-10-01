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
                dietary_restrictions=member_data.dietary_restrictions,
                loved_foods=member_data.loved_foods,
                disliked_foods=member_data.disliked_foods
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
            "family_members": family_members,
            "preferred_grocers": profile_data.preferred_grocers,
            "subscription": profile_data.subscription,
            "trial_ends_at": profile_data.trial_ends_at,
            "onboarding_completed": profile_data.onboarding_completed,
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
        logger.info(f"Raw profile from database: {profile}")
        
        if profile:
            # Convert ObjectId to string for the response
            profile["_id"] = str(profile["_id"])
            logger.info(f"Profile after ObjectId conversion: {profile}")
            
            try:
                user_profile = UserProfile(**profile)
                logger.info(f"Successfully created UserProfile object")
                return user_profile
            except Exception as validation_error:
                logger.error(f"UserProfile validation error: {validation_error}")
                logger.error(f"Profile data that failed validation: {profile}")
                return None
        
        logger.info(f"No profile found for user_id: {user_id}")
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error getting profile for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception args: {e.args}")
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
            dietary_restrictions=member_data.dietary_restrictions,
            loved_foods=member_data.loved_foods,
            disliked_foods=member_data.disliked_foods
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


async def create_profile_stub(user_id: str) -> Optional[UserProfile]:
    """
    Create a minimal profile stub for a new user with onboarding_completed: false
    
    Args:
        user_id: User's ObjectId as string
        
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
        
        # Create minimal profile stub
        profile_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "dietary_restrictions": [],
            "allergies": [],
            "taste_preferences": [],
            "meal_preferences": [],
            "kitchen_equipment": [],
            "weekly_budget": None,
            "family_members": [],
            "preferred_grocers": [],
            "subscription": "free",
            "setup_level": None,
            "trial_ends_at": None,
            "onboarding_completed": False,
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
        logger.error(f"Database error creating profile stub for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating profile stub for user {user_id}: {e}")
        return None


async def get_onboarding_status(user_id: str) -> dict:
    """
    Check if user has completed onboarding with detailed status information
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        Dict with detailed onboarding status information
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        profile = await profiles_collection.find_one({"user_id": user_id})
        
        if not profile:
            return {
                "onboarding_completed": False,
                "has_profile": False,
                "user_id": user_id,
                "current_step": "plan-selection",
                "plan_selected": False,
                "profile_completed": False,
                "setup_level": None,
                "plan_type": None
            }
        
        # Determine current step and completion status
        onboarding_completed = profile.get("onboarding_completed", False)
        plan_selected = profile.get("subscription") is not None and profile.get("subscription") != "free"
        setup_level = profile.get("setup_level")
        plan_type = profile.get("subscription", "free")
        
        # Check if profile has meaningful data (not just defaults)
        profile_completed = (
            profile.get("weekly_budget") is not None and
            len(profile.get("dietary_restrictions", [])) > 0 or
            len(profile.get("allergies", [])) > 0 or
            len(profile.get("taste_preferences", [])) > 0 or
            len(profile.get("meal_preferences", [])) > 0 or
            len(profile.get("kitchen_equipment", [])) > 0
        )
        
        # Determine current step
        current_step = None
        if not plan_selected:
            current_step = "plan-selection"
        elif not profile_completed:
            current_step = "profile-setup"
        elif not onboarding_completed:
            current_step = "completion"
        
        return {
            "onboarding_completed": onboarding_completed,
            "has_profile": True,
            "user_id": user_id,
            "current_step": current_step,
            "plan_selected": plan_selected,
            "profile_completed": profile_completed,
            "setup_level": setup_level,
            "plan_type": plan_type
        }
        
    except PyMongoError as e:
        logger.error(f"Database error getting onboarding status for user {user_id}: {e}")
        return {
            "onboarding_completed": False,
            "has_profile": False,
            "user_id": user_id,
            "current_step": "plan-selection",
            "plan_selected": False,
            "profile_completed": False,
            "setup_level": None,
            "plan_type": None
        }
    except Exception as e:
        logger.error(f"Error getting onboarding status for user {user_id}: {e}")
        return {
            "onboarding_completed": False,
            "has_profile": False,
            "user_id": user_id,
            "current_step": "plan-selection",
            "plan_selected": False,
            "profile_completed": False,
            "setup_level": None,
            "plan_type": None
        }


async def complete_onboarding(user_id: str) -> Optional[UserProfile]:
    """
    Mark user's onboarding as complete
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Update onboarding status
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "onboarding_completed": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error completing onboarding for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error completing onboarding for user {user_id}: {e}")
        return None


async def update_plan_selection(user_id: str, plan_type: str, setup_level: str, trial_ends_at: Optional[datetime] = None) -> Optional[UserProfile]:
    """
    Update user's plan selection during onboarding
    
    Args:
        user_id: User's ObjectId as string
        plan_type: Selected plan type (free, basic, premium)
        setup_level: Selected setup level (basic, medium, full)
        trial_ends_at: Trial end date if applicable
        
    Returns:
        Updated UserProfile object if successful, None otherwise
    """
    try:
        profiles_collection = await get_collection("profiles")
        
        # Build update document
        update_doc = {
            "subscription": plan_type,
            "setup_level": setup_level,
            "updated_at": datetime.utcnow()
        }
        
        if trial_ends_at:
            update_doc["trial_ends_at"] = trial_ends_at
        
        # Update plan selection
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated profile
        return await get_profile_by_user_id(user_id)
        
    except PyMongoError as e:
        logger.error(f"Database error updating plan selection for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error updating plan selection for user {user_id}: {e}")
        return None