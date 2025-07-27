from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from starlette.config import Config
from starlette.requests import Request
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, Tuple
import logging
import httpx

from app.config import settings
from app.models.user import User
from app.auth.jwt import create_user_token
from app.schemas.user import UserResponse, TokenResponse
from app.services.email import send_welcome_email

logger = logging.getLogger(__name__)


class OAuthConfig:
    """OAuth configuration for InstantIn.me platform"""
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = settings.google_client_id
    GOOGLE_CLIENT_SECRET = settings.google_client_secret
    GOOGLE_REDIRECT_URI = settings.google_redirect_uri
    
    # OAuth scopes
    GOOGLE_SCOPES = ['openid', 'email', 'profile']
    
    # OAuth endpoints
    GOOGLE_AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_ACCESS_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


class OAuthService:
    """
    OAuth service for InstantIn.me platform.
    Handles Google OAuth integration for user authentication.
    """
    
    def __init__(self):
        # Create OAuth instance
        config = Config()
        self.oauth = OAuth(config)
        
        # Register Google OAuth client
        if settings.google_oauth_configured:
            self.google = self.oauth.register(
                name='google',
                client_id=OAuthConfig.GOOGLE_CLIENT_ID,
                client_secret=OAuthConfig.GOOGLE_CLIENT_SECRET,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': ' '.join(OAuthConfig.GOOGLE_SCOPES),
                    'redirect_uri': OAuthConfig.GOOGLE_REDIRECT_URI
                }
            )
            logger.info("✅ Google OAuth client configured successfully")
        else:
            self.google = None
            logger.warning("⚠️ Google OAuth not configured - missing credentials")
    
    def is_google_oauth_available(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return self.google is not None and settings.google_oauth_configured
    
    async def get_google_auth_url(self, request: Request, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            request: FastAPI request object
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
            
        Raises:
            HTTPException: If OAuth is not configured
        """
        if not self.is_google_oauth_available():
            logger.error("Google OAuth authorization attempted but not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not available"
            )
        
        try:
            # Generate authorization URL
            redirect_uri = await self.google.authorize_redirect(
                request, 
                OAuthConfig.GOOGLE_REDIRECT_URI,
                state=state
            )
            
            auth_url = str(redirect_uri.headers.get('location', ''))
            logger.info("Google OAuth authorization URL generated")
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating Google OAuth URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authorization URL"
            )
    
    async def handle_google_callback(
        self,
        request: Request,
        db: AsyncSession
    ) -> Tuple[User, str, bool]:
        """
        Handle Google OAuth callback and create/authenticate user.
        
        Args:
            request: FastAPI request object with OAuth callback data
            db: Database session
            
        Returns:
            Tuple of (User instance, access_token, is_new_user)
            
        Raises:
            HTTPException: If OAuth callback handling fails
        """
        if not self.is_google_oauth_available():
            logger.error("Google OAuth callback attempted but not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not available"
            )
        
        try:
            # Exchange authorization code for access token
            token = await self.google.authorize_access_token(request)
            
            if not token:
                logger.warning("Google OAuth callback failed - no token received")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OAuth authorization failed"
                )
            
            # Get user info from Google
            user_info = await self._get_google_user_info(token)
            
            # Find or create user
            user, is_new_user = await self._find_or_create_google_user(user_info, db)
            
            # Create access token
            access_token = create_user_token(user.id, user.email)
            
            # Update login tracking
            from datetime import datetime
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Google OAuth {'registration' if is_new_user else 'login'} successful: {user.email}")
            
            return user, access_token, is_new_user
            
        except HTTPException:
            raise
        except OAuthError as e:
            logger.error(f"OAuth error during Google callback: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {e.description if hasattr(e, 'description') else str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during Google OAuth callback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth authentication failed"
            )
    
    async def _get_google_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user information from Google using access token.
        
        Args:
            token: OAuth token dictionary
            
        Returns:
            User information dictionary
            
        Raises:
            HTTPException: If user info retrieval fails
        """
        try:
            # Use the token to get user info
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    OAuthConfig.GOOGLE_USER_INFO_URL,
                    headers={'Authorization': f"Bearer {token['access_token']}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google user info request failed: {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to retrieve user information from Google"
                    )
                
                user_info = response.json()
                logger.debug(f"Google user info retrieved for: {user_info.get('email', 'unknown')}")
                
                return user_info
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving Google user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information"
            )
    
    async def _find_or_create_google_user(
        self,
        user_info: Dict[str, Any],
        db: AsyncSession
    ) -> Tuple[User, bool]:
        """
        Find existing user or create new user from Google OAuth info.
        
        Args:
            user_info: Google user information
            db: Database session
            
        Returns:
            Tuple of (User instance, is_new_user)
        """
        google_id = user_info.get('id')
        email = user_info.get('email')
        first_name = user_info.get('given_name')
        last_name = user_info.get('family_name')
        avatar_url = user_info.get('picture')
        
        # First, try to find user by Google ID
        result = await db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # User exists with this Google ID
            return user, False
        
        # Try to find user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # User exists with this email - link Google account
            user.google_id = google_id
            
            # Update profile info if not set
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url
            
            # Mark email as verified (Google verified it)
            if not user.is_verified:
                user.is_verified = True
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Linked Google account to existing user: {email}")
            
            return user, False
        
        # Create new user
        new_user = User(
            email=email,
            google_id=google_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            is_verified=True,  # Google verified the email
            is_active=True,
            hashed_password=None  # OAuth-only user
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Send welcome email for new OAuth users
        try:
            await send_welcome_email(new_user.email, new_user.first_name)
        except Exception as e:
            logger.warning(f"Failed to send welcome email to new OAuth user: {e}")
        
        logger.info(f"Created new user via Google OAuth: {email}")
        
        return new_user, True


# Global OAuth service instance
oauth_service = OAuthService()


# Convenience functions
async def get_google_authorization_url(request: Request, state: Optional[str] = None) -> str:
    """Get Google OAuth authorization URL."""
    return await oauth_service.get_google_auth_url(request, state)


async def handle_google_oauth_callback(
    request: Request,
    db: AsyncSession
) -> Tuple[User, str, bool]:
    """Handle Google OAuth callback."""
    return await oauth_service.handle_google_callback(request, db)


def is_google_oauth_configured() -> bool:
    """Check if Google OAuth is properly configured."""
    return oauth_service.is_google_oauth_available() 