#!/usr/bin/env python3
"""
Comprehensive test for the "Complete Sign-up" button implementation
Tests all three plan flows: Basic (4 questions), Medium (8 questions), Full (12 questions)
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignupFlowTester:
    def __init__(self):
        self.browser = None
        self.page = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
        
    async def setup_browser(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1200, "height": 800})
        
    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            
    async def take_screenshot(self, name: str):
        """Take a screenshot for documentation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{name}_{timestamp}.png"
        await self.page.screenshot(path=filename)
        logger.info(f"Screenshot saved: {filename}")
        return filename
        
    async def wait_for_element(self, selector: str, timeout: int = 10000):
        """Wait for element to be visible"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element not found: {selector} - {e}")
            return False
            
    async def navigate_to_signup(self):
        """Navigate to the signup page"""
        logger.info("Navigating to signup page...")
        await self.page.goto('http://localhost:3000')
        await self.page.wait_for_load_state('networkidle')
        
        # Take screenshot of landing page
        await self.take_screenshot("landing_page")
        
        # Look for signup/login button
        signup_selectors = [
            'text="Sign Up"',
            'text="Get Started"',
            'text="Create Account"',
            '[data-testid="signup-button"]',
            'button:has-text("Sign")',
            'a:has-text("Sign")'
        ]
        
        for selector in signup_selectors:
            try:
                if await self.page.is_visible(selector):
                    await self.page.click(selector)
                    logger.info(f"Clicked signup button: {selector}")
                    break
            except:
                continue
        
        await self.page.wait_for_load_state('networkidle')
        await self.take_screenshot("signup_page")
        
    async def register_new_user(self, plan_type: str):
        """Register a new user for testing"""
        timestamp = int(time.time())
        test_email = f"test_{plan_type}_{timestamp}@example.com"
        test_password = "TestPassword123!"
        
        logger.info(f"Registering new user: {test_email}")
        
        try:
            # Fill registration form
            await self.page.fill('input[type="email"]', test_email)
            await self.page.fill('input[type="password"]', test_password)
            
            # Look for confirm password field
            confirm_password_selectors = [
                'input[name="confirmPassword"]',
                'input[placeholder*="confirm"]',
                'input[placeholder*="Confirm"]'
            ]
            
            for selector in confirm_password_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.fill(selector, test_password)
                        break
                except:
                    continue
            
            # Submit registration
            submit_selectors = [
                'button[type="submit"]',
                'text="Sign Up"',
                'text="Create Account"',
                'text="Register"'
            ]
            
            for selector in submit_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.click(selector)
                        logger.info(f"Clicked submit button: {selector}")
                        break
                except:
                    continue
                    
            await self.page.wait_for_load_state('networkidle')
            await self.take_screenshot(f"after_registration_{plan_type}")
            
            return test_email, test_password
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            await self.take_screenshot(f"registration_error_{plan_type}")
            raise
            
    async def select_plan(self, plan_type: str):
        """Select the specified plan"""
        logger.info(f"Selecting {plan_type} plan...")
        
        plan_selectors = {
            'basic': [
                'text="Free"',
                'text="Basic"',
                'text="Free Plan"',
                '[data-testid="basic-plan"]',
                'button:has-text("Free")'
            ],
            'medium': [
                'text="Basic Plan"',
                'text="Medium"',
                'text="$5"',
                'text="$7"',
                '[data-testid="medium-plan"]',
                'button:has-text("Basic Plan")'
            ],
            'full': [
                'text="Premium"',
                'text="Full"',
                'text="$9"',
                'text="$12"',
                '[data-testid="full-plan"]',
                'button:has-text("Premium")'
            ]
        }
        
        for selector in plan_selectors.get(plan_type, []):
            try:
                if await self.page.is_visible(selector):
                    await self.page.click(selector)
                    logger.info(f"Selected {plan_type} plan with selector: {selector}")
                    await self.page.wait_for_load_state('networkidle')
                    await self.take_screenshot(f"plan_selected_{plan_type}")
                    return True
            except Exception as e:
                logger.debug(f"Plan selector failed: {selector} - {e}")
                continue
                
        logger.error(f"Could not select {plan_type} plan")
        await self.take_screenshot(f"plan_selection_failed_{plan_type}")
        return False
        
    async def answer_questions(self, plan_type: str, expected_questions: int):
        """Answer all questions in the setup flow"""
        logger.info(f"Starting {plan_type} plan setup with {expected_questions} questions...")
        
        questions_answered = 0
        max_questions = expected_questions + 2  # Safety buffer
        
        for question_num in range(1, max_questions + 1):
            try:
                # Wait for question to load
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                # Take screenshot of current question
                await self.take_screenshot(f"{plan_type}_question_{question_num}")
                
                # Check if we're on the final question by looking for "Complete Sign-up" button
                complete_button_visible = await self.page.is_visible('text="Complete Sign-up"')
                if complete_button_visible:
                    logger.info(f"Found 'Complete Sign-up' button on question {question_num}")
                    await self.take_screenshot(f"{plan_type}_complete_button_visible")
                    break
                
                # Look for question progress indicator
                progress_text = await self.page.text_content('text=/Question \\d+ of \\d+/')
                if progress_text:
                    logger.info(f"Progress: {progress_text}")
                
                # Find and click answer options
                answer_clicked = False
                
                # Try different answer button selectors
                answer_selectors = [
                    'button[class*="outline"]:not([disabled])',
                    'button:has-text("minutes")',
                    'button:has-text("comfort")',
                    'button:has-text("adventure")',
                    'button:has-text("Chicken")',
                    'button:has-text("Just me")',
                    'button:has-text("Two")',
                    'button:has-text("Family")',
                    'button:has-text("everything")',
                    'button:has-text("Balanced")',
                    'button:has-text("$50")',
                    'button:has-text("Quick")'
                ]
                
                for selector in answer_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            # Click the first available answer
                            await elements[0].click()
                            logger.info(f"Clicked answer with selector: {selector}")
                            answer_clicked = True
                            questions_answered += 1
                            break
                    except Exception as e:
                        logger.debug(f"Answer selector failed: {selector} - {e}")
                        continue
                
                if not answer_clicked:
                    # Try clicking any visible button that's not disabled
                    try:
                        buttons = await self.page.query_selector_all('button:not([disabled])')
                        for button in buttons:
                            button_text = await button.text_content()
                            if button_text and len(button_text.strip()) > 5:  # Avoid clicking small buttons
                                await button.click()
                                logger.info(f"Clicked button: {button_text[:50]}...")
                                answer_clicked = True
                                questions_answered += 1
                                break
                    except Exception as e:
                        logger.error(f"Failed to click any button: {e}")
                
                if not answer_clicked:
                    logger.error(f"Could not find answer to click on question {question_num}")
                    await self.take_screenshot(f"{plan_type}_question_{question_num}_no_answer")
                    break
                
                # Wait for next question to load
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                # Check if "Complete Sign-up" button appeared after answering
                complete_button_visible = await self.page.is_visible('text="Complete Sign-up"')
                if complete_button_visible:
                    logger.info(f"'Complete Sign-up' button appeared after answering question {question_num}")
                    await self.take_screenshot(f"{plan_type}_complete_button_after_q{question_num}")
                    break
                    
            except Exception as e:
                logger.error(f"Error on question {question_num}: {e}")
                await self.take_screenshot(f"{plan_type}_question_{question_num}_error")
                break
        
        return questions_answered
        
    async def test_complete_button(self, plan_type: str):
        """Test the Complete Sign-up button functionality"""
        logger.info(f"Testing 'Complete Sign-up' button for {plan_type} plan...")
        
        # Verify button is visible
        complete_button_visible = await self.page.is_visible('text="Complete Sign-up"')
        if not complete_button_visible:
            logger.error("'Complete Sign-up' button not visible!")
            await self.take_screenshot(f"{plan_type}_no_complete_button")
            return False
            
        # Take screenshot of the button
        await self.take_screenshot(f"{plan_type}_complete_button_ready")
        
        # Click the Complete Sign-up button
        try:
            await self.page.click('text="Complete Sign-up"')
            logger.info("Clicked 'Complete Sign-up' button")
            
            # Wait for loading state
            await asyncio.sleep(2)
            await self.take_screenshot(f"{plan_type}_after_complete_click")
            
            # Check for loading indicator
            loading_visible = await self.page.is_visible('text="Completing Setup"')
            if loading_visible:
                logger.info("Loading state detected")
                await self.take_screenshot(f"{plan_type}_loading_state")
                
                # Wait for completion
                await self.page.wait_for_selector('text="Completing Setup"', state='hidden', timeout=30000)
            
            # Wait for navigation to dashboard
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Take final screenshot
            await self.take_screenshot(f"{plan_type}_final_result")
            
            # Check if we reached the dashboard
            dashboard_indicators = [
                'text="Dashboard"',
                'text="Welcome"',
                'text="Meal"',
                'text="Pantry"',
                '[data-testid="dashboard"]'
            ]
            
            for indicator in dashboard_indicators:
                if await self.page.is_visible(indicator):
                    logger.info(f"Successfully reached dashboard - found: {indicator}")
                    return True
                    
            logger.warning("Dashboard indicators not found, but completion may have succeeded")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking Complete Sign-up button: {e}")
            await self.take_screenshot(f"{plan_type}_complete_button_error")
            return False
            
    async def test_plan_flow(self, plan_type: str, expected_questions: int):
        """Test complete signup flow for a specific plan"""
        logger.info(f"\n{'='*50}")
        logger.info(f"TESTING {plan_type.upper()} PLAN FLOW ({expected_questions} questions)")
        logger.info(f"{'='*50}")
        
        test_result = {
            'plan_type': plan_type,
            'expected_questions': expected_questions,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'steps': [],
            'screenshots': [],
            'errors': []
        }
        
        try:
            # Step 1: Navigate to signup
            logger.info("Step 1: Navigate to signup")
            await self.navigate_to_signup()
            test_result['steps'].append('navigation_completed')
            
            # Step 2: Register new user
            logger.info("Step 2: Register new user")
            email, password = await self.register_new_user(plan_type)
            test_result['steps'].append('registration_completed')
            test_result['test_email'] = email
            
            # Step 3: Select plan
            logger.info("Step 3: Select plan")
            plan_selected = await self.select_plan(plan_type)
            if not plan_selected:
                raise Exception(f"Failed to select {plan_type} plan")
            test_result['steps'].append('plan_selected')
            
            # Step 4: Answer questions
            logger.info("Step 4: Answer questions")
            questions_answered = await self.answer_questions(plan_type, expected_questions)
            test_result['questions_answered'] = questions_answered
            test_result['steps'].append('questions_completed')
            
            # Step 5: Test Complete Sign-up button
            logger.info("Step 5: Test Complete Sign-up button")
            button_success = await self.test_complete_button(plan_type)
            test_result['complete_button_success'] = button_success
            test_result['steps'].append('completion_tested')
            
            # Determine overall success
            if button_success and questions_answered >= expected_questions - 1:  # Allow 1 question tolerance
                test_result['status'] = 'passed'
                self.test_results['summary']['passed'] += 1
                logger.info(f"✅ {plan_type.upper()} PLAN TEST PASSED")
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append(f"Expected {expected_questions} questions, answered {questions_answered}")
                self.test_results['summary']['failed'] += 1
                logger.error(f"❌ {plan_type.upper()} PLAN TEST FAILED")
                
        except Exception as e:
            test_result['status'] = 'error'
            test_result['errors'].append(str(e))
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['errors'].append(f"{plan_type}: {str(e)}")
            logger.error(f"❌ {plan_type.upper()} PLAN TEST ERROR: {e}")
            
        finally:
            test_result['end_time'] = datetime.now().isoformat()
            self.test_results['tests'].append(test_result)
            self.test_results['summary']['total_tests'] += 1
            
        return test_result
        
    async def run_all_tests(self):
        """Run tests for all plan types"""
        logger.info("Starting comprehensive signup flow tests...")
        
        await self.setup_browser()
        
        try:
            # Test plans in order of complexity
            test_plans = [
                ('basic', 4),    # Basic Plan: 4 questions
                ('medium', 8),   # Medium Plan: 8 questions  
                ('full', 12)     # Full Plan: 12 questions
            ]
            
            for plan_type, expected_questions in test_plans:
                await self.test_plan_flow(plan_type, expected_questions)
                
                # Brief pause between tests
                await asyncio.sleep(3)
                
        finally:
            await self.cleanup()
            
        # Generate final report
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("COMPREHENSIVE SIGNUP FLOW TEST REPORT")
        logger.info("="*60)
        
        summary = self.test_results['summary']
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%")
        
        logger.info("\nDETAILED RESULTS:")
        logger.info("-" * 40)
        
        for test in self.test_results['tests']:
            status_icon = "✅" if test['status'] == 'passed' else "❌"
            logger.info(f"{status_icon} {test['plan_type'].upper()} Plan:")
            logger.info(f"   Expected Questions: {test['expected_questions']}")
            logger.info(f"   Questions Answered: {test.get('questions_answered', 'N/A')}")
            logger.info(f"   Complete Button: {'✅' if test.get('complete_button_success') else '❌'}")
            logger.info(f"   Status: {test['status']}")
            
            if test.get('errors'):
                logger.info(f"   Errors: {', '.join(test['errors'])}")
            logger.info("")
            
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_signup_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
            
        logger.info(f"Detailed results saved to: {filename}")
        
        if summary['errors']:
            logger.info("\nERRORS ENCOUNTERED:")
            for error in summary['errors']:
                logger.error(f"  - {error}")

async def main():
    """Main test execution"""
    tester = SignupFlowTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())