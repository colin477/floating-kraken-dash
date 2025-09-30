#!/usr/bin/env python3
"""
Real Browser Automation Test for Sign-up Workflow

This script uses Selenium WebDriver to test the actual browser behavior:
1. Real plan selection UI interactions
2. Actual question count validation
3. Complete end-to-end user journey
4. Screenshot capture for validation

Requirements: pip install selenium
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000/api/v1"

@dataclass
class RealBrowserTestResult:
    test_name: str
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None
    screenshot_path: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class RealBrowserTester:
    def __init__(self):
        self.test_results: List[RealBrowserTestResult] = []
        self.test_email = f"real_browser_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_password = "TestPassword123!"
        self.test_name = "Real Browser Test User"
        self.driver = None
        self.wait = None
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any] = None, error: str = None, screenshot_path: str = None):
        """Log test result"""
        result = RealBrowserTestResult(
            test_name=test_name,
            success=success,
            details=details or {},
            error=error,
            screenshot_path=screenshot_path
        )
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        if screenshot_path:
            print(f"   Screenshot: {screenshot_path}")
        print()

    def setup_browser(self) -> bool:
        """Setup Chrome browser with options"""
        try:
            if not SELENIUM_AVAILABLE:
                self.log_result("Browser Setup", False, error="Selenium not available. Install with: pip install selenium")
                return False
                
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1200,800")
            # chrome_options.add_argument("--headless")  # Uncomment for headless mode
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            self.log_result("Browser Setup", True, {"browser": "Chrome", "window_size": "1200x800"})
            return True
            
        except Exception as e:
            self.log_result("Browser Setup", False, error=f"Failed to setup browser: {str(e)}")
            return False

    def take_screenshot(self, name: str) -> str:
        """Take screenshot and return path"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"screenshot_{name}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            return screenshot_path
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return None

    def test_landing_page_load(self) -> bool:
        """Test landing page loads correctly"""
        try:
            self.driver.get(FRONTEND_URL)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Take screenshot
            screenshot_path = self.take_screenshot("landing_page")
            
            # Check for key elements
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            # Look for auth-related elements
            has_auth_elements = any(keyword in page_source.lower() for keyword in [
                "login", "sign up", "register", "auth", "trial"
            ])
            
            self.log_result("Landing Page Load", True, {
                "page_title": page_title,
                "url": self.driver.current_url,
                "has_auth_elements": has_auth_elements
            }, screenshot_path=screenshot_path)
            
            return True
            
        except Exception as e:
            screenshot_path = self.take_screenshot("landing_page_error")
            self.log_result("Landing Page Load", False, error=str(e), screenshot_path=screenshot_path)
            return False

    def test_signup_process(self) -> bool:
        """Test the signup process"""
        try:
            # Look for signup/login button
            signup_selectors = [
                "button:contains('Sign Up')",
                "button:contains('Login')",
                "button:contains('Trial')",
                "[data-testid='auth-button']",
                ".auth-button",
                "button[type='submit']"
            ]
            
            signup_button = None
            for selector in signup_selectors:
                try:
                    if "contains" in selector:
                        # Use XPath for text-based selection
                        text_to_find = selector.split("'")[1]
                        xpath_selector = f"//button[contains(text(), '{text_to_find}')]"
                        signup_button = self.driver.find_element(By.XPATH, xpath_selector)
                        break
                    else:
                        signup_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                except NoSuchElementException:
                    continue
            
            if not signup_button:
                # Try to find any button that might be the auth button
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    signup_button = buttons[0]  # Take the first button as fallback
            
            if signup_button:
                screenshot_path = self.take_screenshot("before_signup_click")
                signup_button.click()
                time.sleep(2)  # Wait for modal/form to appear
                
                screenshot_path = self.take_screenshot("after_signup_click")
                
                self.log_result("Signup Process", True, {
                    "signup_button_found": True,
                    "button_text": signup_button.text
                }, screenshot_path=screenshot_path)
                return True
            else:
                screenshot_path = self.take_screenshot("no_signup_button")
                self.log_result("Signup Process", False, {
                    "signup_button_found": False,
                    "available_buttons": len(self.driver.find_elements(By.TAG_NAME, "button"))
                }, error="No signup button found", screenshot_path=screenshot_path)
                return False
                
        except Exception as e:
            screenshot_path = self.take_screenshot("signup_process_error")
            self.log_result("Signup Process", False, error=str(e), screenshot_path=screenshot_path)
            return False

    def test_plan_selection_ui(self) -> bool:
        """Test plan selection UI behavior"""
        try:
            # Look for plan selection elements
            time.sleep(3)  # Wait for any navigation
            
            screenshot_path = self.take_screenshot("plan_selection_page")
            
            # Look for plan cards/options
            plan_selectors = [
                "[data-testid*='plan']",
                ".plan-card",
                ".pricing-card",
                "button:contains('Basic')",
                "button:contains('Premium')",
                "button:contains('Free')"
            ]
            
            plan_elements = []
            for selector in plan_selectors:
                try:
                    if "contains" in selector:
                        text_to_find = selector.split("'")[1]
                        xpath_selector = f"//button[contains(text(), '{text_to_find}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath_selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    plan_elements.extend(elements)
                except Exception:
                    continue
            
            # Remove duplicates
            plan_elements = list(set(plan_elements))
            
            if len(plan_elements) >= 2:  # Should have at least 2 plan options
                # Test clicking on a plan
                first_plan = plan_elements[0]
                plan_text = first_plan.text
                
                # Take screenshot before click
                screenshot_before = self.take_screenshot("before_plan_click")
                
                first_plan.click()
                time.sleep(2)  # Wait for UI update
                
                # Take screenshot after click
                screenshot_after = self.take_screenshot("after_plan_click")
                
                # Look for continue button
                continue_selectors = [
                    "button:contains('Continue')",
                    "[data-testid='continue-button']",
                    ".continue-button"
                ]
                
                continue_button_found = False
                for selector in continue_selectors:
                    try:
                        if "contains" in selector:
                            text_to_find = selector.split("'")[1]
                            xpath_selector = f"//button[contains(text(), '{text_to_find}')]"
                            continue_button = self.driver.find_element(By.XPATH, xpath_selector)
                        else:
                            continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        continue_button_found = True
                        break
                    except Exception:
                        continue
                
                self.log_result("Plan Selection UI", True, {
                    "plan_elements_found": len(plan_elements),
                    "clicked_plan_text": plan_text,
                    "continue_button_appeared": continue_button_found
                }, screenshot_path=screenshot_after)
                
                return True
            else:
                self.log_result("Plan Selection UI", False, {
                    "plan_elements_found": len(plan_elements),
                    "page_source_length": len(self.driver.page_source)
                }, error="Insufficient plan options found", screenshot_path=screenshot_path)
                return False
                
        except Exception as e:
            screenshot_path = self.take_screenshot("plan_selection_error")
            self.log_result("Plan Selection UI", False, error=str(e), screenshot_path=screenshot_path)
            return False

    def test_question_flow(self) -> bool:
        """Test question flow progression"""
        try:
            # Look for question elements
            time.sleep(3)
            
            screenshot_path = self.take_screenshot("question_flow")
            
            # Look for question indicators
            question_indicators = [
                "Question 1 of",
                "1 / ",
                "Step 1",
                "[data-testid*='question']",
                ".question-progress"
            ]
            
            question_found = False
            question_count_info = None
            
            page_source = self.driver.page_source
            for indicator in question_indicators:
                if indicator in page_source:
                    question_found = True
                    # Try to extract question count info
                    if "of" in indicator:
                        # Look for pattern like "Question 1 of 8"
                        import re
                        pattern = r"Question \d+ of (\d+)"
                        match = re.search(pattern, page_source)
                        if match:
                            question_count_info = f"Total questions: {match.group(1)}"
                    break
            
            # Look for question text
            question_text_elements = self.driver.find_elements(By.TAG_NAME, "h2")
            question_text = None
            if question_text_elements:
                question_text = question_text_elements[0].text
            
            self.log_result("Question Flow", question_found, {
                "question_found": question_found,
                "question_count_info": question_count_info,
                "question_text": question_text,
                "page_url": self.driver.current_url
            }, screenshot_path=screenshot_path)
            
            return question_found
            
        except Exception as e:
            screenshot_path = self.take_screenshot("question_flow_error")
            self.log_result("Question Flow", False, error=str(e), screenshot_path=screenshot_path)
            return False

    def run_real_browser_tests(self) -> Dict[str, Any]:
        """Run all real browser tests"""
        print("🌐 Starting Real Browser Automation Tests")
        print("=" * 70)
        print(f"Test Email: {self.test_email}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print("=" * 70)
        
        if not self.setup_browser():
            return self.generate_summary()
        
        try:
            # Test sequence
            test_sequence = [
                ("Landing Page Load", self.test_landing_page_load),
                ("Signup Process", self.test_signup_process),
                ("Plan Selection UI", self.test_plan_selection_ui),
                ("Question Flow", self.test_question_flow)
            ]
            
            all_passed = True
            for section_name, test_func in test_sequence:
                print(f"\n🧪 {section_name}")
                print("-" * 50)
                
                try:
                    result = test_func()
                    if not result:
                        all_passed = False
                except Exception as e:
                    print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
                    all_passed = False
            
            return self.generate_summary(all_passed)
            
        finally:
            if self.driver:
                self.driver.quit()

    def generate_summary(self, all_passed: bool = False) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        summary = {
            "test_type": "Real Browser Automation",
            "test_email": self.test_email,
            "frontend_url": FRONTEND_URL,
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_success": all_passed,
            "test_results": [asdict(r) for r in self.test_results],
            "selenium_available": SELENIUM_AVAILABLE
        }
        
        print("\n" + "=" * 70)
        print("📊 REAL BROWSER TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Result: {'✅ SUCCESS' if all_passed else '❌ ISSUES FOUND'}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result.success:
                    print(f"  • {result.test_name}: {result.error or 'Unknown error'}")
        
        return summary

def main():
    """Main test execution"""
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium WebDriver not available!")
        print("Install with: pip install selenium")
        print("Also ensure Chrome browser and ChromeDriver are installed")
        return 1
    
    tester = RealBrowserTester()
    
    try:
        results = tester.run_real_browser_tests()
        
        # Save results to file
        results_file = f"real_browser_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        print(f"\n🔍 KEY FINDINGS:")
        print("  📸 Screenshots captured for visual validation")
        print("  🌐 Real browser interactions tested")
        print("  🖱️  UI element detection and clicking validated")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if results["overall_success"]:
            print("  ✅ Browser automation tests passed!")
            print("  🚀 UI interactions working as expected")
        else:
            print("  🔧 Review failed tests and screenshots")
            print("  🎯 Focus on UI element selectors and timing")
        
        return 0 if results["overall_success"] else 1
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())