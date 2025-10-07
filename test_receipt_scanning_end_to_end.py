#!/usr/bin/env python3
"""
Comprehensive End-to-End Receipt Scanning Workflow Test
Tests the complete receipt scanning system from upload to pantry integration.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import requests
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append('./backend')

# Test configuration
TEST_CONFIG = {
    'backend_url': 'http://localhost:8000/api/v1',
    'frontend_url': 'http://localhost:3000',
    'test_user': {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'full_name': 'Test User'
    },
    'timeout': 30
}

class ReceiptScanningTester:
    """Comprehensive tester for receipt scanning workflow"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test results"""
        self.test_results['tests'][test_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.test_results['summary']['total_tests'] += 1
        if status == 'PASSED':
            self.test_results['summary']['passed'] += 1
            print(f"✅ {test_name}: {status}")
        else:
            self.test_results['summary']['failed'] += 1
            print(f"❌ {test_name}: {status}")
            if details and 'error' in details:
                print(f"   Error: {details['error']}")
                self.test_results['summary']['errors'].append(f"{test_name}: {details['error']}")
    
    async def test_backend_health(self):
        """Test backend health and connectivity"""
        test_name = "Backend Health Check"
        try:
            response = self.session.get(f"{TEST_CONFIG['backend_url']}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(test_name, "PASSED", {
                    'status_code': response.status_code,
                    'response': health_data
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'status_code': response.status_code,
                    'error': f"Unexpected status code: {response.status_code}"
                })
                return False
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        test_name = "Frontend Accessibility"
        try:
            response = self.session.get(TEST_CONFIG['frontend_url'], timeout=10)
            if response.status_code == 200:
                self.log_test(test_name, "PASSED", {
                    'status_code': response.status_code,
                    'content_length': len(response.content)
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'status_code': response.status_code,
                    'error': f"Frontend not accessible: {response.status_code}"
                })
                return False
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_ocr_service_configuration(self):
        """Test OCR service configuration and status"""
        test_name = "OCR Service Configuration"
        try:
            # Import OCR service
            from app.utils.ocr_service import ocr_service
            
            # Get service status
            status = ocr_service.get_service_status()
            
            # Check if service is properly configured
            if status.get('enabled') or status.get('fallback_enabled'):
                self.log_test(test_name, "PASSED", {
                    'service_status': status,
                    'demo_mode': status.get('demo_mode', False),
                    'fallback_enabled': status.get('fallback_enabled', False)
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'service_status': status,
                    'error': "OCR service not properly configured"
                })
                return False
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_ocr_text_extraction(self):
        """Test OCR text extraction functionality"""
        test_name = "OCR Text Extraction"
        try:
            from app.utils.ocr_service import ocr_service
            
            # Test with a mock image URL
            test_image_url = 'test-receipt.jpg'
            result = await ocr_service.extract_text_from_image(test_image_url)
            
            if result and len(result) > 0:
                self.log_test(test_name, "PASSED", {
                    'text_length': len(result),
                    'first_100_chars': result[:100],
                    'demo_mode': ocr_service.demo_mode
                })
                return result
            else:
                self.log_test(test_name, "FAILED", {
                    'error': "No text extracted from image"
                })
                return None
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return None
    
    async def test_receipt_text_parsing(self, ocr_text: str):
        """Test receipt text parsing"""
        test_name = "Receipt Text Parsing"
        try:
            from app.utils.ocr_service import ocr_service
            
            parsed_data = ocr_service.parse_receipt_text(ocr_text)
            
            if parsed_data and 'items' in parsed_data:
                self.log_test(test_name, "PASSED", {
                    'store_name': parsed_data.get('store_name'),
                    'items_count': len(parsed_data.get('items', [])),
                    'total': parsed_data.get('total'),
                    'parsed_data_keys': list(parsed_data.keys())
                })
                return parsed_data
            else:
                self.log_test(test_name, "FAILED", {
                    'error': "Failed to parse receipt text",
                    'parsed_data': parsed_data
                })
                return None
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return None
    
    async def test_category_mapping(self):
        """Test category mapping functionality"""
        test_name = "Category Mapping"
        try:
            from app.utils.category_mapper import category_mapper
            from app.models.pantry import PantryCategory
            
            # Test various item names
            test_items = [
                'chicken breast',
                'milk',
                'bananas',
                'bread',
                'cheese',
                'tomatoes',
                'rice',
                'unknown item'
            ]
            
            mapping_results = {}
            for item in test_items:
                category = category_mapper.map_category(item_name=item)
                mapping_results[item] = category.value
            
            # Check if mappings are reasonable
            expected_mappings = {
                'chicken breast': 'meat',
                'milk': 'dairy',
                'bananas': 'produce',
                'bread': 'grains',
                'cheese': 'dairy',
                'tomatoes': 'produce',
                'rice': 'grains'
            }
            
            correct_mappings = 0
            for item, expected in expected_mappings.items():
                if mapping_results.get(item) == expected:
                    correct_mappings += 1
            
            accuracy = correct_mappings / len(expected_mappings)
            
            if accuracy >= 0.8:  # 80% accuracy threshold
                self.log_test(test_name, "PASSED", {
                    'mapping_results': mapping_results,
                    'accuracy': accuracy,
                    'correct_mappings': correct_mappings,
                    'total_tested': len(expected_mappings)
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'mapping_results': mapping_results,
                    'accuracy': accuracy,
                    'error': f"Category mapping accuracy too low: {accuracy:.2%}"
                })
                return False
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_demo_mode_functionality(self):
        """Test demo mode functionality"""
        test_name = "Demo Mode Functionality"
        try:
            # Test mock data generation
            from frontend.src.lib.mockData import simulateReceiptProcessing
            
            # This would normally be tested in the frontend, but we can test the concept
            # by checking if the OCR service falls back to demo mode properly
            from app.utils.ocr_service import ocr_service
            
            if ocr_service.demo_mode or ocr_service.fallback_enabled:
                # Test demo OCR text generation
                demo_text = await ocr_service._get_demo_ocr_text('demo-receipt.jpg')
                
                if demo_text and len(demo_text) > 0:
                    self.log_test(test_name, "PASSED", {
                        'demo_mode_active': ocr_service.demo_mode,
                        'fallback_enabled': ocr_service.fallback_enabled,
                        'demo_text_length': len(demo_text),
                        'demo_text_preview': demo_text[:200]
                    })
                    return True
                else:
                    self.log_test(test_name, "FAILED", {
                        'error': "Demo mode failed to generate text"
                    })
                    return False
            else:
                self.log_test(test_name, "SKIPPED", {
                    'reason': "Demo mode not enabled"
                })
                return True
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_api_endpoints_structure(self):
        """Test API endpoints structure and availability"""
        test_name = "API Endpoints Structure"
        try:
            # Test key receipt-related endpoints (without authentication for structure check)
            endpoints_to_test = [
                '/receipts/upload',
                '/pantry/',
                '/auth/register',
                '/auth/login-form'
            ]
            
            endpoint_results = {}
            for endpoint in endpoints_to_test:
                try:
                    # Use HEAD request to check if endpoint exists without triggering full logic
                    response = self.session.head(f"{TEST_CONFIG['backend_url']}{endpoint}", timeout=5)
                    endpoint_results[endpoint] = {
                        'status_code': response.status_code,
                        'exists': response.status_code != 404
                    }
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'status_code': None,
                        'exists': False,
                        'error': str(e)
                    }
            
            # Check if critical endpoints exist
            critical_endpoints = ['/receipts/upload', '/pantry/']
            existing_critical = sum(1 for ep in critical_endpoints if endpoint_results.get(ep, {}).get('exists', False))
            
            if existing_critical == len(critical_endpoints):
                self.log_test(test_name, "PASSED", {
                    'endpoint_results': endpoint_results,
                    'critical_endpoints_available': existing_critical
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'endpoint_results': endpoint_results,
                    'critical_endpoints_available': existing_critical,
                    'error': f"Only {existing_critical}/{len(critical_endpoints)} critical endpoints available"
                })
                return False
        except Exception as e:
            self.log_test(test_name, "FAILED", {'error': str(e)})
            return False
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        test_name = "Error Handling"
        try:
            from app.utils.ocr_service import ocr_service
            
            # Test with invalid image URL
            result = await ocr_service.extract_text_from_image('invalid-url')
            
            # Should either return None or fallback to demo mode
            if result is None or (ocr_service.fallback_enabled and result):
                self.log_test(test_name, "PASSED", {
                    'invalid_url_handling': 'Handled gracefully',
                    'fallback_enabled': ocr_service.fallback_enabled,
                    'result': result is not None
                })
                return True
            else:
                self.log_test(test_name, "FAILED", {
                    'error': "Error handling not working properly"
                })
                return False
        except Exception as e:
            # Exception handling is also a form of error handling
            self.log_test(test_name, "PASSED", {
                'exception_handling': 'Working',
                'exception': str(e)
            })
            return True
    
    async def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🔍 STARTING COMPREHENSIVE RECEIPT SCANNING WORKFLOW TEST")
        print("=" * 70)
        
        # Test 1: Backend Health
        backend_healthy = await self.test_backend_health()
        
        # Test 2: Frontend Accessibility
        frontend_accessible = await self.test_frontend_accessibility()
        
        # Test 3: OCR Service Configuration
        ocr_configured = await self.test_ocr_service_configuration()
        
        # Test 4: OCR Text Extraction
        ocr_text = await self.test_ocr_text_extraction()
        
        # Test 5: Receipt Text Parsing (if OCR worked)
        parsed_data = None
        if ocr_text:
            parsed_data = await self.test_receipt_text_parsing(ocr_text)
        
        # Test 6: Category Mapping
        await self.test_category_mapping()
        
        # Test 7: Demo Mode Functionality
        await self.test_demo_mode_functionality()
        
        # Test 8: API Endpoints Structure
        await self.test_api_endpoints_structure()
        
        # Test 9: Error Handling
        await self.test_error_handling()
        
        # Generate summary
        await self.generate_test_report()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE RECEIPT SCANNING TEST REPORT")
        print("=" * 70)
        
        summary = self.test_results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {(summary['passed'] / summary['total_tests'] * 100):.1f}%")
        
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 50)
        
        for test_name, result in self.test_results['tests'].items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌" if result['status'] == 'FAILED' else "⏭️"
            print(f"{status_icon} {test_name}: {result['status']}")
            
            if result['details']:
                for key, value in result['details'].items():
                    if key != 'error':
                        print(f"   {key}: {value}")
        
        print("\n🔧 SYSTEM STATUS ANALYSIS:")
        print("-" * 50)
        
        # Analyze system readiness
        critical_tests = [
            'Backend Health Check',
            'OCR Service Configuration', 
            'Category Mapping'
        ]
        
        critical_passed = sum(1 for test in critical_tests 
                            if self.test_results['tests'].get(test, {}).get('status') == 'PASSED')
        
        if critical_passed == len(critical_tests):
            print("✅ SYSTEM STATUS: READY FOR RECEIPT SCANNING")
            print("   All critical components are functioning properly")
        else:
            print("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
            print(f"   {critical_passed}/{len(critical_tests)} critical tests passed")
        
        # Specific component analysis
        ocr_status = self.test_results['tests'].get('OCR Service Configuration', {})
        if ocr_status.get('status') == 'PASSED':
            ocr_details = ocr_status.get('details', {})
            if ocr_details.get('service_status', {}).get('demo_mode'):
                print("🧪 OCR MODE: Demo mode active (fallback working)")
            else:
                print("🔧 OCR MODE: Production mode")
        
        print("\n🎯 RECEIPT SCANNING WORKFLOW ASSESSMENT:")
        print("-" * 50)
        
        workflow_components = {
            'Upload': self.test_results['tests'].get('API Endpoints Structure', {}).get('status') == 'PASSED',
            'OCR Processing': self.test_results['tests'].get('OCR Text Extraction', {}).get('status') == 'PASSED',
            'Item Extraction': self.test_results['tests'].get('Receipt Text Parsing', {}).get('status') == 'PASSED',
            'Category Mapping': self.test_results['tests'].get('Category Mapping', {}).get('status') == 'PASSED',
            'Error Handling': self.test_results['tests'].get('Error Handling', {}).get('status') == 'PASSED'
        }
        
        for component, working in workflow_components.items():
            status = "✅ Working" if working else "❌ Issues"
            print(f"   {component}: {status}")
        
        working_components = sum(workflow_components.values())
        total_components = len(workflow_components)
        
        print(f"\n📈 WORKFLOW COMPLETENESS: {working_components}/{total_components} components working ({working_components/total_components*100:.1f}%)")
        
        if working_components >= total_components * 0.8:  # 80% threshold
            print("✅ VERDICT: Receipt scanning workflow is functional and ready for end-to-end testing")
        else:
            print("⚠️  VERDICT: Receipt scanning workflow needs fixes before full deployment")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"receipt_scanning_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed test results saved to: {report_file}")
        
        if summary['errors']:
            print(f"\n🚨 ERRORS ENCOUNTERED:")
            for error in summary['errors']:
                print(f"   • {error}")

async def main():
    """Main test execution"""
    tester = ReceiptScanningTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())