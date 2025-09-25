"""
Authentication API tests
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, patch

from app.models.auth import User, UserCreate, UserLogin
from app.utils.auth import verify_password, get_password_hash


@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints"""

    async def test_register_success(self, async_client: AsyncClient, test_user_data):
        """Test successful user registration"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user_data):
        """Test registration with duplicate email"""
        # First registration
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email"""
        invalid_data = {
            "email": "invalid-email",
            "password": "ValidPassword123!",
            "full_name": "Test User"
        }
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json=invalid_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password"""
        weak_password_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User"
        }
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json=weak_password_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_success(self, async_client: AsyncClient, test_user_data):
        """Test successful login"""
        # Register user first
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_wrong_password(self, async_client: AsyncClient, test_user_data):
        """Test login with wrong password"""
        # Register user first
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token_success(self, async_client: AsyncClient, test_user_data):
        """Test successful token refresh"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh with invalid token"""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_logout_success(self, async_client: AsyncClient, test_user_data):
        """Test successful logout"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK

    async def test_get_current_user(self, async_client: AsyncClient, test_user_data):
        """Test getting current user info"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]

    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without token"""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.unit
class TestAuthUtils:
    """Test authentication utility functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_password_hash_different_each_time(self):
        """Test that password hashing produces different results each time"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


@pytest.mark.auth
@pytest.mark.security
class TestAuthSecurity:
    """Test authentication security measures"""

    async def test_rate_limiting_login(self, async_client: AsyncClient):
        """Test rate limiting on login endpoint"""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Make multiple failed login attempts
        responses = []
        for _ in range(10):
            response = await async_client.post(
                "/api/v1/auth/login",
                json=login_data
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses

    async def test_sql_injection_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test protection against SQL injection in auth endpoints"""
        for payload in malicious_payloads["sql_injection"]:
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": payload,
                    "password": "password"
                }
            )
            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    async def test_xss_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test protection against XSS in registration"""
        for payload in malicious_payloads["xss"]:
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )
            # Should either reject or sanitize
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                assert payload not in data["full_name"]

    async def test_password_requirements(self, async_client: AsyncClient):
        """Test password strength requirements"""
        weak_passwords = [
            "123456",
            "password",
            "abc",
            "PASSWORD",
            "12345678",
            "qwerty"
        ]
        
        for weak_password in weak_passwords:
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"test{weak_password}@example.com",
                    "password": weak_password,
                    "full_name": "Test User"
                }
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_token_expiration_handling(self, async_client: AsyncClient, test_user_data):
        """Test handling of expired tokens"""
        # This would require mocking time or using very short expiration times
        # For now, we'll test the structure
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        # Verify token structure
        data = login_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data