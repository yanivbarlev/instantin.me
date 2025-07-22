import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import unicodedata
import os
from decimal import Decimal, ROUND_HALF_UP


# ===== STRING UTILITIES =====

def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: Input text to convert to slug
        max_length: Maximum length of the slug
        
    Returns:
        URL-friendly slug string
    """
    if not text:
        return ""
    
    # Convert to lowercase and normalize unicode
    text = unicodedata.normalize('NFKD', text.lower())
    
    # Remove non-alphanumeric characters except spaces and hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Replace spaces and multiple hyphens with single hyphen
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def clean_url(url: str) -> str:
    """
    Clean and normalize a URL.
    
    Args:
        url: Input URL to clean
        
    Returns:
        Cleaned URL with proper formatting
    """
    if not url:
        return ""
    
    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: Input URL
        
    Returns:
        Domain name without protocol or path
    """
    try:
        parsed = urlparse(clean_url(url))
        return parsed.netloc.lower()
    except Exception:
        return ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Ensure it's not too long
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"


# ===== VALIDATION UTILITIES =====

def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL format is valid
    """
    if not url:
        return False
    
    try:
        result = urlparse(clean_url(url))
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_slug(slug: str) -> bool:
    """
    Validate slug format for storefronts.
    
    Args:
        slug: Slug to validate
        
    Returns:
        True if slug format is valid
    """
    if not slug:
        return False
    
    # Check length (3-50 characters)
    if len(slug) < 3 or len(slug) > 50:
        return False
    
    # Check format: lowercase alphanumeric and hyphens only
    pattern = r'^[a-z0-9-]+$'
    if not re.match(pattern, slug):
        return False
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False
    
    # Cannot have consecutive hyphens
    if '--' in slug:
        return False
    
    return True


def validate_file_size(file_size: int, max_size_gb: int = 5) -> bool:
    """
    Validate file size against maximum limit.
    
    Args:
        file_size: File size in bytes
        max_size_gb: Maximum size in GB
        
    Returns:
        True if file size is within limit
    """
    max_size_bytes = max_size_gb * 1024 * 1024 * 1024  # Convert GB to bytes
    return file_size <= max_size_bytes


# ===== DATE/TIME UTILITIES =====

def utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object to format
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    
    # Ensure timezone is UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference.
    
    Args:
        dt: Datetime to compare against now
        
    Returns:
        Human-readable time difference (e.g., "2 hours ago")
    """
    if not dt:
        return "unknown"
    
    now = utc_now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:  # 30 days
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return format_datetime(dt, "%B %d, %Y")


# ===== RESPONSE UTILITIES =====

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Standardized success response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": utc_now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def error_response(message: str, code: str = "ERROR", details: Any = None) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        code: Error code
        details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": utc_now().isoformat()
        }
    }
    
    if details is not None:
        response["error"]["details"] = details
    
    return response


def paginated_response(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """
    Create paginated response.
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Response message
        
    Returns:
        Paginated response with metadata
    """
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": utc_now().isoformat()
    }


# ===== SECURITY UTILITIES =====

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Length of the token
        
    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(length)


def mask_email(email: str) -> str:
    """
    Mask email address for privacy.
    
    Args:
        email: Email address to mask
        
    Returns:
        Masked email address (e.g., "u***@example.com")
    """
    if not email or '@' not in email:
        return email
    
    username, domain = email.split('@', 1)
    
    if len(username) <= 2:
        masked_username = username[0] + '*'
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"


# ===== FILE UTILITIES =====

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (without dot)
    """
    if not filename:
        return ""
    
    return os.path.splitext(filename)[1].lstrip('.').lower()


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate unique filename with timestamp.
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix for the filename
        
    Returns:
        Unique filename with timestamp
    """
    name, ext = os.path.splitext(sanitize_filename(original_filename))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate random suffix for extra uniqueness
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    
    unique_name = f"{prefix}_{timestamp}_{random_suffix}_{name}" if prefix else f"{timestamp}_{random_suffix}_{name}"
    
    return f"{unique_name}{ext}"


# ===== BUSINESS LOGIC UTILITIES =====

def calculate_platform_fee(amount: Union[int, float, Decimal], fee_percentage: float = 2.9) -> Decimal:
    """
    Calculate platform fee for transactions.
    
    Args:
        amount: Transaction amount
        fee_percentage: Fee percentage (default 2.9%)
        
    Returns:
        Platform fee amount
    """
    if not amount or amount <= 0:
        return Decimal('0.00')
    
    amount_decimal = Decimal(str(amount))
    fee_decimal = Decimal(str(fee_percentage / 100))
    
    fee = amount_decimal * fee_decimal
    
    # Round to 2 decimal places
    return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def format_price(amount: Union[int, float, Decimal], currency: str = "USD") -> str:
    """
    Format price for display.
    
    Args:
        amount: Price amount
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    if not amount:
        return f"$0.00"
    
    amount_decimal = Decimal(str(amount))
    
    # Format based on currency
    if currency.upper() == "USD":
        return f"${amount_decimal:.2f}"
    else:
        return f"{amount_decimal:.2f} {currency.upper()}"


def generate_short_id(length: int = 8) -> str:
    """
    Generate short ID for public-facing identifiers.
    
    Args:
        length: Length of the ID
        
    Returns:
        Short alphanumeric ID
    """
    # Use only uppercase letters and numbers for readability
    alphabet = string.ascii_uppercase + string.digits
    
    # Remove potentially confusing characters
    alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ===== HELPER CONSTANTS =====

# Common file extensions for different product types
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'aac'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz'}

# Platform configuration
DEFAULT_PLATFORM_FEE_PERCENTAGE = 2.9
MAX_FILE_SIZE_GB = 5
MIN_SLUG_LENGTH = 3
MAX_SLUG_LENGTH = 50 