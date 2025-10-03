"""
Authentication router for user signup, login, and logout
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.models.responses import SuccessResponse
from app.models.auth import UserCreate, UserLogin, LoginResponse, UserResponse
from app.crud.profiles import create_profile_stub
from app.utils.auth import create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils.exceptions import PasswordValidationError, EmailAlreadyExistsError, UserCreationError

router = APIRouter()


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    User registration endpoint
    
    Creates a new user account with email and password validation.
    Ensures email uniqueness and proper password hashing.
    Returns JWT token for immediate login after registration.
    """
    try:
        from app.crud.users import create_user
        
        # Create the user
        created_user = await create_user(user_data)
        
        # Create profile stub for the new user
        profile_stub = await create_profile_stub(str(created_user["_id"]))
        if not profile_stub:
            # Log warning but don't fail registration
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create profile stub for user {created_user['_id']}")
        
        # Create access token for the new user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(created_user["_id"]), "email": created_user["email"]},
            expires_delta=access_token_expires
        )
        
        # Update last login for the new user
        from app.crud.users import update_user_last_login
        await update_user_last_login(str(created_user["_id"]))
        
        # Prepare user response
        user_response = UserResponse(
            id=str(created_user["_id"]),
            email=created_user["email"],
            full_name=created_user["full_name"],
            created_at=created_user["created_at"],
            updated_at=created_user["updated_at"],
            is_active=created_user["is_active"]
        )
        
        # Return login response with token and user info
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_response
        )
        
    except PasswordValidationError as e:
        # Password validation failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(e.errors)}"
        )
    except EmailAlreadyExistsError as e:
        # Email already registered
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except UserCreationError as e:
        # Other user creation errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except HTTPException:
        raise
    except ConnectionError as e:
        # Database connection issues
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable. Please try again later."
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error during user registration: {e}", exc_info=True)
        
        # Check if it's a Redis-related error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['redis', 'connection', 'timeout', 'rate limit']):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable due to rate limiting service issues. Please try again in a moment."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user registration. Please try again later."
        )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    User registration endpoint (alias for signup)
    
    Creates a new user account with email and password validation.
    This endpoint provides compatibility with frontend expectations.
    """
    return await signup(user_data)


@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, request: Request):
    """
    User login endpoint (JSON format)
    
    Authenticates user with email and password, returns JWT token on success.
    """
    try:
        from app.crud.users import authenticate_user
        # Authenticate user
        user = await authenticate_user(user_credentials.email, user_credentials.password, request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        # Update last login
        from app.crud.users import update_user_last_login
        await update_user_last_login(str(user["_id"]))
        
        # Prepare user response
        user_response = UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            is_active=user["is_active"]
        )
        
        # Return login response with token and user info
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_response
        )
        
    except HTTPException:
        raise
    except ConnectionError as e:
        # Database connection issues
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable. Please try again later."
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        
        # Check if it's a Redis-related error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['redis', 'connection', 'timeout', 'rate limit']):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable due to rate limiting service issues. Please try again in a moment."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login. Please try again later."
        )


@router.post("/login-form", response_model=LoginResponse)
async def login_form(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login endpoint (form data format)
    
    Authenticates user with form data (username/password), returns JWT token on success.
    This endpoint provides compatibility with frontend form submissions.
    """
    try:
        from app.crud.users import authenticate_user
        # Authenticate user (username field contains email)
        user = await authenticate_user(form_data.username, form_data.password, request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        # Update last login
        from app.crud.users import update_user_last_login
        await update_user_last_login(str(user["_id"]))
        
        # Prepare user response
        user_response = UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            is_active=user["is_active"]
        )
        
        # Return login response with token and user info
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_response
        )
        
    except HTTPException:
        raise
    except ConnectionError as e:
        # Database connection issues
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection error during form login: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable. Please try again later."
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error during form login: {e}", exc_info=True)
        
        # Check if it's a Redis-related error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['redis', 'connection', 'timeout', 'rate limit']):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable due to rate limiting service issues. Please try again in a moment."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login. Please try again later."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: dict = Depends(get_current_active_user)):
    """
    Get current user information
    
    Protected endpoint that returns the current authenticated user's information.
    Requires valid JWT token in Authorization header.
    """
    try:
        # Convert current user to response model
        user_response = UserResponse(
            id=str(current_user["_id"]),
            email=current_user["email"],
            full_name=current_user["full_name"],
            created_at=current_user["created_at"],
            updated_at=current_user["updated_at"],
            is_active=current_user["is_active"]
        )
        
        return user_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving user information"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    User logout endpoint
    
    Currently returns success message. In a production environment,
    this could implement token blacklisting or other logout mechanisms.
    """
    try:
        # For now, just return success message
        # In production, you might want to implement token blacklisting
        return SuccessResponse(
            message="Successfully logged out",
            data={"user_id": str(current_user["_id"])}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )