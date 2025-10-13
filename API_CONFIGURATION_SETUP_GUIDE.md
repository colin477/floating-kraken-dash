# API Configuration Setup Guide

## Overview

This guide provides step-by-step instructions for configuring the Google Vision API and OpenAI API to enable full functionality for receipt processing and AI recipe generation in the EZ Eatin' application.

**Current Status**: Both APIs are running in **DEMO MODE** with fallback functionality.

## Required API Keys

### 1. Google Vision API (for OCR Receipt Processing and Meal Photo Analysis)
- **Purpose**: Extract text from receipt images and analyze meal photos
- **Services Used**: 
  - Text Detection (OCR)
  - Label Detection (Food Recognition)
  - Object Localization (Food Items)

### 2. OpenAI API (for AI Recipe Generation)
- **Purpose**: Generate recipes from available ingredients using GPT models
- **Services Used**: 
  - Chat Completions API
  - GPT-4 model (configurable)

## Current Configuration Status

Based on the analysis, here's the current status:

```
Environment Variables: ❌ Not configured
Google Vision API: ⚠️  Demo Mode (credentials not configured)
OpenAI API: ⚠️  Demo Mode (API key not configured)
Food Vision Service: ⚠️  Demo Mode (credentials not configured)
OCR Service: ⚠️  Demo Mode (credentials not configured)
```

## Step-by-Step Configuration

### Step 1: Google Vision API Setup

#### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID (you'll need this later)

#### 1.2 Enable Vision API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Vision API"
3. Click on "Cloud Vision API" and click "Enable"

#### 1.3 Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `ez-eatin-vision-api`
   - Description: `Service account for EZ Eatin Vision API access`
4. Click "Create and Continue"
5. Grant the role: "Cloud Vision API Service Agent"
6. Click "Continue" and then "Done"

#### 1.4 Generate Service Account Key
1. In the Credentials page, find your service account
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" format and click "Create"
6. Save the downloaded JSON file securely (e.g., `backend/credentials/google-vision-key.json`)

### Step 2: OpenAI API Setup

#### 2.1 Create OpenAI Account
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account

