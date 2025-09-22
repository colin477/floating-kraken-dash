"""
User profile management router
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.profiles import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    FamilyMemberCreate,
    FamilyMemberUpdate
)
from app.crud.profiles import (
    get_profile_by_user_id,
    create_profile,
    update_profile,
    add_family_member,
    update_family_member,
    delete_family_member
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_user_profile(current_user: dict = Depends(get_current_active_user)):
    """
    Get user profile
    
    Returns the complete user profile including family members, dietary restrictions,
    and all other profile information. Returns 404 if profile doesn't exist.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserProfile: Complete user profile data
        
    Raises:
        HTTPException: 404 if profile not found
    """
    try:
        user_id = str(current_user["_id"])
        profile = await get_profile_by_user_id(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving profile"
        )


@router.put("/", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update user profile
    
    Creates a new profile if one doesn't exist, or updates the existing profile.
    Validates all profile fields and handles family member updates.
    
    Args:
        profile_data: Profile update data with validation
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserProfile: Updated user profile data
        
    Raises:
        HTTPException: 500 if update fails
    """
    try:
        user_id = str(current_user["_id"])
        
        # Check if profile exists
        existing_profile = await get_profile_by_user_id(user_id)
        
        if existing_profile:
            # Update existing profile
            updated_profile = await update_profile(user_id, profile_data)
            if not updated_profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update profile"
                )
            return updated_profile
        else:
            # Create new profile - convert update data to create data
            create_data = UserProfileCreate(
                dietary_restrictions=profile_data.dietary_restrictions or [],
                allergies=profile_data.allergies or [],
                taste_preferences=profile_data.taste_preferences or [],
                meal_preferences=profile_data.meal_preferences or [],
                kitchen_equipment=profile_data.kitchen_equipment or [],
                weekly_budget=profile_data.weekly_budget,
                zip_code=profile_data.zip_code,
                family_members=[],  # Family members handled separately
                preferred_grocers=profile_data.preferred_grocers or [],
                subscription=profile_data.subscription or "free",
                trial_ends_at=profile_data.trial_ends_at
            )
            
            created_profile = await create_profile(user_id, create_data)
            if not created_profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create profile"
                )
            return created_profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating profile"
        )


@router.post("/family-members", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def add_family_member_to_profile(
    member_data: FamilyMemberCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Add family member to user profile
    
    Generates a unique ID for the family member and adds them to the user's profile.
    Validates family member data including name, age, allergies, and dietary restrictions.
    
    Args:
        member_data: Family member creation data with validation
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserProfile: Updated user profile with new family member
        
    Raises:
        HTTPException: 404 if profile not found, 500 if addition fails
    """
    try:
        user_id = str(current_user["_id"])
        
        # Check if profile exists
        existing_profile = await get_profile_by_user_id(user_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first."
            )
        
        # Add family member
        updated_profile = await add_family_member(user_id, member_data)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add family member"
            )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error adding family member"
        )


@router.put("/family-members/{member_id}", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_family_member_in_profile(
    member_id: str,
    member_data: FamilyMemberUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update specific family member by ID
    
    Updates an existing family member's information including name, age, allergies,
    and dietary restrictions. Validates that the family member exists.
    
    Args:
        member_id: Unique identifier of the family member to update
        member_data: Family member update data with validation
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserProfile: Updated user profile with modified family member
        
    Raises:
        HTTPException: 404 if profile or family member not found, 500 if update fails
    """
    try:
        user_id = str(current_user["_id"])
        
        # Check if profile exists
        existing_profile = await get_profile_by_user_id(user_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Check if family member exists
        member_exists = any(member.id == member_id for member in existing_profile.family_members)
        if not member_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )
        
        # Update family member
        updated_profile = await update_family_member(user_id, member_id, member_data)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update family member"
            )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating family member"
        )


@router.delete("/family-members/{member_id}", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def remove_family_member_from_profile(
    member_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Remove family member from user profile
    
    Removes a family member from the user's profile by their unique ID.
    Validates that both the profile and family member exist.
    
    Args:
        member_id: Unique identifier of the family member to remove
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserProfile: Updated user profile without the removed family member
        
    Raises:
        HTTPException: 404 if profile or family member not found, 500 if removal fails
    """
    try:
        user_id = str(current_user["_id"])
        
        # Check if profile exists
        existing_profile = await get_profile_by_user_id(user_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Check if family member exists
        member_exists = any(member.id == member_id for member in existing_profile.family_members)
        if not member_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )
        
        # Remove family member
        updated_profile = await delete_family_member(user_id, member_id)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove family member"
            )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error removing family member"
        )