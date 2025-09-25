"""
Performance testing suite
"""

import pytest
import asyncio
import time
from httpx import AsyncClient
from fastapi import status
from concurrent.futures import ThreadPoolExecutor
import statistics


@pytest.mark.performance
@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API endpoint performance"""

    async def test_health_check_performance(self, async_client: AsyncClient):
        """Test health check endpoint performance"""
        times = []
        
        for _ in range(100):
            start_time = time.time()
            response = await async_client.get("/healthz")
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        # Health check should be very fast
        assert avg_time < 0.1  # 100ms average
        assert p95_time < 0.2  # 200ms 95th percentile
        
        print(f"Health check - Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s")

    async def test_authentication_performance(self, async_client: AsyncClient, test_user_data):
        """Test authentication endpoint performance"""
        # Register user first
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        times = []
        
        for _ in range(50):
            start_time = time.time()
            response = await async_client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        # Authentication should complete within reasonable time
        assert avg_time < 1.0  # 1 second average
        assert p95_time < 2.0  # 2 seconds 95th percentile
        
        print(f"Authentication - Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s")

    async def test_pantry_operations_performance(self, async_client: AsyncClient, auth_headers, test_pantry_item):
        """Test pantry CRUD operations performance"""
        # Test CREATE performance
        create_times = []
        item_ids = []
        
        for i in range(50):
            item_data = test_pantry_item.copy()
            item_data["name"] = f"Test Item {i}"
            
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/pantry/items",
                json=item_data,
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == status.HTTP_201_CREATED
            create_times.append(end_time - start_time)
            item_ids.append(response.json()["id"])
        
        # Test READ performance
        read_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = await async_client.get(
                "/api/v1/pantry/items",
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            read_times.append(end_time - start_time)
        
        # Test UPDATE performance
        update_times = []
        
        for item_id in item_ids[:10]:  # Test first 10 items
            start_time = time.time()
            response = await async_client.put(
                f"/api/v1/pantry/items/{item_id}",
                json={"quantity": 99},
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            update_times.append(end_time - start_time)
        
        # Performance assertions
        assert statistics.mean(create_times) < 0.5  # 500ms average for create
        assert statistics.mean(read_times) < 0.3    # 300ms average for read
        assert statistics.mean(update_times) < 0.5  # 500ms average for update
        
        print(f"Pantry CREATE - Avg: {statistics.mean(create_times):.3f}s")
        print(f"Pantry READ - Avg: {statistics.mean(read_times):.3f}s")
        print(f"Pantry UPDATE - Avg: {statistics.mean(update_times):.3f}s")

    async def test_bulk_operations_performance(self, async_client: AsyncClient, auth_headers):
        """Test bulk operations performance"""
        # Create bulk data
        items = [
            {
                "name": f"Bulk Item {i}",
                "category": "vegetables",
                "quantity": i,
                "unit": "pieces",
                "location": "refrigerator"
            }
            for i in range(100)
        ]
        
        # Test bulk insert performance
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/pantry/items/bulk",
            json={"items": items},
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_201_CREATED
        bulk_time = end_time - start_time
        
        # Bulk operations should be efficient
        assert bulk_time < 5.0  # Should complete within 5 seconds
        
        # Calculate items per second
        items_per_second = len(items) / bulk_time
        assert items_per_second > 20  # At least 20 items per second
        
        print(f"Bulk insert - {len(items)} items in {bulk_time:.3f}s ({items_per_second:.1f} items/s)")


@pytest.mark.performance
@pytest.mark.asyncio
class TestConcurrencyPerformance:
    """Test performance under concurrent load"""

    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test performance under concurrent requests"""
        async def make_request():
            start_time = time.time()
            response = await async_client.get("/healthz")
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Create 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Check all requests succeeded
        status_codes = [result[0] for result in results]
        times = [result[1] for result in results]
        
        assert all(code == status.HTTP_200_OK for code in status_codes)
        
        # Performance under load
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        assert avg_time < 0.5  # 500ms average under load
        assert max_time < 2.0  # 2 seconds maximum
        
        print(f"Concurrent requests - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")

    async def test_concurrent_authentication(self, async_client: AsyncClient):
        """Test concurrent authentication requests"""
        # Create multiple users for concurrent testing
        users = [
            {
                "email": f"user{i}@example.com",
                "password": "TestPassword123!",
                "full_name": f"User {i}"
            }
            for i in range(10)
        ]
        
        # Register all users first
        for user in users:
            await async_client.post("/api/v1/auth/register", json=user)
        
        async def login_user(user_data):
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": user_data["email"], "password": user_data["password"]}
            )
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Concurrent logins
        tasks = [login_user(user) for user in users]
        results = await asyncio.gather(*tasks)
        
        status_codes = [result[0] for result in results]
        times = [result[1] for result in results]
        
        assert all(code == status.HTTP_200_OK for code in status_codes)
        
        avg_time = statistics.mean(times)
        assert avg_time < 2.0  # 2 seconds average for concurrent auth
        
        print(f"Concurrent auth - Avg: {avg_time:.3f}s")

    async def test_database_connection_pooling(self, async_client: AsyncClient, auth_headers):
        """Test database connection pooling performance"""
        async def database_operation():
            start_time = time.time()
            response = await async_client.get("/api/v1/pantry/items", headers=auth_headers)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Create many concurrent database operations
        tasks = [database_operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        status_codes = [result[0] for result in results]
        times = [result[1] for result in results]
        
        # Most should succeed (some might fail due to auth, but that's OK)
        success_rate = sum(1 for code in status_codes if code in [200, 401]) / len(status_codes)
        assert success_rate > 0.9  # 90% success rate
        
        # Database operations should be reasonably fast
        successful_times = [time for i, time in enumerate(times) if status_codes[i] in [200, 401]]
        if successful_times:
            avg_time = statistics.mean(successful_times)
            assert avg_time < 1.0  # 1 second average
            
            print(f"DB pooling - {len(successful_times)} ops, Avg: {avg_time:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
class TestMemoryPerformance:
    """Test memory usage and efficiency"""

    async def test_large_response_handling(self, async_client: AsyncClient, auth_headers):
        """Test handling of large responses"""
        # Create many pantry items
        items = [
            {
                "name": f"Item {i}",
                "category": f"category_{i % 10}",
                "quantity": i,
                "unit": "pieces",
                "location": "refrigerator",
                "description": f"This is a long description for item {i} " * 10  # Make it larger
            }
            for i in range(1000)
        ]
        
        # Add items in batches to avoid timeout
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            await async_client.post(
                "/api/v1/pantry/items/bulk",
                json={"items": batch},
                headers=auth_headers
            )
        
        # Test retrieving large response
        start_time = time.time()
        response = await async_client.get("/api/v1/pantry/items", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1000
        
        # Should handle large responses efficiently
        response_time = end_time - start_time
        assert response_time < 5.0  # 5 seconds for large response
        
        # Check response size
        response_size = len(response.content)
        throughput = response_size / response_time / 1024 / 1024  # MB/s
        
        print(f"Large response - {len(data)} items, {response_size/1024:.1f}KB in {response_time:.3f}s ({throughput:.1f} MB/s)")

    async def test_memory_leak_detection(self, async_client: AsyncClient, auth_headers):
        """Test for potential memory leaks in repeated operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations
        for i in range(100):
            # Create and delete items
            item_data = {
                "name": f"Temp Item {i}",
                "category": "test",
                "quantity": 1,
                "unit": "piece",
                "location": "test"
            }
            
            create_response = await async_client.post(
                "/api/v1/pantry/items",
                json=item_data,
                headers=auth_headers
            )
            
            if create_response.status_code == status.HTTP_201_CREATED:
                item_id = create_response.json()["id"]
                await async_client.delete(
                    f"/api/v1/pantry/items/{item_id}",
                    headers=auth_headers
                )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 100 operations)
        assert memory_increase < 50
        
        print(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")


@pytest.mark.performance
@pytest.mark.benchmark
@pytest.mark.asyncio
class TestBenchmarks:
    """Benchmark tests for performance regression detection"""

    async def test_auth_benchmark(self, async_client: AsyncClient, test_user_data, benchmark):
        """Benchmark authentication performance"""
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        async def login():
            response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == status.HTTP_200_OK
            return response
        
        # Benchmark the login operation
        result = benchmark(asyncio.run, login())
        assert result.status_code == status.HTTP_200_OK

    async def test_pantry_crud_benchmark(self, async_client: AsyncClient, auth_headers, test_pantry_item, benchmark):
        """Benchmark pantry CRUD operations"""
        async def crud_operations():
            # Create
            create_response = await async_client.post(
                "/api/v1/pantry/items",
                json=test_pantry_item,
                headers=auth_headers
            )
            assert create_response.status_code == status.HTTP_201_CREATED
            item_id = create_response.json()["id"]
            
            # Read
            read_response = await async_client.get(
                f"/api/v1/pantry/items/{item_id}",
                headers=auth_headers
            )
            assert read_response.status_code == status.HTTP_200_OK
            
            # Update
            update_response = await async_client.put(
                f"/api/v1/pantry/items/{item_id}",
                json={"quantity": 99},
                headers=auth_headers
            )
            assert update_response.status_code == status.HTTP_200_OK
            
            # Delete
            delete_response = await async_client.delete(
                f"/api/v1/pantry/items/{item_id}",
                headers=auth_headers
            )
            assert delete_response.status_code == status.HTTP_200_OK
            
            return "completed"
        
        # Benchmark the full CRUD cycle
        result = benchmark(asyncio.run, crud_operations())
        assert result == "completed"

    async def test_search_performance_benchmark(self, async_client: AsyncClient, auth_headers, benchmark):
        """Benchmark search operations"""
        # First, create some test data
        items = [
            {
                "name": f"Searchable Item {i}",
                "category": "vegetables",
                "quantity": i,
                "unit": "pieces",
                "location": "refrigerator"
            }
            for i in range(50)
        ]
        
        await async_client.post(
            "/api/v1/pantry/items/bulk",
            json={"items": items},
            headers=auth_headers
        )
        
        async def search_operation():
            response = await async_client.get(
                "/api/v1/pantry/items?category=vegetables",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_200_OK
            return response
        
        # Benchmark the search operation
        result = benchmark(asyncio.run, search_operation())
        assert result.status_code == status.HTTP_200_OK


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestLoadTesting:
    """Load testing for high-traffic scenarios"""

    async def test_sustained_load(self, async_client: AsyncClient):
        """Test sustained load over time"""
        duration = 30  # 30 seconds
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                response = await async_client.get("/healthz")
                if response.status_code != status.HTTP_200_OK:
                    errors += 1
                request_count += 1
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
                
            except Exception:
                errors += 1
        
        end_time = time.time()
        actual_duration = end_time - start_time
        requests_per_second = request_count / actual_duration
        error_rate = errors / request_count if request_count > 0 else 1
        
        # Performance requirements
        assert requests_per_second > 50  # At least 50 RPS
        assert error_rate < 0.05  # Less than 5% error rate
        
        print(f"Sustained load - {request_count} requests in {actual_duration:.1f}s ({requests_per_second:.1f} RPS, {error_rate:.2%} errors)")

    async def test_spike_load(self, async_client: AsyncClient):
        """Test handling of sudden traffic spikes"""
        # Simulate a traffic spike with many concurrent requests
        spike_size = 200
        
        async def make_request():
            try:
                start_time = time.time()
                response = await async_client.get("/healthz")
                end_time = time.time()
                return response.status_code, end_time - start_time, None
            except Exception as e:
                return 500, 0, str(e)
        
        # Create spike
        start_time = time.time()
        tasks = [make_request() for _ in range(spike_size)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        spike_duration = end_time - start_time
        
        # Analyze results
        status_codes = [result[0] for result in results]
        times = [result[1] for result in results if result[1] > 0]
        errors = [result[2] for result in results if result[2] is not None]
        
        success_count = sum(1 for code in status_codes if code == 200)
        success_rate = success_count / len(status_codes)
        
        # Should handle spike reasonably well
        assert success_rate > 0.8  # At least 80% success rate during spike
        assert spike_duration < 10.0  # Complete spike within 10 seconds
        
        if times:
            avg_response_time = statistics.mean(times)
            assert avg_response_time < 2.0  # Average response time under 2 seconds
        
        print(f"Spike load - {spike_size} requests in {spike_duration:.1f}s ({success_rate:.1%} success, {len(errors)} errors)")