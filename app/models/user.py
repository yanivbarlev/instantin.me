from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model for InstantIn.me platform.
    Handles authentication, profile info, and payment provider links.
    """
    
    __tablename__ = "users"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Authentication fields
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # OAuth integration
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Payment provider integration
    stripe_account_id = Column(String(255), nullable=True)
    paypal_email = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Last login tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', verified={self.is_verified})>"
    
    # Relationships
    storefronts = relationship("Storefront", back_populates="user", cascade="all, delete-orphan")
    created_drops = relationship("Drop", back_populates="creator", cascade="all, delete-orphan")
    drop_participations = relationship("DropParticipant", back_populates="user", cascade="all, delete-orphan")
    raffle_entries = relationship("RaffleEntry", back_populates="user", cascade="all, delete-orphan")
    page_views = relationship("PageView", back_populates="user", cascade="all, delete-orphan")
    # Note: Additional relationships will be added as models are created:
    
    # Helper properties
    
    @property
    def full_name(self) -> str:
        """Get user's full name or email if name not available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]  # Use email prefix as fallback
    
    @property
    def has_password(self) -> bool:
        """Check if user has a password set (not OAuth-only)."""
        return bool(self.hashed_password)
    
    @property
    def has_google_oauth(self) -> bool:
        """Check if user has Google OAuth linked."""
        return bool(self.google_id)
    
    @property
    def stripe_connected(self) -> bool:
        """Check if user has Stripe account connected."""
        return bool(self.stripe_account_id)
    
    @property
    def paypal_connected(self) -> bool:
        """Check if user has PayPal account connected."""
        return bool(self.paypal_email)
    
    @property
    def can_receive_payments(self) -> bool:
        """Check if user can receive payments (has at least one payment method)."""
        return self.stripe_connected or self.paypal_connected 