#!/usr/bin/env python3
"""
Comprehensive Receipt Database CRUD Operations Test

This script validates all receipt database operations including:
- Create operations with various data types
- Read operations (by ID, user, date ranges, filters)
- Update operations (status, metadata, items)
- Delete operations and cleanup
- Index performance validation
- Data integrity checks
- Error handling scenarios
- Concurrent operations testing

Based on analysis of:
- backend/app/models/receipts.py (Receipt models and validation)
- backend/app/crud/receipts.py (CRUD operations)
- backend/app/routers/receipts.py (API endpoints)
- backend/app/database.py (MongoDB connection)
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReceiptCRUDTester:
    """Comprehensive tester for receipt database CRUD operations"""
    
    def __init__(self):
        self.test_results = {
            'create_operations': [],
            'read_operations': [],
            'update_operations': [],
            'delete_operations': [],
            'index_performance': [],
            'data_integrity': [],
            'error_handling': [],
            'concurrent_operations': [],
            'summary': {}
        }
        self.test_user_id = None
        self.test_receipts = []
        self.start_time = None
        
    async def setup_test_environment(self):
        """Setup test environment and database connection"""
        try:
            logger.info("Setting up test environment...")
            
            # Import database modules
            from app.database import connect_to_mongo, get_database, get_collection
            from app.crud.receipts import create_receipt_indexes
            
            # Connect to database
            await connect_to_mongo()
            self.db = await get_database()
            
            if self.db is None:
                raise Exception("Failed to connect to database")
            
            # Create indexes
            await create_receipt_indexes()
            
            # Create test user ID
            self.test_user_id = str(uuid.uuid4())
            
            logger.info(f"Test environment setup complete. Test user ID: {self.test_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def test_create_operations(self):
        """Test receipt creation with various data types and edge cases"""
        logger.info("Testing CREATE operations...")
        
        from app.models.receipts import ReceiptCreate, ReceiptItemCategory
        from app.crud.receipts import create_receipt
        
        test_cases = [
            {
                'name': 'Basic receipt creation',
                'data': ReceiptCreate(
                    store_name="Test Store",
                    receipt_date=date.today(),
                    total_amount=25.99,
                    photo_url="uploads/test_receipt.jpg"
                )
            },
            {
                'name': 'Receipt with minimum values',
                'data': ReceiptCreate(
                    store_name="A",  # Minimum length
                    receipt_date=date.today() - timedelta(days=365),  # Old date
                    total_amount=0.01,  # Minimum amount
                    photo_url=None
                )
            },
            {
                'name': 'Receipt with maximum values',
                'data': ReceiptCreate(
                    store_name="A" * 200,  # Maximum length
                    receipt_date=date.today(),
                    total_amount=9999.99,  # Large amount
                    photo_url="https://example.com/receipt.jpg"
                )
            },
            {
                'name': 'Receipt with special characters',
                'data': ReceiptCreate(
                    store_name="Store & Co. (Main St.)",
                    receipt_date=date.today(),
                    total_amount=15.50,
                    photo_url="uploads/receipt_with_spaces.jpg"
                )
            },
            {
                'name': 'Receipt with zero amount',
                'data': ReceiptCreate(
                    store_name="Free Sample Store",
                    receipt_date=date.today(),
                    total_amount=0.0,
                    photo_url=None
                )
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                result = await create_receipt(self.test_user_id, test_case['data'])
                end_time = time.time()
                
                if result:
                    self.test_receipts.append(result)
                    self.test_results['create_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'PASS',
                        'receipt_id': result.id,
                        'execution_time_ms': (end_time - start_time) * 1000,
                        'details': f"Created receipt with ID: {result.id}"
                    })
                    logger.info(f"✓ {test_case['name']}: Created receipt {result.id}")
                else:
                    self.test_results['create_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'FAIL',
                        'error': 'create_receipt returned None',
                        'execution_time_ms': (end_time - start_time) * 1000
                    })
                    logger.error(f"✗ {test_case['name']}: Failed to create receipt")
                    
            except Exception as e:
                end_time = time.time()
                self.test_results['create_operations'].append({
                    'test_name': test_case['name'],
                    'status': 'ERROR',
                    'error': str(e),
                    'execution_time_ms': (end_time - start_time) * 1000
                })
                logger.error(f"✗ {test_case['name']}: Exception - {e}")
    
    async def test_read_operations(self):
        """Test receipt read operations with various filters and queries"""
        logger.info("Testing READ operations...")
        
        from app.crud.receipts import get_receipts, get_receipt_by_id
        from app.models.receipts import ReceiptProcessingStatus
        
        if not self.test_receipts:
            logger.warning("No test receipts available for read operations")
            return
        
        test_cases = [
            {
                'name': 'Get receipt by ID',
                'operation': lambda: get_receipt_by_id(self.test_user_id, self.test_receipts[0].id)
            },
            {
                'name': 'Get all receipts for user',
                'operation': lambda: get_receipts(self.test_user_id)
            },
            {
                'name': 'Get receipts with pagination',
                'operation': lambda: get_receipts(self.test_user_id, page=1, page_size=2)
            },
            {
                'name': 'Get receipts by store name',
                'operation': lambda: get_receipts(self.test_user_id, store_name="Test Store")
            },
            {
                'name': 'Get receipts by date range',
                'operation': lambda: get_receipts(
                    self.test_user_id,
                    start_date=date.today() - timedelta(days=1),
                    end_date=date.today()
                )
            },
            {
                'name': 'Get receipts by processing status',
                'operation': lambda: get_receipts(
                    self.test_user_id,
                    processing_status=ReceiptProcessingStatus.PENDING
                )
            },
            {
                'name': 'Get receipts with sorting',
                'operation': lambda: get_receipts(
                    self.test_user_id,
                    sort_by="total_amount",
                    sort_order="desc"
                )
            },
            {
                'name': 'Get receipts with complex filters',
                'operation': lambda: get_receipts(
                    self.test_user_id,
                    store_name="Store",
                    start_date=date.today() - timedelta(days=30),
                    processing_status=ReceiptProcessingStatus.PENDING,
                    page=1,
                    page_size=10
                )
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                result = await test_case['operation']()
                end_time = time.time()
                
                if result:
                    if hasattr(result, 'receipts'):  # ReceiptsListResponse
                        count = len(result.receipts)
                        details = f"Retrieved {count} receipts, total: {result.total_count}"
                    else:  # Single receipt
                        count = 1
                        details = f"Retrieved receipt: {result.id}"
                    
                    self.test_results['read_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'PASS',
                        'count': count,
                        'execution_time_ms': (end_time - start_time) * 1000,
                        'details': details
                    })
                    logger.info(f"✓ {test_case['name']}: {details}")
                else:
                    self.test_results['read_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'FAIL',
                        'error': 'Operation returned None',
                        'execution_time_ms': (end_time - start_time) * 1000
                    })
                    logger.error(f"✗ {test_case['name']}: No results returned")
                    
            except Exception as e:
                end_time = time.time()
                self.test_results['read_operations'].append({
                    'test_name': test_case['name'],
                    'status': 'ERROR',
                    'error': str(e),
                    'execution_time_ms': (end_time - start_time) * 1000
                })
                logger.error(f"✗ {test_case['name']}: Exception - {e}")
    
    async def test_update_operations(self):
        """Test receipt update operations"""
        logger.info("Testing UPDATE operations...")
        
        from app.crud.receipts import update_receipt
        from app.models.receipts import ReceiptUpdate, ReceiptProcessingStatus, ReceiptItem, ReceiptItemCategory
        
        if not self.test_receipts:
            logger.warning("No test receipts available for update operations")
            return
        
        test_receipt = self.test_receipts[0]
        
        test_cases = [
            {
                'name': 'Update store name',
                'data': ReceiptUpdate(store_name="Updated Store Name")
            },
            {
                'name': 'Update total amount',
                'data': ReceiptUpdate(total_amount=99.99)
            },
            {
                'name': 'Update processing status',
                'data': ReceiptUpdate(
                    processing_status=ReceiptProcessingStatus.PROCESSING,
                    processed_at=datetime.utcnow()
                )
            },
            {
                'name': 'Update receipt items',
                'data': ReceiptUpdate(
                    items=[
                        ReceiptItem(
                            name="Test Item 1",
                            quantity=2.0,
                            unit_price=5.99,
                            total_price=11.98,
                            category=ReceiptItemCategory.PRODUCE
                        ),
                        ReceiptItem(
                            name="Test Item 2",
                            quantity=1.0,
                            unit_price=3.50,
                            total_price=3.50,
                            category=ReceiptItemCategory.DAIRY
                        )
                    ]
                )
            },
            {
                'name': 'Update multiple fields',
                'data': ReceiptUpdate(
                    store_name="Multi-Update Store",
                    total_amount=45.67,
                    processing_status=ReceiptProcessingStatus.COMPLETED,
                    processed_at=datetime.utcnow()
                )
            },
            {
                'name': 'Update with empty data (no-op)',
                'data': ReceiptUpdate()
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                result = await update_receipt(self.test_user_id, test_receipt.id, test_case['data'])
                end_time = time.time()
                
                if result:
                    self.test_results['update_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'PASS',
                        'receipt_id': result.id,
                        'execution_time_ms': (end_time - start_time) * 1000,
                        'details': f"Updated receipt {result.id}"
                    })
                    logger.info(f"✓ {test_case['name']}: Updated receipt {result.id}")
                else:
                    self.test_results['update_operations'].append({
                        'test_name': test_case['name'],
                        'status': 'FAIL',
                        'error': 'update_receipt returned None',
                        'execution_time_ms': (end_time - start_time) * 1000
                    })
                    logger.error(f"✗ {test_case['name']}: Failed to update receipt")
                    
            except Exception as e:
                end_time = time.time()
                self.test_results['update_operations'].append({
                    'test_name': test_case['name'],
                    'status': 'ERROR',
                    'error': str(e),
                    'execution_time_ms': (end_time - start_time) * 1000
                })
                logger.error(f"✗ {test_case['name']}: Exception - {e}")
    
    async def test_delete_operations(self):
        """Test receipt delete operations and cleanup"""
        logger.info("Testing DELETE operations...")
        
        from app.crud.receipts import delete_receipt, get_receipt_by_id
        
        if len(self.test_receipts) < 2:
            logger.warning("Not enough test receipts for delete operations")
            return
        
        # Test deleting one receipt
        receipt_to_delete = self.test_receipts[-1]  # Delete the last one
        
        test_cases = [
            {
                'name': 'Delete existing receipt',
                'receipt_id': receipt_to_delete.id,
                'should_succeed': True
            },
            {
                'name': 'Delete non-existent receipt',
                'receipt_id': str(uuid.uuid4()),
                'should_succeed': False
            },
            {
                'name': 'Delete with invalid receipt ID',
                'receipt_id': 'invalid-id',
                'should_succeed': False
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                # First verify receipt exists (for valid cases)
                if test_case['should_succeed']:
                    existing_receipt = await get_receipt_by_id(self.test_user_id, test_case['receipt_id'])
                    if not existing_receipt:
                        logger.warning(f"Receipt {test_case['receipt_id']} doesn't exist before delete test")
                
                # Perform delete
                result = await delete_receipt(self.test_user_id, test_case['receipt_id'])
                end_time = time.time()
                
                if result == test_case['should_succeed']:
                    # Verify deletion (for successful cases)
                    if test_case['should_succeed']:
                        deleted_receipt = await get_receipt_by_id(self.test_user_id, test_case['receipt_id'])
                        if deleted_receipt is None:
                            status = 'PASS'
                            details = f"Successfully deleted receipt {test_case['receipt_id']}"
                        else:
                            status = 'FAIL'
                            details = f"Receipt {test_case['receipt_id']} still exists after deletion"
                    else:
                        status = 'PASS'
                        details = f"Correctly failed to delete {test_case['receipt_id']}"
                else:
                    status = 'FAIL'
                    details = f"Expected {test_case['should_succeed']}, got {result}"
                
                self.test_results['delete_operations'].append({
                    'test_name': test_case['name'],
                    'status': status,
                    'receipt_id': test_case['receipt_id'],
                    'execution_time_ms': (end_time - start_time) * 1000,
                    'details': details
                })
                
                if status == 'PASS':
                    logger.info(f"✓ {test_case['name']}: {details}")
                else:
                    logger.error(f"✗ {test_case['name']}: {details}")
                    
            except Exception as e:
                end_time = time.time()
                self.test_results['delete_operations'].append({
                    'test_name': test_case['name'],
                    'status': 'ERROR',
                    'error': str(e),
                    'execution_time_ms': (end_time - start_time) * 1000
                })
                logger.error(f"✗ {test_case['name']}: Exception - {e}")
    
    async def test_index_performance(self):
        """Test database index performance"""
        logger.info("Testing INDEX performance...")
        
        from app.database import get_collection
        from app.crud.receipts import get_receipts
        
        try:
            receipts_collection = await get_collection("receipts")
            
            # Test index existence
            indexes = await receipts_collection.list_indexes().to_list(length=None)
            index_names = [idx['name'] for idx in indexes]
            
            expected_indexes = [
                '_id_',  # Default MongoDB index
                'user_id_index',
                'receipt_date_index',
                'user_id_store_index',
                'user_id_status_index'
            ]
            
            for expected_index in expected_indexes:
                if expected_index in index_names:
                    self.test_results['index_performance'].append({
                        'test_name': f'Index exists: {expected_index}',
                        'status': 'PASS',
                        'details': f'Index {expected_index} found'
                    })
                    logger.info(f"✓ Index exists: {expected_index}")
                else:
                    self.test_results['index_performance'].append({
                        'test_name': f'Index exists: {expected_index}',
                        'status': 'FAIL',
                        'details': f'Index {expected_index} not found'
                    })
                    logger.error(f"✗ Index missing: {expected_index}")
            
            # Test query performance with indexes
            start_time = time.time()
            result = await get_receipts(self.test_user_id, page_size=100)
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            
            self.test_results['index_performance'].append({
                'test_name': 'User query performance',
                'status': 'PASS' if query_time < 1000 else 'SLOW',  # < 1 second
                'execution_time_ms': query_time,
                'details': f'Query took {query_time:.2f}ms'
            })
            
            if query_time < 1000:
                logger.info(f"✓ User query performance: {query_time:.2f}ms")
            else:
                logger.warning(f"⚠ User query performance slow: {query_time:.2f}ms")
                
        except Exception as e:
            self.test_results['index_performance'].append({
                'test_name': 'Index performance test',
                'status': 'ERROR',
                'error': str(e)
            })
            logger.error(f"✗ Index performance test failed: {e}")
    
    async def test_data_integrity(self):
        """Test data integrity and referential constraints"""
        logger.info("Testing DATA INTEGRITY...")
        
        from app.crud.receipts import create_receipt, get_receipt_by_id
        from app.models.receipts import ReceiptCreate
        
        test_cases = [
            {
                'name': 'Invalid user ID format',
                'user_id': 'invalid-user-id',
                'data': ReceiptCreate(
                    store_name="Test Store",
                    receipt_date=date.today(),
                    total_amount=10.00
                ),
                'should_succeed': True  # Should still work, just with invalid user_id
            },
            {
                'name': 'Future receipt date validation',
                'user_id': self.test_user_id,
                'data': ReceiptCreate(
                    store_name="Future Store",
                    receipt_date=date.today() + timedelta(days=1),
                    total_amount=10.00
                ),
                'should_succeed': False  # Should fail validation
            },
            {
                'name': 'Negative total amount',
                'user_id': self.test_user_id,
                'data': ReceiptCreate(
                    store_name="Negative Store",
                    receipt_date=date.today(),
                    total_amount=-10.00
                ),
                'should_succeed': False  # Should fail validation
            },
            {
                'name': 'Empty store name',
                'user_id': self.test_user_id,
                'data': ReceiptCreate(
                    store_name="",
                    receipt_date=date.today(),
                    total_amount=10.00
                ),
                'should_succeed': False  # Should fail validation
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                result = await create_receipt(test_case['user_id'], test_case['data'])
                end_time = time.time()
                
                success = result is not None
                
                if success == test_case['should_succeed']:
                    status = 'PASS'
                    details = f"Validation behaved as expected: {success}"
                else:
                    status = 'FAIL'
                    details = f"Expected {test_case['should_succeed']}, got {success}"
                
                self.test_results['data_integrity'].append({
                    'test_name': test_case['name'],
                    'status': status,
                    'execution_time_ms': (end_time - start_time) * 1000,
                    'details': details
                })
                
                if status == 'PASS':
                    logger.info(f"✓ {test_case['name']}: {details}")
                else:
                    logger.error(f"✗ {test_case['name']}: {details}")
                    
            except Exception as e:
                end_time = time.time()
                # For validation tests, exceptions might be expected
                if not test_case['should_succeed']:
                    status = 'PASS'
                    details = f"Expected validation error: {str(e)}"
                    logger.info(f"✓ {test_case['name']}: {details}")
                else:
                    status = 'ERROR'
                    details = f"Unexpected exception: {str(e)}"
                    logger.error(f"✗ {test_case['name']}: {details}")
                
                self.test_results['data_integrity'].append({
                    'test_name': test_case['name'],
                    'status': status,
                    'execution_time_ms': (end_time - start_time) * 1000,
                    'details': details
                })
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("Testing ERROR HANDLING...")
        
        from app.crud.receipts import get_receipt_by_id, update_receipt, delete_receipt
        from app.models.receipts import ReceiptUpdate
        
        test_cases = [
            {
                'name': 'Get receipt with invalid ObjectId',
                'operation': lambda: get_receipt_by_id(self.test_user_id, 'invalid-object-id')
            },
            {
                'name': 'Get receipt with non-existent ID',
                'operation': lambda: get_receipt_by_id(self.test_user_id, str(uuid.uuid4()))
            },
            {
                'name': 'Update non-existent receipt',
                'operation': lambda: update_receipt(
                    self.test_user_id,
                    str(uuid.uuid4()),
                    ReceiptUpdate(store_name="Updated")
                )
            },
            {
                'name': 'Delete non-existent receipt',
                'operation': lambda: delete_receipt(self.test_user_id, str(uuid.uuid4()))
            },
            {
                'name': 'Get receipt for wrong user',
                'operation': lambda: get_receipt_by_id(
                    str(uuid.uuid4()),  # Different user
                    self.test_receipts[0].id if self.test_receipts else str(uuid.uuid4())
                )
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            try:
                result = await test_case['operation']()
                end_time = time.time()
                
                # For error handling tests, we expect None or False results
                if result is None or result is False:
                    status = 'PASS'
                    details = "Correctly handled error case"
                else:
                    status = 'FAIL'
                    details = f"Expected None/False, got {type(result)}"
                
                self.test_results['error_handling'].append({
                    'test_name': test_case['name'],
                    'status': status,
                    'execution_time_ms': (end_time - start_time) * 1000,
                    'details': details
                })
                
                if status == 'PASS':
                    logger.info(f"✓ {test_case['name']}: {details}")
                else:
                    logger.error(f"✗ {test_case['name']}: {details}")
                    
            except Exception as e:
                end_time = time.time()
                # Some exceptions are acceptable for error handling tests
                self.test_results['error_handling'].append({
                    'test_name': test_case['name'],
                    'status': 'PASS',  # Exception is acceptable for error cases
                    'execution_time_ms': (end_time - start_time) * 1000,
                    'details': f"Exception handled: {str(e)}"
                })
                logger.info(f"✓ {test_case['name']}: Exception handled - {e}")
    
    async def test_concurrent_operations(self):
        """Test concurrent database operations"""
        logger.info("Testing CONCURRENT operations...")
        
        from app.crud.receipts import create_receipt, get_receipts
        from app.models.receipts import ReceiptCreate
        
        # Test concurrent creates
        async def create_concurrent_receipt(index):
            try:
                data = ReceiptCreate(
                    store_name=f"Concurrent Store {index}",
                    receipt_date=date.today(),
                    total_amount=float(index * 10)
                )
                result = await create_receipt(self.test_user_id, data)
                return {'success': True, 'receipt_id': result.id if result else None, 'index': index}
            except Exception as e:
                return {'success': False, 'error': str(e), 'index': index}
        
        # Test concurrent reads
        async def read_concurrent_receipts(index):
            try:
                result = await get_receipts(self.test_user_id, page=1, page_size=10)
                return {'success': True, 'count': len(result.receipts) if result else 0, 'index': index}
            except Exception as e:
                return {'success': False, 'error': str(e), 'index': index}
        
        # Run concurrent creates
        start_time = time.time()
        create_tasks = [create_concurrent_receipt(i) for i in range(5)]
        create_results = await asyncio.gather(*create_tasks)
        create_end_time = time.time()
        
        successful_creates = sum(1 for r in create_results if r['success'])
        
        self.test_results['concurrent_operations'].append({
            'test_name': 'Concurrent creates',
            'status': 'PASS' if successful_creates >= 4 else 'FAIL',  # Allow 1 failure
            'execution_time_ms': (create_end_time - start_time) * 1000,
            'details': f'{successful_creates}/5 concurrent creates succeeded'
        })
        
        if successful_creates >= 4:
            logger.info(f"✓ Concurrent creates: {successful_creates}/5 succeeded")
        else:
            logger.error(f"✗ Concurrent creates: Only {successful_creates}/5 succeeded")
        
        # Run concurrent reads
        start_time = time.time()
        read_tasks = [read_concurrent_receipts(i) for i in range(10)]
        read_results = await asyncio.gather(*read_tasks)
        read_end_time = time.time()
        
        successful_reads = sum(1 for r in read_results if r['success'])
        
        self.test_results['concurrent_operations'].append({
            'test_name': 'Concurrent reads',
            'status': 'PASS' if successful_reads >= 9 else 'FAIL',  # Allow 1 failure
            'execution_time_ms': (read_end_time - start_time) * 1000,
            'details': f'{successful_reads}/10 concurrent reads succeeded'
        })
        
        if successful_reads >= 9:
            logger.info(f"✓ Concurrent reads: {successful_reads}/10 succeeded")
        else:
            logger.error(f"✗ Concurrent reads: Only {successful_reads}/10 succeeded")
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        try:
            from app.database import get_collection
            
            receipts_collection = await get_collection("receipts")
            
            # Delete all test receipts
            result = await receipts_collection.delete_many({"user_id": self.test_user_id})
            
            logger.info(f"Cleaned up {result.deleted_count} test receipts")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.test_results.items():
            if category == 'summary':
                continue
            
            for test in tests:
                total_tests += 1
                status = test.get('status', 'UNKNOWN')
                if status == 'PASS':
                    passed_tests += 1
                elif status == 'FAIL':
                    failed_tests += 1
                elif status == 'ERROR':
                    error_tests += 1
        
        end_time = time.time()
        total_execution_time = (end_time - self.start_time) if self.start_time else 0
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_execution_time_seconds': total_execution_time,
            'test_user_id': self.test_user_id,
            'test_receipts_created': len(self.test_receipts)
        }
        
        logger.info(f"Test Summary: {passed_tests}/{total_tests} passed ({self.test_results['summary']['success_rate']:.1f}%)")
        logger.info(f"Failed: {failed_tests}, Errors: {error_tests}")
        logger.info(f"Total execution time: {total_execution_time:.2f} seconds")
    
    async def run_all_tests(self):
        """Run all CRUD tests"""
        self.start_time = time.time()
        logger.info("Starting comprehensive receipt database CRUD tests...")
        
        # Setup
        if not await self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        try:
            # Run all test categories
            await self.test_create_operations()
            await self.test_read_operations()
            await self.test_update_operations()
            await self.test_delete_operations()
            await self.test_index_performance()
            await self.test_data_integrity()
            await self.test_error_handling()
            await self.test_concurrent_operations()
            
            # Generate summary
            self.generate_summary()
            
            # Save results
            await self.save_test_results()
            
            return True
            
        finally:
            # Cleanup
            await self.cleanup_test_data()
    
    async def save_test_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_crud_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            logger.info(f"Test results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")


async def main():
    """Main test execution function"""
    tester = ReceiptCRUDTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("All tests completed successfully!")
            
            # Print summary
            summary = tester.test_results['summary']
            print("\n" + "="*60)
            print("RECEIPT DATABASE CRUD TEST SUMMARY")
            print("="*60)
            print(f"Total Tests: {summary['total_tests']}")
            print(f"Passed: {summary['passed_tests']}")
            print(f"Failed: {summary['failed_tests']}")
            print(f"Errors: {summary['error_tests']}")
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Execution Time: {summary['total_execution_time_seconds']:.2f} seconds")
            print(f"Test Receipts Created: {summary['test_receipts_created']}")
            print("="*60)
            
            # Print category breakdown
            for category, tests in tester.test_results.items():
                if category == 'summary':
                    continue
                
                category_passed = sum(1 for t in tests if t.get('status') == 'PASS')
                category_total = len(tests)
                print(f"{category.replace('_', ' ').title()}: {category_passed}/{category_total}")
            
            print("="*60)
            
            return 0 if summary['failed_tests'] == 0 and summary['error_tests'] == 0 else 1
        else:
            logger.error("Test execution failed")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)