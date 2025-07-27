from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Storefront(Base):
    """
    Storefront model for InstantIn.me Link-in-Bio Commerce Platform.
    Represents a user's customizable storefront page with products and content.
    """
    
    __tablename__ = "storefronts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationship to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic storefront information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)  # URL-friendly identifier
    
    # Content and description
    description = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)  # Short bio/tagline
    
    # Theme and customization
    theme = Column(String(50), nullable=False, default="light")  # light, dark, custom
    custom_css = Column(Text, nullable=True)  # Custom CSS overrides
    primary_color = Column(String(7), nullable=True)  # Hex color code #RRGGBB
    accent_color = Column(String(7), nullable=True)   # Secondary color
    
    # Branding and media
    avatar_url = Column(String(500), nullable=True)  # Profile picture
    cover_image_url = Column(String(500), nullable=True)  # Header/banner image
    logo_url = Column(String(500), nullable=True)  # Brand logo
    
    # Social media links
    instagram_url = Column(String(255), nullable=True)
    twitter_url = Column(String(255), nullable=True)
    tiktok_url = Column(String(255), nullable=True)
    youtube_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    
    # Publication and visibility
    is_published = Column(Boolean, nullable=False, default=False, index=True)
    is_featured = Column(Boolean, nullable=False, default=False)  # Featured on platform
    
    # SEO and discoverability
    meta_title = Column(String(60), nullable=True)  # SEO title tag
    meta_description = Column(String(160), nullable=True)  # SEO description
    
    # Analytics and tracking
    view_count = Column(String, nullable=False, default="0")  # Total page views
    click_count = Column(String, nullable=False, default="0")  # Total link clicks
    
    # Platform features
    enable_analytics = Column(Boolean, nullable=False, default=True)
    enable_tips = Column(Boolean, nullable=False, default=True)  # Accept tips/donations
    enable_scheduling = Column(Boolean, nullable=False, default=False)  # Booking functionality
    
    # Content settings
    show_recent_activity = Column(Boolean, nullable=False, default=True)
    show_social_proof = Column(Boolean, nullable=False, default=True)
    show_visitor_count = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="storefronts")
    products = relationship("Product", back_populates="storefront", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="storefront", cascade="all, delete-orphan")
    page_views = relationship("PageView", back_populates="storefront", cascade="all, delete-orphan")
    # Note: Additional relationships will be added as models are created:
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_storefronts_user_slug', 'user_id', 'slug'),
        Index('ix_storefronts_published_featured', 'is_published', 'is_featured'),
        Index('ix_storefronts_created_published', 'created_at', 'is_published'),
    )
    
    def __init__(self, **kwargs):
        """Initialize storefront with default values"""
        super().__init__(**kwargs)
        if not self.slug and self.name:
            # Generate slug from name if not provided
            self.slug = self._generate_slug_from_name(self.name)
    
    def __repr__(self):
        return f"<Storefront(id={self.id}, name='{self.name}', slug='{self.slug}', user_id={self.user_id})>"
    
    # Helper properties
    @property
    def full_url(self) -> str:
        """Get the full URL for this storefront"""
        # Will be configurable based on domain settings
        return f"https://instantin.me/{self.slug}"
    
    @property
    def is_fully_configured(self) -> bool:
        """Check if storefront has minimum required configuration"""
        return bool(
            self.name and 
            self.slug and 
            self.description and
            (self.avatar_url or self.logo_url)
        )
    
    @property
    def theme_colors(self) -> dict:
        """Get theme color configuration"""
        return {
            "primary": self.primary_color or "#3B82F6",  # Default blue
            "accent": self.accent_color or "#10B981",    # Default green
            "theme": self.theme
        }
    
    @property
    def social_links(self) -> dict:
        """Get all configured social media links"""
        return {
            "instagram": self.instagram_url,
            "twitter": self.twitter_url,
            "tiktok": self.tiktok_url,
            "youtube": self.youtube_url,
            "linkedin": self.linkedin_url,
            "website": self.website_url
        }
    
    @property
    def analytics_summary(self) -> dict:
        """Get basic analytics summary"""
        return {
            "views": int(self.view_count) if self.view_count.isdigit() else 0,
            "clicks": int(self.click_count) if self.click_count.isdigit() else 0,
            "published": self.is_published,
            "last_published": self.last_published_at
        }
    
    # Helper methods
    def _generate_slug_from_name(self, name: str) -> str:
        """Generate URL-friendly slug from storefront name"""
        import re
        # Convert to lowercase, replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
        slug = slug.strip('-')
        return slug[:100]  # Limit length
    
    def update_view_count(self):
        """Increment view count (analytics)"""
        current_count = int(self.view_count) if self.view_count.isdigit() else 0
        self.view_count = str(current_count + 1)
    
    def update_click_count(self):
        """Increment click count (analytics)"""
        current_count = int(self.click_count) if self.click_count.isdigit() else 0
        self.click_count = str(current_count + 1)
    
    def publish(self):
        """Publish the storefront"""
        self.is_published = True
        self.last_published_at = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the storefront"""
        self.is_published = False 