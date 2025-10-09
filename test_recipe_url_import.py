"""
Test script for recipe URL import functionality
"""

import asyncio
import json
import time
from datetime import datetime

import requests

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_URLS = [
    "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/",
    "https://www.food.com/recipe/simple-chicken-stir-fry-87059",
    "https://www.foodnetwork.com/recipes/alton-brown/baked-macaroni-and-cheese-recipe-1939524",
    "https://www.bonappetit.com/recipe/bas-best-chocolate-chip-cookies",
    "https://www.seriouseats.com/perfect-pan-pizza-recipe"
]

# Mock user credentials for testing (replace with actual test user)
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

class RecipeImportTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.results = []
    
    def login(self):
        """Login to get authentication token"""
        try:
            print("🔐 Logging in...")
            response = self.session.post(
                f"{BASE_URL}/auth/login-form",
                data={
                    "username": TEST_USER["email"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    print("✅ Login successful")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_url_validation(self, url):
        """Test URL validation endpoint"""
        try:
            print(f"🔍 Validating URL: {url}")
            
            response = self.session.post(
                f"{BASE_URL}/recipes/validate-url",
                json={"url": url},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Validation successful:")
                print(f"   - Domain: {data.get('domain')}")
                print(f"   - Supported: {data.get('is_supported')}")
                print(f"   - Accessible: {data.get('is_accessible')}")
                print(f"   - Valid: {data.get('is_valid')}")
                if data.get('estimated_confidence'):
                    print(f"   - Confidence: {data.get('estimated_confidence'):.2%}")
                
                return data
            else:
                print(f"❌ Validation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return None
    
    def test_recipe_import(self, url, custom_tags=None):
        """Test recipe import from URL"""
        try:
            print(f"📥 Importing recipe from: {url}")
            start_time = time.time()
            
            request_data = {
                "url": url,
                "override_duplicate": True,
                "custom_tags": custom_tags or ["test-import", "automated-test"]
            }
            
            response = self.session.post(
                f"{BASE_URL}/recipes/from-link",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Import successful in {processing_time:.0f}ms:")
                
                if data.get('success'):
                    preview = data.get('preview', {})
                    recipe = data.get('recipe', {})
                    
                    print(f"   - Title: {preview.get('title', 'N/A')}")
                    print(f"   - Ingredients: {preview.get('ingredients_count', 0)}")
                    print(f"   - Instructions: {preview.get('instructions_count', 0)}")
                    print(f"   - Servings: {preview.get('servings', 'N/A')}")
                    print(f"   - Difficulty: {preview.get('difficulty', 'N/A')}")
                    print(f"   - Data Quality: {data.get('data_quality_score', 0):.2%}")
                    print(f"   - Completeness: {data.get('completeness_score', 0):.2%}")
                    print(f"   - Recipe ID: {recipe.get('id', 'N/A')}")
                    
                    if preview.get('meal_types'):
                        print(f"   - Meal Types: {', '.join(preview['meal_types'])}")
                    
                    if preview.get('dietary_restrictions'):
                        print(f"   - Dietary: {', '.join(preview['dietary_restrictions'])}")
                    
                    if data.get('warnings'):
                        print(f"   - Warnings: {len(data['warnings'])}")
                        for warning in data['warnings']:
                            print(f"     • {warning}")
                else:
                    print(f"❌ Import failed: {data.get('error_message', 'Unknown error')}")
                    if data.get('validation_issues'):
                        for issue in data['validation_issues']:
                            print(f"     • {issue}")
                
                return data
            else:
                print(f"❌ Import failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Import error: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run comprehensive test of recipe import functionality"""
        print("🧪 Starting Recipe URL Import Tests")
        print("=" * 50)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return
        
        print("\n" + "=" * 50)
        print("📋 Testing URL Validation")
        print("=" * 50)
        
        # Test URL validation for each URL
        validation_results = []
        for url in TEST_URLS:
            print(f"\n--- Testing: {url} ---")
            result = self.test_url_validation(url)
            validation_results.append({
                'url': url,
                'result': result,
                'valid': result.get('is_valid', False) if result else False
            })
        
        print("\n" + "=" * 50)
        print("📥 Testing Recipe Import")
        print("=" * 50)
        
        # Test recipe import for valid URLs
        import_results = []
        for validation in validation_results:
            if validation['valid']:
                print(f"\n--- Importing: {validation['url']} ---")
                result = self.test_recipe_import(
                    validation['url'], 
                    custom_tags=["test-import", f"domain-{validation['result']['domain'].replace('.', '-')}"]
                )
                import_results.append({
                    'url': validation['url'],
                    'result': result,
                    'success': result.get('success', False) if result else False
                })
            else:
                print(f"\n⏭️  Skipping invalid URL: {validation['url']}")
        
        # Generate summary report
        print("\n" + "=" * 50)
        print("📊 Test Summary Report")
        print("=" * 50)
        
        total_urls = len(TEST_URLS)
        valid_urls = sum(1 for v in validation_results if v['valid'])
        successful_imports = sum(1 for i in import_results if i['success'])
        
        print(f"Total URLs tested: {total_urls}")
        print(f"Valid URLs: {valid_urls} ({valid_urls/total_urls:.1%})")
        print(f"Successful imports: {successful_imports} ({successful_imports/valid_urls:.1%} of valid)")
        
        print(f"\n📈 Validation Results:")
        for validation in validation_results:
            status = "✅ Valid" if validation['valid'] else "❌ Invalid"
            domain = validation['result']['domain'] if validation['result'] else "Unknown"
            print(f"   {status} - {domain}")
        
        print(f"\n📥 Import Results:")
        for import_result in import_results:
            status = "✅ Success" if import_result['success'] else "❌ Failed"
            url_domain = import_result['url'].split('/')[2]
            print(f"   {status} - {url_domain}")
        
        # Save detailed results
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_urls': total_urls,
                'valid_urls': valid_urls,
                'successful_imports': successful_imports,
                'validation_success_rate': valid_urls / total_urls,
                'import_success_rate': successful_imports / valid_urls if valid_urls > 0 else 0
            },
            'validation_results': validation_results,
            'import_results': import_results
        }
        
        report_filename = f"recipe_import_test_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        print("\n🎉 Recipe URL Import Testing Complete!")

def main():
    """Main test function"""
    tester = RecipeImportTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()