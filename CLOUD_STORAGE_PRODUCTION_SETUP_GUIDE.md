# Cloud Storage Production Setup Guide

## 🔍 Current State Analysis

Based on comprehensive testing, the system currently has:

### ✅ **Working Components**
- **Local Storage**: Fully functional with 7 existing files (2.78 MB total)
- **Fallback System**: Robust fallback from cloud to local storage
- **File Operations**: Upload, delete, and URL generation working
- **Security Framework**: User-based file organization and presigned URL support
- **Error Handling**: Comprehensive error handling and logging

### ⚠️ **Configuration Gaps**
- **Cloud Storage Disabled**: `CLOUD_STORAGE_ENABLED=false`
- **Missing AWS Credentials**: No AWS access keys configured
- **No S3 Bucket**: S3 bucket name not specified
- **Production Readiness**: Configuration incomplete for production deployment

---

## 🚀 Production Cloud Storage Configuration

### Step 1: AWS S3 Setup

#### 1.1 Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://ez-eatin-receipts-prod --region us-east-1

# Or create via AWS Console with these settings:
# - Bucket name: ez-eatin-receipts-prod
# - Region: us-east-1
# - Block public access: Enabled
# - Versioning: Enabled
# - Server-side encryption: AES-256
```

#### 1.2 Configure Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EzEatinAppAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/ez-eatin-app"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::ez-eatin-receipts-prod/*"
    },
    {
      "Sid": "EzEatinBucketAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/ez-eatin-app"
      },
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::ez-eatin-receipts-prod"
    }
  ]
}
```

#### 1.3 Create IAM User and Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::ez-eatin-receipts-prod",
        "arn:aws:s3:::ez-eatin-receipts-prod/*"
      ]
    }
  ]
}
```

### Step 2: Environment Configuration

#### 2.1 Update Production Environment Variables
```bash
# Cloud Storage Configuration
CLOUD_STORAGE_ENABLED=true
CLOUD_STORAGE_FALLBACK_LOCAL=true

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=ez-eatin-receipts-prod
S3_BUCKET_PREFIX=receipts/

# Optional: For different environments
S3_BUCKET_NAME_DEV=ez-eatin-receipts-dev
S3_BUCKET_NAME_STAGING=ez-eatin-receipts-staging
S3_BUCKET_NAME_PROD=ez-eatin-receipts-prod
```

#### 2.2 Environment-Specific Configuration
```python
# Add to backend/app/config.py
import os

class StorageConfig:
    """Storage configuration based on environment"""
    
    @staticmethod
    def get_bucket_name():
        env = os.getenv('APP_ENV', 'development')
        if env == 'production':
            return os.getenv('S3_BUCKET_NAME_PROD', 'ez-eatin-receipts-prod')
        elif env == 'staging':
            return os.getenv('S3_BUCKET_NAME_STAGING', 'ez-eatin-receipts-staging')
        else:
            return os.getenv('S3_BUCKET_NAME_DEV', 'ez-eatin-receipts-dev')
