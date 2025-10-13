#!/usr/bin/env python3
"""
Debug script to reproduce and diagnose 422 errors when adding receipt items to pantry
"""

import asyncio
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock the database and models for testing
class MockPantryItemCreate:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.category = kwargs.get('category')
        self.quantity = kwargs.get('quantity')
        self.unit = kwargs.get('unit')
        self.expiration_date = kwargs.get('expiration_date')
        self.purchase_date = kwargs.get('purchase_date')
        self.notes = kwargs.get('notes')
    
    def dict(self):
        return {
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'unit': self.unit,
            'expiration_date': self.expiration_date,
            'purchase_date': self.purchase_date,
            'notes': self.notes
        }

def analyze_422_error_sources():
    """
    Analyze the 5-7 most likely sources of 422 errors based on code examination
    """
    
    print("🔍 ANALYZING POTENTIAL 422 ERROR SOURCES")
    print("=" * 60)
    
    error_sources = [
        {
            "source": "Frontend-Backend Data Format Mismatch",
            "likelihood": "HIGH",
            "description": "Frontend sends receipt items with different field names/types than expected by pantry API",
            "evidence": [
                "Frontend ReceiptScan.tsx maps receipt items to pantry items manually",
                "Receipt items have 'price' field, pantry items don't expect this",
                "Category mapping between receipt and pantry enums may fail"
            ]
        },
        {
            "source": "Pydantic Model Validation Failures",
            "likelihood": "HIGH", 
            "description": "PantryItemCreate model validation fails on required fields or data types",
            "evidence": [
                "PantryItemCreate has strict validators for name, quantity, dates",
                "purchase_date validator rejects future dates",
                "quantity must be > 0",
                "name cannot be empty after stripping"
            ]
        },
        {
            "source": "Category Enum Validation Issues",
            "likelihood": "MEDIUM",
            "description": "Category mapping from receipt to pantry fails validation",
            "evidence": [
                "Frontend maps string categories to PantryCategory enum",
                "Case sensitivity issues in category mapping",
                "Unknown categories default to 'OTHER' but enum validation may fail"
            ]
        },
        {
            "source": "Date Format/Timezone Issues",
            "likelihood": "MEDIUM",
            "description": "Date fields sent from frontend don't match expected format",
            "evidence": [
                "Frontend sends dates as ISO strings",
                "Backend expects date objects for validation",
                "Timezone conversion issues between frontend/backend"
            ]
        },
        {
            "source": "Duplicate Item Name Validation",
            "likelihood": "MEDIUM",
            "description": "Pantry CRUD rejects items with duplicate names for same user",
            "evidence": [
                "create_pantry_item checks for existing items with same name",
                "Returns None if duplicate found, causing 400 error in router",
                "But this should be 400, not 422"
            ]
        },
        {
            "source": "Request Body Size/Structure Issues",
            "likelihood": "LOW",
            "description": "Request body structure doesn't match expected schema",
            "evidence": [
                "RequestSizeLimitMiddleware limits to 10MB",
                "JSON parsing issues with nested objects",
                "Missing required fields in request body"
            ]
        },
        {
            "source": "Database Connection/Constraint Issues",
            "likelihood": "LOW",
            "description": "Database-level validation or constraint failures",
            "evidence": [
                "MongoDB unique indexes on user_id + name",
                "Database connection issues causing validation failures",
                "But these should cause 500 errors, not 422"
            ]
        }
    ]
    
    for i, source in enumerate(error_sources, 1):
        print(f"{i}. {source['source']} (Likelihood: {source['likelihood']})")
        print(f"   Description: {source['description']}")
        print(f"   Evidence:")
        for evidence in source['evidence']:
            print(f"   - {evidence}")
        print()
    
    return error_sources

def simulate_frontend_request():
    """
    Simulate the exact request that frontend sends when adding receipt items to pantry
    """
    
    print("🧪 SIMULATING FRONTEND REQUEST")
    print("=" * 40)
    
    # This is what ReceiptScan.tsx sends (lines 121-147)
    receipt_items = [
        {
            "name": "Chicken breast",
            "quantity": 1.0,
            "price": 8.99,  # This field doesn't exist in PantryItemCreate!
            "category": "meat"
        },
        {
            "name": "Mixed vegetables", 
            "quantity": 2.0,
            "price": 3.49,  # This field doesn't exist in PantryItemCreate!
            "category": "produce"
        }
    ]
    
    print("Frontend receipt items:")
    print(json.dumps(receipt_items, indent=2))
    print()
    
    # Frontend mapping logic (lines 123-147)
    category_map = {
        'produce': 'produce',
        'dairy': 'dairy', 
        'meat': 'meat',
        'seafood': 'seafood',
        'grains': 'grains',
        'canned goods': 'canned_goods',
        'frozen': 'frozen',
        'beverages': 'beverages',
        'snacks': 'snacks',
        'condiments': 'condiments',
        'spices': 'spices',
        'baking': 'baking',
    }
    
    pantry_requests = []
    for item in receipt_items:
        category = category_map.get(item['category'].lower(), 'other')
        
        pantry_request = {
            'name': item['name'],
            'category': category,
            'quantity': item['quantity'],
            'unit': 'piece',  # Default unit
            'purchase_date': date.today().isoformat(),  # Today's date as string
            'notes': 'Added from receipt scan'
        }
        pantry_requests.append(pantry_request)
    
    print("Frontend pantry creation requests:")
    print(json.dumps(pantry_requests, indent=2, default=str))
    print()
    
    return pantry_requests

def validate_pantry_requests(requests: List[Dict[str, Any]]):
    """
    Validate pantry requests against PantryItemCreate model requirements
    """
    
    print("🔬 VALIDATING PANTRY REQUESTS")
    print("=" * 35)
    
    validation_errors = []
    
    for i, request in enumerate(requests):
        print(f"Validating request {i+1}: {request['name']}")
        
        # Check required fields
        required_fields = ['name', 'category', 'quantity', 'unit']
        for field in required_fields:
            if field not in request:
                validation_errors.append(f"Request {i+1}: Missing required field '{field}'")
            elif request[field] is None:
                validation_errors.append(f"Request {i+1}: Field '{field}' cannot be None")
        
        # Validate name
        if 'name' in request:
            name = request['name']
            if not isinstance(name, str):
                validation_errors.append(f"Request {i+1}: 'name' must be string, got {type(name)}")
            elif not name.strip():
                validation_errors.append(f"Request {i+1}: 'name' cannot be empty after stripping")
            elif len(name) > 200:
                validation_errors.append(f"Request {i+1}: 'name' exceeds 200 character limit")
        
        # Validate quantity
        if 'quantity' in request:
            quantity = request['quantity']
            if not isinstance(quantity, (int, float)):
                validation_errors.append(f"Request {i+1}: 'quantity' must be number, got {type(quantity)}")
            elif quantity <= 0:
                validation_errors.append(f"Request {i+1}: 'quantity' must be positive, got {quantity}")
        
        # Validate category
        if 'category' in request:
            category = request['category']
            valid_categories = [
                'produce', 'dairy', 'meat', 'seafood', 'grains', 'canned_goods',
                'frozen', 'beverages', 'snacks', 'condiments', 'spices', 'baking', 'other'
            ]
            if category not in valid_categories:
                validation_errors.append(f"Request {i+1}: Invalid category '{category}', must be one of {valid_categories}")
        
        # Validate unit
        if 'unit' in request:
            unit = request['unit']
            valid_units = [
                'piece', 'lb', 'oz', 'g', 'kg', 'cup', 'tbsp', 'tsp', 'L', 'ml',
                'gal', 'qt', 'pt', 'fl oz', 'package', 'can', 'bottle', 'bag', 'box', 'container'
            ]
            if unit not in valid_units:
                validation_errors.append(f"Request {i+1}: Invalid unit '{unit}', must be one of {valid_units}")
        
        # Validate purchase_date
        if 'purchase_date' in request:
            purchase_date = request['purchase_date']
            if isinstance(purchase_date, str):
                try:
                    parsed_date = datetime.fromisoformat(purchase_date).date()
                    if parsed_date > date.today():
                        validation_errors.append(f"Request {i+1}: 'purchase_date' cannot be in the future")
                except ValueError as e:
                    validation_errors.append(f"Request {i+1}: Invalid date format for 'purchase_date': {e}")
        
        # Check for unexpected fields
        expected_fields = ['name', 'category', 'quantity', 'unit', 'expiration_date', 'purchase_date', 'notes']
        for field in request:
            if field not in expected_fields:
                validation_errors.append(f"Request {i+1}: Unexpected field '{field}' (value: {request[field]})")
        
        print(f"  ✓ Request {i+1} validation complete")
    
    print()
    if validation_errors:
        print("❌ VALIDATION ERRORS FOUND:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✅ All requests passed validation")
    
    return validation_errors

