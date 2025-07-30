import boto3
import botocore
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, List, Dict, Any, Tuple, BinaryIO
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import mimetypes
import logging
from io import BytesIO

from app.config import settings

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Base exception for file storage operations"""
    pass


class FileUploadError(FileStorageError):
    """Exception raised when file upload fails"""
    pass


class FileNotFoundError(FileStorageError):
    """Exception raised when file is not found"""
    pass


class FileSizeError(FileStorageError):
    """Exception raised when file exceeds size limits"""
    pass


class FileTypeError(FileStorageError):
    """Exception raised when file type is not allowed"""
    pass


class FileStorageService:
    """
    AWS S3 file storage service for InstantIn.me digital products
    
    Handles secure file uploads, downloads, and management with proper organization:
    - User/storefront/product-based file organization
    - File size and type validation
    - Secure URL generation with expiration
    - File metadata tracking
    - Automatic cleanup and management
    """
    
    # Maximum file size: 5GB (as specified in product schemas)
    MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes
    
    # Allowed file types for digital products
    ALLOWED_MIME_TYPES = {
        # Documents
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/csv',
        'application/rtf',
        
        # Archives
        'application/zip',
        'application/x-zip-compressed',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/gzip',
        'application/x-tar',
        
        # Images
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml',
        'image/bmp',
        'image/tiff',
        
        # Audio
        'audio/mpeg',
        'audio/wav',
        'audio/flac',
        'audio/aac',
        'audio/ogg',
        'audio/mp4',
        
        # Video
        'video/mp4',
        'video/mpeg',
        'video/quicktime',
        'video/x-msvideo',
        'video/webm',
        'video/ogg',
        
        # Software/Code
        'application/x-executable',
        'application/octet-stream',
        'application/json',
        'application/xml',
        'text/html',
        'text/css',
        'text/javascript',
        'application/javascript',
        
        # Fonts
        'font/ttf',
        'font/otf',
        'font/woff',
        'font/woff2',
        'application/font-woff',
        'application/font-woff2',
        
        # 3D Models
        'model/gltf-binary',
        'model/gltf+json',
        'application/x-blender',
        
        # Adobe formats
        'application/x-photoshop',
        'application/illustrator',
        'application/x-indesign',
    }
    
    # File extensions for additional validation
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.rtf',
        '.zip', '.rar', '.7z', '.gz', '.tar', '.bz2',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', '.tif',
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
        '.exe', '.dmg', '.pkg', '.deb', '.rpm', '.msi', '.app',
        '.json', '.xml', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.glb', '.gltf', '.blend', '.obj', '.fbx',
        '.psd', '.ai', '.indd', '.sketch', '.fig',
        '.epub', '.mobi', '.azw', '.azw3',
        '.ics', '.vcf', '.kml', '.gpx'
    }

    def __init__(self):
        """Initialize S3 client configuration (connection validation deferred)"""
        if not settings.aws_configured:
            raise FileStorageError("AWS S3 is not properly configured")
        
        self.bucket_name = settings.aws_s3_bucket
        self.region = settings.aws_region
        self._s3_client = None
        self._s3_validated = False
        
        logger.info(f"🔧 FileStorageService initialized (S3 validation deferred)")
    
    @property
    def s3_client(self):
        """
        Lazy initialization of S3 client with validation
        
        Returns:
            boto3.client: S3 client instance
            
        Raises:
            FileStorageError: If S3 client cannot be initialized or bucket is inaccessible
        """
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=self.region
                )
                logger.info(f"✅ S3 client initialized for region '{self.region}'")
            except Exception as e:
                logger.error(f"❌ Failed to initialize S3 client: {e}")
                raise FileStorageError(f"Failed to initialize S3 client: {e}")
        
        # Validate bucket access on first use
        if not self._s3_validated:
            try:
                self._s3_client.head_bucket(Bucket=self.bucket_name)
                self._s3_validated = True
                logger.info(f"✅ S3 bucket '{self.bucket_name}' accessible")
            except Exception as e:
                logger.error(f"❌ S3 bucket '{self.bucket_name}' not accessible: {e}")
                raise FileStorageError(f"S3 bucket '{self.bucket_name}' not accessible: {e}")
        
        return self._s3_client

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        user_id: UUID,
        storefront_id: UUID,
        product_id: Optional[UUID] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 with proper organization and validation
        
        Args:
            file_data: File binary data
            filename: Original filename
            user_id: User ID for organization
            storefront_id: Storefront ID for organization
            product_id: Optional product ID for association
            content_type: Optional MIME type (auto-detected if not provided)
            metadata: Optional additional metadata
            
        Returns:
            Dict containing file information (url, key, size, etc.)
            
        Raises:
            FileSizeError: If file exceeds size limits
            FileTypeError: If file type is not allowed
            FileUploadError: If upload fails
        """
        try:
            # Reset file pointer to beginning
            file_data.seek(0)
            file_content = file_data.read()
            file_size = len(file_content)
            
            # Validate file size
            if file_size > self.MAX_FILE_SIZE:
                raise FileSizeError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)")
            
            if file_size == 0:
                raise FileSizeError("File is empty")
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Validate file type
            file_extension = Path(filename).suffix.lower()
            if not self._is_allowed_file_type(content_type, file_extension):
                raise FileTypeError(f"File type '{content_type}' with extension '{file_extension}' is not allowed")
            
            # Generate unique file key with proper organization
            file_key = self._generate_file_key(filename, user_id, storefront_id, product_id)
            
            # Calculate file hash for integrity
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Prepare metadata
            file_metadata = {
                'user_id': str(user_id),
                'storefront_id': str(storefront_id),
                'original_filename': filename,
                'file_size': str(file_size),
                'file_hash': file_hash,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': content_type
            }
            
            if product_id:
                file_metadata['product_id'] = str(product_id)
            
            if metadata:
                file_metadata.update(metadata)
            
            # Upload to S3
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': file_key,
                'Body': file_content,
                'ContentType': content_type,
                'Metadata': file_metadata,
                'ServerSideEncryption': 'AES256',  # Encrypt at rest
                'StorageClass': 'STANDARD'  # Use standard storage for digital products
            }
            
            self.s3_client.put_object(**upload_args)
            
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"
            
            logger.info(f"✅ File uploaded successfully: {filename} -> {file_key}")
            
            return {
                'file_key': file_key,
                'file_url': file_url,
                'filename': filename,
                'file_size': file_size,
                'content_type': content_type,
                'file_hash': file_hash,
                'bucket': self.bucket_name,
                'metadata': file_metadata
            }
            
        except (FileSizeError, FileTypeError) as e:
            logger.warning(f"⚠️ File validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
            raise FileUploadError(f"Failed to upload file: {e}")

    async def generate_download_url(
        self,
        file_key: str,
        expiration_seconds: int = 3600,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a secure, time-limited download URL for a file
        
        Args:
            file_key: S3 file key
            expiration_seconds: URL expiration time in seconds (default: 1 hour)
            filename: Optional filename for download (sets Content-Disposition)
            
        Returns:
            Pre-signed download URL
            
        Raises:
            FileNotFoundError: If file doesn't exist
            FileStorageError: If URL generation fails
        """
        try:
            # Check if file exists
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise FileNotFoundError(f"File not found: {file_key}")
                raise
            
            # Prepare parameters for pre-signed URL
            params = {
                'Bucket': self.bucket_name,
                'Key': file_key
            }
            
            # Add Content-Disposition if filename provided
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            # Generate pre-signed URL
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration_seconds
            )
            
            logger.info(f"✅ Download URL generated for: {file_key} (expires in {expiration_seconds}s)")
            return download_url
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to generate download URL for {file_key}: {e}")
            raise FileStorageError(f"Failed to generate download URL: {e}")

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            file_key: S3 file key to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            FileNotFoundError: If file doesn't exist
            FileStorageError: If deletion fails
        """
        try:
            # Check if file exists first
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise FileNotFoundError(f"File not found: {file_key}")
                raise
            
            # Delete the file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            
            logger.info(f"✅ File deleted successfully: {file_key}")
            return True
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to delete file {file_key}: {e}")
            raise FileStorageError(f"Failed to delete file: {e}")

    async def get_file_metadata(self, file_key: str) -> Dict[str, Any]:
        """
        Get metadata for a file
        
        Args:
            file_key: S3 file key
            
        Returns:
            File metadata dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            FileStorageError: If metadata retrieval fails
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            
            metadata = {
                'file_key': file_key,
                'content_type': response.get('ContentType', 'unknown'),
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'metadata': response.get('Metadata', {})
            }
            
            return metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File not found: {file_key}")
            raise FileStorageError(f"Failed to get file metadata: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to get metadata for {file_key}: {e}")
            raise FileStorageError(f"Failed to get file metadata: {e}")

    async def list_user_files(
        self,
        user_id: UUID,
        storefront_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files for a user, optionally filtered by storefront/product
        
        Args:
            user_id: User ID
            storefront_id: Optional storefront filter
            product_id: Optional product filter
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            # Build prefix for listing
            prefix = f"users/{user_id}/"
            if storefront_id:
                prefix += f"storefronts/{storefront_id}/"
                if product_id:
                    prefix += f"products/{product_id}/"
            
            # List objects with prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                try:
                    # Get detailed metadata for each file
                    file_metadata = await self.get_file_metadata(obj['Key'])
                    files.append(file_metadata)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get metadata for {obj['Key']}: {e}")
                    continue
            
            logger.info(f"✅ Listed {len(files)} files for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list files for user {user_id}: {e}")
            raise FileStorageError(f"Failed to list user files: {e}")

    async def calculate_storage_usage(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calculate storage usage for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Storage usage statistics
        """
        try:
            prefix = f"users/{user_id}/"
            
            total_size = 0
            file_count = 0
            
            # Use paginator to handle large numbers of files
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    total_size += obj['Size']
                    file_count += 1
            
            return {
                'user_id': str(user_id),
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'storage_limit_gb': round(self.MAX_FILE_SIZE / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate storage usage for user {user_id}: {e}")
            raise FileStorageError(f"Failed to calculate storage usage: {e}")

    def _generate_file_key(
        self,
        filename: str,
        user_id: UUID,
        storefront_id: UUID,
        product_id: Optional[UUID] = None
    ) -> str:
        """
        Generate a unique S3 key for file organization
        
        Organization structure:
        users/{user_id}/storefronts/{storefront_id}/[products/{product_id}/]{timestamp}_{uuid}_{filename}
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Generate unique identifier
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8]
        
        # Build key path
        key_parts = [
            "users", str(user_id),
            "storefronts", str(storefront_id)
        ]
        
        if product_id:
            key_parts.extend(["products", str(product_id)])
        
        # Add filename with timestamp and unique ID
        final_filename = f"{timestamp}_{unique_id}_{safe_filename}"
        key_parts.append(final_filename)
        
        return "/".join(key_parts)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for S3 storage"""
        # Remove any path components
        filename = Path(filename).name
        
        # Replace problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = "".join(c if c in safe_chars else "_" for c in filename)
        
        # Ensure it's not too long (S3 key limit is 1024 chars, but we want reasonable filenames)
        if len(sanitized) > 100:
            name_part = sanitized[:80]
            ext_part = sanitized[-20:] if "." in sanitized[-20:] else ""
            sanitized = name_part + ext_part
        
        return sanitized

    def _is_allowed_file_type(self, content_type: str, file_extension: str) -> bool:
        """Check if file type and extension are allowed"""
        # Check MIME type
        if content_type in self.ALLOWED_MIME_TYPES:
            return True
        
        # Check file extension
        if file_extension in self.ALLOWED_EXTENSIONS:
            return True
        
        # Special case for octet-stream with allowed extensions
        if content_type == 'application/octet-stream' and file_extension in self.ALLOWED_EXTENSIONS:
            return True
        
        return False

    @staticmethod
    def get_human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on S3 service
        
        Returns:
            Health status information
        """
        try:
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Test basic operations (list with limit to avoid performance issues)
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            
            return {
                'status': 'healthy',
                'bucket': self.bucket_name,
                'region': settings.aws_region,
                'max_file_size': self.get_human_readable_size(self.MAX_FILE_SIZE),
                'allowed_file_types': len(self.ALLOWED_MIME_TYPES),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ S3 health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global instance for dependency injection (lazy initialization)
_file_storage_service = None


def get_file_storage_service() -> FileStorageService:
    """
    Dependency injection function for file storage service with lazy initialization
    
    Returns:
        FileStorageService instance
        
    Raises:
        FileStorageError: If service is not available or cannot be initialized
    """
    global _file_storage_service
    
    if not settings.aws_configured:
        raise FileStorageError("File storage service is not available - AWS S3 not configured")
    
    if _file_storage_service is None:
        try:
            _file_storage_service = FileStorageService()
        except Exception as e:
            raise FileStorageError(f"Failed to initialize file storage service: {e}")
    
    return _file_storage_service