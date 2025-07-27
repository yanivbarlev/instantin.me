from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid
import enum

from app.database import Base


class DropStatus(str, enum.Enum):
    """Drop lifecycle status"""
    DRAFT = "draft"                   # Drop being configured
    SCHEDULED = "scheduled"           # Drop scheduled for future start
    ACTIVE = "active"                # Drop currently running
    ENDED = "ended"                  # Drop completed successfully
    CANCELLED = "cancelled"          # Drop cancelled before completion
    PAUSED = "paused"               # Drop temporarily paused


class DropType(str, enum.Enum):
    """Type of drop collaboration"""
    REVENUE_SHARE = "revenue_share"   # Standard revenue sharing drop
    FIXED_SPLIT = "fixed_split"      # Fixed percentage split
    EQUAL_SPLIT = "equal_split"      # Equal split among participants
    CREATOR_LEAD = "creator_lead"    # Creator gets majority, others get fixed amounts


class Drop(Base):
    """
    Drop model for InstantIn.me Link-in-Bio Commerce Platform.
    Enables collaborative commerce with revenue sharing among multiple users.
    """
    
    __tablename__ = "drops"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Drop identification and branding
    name = Column(String(255), nullable=False)                      # Drop display name
    slug = Column(String(255), nullable=False, unique=True, index=True) # URL-friendly identifier
    description = Column(Text, nullable=True)                       # Drop description
    short_description = Column(String(500), nullable=True)          # Brief description for listings
    
    # Drop creator and ownership
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Drop lifecycle and timing
    status = Column(Enum(DropStatus), nullable=False, default=DropStatus.DRAFT, index=True)
    drop_type = Column(Enum(DropType), nullable=False, default=DropType.REVENUE_SHARE, index=True)
    
    # Schedule and duration
    start_date = Column(DateTime(timezone=True), nullable=True, index=True)
    end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_hours = Column(Integer, nullable=True)                # Drop duration in hours
    timezone = Column(String(50), nullable=False, default="UTC")   # Drop timezone
    
    # Participation and collaboration
    max_participants = Column(Integer, nullable=True, default=10)   # Maximum number of participants
    invite_only = Column(Boolean, nullable=False, default=False)    # Requires invitation to join
    application_required = Column(Boolean, nullable=False, default=False) # Requires application approval
    auto_approve_applications = Column(Boolean, nullable=False, default=True)
    
    # Revenue sharing configuration
    creator_revenue_percentage = Column(Numeric(5, 2), nullable=False, default=50.0) # Creator's base share
    participant_revenue_percentage = Column(Numeric(5, 2), nullable=False, default=30.0) # Default participant share
    platform_fee_percentage = Column(Numeric(5, 2), nullable=False, default=20.0) # Platform fee
    minimum_revenue_share = Column(Numeric(5, 2), nullable=False, default=5.0) # Minimum share per participant
    
    # Performance tracking
    total_sales = Column(Numeric(12, 2), nullable=False, default=0)  # Total revenue generated
    total_orders = Column(Integer, nullable=False, default=0)        # Number of orders
    participant_count = Column(Integer, nullable=False, default=1)   # Current participant count
    conversion_rate = Column(Numeric(5, 2), nullable=False, default=0) # Overall conversion rate
    
    # Drop content and media
    featured_image_url = Column(String(500), nullable=True)         # Main drop image
    banner_image_url = Column(String(500), nullable=True)          # Banner for drop page
    video_url = Column(String(500), nullable=True)                 # Promotional video
    gallery_urls = Column(Text, nullable=True)                     # JSON array of additional images
    
    # Marketing and promotion
    promotional_message = Column(Text, nullable=True)              # Marketing message
    hashtags = Column(Text, nullable=True)                         # JSON array of hashtags
    social_media_kit_url = Column(String(500), nullable=True)     # Marketing materials
    
    # Drop settings and configuration
    is_public = Column(Boolean, nullable=False, default=True)      # Visible in public listings
    is_featured = Column(Boolean, nullable=False, default=False)   # Featured drop
    allow_late_join = Column(Boolean, nullable=False, default=True) # Allow joining after start
    require_social_promotion = Column(Boolean, nullable=False, default=False) # Require social sharing
    
    # Analytics and insights
    page_views = Column(Integer, nullable=False, default=0)        # Drop page views
    click_through_rate = Column(Numeric(5, 2), nullable=False, default=0) # CTR for promotions
    social_shares = Column(Integer, nullable=False, default=0)     # Social media shares
    
    # Goal setting and targets
    revenue_goal = Column(Numeric(12, 2), nullable=True)          # Target revenue
    participant_goal = Column(Integer, nullable=True)             # Target number of participants
    order_goal = Column(Integer, nullable=True)                   # Target number of orders
    
    # Communication and updates
    announcement_message = Column(Text, nullable=True)             # Latest announcement
    last_update_message = Column(Text, nullable=True)             # Last status update
    creator_message = Column(Text, nullable=True)                 # Message from creator
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)  # When drop was made public
    launched_at = Column(DateTime(timezone=True), nullable=True)   # When drop actually started
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When drop ended
    
    # Relationships
    creator = relationship("User", back_populates="created_drops")
    participants = relationship("DropParticipant", back_populates="drop", cascade="all, delete-orphan")
    # Note: Additional relationships will be added as models are created:
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_drops_status_start_date', 'status', 'start_date'),
        Index('ix_drops_creator_status', 'created_by_user_id', 'status'),
        Index('ix_drops_public_featured', 'is_public', 'is_featured'),
        Index('ix_drops_type_status', 'drop_type', 'status'),
        Index('ix_drops_end_date_status', 'end_date', 'status'),
        Index('ix_drops_revenue_goal', 'total_sales', 'revenue_goal'),
    )
    
    def __repr__(self):
        return f"<Drop(id={self.id}, name='{self.name}', status={self.status}, participants={self.participant_count})>"
    
    # Helper properties
    @property
    def is_active(self) -> bool:
        """Check if drop is currently active"""
        return self.status == DropStatus.ACTIVE
    
    @property
    def is_scheduled(self) -> bool:
        """Check if drop is scheduled for future"""
        return self.status == DropStatus.SCHEDULED
    
    @property
    def is_ended(self) -> bool:
        """Check if drop has ended"""
        return self.status in [DropStatus.ENDED, DropStatus.CANCELLED]
    
    @property
    def can_join(self) -> bool:
        """Check if new participants can join"""
        if self.status not in [DropStatus.SCHEDULED, DropStatus.ACTIVE]:
            return False
        
        if not self.allow_late_join and self.status == DropStatus.ACTIVE:
            return False
        
        if self.max_participants and self.participant_count >= self.max_participants:
            return False
        
        return True
    
    @property
    def time_remaining(self) -> timedelta:
        """Get time remaining in drop"""
        if not self.end_date:
            return timedelta(0)
        
        now = datetime.utcnow()
        if now >= self.end_date:
            return timedelta(0)
        
        return self.end_date - now
    
    @property
    def time_until_start(self) -> timedelta:
        """Get time until drop starts"""
        if not self.start_date:
            return timedelta(0)
        
        now = datetime.utcnow()
        if now >= self.start_date:
            return timedelta(0)
        
        return self.start_date - now
    
    @property
    def revenue_goal_progress(self) -> float:
        """Get revenue goal progress percentage"""
        if not self.revenue_goal or self.revenue_goal <= 0:
            return 0.0
        return min(100.0, (float(self.total_sales) / float(self.revenue_goal)) * 100)
    
    @property
    def participant_goal_progress(self) -> float:
        """Get participant goal progress percentage"""
        if not self.participant_goal or self.participant_goal <= 0:
            return 0.0
        return min(100.0, (self.participant_count / self.participant_goal) * 100)
    
    @property
    def average_order_value(self) -> float:
        """Calculate average order value"""
        if self.total_orders <= 0:
            return 0.0
        return float(self.total_sales) / self.total_orders
    
    @property
    def full_url(self) -> str:
        """Get full drop URL"""
        return f"https://instantin.me/drops/{self.slug}"
    
    @property
    def remaining_spots(self) -> int:
        """Get remaining participant spots"""
        if not self.max_participants:
            return -1  # Unlimited
        return max(0, self.max_participants - self.participant_count)
    
    # Business logic methods
    def generate_slug(self):
        """Generate URL-friendly slug from name"""
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', self.name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        self.slug = slug.strip('-')
    
    def start_drop(self):
        """Start the drop"""
        if self.status == DropStatus.SCHEDULED:
            self.status = DropStatus.ACTIVE
            self.launched_at = datetime.utcnow()
    
    def end_drop(self):
        """End the drop"""
        if self.status == DropStatus.ACTIVE:
            self.status = DropStatus.ENDED
            self.completed_at = datetime.utcnow()
    
    def pause_drop(self):
        """Pause the drop temporarily"""
        if self.status == DropStatus.ACTIVE:
            self.status = DropStatus.PAUSED
    
    def resume_drop(self):
        """Resume a paused drop"""
        if self.status == DropStatus.PAUSED:
            self.status = DropStatus.ACTIVE
    
    def cancel_drop(self, reason: str = None):
        """Cancel the drop"""
        self.status = DropStatus.CANCELLED
        if reason:
            self.last_update_message = f"Drop cancelled: {reason}"
    
    def publish_drop(self):
        """Make drop public and available"""
        self.is_public = True
        self.published_at = datetime.utcnow()
        if self.status == DropStatus.DRAFT:
            self.status = DropStatus.SCHEDULED
    
    def record_sale(self, order_amount: float):
        """Record a sale for this drop"""
        self.total_sales += order_amount
        self.total_orders += 1
        self.calculate_conversion_rate()
    
    def record_page_view(self):
        """Record a page view"""
        self.page_views += 1
        self.calculate_conversion_rate()
    
    def record_social_share(self):
        """Record a social media share"""
        self.social_shares += 1
    
    def calculate_conversion_rate(self):
        """Calculate and update conversion rate"""
        if self.page_views <= 0:
            self.conversion_rate = 0
        else:
            self.conversion_rate = (self.total_orders / self.page_views) * 100
    
    def update_participant_count(self, count: int):
        """Update participant count"""
        self.participant_count = count
    
    def can_user_join(self, user_id: str) -> tuple[bool, str]:
        """Check if a user can join this drop"""
        if not self.can_join:
            return False, "Drop is not accepting new participants"
        
        if self.invite_only:
            # Would need to check invite status
            return False, "Drop is invite-only"
        
        if self.application_required and not self.auto_approve_applications:
            return False, "Application required for this drop"
        
        return True, "User can join"
    
    def calculate_revenue_split(self, total_revenue: float) -> dict:
        """Calculate revenue split among participants"""
        platform_fee = total_revenue * (self.platform_fee_percentage / 100)
        remaining_revenue = total_revenue - platform_fee
        
        creator_share = remaining_revenue * (self.creator_revenue_percentage / 100)
        
        if self.participant_count > 1:
            participant_pool = remaining_revenue - creator_share
            participant_share = participant_pool / (self.participant_count - 1)  # Exclude creator
        else:
            participant_share = 0
        
        return {
            "total_revenue": total_revenue,
            "platform_fee": platform_fee,
            "creator_share": creator_share,
            "participant_share": participant_share,
            "remaining_revenue": remaining_revenue
        }
    
    def set_schedule(self, start_date: datetime, duration_hours: int = None, end_date: datetime = None):
        """Set drop schedule"""
        self.start_date = start_date
        
        if end_date:
            self.end_date = end_date
            self.duration_hours = int((end_date - start_date).total_seconds() / 3600)
        elif duration_hours:
            self.duration_hours = duration_hours
            self.end_date = start_date + timedelta(hours=duration_hours)
        
        # Auto-schedule if currently draft
        if self.status == DropStatus.DRAFT:
            self.status = DropStatus.SCHEDULED
    
    def add_announcement(self, message: str):
        """Add announcement to drop"""
        self.announcement_message = message
        self.last_update_message = f"Announcement: {message[:100]}..."
    
    def feature_drop(self):
        """Feature this drop"""
        self.is_featured = True
    
    def unfeature_drop(self):
        """Remove featured status"""
        self.is_featured = False 