#!/usr/bin/env python3
"""
Test script to verify API configuration status for Google Vision API and OpenAI API
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_api_configuration():
    """Test the current API configuration status"""
    print("=" * 60)
    print("API CONFIGURATION VERIFICATION REPORT")
    print("=" * 60)
    print(f"Generated at: {datetime.now().isoformat()}")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "google_vision_api": {},
        "openai_api": {},
        "environment_variables": {},
        "service_status": {},
        "recommendations": []
    }
    
    # Check environment variables
    print("1. ENVIRONMENT VARIABLES CHECK")
    print("-" * 40)
    
    env_vars = {
        "OCR_ENABLED": os.getenv('OCR_ENABLED', 'Not Set'),
        "OCR_FALLBACK_ENABLED": os.getenv('OCR_FALLBACK_ENABLED', 'Not Set'),
        "GOOGLE_CLOUD_PROJECT_ID": os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'Not Set'),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Not Set'),
        "AI_RECIPE_GENERATION_ENABLED": os.getenv('AI_RECIPE_GENERATION_ENABLED', 'Not Set'),
        "AI_RECIPE_GENERATION_FALLBACK_ENABLED": os.getenv('AI_RECIPE_GENERATION_FALLBACK_ENABLED', 'Not Set'),
        "OPENAI_API_KEY": "***REDACTED***" if os.getenv('OPENAI_API_KEY') else 'Not Set',
        "OPENAI_MODEL": os.getenv('OPENAI_MODEL', 'Not Set')
    }
    
    for var, value in env_vars.items():
        print(f"  {var}: {value}")
        results["environment_variables"][var] = value
    
    print()
    
    # Test Google Vision API configuration
    print("2. GOOGLE VISION API CONFIGURATION")
    print("-" * 40)
    
    try:
        from app.utils.ocr_service import ocr_service
        
        ocr_status = ocr_service.get_service_status()
        results["google_vision_api"] = ocr_status
        
        print(f"  Service Enabled: {ocr_status['enabled']}")
        print(f"  Demo Mode: {ocr_status['demo_mode']}")
        print(f"  Credentials Configured: {ocr_status['credentials_configured']}")
        print(f"  Google Vision Available: {ocr_status['google_vision_available']}")
        print(f"  Client Initialized: {ocr_status['client_initialized']}")
        print(f"  Fallback Enabled: {ocr_status['fallback_enabled']}")
        
        if ocr_status['demo_mode']:
            print("  ⚠️  WARNING: OCR service is running in DEMO MODE")
            results["recommendations"].append("Configure Google Vision API credentials for real OCR processing")
        elif ocr_status['client_initialized']:
            print("  ✅ OCR service is properly configured")
        else:
            print("  ❌ OCR service has configuration issues")
            
    except Exception as e:
        print(f"  ❌ Error checking OCR service: {e}")
        results["google_vision_api"]["error"] = str(e)
    
    print()
    
    # Test OpenAI API configuration
    print("3. OPENAI API CONFIGURATION")
    print("-" * 40)
    
    try:
        from app.services.ai_recipe_generator import ai_recipe_generator
        
        ai_status = ai_recipe_generator.get_service_status()
        results["openai_api"] = ai_status
        
        print(f"  Service Enabled: {ai_status['enabled']}")
        print(f"  Demo Mode: {ai_status['demo_mode']}")
        print(f"  API Key Configured: {ai_status['api_key_configured']}")
        print(f"  OpenAI Available: {ai_status['openai_available']}")
        print(f"  Model: {ai_status['model']}")
        print(f"  Client Initialized: {ai_status['client_initialized']}")
        print(f"  Fallback Enabled: {ai_status['fallback_enabled']}")
        
        if ai_status['demo_mode']:
            print("  ⚠️  WARNING: AI Recipe Generation is running in DEMO MODE")
            results["recommendations"].append("Configure OpenAI API key for real AI recipe generation")
        elif ai_status['client_initialized']:
            print("  ✅ AI Recipe Generation service is properly configured")
        else:
            print("  ❌ AI Recipe Generation service has configuration issues")
            
    except Exception as e:
        print(f"  ❌ Error checking AI Recipe Generation service: {e}")
        results["openai_api"]["error"] = str(e)
    
    print()
    
    # Test Food Vision API configuration
    print("4. FOOD VISION API CONFIGURATION")
    print("-" * 40)
    
    try:
        from app.services.food_vision import food_vision_service
        
        vision_status = food_vision_service.get_service_status()
        results["service_status"]["food_vision"] = vision_status
        
        print(f"  Service Enabled: {vision_status['enabled']}")
        print(f"  Demo Mode: {vision_status['demo_mode']}")
        print(f"  Credentials Configured: {vision_status['credentials_configured']}")
        print(f"  Google Vision Available: {vision_status['google_vision_available']}")
        print(f"  Client Initialized: {vision_status['client_initialized']}")
        print(f"  Fallback Enabled: {vision_status['fallback_enabled']}")
        
        if vision_status['demo_mode']:
            print("  ⚠️  WARNING: Food Vision service is running in DEMO MODE")
        elif vision_status['client_initialized']:
            print("  ✅ Food Vision service is properly configured")
        else:
            print("  ❌ Food Vision service has configuration issues")
            
    except Exception as e:
        print(f"  ❌ Error checking Food Vision service: {e}")
        results["service_status"]["food_vision"] = {"error": str(e)}
    
    print()
    
    # Test API connectivity (if not in demo mode)
    print("5. API CONNECTIVITY TEST")
    print("-" * 40)
    
    # Test OCR service with demo data
    try:
        if not ocr_service.demo_mode:
            print("  Testing Google Vision API connectivity...")
            # We can't test real API without credentials, so just check if client is ready
            if ocr_service.client:
                print("  ✅ Google Vision API client is ready")
            else:
                print("  ❌ Google Vision API client not initialized")
        else:
            print("  ⚠️  Skipping Google Vision API test (demo mode)")
            
        # Test demo OCR functionality
        print("  Testing OCR demo functionality...")
        demo_text = await ocr_service._get_demo_ocr_text("test_image.jpg")
        if demo_text and len(demo_text) > 0:
            print("  ✅ OCR demo functionality working")
        else:
            print("  ❌ OCR demo functionality failed")
            
    except Exception as e:
        print(f"  ❌ Error testing OCR connectivity: {e}")
    
    # Test AI Recipe Generation service
    try:
        if not ai_recipe_generator.demo_mode:
            print("  Testing OpenAI API connectivity...")
            if ai_recipe_generator.client:
                print("  ✅ OpenAI API client is ready")
            else:
                print("  ❌ OpenAI API client not initialized")
        else:
            print("  ⚠️  Skipping OpenAI API test (demo mode)")
            
        # Test demo AI functionality
        print("  Testing AI Recipe Generation demo functionality...")
        demo_recipe = await ai_recipe_generator._get_demo_recipe_from_ingredients(
            ["chicken", "rice", "vegetables"]
        )
        if demo_recipe and demo_recipe.title:
            print("  ✅ AI Recipe Generation demo functionality working")
        else:
            print("  ❌ AI Recipe Generation demo functionality failed")
            
    except Exception as e:
        print(f"  ❌ Error testing AI Recipe Generation connectivity: {e}")
    
    print()
    
    # Summary and Recommendations
    print("6. SUMMARY AND RECOMMENDATIONS")
    print("-" * 40)
    
    # Determine overall status
    ocr_configured = not results["google_vision_api"].get("demo_mode", True)
    ai_configured = not results["openai_api"].get("demo_mode", True)
    
    if ocr_configured and ai_configured:
        overall_status = "✅ FULLY CONFIGURED"
        print("  Overall Status: All APIs are properly configured")
    elif ocr_configured or ai_configured:
        overall_status = "⚠️  PARTIALLY CONFIGURED"
        print("  Overall Status: Some APIs are configured, others in demo mode")
    else:
        overall_status = "⚠️  DEMO MODE"
        print("  Overall Status: All APIs are running in demo mode")
    
    results["overall_status"] = overall_status
    
    print()
    print("  Recommendations:")
    
    if results["google_vision_api"].get("demo_mode", True):
        print("    • Configure Google Vision API for real OCR processing:")
        print("      - Set GOOGLE_CLOUD_PROJECT_ID in .env")
        print("      - Set GOOGLE_APPLICATION_CREDENTIALS path in .env")
        print("      - Create and download service account key from Google Cloud Console")
        
    if results["openai_api"].get("demo_mode", True):
        print("    • Configure OpenAI API for real AI recipe generation:")
        print("      - Set OPENAI_API_KEY in .env")
        print("      - Optionally set OPENAI_MODEL (default: gpt-4)")
        
    if not results["environment_variables"].get("OCR_ENABLED") == "true":
        print("    • Enable OCR processing by setting OCR_ENABLED=true")
        
    if not results["environment_variables"].get("AI_RECIPE_GENERATION_ENABLED") == "true":
        print("    • Enable AI recipe generation by setting AI_RECIPE_GENERATION_ENABLED=true")
    
    print()
    print("=" * 60)
    
    # Save results to file
    with open("api_configuration_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Detailed report saved to: api_configuration_report.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_api_configuration())