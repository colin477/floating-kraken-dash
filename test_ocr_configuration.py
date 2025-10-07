#!/usr/bin/env python3
"""
Test script for OCR service configuration and functionality
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_environment_variables():
    """Test if environment variables are properly configured"""
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    env_file = backend_path / ".env"
    load_dotenv(env_file)
    
    ocr_vars = {
        'GOOGLE_CLOUD_PROJECT_ID': os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        'OCR_ENABLED': os.getenv('OCR_ENABLED', 'false'),
        'OCR_FALLBACK_ENABLED': os.getenv('OCR_FALLBACK_ENABLED', 'true')
    }
    
    for var, value in ocr_vars.items():
        if value:
            if 'CREDENTIALS' in var or 'PROJECT_ID' in var:
                display_value = f'{value[:10]}...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
    
    return ocr_vars

def test_google_vision_availability():
    """Test if Google Vision API package is available"""
    print("\n📦 TESTING GOOGLE VISION API AVAILABILITY")
    print("=" * 50)
    
    try:
        from google.cloud import vision
        print("✅ google-cloud-vision package is available")
        
        # Try to initialize client (will fail without credentials, but that's expected)
        try:
            client = vision.ImageAnnotatorClient()
            print("✅ Google Vision API client can be initialized")
            return True
        except Exception as e:
            print(f"❌ Google Vision API client initialization failed: {e}")
            print("   This is expected if credentials are not configured")
            return False
            
    except ImportError as e:
        print(f"❌ google-cloud-vision package not available: {e}")
        return False

def test_ocr_service():
    """Test OCR service initialization and functionality"""
    print("\n🔍 TESTING OCR SERVICE")
    print("=" * 50)
    
    try:
        from app.utils.ocr_service import ocr_service
        
        # Get service status
        status = ocr_service.get_service_status()
        print("Service Status:")
        for key, value in status.items():
            icon = "✅" if value else "❌"
            print(f"  {icon} {key}: {value}")
        
        return status
        
    except Exception as e:
        print(f"❌ Error importing OCR service: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_ocr_functionality():
    """Test OCR text extraction functionality"""
    print("\n🧪 TESTING OCR FUNCTIONALITY")
    print("=" * 50)
    
    try:
        from app.utils.ocr_service import ocr_service
        
        # Test with a mock image URL
        test_image_url = "test-receipt.jpg"
        
        print(f"Testing OCR with image: {test_image_url}")
        result = await ocr_service.extract_text_from_image(test_image_url)
        
        if result:
            print("✅ OCR extraction successful!")
            print(f"   Text length: {len(result)} characters")
            print(f"   First 100 characters: {result[:100]}...")
            
            # Test parsing
            parsed = ocr_service.parse_receipt_text(result)
            print("✅ Text parsing successful!")
            print(f"   Store: {parsed.get('store_name', 'Not found')}")
            print(f"   Items found: {len(parsed.get('items', []))}")
            print(f"   Total: ${parsed.get('total', 'Not found')}")
            
            return True
        else:
            print("❌ OCR extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OCR functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 OCR SERVICE CONFIGURATION TEST")
    print("=" * 60)
    
    # Test environment variables
    env_vars = test_environment_variables()
    
    # Test Google Vision API availability
    vision_available = test_google_vision_availability()
    
    # Test OCR service
    service_status = test_ocr_service()
    
    # Test OCR functionality
    if service_status:
        functionality_works = asyncio.run(test_ocr_functionality())
    else:
        functionality_works = False
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 50)
    
    ocr_enabled = env_vars.get('OCR_ENABLED', 'false').lower() == 'true'
    fallback_enabled = env_vars.get('OCR_FALLBACK_ENABLED', 'true').lower() == 'true'
    credentials_configured = bool(env_vars.get('GOOGLE_CLOUD_PROJECT_ID')) and bool(env_vars.get('GOOGLE_APPLICATION_CREDENTIALS'))
    
    print(f"OCR Enabled: {ocr_enabled}")
    print(f"Fallback Enabled: {fallback_enabled}")
    print(f"Credentials Configured: {credentials_configured}")
    print(f"Google Vision Available: {vision_available}")
    print(f"OCR Functionality Works: {functionality_works}")
    
    if not ocr_enabled:
        print("\n💡 RECOMMENDATION: Set OCR_ENABLED=true in .env to enable OCR functionality")
    
    if not credentials_configured:
        print("\n💡 RECOMMENDATION: Configure Google Vision API credentials to use real OCR")
        print("   See GOOGLE_VISION_API_SETUP_GUIDE.md for detailed instructions")
    
    if fallback_enabled and not credentials_configured:
        print("\n✅ DEMO MODE: System will work with mock OCR data")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()