"""
Pantry API tests
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.models.pantry import PantryItem, PantryItemCreate, PantryItemUpdate


@pytest.mark.api
@pytest.mark.asyncio
class TestPantryEndpoints:
    """Test pantry management endpoints"""

    async def test_add_pantry_item_success(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test successfully adding a pantry item"""
        response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == test_pantry_item["name"]
        assert data["category"] == test_pantry_item["category"]
        assert data["quantity"] == test_pantry_item["quantity"]
        assert "id" in data
        assert "created_at" in data

    async def test_add_pantry_item_unauthorized(self, async_client: AsyncClient, test_pantry_item):
        """Test adding pantry item without authentication"""
        response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_pantry_items_success(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test getting all pantry items for user"""
        # Add a pantry item first
        await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        # Get pantry items
        response = await async_client.get(
            "/api/v1/pantry/items",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == test_pantry_item["name"]

    async def test_get_pantry_items_with_filters(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test getting pantry items with category filter"""
        # Add a pantry item
        await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        # Get items by category
        response = await async_client.get(
            f"/api/v1/pantry/items?category={test_pantry_item['category']}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["category"] == test_pantry_item["category"]

    async def test_get_pantry_item_by_id(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test getting a specific pantry item by ID"""
        # Add a pantry item
        create_response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Get the specific item
        response = await async_client.get(
            f"/api/v1/pantry/items/{item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == test_pantry_item["name"]

    async def test_get_pantry_item_not_found(self, async_client: AsyncClient, auth_headers):
        """Test getting non-existent pantry item"""
        response = await async_client.get(
            "/api/v1/pantry/items/nonexistent_id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_pantry_item_success(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test updating a pantry item"""
        # Add a pantry item
        create_response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Update the item
        update_data = {"quantity": 10, "location": "pantry"}
        response = await async_client.put(
            f"/api/v1/pantry/items/{item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["quantity"] == update_data["quantity"]
        assert data["location"] == update_data["location"]
        assert data["name"] == test_pantry_item["name"]  # Unchanged

    async def test_update_pantry_item_not_found(self, async_client: AsyncClient, auth_headers):
        """Test updating non-existent pantry item"""
        update_data = {"quantity": 10}
        response = await async_client.put(
            "/api/v1/pantry/items/nonexistent_id",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_pantry_item_success(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test deleting a pantry item"""
        # Add a pantry item
        create_response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Delete the item
        response = await async_client.delete(
            f"/api/v1/pantry/items/{item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify item is deleted
        get_response = await async_client.get(
            f"/api/v1/pantry/items/{item_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_pantry_item_not_found(self, async_client: AsyncClient, auth_headers):
        """Test deleting non-existent pantry item"""
        response = await async_client.delete(
            "/api/v1/pantry/items/nonexistent_id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_expiring_items(self, async_client: AsyncClient, auth_headers):
        """Test getting items expiring soon"""
        # Add items with different expiry dates
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        expiring_item = {
            "name": "Expiring Item",
            "category": "dairy",
            "quantity": 1,
            "unit": "piece",
            "expiry_date": tomorrow,
            "location": "refrigerator"
        }
        
        not_expiring_item = {
            "name": "Fresh Item",
            "category": "dairy",
            "quantity": 1,
            "unit": "piece",
            "expiry_date": next_week,
            "location": "refrigerator"
        }
        
        await async_client.post("/api/v1/pantry/items", json=expiring_item, headers=auth_headers)
        await async_client.post("/api/v1/pantry/items", json=not_expiring_item, headers=auth_headers)
        
        # Get expiring items (within 3 days)
        response = await async_client.get(
            "/api/v1/pantry/expiring?days=3",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should include the expiring item
        expiring_names = [item["name"] for item in data]
        assert "Expiring Item" in expiring_names

    async def test_get_pantry_categories(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test getting all pantry categories"""
        # Add a pantry item
        await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        response = await async_client.get(
            "/api/v1/pantry/categories",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert test_pantry_item["category"] in data

    async def test_bulk_add_pantry_items(self, async_client: AsyncClient, auth_headers):
        """Test adding multiple pantry items at once"""
        items = [
            {
                "name": "Item 1",
                "category": "vegetables",
                "quantity": 1,
                "unit": "piece",
                "location": "refrigerator"
            },
            {
                "name": "Item 2",
                "category": "fruits",
                "quantity": 2,
                "unit": "pieces",
                "location": "refrigerator"
            }
        ]
        
        response = await async_client.post(
            "/api/v1/pantry/items/bulk",
            json={"items": items},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Item 1"
        assert data[1]["name"] == "Item 2"


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestPantryIntegration:
    """Test pantry integration with other services"""

    async def test_pantry_recipe_integration(self, async_client: AsyncClient, auth_headers, test_pantry_item, test_recipe_data):
        """Test finding recipes based on pantry items"""
        # Add pantry items
        await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        # Add a recipe that uses pantry ingredients
        await async_client.post(
            "/api/v1/recipes",
            json=test_recipe_data,
            headers=auth_headers
        )
        
        # Find recipes that can be made with pantry items
        response = await async_client.get(
            "/api/v1/pantry/recipes/suggestions",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_pantry_shopping_list_integration(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test generating shopping list from pantry needs"""
        # Add pantry item
        await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=auth_headers
        )
        
        # Generate shopping list for missing items
        response = await async_client.post(
            "/api/v1/pantry/shopping-list/generate",
            json={"recipe_ids": []},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
@pytest.mark.performance
@pytest.mark.asyncio
class TestPantryPerformance:
    """Test pantry API performance"""

    async def test_bulk_operations_performance(self, async_client: AsyncClient, auth_headers, performance_test_data):
        """Test performance of bulk pantry operations"""
        import time
        
        # Create many pantry items
        items = [
            {
                "name": f"Item {i}",
                "category": "vegetables",
                "quantity": i,
                "unit": "pieces",
                "location": "refrigerator"
            }
            for i in range(100)
        ]
        
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/pantry/items/bulk",
            json={"items": items},
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_201_CREATED
        assert end_time - start_time < 5.0  # Should complete within 5 seconds

    async def test_large_pantry_retrieval(self, async_client: AsyncClient, auth_headers):
        """Test retrieving large number of pantry items"""
        import time
        
        # Add many items first
        items = [
            {
                "name": f"Item {i}",
                "category": f"category_{i % 10}",
                "quantity": i,
                "unit": "pieces",
                "location": "refrigerator"
            }
            for i in range(500)
        ]
        
        await async_client.post(
            "/api/v1/pantry/items/bulk",
            json={"items": items},
            headers=auth_headers
        )
        
        # Test retrieval performance
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/pantry/items",
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert end_time - start_time < 2.0  # Should complete within 2 seconds
        data = response.json()
        assert len(data) >= 500


@pytest.mark.api
@pytest.mark.security
@pytest.mark.asyncio
class TestPantrySecurity:
    """Test pantry API security"""

    async def test_user_isolation(self, async_client: AsyncClient, test_user_data, test_pantry_item):
        """Test that users can only access their own pantry items"""
        # Create two users
        user1_data = test_user_data.copy()
        user2_data = {
            "email": "user2@example.com",
            "password": "TestPassword123!",
            "full_name": "User Two"
        }
        
        # Register both users
        user1_response = await async_client.post("/api/v1/auth/register", json=user1_data)
        user2_response = await async_client.post("/api/v1/auth/register", json=user2_data)
        
        user1_token = user1_response.json()["access_token"]
        user2_token = user2_response.json()["access_token"]
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User 1 adds pantry item
        create_response = await async_client.post(
            "/api/v1/pantry/items",
            json=test_pantry_item,
            headers=user1_headers
        )
        item_id = create_response.json()["id"]
        
        # User 2 tries to access User 1's item
        response = await async_client.get(
            f"/api/v1/pantry/items/{item_id}",
            headers=user2_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_input_validation(self, async_client: AsyncClient, auth_headers, malicious_payloads):
        """Test input validation against malicious payloads"""
        for payload in malicious_payloads["xss"]:
            malicious_item = {
                "name": payload,
                "category": "vegetables",
                "quantity": 1,
                "unit": "piece",
                "location": "refrigerator"
            }
            
            response = await async_client.post(
                "/api/v1/pantry/items",
                json=malicious_item,
                headers=auth_headers
            )
            
            # Should either reject or sanitize
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                assert payload not in data["name"]

    async def test_quantity_validation(self, async_client: AsyncClient, auth_headers):
        """Test validation of quantity values"""
        invalid_items = [
            {
                "name": "Test Item",
                "category": "vegetables",
                "quantity": -1,  # Negative quantity
                "unit": "piece",
                "location": "refrigerator"
            },
            {
                "name": "Test Item",
                "category": "vegetables",
                "quantity": "invalid",  # Non-numeric quantity
                "unit": "piece",
                "location": "refrigerator"
            }
        ]
        
        for invalid_item in invalid_items:
            response = await async_client.post(
                "/api/v1/pantry/items",
                json=invalid_item,
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_rate_limiting(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test rate limiting on pantry endpoints"""
        responses = []
        
        # Make many requests quickly
        for _ in range(50):
            response = await async_client.post(
                "/api/v1/pantry/items",
                json=test_pantry_item,
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses