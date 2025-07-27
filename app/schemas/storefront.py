from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import re


class StorefrontBase(BaseModel):
    """Base storefront schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Storefront display name")
    slug: str = Field(..., min_length=3, max_length=100, pattern=r'^[a-z0-9-]+$', description="URL-friendly identifier")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description of the storefront")
    bio: Optional[str] = Field(None, max_length=500, description="Short bio or tagline")
    
    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Slug cannot start or end with a hyphen')
        if '--' in v:
            raise ValueError('Slug cannot contain consecutive hyphens')
        return v


class StorefrontTheme(BaseModel):
    """Theme and customization settings"""
    theme: str = Field("light", pattern=r'^(light|dark|custom)$', description="Theme preset")
    custom_css: Optional[str] = Field(None, max_length=10000, description="Custom CSS overrides")
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Primary color in hex format")
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Accent color in hex format")


class StorefrontMedia(BaseModel):
    """Media and branding assets"""
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile picture URL")
    cover_image_url: Optional[HttpUrl] = Field(None, description="Header/banner image URL")
    logo_url: Optional[HttpUrl] = Field(None, description="Brand logo URL")


class StorefrontSocial(BaseModel):
    """Social media links"""
    instagram_url: Optional[HttpUrl] = Field(None, description="Instagram profile URL")
    twitter_url: Optional[HttpUrl] = Field(None, description="Twitter profile URL")
    tiktok_url: Optional[HttpUrl] = Field(None, description="TikTok profile URL")
    youtube_url: Optional[HttpUrl] = Field(None, description="YouTube channel URL")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    website_url: Optional[HttpUrl] = Field(None, description="Personal/business website URL")


class StorefrontSEO(BaseModel):
    """SEO and metadata settings"""
    meta_title: Optional[str] = Field(None, max_length=60, description="SEO title tag")
    meta_description: Optional[str] = Field(None, max_length=160, description="SEO meta description")


class StorefrontSettings(BaseModel):
    """Platform feature settings"""
    enable_analytics: bool = Field(True, description="Enable visitor analytics")
    enable_tips: bool = Field(True, description="Accept tips and donations")
    enable_scheduling: bool = Field(False, description="Enable booking/scheduling functionality")
    show_recent_activity: bool = Field(True, description="Display recent activity")
    show_social_proof: bool = Field(True, description="Show social proof elements")
    show_visitor_count: bool = Field(False, description="Display visitor count")


class StorefrontVisibility(BaseModel):
    """Publication and visibility settings"""
    is_published: bool = Field(False, description="Whether storefront is publicly accessible")


class StorefrontCreate(StorefrontBase):
    """Schema for creating a new storefront"""
    # Theme and customization
    theme: str = Field("light", pattern=r'^(light|dark|custom)$')
    custom_css: Optional[str] = Field(None, max_length=10000)
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    # Media and branding
    avatar_url: Optional[str] = Field(None, max_length=500)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    
    # Social media links
    instagram_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    tiktok_url: Optional[str] = Field(None, max_length=255)
    youtube_url: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=255)
    
    # SEO settings
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    # Platform settings
    enable_analytics: bool = Field(True)
    enable_tips: bool = Field(True)
    enable_scheduling: bool = Field(False)
    show_recent_activity: bool = Field(True)
    show_social_proof: bool = Field(True)
    show_visitor_count: bool = Field(False)
    
    # Visibility
    is_published: bool = Field(False)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Creative Studio",
                "slug": "my-creative-studio",
                "description": "Welcome to my creative space where I share my latest projects and connect with clients.",
                "bio": "Digital creator & designer helping brands tell their story",
                "theme": "light",
                "primary_color": "#3B82F6",
                "accent_color": "#EF4444",
                "avatar_url": "https://images.unsplash.com/photo-1494790108755-2616b612b8c5",
                "cover_image_url": "https://images.unsplash.com/photo-1561736778-92e52a7769ef",
                "instagram_url": "https://instagram.com/mycreativestudio",
                "website_url": "https://mycreativestudio.com",
                "meta_title": "My Creative Studio - Digital Design & Branding",
                "meta_description": "Discover unique digital designs and branding solutions from My Creative Studio.",
                "enable_analytics": True,
                "enable_tips": True,
                "is_published": True
            }
        }


class StorefrontUpdate(BaseModel):
    """Schema for updating an existing storefront - all fields optional"""
    # Basic information
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = Field(None, max_length=2000)
    bio: Optional[str] = Field(None, max_length=500)
    
    # Theme and customization
    theme: Optional[str] = Field(None, pattern=r'^(light|dark|custom)$')
    custom_css: Optional[str] = Field(None, max_length=10000)
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    # Media and branding
    avatar_url: Optional[str] = Field(None, max_length=500)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    
    # Social media links
    instagram_url: Optional[str] = Field(None, max_length=255)
    twitter_url: Optional[str] = Field(None, max_length=255)
    tiktok_url: Optional[str] = Field(None, max_length=255)
    youtube_url: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=255)
    
    # SEO settings
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    # Platform settings
    enable_analytics: Optional[bool] = None
    enable_tips: Optional[bool] = None
    enable_scheduling: Optional[bool] = None
    show_recent_activity: Optional[bool] = None
    show_social_proof: Optional[bool] = None
    show_visitor_count: Optional[bool] = None
    
    # Visibility
    is_published: Optional[bool] = None

    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly"""
        if v is None:
            return v
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Slug cannot start or end with a hyphen')
        if '--' in v:
            raise ValueError('Slug cannot contain consecutive hyphens')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Studio Name",
                "bio": "Updated bio text",
                "primary_color": "#10B981",
                "is_published": True
            }
        }


