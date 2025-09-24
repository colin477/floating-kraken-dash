"""
Test script to verify Receipt Processing integration with existing systems
"""

import asyncio
import json
import os
from datetime import date, datetime
from app.models.receipts import ReceiptCreate, ReceiptItem, ReceiptItemCategory
from app.crud.receipts import (
    create_receipt,
    get_receipt_by_id,
    process_receipt_image,
    add_receipt_items_to_pantry
)
from app.crud.pantry import get_pantry_items
from app.database import get_collection, connect_to_mongo, close_mongo_connection

# Mock user ID for testing
TEST_USER_ID = "507f1f77bcf86cd799439011"

async def test_receipt_integration():
    """Test the complete receipt processing workflow"""
    print("🧪 Testing Receipt Processing Integration...")
    
    try:
        # Test 1: Create a receipt
        print("\n1️⃣ Testing receipt creation...")
        receipt_data = ReceiptCreate(
            store_name="Test Grocery Store",
            receipt_date=date.today(),
            total_amount=25.99,
            photo_url="https://example.com/receipt.jpg"
        )
        
        created_receipt = await create_receipt(TEST_USER_ID, receipt_data)
        if created_receipt:
            print(f"✅ Receipt created successfully: {created_receipt.id}")
            receipt_id = created_receipt.id
        else:
            print("❌ Failed to create receipt")
            return False
        
        # Test 2: Process the receipt (mock AI processing)
        print("\n2️⃣ Testing receipt processing...")
        processing_result = await process_receipt_image(TEST_USER_ID, receipt_id)
        if processing_result:
            print(f"✅ Receipt processed successfully with {len(processing_result.extracted_items)} items")
            print(f"   Confidence score: {processing_result.confidence_score}")
        else:
            print("❌ Failed to process receipt")
            return False
        
        # Test 3: Verify receipt was updated with items
        print("\n3️⃣ Testing receipt retrieval after processing...")
        updated_receipt = await get_receipt_by_id(TEST_USER_ID, receipt_id)
        if updated_receipt and updated_receipt.items:
            print(f"✅ Receipt has {len(updated_receipt.items)} processed items")
            for i, item in enumerate(updated_receipt.items):
                print(f"   Item {i}: {item.name} - ${item.total_price}")
        else:
            print("❌ Receipt not properly updated with items")
            return False
        
        # Test 4: Add items to pantry
        print("\n4️⃣ Testing pantry integration...")
        selected_items = [0, 1]  # Select first two items
        pantry_result = await add_receipt_items_to_pantry(
            TEST_USER_ID, 
            receipt_id, 
            selected_items, 
            expiration_days=7
        )
        
        if pantry_result:
            print(f"✅ Added {pantry_result.items_added} items to pantry")
            print(f"   Failed items: {pantry_result.items_failed}")
            if pantry_result.errors:
                print(f"   Errors: {pantry_result.errors}")
        else:
            print("❌ Failed to add items to pantry")
            return False
        
        # Test 5: Verify pantry items were created
        print("\n5️⃣ Testing pantry verification...")
        pantry_items = await get_pantry_items(TEST_USER_ID, page_size=10)
        if pantry_items and pantry_items.items:
            receipt_items = [item for item in pantry_items.items if "receipt" in item.notes.lower()]
            print(f"✅ Found {len(receipt_items)} items in pantry from receipts")
            for item in receipt_items:
                print(f"   Pantry item: {item.name} ({item.category}) - expires in {item.days_until_expiration} days")
        else:
            print("❌ No pantry items found")
            return False
        
        print("\n🎉 All integration tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def cleanup_test_data():
    """Clean up test data"""
    try:
        print("\n🧹 Cleaning up test data...")
        
        # Clean up receipts
        receipts_collection = await get_collection("receipts")
        result = await receipts_collection.delete_many({"user_id": TEST_USER_ID})
        print(f"   Deleted {result.deleted_count} test receipts")
        
        # Clean up pantry items
        pantry_collection = await get_collection("pantry_items")
        result = await pantry_collection.delete_many({
            "user_id": TEST_USER_ID,
            "notes": {"$regex": "receipt", "$options": "i"}
        })
        print(f"   Deleted {result.deleted_count} test pantry items")
        
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Receipt Processing Integration Tests")
    
    try:
        # Initialize database connection
        print("🔌 Connecting to database...")
        await connect_to_mongo()
        print("✅ Database connected successfully")
        
        # Run the integration test
        success = await test_receipt_integration()
        
        # Clean up test data
        await cleanup_test_data()
        
        if success:
            print("\n✅ All tests completed successfully!")
            print("\n📋 Summary of implemented features:")
            print("   • Receipt data models with proper validation")
            print("   • Complete CRUD operations for receipts")
            print("   • Mock AI processing for receipt image analysis")
            print("   • Integration with pantry management system")
            print("   • Full REST API with authentication")
            print("   • Database indexes for optimal performance")
            print("   • Comprehensive error handling")
        else:
            print("\n❌ Some tests failed - check the output above")
            
    except Exception as e:
        print(f"\n❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        print("\n🔌 Closing database connection...")
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())