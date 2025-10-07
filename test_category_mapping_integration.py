#!/usr/bin/env python3
"""
Test script to verify category mapping integration between receipt processing and pantry system.
Tests the standardized category mapping system for seamless integration.
"""

import sys
import os
import asyncio
from datetime import date, timedelta

# Add the backend directory to the Python path
sys.path.append('./backend')

def test_category_mapper():
    """Test the category mapper functionality"""
    print("🧪 TESTING CATEGORY MAPPER")
    print("=" * 50)
    
    try:
        from backend.app.utils.category_mapper import category_mapper
        from backend.app.models.pantry import PantryCategory
        
        # Test cases for category mapping
        test_cases = [
            # (receipt_category, item_name, expected_category)
            (None, "bananas", PantryCategory.PRODUCE),
            (None, "milk 2% gallon", PantryCategory.DAIRY),
            (None, "chicken breast", PantryCategory.MEAT),
            (None, "salmon fillet", PantryCategory.SEAFOOD),
            (None, "whole wheat bread", PantryCategory.GRAINS),
            (None, "frozen pizza", PantryCategory.FROZEN),
            (None, "coca cola", PantryCategory.BEVERAGES),
            (None, "potato chips", PantryCategory.SNACKS),
            (None, "canned tomatoes", PantryCategory.CANNED_GOODS),
            (None, "olive oil", PantryCategory.CONDIMENTS),
            (None, "black pepper", PantryCategory.SPICES),
            (None, "vanilla extract", PantryCategory.BAKING),
            (None, "unknown item", PantryCategory.OTHER),
            ("produce", None, PantryCategory.PRODUCE),
            ("dairy", None, PantryCategory.DAIRY),
            ("beverages", None, PantryCategory.BEVERAGES),
        ]
        
        passed = 0
        failed = 0
        
        for receipt_category, item_name, expected in test_cases:
            try:
                result = category_mapper.map_category(receipt_category, item_name)
                if result == expected:
                    print(f"✅ {item_name or receipt_category} -> {result.value}")
                    passed += 1
                else:
                    print(f"❌ {item_name or receipt_category} -> {result.value} (expected {expected.value})")
                    failed += 1
            except Exception as e:
                print(f"❌ Error testing {item_name or receipt_category}: {e}")
                failed += 1
        
        print(f"\n📊 Category Mapper Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"❌ Error testing category mapper: {e}")
        return False

def test_ocr_categorization():
    """Test OCR service categorization with standardized mapping"""
    print("\n🧪 TESTING OCR CATEGORIZATION")
    print("=" * 50)
    
    try:
        from backend.app.utils.ocr_service import ocr_service
        from backend.app.models.receipts import ReceiptItemCategory
        
        # Test items with expected categories
        test_items = [
            ("BANANAS", ReceiptItemCategory.PRODUCE),
            ("MILK 2% GALLON", ReceiptItemCategory.DAIRY),
            ("CHICKEN BREAST", ReceiptItemCategory.MEAT),
            ("BREAD WHOLE WHEAT", ReceiptItemCategory.GRAINS),
            ("FROZEN PIZZA", ReceiptItemCategory.FROZEN),
            ("COCA COLA", ReceiptItemCategory.BEVERAGES),
            ("POTATO CHIPS", ReceiptItemCategory.SNACKS),
            ("CANNED SOUP", ReceiptItemCategory.CANNED_GOODS),
            ("OLIVE OIL", ReceiptItemCategory.CONDIMENTS),
            ("BLACK PEPPER", ReceiptItemCategory.SPICES),
            ("VANILLA EXTRACT", ReceiptItemCategory.BAKING),
        ]
        
        passed = 0
        failed = 0
        
        for item_name, expected_category in test_items:
            try:
                result = ocr_service._categorize_item(item_name)
                if result == expected_category:
                    print(f"✅ {item_name} -> {result.value}")
                    passed += 1
                else:
                    print(f"❌ {item_name} -> {result.value} (expected {expected_category.value})")
                    failed += 1
            except Exception as e:
                print(f"❌ Error categorizing {item_name}: {e}")
                failed += 1
        
        print(f"\n📊 OCR Categorization Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"❌ Error testing OCR categorization: {e}")
        return False

async def test_receipt_to_pantry_integration():
    """Test the full integration from receipt processing to pantry storage"""
    print("\n🧪 TESTING RECEIPT TO PANTRY INTEGRATION")
    print("=" * 50)
    
    try:
        from backend.app.utils.ocr_service import ocr_service
        from backend.app.crud.receipts import _map_receipt_category_to_pantry
        from backend.app.models.receipts import ReceiptItemCategory
        from backend.app.models.pantry import PantryCategory
        
        # Test the mapping function
        test_mappings = [
            (ReceiptItemCategory.PRODUCE, "bananas", PantryCategory.PRODUCE),
            (ReceiptItemCategory.DAIRY, "milk", PantryCategory.DAIRY),
            (ReceiptItemCategory.MEAT, "chicken", PantryCategory.MEAT),
            (ReceiptItemCategory.SEAFOOD, "salmon", PantryCategory.SEAFOOD),
            (ReceiptItemCategory.GRAINS, "bread", PantryCategory.GRAINS),
            (ReceiptItemCategory.FROZEN, "ice cream", PantryCategory.FROZEN),
            (ReceiptItemCategory.BEVERAGES, "soda", PantryCategory.BEVERAGES),
            (ReceiptItemCategory.SNACKS, "chips", PantryCategory.SNACKS),
            (ReceiptItemCategory.CANNED_GOODS, "soup", PantryCategory.CANNED_GOODS),
            (ReceiptItemCategory.CONDIMENTS, "ketchup", PantryCategory.CONDIMENTS),
            (ReceiptItemCategory.SPICES, "pepper", PantryCategory.SPICES),
            (ReceiptItemCategory.BAKING, "flour", PantryCategory.BAKING),
            (ReceiptItemCategory.OTHER, "unknown", PantryCategory.OTHER),
        ]
        
        passed = 0
        failed = 0
        
        for receipt_cat, item_name, expected_pantry_cat in test_mappings:
            try:
                result = _map_receipt_category_to_pantry(receipt_cat, item_name)
                if result == expected_pantry_cat:
                    print(f"✅ {receipt_cat.value} ({item_name}) -> {result.value}")
                    passed += 1
                else:
                    print(f"❌ {receipt_cat.value} ({item_name}) -> {result.value} (expected {expected_pantry_cat.value})")
                    failed += 1
            except Exception as e:
                print(f"❌ Error mapping {receipt_cat.value}: {e}")
                failed += 1
        
        print(f"\n📊 Receipt to Pantry Mapping Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"❌ Error testing receipt to pantry integration: {e}")
        return False

async def test_ocr_parsing_with_categories():
    """Test OCR parsing with proper categorization"""
    print("\n🧪 TESTING OCR PARSING WITH CATEGORIES")
    print("=" * 50)
    
    try:
        from backend.app.utils.ocr_service import ocr_service
        
        # Test OCR parsing with demo text
        demo_text = await ocr_service._get_demo_ocr_text("test-receipt.jpg")
        parsed_data = ocr_service.parse_receipt_text(demo_text)
        
        print(f"✅ Parsed {len(parsed_data.get('items', []))} items from demo receipt")
        
        # Check that items have proper categories
        items = parsed_data.get('items', [])
        categorized_items = 0
        
        for item in items:
            if hasattr(item, 'category') and item.category:
                print(f"✅ {item.name} -> {item.category}")
                categorized_items += 1
            else:
                print(f"❌ {item.name} -> No category")
        
        print(f"\n📊 OCR Parsing Results: {categorized_items}/{len(items)} items properly categorized")
        return categorized_items == len(items)
        
    except Exception as e:
        print(f"❌ Error testing OCR parsing: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing pantry items"""
    print("\n🧪 TESTING BACKWARD COMPATIBILITY")
    print("=" * 50)
    
    try:
        from backend.app.utils.category_mapper import category_mapper
        from backend.app.models.pantry import PantryCategory
        
        # Test various input formats that might exist in the database
        test_inputs = [
            ("produce", PantryCategory.PRODUCE),
            ("PRODUCE", PantryCategory.PRODUCE),
            ("Produce", PantryCategory.PRODUCE),
            ("dairy", PantryCategory.DAIRY),
            ("meat", PantryCategory.MEAT),
            ("beverages", PantryCategory.BEVERAGES),
            ("snacks", PantryCategory.SNACKS),
            ("other", PantryCategory.OTHER),
            ("invalid_category", PantryCategory.OTHER),
            ("", PantryCategory.OTHER),
            (None, PantryCategory.OTHER),
        ]
        
        passed = 0
        failed = 0
        
        for input_category, expected in test_inputs:
            try:
                result = category_mapper.ensure_backward_compatibility(input_category)
                if result == expected:
                    print(f"✅ '{input_category}' -> {result.value}")
                    passed += 1
                else:
                    print(f"❌ '{input_category}' -> {result.value} (expected {expected.value})")
                    failed += 1
            except Exception as e:
                print(f"❌ Error testing '{input_category}': {e}")
                failed += 1
        
        print(f"\n📊 Backward Compatibility Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"❌ Error testing backward compatibility: {e}")
        return False

async def main():
    """Run all category mapping integration tests"""
    print("🔍 CATEGORY MAPPING INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Category Mapper", test_category_mapper()),
        ("OCR Categorization", test_ocr_categorization()),
        ("Receipt to Pantry Integration", await test_receipt_to_pantry_integration()),
        ("OCR Parsing with Categories", await test_ocr_parsing_with_categories()),
        ("Backward Compatibility", test_backward_compatibility()),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, result in tests:
        if result:
            passed_tests += 1
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All category mapping integration tests PASSED!")
        print("✅ Receipt items will be correctly categorized and added to pantry")
        return True
    else:
        print("❌ Some tests failed. Category mapping needs attention.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)