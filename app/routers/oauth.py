from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.database import get_async_session
from app.schemas.user import TokenResponse
from app.auth.oauth import (
    oauth_service,
    get_google_authorization_url,
    handle_google_oauth_callback,
    is_google_oauth_configured
)

logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(
    prefix="/oauth",
    tags=["OAuth Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Authorization failed"},
        503: {"description": "OAuth service unavailable"}
    }
)


@router.get(
    "/google/authorize",
    summary="Get Google OAuth authorization URL",
    description="Get the Google OAuth authorization URL to redirect users for authentication"
)
async def google_oauth_authorize(
    request: Request,
    state: str = None
) -> Dict[str, Any]:
    """
    Get Google OAuth authorization URL.
    
    - **state**: Optional state parameter for CSRF protection
    
    Returns the authorization URL where users should be redirected.
    """
    try:
        if not is_google_oauth_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )
        
        auth_url = await get_google_authorization_url(request, state)
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "provider": "google"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Google OAuth authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get(
    "/google/callback",
    response_model=TokenResponse,
    summary="Handle Google OAuth callback",
    description="Handle the callback from Google OAuth and authenticate or register the user"
)
async def google_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Handle Google OAuth callback.
    
    This endpoint is called by Google after user authorization.
    It exchanges the authorization code for user information and creates/authenticates the user.
    
    Returns JWT token and user information.
    """
    try:
        if not is_google_oauth_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )
        
        # Handle OAuth callback
        user, access_token, is_new_user = await handle_google_oauth_callback(request, db)
        
        # Create token response
        token_response = oauth_service.create_token_response(user, access_token)
        
        # Log the successful OAuth flow
        flow_type = "registration" if is_new_user else "login"
        logger.info(f"Google OAuth {flow_type} completed for user: {user.email}")
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.get(
    "/status",
    summary="Get OAuth configuration status",
    description="Check which OAuth providers are available and configured"
)
async def oauth_status() -> Dict[str, Any]:
    """
    Get OAuth configuration status.
    
    Returns information about which OAuth providers are available.
    """
    return {
        "providers": {
            "google": {
                "available": is_google_oauth_configured(),
                "name": "Google",
                "scopes": ["openid", "email", "profile"]
            }
        },
        "configured_providers": ["google"] if is_google_oauth_configured() else []
    } 