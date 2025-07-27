from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class TokenType(str, Enum):
    """Token type enumeration for JWT responses"""
    BEARER = "bearer"


class UserCreate(BaseModel):
    """
    Schema for user registration.
    Used in POST /auth/register endpoint.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="User's password (8-128 characters)"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's last name"
    )
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or just whitespace')
            if any(char.isdigit() for char in v):
                raise ValueError('Names cannot contain numbers')
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login.
    Used in POST /auth/login endpoint.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.
    Excludes sensitive information like hashed passwords.
    """
    id: int = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    is_verified: bool = Field(..., description="Whether user's email is verified")
    is_active: bool = Field(..., description="Whether user account is active")
    
    # OAuth status
    has_google_oauth: bool = Field(..., description="Whether user has Google OAuth linked")
    
    # Payment provider status
    stripe_connected: bool = Field(..., description="Whether user has Stripe account connected")
    paypal_connected: bool = Field(..., description="Whether user has PayPal account connected")
    can_receive_payments: bool = Field(..., description="Whether user can receive payments")
    
    # Computed fields
    full_name: str = Field(..., description="User's full name or email prefix")
    
    # Timestamps
    created_at: datetime = Field(..., description="When the user account was created")
    updated_at: datetime = Field(..., description="When the user account was last updated")
    last_login_at: Optional[datetime] = Field(None, description="User's last login timestamp")
    
    class Config:
        from_attributes = True  # SQLAlchemy 2.0 compatibility
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_verified": True,
                "is_active": True,
                "has_google_oauth": True,
                "stripe_connected": False,
                "paypal_connected": True,
                "can_receive_payments": True,
                "full_name": "John Doe",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_login_at": "2024-01-15T15:45:00Z"
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for updating user profile information.
    Used in PATCH /auth/me endpoint.
    """
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's last name"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image"
    )
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or just whitespace')
            if any(char.isdigit() for char in v):
                raise ValueError('Names cannot contain numbers')
        return v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        """Validate avatar URL format"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('Avatar URL must start with http:// or https://')
            if not any(v.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                raise ValueError('Avatar URL must point to a valid image file')
        return v

    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "avatar_url": "https://example.com/new-avatar.jpg"
            }
        }


class UserProfile(BaseModel):
    """
    Schema for detailed user profile information.
    Used in GET /auth/me endpoint.
    """
    id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    is_active: bool
    
    # OAuth information
    has_google_oauth: bool
    
    # Payment provider information
    stripe_connected: bool
    paypal_connected: bool
    can_receive_payments: bool
    
    # Account statistics
    login_count: int = Field(..., description="Total number of logins")
    
    # Computed fields
    full_name: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_verified": True,
                "is_active": True,
                "has_google_oauth": True,
                "stripe_connected": False,
                "paypal_connected": True,
                "can_receive_payments": True,
                "login_count": 42,
                "full_name": "John Doe",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_login_at": "2024-01-15T15:45:00Z"
            }
        }


class TokenResponse(BaseModel):
    """
    Schema for JWT token response.
    Used in POST /auth/login and POST /auth/register endpoints.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: TokenType = Field(
        TokenType.BEARER, 
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_verified": True,
                    "is_active": True,
                    "full_name": "John Doe"
                }
            }
        }


class EmailVerificationRequest(BaseModel):
    """
    Schema for email verification request.
    Used in POST /auth/verify-email endpoint.
    """
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789"
            }
        }


class PasswordResetRequest(BaseModel):
    """
    Schema for password reset request.
    Used in POST /auth/password-reset endpoint.
    """
    email: EmailStr = Field(..., description="User's email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """
    Schema for password reset confirmation.
    Used in POST /auth/password-reset-confirm endpoint.
    """
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)"
    )
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset123token456",
                "new_password": "NewSecurePass123"
            }
        } 