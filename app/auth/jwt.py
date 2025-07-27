from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class JWTHandler:
    """
    JWT token handler for InstantIn.me platform.
    Handles creation, verification, and decoding of JWT tokens.
    """
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary containing user information to encode
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
            
        Example:
            jwt_handler = JWTHandler()
            token = jwt_handler.create_access_token({"sub": "user@example.com", "user_id": 1})
        """
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "instantin.me",  # Issuer
            "aud": "instantin.me-users"  # Audience
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT token created for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="instantin.me-users",
                issuer="instantin.me"
            )
            
            # Verify required claims
            if payload.get("sub") is None:
                logger.warning("JWT token missing 'sub' claim")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject"
                )
            
            logger.debug(f"JWT token verified for user: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification error"
            )
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT token without verification (for debugging/logging).
        WARNING: Do not use for authentication - verification bypass!
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.debug(f"Failed to decode token without verification: {e}")
            return None
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime or None if invalid
        """
        try:
            payload = self.decode_token_without_verification(token)
            if payload and "exp" in payload:
                return datetime.fromtimestamp(payload["exp"])
            return None
        except Exception:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a JWT token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if expired, False if valid, None if invalid token
        """
        expiration = self.get_token_expiration(token)
        if expiration is None:
            return True  # Treat invalid tokens as expired
        return datetime.utcnow() > expiration
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh a JWT token if it's still valid but close to expiration.
        
        Args:
            token: Current JWT token
            
        Returns:
            New token if refresh is needed and possible, None otherwise
        """
        try:
            payload = self.verify_token(token)
            
            # Check if token needs refresh (within 5 minutes of expiration)
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp)
                time_until_exp = exp_time - datetime.utcnow()
                
                if time_until_exp <= timedelta(minutes=5):
                    # Create new token with same data (excluding exp, iat)
                    new_data = {k: v for k, v in payload.items() 
                              if k not in ["exp", "iat", "iss", "aud"]}
                    return self.create_access_token(new_data)
            
            return None  # No refresh needed
            
        except HTTPException:
            return None  # Invalid token, cannot refresh


# Global JWT handler instance
jwt_handler = JWTHandler()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Convenience function to create access token.
    
    Args:
        data: User data to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    return jwt_handler.create_access_token(data, expires_delta)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Convenience function to verify token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
    """
    return jwt_handler.verify_token(token)


def create_user_token(user_id: int, email: str) -> str:
    """
    Create a JWT token for a specific user.
    
    Args:
        user_id: User's database ID
        email: User's email address
        
    Returns:
        JWT token string
    """
    token_data = {
        "sub": email,  # Subject (standard JWT claim)
        "user_id": user_id,
        "token_type": "access"
    }
    return create_access_token(token_data)


def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user_id and email
        
    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_token(token)
    
    user_id = payload.get("user_id")
    email = payload.get("sub")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user information"
        )
    
    return {
        "user_id": user_id,
        "email": email
    }


def create_email_verification_token(email: str) -> str:
    """
    Create a JWT token for email verification.
    
    Args:
        email: User's email address
        
    Returns:
        JWT token string (expires in 24 hours)
    """
    token_data = {
        "sub": email,
        "token_type": "email_verification"
    }
    # Email verification tokens expire in 24 hours
    expires_delta = timedelta(hours=24)
    return create_access_token(token_data, expires_delta)


def create_password_reset_token(email: str) -> str:
    """
    Create a JWT token for password reset.
    
    Args:
        email: User's email address
        
    Returns:
        JWT token string (expires in 1 hour)
    """
    token_data = {
        "sub": email,
        "token_type": "password_reset"
    }
    # Password reset tokens expire in 1 hour for security
    expires_delta = timedelta(hours=1)
    return create_access_token(token_data, expires_delta)


def verify_email_verification_token(token: str) -> str:
    """
    Verify an email verification token and extract email.
    
    Args:
        token: Email verification token
        
    Returns:
        Email address from token
        
    Raises:
        HTTPException: If token is invalid or wrong type
    """
    payload = verify_token(token)
    
    if payload.get("token_type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for email verification"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email"
        )
    
    return email


def verify_password_reset_token(token: str) -> str:
    """
    Verify a password reset token and extract email.
    
    Args:
        token: Password reset token
        
    Returns:
        Email address from token
        
    Raises:
        HTTPException: If token is invalid or wrong type
    """
    payload = verify_token(token)
    
    if payload.get("token_type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for password reset"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email"
        )
    
    return email 