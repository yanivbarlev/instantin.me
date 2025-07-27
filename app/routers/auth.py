from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Any, Dict
import logging

from app.database import get_async_session
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserLogin, 
    UserResponse, 
    UserProfile,
    UserUpdate,
    TokenResponse,
    EmailVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.auth.jwt import (
    create_user_token,
    create_email_verification_token,
    create_password_reset_token,
    verify_email_verification_token,
    verify_password_reset_token
)
from app.auth.password import (
    create_user_password,
    authenticate_user_password,
    hash_password
)
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_user
)
from app.config import settings
from app.utils.helpers import generate_short_id
from app.services.email import send_verification_email, send_password_reset_email, send_welcome_email

logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Authorization failed"},
        422: {"description": "Validation error"}
    }
)


@router.post(
    "/register", 
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Strong password (8+ chars, mixed case, digits)
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    
    Returns JWT token and user information.
    """
    try:
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )
        
        # Create password hash with validation
        try:
            hashed_password = create_user_password(user_data.password)
        except ValueError as e:
            logger.warning(f"Password validation failed for {user_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Create new user
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_verified=False,  # Email verification required
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Create access token
        access_token = create_user_token(new_user.id, new_user.email)
        
        # Create user response
        user_response = UserResponse(
            id=new_user.id,
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            avatar_url=new_user.avatar_url,
            is_verified=new_user.is_verified,
            is_active=new_user.is_active,
            has_google_oauth=new_user.has_google_oauth,
            stripe_connected=new_user.stripe_connected,
            paypal_connected=new_user.paypal_connected,
            can_receive_payments=new_user.can_receive_payments,
            full_name=new_user.full_name,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            last_login_at=new_user.last_login_at
        )
        
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user with email and password"
)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Authenticate user and return access token.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT token and user information.
    """
    try:
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == user_credentials.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password and check for hash update
        is_authenticated, new_hash = authenticate_user_password(
            user_credentials.password, 
            user.hashed_password
        )
        
        if not is_authenticated:
            logger.warning(f"Failed login attempt for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update password hash if needed
        if new_hash:
            user.hashed_password = new_hash
            logger.info(f"Updated password hash for user: {user.email}")
        
        # Update login tracking
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        
        await db.commit()
        await db.refresh(user)
        
        # Create access token
        access_token = create_user_token(user.id, user.email)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            is_active=user.is_active,
            has_google_oauth=user.has_google_oauth,
            stripe_connected=user.stripe_connected,
            paypal_connected=user.paypal_connected,
            can_receive_payments=user.can_receive_payments,
            full_name=user.full_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )
        
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Get detailed profile information for the authenticated user"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get detailed profile information for the authenticated user.
    
    Requires valid JWT token in Authorization header.
    Returns comprehensive user profile data.
    """
    try:
        user_profile = UserProfile(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            avatar_url=current_user.avatar_url,
            is_verified=current_user.is_verified,
            is_active=current_user.is_active,
            has_google_oauth=current_user.has_google_oauth,
            stripe_connected=current_user.stripe_connected,
            paypal_connected=current_user.paypal_connected,
            can_receive_payments=current_user.can_receive_payments,
            login_count=current_user.login_count,
            full_name=current_user.full_name,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login_at=current_user.last_login_at
        )
        
        logger.info(f"Profile retrieved for user: {current_user.email}")
        return user_profile
        
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update profile information for the authenticated user"
)
async def update_current_user_profile(
    user_updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """
    Update profile information for the authenticated user.
    
    - **first_name**: Updated first name (optional)
    - **last_name**: Updated last name (optional)  
    - **avatar_url**: Updated avatar URL (optional)
    
    Requires valid JWT token and active account.
    """
    try:
        # Update user fields if provided
        update_data = user_updates.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        # Create response
        user_response = UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            avatar_url=current_user.avatar_url,
            is_verified=current_user.is_verified,
            is_active=current_user.is_active,
            has_google_oauth=current_user.has_google_oauth,
            stripe_connected=current_user.stripe_connected,
            paypal_connected=current_user.paypal_connected,
            can_receive_payments=current_user.can_receive_payments,
            full_name=current_user.full_name,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login_at=current_user.last_login_at
        )
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return user_response
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post(
    "/send-verification",
    summary="Send email verification",
    description="Send email verification token to user's email address"
)
async def send_email_verification(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Send email verification token to user's email address.
    
    Requires authenticated user with unverified email.
    """
    try:
        if current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        # Create verification token
        verification_token = create_email_verification_token(current_user.email)
        
        # Send verification email
        email_sent = await send_verification_email(
            email=current_user.email,
            token=verification_token,
            first_name=current_user.first_name
        )
        
        if not email_sent:
            logger.error(f"Failed to send verification email to: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        logger.info(f"Email verification sent successfully to: {current_user.email}")
        
        return {
            "message": "Verification email sent successfully",
            "email": current_user.email,
            # In development, return token for testing
            "verification_token": verification_token if settings.is_development else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post(
    "/verify-email",
    summary="Verify email address",
    description="Verify user's email address using verification token"
)
async def verify_email_address(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Verify user's email address using verification token.
    
    - **token**: Email verification token received via email
    
    Marks user's email as verified.
    """
    try:
        # Verify token and get email
        email = verify_email_verification_token(verification_data.token)
        
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Email verification attempted for non-existent user: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        if user.is_verified:
            return {
                "message": "Email is already verified",
                "email": user.email
            }
        
        # Mark email as verified
        user.is_verified = True
        await db.commit()
        
        # Send welcome email
        await send_welcome_email(
            email=user.email,
            first_name=user.first_name
        )
        
        logger.info(f"Email verified successfully for user: {user.email}")
        
        return {
            "message": "Email verified successfully",
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post(
    "/password-reset",
    summary="Request password reset",
    description="Send password reset token to user's email address"
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Send password reset token to user's email address.
    
    - **email**: User's email address
    
    Always returns success message for security (doesn't reveal if email exists).
    """
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == reset_request.email)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            # Create password reset token
            reset_token = create_password_reset_token(user.email)
            
            # Send password reset email
            email_sent = await send_password_reset_email(
                email=user.email,
                token=reset_token,
                first_name=user.first_name
            )
            
            if email_sent:
                logger.info(f"Password reset email sent to: {user.email}")
            else:
                logger.error(f"Failed to send password reset email to: {user.email}")
            
            # In development, return token for testing
            if settings.is_development:
                return {
                    "message": "Password reset email sent",
                    "email": reset_request.email,
                    "reset_token": reset_token  # Remove in production
                }
        else:
            # Log attempt for non-existent or inactive user
            logger.warning(f"Password reset requested for non-existent/inactive user: {reset_request.email}")
        
        # Always return same message for security
        return {
            "message": "If an account with that email exists, a password reset link has been sent",
            "email": reset_request.email
        }
        
    except Exception as e:
        logger.error(f"Error processing password reset request: {e}")
        # Return generic message to avoid revealing errors
        return {
            "message": "If an account with that email exists, a password reset link has been sent",
            "email": reset_request.email
        }


@router.post(
    "/password-reset-confirm",
    summary="Confirm password reset",
    description="Reset user's password using reset token"
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Reset user's password using reset token.
    
    - **token**: Password reset token received via email
    - **new_password**: New password (must meet strength requirements)
    
    Resets the user's password and invalidates the token.
    """
    try:
        # Verify token and get email
        email = verify_password_reset_token(reset_data.token)
        
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            logger.warning(f"Password reset attempted for non-existent/inactive user: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Create new password hash with validation
        try:
            new_hashed_password = create_user_password(reset_data.new_password)
        except ValueError as e:
            logger.warning(f"Password validation failed during reset for {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Update user's password
        user.hashed_password = new_hashed_password
        await db.commit()
        
        logger.info(f"Password reset successfully for user: {user.email}")
        
        return {
            "message": "Password reset successfully",
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.delete(
    "/account",
    summary="Delete user account",
    description="Permanently delete the authenticated user's account"
)
async def delete_user_account(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Permanently delete the authenticated user's account.
    
    Requires verified user account.
    This action cannot be undone.
    """
    try:
        user_email = current_user.email
        user_id = current_user.id
        
        # Delete user from database
        await db.delete(current_user)
        await db.commit()
        
        logger.info(f"User account deleted: {user_email} (ID: {user_id})")
        
        return {
            "message": "Account deleted successfully",
            "email": user_email
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        ) 