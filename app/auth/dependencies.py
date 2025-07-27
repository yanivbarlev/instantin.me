from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.database import get_async_session
from app.models.user import User
from app.auth.jwt import get_user_from_token, verify_token
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error for better error handling"""
    
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error for permission checks"""
    
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        credentials: HTTP Bearer credentials from FastAPI security
        
    Returns:
        JWT token string or None if not provided
    """
    if credentials is None:
        return None
    
    if credentials.scheme.lower() != "bearer":
        logger.warning(f"Invalid authentication scheme: {credentials.scheme}")
        return None
    
    return credentials.credentials


async def verify_and_get_user_info(token: str) -> dict:
    """
    Verify JWT token and extract user information.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user_id and email
        
    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        user_info = get_user_from_token(token)
        return user_info
    except HTTPException as e:
        logger.warning(f"Token verification failed: {e.detail}")
        raise AuthenticationError("Invalid or expired token")
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise AuthenticationError("Token verification failed")


async def get_user_by_id(
    user_id: int, 
    db: AsyncSession
) -> Optional[User]:
    """
    Get user from database by ID.
    
    Args:
        user_id: User's database ID
        db: Database session
        
    Returns:
        User model instance or None if not found
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        logger.error(f"Database error when fetching user {user_id}: {e}")
        return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        AuthenticationError: If authentication fails
        
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    if token is None:
        logger.info("No token provided for authentication")
        raise AuthenticationError("Authentication token required")
    
    # Verify token and get user info
    user_info = await verify_and_get_user_info(token)
    
    # Get user from database
    user = await get_user_by_id(user_info["user_id"], db)
    
    if user is None:
        logger.warning(f"User {user_info['user_id']} not found in database")
        raise AuthenticationError("User not found")
    
    logger.info(f"User {user.id} authenticated successfully")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current user and verify they are active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user model instance
        
    Raises:
        AuthorizationError: If user is not active
        
    Usage:
        @app.get("/active-only")
        async def active_route(user: User = Depends(get_current_active_user)):
            return {"message": "You are active!"}
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user {current_user.id} attempted access")
        raise AuthorizationError("Account is not active")
    
    if current_user.is_suspended:
        logger.warning(f"Suspended user {current_user.id} attempted access")
        raise AuthorizationError("Account is suspended")
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    FastAPI dependency to get current user and verify their email is verified.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        Verified user model instance
        
    Raises:
        AuthorizationError: If user's email is not verified
        
    Usage:
        @app.get("/verified-only")
        async def verified_route(user: User = Depends(get_current_verified_user)):
            return {"message": "Your email is verified!"}
    """
    if not current_user.is_verified:
        logger.warning(f"Unverified user {current_user.id} attempted access to verified-only endpoint")
        raise AuthorizationError("Email verification required")
    
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user.
    Returns None if no token is provided or token is invalid.
    
    Args:
        token: JWT token from Authorization header (optional)
        db: Database session
        
    Returns:
        User model instance or None
        
    Usage:
        @app.get("/public-or-private")
        async def mixed_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.full_name}!"}
            return {"message": "Hello anonymous user!"}
    """
    if token is None:
        return None
    
    try:
        # Verify token and get user info
        user_info = await verify_and_get_user_info(token)
        
        # Get user from database
        user = await get_user_by_id(user_info["user_id"], db)
        
        if user is None:
            logger.warning(f"User {user_info['user_id']} not found for optional auth")
            return None
        
        logger.info(f"Optional auth successful for user {user.id}")
        return user
        
    except AuthenticationError:
        logger.info("Optional authentication failed, returning None")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error in optional auth: {e}")
        return None


async def get_user_with_payment_access(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    FastAPI dependency to get user who can access payment features.
    Requires verified user with at least one payment method connected.
    
    Args:
        current_user: User from get_current_verified_user dependency
        
    Returns:
        User with payment access
        
    Raises:
        AuthorizationError: If user cannot access payment features
        
    Usage:
        @app.get("/payment-dashboard")
        async def payment_route(user: User = Depends(get_user_with_payment_access)):
            return {"stripe_connected": user.stripe_connected}
    """
    if not current_user.can_receive_payments:
        logger.warning(f"User {current_user.id} attempted payment access without connected payment method")
        raise AuthorizationError("Payment method required. Please connect Stripe or PayPal.")
    
    return current_user


# Type aliases for common dependency combinations
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user) 
CurrentVerifiedUser = Depends(get_current_verified_user)
OptionalUser = Depends(get_optional_user)
PaymentUser = Depends(get_user_with_payment_access)


# Utility functions for manual authentication (not FastAPI dependencies)
async def authenticate_user_manually(
    token: str, 
    db: AsyncSession
) -> tuple[bool, Optional[User]]:
    """
    Manually authenticate a user without FastAPI dependency injection.
    Useful for WebSocket connections or custom authentication flows.
    
    Args:
        token: JWT token string
        db: Database session
        
    Returns:
        Tuple of (is_authenticated, user_or_none)
    """
    try:
        user_info = await verify_and_get_user_info(token)
        user = await get_user_by_id(user_info["user_id"], db)
        
        if user and user.is_active and not user.is_suspended:
            return True, user
        
        return False, None
        
    except Exception as e:
        logger.warning(f"Manual authentication failed: {e}")
        return False, None


def require_permissions(*required_conditions) -> callable:
    """
    Decorator factory for custom permission checks.
    
    Args:
        required_conditions: Functions that take a User and return bool
        
    Returns:
        FastAPI dependency function
        
    Example:
        def is_admin(user: User) -> bool:
            return user.email.endswith('@instantin.me')
        
        AdminRequired = require_permissions(is_admin)
        
        @app.get("/admin")
        async def admin_route(user: User = Depends(AdminRequired)):
            return {"message": "Admin access granted"}
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        for condition in required_conditions:
            if not condition(current_user):
                condition_name = getattr(condition, '__name__', 'unknown')
                logger.warning(f"User {current_user.id} failed permission check: {condition_name}")
                raise AuthorizationError(f"Required permission not met: {condition_name}")
        
        return current_user
    
    return permission_dependency


# Example permission conditions
def has_stripe_connected(user: User) -> bool:
    """Check if user has Stripe account connected"""
    return user.stripe_connected

def has_paypal_connected(user: User) -> bool:
    """Check if user has PayPal account connected"""
    return user.paypal_connected

def is_instantin_admin(user: User) -> bool:
    """Check if user is an InstantIn.me admin"""
    return user.email.endswith('@instantin.me')


# Pre-built permission dependencies
StripeRequired = require_permissions(has_stripe_connected)
PayPalRequired = require_permissions(has_paypal_connected)
AdminRequired = require_permissions(is_instantin_admin) 