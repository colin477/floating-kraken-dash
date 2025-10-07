#!/usr/bin/env python3
"""
Comprehensive test to verify the signup flow "Loading your profile..." fix is working correctly.

This test specifically validates:
1. Complete signup flow from registration through onboarding completion
2. Proper transition from final "complete" button to dashboard without hanging
3. No "Loading your profile..." state persistence
4. No browser refresh required for login completion

The fix implemented in Auth.tsx:
- Added onboardingState to useAuth destructuring (line 28)
- Added onboardingState.isOnboardingComplete to useEffect dependency array (line 104)
"""

import asyncio
import json
import time
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class SignupFlowFixVerification:
    def __init__(self):
        self.test_results = {
            'test_name': 'Signup Flow "Loading your profile..." Fix Verification',
            'timestamp': datetime.now().isoformat(),
            'frontend_url': 'http://localhost:5173',
            'backend_url': 'http://localhost:8000',
            'test_phases': {},
            'overall_result': 'PENDING',
            'fix_validation': {
                'code_fix_verified': False,
                'functional_fix_verified': False,
                'no_loading_hang': False,
                'dashboard_accessible': False,
                'no_refresh_required': False
            }
        }
        
    def generate_test_user(self):
        """Generate unique test user credentials"""
        timestamp = str(int(time.time()))
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return {
            'email': f'testuser_{timestamp}_{random_suffix}@example.com',
            'password': 'TestPassword123!',
            'name': f'Test User {timestamp}'
        }

    async def wait_for_element_with_timeout(self, page: Page, selector: str, timeout: int = 10000, state: str = 'visible'):
        """Wait for element with enhanced error handling"""
        try:
            await page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception as e:
            print(f"❌ Element not found: {selector} (timeout: {timeout}ms, state: {state})")
            print(f"   Error: {str(e)}")
            return False

    async def take_screenshot(self, page: Page, name: str):
        """Take screenshot for debugging"""
        try:
            screenshot_path = f"screenshot_{name}_{int(time.time())}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None

    async def verify_code_fix(self):
        """Verify the code fix is in place in Auth.tsx"""
        print('\n🔍 PHASE 1: VERIFYING CODE FIX IN AUTH.TSX')
        print('=' * 60)
        
        try:
            with open('frontend/src/pages/Auth.tsx', 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if onboardingState is destructured from useAuth
            onboarding_state_destructured = 'onboardingState' in content and 'useAuth()' in content
            
            # Check if the dependency array includes onboardingState.isOnboardingComplete
            dependency_array_fixed = 'onboardingState.isOnboardingComplete' in content
            
            # Find the specific line with the dependency array
            lines = content.split('\n')
            dependency_line = None
            for i, line in enumerate(lines):
                if 'onboardingState.isOnboardingComplete' in line and ']);' in line:
                    dependency_line = f"Line {i+1}: {line.strip()}"
                    break
            
            if onboarding_state_destructured and dependency_array_fixed and dependency_line:
                print('✅ onboardingState is destructured from useAuth hook')
                print('✅ onboardingState.isOnboardingComplete is included in dependency array')
                print(f'✅ useEffect dependency array correctly includes the missing dependency')
                print(f'   {dependency_line}')
                
                self.test_results['fix_validation']['code_fix_verified'] = True
                self.test_results['test_phases']['code_verification'] = {
                    'status': 'PASSED',
                    'details': 'Code fix properly implemented in Auth.tsx'
                }
                return True
            else:
                print('❌ Code fix verification failed')
                self.test_results['test_phases']['code_verification'] = {
                    'status': 'FAILED',
                    'details': 'Code fix not properly implemented'
                }
                return False
                
        except Exception as e:
            print(f'❌ Error verifying code fix: {e}')
            self.test_results['test_phases']['code_verification'] = {
                'status': 'ERROR',
                'details': f'Error reading Auth.tsx: {str(e)}'
            }
            return False

    async def test_complete_signup_flow(self, page: Page):
        """Test the complete signup flow from registration to dashboard"""
        print('\n🧪 PHASE 2: TESTING COMPLETE SIGNUP FLOW')
        print('=' * 60)
        
        test_user = self.generate_test_user()
        print(f"📧 Test user: {test_user['email']}")
        
        try:
            # Navigate to the application
            print("🌐 Navigating to application...")
            await page.goto(self.test_results['frontend_url'])
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            await self.take_screenshot(page, "01_initial_load")
            
            # Step 1: Registration
            print("\n📝 Step 1: User Registration")
            
            # Look for signup/register button or form
            signup_selectors = [
                'button:has-text("Sign Up")',
                'button:has-text("Register")',
                'a:has-text("Sign Up")',
                'a:has-text("Register")',
                '[data-testid="signup-button"]',
                '.signup-button'
            ]
            
            signup_found = False
            for selector in signup_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"✅ Found signup element: {selector}")
                    await page.click(selector)
                    signup_found = True
                    break
            
            if not signup_found:
                # Check if we're already on a signup form
                email_input = page.locator('input[type="email"]')
                if await email_input.count() > 0:
                    print("✅ Already on signup form")
                    signup_found = True
            
            if not signup_found:
                print("❌ Could not find signup form or button")
                await self.take_screenshot(page, "02_signup_not_found")
                return False
            
            await page.wait_for_timeout(1000)
            await self.take_screenshot(page, "03_signup_form")
            
            # Fill registration form
            print("📝 Filling registration form...")
            
            # Fill email
            email_selectors = ['input[type="email"]', 'input[name="email"]', '#email']
            for selector in email_selectors:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, test_user['email'])
                    print(f"✅ Filled email: {selector}")
                    break
            
            # Fill password
            password_selectors = ['input[type="password"]', 'input[name="password"]', '#password']
            for selector in password_selectors:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, test_user['password'])
                    print(f"✅ Filled password: {selector}")
                    break
            
            # Fill name if present
            name_selectors = ['input[name="name"]', 'input[name="fullName"]', '#name', '#fullName']
            for selector in name_selectors:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, test_user['name'])
                    print(f"✅ Filled name: {selector}")
                    break
            
            await self.take_screenshot(page, "04_form_filled")
            
            # Submit registration
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign Up")',
                'button:has-text("Register")',
                'button:has-text("Create Account")',
                '.submit-button'
            ]
            
            for selector in submit_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"🚀 Submitting registration: {selector}")
                    await page.click(selector)
                    break
            
            # Wait for registration response
            await page.wait_for_timeout(3000)
            await self.take_screenshot(page, "05_after_registration")
            
            # Step 2: Handle onboarding flow
            print("\n🎯 Step 2: Onboarding Flow")
            
            # Look for onboarding elements
            onboarding_indicators = [
                'text="Welcome"',
                'text="Let\'s get started"',
                'text="Profile Setup"',
                'text="Tell us about yourself"',
                '[data-testid="onboarding"]',
                '.onboarding'
            ]
            
            onboarding_found = False
            for indicator in onboarding_indicators:
                if await page.locator(indicator).count() > 0:
                    print(f"✅ Found onboarding: {indicator}")
                    onboarding_found = True
                    break
            
            if onboarding_found:
                # Navigate through onboarding steps
                max_steps = 10  # Prevent infinite loop
                step_count = 0
                
                while step_count < max_steps:
                    step_count += 1
                    print(f"📋 Onboarding step {step_count}")
                    
                    await self.take_screenshot(page, f"06_onboarding_step_{step_count}")
                    
                    # Look for next/continue/complete buttons
                    next_selectors = [
                        'button:has-text("Next")',
                        'button:has-text("Continue")',
                        'button:has-text("Complete")',
                        'button:has-text("Finish")',
                        'button:has-text("Get Started")',
                        'button[type="submit"]',
                        '.next-button',
                        '.continue-button',
                        '.complete-button'
                    ]
                    
                    button_clicked = False
                    for selector in next_selectors:
                        if await page.locator(selector).count() > 0:
                            button_text = await page.locator(selector).text_content()
                            print(f"🔘 Clicking: {button_text} ({selector})")
                            
                            # Special handling for the final "Complete" button
                            if 'complete' in button_text.lower() or 'finish' in button_text.lower():
                                print("🎯 CRITICAL: Clicking final completion button - monitoring for loading hang...")
                                
                                # Take screenshot before clicking complete
                                await self.take_screenshot(page, "07_before_complete_click")
                                
                                # Click the complete button
                                await page.click(selector)
                                
                                # Monitor for loading states and transitions
                                await self.monitor_post_completion_transition(page)
                                return True
                            else:
                                await page.click(selector)
                                await page.wait_for_timeout(2000)  # Wait for transition
                                button_clicked = True
                                break
                    
                    if not button_clicked:
                        print("⚠️ No next/continue button found, checking if onboarding is complete")
                        break
                
                print("✅ Onboarding flow completed")
            else:
                print("ℹ️ No onboarding flow detected, proceeding to dashboard check")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in signup flow: {e}")
            await self.take_screenshot(page, "error_signup_flow")
            return False

    async def monitor_post_completion_transition(self, page: Page):
        """Monitor the critical transition after clicking the final complete button"""
        print("\n🔍 PHASE 3: MONITORING POST-COMPLETION TRANSITION")
        print('=' * 60)
        
        start_time = time.time()
        max_wait_time = 30  # 30 seconds max wait
        
        # Take screenshot immediately after clicking complete
        await page.wait_for_timeout(1000)
        await self.take_screenshot(page, "08_immediately_after_complete")
        
        loading_detected = False
        loading_hang_detected = False
        dashboard_reached = False
        
        while time.time() - start_time < max_wait_time:
            current_time = time.time() - start_time
            
            # Check for loading states
            loading_selectors = [
                'text="Loading your profile..."',
                'text="Loading..."',
                '.loading',
                '.spinner',
                '[data-testid="loading"]'
            ]
            
            for selector in loading_selectors:
                if await page.locator(selector).count() > 0:
                    if not loading_detected:
                        print(f"⏳ Loading state detected: {selector} (at {current_time:.1f}s)")
                        loading_detected = True
                        await self.take_screenshot(page, f"09_loading_detected_{int(current_time)}")
                    
                    # Check if loading persists too long (indicates hang)
                    if current_time > 10:  # If loading for more than 10 seconds
                        loading_hang_detected = True
                        print(f"❌ LOADING HANG DETECTED: Loading state persisting for {current_time:.1f}s")
                        await self.take_screenshot(page, f"10_loading_hang_{int(current_time)}")
                        break
            
            # Check for dashboard elements
            dashboard_selectors = [
                'text="Dashboard"',
                'text="Welcome"',
                'text="EZ Eatin\'"',
                '[data-testid="dashboard"]',
                '.dashboard',
                'nav',
                '.sidebar'
            ]
            
            for selector in dashboard_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"✅ Dashboard element detected: {selector} (at {current_time:.1f}s)")
                    dashboard_reached = True
                    await self.take_screenshot(page, f"11_dashboard_reached_{int(current_time)}")
                    break
            
            if dashboard_reached and not loading_hang_detected:
                print(f"🎉 SUCCESS: Smooth transition to dashboard in {current_time:.1f}s")
                break
            
            if loading_hang_detected:
                print(f"💥 FAILURE: Loading hang detected, breaking monitoring")
                break
            
            await page.wait_for_timeout(500)  # Check every 500ms
        
        # Final assessment
        transition_time = time.time() - start_time
        
        if loading_hang_detected:
            self.test_results['fix_validation']['no_loading_hang'] = False
            self.test_results['test_phases']['post_completion_transition'] = {
                'status': 'FAILED',
                'details': f'Loading hang detected - loading state persisted for more than 10 seconds',
                'transition_time': transition_time,
                'loading_detected': loading_detected,
                'dashboard_reached': dashboard_reached
            }
            print(f"❌ CRITICAL FAILURE: Loading hang detected")
            return False
        elif dashboard_reached:
            self.test_results['fix_validation']['no_loading_hang'] = True
            self.test_results['fix_validation']['dashboard_accessible'] = True
            self.test_results['fix_validation']['functional_fix_verified'] = True
            self.test_results['test_phases']['post_completion_transition'] = {
                'status': 'PASSED',
                'details': f'Smooth transition to dashboard without loading hang',
                'transition_time': transition_time,
                'loading_detected': loading_detected,
                'dashboard_reached': dashboard_reached
            }
            print(f"✅ SUCCESS: Smooth transition completed in {transition_time:.1f}s")
            return True
        else:
            self.test_results['test_phases']['post_completion_transition'] = {
                'status': 'INCONCLUSIVE',
                'details': f'Neither loading hang nor dashboard clearly detected within {max_wait_time}s',
                'transition_time': transition_time,
                'loading_detected': loading_detected,
                'dashboard_reached': dashboard_reached
            }
            print(f"⚠️ INCONCLUSIVE: Unable to determine final state within {max_wait_time}s")
            return False

    async def test_dashboard_functionality(self, page: Page):
        """Test that dashboard functionality works without requiring refresh"""
        print("\n🎮 PHASE 4: TESTING DASHBOARD FUNCTIONALITY")
        print('=' * 60)
        
        try:
            # Test navigation elements
            nav_elements = [
                'text="Dashboard"',
                'text="Pantry"',
                'text="Recipes"',
                'text="Profile"',
                'nav a',
                '.sidebar a'
            ]
            
            functional_elements_found = 0
            for selector in nav_elements:
                if await page.locator(selector).count() > 0:
                    functional_elements_found += 1
                    print(f"✅ Found functional element: {selector}")
            
            if functional_elements_found >= 2:
                print(f"✅ Dashboard functionality verified ({functional_elements_found} elements found)")
                self.test_results['fix_validation']['dashboard_accessible'] = True
                self.test_results['test_phases']['dashboard_functionality'] = {
                    'status': 'PASSED',
                    'details': f'Dashboard functional with {functional_elements_found} interactive elements'
                }
                return True
            else:
                print(f"❌ Insufficient dashboard functionality ({functional_elements_found} elements found)")
                self.test_results['test_phases']['dashboard_functionality'] = {
                    'status': 'FAILED',
                    'details': f'Only {functional_elements_found} functional elements found'
                }
                return False
                
        except Exception as e:
            print(f"❌ Error testing dashboard functionality: {e}")
            self.test_results['test_phases']['dashboard_functionality'] = {
                'status': 'ERROR',
                'details': f'Error testing functionality: {str(e)}'
            }
            return False

    async def test_no_refresh_required(self, page: Page):
        """Test that no browser refresh is required for proper functionality"""
        print("\n🔄 PHASE 5: TESTING NO REFRESH REQUIRED")
        print('=' * 60)
        
        try:
            # Get current URL and page state
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            # Test that we can interact with elements without refresh
            clickable_elements = [
                'nav a',
                '.sidebar a',
                'button',
                '[role="button"]'
            ]
            
            interaction_successful = False
            for selector in clickable_elements:
                elements = page.locator(selector)
                count = await elements.count()
                
                if count > 0:
                    try:
                        # Try to hover over the first element to test interactivity
                        await elements.first.hover(timeout=2000)
                        print(f"✅ Successfully interacted with: {selector}")
                        interaction_successful = True
                        break
                    except Exception as e:
                        print(f"⚠️ Could not interact with {selector}: {e}")
                        continue
            
            if interaction_successful:
                print("✅ No browser refresh required - elements are interactive")
                self.test_results['fix_validation']['no_refresh_required'] = True
                self.test_results['test_phases']['no_refresh_required'] = {
                    'status': 'PASSED',
                    'details': 'Dashboard elements are interactive without refresh'
                }
                return True
            else:
                print("❌ Elements may not be interactive - refresh might be required")
                self.test_results['test_phases']['no_refresh_required'] = {
                    'status': 'FAILED',
                    'details': 'Could not interact with dashboard elements'
                }
                return False
                
        except Exception as e:
            print(f"❌ Error testing refresh requirement: {e}")
            self.test_results['test_phases']['no_refresh_required'] = {
                'status': 'ERROR',
                'details': f'Error testing refresh requirement: {str(e)}'
            }
            return False

    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        print('🚀 STARTING COMPREHENSIVE SIGNUP FLOW FIX VERIFICATION')
        print('=' * 80)
        
        # Phase 1: Verify code fix
        code_fix_verified = await self.verify_code_fix()
        if not code_fix_verified:
            print("❌ Code fix verification failed - aborting test")
            self.test_results['overall_result'] = 'FAILED'
            return self.test_results
        
        # Phase 2-5: Browser automation tests
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Test complete signup flow
                signup_success = await self.test_complete_signup_flow(page)
                if not signup_success:
                    print("❌ Signup flow test failed")
                    self.test_results['overall_result'] = 'FAILED'
                    return self.test_results
                
                # Test dashboard functionality
                dashboard_success = await self.test_dashboard_functionality(page)
                
                # Test no refresh required
                no_refresh_success = await self.test_no_refresh_required(page)
                
                # Final assessment
                all_tests_passed = all([
                    code_fix_verified,
                    signup_success,
                    dashboard_success,
                    no_refresh_success,
                    self.test_results['fix_validation']['no_loading_hang'],
                    self.test_results['fix_validation']['dashboard_accessible']
                ])
                
                if all_tests_passed:
                    self.test_results['overall_result'] = 'PASSED'
                    print("\n🎉 ALL TESTS PASSED - SIGNUP FLOW FIX VERIFIED!")
                else:
                    self.test_results['overall_result'] = 'PARTIAL'
                    print("\n⚠️ SOME TESTS FAILED - FIX MAY NEED ADDITIONAL WORK")
                
            except Exception as e:
                print(f"❌ Critical error during testing: {e}")
                self.test_results['overall_result'] = 'ERROR'
                self.test_results['error'] = str(e)
                
            finally:
                await browser.close()
        
        return self.test_results

    def generate_report(self):
        """Generate comprehensive test report"""
        report_filename = f"signup_flow_fix_verification_{int(time.time())}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📊 COMPREHENSIVE TEST REPORT")
        print('=' * 80)
        print(f"📁 Report saved to: {report_filename}")
        print(f"🎯 Overall Result: {self.test_results['overall_result']}")
        print(f"⏰ Test Duration: {datetime.now().isoformat()}")
        
        print(f"\n🔧 Fix Validation Summary:")
        for key, value in self.test_results['fix_validation'].items():
            status = "✅ PASS" if value else "❌ FAIL"
            print(f"   {key}: {status}")
        
        print(f"\n📋 Test Phases Summary:")
        for phase, details in self.test_results['test_phases'].items():
            status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥", "INCONCLUSIVE": "⚠️"}.get(details['status'], "❓")
            print(f"   {phase}: {status_icon} {details['status']}")
            if 'details' in details:
                print(f"      {details['details']}")
        
        return report_filename

async def main():
    """Main test execution"""
    tester = SignupFlowFixVerification()
    
    try:
        results = await tester.run_comprehensive_test()
        report_file = tester.generate_report()
        
        print(f"\n🏁 TEST EXECUTION COMPLETED")
        print(f"📊 Results: {results['overall_result']}")
        print(f"📁 Report: {report_file}")
        
        return results['overall_result'] == 'PASSED'
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)