class StorefrontResponse(StorefrontBase):
    """Schema for returning storefront data"""
    id: UUID = Field(..., description="Unique storefront identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    
    # Theme and customization
    theme: str = Field(..., description="Theme preset")
    custom_css: Optional[str] = Field(None, description="Custom CSS overrides")
    primary_color: Optional[str] = Field(None, description="Primary color in hex format")
    accent_color: Optional[str] = Field(None, description="Accent color in hex format")
    
    # Media and branding
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    cover_image_url: Optional[str] = Field(None, description="Header/banner image URL")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    
    # Social media links
    instagram_url: Optional[str] = Field(None, description="Instagram profile URL")
    twitter_url: Optional[str] = Field(None, description="Twitter profile URL")
    tiktok_url: Optional[str] = Field(None, description="TikTok profile URL")
    youtube_url: Optional[str] = Field(None, description="YouTube channel URL")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    website_url: Optional[str] = Field(None, description="Personal/business website URL")
    
    # SEO and discoverability
    meta_title: Optional[str] = Field(None, description="SEO title tag")
    meta_description: Optional[str] = Field(None, description="SEO meta description")
    
    # Analytics and tracking
    view_count: str = Field(..., description="Total page views")
    click_count: str = Field(..., description="Total link clicks")
    
    # Platform feature settings
    enable_analytics: bool = Field(..., description="Analytics enabled")
    enable_tips: bool = Field(..., description="Tips enabled")
    enable_scheduling: bool = Field(..., description="Scheduling enabled")
    show_recent_activity: bool = Field(..., description="Show recent activity")
    show_social_proof: bool = Field(..., description="Show social proof")
    show_visitor_count: bool = Field(..., description="Show visitor count")
    
    # Publication and visibility
    is_published: bool = Field(..., description="Published status")
    is_featured: bool = Field(..., description="Featured on platform")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_published_at: Optional[datetime] = Field(None, description="Last publication timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "My Creative Studio",
                "slug": "my-creative-studio",
                "description": "Welcome to my creative space...",
                "bio": "Digital creator & designer",
                "theme": "light",
                "primary_color": "#3B82F6",
                "accent_color": "#EF4444",
                "avatar_url": "https://images.unsplash.com/photo-1494790108755-2616b612b8c5",
                "cover_image_url": "https://images.unsplash.com/photo-1561736778-92e52a7769ef",
                "instagram_url": "https://instagram.com/mycreativestudio",
                "website_url": "https://mycreativestudio.com",
                "meta_title": "My Creative Studio - Digital Design & Branding",
                "meta_description": "Discover unique digital designs...",
                "view_count": "1247",
                "click_count": "856",
                "enable_analytics": True,
                "enable_tips": True,
                "enable_scheduling": False,
                "show_recent_activity": True,
                "show_social_proof": True,
                "show_visitor_count": False,
                "is_published": True,
                "is_featured": False,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z",
                "last_published_at": "2024-01-20T14:45:00Z"
            }
        }


class StorefrontListResponse(BaseModel):
    """Schema for listing multiple storefronts with pagination"""
    storefronts: list[StorefrontResponse] = Field(..., description="List of storefronts")
    total: int = Field(..., description="Total number of storefronts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "storefronts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My Creative Studio",
                        "slug": "my-creative-studio",
                        "bio": "Digital creator & designer",
                        "is_published": True,
                        "view_count": "1247"
                    }
                ],
                "total": 25,
                "page": 1,
                "per_page": 10,
                "pages": 3
            }
        }


class StorefrontStats(BaseModel):
    """Schema for storefront analytics and statistics"""
    view_count: int = Field(..., description="Total page views")
    click_count: int = Field(..., description="Total link clicks")
    visitor_count: int = Field(..., description="Unique visitors")
    conversion_rate: float = Field(..., description="Conversion percentage")
    top_referrers: list[str] = Field(..., description="Top referral sources")
    popular_pages: list[str] = Field(..., description="Most visited pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "view_count": 1247,
                "click_count": 856,
                "visitor_count": 892,
                "conversion_rate": 12.5,
                "top_referrers": ["instagram.com", "twitter.com", "direct"],
                "popular_pages": ["/products/design-pack", "/about", "/contact"]
            }
        } 