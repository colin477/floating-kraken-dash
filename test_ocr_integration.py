"""
Test script for OCR integration
"""

import asyncio
import os
import sys
from datetime import date

# Add backend to path
sys.path.append('backend')

from app.utils.ocr_service import OCRService
from app.models.receipts import ReceiptItemCategory

async def test_ocr_service():
    """Test the OCR service functionality"""
    print("Testing OCR Service Integration")
    print("=" * 50)
    
    # Initialize OCR service
    ocr_service = OCRService()
    
    print(f"OCR Enabled: {ocr_service.enabled}")
    print(f"Fallback Enabled: {ocr_service.fallback_enabled}")
    print(f"Google Vision Available: {ocr_service.client is not None}")
    print()
    
    # Test text parsing with sample receipt text
    sample_receipt_text = """
    WALMART SUPERCENTER
    123 MAIN ST
    ANYTOWN, ST 12345
    
    12/15/2023
    
    BANANAS                 1.68
    MILK WHOLE GAL          3.49
    BREAD WHITE             2.99
    GROUND BEEF 80/20       7.19
    EGGS LARGE              2.89
    CHEESE CHEDDAR          4.99
    
    SUBTOTAL               23.23
    TAX                     1.86
    TOTAL                  25.09
    
    THANK YOU FOR SHOPPING
    """
    
    print("Testing text parsing with sample receipt:")
    print("-" * 40)
    
    parsed_data = ocr_service.parse_receipt_text(sample_receipt_text)
    
    print(f"Store Name: {parsed_data.get('store_name', 'Not detected')}")
    print(f"Receipt Date: {parsed_data.get('receipt_date', 'Not detected')}")
    print(f"Subtotal: ${parsed_data.get('subtotal', 'Not detected')}")
    print(f"Tax: ${parsed_data.get('tax', 'Not detected')}")
    print(f"Total: ${parsed_data.get('total', 'Not detected')}")
    print()
    
    items = parsed_data.get('items', [])
    print(f"Items Found: {len(items)}")
    print("-" * 40)
    
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.name}")
        print(f"   Quantity: {item.quantity}")
        print(f"   Unit Price: ${item.unit_price:.2f}")
        print(f"   Total Price: ${item.total_price:.2f}")
        print(f"   Category: {item.category.value}")
        print()
    
    # Test categorization
    print("Testing item categorization:")
    print("-" * 40)
    
    test_items = [
        "Organic Bananas",
        "Whole Milk",
        "Ground Beef",
        "Frozen Pizza",
        "Coca Cola",
        "Bread",
        "Canned Soup",
        "Potato Chips",
        "Olive Oil",
        "Salt",
        "Vanilla Extract"
    ]
    
    for item_name in test_items:
        category = ocr_service._categorize_item(item_name)
        print(f"{item_name:<20} -> {category.value}")
    
    print("\nOCR Service test completed!")

if __name__ == "__main__":
    asyncio.run(test_ocr_service())