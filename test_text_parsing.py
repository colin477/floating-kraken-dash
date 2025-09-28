"""
Test script for text parsing functionality (without OCR dependencies)
"""

import sys
import os
from datetime import date

# Add backend to path
sys.path.append('backend')

# Mock the PIL import to avoid dependency issues during testing
sys.modules['PIL'] = type(sys)('PIL')
sys.modules['PIL.Image'] = type(sys)('PIL.Image')

# Mock google.cloud.vision
sys.modules['google'] = type(sys)('google')
sys.modules['google.cloud'] = type(sys)('google.cloud')
sys.modules['google.cloud.vision'] = type(sys)('google.cloud.vision')

from app.models.receipts import ReceiptItemCategory

def test_text_parsing():
    """Test the text parsing functionality without OCR dependencies"""
    print("Testing Receipt Text Parsing")
    print("=" * 50)
    
    # Import after mocking dependencies
    from app.utils.ocr_service import OCRService
    
    # Initialize OCR service
    ocr_service = OCRService()
    
    print(f"OCR Enabled: {ocr_service.enabled}")
    print(f"Fallback Enabled: {ocr_service.fallback_enabled}")
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
    
    print("\nText parsing test completed!")
    
    # Test different receipt formats
    print("\nTesting different receipt formats:")
    print("-" * 40)
    
    # Test with @ pricing format
    receipt_with_at_pricing = """
    TARGET
    456 OAK ST
    
    01/20/2024
    
    APPLES @ 1.99          3.98
    CHICKEN BREAST @ 5.99  11.98
    ORANGE JUICE           4.49
    
    SUBTOTAL              20.45
    TAX                    1.64
    TOTAL                 22.09
    """
    
    parsed_at_data = ocr_service.parse_receipt_text(receipt_with_at_pricing)
    at_items = parsed_at_data.get('items', [])
    
    print(f"Store: {parsed_at_data.get('store_name', 'Not detected')}")
    print(f"Items with @ pricing: {len(at_items)}")
    
    for item in at_items:
        print(f"  {item.name}: {item.quantity} x ${item.unit_price:.2f} = ${item.total_price:.2f}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_text_parsing()