#### 2.2 Generate API Key
1. Go to [API Keys page](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Give it a name like "EZ Eatin App"
4. Copy the API key (you won't be able to see it again)
5. Store it securely

#### 2.3 Set Up Billing (if needed)
1. Go to [Billing page](https://platform.openai.com/account/billing)
2. Add a payment method if you plan to exceed free tier limits

### Step 3: Environment Configuration

#### 3.1 Update Backend .env File
Edit `backend/.env` and add/update the following variables:

```bash
# OCR Configuration (Google Vision API)
OCR_ENABLED=true
OCR_FALLBACK_ENABLED=true
GOOGLE_CLOUD_PROJECT_ID=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-vision-key.json

# OpenAI Configuration (for AI recipe generation)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
AI_RECIPE_GENERATION_ENABLED=true
AI_RECIPE_GENERATION_FALLBACK_ENABLED=true
```

#### 3.2 Create Credentials Directory
```bash
mkdir -p backend/credentials
# Copy your Google Vision API key file to this directory
cp /path/to/downloaded/key.json backend/credentials/google-vision-key.json
```

#### 3.3 Update .gitignore
Ensure your credentials are not committed to version control:

```bash
# Add to .gitignore if not already present
backend/credentials/
*.json
!backend/credentials/.gitkeep
```

### Step 4: Verification

#### 4.1 Restart the Backend Server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4.2 Run Configuration Test
```bash
python test_api_configuration.py
```

#### 4.3 Check Health Endpoints
```bash
# Check OCR service status
curl -X GET "http://localhost:8000/api/v1/health/ocr"

# Check overall system health
curl -X GET "http://localhost:8000/api/v1/health/system"
```

## Expected Results After Configuration

Once properly configured, you should see:

### OCR Service Status
```json
{
  "status": "healthy",
  "message": "OCR service is operational",
  "details": {
    "enabled": true,
    "demo_mode": false,
    "credentials_configured": true,
    "google_vision_available": true,
    "client_initialized": true,
    "fallback_enabled": true
  }
}
```

### AI Recipe Generation Status
```json
{
  "enabled": true,
  "demo_mode": false,
  "api_key_configured": true,
  "openai_available": true,
  "model": "gpt-4",
  "client_initialized": true,
  "fallback_enabled": true
}
```

## Testing Real API Functionality

### Test Receipt Processing
1. Upload a receipt image through the frontend
2. Check that real OCR text extraction occurs (not demo data)
3. Verify items are properly extracted and categorized

### Test Meal Photo Analysis
1. Upload a meal photo through the frontend
2. Check that real food detection occurs
3. Verify recipe generation uses actual AI

### Test AI Recipe Generation
1. Use the recipe generation feature with your pantry items
2. Verify recipes are generated using real OpenAI API
3. Check for realistic and varied recipe suggestions

## Troubleshooting

### Common Issues

#### Google Vision API Issues
- **Error**: "Permission denied" or "Invalid credentials"
  - **Solution**: Check that the service account has proper permissions
  - **Solution**: Verify the JSON key file path is correct

- **Error**: "API not enabled"
  - **Solution**: Enable the Cloud Vision API in Google Cloud Console

#### OpenAI API Issues
- **Error**: "Invalid API key"
  - **Solution**: Verify the API key is correct and active
  - **Solution**: Check if you have sufficient credits/billing set up

- **Error**: "Rate limit exceeded"
  - **Solution**: Implement rate limiting or upgrade your OpenAI plan

#### Environment Variable Issues
- **Error**: Variables not loading
  - **Solution**: Restart the backend server after updating .env
  - **Solution**: Check for typos in variable names

### Debug Commands
```bash
# Check environment variables are loaded
python -c "import os; print('OCR_ENABLED:', os.getenv('OCR_ENABLED')); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"

# Test Google Vision API credentials
python -c "from google.cloud import vision; client = vision.ImageAnnotatorClient(); print('Google Vision client initialized successfully')"

# Test OpenAI API key
python -c "import openai; openai.api_key='your-key-here'; print('OpenAI key format valid')"
```

## Cost Considerations

### Google Vision API Pricing
- Text Detection: $1.50 per 1,000 images (first 1,000 free per month)
- Label Detection: $1.50 per 1,000 images (first 1,000 free per month)
- Object Localization: $1.50 per 1,000 images (first 1,000 free per month)

### OpenAI API Pricing (as of 2024)
- GPT-4: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- GPT-3.5-turbo: ~$0.001 per 1K input tokens, ~$0.002 per 1K output tokens

### Cost Optimization Tips
1. Use fallback modes during development
2. Implement caching for repeated requests
3. Consider using GPT-3.5-turbo for less complex recipe generation
4. Monitor usage through respective dashboards

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables for all sensitive data**
3. **Rotate API keys regularly**
4. **Set up billing alerts to monitor usage**
5. **Use least-privilege access for service accounts**
6. **Monitor API usage logs for unusual activity**

## Support and Documentation

### Google Vision API
- [Documentation](https://cloud.google.com/vision/docs)
- [Pricing](https://cloud.google.com/vision/pricing)
- [Support](https://cloud.google.com/support)

### OpenAI API
- [Documentation](https://platform.openai.com/docs)
- [Pricing](https://openai.com/pricing)
- [Support](https://help.openai.com/)

## Next Steps

After successful configuration:

1. **Test thoroughly** with real data
2. **Monitor costs** and usage patterns
3. **Implement error handling** for API failures
4. **Set up monitoring** and alerting
5. **Consider implementing caching** to reduce API calls
6. **Plan for scaling** as usage grows

---

*This guide was generated based on the current system architecture and API integration patterns. Update as needed when APIs or requirements change.*