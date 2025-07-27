from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse
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
    validate_password_strength
)
from app.services.email import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email
)
from app.config import settings

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors"""
    
    def __init__(self, message: str, error_code: str = "AUTH_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthService:
    """
    Authentication service for InstantIn.me platform.
    Contains business logic for user registration, login, verification, and account management.
    """
    
    async def register_user(
        self,
        user_data: UserCreate,
        db: AsyncSession,
        send_verification: bool = True
    ) -> Tuple[User, str]:
        """
        Register a new user account.
        
        Args:
            user_data: User registration data
            db: Database session
            send_verification: Whether to send verification email
            
        Returns:
            Tuple of (User instance, access_token)
            
        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Check if user already exists
            existing_user = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                logger.warning(f"Registration attempt with existing email: {user_data.email}")
                raise AuthenticationError(
                    "Email address is already registered",
                    "EMAIL_EXISTS"
                )
            
            # Validate password strength
            password_validation = validate_password_strength(user_data.password)
            if not password_validation["is_valid"]:
                error_msg = "; ".join(password_validation["errors"])
                logger.warning(f"Password validation failed for {user_data.email}: {error_msg}")
                raise AuthenticationError(
                    f"Password validation failed: {error_msg}",
                    "WEAK_PASSWORD"
                )
            
            # Create password hash
            hashed_password = create_user_password(user_data.password)
            
            # Create new user
            new_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_verified=False,
                is_active=True
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # Send verification email if requested
            if send_verification:
                await self._send_verification_email(new_user)
            
            # Create access token
            access_token = create_user_token(new_user.id, new_user.email)
            
            logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
            
            return new_user, access_token
            
        except AuthenticationError:
            await db.rollback()
            raise
        except IntegrityError:
            await db.rollback()
            logger.error(f"Database integrity error during registration for: {user_data.email}")
            raise AuthenticationError(
                "Email address is already registered",
                "EMAIL_EXISTS"
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error during registration: {e}")
            raise AuthenticationError(
                "Registration failed. Please try again.",
                "REGISTRATION_ERROR"
            )
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        db: AsyncSession
    ) -> Tuple[User, str]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            db: Database session
            
        Returns:
            Tuple of (User instance, access_token)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Get user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise AuthenticationError(
                    "Invalid email or password",
                    "INVALID_CREDENTIALS"
                )
            
            if not user.is_active:
                logger.warning(f"Login attempt for inactive user: {email}")
                raise AuthenticationError(
                    "Account is not active",
                    "ACCOUNT_INACTIVE"
                )
            
            if user.is_suspended:
                logger.warning(f"Login attempt for suspended user: {email}")
                raise AuthenticationError(
                    "Account is suspended",
                    "ACCOUNT_SUSPENDED"
                )
            
            # Verify password
            is_authenticated, new_hash = authenticate_user_password(password, user.hashed_password)
            
            if not is_authenticated:
                logger.warning(f"Failed login attempt for user: {email}")
                raise AuthenticationError(
                    "Invalid email or password",
                    "INVALID_CREDENTIALS"
                )
            
            # Update password hash if needed
            if new_hash:
                user.hashed_password = new_hash
                logger.info(f"Updated password hash for user: {email}")
            
            # Update login tracking
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            
            await db.commit()
            await db.refresh(user)
            
            # Create access token
            access_token = create_user_token(user.id, user.email)
            
            logger.info(f"User authenticated successfully: {email} (ID: {user.id})")
            
            return user, access_token
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError(
                "Authentication failed. Please try again.",
                "AUTH_ERROR"
            )
    
    async def verify_user_email(
        self,
        verification_token: str,
        db: AsyncSession
    ) -> User:
        """
        Verify user's email address using verification token.
        
        Args:
            verification_token: JWT verification token
            db: Database session
            
        Returns:
            User instance
            
        Raises:
            AuthenticationError: If verification fails
        """
        try:
            # Verify token and get email
            email = verify_email_verification_token(verification_token)
            
            # Get user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Email verification attempted for non-existent user: {email}")
                raise AuthenticationError(
                    "Invalid verification token",
                    "INVALID_TOKEN"
                )
            
            if user.is_verified:
                logger.info(f"Email already verified for user: {email}")
                return user
            
            # Mark email as verified
            user.is_verified = True
            await db.commit()
            await db.refresh(user)
            
            # Send welcome email
            await send_welcome_email(user.email, user.first_name)
            
            logger.info(f"Email verified successfully for user: {email}")
            
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error during email verification: {e}")
            raise AuthenticationError(
                "Email verification failed",
                "VERIFICATION_ERROR"
            )
    
    async def request_password_reset(
        self,
        email: str,
        db: AsyncSession
    ) -> bool:
        """
        Request password reset for user.
        
        Args:
            email: User's email address
            db: Database session
            
        Returns:
            True if reset email was sent (or user doesn't exist but we don't reveal that)
        """
        try:
            # Get user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if user and user.is_active and not user.is_suspended:
                # Create reset token
                reset_token = create_password_reset_token(user.email)
                
                # Send reset email
                email_sent = await send_password_reset_email(
                    email=user.email,
                    token=reset_token,
                    first_name=user.first_name
                )
                
                if email_sent:
                    logger.info(f"Password reset email sent to: {user.email}")
                else:
                    logger.error(f"Failed to send password reset email to: {user.email}")
                
                return email_sent
            else:
                # Log attempt for non-existent or inactive user
                logger.warning(f"Password reset requested for non-existent/inactive user: {email}")
                # Return True to avoid revealing user existence
                return True
                
        except Exception as e:
            logger.error(f"Error processing password reset request: {e}")
            # Return True to avoid revealing errors
            return True
    
    async def reset_user_password(
        self,
        reset_token: str,
        new_password: str,
        db: AsyncSession
    ) -> User:
        """
        Reset user's password using reset token.
        
        Args:
            reset_token: JWT reset token
            new_password: New password
            db: Database session
            
        Returns:
            User instance
            
        Raises:
            AuthenticationError: If reset fails
        """
        try:
            # Verify token and get email
            email = verify_password_reset_token(reset_token)
            
            # Get user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                logger.warning(f"Password reset attempted for non-existent/inactive user: {email}")
                raise AuthenticationError(
                    "Invalid or expired reset token",
                    "INVALID_TOKEN"
                )
            
            # Validate new password
            password_validation = validate_password_strength(new_password)
            if not password_validation["is_valid"]:
                error_msg = "; ".join(password_validation["errors"])
                logger.warning(f"Password validation failed during reset for {email}: {error_msg}")
                raise AuthenticationError(
                    f"Password validation failed: {error_msg}",
                    "WEAK_PASSWORD"
                )
            
            # Create new password hash
            new_hashed_password = create_user_password(new_password)
            
            # Update user's password
            user.hashed_password = new_hashed_password
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Password reset successfully for user: {user.email}")
            
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error during password reset: {e}")
            raise AuthenticationError(
                "Password reset failed",
                "RESET_ERROR"
            )
    
    async def update_user_profile(
        self,
        user: User,
        update_data: Dict[str, Any],
        db: AsyncSession
    ) -> User:
        """
        Update user profile information.
        
        Args:
            user: User instance
            update_data: Dictionary of fields to update
            db: Database session
            
        Returns:
            Updated user instance
            
        Raises:
            AuthenticationError: If update fails
        """
        try:
            # Update user fields
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Profile updated for user: {user.email}")
            
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise AuthenticationError(
                "Failed to update profile",
                "UPDATE_ERROR"
            )
    
    async def delete_user_account(
        self,
        user: User,
        db: AsyncSession
    ) -> bool:
        """
        Delete user account permanently.
        
        Args:
            user: User instance
            db: Database session
            
        Returns:
            True if deletion successful
            
        Raises:
            AuthenticationError: If deletion fails
        """
        try:
            user_email = user.email
            user_id = user.id
            
            # Delete user from database
            await db.delete(user)
            await db.commit()
            
            logger.info(f"User account deleted: {user_email} (ID: {user_id})")
            
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user account: {e}")
            raise AuthenticationError(
                "Failed to delete account",
                "DELETE_ERROR"
            )
    
    async def resend_verification_email(
        self,
        user: User
    ) -> bool:
        """
        Resend email verification to user.
        
        Args:
            user: User instance
            
        Returns:
            True if email sent successfully
            
        Raises:
            AuthenticationError: If user is already verified
        """
        try:
            if user.is_verified:
                raise AuthenticationError(
                    "Email is already verified",
                    "ALREADY_VERIFIED"
                )
            
            return await self._send_verification_email(user)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error resending verification email: {e}")
            raise AuthenticationError(
                "Failed to send verification email",
                "EMAIL_ERROR"
            )
    
    async def _send_verification_email(self, user: User) -> bool:
        """
        Internal method to send verification email.
        
        Args:
            user: User instance
            
        Returns:
            True if email sent successfully
        """
        try:
            verification_token = create_email_verification_token(user.email)
            
            email_sent = await send_verification_email(
                email=user.email,
                token=verification_token,
                first_name=user.first_name
            )
            
            if email_sent:
                logger.info(f"Verification email sent to: {user.email}")
            else:
                logger.error(f"Failed to send verification email to: {user.email}")
            
            return email_sent
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False
    
    def create_token_response(
        self,
        user: User,
        access_token: str
    ) -> TokenResponse:
        """
        Create token response for API endpoints.
        
        Args:
            user: User instance
            access_token: JWT access token
            
        Returns:
            TokenResponse instance
        """
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
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
    
    async def get_user_stats(self, user: User) -> Dict[str, Any]:
        """
        Get user statistics and account information.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with user statistics
        """
        account_age_days = (datetime.utcnow() - user.created_at).days
        
        return {
            "account_age_days": account_age_days,
            "login_count": user.login_count,
            "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
            "email_verified": user.is_verified,
            "oauth_connected": user.has_google_oauth,
            "payment_methods": {
                "stripe": user.stripe_connected,
                "paypal": user.paypal_connected,
                "can_receive_payments": user.can_receive_payments
            },
            "account_status": {
                "active": user.is_active,
                "suspended": user.is_suspended
            }
        }


# Global auth service instance
auth_service = AuthService()


# Convenience functions for common operations
async def register_new_user(
    user_data: UserCreate,
    db: AsyncSession,
    send_verification: bool = True
) -> Tuple[User, str]:
    """Register a new user account."""
    return await auth_service.register_user(user_data, db, send_verification)


async def authenticate_user_credentials(
    email: str,
    password: str,
    db: AsyncSession
) -> Tuple[User, str]:
    """Authenticate user with email and password."""
    return await auth_service.authenticate_user(email, password, db)


async def verify_email_token(
    verification_token: str,
    db: AsyncSession
) -> User:
    """Verify user's email address."""
    return await auth_service.verify_user_email(verification_token, db)


async def send_password_reset_request(
    email: str,
    db: AsyncSession
) -> bool:
    """Send password reset email."""
    return await auth_service.request_password_reset(email, db)


async def confirm_password_reset(
    reset_token: str,
    new_password: str,
    db: AsyncSession
) -> User:
    """Reset user's password."""
    return await auth_service.reset_user_password(reset_token, new_password, db) 