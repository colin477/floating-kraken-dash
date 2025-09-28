# Cloud Storage Integration Guide

## Overview

This guide covers the implementation of cloud storage integration for receipt images in the EZ Eatin' application. The system now supports AWS S3 for production-grade file storage while maintaining local file storage as a fallback for development and testing.

## Features Implemented

### ✅ Core Features
- **AWS S3 Integration**: Full support for Amazon S3 cloud storage
- **Local Storage Fallback**: Automatic fallback to local file storage when cloud storage is unavailable
- **Secure File Upload**: Receipt images are uploaded to cloud storage with proper organization
- **Presigned URLs**: Generate secure, time-limited URLs for image access
- **File Cleanup**: Automatic cleanup of files when receipts are deleted
- **OCR Compatibility**: OCR service works with both cloud-stored and local files
- **Error Handling**: Comprehensive error handling and logging

### 🔧 Technical Implementation

#### 1. Cloud Storage Service (`backend/app/utils/cloud_storage.py`)
- **CloudStorageService**: Main service class for handling file operations
- **Upload Files**: Store files in S3 with user-specific organization
- **Generate Presigned URLs**: Create secure access URLs with expiration
- **File Management**: Delete, get info, and manage stored files
- **Fallback Support**: Automatic fallback to local storage when needed

#### 2. Updated Receipt Upload (`backend/app/routers/receipts.py`)
- **Modified Upload Endpoint**: Now uses cloud storage for file uploads
- **Error Handling**: Proper cleanup on upload failures
- **Secure Image URLs**: New endpoint for generating secure image access URLs

#### 3. Enhanced OCR Service (`backend/app/utils/ocr_service.py`)
- **Multi-Source Support**: Works with both S3 URLs and local file paths
- **Presigned URL Generation**: Automatically generates presigned URLs for S3 files
- **Backward Compatibility**: Maintains support for existing local files

#### 4. Database Integration (`backend/app/crud/receipts.py`)
- **File Cleanup**: Automatic file deletion when receipts are removed
- **URL Storage**: Stores cloud storage URLs in receipt records

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Cloud Storage Configuration (AWS S3)
CLOUD_STORAGE_ENABLED=true
CLOUD_STORAGE_FALLBACK_LOCAL=true
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
S3_BUCKET_PREFIX=receipts/
```

### AWS S3 Setup

1. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://your-receipt-bucket-name
   ```

2. **Set Bucket Policy** (example):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AllowReceiptUploads",
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::YOUR-ACCOUNT:user/receipt-uploader"
         },
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::your-receipt-bucket-name/*"
       }
     ]
   }
   ```

3. **Create IAM User** with permissions:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject`
   - `s3:ListBucket`

### Dependencies

The following packages have been added to `requirements.txt`:
```
boto3==1.34.0
botocore==1.34.0
```

Install with:
```bash
pip install boto3==1.34.0 botocore==1.34.0
```

## API Endpoints

### Upload Receipt Image
```http
POST /api/v1/receipts/upload
Content-Type: multipart/form-data

file: [receipt image file]
```

**Response**:
```json
{
  "receipt_id": "receipt_id_here",
  "processing_status": "COMPLETED",
  "extracted_items": [...],
  "confidence_score": 0.85,
  "processing_notes": "OCR processing completed..."
}
```

### Get Secure Image URL
```http
GET /api/v1/receipts/{receipt_id}/image-url
```

**Response**:
```json
{
  "receipt_id": "receipt_id_here",
  "image_url": "https://presigned-s3-url...",
  "expires_in": 3600,
  "storage_type": "cloud"
}
```

## File Organization

Files are organized in S3 with the following structure:
```
receipts/
├── users/
│   ├── user_id_1/
│   │   ├── uuid1.jpg
│   │   ├── uuid2.png
│   │   └── ...
│   ├── user_id_2/
│   │   └── ...
│   └── ...
└── ...
```

## Security Features

### 1. Presigned URLs
- **Time-Limited Access**: URLs expire after 1 hour by default
- **Secure Access**: No need to expose AWS credentials to frontend
- **User-Specific**: Only authenticated users can access their own images

### 2. File Validation
- **Content Type Checking**: Only image files are accepted
- **File Size Limits**: 10MB maximum file size
- **Image Validation**: Files are validated as proper images

### 3. Access Control
- **User Isolation**: Files are organized by user ID
- **Authentication Required**: All endpoints require valid JWT tokens
- **Proper IAM Roles**: AWS access is limited to necessary permissions

## Development vs Production

### Development Mode
- **Local Storage**: Files stored in `uploads/` directory
- **Direct File Access**: Files accessed via local file paths
- **No AWS Required**: Works without AWS credentials

### Production Mode
- **Cloud Storage**: Files stored in AWS S3
- **Presigned URLs**: Secure access via time-limited URLs
- **Scalable**: Handles large numbers of files efficiently

## Testing

Run the integration test:
```bash
python test_cloud_storage_integration.py
```

This test verifies:
- ✅ Cloud storage configuration
- ✅ File upload functionality
- ✅ Secure URL generation
- ✅ File deletion
- ✅ Receipt workflow integration
- ✅ OCR service compatibility

## Monitoring and Logging

The system includes comprehensive logging for:
- File upload success/failure
- S3 operations
- Presigned URL generation
- File cleanup operations
- Error conditions and fallbacks

Logs are structured and include:
- Timestamp
- Log level
- Operation details
- Error messages
- File URLs/paths

## Migration from Local Storage

For existing installations with local files:

1. **Gradual Migration**: New uploads go to cloud storage
2. **Backward Compatibility**: Existing local files continue to work
3. **Migration Script**: Can be created to move existing files to S3

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**:
   - Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
   - Check IAM user permissions

2. **Bucket Access Denied**:
   - Verify bucket policy allows your IAM user
   - Check bucket name is correct

3. **Files Not Uploading**:
   - Check `CLOUD_STORAGE_ENABLED=true`
   - Verify network connectivity to AWS
   - Check file size limits

4. **OCR Not Working with S3 Files**:
   - Verify presigned URL generation is working
   - Check Google Vision API credentials

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed information about:
- S3 operations
- File upload/download processes
- Presigned URL generation
- Error conditions

## Performance Considerations

### Upload Performance
- **Direct Upload**: Files uploaded directly to S3
- **Streaming**: Large files handled efficiently
- **Parallel Processing**: Multiple uploads can be handled concurrently

### Access Performance
- **CDN Ready**: S3 URLs can be used with CloudFront
- **Caching**: Presigned URLs can be cached for their lifetime
- **Regional Storage**: Files stored in specified AWS region

### Cost Optimization
- **Lifecycle Policies**: Can be configured for automatic archival
- **Storage Classes**: Can use different S3 storage classes
- **Cleanup**: Automatic deletion prevents storage bloat

## Future Enhancements

Potential improvements:
- **Multiple Cloud Providers**: Support for Google Cloud, Azure
- **Image Optimization**: Automatic resizing and compression
- **CDN Integration**: CloudFront distribution for faster access
- **Backup Strategy**: Cross-region replication
- **Analytics**: File access and usage metrics

## Conclusion

The cloud storage integration provides a robust, scalable solution for receipt image storage while maintaining backward compatibility and development-friendly fallbacks. The system is production-ready and includes comprehensive error handling, security features, and monitoring capabilities.