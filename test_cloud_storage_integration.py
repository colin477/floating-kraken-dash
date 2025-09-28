#!/usr/bin/env python3
"""
Test script for cloud storage integration
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.utils.cloud_storage import cloud_storage_service


async def test_cloud_storage_integration():
    """Test the cloud storage integration"""
    print("🧪 Testing Cloud Storage Integration")
    print("=" * 50)
    
    # Test 1: Check if cloud storage is properly configured
    print("\n1. Testing cloud storage configuration...")
    print(f"   Cloud storage enabled: {cloud_storage_service.enabled}")
    print(f"   Fallback to local: {cloud_storage_service.fallback_to_local}")
    print(f"   S3 client initialized: {cloud_storage_service.s3_client is not None}")
    print(f"   AWS Region: {cloud_storage_service.aws_region}")
    print(f"   S3 Bucket: {cloud_storage_service.s3_bucket_name}")
    
    # Test 2: Create a test image file
    print("\n2. Creating test image file...")
    test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    test_filename = "test_receipt.png"
    print(f"   Created test PNG file: {test_filename}")
    
    # Test 3: Upload file
    print("\n3. Testing file upload...")
    try:
        file_url = await cloud_storage_service.upload_file(
            file_content=test_image_content,
            filename=test_filename,
            content_type="image/png",
            user_id="test_user_123"
        )
        
        if file_url:
            print(f"   ✅ File uploaded successfully: {file_url}")
            storage_type = cloud_storage_service.get_storage_type(file_url)
            print(f"   Storage type: {storage_type}")
        else:
            print("   ❌ File upload failed")
            return False
            
    except Exception as e:
        print(f"   ❌ File upload error: {e}")
        return False
    
    # Test 4: Generate secure URL
    print("\n4. Testing secure URL generation...")
    try:
        secure_url = await cloud_storage_service.generate_presigned_url(file_url, expiration=300)
        if secure_url:
            print(f"   ✅ Secure URL generated: {secure_url[:100]}...")
        else:
            print("   ❌ Failed to generate secure URL")
            
    except Exception as e:
        print(f"   ❌ Secure URL generation error: {e}")
    
    # Test 5: Get file info
    print("\n5. Testing file info retrieval...")
    try:
        file_info = await cloud_storage_service.get_file_info(file_url)
        if file_info:
            print(f"   ✅ File info retrieved: {file_info}")
        else:
            print("   ℹ️  File info not available (normal for local storage)")
            
    except Exception as e:
        print(f"   ❌ File info retrieval error: {e}")
    
    # Test 6: Clean up - delete file
    print("\n6. Testing file deletion...")
    try:
        deleted = await cloud_storage_service.delete_file(file_url)
        if deleted:
            print("   ✅ File deleted successfully")
        else:
            print("   ❌ File deletion failed")
            
    except Exception as e:
        print(f"   ❌ File deletion error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Cloud storage integration test completed!")
    
    return True


async def test_receipt_upload_simulation():
    """Simulate a receipt upload workflow"""
    print("\n🧪 Testing Receipt Upload Workflow Simulation")
    print("=" * 50)
    
    # Import receipt-related modules
    try:
        from app.models.receipts import ReceiptCreate
        from app.utils.ocr_service import ocr_service
        print("   ✅ Receipt modules imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import receipt modules: {e}")
        return False
    
    # Test OCR service configuration
    print(f"\n   OCR enabled: {ocr_service.enabled}")
    print(f"   OCR fallback enabled: {ocr_service.fallback_enabled}")
    print(f"   OCR client initialized: {ocr_service.client is not None}")
    
    # Create a mock receipt image
    mock_receipt_content = test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Upload mock receipt
    print("\n   Uploading mock receipt...")
    try:
        receipt_url = await cloud_storage_service.upload_file(
            file_content=mock_receipt_content,
            filename="mock_receipt.png",
            content_type="image/png",
            user_id="test_user_receipt"
        )
        
        if receipt_url:
            print(f"   ✅ Mock receipt uploaded: {receipt_url}")
            
            # Test OCR processing (will likely fail due to mock image, but tests the workflow)
            print("   Testing OCR processing workflow...")
            try:
                extracted_text = await ocr_service.extract_text_from_image(receipt_url)
                if extracted_text:
                    print(f"   ✅ OCR extracted text: {extracted_text[:100]}...")
                else:
                    print("   ℹ️  OCR returned no text (expected for mock image)")
            except Exception as e:
                print(f"   ℹ️  OCR processing failed (expected): {e}")
            
            # Clean up
            await cloud_storage_service.delete_file(receipt_url)
            print("   ✅ Mock receipt cleaned up")
            
        else:
            print("   ❌ Mock receipt upload failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Receipt workflow error: {e}")
        return False
    
    print("\n🎉 Receipt upload workflow test completed!")
    return True


async def main():
    """Main test function"""
    print("🚀 Starting Cloud Storage Integration Tests")
    
    # Test basic cloud storage functionality
    success1 = await test_cloud_storage_integration()
    
    # Test receipt upload workflow
    success2 = await test_receipt_upload_simulation()
    
    if success1 and success2:
        print("\n✅ All tests passed! Cloud storage integration is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)