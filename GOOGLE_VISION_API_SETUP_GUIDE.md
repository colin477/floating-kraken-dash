# Google Vision API Setup Guide for EZ Eatin' Receipt Scanning

This guide will help you configure Google Vision API for OCR functionality in the EZ Eatin' receipt scanning system.

## Overview

The EZ Eatin' application uses Google Vision API to extract text from receipt images. The system is designed with fallback mechanisms to work in demo mode when Google Vision API is not configured.

## Current System Status

- **Demo Mode**: The system currently runs in demo mode with mock OCR data
- **Fallback Enabled**: When OCR fails, the system provides sample receipt data
- **Production Ready**: Once configured, the system will use real Google Vision API

## Prerequisites

1. Google Cloud Platform (GCP) account
2. Billing enabled on your GCP project
3. Google Vision API enabled
4. Service account with appropriate permissions

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "ez-eatin-ocr")
4. Note your **Project ID** (you'll need this later)

### 2. Enable the Vision API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Cloud Vision API"
3. Click on "Cloud Vision API" and click "Enable"

### 3. Create a Service Account

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Enter details:
   - **Name**: `ez-eatin-vision-service`
   - **Description**: `Service account for EZ Eatin OCR functionality`
4. Click "Create and Continue"
5. Grant the role: **Cloud Vision API Service Agent**
6. Click "Continue" → "Done"

### 4. Generate Service Account Key

1. Click on your newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create"
6. **Important**: Save the downloaded JSON file securely
7. Note the file path where you saved it

### 5. Configure Environment Variables

Update your `backend/.env` file with the following values:

```env
# OCR Configuration (Google Vision API)
GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
OCR_ENABLED=true
OCR_FALLBACK_ENABLED=true
```

**Replace the values:**
- `your-project-id-here`: Your Google Cloud Project ID from Step 1
- `/path/to/your/service-account-key.json`: Full path to your downloaded JSON key file

### 6. Install Required Dependencies

The Google Vision API client library should already be installed. If not, install it:

```bash
cd backend
pip install google-cloud-vision
```

### 7. Test the Configuration

Run the OCR service test to verify everything is working:

```bash
cd backend
python -c "
import sys
sys.path.append('.')
from app.utils.ocr_service import ocr_service

print('🔍 OCR SERVICE STATUS')
print('=' * 30)
status = ocr_service.get_service_status()
for key, value in status.items():
    print(f'{key}: {value}')

if status['client_initialized']:
    print('✅ Google Vision API is ready!')
else:
    print('❌ Google Vision API not configured - running in demo mode')
"
```

## Security Best Practices

### 1. Secure Credential Storage

**Development:**
- Store the JSON key file outside your project directory
- Add the key file path to `.gitignore`
- Never commit credentials to version control

**Production:**
- Use Google Cloud's built-in service account authentication
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Consider using Google Secret Manager

### 2. Minimal Permissions

Ensure your service account only has the necessary permissions:
- **Cloud Vision API Service Agent** (minimum required)
- Avoid using overly broad roles like "Editor" or "Owner"

### 3. Key Rotation

- Regularly rotate service account keys
- Monitor key usage in Google Cloud Console
- Delete unused keys

## Environment Configuration Options

### OCR Settings

```env
# Enable/disable OCR functionality
OCR_ENABLED=true|false

# Enable fallback to demo mode when OCR fails
OCR_FALLBACK_ENABLED=true|false

# Google Cloud Project ID
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Path to service account JSON key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Behavior Modes

| OCR_ENABLED | Credentials | Behavior |
|-------------|-------------|----------|
| `false` | Any | Demo mode only |
| `true` | Missing | Demo mode with warnings |
| `true` | Invalid | Demo mode with errors |
| `true` | Valid | Full OCR functionality |

## Troubleshooting

### Common Issues

#### 1. "Application Default Credentials not found"
**Solution**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key file

#### 2. "Permission denied" errors
**Solution**: Verify your service account has the "Cloud Vision API Service Agent" role

#### 3. "API not enabled" errors
**Solution**: Enable the Cloud Vision API in your Google Cloud project

#### 4. "Quota exceeded" errors
**Solution**: Check your API quotas and billing settings in Google Cloud Console

### Debug Commands

Check OCR service status:
```bash
cd backend
python -c "
from app.utils.ocr_service import ocr_service
import json
print(json.dumps(ocr_service.get_service_status(), indent=2))
"
```

Test with a sample image:
```bash
cd backend
python -c "
import asyncio
from app.utils.ocr_service import ocr_service

async def test_ocr():
    # This will use demo mode if not configured
    result = await ocr_service.extract_text_from_image('test-image.jpg')
    print('OCR Result:', result[:100] if result else 'None')

asyncio.run(test_ocr())
"
```

## Cost Considerations

### Google Vision API Pricing

- **First 1,000 requests/month**: Free
- **Additional requests**: $1.50 per 1,000 requests
- **Text detection**: Standard pricing applies

### Cost Optimization

1. **Enable fallback mode**: Reduces API calls when OCR fails
2. **Image preprocessing**: Optimize image quality before sending to API
3. **Caching**: Consider caching OCR results for identical images
4. **Monitoring**: Set up billing alerts in Google Cloud Console

## Production Deployment

### Environment Variables

For production deployment, set these environment variables:

```bash
export GOOGLE_CLOUD_PROJECT_ID="your-production-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/app/credentials/service-account.json"
export OCR_ENABLED="true"
export OCR_FALLBACK_ENABLED="true"
```

### Docker Configuration

If using Docker, mount the credentials file:

```dockerfile
# Copy service account key
COPY service-account-key.json /app/credentials/
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-key.json
```

### Health Checks

The system provides health check endpoints to verify OCR functionality:

```bash
curl http://localhost:8000/api/v1/health/ocr
```

## Support

### Getting Help

1. **Google Cloud Support**: For API-related issues
2. **Application Logs**: Check backend logs for detailed error messages
3. **Demo Mode**: System continues to work without Google Vision API

### Monitoring

Monitor your Google Vision API usage:
1. Go to Google Cloud Console
2. Navigate to "APIs & Services" → "Dashboard"
3. Click on "Cloud Vision API"
4. Review usage metrics and quotas

## Summary

The EZ Eatin' receipt scanning system is designed to work with or without Google Vision API:

- **With Google Vision API**: Full OCR functionality for real receipt processing
- **Without Google Vision API**: Demo mode with sample data for testing and development

The fallback mechanisms ensure the application remains functional even when OCR services are unavailable, making it robust for both development and production environments.