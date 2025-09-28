"""
Cloud storage service for handling file uploads to AWS S3
"""

import logging
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None

# Configure logging
logger = logging.getLogger(__name__)


class CloudStorageService:
    """Cloud storage service for managing file uploads and access"""
    
    def __init__(self):
        self.enabled = os.getenv('CLOUD_STORAGE_ENABLED', 'false').lower() == 'true'
        self.fallback_to_local = os.getenv('CLOUD_STORAGE_FALLBACK_LOCAL', 'true').lower() == 'true'
        
        # AWS S3 Configuration
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        self.s3_bucket_prefix = os.getenv('S3_BUCKET_PREFIX', 'receipts/')
        
        # Initialize S3 client
        self.s3_client = None
        if self.enabled and BOTO3_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
                logger.info("AWS S3 client initialized successfully")
                
                # Verify bucket access
                self._verify_bucket_access()
                
            except (NoCredentialsError, ClientError) as e:
                logger.error(f"Failed to initialize AWS S3 client: {e}")
                if not self.fallback_to_local:
                    raise
                self.s3_client = None
            except Exception as e:
                logger.error(f"Unexpected error initializing S3 client: {e}")
                if not self.fallback_to_local:
                    raise
                self.s3_client = None
    
    def _verify_bucket_access(self):
        """Verify that we can access the S3 bucket"""
        if not self.s3_client or not self.s3_bucket_name:
            return
        
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
            logger.info(f"Successfully verified access to S3 bucket: {self.s3_bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.s3_bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.s3_bucket_name}'")
            else:
                logger.error(f"Error accessing S3 bucket '{self.s3_bucket_name}': {e}")
            
            if not self.fallback_to_local:
                raise
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/octet-stream',
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to cloud storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            user_id: Optional user ID for organizing files
            
        Returns:
            Cloud storage URL if successful, local file path if fallback, None if failed
        """
        if not self.enabled or not self.s3_client:
            if self.fallback_to_local:
                return await self._upload_file_local(file_content, filename)
            return None
        
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create S3 key with optional user organization
            if user_id:
                s3_key = f"{self.s3_bucket_prefix}users/{user_id}/{unique_filename}"
            else:
                s3_key = f"{self.s3_bucket_prefix}{unique_filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'user_id': user_id or 'anonymous'
                }
            )
            
            # Return S3 URL
            s3_url = f"https://{self.s3_bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded file to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"AWS S3 error uploading file: {e}")
            if self.fallback_to_local:
                return await self._upload_file_local(file_content, filename)
            return None
        except Exception as e:
            logger.error(f"Error uploading file to cloud storage: {e}")
            if self.fallback_to_local:
                return await self._upload_file_local(file_content, filename)
            return None
    
    async def _upload_file_local(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Fallback: Upload file to local storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            logger.info(f"Successfully uploaded file locally: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error uploading file locally: {e}")
            return None
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete file from cloud storage or local storage
        
        Args:
            file_url: URL or path of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not file_url:
            return False
        
        # Check if it's an S3 URL
        if file_url.startswith('https://') and '.s3.' in file_url:
            return await self._delete_file_s3(file_url)
        else:
            return await self._delete_file_local(file_url)
    
    async def _delete_file_s3(self, s3_url: str) -> bool:
        """Delete file from S3"""
        if not self.s3_client:
            return False
        
        try:
            # Extract S3 key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/key
            url_parts = s3_url.split('/')
            s3_key = '/'.join(url_parts[3:])  # Everything after the domain
            
            self.s3_client.delete_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted file from S3: {s3_url}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS S3 error deleting file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    async def _delete_file_local(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Successfully deleted local file: {file_path}")
                return True
            else:
                logger.warning(f"Local file not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting local file: {e}")
            return False
    
    async def generate_presigned_url(
        self,
        file_url: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for secure access to a file
        
        Args:
            file_url: S3 URL of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL if successful, original URL if not S3, None if failed
        """
        if not file_url:
            return None
        
        # If it's not an S3 URL, return the original URL
        if not (file_url.startswith('https://') and '.s3.' in file_url):
            return file_url
        
        if not self.s3_client:
            return file_url  # Fallback to original URL
        
        try:
            # Extract S3 key from URL
            url_parts = file_url.split('/')
            s3_key = '/'.join(url_parts[3:])
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.debug(f"Generated presigned URL for {file_url}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"AWS S3 error generating presigned URL: {e}")
            return file_url  # Fallback to original URL
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return file_url  # Fallback to original URL
    
    async def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from cloud storage
        
        Args:
            file_url: URL of the file
            
        Returns:
            Dictionary with file info if successful, None otherwise
        """
        if not file_url or not self.s3_client:
            return None
        
        # Only works for S3 URLs
        if not (file_url.startswith('https://') and '.s3.' in file_url):
            return None
        
        try:
            # Extract S3 key from URL
            url_parts = file_url.split('/')
            s3_key = '/'.join(url_parts[3:])
            
            # Get object metadata
            response = self.s3_client.head_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            
            return {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"AWS S3 error getting file info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
    
    def is_cloud_storage_enabled(self) -> bool:
        """Check if cloud storage is enabled and available"""
        return self.enabled and self.s3_client is not None
    
    def get_storage_type(self, file_url: str) -> str:
        """
        Determine storage type based on file URL
        
        Args:
            file_url: URL or path of the file
            
        Returns:
            'cloud' for S3 URLs, 'local' for local paths
        """
        if file_url and file_url.startswith('https://') and '.s3.' in file_url:
            return 'cloud'
        return 'local'


# Global cloud storage service instance
cloud_storage_service = CloudStorageService()