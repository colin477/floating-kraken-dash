#!/usr/bin/env python3
"""
Test script to verify thefuzz import and functionality for Python 3.13 compatibility.
"""

def test_thefuzz_import():
    """Test that thefuzz can be imported successfully."""
    try:
        from thefuzz import fuzz
        print("✅ Successfully imported thefuzz.fuzz")
        return True
    except ImportError as e:
        print(f"❌ Failed to import thefuzz.fuzz: {e}")
        return False

def test_fuzz_ratio_functionality():
    """Test that fuzz.ratio() function works as expected."""
    try:
        from thefuzz import fuzz
        
        # Test basic string similarity
        test_cases = [
            ("apple", "apple", 100),  # Exact match
            ("apple", "aple", 80),    # Close match
            ("apple", "orange", 30),   # Different strings
            ("chicken breast", "chicken", 60),  # Partial match
        ]
        
        print("\n🧪 Testing fuzz.ratio() functionality:")
        all_passed = True
        
        for str1, str2, expected_min in test_cases:
            ratio = fuzz.ratio(str1, str2)
            passed = ratio >= expected_min if expected_min > 0 else ratio == 0
            status = "✅" if passed else "❌"
            print(f"{status} fuzz.ratio('{str1}', '{str2}') = {ratio} (expected >= {expected_min})")
            if not passed:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Error testing fuzz.ratio(): {e}")
        return False

def test_process_functionality():
    """Test that thefuzz.process works for fuzzy matching."""
    try:
        from thefuzz import process
        
        choices = ["apple", "banana", "orange", "grape", "pineapple"]
        query = "aple"
        
        # Test extractOne
        best_match = process.extractOne(query, choices)
        print(f"\n🔍 Testing process.extractOne('{query}', {choices}):")
        print(f"✅ Best match: {best_match}")
        
        # Test extract with limit
        matches = process.extract(query, choices, limit=3)
        print(f"✅ Top 3 matches: {matches}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing thefuzz.process: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing thefuzz compatibility for Python 3.13")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_thefuzz_import),
        ("Ratio Functionality Test", test_fuzz_ratio_functionality),
        ("Process Functionality Test", test_process_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests PASSED! thefuzz is working correctly with Python 3.13")
    else:
        print("⚠️  Some tests FAILED! There may be compatibility issues.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)