```

### Step 3: Enhanced Security Configuration

#### 3.1 File Type Validation Enhancement
```python
# Add to backend/app/utils/file_validator.py
import magic
from typing import List, Tuple

ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/heic': ['.heic'],
    'image/webp': ['.webp']
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_file(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """Enhanced file validation with magic number checking"""
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, "File size exceeds 10MB limit"
    
    # Check file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Use python-magic for MIME type detection
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in ALLOWED_IMAGE_TYPES:
            return False, f"Invalid file type: {mime_type}"
        
        # Verify extension matches MIME type
        allowed_extensions = ALLOWED_IMAGE_TYPES[mime_type]
        if f'.{file_ext}' not in allowed_extensions:
            return False, f"File extension .{file_ext} doesn't match content type {mime_type}"
        
        return True, "Valid image file"
        
    except Exception as e:
        return False, f"File validation error: {str(e)}"
```

#### 3.2 Enhanced Upload Endpoint
```python
# Update backend/app/routers/receipts.py upload endpoint
from app.utils.file_validator import validate_image_file

@router.post("/upload", response_model=ReceiptProcessingResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a receipt image file and process it with enhanced validation"""
    user_id = str(current_user["_id"])
    
    # Read file content
    file_content = await file.read()
    
    # Enhanced file validation
    is_valid, validation_message = validate_image_file(file_content, file.filename or "receipt.jpg")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_message
        )
    
    # Continue with existing upload logic...
```

### Step 4: Monitoring and Alerting

#### 4.1 CloudWatch Metrics
```python
# Add to backend/app/utils/metrics.py
import boto3
from datetime import datetime

class StorageMetrics:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def record_upload_success(self, file_size: int, user_id: str):
        """Record successful file upload metrics"""
        self.cloudwatch.put_metric_data(
            Namespace='EzEatin/Storage',
            MetricData=[
                {
                    'MetricName': 'FileUploads',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Status', 'Value': 'Success'},
                        {'Name': 'UserId', 'Value': user_id}
                    ]
                },
                {
                    'MetricName': 'FileSize',
                    'Value': file_size,
                    'Unit': 'Bytes'
                }
            ]
        )
    
    def record_upload_failure(self, error_type: str, user_id: str):
        """Record failed file upload metrics"""
        self.cloudwatch.put_metric_data(
            Namespace='EzEatin/Storage',
            MetricData=[
                {
                    'MetricName': 'FileUploads',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Status', 'Value': 'Failed'},
                        {'Name': 'ErrorType', 'Value': error_type},
                        {'Name': 'UserId', 'Value': user_id}
                    ]
                }
            ]
        )
```

#### 4.2 Health Check Enhancement
```python
# Update backend/app/routers/health.py
@router.get("/storage")
async def storage_health_check():
    """Enhanced storage service health check"""
    try:
        from app.utils.cloud_storage import cloud_storage_service
        
        health_data = {
            "status": "healthy",
            "storage_type": "local" if not cloud_storage_service.is_cloud_storage_enabled() else "cloud",
            "fallback_enabled": cloud_storage_service.fallback_to_local,
            "s3_client_available": cloud_storage_service.s3_client is not None,
            "bucket_configured": bool(cloud_storage_service.s3_bucket_name),
            "credentials_configured": bool(
                cloud_storage_service.aws_access_key_id and 
                cloud_storage_service.aws_secret_access_key
            )
        }
        
        # Test S3 connectivity if enabled
        if cloud_storage_service.is_cloud_storage_enabled():
            try:
                # Simple bucket access test
                cloud_storage_service.s3_client.head_bucket(
                    Bucket=cloud_storage_service.s3_bucket_name
                )
                health_data["s3_connectivity"] = "healthy"
            except Exception as e:
                health_data["s3_connectivity"] = "failed"
                health_data["s3_error"] = str(e)
                health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Storage service check failed: {str(e)}",
            "storage_type": "unknown"
        }
```

### Step 5: Backup and Disaster Recovery

#### 5.1 S3 Lifecycle Policy
```json
{
  "Rules": [
    {
      "ID": "EzEatinReceiptLifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "receipts/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

#### 5.2 Cross-Region Replication
```json
{
  "Role": "arn:aws:iam::YOUR-ACCOUNT-ID:role/replication-role",
  "Rules": [
    {
      "ID": "EzEatinReplication",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "receipts/"
      },
      "Destination": {
        "Bucket": "arn:aws:s3:::ez-eatin-receipts-backup",
        "StorageClass": "STANDARD_IA"
      }
    }
  ]
}
```

### Step 6: Migration Strategy

#### 6.1 Existing Files Migration Script
```python
# migration_script.py
import asyncio
import os
from pathlib import Path
from app.utils.cloud_storage import cloud_storage_service

async def migrate_existing_files():
    """Migrate existing local files to S3"""
    uploads_dir = Path("backend/uploads")
    
    if not uploads_dir.exists():
        print("No uploads directory found")
        return
    
    files = list(uploads_dir.glob("*"))
    print(f"Found {len(files)} files to migrate")
    
    for file_path in files:
        if file_path.is_file():
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Upload to S3
                s3_url = await cloud_storage_service.upload_file(
                    file_content=file_content,
                    filename=file_path.name,
                    content_type="image/jpeg",  # Assume JPEG for existing files
                    user_id="migration"
                )
                
                if s3_url:
                    print(f"✅ Migrated {file_path.name} -> {s3_url}")
                    # Optionally remove local file after successful upload
                    # file_path.unlink()
                else:
                    print(f"❌ Failed to migrate {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Error migrating {file_path.name}: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_existing_files())
```

---

## 🔧 Installation and Dependencies

### Required Python Packages
```bash
pip install boto3 python-magic-bin
```

### System Dependencies (for file validation)
```bash
# Ubuntu/Debian
sudo apt-get install libmagic1

# macOS
brew install libmagic

# Windows
# python-magic-bin includes Windows binaries
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Create S3 bucket with proper configuration
- [ ] Set up IAM user with minimal required permissions
- [ ] Configure environment variables
- [ ] Test S3 connectivity
- [ ] Set up CloudWatch monitoring
- [ ] Configure lifecycle policies

### Post-Deployment
- [ ] Run storage health check
- [ ] Test file upload/download functionality
- [ ] Verify fallback mechanism
- [ ] Monitor CloudWatch metrics
- [ ] Test disaster recovery procedures
- [ ] Migrate existing files (if needed)

### Security Verification
- [ ] Verify bucket policies are restrictive
- [ ] Test that public access is blocked
- [ ] Confirm presigned URLs work correctly
- [ ] Validate file type restrictions
- [ ] Test rate limiting on uploads

---

## 🚨 Troubleshooting

### Common Issues

#### 1. S3 Access Denied
```bash
# Check IAM permissions
aws iam get-user-policy --user-name ez-eatin-app --policy-name S3Access

# Test bucket access
aws s3 ls s3://ez-eatin-receipts-prod/
```

#### 2. File Upload Failures
```python
# Check logs for specific error messages
# Common causes:
# - Invalid credentials
# - Bucket doesn't exist
# - Network connectivity issues
# - File size/type restrictions
```

#### 3. Fallback Not Working
```python
# Verify fallback configuration
CLOUD_STORAGE_FALLBACK_LOCAL=true

# Check local storage permissions
# Ensure uploads directory is writable
```

---

## 📊 Performance Optimization

### 1. CloudFront Distribution
```json
{
  "Origins": [
    {
      "DomainName": "ez-eatin-receipts-prod.s3.amazonaws.com",
      "Id": "S3-ez-eatin-receipts-prod",
      "S3OriginConfig": {
        "OriginAccessIdentity": "origin-access-identity/cloudfront/YOUR-OAI-ID"
      }
    }
  ],
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-ez-eatin-receipts-prod",
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  }
}
```

### 2. Multipart Upload for Large Files
```python
# For files > 5MB, use multipart upload
def upload_large_file(file_content: bytes, filename: str):
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        # Use multipart upload
        pass
```

---

## 🔍 Monitoring Dashboard

### Key Metrics to Monitor
- File upload success/failure rates
- Average upload time
- Storage costs
- Error rates by type
- User activity patterns

### Alerts to Configure
- High error rates (>5%)
- Unusual upload volumes
- S3 service issues
- Cost thresholds exceeded

---

This guide provides a comprehensive approach to configuring production-ready cloud storage for the EZ Eatin' application, ensuring scalability, security, and reliability for receipt image and meal photo storage.