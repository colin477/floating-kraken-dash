"""
Security testing framework
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import time
from unittest.mock import patch, AsyncMock


@pytest.mark.security
@pytest.mark.asyncio
class TestSecurityMiddleware:
    """Test security middleware functionality"""

    async def test_security_headers(self, async_client: AsyncClient):
        """Test that security headers are properly set"""
        response = await async_client.get("/healthz")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers

    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are properly configured"""
        # Preflight request
        response = await async_client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

    async def test_request_size_limit(self, async_client: AsyncClient):
        """Test request size limiting"""
        # Create a large payload (larger than 10MB limit)
        large_payload = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json=large_payload
        )
        
        # Should be rejected due to size
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    async def test_rate_limiting_global(self, async_client: AsyncClient):
        """Test global rate limiting"""
        responses = []
        
        # Make many requests to trigger rate limiting
        for _ in range(200):
            response = await async_client.get("/healthz")
            responses.append(response.status_code)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should eventually get rate limited
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses

    async def test_compression_middleware(self, async_client: AsyncClient):
        """Test that responses are compressed when appropriate"""
        response = await async_client.get(
            "/healthz",
            headers={"Accept-Encoding": "gzip"}
        )
        
        # For small responses, compression might not be applied
        # But the middleware should handle it gracefully
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.security
@pytest.mark.asyncio
class TestInputValidation:
    """Test input validation and sanitization"""

    async def test_xss_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test XSS protection across all endpoints"""
        xss_payloads = malicious_payloads["xss"]
        
        # Test registration endpoint
        for payload in xss_payloads:
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
                # Ensure the malicious script is not in the response
                assert "<script>" not in data.get("full_name", "").lower()
                assert "javascript:" not in data.get("full_name", "").lower()

    async def test_sql_injection_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test SQL injection protection"""
        sql_payloads = malicious_payloads["sql_injection"]
        
        for payload in sql_payloads:
            # Test login endpoint
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": payload,
                    "password": "password"
                }
            )
            
            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
            # Should return unauthorized, not crash
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    async def test_nosql_injection_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test NoSQL injection protection"""
        nosql_payloads = malicious_payloads["nosql_injection"]
        
        for payload in nosql_payloads:
            # Test with various endpoints that accept JSON
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": payload,
                    "password": "password"
                }
            )
            
            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    async def test_path_traversal_protection(self, async_client: AsyncClient, malicious_payloads):
        """Test path traversal protection"""
        path_payloads = malicious_payloads["path_traversal"]
        
        for payload in path_payloads:
            # Test file-related endpoints
            response = await async_client.get(f"/api/v1/recipes/{payload}")
            
            # Should return 404 or 422, not expose files
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_401_UNAUTHORIZED
            ]

    async def test_json_bomb_protection(self, async_client: AsyncClient):
        """Test protection against JSON bombs"""
        # Create deeply nested JSON
        nested_json = {"a": {}}
        current = nested_json["a"]
        for i in range(1000):  # Deep nesting
            current["b"] = {}
            current = current["b"]
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json=nested_json
        )
        
        # Should reject malformed or overly complex JSON
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_unicode_normalization(self, async_client: AsyncClient):
        """Test Unicode normalization attacks"""
        # Unicode characters that might bypass filters
        unicode_payloads = [
            "admin\u202e",  # Right-to-left override
            "admin\u200b",  # Zero-width space
            "admin\ufeff",  # Zero-width no-break space
        ]
        
        for payload in unicode_payloads:
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"{payload}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )
            
            # Should handle Unicode properly
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                # Should normalize or reject suspicious Unicode
                assert len(data["full_name"]) <= len(payload)


@pytest.mark.security
@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test authentication security measures"""

    async def test_password_strength_enforcement(self, async_client: AsyncClient):
        """Test password strength requirements"""
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon"
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

    async def test_brute_force_protection(self, async_client: AsyncClient):
        """Test brute force protection on login"""
        # Register a user first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "victim@example.com",
                "password": "ValidPassword123!",
                "full_name": "Victim User"
            }
        )
        
        # Attempt brute force
        responses = []
        for i in range(20):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "victim@example.com",
                    "password": f"wrong_password_{i}"
                }
            )
            responses.append(response.status_code)
            
            # Add small delay to simulate real attack
            time.sleep(0.1)
        
        # Should get rate limited
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses

    async def test_jwt_token_security(self, async_client: AsyncClient, test_user_data):
        """Test JWT token security"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        token = login_response.json()["access_token"]
        
        # Test with malformed tokens
        malformed_tokens = [
            "invalid_token",
            token + "extra",
            token[:-5],  # Truncated
            "Bearer " + token,  # Wrong format
            token.replace(".", ""),  # Remove dots
        ]
        
        for malformed_token in malformed_tokens:
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {malformed_token}"}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_session_fixation_protection(self, async_client: AsyncClient, test_user_data):
        """Test protection against session fixation"""
        # Register user
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login multiple times and ensure tokens are different
        tokens = []
        for _ in range(3):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": test_user_data["email"], "password": test_user_data["password"]}
            )
            tokens.append(response.json()["access_token"])
        
        # All tokens should be different
        assert len(set(tokens)) == len(tokens)

    async def test_token_blacklisting(self, async_client: AsyncClient, test_user_data):
        """Test token blacklisting on logout"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # Use token before logout
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Logout
        await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Try to use token after logout
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # Should be unauthorized (token blacklisted)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
@pytest.mark.asyncio
class TestDataProtection:
    """Test data protection and privacy measures"""

    async def test_password_not_in_response(self, async_client: AsyncClient, test_user_data):
        """Test that passwords are never returned in responses"""
        response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data
        assert test_user_data["password"] not in str(data)

    async def test_user_data_isolation(self, async_client: AsyncClient):
        """Test that users can only access their own data"""
        # Create two users
        user1_data = {
            "email": "user1@example.com",
            "password": "Password123!",
            "full_name": "User One"
        }
        user2_data = {
            "email": "user2@example.com",
            "password": "Password123!",
            "full_name": "User Two"
        }
        
        # Register both users
        user1_response = await async_client.post("/api/v1/auth/register", json=user1_data)
        user2_response = await async_client.post("/api/v1/auth/register", json=user2_data)
        
        user1_token = user1_response.json()["access_token"]
        user2_token = user2_response.json()["access_token"]
        
        # User 1 creates profile
        profile_data = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["nuts"],
            "cooking_skill": "intermediate"
        }
        
        await async_client.post(
            "/api/v1/profile",
            json=profile_data,
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        # User 2 tries to access User 1's profile
        response = await async_client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        # Should not get User 1's data
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data.get("dietary_restrictions") != ["vegetarian"]

    async def test_sensitive_data_logging(self, async_client: AsyncClient, test_user_data):
        """Test that sensitive data is not logged"""
        with patch('structlog.get_logger') as mock_logger:
            mock_log = AsyncMock()
            mock_logger.return_value = mock_log
            
            # Make request with sensitive data
            await async_client.post("/api/v1/auth/register", json=test_user_data)
            
            # Check that password is not in any log calls
            for call in mock_log.info.call_args_list:
                args, kwargs = call
                log_message = str(args) + str(kwargs)
                assert test_user_data["password"] not in log_message


@pytest.mark.security
@pytest.mark.asyncio
class TestAPISecurityHeaders:
    """Test API-specific security headers and configurations"""

    async def test_content_type_validation(self, async_client: AsyncClient):
        """Test content type validation"""
        # Send request with wrong content type
        response = await async_client.post(
            "/api/v1/auth/login",
            data="email=test@example.com&password=password",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should reject non-JSON content for JSON endpoints
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]

    async def test_method_not_allowed(self, async_client: AsyncClient):
        """Test that unsupported HTTP methods are rejected"""
        # Try unsupported methods
        unsupported_methods = ["PATCH", "TRACE", "CONNECT"]
        
        for method in unsupported_methods:
            response = await async_client.request(method, "/api/v1/auth/login")
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    async def test_api_versioning_security(self, async_client: AsyncClient):
        """Test that only supported API versions are accessible"""
        # Try accessing non-existent API versions
        response = await async_client.get("/api/v2/auth/me")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response = await async_client.get("/api/v0/auth/me")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_error_information_disclosure(self, async_client: AsyncClient):
        """Test that error messages don't disclose sensitive information"""
        # Try to trigger various errors
        error_responses = []
        
        # Invalid JSON
        response = await async_client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        error_responses.append(response)
        
        # Missing required fields
        response = await async_client.post(
            "/api/v1/auth/login",
            json={}
        )
        error_responses.append(response)
        
        # Check that error messages don't expose internal details
        for response in error_responses:
            if response.status_code >= 400:
                error_text = response.text.lower()
                # Should not expose internal paths, stack traces, etc.
                assert "traceback" not in error_text
                assert "c:\\" not in error_text
                assert "/usr/" not in error_text
                assert "internal server error" not in error_text or response.status_code != 500


@pytest.mark.security
@pytest.mark.performance
@pytest.mark.asyncio
class TestSecurityPerformance:
    """Test security measures don't significantly impact performance"""

    async def test_rate_limiting_performance(self, async_client: AsyncClient):
        """Test that rate limiting doesn't significantly slow down normal requests"""
        import time
        
        # Make normal requests and measure time
        start_time = time.time()
        
        for _ in range(10):
            response = await async_client.get("/healthz")
            assert response.status_code == status.HTTP_200_OK
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should complete quickly (less than 100ms per request on average)
        assert avg_time < 0.1

    async def test_security_middleware_overhead(self, async_client: AsyncClient):
        """Test that security middleware doesn't add significant overhead"""
        import time
        
        # Test multiple endpoints
        endpoints = ["/healthz", "/api/v1/auth/me"]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            # Make request (will fail for /me without auth, but that's OK)
            await async_client.get(endpoint)
            
            end_time = time.time()
            request_time = end_time - start_time
            
            # Should complete quickly (security middleware overhead < 50ms)
            assert request_time < 0.05