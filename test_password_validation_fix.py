"""
Simple test to demonstrate the password validation fix
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.utils.exceptions import PasswordValidationError, EmailAlreadyExistsError
from app.utils.auth import hash_password
from app.models.auth import UserCreate

async def test_password_validation():
    """Test that password validation works correctly"""
    print("Testing password validation fix...")
    print("=" * 50)
    
    # Test 1: Password validation should raise PasswordValidationError
    print("\n1. Testing weak password validation:")
    try:
        weak_password = "weakpass"  # No uppercase, digits, or special chars
        hash_password(weak_password)
        print("❌ FAIL: Expected PasswordValidationError but none was raised")
        return False
    except PasswordValidationError as e:
        print(f"✅ SUCCESS: PasswordValidationError raised correctly")
        print(f"   Message: {e.message}")
        print(f"   Errors: {e.errors}")
        return True
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {type(e).__name__}: {e}")
        return False

async def test_strong_password():
    """Test that strong passwords work correctly"""
    print("\n2. Testing strong password validation:")
    try:
        strong_password = "StrongPassword123!"
        hashed = hash_password(strong_password)
        print("✅ SUCCESS: Strong password accepted and hashed")
        print(f"   Hash length: {len(hashed)} characters")
        return True
    except Exception as e:
        print(f"❌ FAIL: Strong password rejected: {type(e).__name__}: {e}")
        return False

async def main():
    """Run the tests"""
    test1_result = await test_password_validation()
    test2_result = await test_strong_password()
    
    print("\n" + "=" * 50)
    if test1_result and test2_result:
        print("✅ ALL TESTS PASSED: Password validation fix is working!")
        print("\nKey improvements:")
        print("- Password validation errors now raise PasswordValidationError")
        print("- This prevents them from being misreported as 'Email already registered'")
        print("- Strong passwords are properly accepted")
    else:
        print("❌ SOME TESTS FAILED")

if __name__ == "__main__":
    asyncio.run(main())