def identify_most_likely_causes(error_sources: List[Dict], validation_errors: List[str]):
    """
    Based on analysis, identify the 1-2 most likely root causes
    """
    
    print("🎯 MOST LIKELY ROOT CAUSES")
    print("=" * 30)
    
    # Check if validation errors were found
    has_validation_errors = len(validation_errors) > 0
    
    if has_validation_errors:
        print("1. PYDANTIC MODEL VALIDATION FAILURES (PRIMARY CAUSE)")
        print("   - Direct validation errors found in simulated requests")
        print("   - Frontend sends data that doesn't match PantryItemCreate schema")
        print("   - This would cause FastAPI to return 422 Unprocessable Entity")
        print()
        
        print("2. FRONTEND-BACKEND DATA FORMAT MISMATCH (SECONDARY CAUSE)")
        print("   - Frontend receipt processing creates incompatible data structure")
        print("   - Receipt items have 'price' field not expected by pantry API")
        print("   - Category/unit mapping issues between frontend and backend")
        print()
    else:
        print("1. FRONTEND-BACKEND DATA FORMAT MISMATCH (PRIMARY CAUSE)")
        print("   - Even though basic validation passes, there may be subtle format issues")
        print("   - Date format/timezone conversion problems")
        print("   - Enum value case sensitivity issues")
        print()
        
        print("2. DUPLICATE ITEM NAME VALIDATION (SECONDARY CAUSE)")
        print("   - Backend rejects items with duplicate names")
        print("   - But this should return 400, not 422 - indicates router logic issue")
        print()

def generate_debug_recommendations():
    """
    Generate specific debugging steps to validate assumptions
    """
    
    print("🔧 DEBUGGING RECOMMENDATIONS")
    print("=" * 32)
    
    recommendations = [
        {
            "step": "Add detailed logging to pantry creation endpoint",
            "action": "Log the exact request body received by POST /api/v1/pantry/",
            "purpose": "Verify what data frontend is actually sending"
        },
        {
            "step": "Add Pydantic validation error logging", 
            "action": "Catch ValidationError in pantry router and log detailed field errors",
            "purpose": "Identify which specific fields are failing validation"
        },
        {
            "step": "Test with curl/Postman",
            "action": "Send manual requests with known good/bad data to isolate issue",
            "purpose": "Separate frontend issues from backend validation issues"
        },
        {
            "step": "Check browser network tab",
            "action": "Inspect actual HTTP requests sent by frontend during receipt processing",
            "purpose": "Verify request format and identify any client-side issues"
        },
        {
            "step": "Add middleware request logging",
            "action": "Log all requests to /api/v1/pantry/ with full body content",
            "purpose": "Capture exact request data for analysis"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['step']}")
        print(f"   Action: {rec['action']}")
        print(f"   Purpose: {rec['purpose']}")
        print()

async def main():
    """
    Main debugging analysis
    """
    
    print("🚨 422 PANTRY ERROR DEBUGGING ANALYSIS")
    print("=" * 50)
    print()
    
    # Step 1: Analyze potential error sources
    error_sources = analyze_422_error_sources()
    
    print()
    
    # Step 2: Simulate frontend request
    pantry_requests = simulate_frontend_request()
    
    # Step 3: Validate requests
    validation_errors = validate_pantry_requests(pantry_requests)
    
    print()
    
    # Step 4: Identify most likely causes
    identify_most_likely_causes(error_sources, validation_errors)
    
    print()
    
    # Step 5: Generate debugging recommendations
    generate_debug_recommendations()
    
    print()
    print("🎯 NEXT STEPS:")
    print("1. Add logging to backend pantry endpoint to capture exact request data")
    print("2. Test with browser network tab to see actual frontend requests")
    print("3. Add validation error logging to identify specific field failures")
    print("4. Verify the receipt-to-pantry data flow in ReceiptScan.tsx")

if __name__ == "__main__":
    asyncio.run(main())