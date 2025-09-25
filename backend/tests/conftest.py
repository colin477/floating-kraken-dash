"""
Test configuration and fixtures for the EZ Eatin' backend API
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import AsyncMock, MagicMock

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "ez_eatin_test"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from main import app
from app.database import get_database
from app.models.auth import User
from app.utils.auth import create_access_token, get_password_hash


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a test database connection."""
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]
    
    # Clean up before tests
    await db.drop_collection("users")
    await db.drop_collection("profiles")
    await db.drop_collection("pantry_items")
    await db.drop_collection("recipes")
    await db.drop_collection("meal_plans")
    await db.drop_collection("shopping_lists")
    await db.drop_collection("community_posts")
    await db.drop_collection("leftovers")
    
    yield db
    
    # Clean up after tests
    await db.drop_collection("users")
    await db.drop_collection("profiles")
    await db.drop_collection("pantry_items")
    await db.drop_collection("recipes")
    await db.drop_collection("meal_plans")
    await db.drop_collection("shopping_lists")
    await db.drop_collection("community_posts")
    await db.drop_collection("leftovers")
    
    client.close()


@pytest_asyncio.fixture
async def mock_db():
    """Create a mock database for unit tests."""
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.profiles = AsyncMock()
    mock_db.pantry_items = AsyncMock()
    mock_db.recipes = AsyncMock()
    mock_db.meal_plans = AsyncMock()
    mock_db.shopping_lists = AsyncMock()
    mock_db.community_posts = AsyncMock()
    mock_db.leftovers = AsyncMock()
    return mock_db


@pytest.fixture
def test_user_data():
    """Test user data for authentication tests."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user_hashed():
    """Test user with hashed password."""
    return {
        "email": "test@example.com",
        "hashed_password": get_password_hash("TestPassword123!"),
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def test_access_token(test_user_data):
    """Create a test access token."""
    return create_access_token(data={"sub": test_user_data["email"]})


@pytest.fixture
def auth_headers(test_access_token):
    """Create authorization headers with test token."""
    return {"Authorization": f"Bearer {test_access_token}"}


@pytest.fixture
def test_profile_data():
    """Test profile data."""
    return {
        "dietary_restrictions": ["vegetarian"],
        "allergies": ["nuts"],
        "cooking_skill": "intermediate",
        "household_size": 2,
        "budget_range": "medium",
        "preferred_cuisines": ["italian", "mexican"],
        "meal_prep_time": "30-60",
        "kitchen_equipment": ["oven", "stovetop", "microwave"]
    }


@pytest.fixture
def test_pantry_item():
    """Test pantry item data."""
    return {
        "name": "Tomatoes",
        "category": "vegetables",
        "quantity": 5,
        "unit": "pieces",
        "expiry_date": "2024-12-31",
        "location": "refrigerator"
    }


@pytest.fixture
def test_recipe_data():
    """Test recipe data."""
    return {
        "title": "Test Recipe",
        "description": "A test recipe for testing",
        "ingredients": [
            {"name": "tomatoes", "quantity": 2, "unit": "pieces"},
            {"name": "onion", "quantity": 1, "unit": "piece"}
        ],
        "instructions": [
            "Chop the tomatoes",
            "Dice the onion",
            "Cook together"
        ],
        "prep_time": 15,
        "cook_time": 30,
        "servings": 4,
        "difficulty": "easy",
        "cuisine": "italian",
        "tags": ["vegetarian", "healthy"]
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def disable_rate_limiting(monkeypatch):
    """Disable rate limiting for tests."""
    from app.middleware.security import limiter
    monkeypatch.setattr(limiter, "enabled", False)


# Performance test fixtures
@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing."""
    return {
        "users": [
            {
                "email": f"user{i}@example.com",
                "hashed_password": get_password_hash("password123"),
                "full_name": f"User {i}",
                "is_active": True,
                "is_verified": True
            }
            for i in range(100)
        ],
        "recipes": [
            {
                "title": f"Recipe {i}",
                "description": f"Description for recipe {i}",
                "ingredients": [
                    {"name": "ingredient1", "quantity": 1, "unit": "cup"},
                    {"name": "ingredient2", "quantity": 2, "unit": "tbsp"}
                ],
                "instructions": ["Step 1", "Step 2", "Step 3"],
                "prep_time": 15,
                "cook_time": 30,
                "servings": 4,
                "difficulty": "easy"
            }
            for i in range(50)
        ]
    }


# Security test fixtures
@pytest.fixture
def malicious_payloads():
    """Common malicious payloads for security testing."""
    return {
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--"
        ],
        "nosql_injection": [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "function() { return true; }"},
            {"$regex": ".*"}
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }


@pytest.fixture(autouse=True)
async def setup_test_environment():
    """Set up test environment before each test."""
    # Override database dependency for testing
    async def override_get_database():
        client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
        return client[os.getenv("DATABASE_NAME")]
    
    app.dependency_overrides[get_database] = override_get_database
    
    yield
    
    # Clean up after test
    app.dependency_overrides.clear()