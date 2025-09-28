"""
Authentication utilities for password hashing and JWT token management
"""

import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.auth import TokenData, User
from app.database import get_collection
from app.middleware.security import is_token_blacklisted, blacklist_token
from app.utils.exceptions import PasswordValidationError
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Password hashing context using Argon2 with enhanced security
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=1       # Single thread
)

# JWT configuration with separate keys for access and refresh tokens
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET", "your-super-secret-refresh-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7 days

# HTTP Bearer token scheme
security = HTTPBearer()

# Password validation patterns
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERNS = {
    'uppercase': re.compile(r'[A-Z]'),
    'lowercase': re.compile(r'[a-z]'),
    'digit': re.compile(r'\d'),
    'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]')
}

# Brute force protection
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength against security requirements
    
    Args:
        password: Plain text password to validate
        
    Returns:
        Dictionary with validation results
    """
    errors = []
    
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    
    if not PASSWORD_PATTERNS['uppercase'].search(password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not PASSWORD_PATTERNS['lowercase'].search(password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not PASSWORD_PATTERNS['digit'].search(password):
        errors.append("Password must contain at least one digit")
    
    if not PASSWORD_PATTERNS['special'].search(password):
        errors.append("Password must contain at least one special character")
    
    # Check for common weak passwords
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        errors.append("Password is too common and easily guessable")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength_score": max(0, 100 - (len(errors) * 20))
    }


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2 with enhanced security
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    # Validate password strength before hashing
    validation = validate_password_strength(password)
    if not validation["is_valid"]:
        raise PasswordValidationError(
            "Password does not meet requirements",
            validation['errors']
        )
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token_pair(user_data: dict) -> Dict[str, str]:
    """
    Create both access and refresh tokens
    
    Args:
        user_data: User data to encode in tokens
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        token_type: Type of token ("access" or "refresh")
        
    Returns:
        TokenData if valid, None if invalid
    """
    try:
        # Choose the correct secret key based on token type
        secret_key = REFRESH_SECRET_KEY if token_type == "refresh" else SECRET_KEY
        
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
            return None
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            return None
            
        token_data = TokenData(user_id=user_id, email=email)
        return token_data
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        return None


async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """
    Generate a new access token using a refresh token
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New token pair if refresh token is valid, None otherwise
    """
    # Check if refresh token is blacklisted
    if await is_token_blacklisted(refresh_token):
        logger.warning("Attempted to use blacklisted refresh token")
        return None
    
    # Verify refresh token
    token_data = verify_token(refresh_token, "refresh")
    if not token_data:
        return None
    
    # Get user from database to ensure they still exist and are active
    user = await get_user_by_id(token_data.user_id)
    if not user or not user.get("is_active", True):
        return None
    
    # Create new token pair
    user_data = {
        "sub": str(user["_id"]),
        "email": user["email"]
    }
    
    return create_token_pair(user_data)


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Get user from database by ID
    
    Args:
        user_id: User ID string
        
    Returns:
        User document if found, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        from bson import ObjectId
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user with enhanced security
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Current user document
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        logger.warning("Attempted to use blacklisted token")
        raise credentials_exception
    
    # Verify token
    token_data = verify_token(token, "access")
    if token_data is None:
        raise credentials_exception
    
    # Get user from database
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active user document
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def get_login_attempts_key(identifier: str) -> str:
    """Generate Redis key for login attempts tracking"""
    return f"login_attempts:{hashlib.sha256(identifier.encode()).hexdigest()}"


async def get_lockout_key(identifier: str) -> str:
    """Generate Redis key for account lockout tracking"""
    return f"account_lockout:{hashlib.sha256(identifier.encode()).hexdigest()}"


async def is_account_locked(identifier: str) -> bool:
    """
    Check if account is locked due to too many failed login attempts
    
    Args:
        identifier: Email or IP address to check
        
    Returns:
        True if account is locked, False otherwise
    """
    try:
        from app.middleware.security import get_redis_client
        redis_conn = await get_redis_client()
        if redis_conn:
            lockout_key = await get_lockout_key(identifier)
            return await redis_conn.exists(lockout_key)
        return False
    except Exception as e:
        logger.warning(f"Error checking account lockout: {e}")
        return False


async def record_failed_login(identifier: str, request: Request):
    """
    Record a failed login attempt and lock account if threshold exceeded
    
    Args:
        identifier: Email or IP address
        request: FastAPI request object for logging
    """
    try:
        from app.middleware.security import get_redis_client
        redis_conn = await get_redis_client()
        if not redis_conn:
            return
        
        attempts_key = await get_login_attempts_key(identifier)
        lockout_key = await get_lockout_key(identifier)
        
        # Increment failed attempts
        attempts = await redis_conn.incr(attempts_key)
        await redis_conn.expire(attempts_key, LOCKOUT_DURATION_MINUTES * 60)
        
        # Log failed attempt
        logger.warning(
            "Failed login attempt",
            identifier=identifier,
            attempts=attempts,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        # Lock account if threshold exceeded
        if attempts >= MAX_LOGIN_ATTEMPTS:
            await redis_conn.setex(lockout_key, LOCKOUT_DURATION_MINUTES * 60, "1")
            logger.error(
                "Account locked due to excessive failed login attempts",
                identifier=identifier,
                attempts=attempts,
                lockout_duration_minutes=LOCKOUT_DURATION_MINUTES
            )
            
    except Exception as e:
        logger.error(f"Error recording failed login: {e}")


async def clear_failed_login_attempts(identifier: str):
    """
    Clear failed login attempts after successful login
    
    Args:
        identifier: Email or IP address
    """
    try:
        from app.middleware.security import get_redis_client
        redis_conn = await get_redis_client()
        if redis_conn:
            attempts_key = await get_login_attempts_key(identifier)
            await redis_conn.delete(attempts_key)
    except Exception as e:
        logger.warning(f"Error clearing failed login attempts: {e}")


async def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user from database by email
    
    Args:
        email: User email address
        
    Returns:
        User document if found, None otherwise
    """
    try:
        users_collection = await get_collection("users")
        user = await users_collection.find_one({"email": email.lower()})
        return user
    except Exception:
        return None


async def authenticate_user(email: str, password: str, request: Request) -> Optional[dict]:
    """
    Authenticate user with brute force protection
    
    Args:
        email: User email
        password: User password
        request: FastAPI request object
        
    Returns:
        User document if authentication successful, None otherwise
    """
    # Check if account is locked
    if await is_account_locked(email):
        logger.warning(f"Login attempt on locked account: {email}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked due to too many failed login attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
        )
    
    # Get user from database
    user = await get_user_by_email(email)
    if not user:
        await record_failed_login(email, request)
        return None
    
    # Verify password
    if not verify_password(password, user["password"]):
        await record_failed_login(email, request)
        return None
    
    # Check if user is active
    if not user.get("is_active", True):
        logger.warning(f"Login attempt on inactive account: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Clear failed login attempts on successful authentication
    await clear_failed_login_attempts(email)
    
    # Log successful login
    logger.info(
        "Successful login",
        user_id=str(user["_id"]),
        email=email,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return user


async def logout_user(token: str) -> bool:
    """
    Logout user by blacklisting their token
    
    Args:
        token: JWT access token to blacklist
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Decode token to get expiry time
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        exp = payload.get("exp")
        
        if exp:
            # Calculate remaining TTL
            exp_datetime = datetime.fromtimestamp(exp)
            remaining_seconds = int((exp_datetime - datetime.utcnow()).total_seconds())
            
            if remaining_seconds > 0:
                await blacklist_token(token, remaining_seconds)
                logger.info("User logged out successfully")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return False