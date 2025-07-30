from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID
from io import BytesIO

from app.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.config import settings
try:
    from app.services.file_storage import (
        get_file_storage_service, 
        FileStorageService,
        FileStorageError,
        FileUploadError,
        FileSizeError,
        FileTypeError
    )
    FILE_STORAGE_AVAILABLE = True
except Exception as e:
    FILE_STORAGE_AVAILABLE = False
    print(f"⚠️  File storage not available: {e}")
from app.services.product import ProductService
from app.utils.exceptions import (
    ProductNotFoundError,
    StorefrontNotFoundError,
    UnauthorizedError
)

# Initialize router
router = APIRouter(prefix="/upload", tags=["file-upload"])


def check_file_storage_available():
    """Check if file storage is available and raise appropriate error if not"""
    if not FILE_STORAGE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage service is not available - AWS S3 not configured"
        )
    if not settings.aws_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage service is not available - AWS S3 credentials not configured"
        )


@router.post(
    "/digital-file",
    summary="Upload digital file",
    description="Upload a digital file for products with 5GB size limit"
)
async def upload_digital_file(
    file: UploadFile = File(..., description="Digital file to upload (max 5GB)"),
    storefront_id: UUID = Form(..., description="Storefront ID"),
    product_id: Optional[UUID] = Form(None, description="Optional product ID to associate file with"),
    description: Optional[str] = Form(None, max_length=500, description="Optional file description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Upload a digital file for use in digital products.
    
    **Form Parameters:**
    - **file**: Digital file to upload (required)
    - **storefront_id**: ID of the storefront (must be owned by user)
    - **product_id**: Optional product ID to associate file with
    - **description**: Optional description for the file
    
    **File Requirements:**
    - Maximum size: 5GB
    - Allowed types: Documents, images, audio, video, archives, software, etc.
    - See documentation for complete list of supported file types
    
    **Security:**
    - User must own the specified storefront
    - Files are encrypted at rest with AES256
    - Secure, organized storage by user/storefront/product
    
    **Returns:**
    - File information including secure URL and metadata
    - File can be associated with digital products
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        # Validate storefront ownership
        await _validate_storefront_ownership(db, storefront_id, current_user.id)
        
        # Validate product ownership if product_id provided
        if product_id:
            await _validate_product_ownership(db, product_id, current_user.id)
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Convert UploadFile to BytesIO for file storage service
        file_content = await file.read()
        file_data = BytesIO(file_content)
        
        # Prepare metadata
        metadata = {
            "uploaded_by": str(current_user.id),
            "original_size": str(len(file_content))
        }
        
        if description:
            metadata["description"] = description
        
        # Upload file to S3
        upload_result = await file_storage.upload_file(
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            storefront_id=storefront_id,
            product_id=product_id,
            content_type=file.content_type,
            metadata=metadata
        )
        
        # Generate initial download URL (1 hour expiration)
        download_url = await file_storage.generate_download_url(
            file_key=upload_result["file_key"],
            expiration_seconds=3600,
            filename=file.filename
        )
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "File uploaded successfully",
            "file": {
                "file_key": upload_result["file_key"],
                "file_url": upload_result["file_url"],  # Direct S3 URL (not pre-signed)
                "download_url": download_url,  # Pre-signed URL for immediate download
                "filename": upload_result["filename"],
                "file_size": upload_result["file_size"],
                "file_size_human": file_storage.get_human_readable_size(upload_result["file_size"]),
                "content_type": upload_result["content_type"],
                "file_hash": upload_result["file_hash"],
                "storefront_id": str(storefront_id),
                "product_id": str(product_id) if product_id else None,
                "description": description
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data
        )
        
    except FileSizeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {str(e)}"
        )
    except FileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {str(e)}"
        )
    except FileUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
    except FileStorageError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/multiple-files",
    summary="Upload multiple digital files",
    description="Upload multiple digital files in a single request"
)
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="List of digital files to upload"),
    storefront_id: UUID = Form(..., description="Storefront ID"),
    product_id: Optional[UUID] = Form(None, description="Optional product ID to associate files with"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Upload multiple digital files in a single request.
    
    **Form Parameters:**
    - **files**: List of digital files to upload (required)
    - **storefront_id**: ID of the storefront (must be owned by user)
    - **product_id**: Optional product ID to associate all files with
    
    **Limits:**
    - Maximum 10 files per request
    - Each file maximum 5GB
    - Total request size limited by server configuration
    
    **Returns:**
    - Array of upload results with success/failure status for each file
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        # Validate request limits
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 files allowed per request"
            )
        
        # Validate storefront ownership
        await _validate_storefront_ownership(db, storefront_id, current_user.id)
        
        # Validate product ownership if product_id provided
        if product_id:
            await _validate_product_ownership(db, product_id, current_user.id)
        
        upload_results = []
        
        for i, file in enumerate(files):
            try:
                if not file.filename:
                    upload_results.append({
                        "index": i,
                        "filename": "unknown",
                        "success": False,
                        "error": "Filename is required"
                    })
                    continue
                
                # Convert UploadFile to BytesIO
                file_content = await file.read()
                file_data = BytesIO(file_content)
                
                # Upload file
                upload_result = await file_storage.upload_file(
                    file_data=file_data,
                    filename=file.filename,
                    user_id=current_user.id,
                    storefront_id=storefront_id,
                    product_id=product_id,
                    content_type=file.content_type,
                    metadata={
                        "uploaded_by": str(current_user.id),
                        "batch_upload": "true",
                        "batch_index": str(i)
                    }
                )
                
                upload_results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": True,
                    "file_key": upload_result["file_key"],
                    "file_size": upload_result["file_size"],
                    "file_size_human": file_storage.get_human_readable_size(upload_result["file_size"]),
                    "content_type": upload_result["content_type"]
                })
                
            except Exception as e:
                upload_results.append({
                    "index": i,
                    "filename": file.filename if file.filename else "unknown",
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate summary
        successful_uploads = [r for r in upload_results if r["success"]]
        failed_uploads = [r for r in upload_results if not r["success"]]
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED if successful_uploads else status.HTTP_400_BAD_REQUEST,
            content={
                "success": len(successful_uploads) > 0,
                "message": f"Uploaded {len(successful_uploads)} of {len(files)} files successfully",
                "summary": {
                    "total_files": len(files),
                    "successful": len(successful_uploads),
                    "failed": len(failed_uploads)
                },
                "results": upload_results
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get(
    "/files",
    summary="List uploaded files",
    description="Get list of uploaded files for user"
)
async def list_uploaded_files(
    storefront_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Get list of uploaded files for the authenticated user.
    
    **Query Parameters:**
    - **storefront_id**: Filter by storefront (optional)
    - **product_id**: Filter by product (optional)
    - **limit**: Maximum number of files to return (default: 50, max: 100)
    
    **Returns:**
    - List of file metadata including URLs and properties
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # Get files from storage service
        files = await file_storage.list_user_files(
            user_id=current_user.id,
            storefront_id=storefront_id,
            product_id=product_id,
            limit=limit
        )
        
        # Enhance file data with download URLs
        enhanced_files = []
        for file_metadata in files:
            try:
                # Generate download URL for each file
                download_url = await file_storage.generate_download_url(
                    file_key=file_metadata["file_key"],
                    expiration_seconds=3600,
                    filename=file_metadata.get("metadata", {}).get("original_filename")
                )
                
                enhanced_file = {
                    "file_key": file_metadata["file_key"],
                    "filename": file_metadata.get("metadata", {}).get("original_filename", "unknown"),
                    "file_size": file_metadata["content_length"],
                    "file_size_human": file_storage.get_human_readable_size(file_metadata["content_length"]),
                    "content_type": file_metadata["content_type"],
                    "last_modified": file_metadata["last_modified"].isoformat() if file_metadata.get("last_modified") else None,
                    "download_url": download_url,
                    "metadata": file_metadata.get("metadata", {})
                }
                enhanced_files.append(enhanced_file)
                
            except Exception as e:
                # Skip files that can't generate download URLs
                continue
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "files": enhanced_files,
                "total_files": len(enhanced_files),
                "limit": limit
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@router.get(
    "/storage-usage",
    summary="Get storage usage",
    description="Get storage usage statistics for user"
)
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Get storage usage statistics for the authenticated user.
    
    **Returns:**
    - Total files count
    - Total storage used (bytes, MB, GB)
    - Storage limit information
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        usage_stats = await file_storage.calculate_storage_usage(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "storage_usage": usage_stats
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage usage: {str(e)}"
        )


@router.delete(
    "/files/{file_key:path}",
    summary="Delete uploaded file",
    description="Delete an uploaded file"
)
async def delete_uploaded_file(
    file_key: str,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Delete an uploaded file.
    
    **Path Parameters:**
    - **file_key**: S3 file key to delete
    
    **Security:**
    - Only the file owner can delete their files
    - File key must belong to the authenticated user
    
    **Returns:**
    - Success confirmation or error details
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        # Validate file ownership by checking if it's in user's directory
        if not file_key.startswith(f"users/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this file"
            )
        
        # Delete file
        await file_storage.delete_file(file_key)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "File deleted successfully",
                "file_key": file_key
            }
        )
        
    except FileStorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get(
    "/download/{file_key:path}",
    summary="Generate download URL",
    description="Generate a secure download URL for a file"
)
async def generate_download_url(
    file_key: str,
    expiration_hours: int = 1,
    filename: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
) -> JSONResponse:
    """
    Generate a secure, time-limited download URL for a file.
    
    **Path Parameters:**
    - **file_key**: S3 file key
    
    **Query Parameters:**
    - **expiration_hours**: URL expiration time in hours (default: 1, max: 24)
    - **filename**: Custom filename for download (optional)
    
    **Security:**
    - Only the file owner can generate download URLs
    - File key must belong to the authenticated user
    
    **Returns:**
    - Pre-signed download URL with expiration info
    """
    try:
        # Check if file storage is available
        check_file_storage_available()
        
        # Validate file ownership
        if not file_key.startswith(f"users/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Validate expiration time
        if expiration_hours > 24:
            expiration_hours = 24
        elif expiration_hours < 1:
            expiration_hours = 1
        
        expiration_seconds = expiration_hours * 3600
        
        # Generate download URL
        download_url = await file_storage.generate_download_url(
            file_key=file_key,
            expiration_seconds=expiration_seconds,
            filename=filename
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "download_url": download_url,
                "file_key": file_key,
                "expiration_hours": expiration_hours,
                "filename": filename
            }
        )
        
    except FileStorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Helper functions
async def _validate_storefront_ownership(db: AsyncSession, storefront_id: UUID, user_id: UUID):
    """Validate that user owns the specified storefront"""
    from app.models.storefront import Storefront
    from sqlalchemy import select
    
    result = await db.execute(
        select(Storefront).where(
            Storefront.id == storefront_id,
            Storefront.user_id == user_id
        )
    )
    storefront = result.scalar_one_or_none()
    
    if not storefront:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storefront not found or not owned by user"
        )


async def _validate_product_ownership(db: AsyncSession, product_id: UUID, user_id: UUID):
    """Validate that user owns the specified product (via storefront)"""
    from app.models.product import Product
    from app.models.storefront import Storefront
    from sqlalchemy import select
    
    result = await db.execute(
        select(Product)
        .join(Storefront)
        .where(
            Product.id == product_id,
            Storefront.user_id == user_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or not owned by user"
        )