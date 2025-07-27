from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid
import enum
import calendar

from app.database import Base


class RaffleStatus(str, enum.Enum):
    """Raffle lifecycle status"""
    UPCOMING = "upcoming"               # Raffle announced but not started
    ACTIVE = "active"                  # Currently accepting entries
    PAUSED = "paused"                  # Temporarily paused
    DRAWING = "drawing"                # Winner selection in progress
    COMPLETED = "completed"            # Winners selected and announced
    CANCELLED = "cancelled"            # Raffle cancelled


class RaffleType(str, enum.Enum):
    """Type of raffle"""
    MONTHLY = "monthly"                # Regular monthly raffle
    SPECIAL = "special"                # Special event raffle
    HOLIDAY = "holiday"                # Holiday-themed raffle
    MILESTONE = "milestone"            # Platform milestone celebration
    SPONSORED = "sponsored"            # Sponsored by partners


class PrizeType(str, enum.Enum):
    """Type of prize offered"""
    CASH = "cash"                      # Cash prize
    CREDIT = "credit"                  # Platform credit
    PRODUCT = "product"                # Physical/digital product
    EXPERIENCE = "experience"          # Experience or service
    GIFT_CARD = "gift_card"           # Gift card
    BUNDLE = "bundle"                  # Multiple prizes


class Raffle(Base):
    """
    Raffle model for InstantIn.me Link-in-Bio Commerce Platform.
    Manages monthly raffles and special prize draws for community engagement.
    """
    
    __tablename__ = "raffles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Raffle identification and timing
    title = Column(String(255), nullable=False)                    # Raffle title
    slug = Column(String(255), nullable=False, unique=True, index=True) # URL-friendly identifier
    description = Column(Text, nullable=True)                      # Raffle description
    month = Column(Integer, nullable=False, index=True)            # Month (1-12)
    year = Column(Integer, nullable=False, index=True)             # Year
    
    # Raffle status and type
    status = Column(Enum(RaffleStatus), nullable=False, default=RaffleStatus.UPCOMING, index=True)
    raffle_type = Column(Enum(RaffleType), nullable=False, default=RaffleType.MONTHLY, index=True)
    
    # Raffle schedule
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    drawing_date = Column(DateTime(timezone=True), nullable=False)
    announcement_date = Column(DateTime(timezone=True), nullable=True)
    
    # Prize pool and configuration
    total_prize_pool = Column(Numeric(12, 2), nullable=False, default=0) # Total prize value
    cash_prize_amount = Column(Numeric(10, 2), nullable=True)           # Cash portion
    credit_prize_amount = Column(Numeric(10, 2), nullable=True)         # Platform credit portion
    number_of_winners = Column(Integer, nullable=False, default=1)       # Total winners
    grand_prize_amount = Column(Numeric(10, 2), nullable=True)          # Grand prize value
    
    # Entry requirements and limits
    max_entries_per_user = Column(Integer, nullable=False, default=100)  # Entry limit per user
    min_sales_requirement = Column(Numeric(10, 2), nullable=False, default=0) # Min sales to enter
    min_account_age_days = Column(Integer, nullable=False, default=0)    # Account age requirement
    requires_storefront = Column(Boolean, nullable=False, default=False) # Must have storefront
    requires_sales = Column(Boolean, nullable=False, default=False)      # Must have made sales
    
    # Entry mechanics
    tickets_per_dollar_spent = Column(Numeric(5, 2), nullable=False, default=1.0) # Tickets per $1
    bonus_multiplier = Column(Numeric(3, 2), nullable=False, default=1.0)         # Bonus multiplier
    referral_bonus_tickets = Column(Integer, nullable=False, default=0)           # Bonus for referrals
    social_share_bonus = Column(Integer, nullable=False, default=0)               # Bonus for sharing
    
    # Tracking and analytics
    total_entries = Column(Integer, nullable=False, default=0)           # Total entries submitted
    total_participants = Column(Integer, nullable=False, default=0)      # Unique participants
    total_tickets = Column(Integer, nullable=False, default=0)           # Total tickets issued
    page_views = Column(Integer, nullable=False, default=0)              # Raffle page views
    social_shares = Column(Integer, nullable=False, default=0)           # Social media shares
    
    # Winners and results
    winners_selected = Column(Boolean, nullable=False, default=False)    # Winners drawn
    winners_announced = Column(Boolean, nullable=False, default=False)   # Winners public
    winners_data = Column(Text, nullable=True)                          # JSON of winners
    drawing_notes = Column(Text, nullable=True)                         # Drawing process notes
    
    # Content and media
    featured_image_url = Column(String(500), nullable=True)             # Main raffle image
    banner_image_url = Column(String(500), nullable=True)              # Banner image
    video_url = Column(String(500), nullable=True)                     # Promotional video
    gallery_urls = Column(Text, nullable=True)                         # JSON array of images
    
    # Marketing and promotion
    promotional_message = Column(Text, nullable=True)                   # Marketing message
    rules_text = Column(Text, nullable=True)                           # Complete rules
    terms_and_conditions = Column(Text, nullable=True)                 # Legal terms
    hashtags = Column(Text, nullable=True)                             # JSON array of hashtags
    
    # Configuration and settings
    is_public = Column(Boolean, nullable=False, default=True)          # Visible publicly
    is_featured = Column(Boolean, nullable=False, default=False)       # Featured raffle
    auto_announce_winners = Column(Boolean, nullable=False, default=True) # Auto announce
    allow_duplicate_entries = Column(Boolean, nullable=False, default=False) # Multiple entries
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    launched_at = Column(DateTime(timezone=True), nullable=True)        # When raffle went live
    completed_at = Column(DateTime(timezone=True), nullable=True)       # When drawing completed
    
    # Relationships
    # Note: Relationship will be added when RaffleEntry is defined below
    # entries = relationship("RaffleEntry", back_populates="raffle", cascade="all, delete-orphan")
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_raffles_month_year', 'month', 'year'),
        Index('ix_raffles_status_type', 'status', 'raffle_type'),
        Index('ix_raffles_dates', 'start_date', 'end_date'),
        Index('ix_raffles_public_featured', 'is_public', 'is_featured'),
        Index('ix_raffles_winners', 'winners_selected', 'winners_announced'),
        # Unique constraint for monthly raffles
        Index('ix_raffles_monthly_unique', 'month', 'year', 'raffle_type', unique=True),
    )
    
    def __repr__(self):
        return f"<Raffle(id={self.id}, title='{self.title}', month={self.month}/{self.year}, prize_pool=${self.total_prize_pool})>"
    
    # Helper properties
    @property
    def is_active(self) -> bool:
        """Check if raffle is currently active"""
        return self.status == RaffleStatus.ACTIVE
    
    @property
    def is_upcoming(self) -> bool:
        """Check if raffle is upcoming"""
        return self.status == RaffleStatus.UPCOMING
    
    @property
    def is_completed(self) -> bool:
        """Check if raffle is completed"""
        return self.status == RaffleStatus.COMPLETED
    
    @property
    def can_enter(self) -> bool:
        """Check if users can enter this raffle"""
        now = datetime.utcnow()
        return (self.status == RaffleStatus.ACTIVE and 
                now >= self.start_date and 
                now <= self.end_date)
    
    @property
    def time_remaining(self) -> timedelta:
        """Get time remaining to enter"""
        if not self.can_enter:
            return timedelta(0)
        
        now = datetime.utcnow()
        if now >= self.end_date:
            return timedelta(0)
        
        return self.end_date - now
    
    @property
    def days_until_drawing(self) -> int:
        """Get days until drawing"""
        now = datetime.utcnow()
        if now >= self.drawing_date:
            return 0
        return (self.drawing_date - now).days
    
    @property
    def month_name(self) -> str:
        """Get month name"""
        return calendar.month_name[self.month]
    
    @property
    def display_title(self) -> str:
        """Get display title"""
        if self.title:
            return self.title
        return f"{self.month_name} {self.year} Raffle"
    
    @property
    def prize_pool_display(self) -> str:
        """Get formatted prize pool"""
        return f"${self.total_prize_pool:,.2f}"
    
    @property
    def participation_rate(self) -> float:
        """Calculate participation rate (entries per view)"""
        if self.page_views <= 0:
            return 0.0
        return (self.total_entries / self.page_views) * 100
    
    @property
    def average_tickets_per_user(self) -> float:
        """Calculate average tickets per participant"""
        if self.total_participants <= 0:
            return 0.0
        return self.total_tickets / self.total_participants
    
    @property
    def full_url(self) -> str:
        """Get full raffle URL"""
        return f"https://instantin.me/raffles/{self.slug}"
    
    # Business logic methods
    def generate_slug(self):
        """Generate URL-friendly slug"""
        import re
        if self.title:
            base = self.title.lower()
        else:
            base = f"{self.month_name.lower()}-{self.year}-raffle"
        
        slug = re.sub(r'[^\w\s-]', '', base)
        slug = re.sub(r'[-\s]+', '-', slug)
        self.slug = slug.strip('-')
    
    def launch_raffle(self):
        """Launch the raffle"""
        if self.status == RaffleStatus.UPCOMING:
            self.status = RaffleStatus.ACTIVE
            self.launched_at = datetime.utcnow()
    
    def pause_raffle(self):
        """Pause the raffle"""
        if self.status == RaffleStatus.ACTIVE:
            self.status = RaffleStatus.PAUSED
    
    def resume_raffle(self):
        """Resume a paused raffle"""
        if self.status == RaffleStatus.PAUSED:
            self.status = RaffleStatus.ACTIVE
    
    def start_drawing(self):
        """Begin winner selection process"""
        if self.status == RaffleStatus.ACTIVE:
            self.status = RaffleStatus.DRAWING
    
    def complete_raffle(self, winners_data: dict = None):
        """Complete raffle with winners"""
        self.status = RaffleStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.winners_selected = True
        
        if winners_data:
            import json
            self.winners_data = json.dumps(winners_data)
            
        if self.auto_announce_winners:
            self.announce_winners()
    
    def announce_winners(self):
        """Announce raffle winners"""
        self.winners_announced = True
        self.announcement_date = datetime.utcnow()
    
    def cancel_raffle(self, reason: str = None):
        """Cancel the raffle"""
        self.status = RaffleStatus.CANCELLED
        if reason:
            self.drawing_notes = f"Cancelled: {reason}"
    
    def record_page_view(self):
        """Record a page view"""
        self.page_views += 1
    
    def record_social_share(self):
        """Record a social media share"""
        self.social_shares += 1
    
    def add_entry(self, tickets: int = 1):
        """Add entry to raffle totals"""
        self.total_entries += 1
        self.total_tickets += tickets
    
    def add_participant(self):
        """Add new participant to count"""
        self.total_participants += 1
    
    def calculate_prize_breakdown(self) -> dict:
        """Calculate prize distribution"""
        prizes = []
        remaining_pool = float(self.total_prize_pool)
        
        if self.grand_prize_amount and self.number_of_winners >= 1:
            prizes.append({
                "place": 1,
                "amount": float(self.grand_prize_amount),
                "type": "Grand Prize"
            })
            remaining_pool -= float(self.grand_prize_amount)
        
        # Distribute remaining among other winners
        if self.number_of_winners > 1 and remaining_pool > 0:
            other_winners = self.number_of_winners - 1
            amount_per_winner = remaining_pool / other_winners
            
            for i in range(2, self.number_of_winners + 1):
                prizes.append({
                    "place": i,
                    "amount": amount_per_winner,
                    "type": f"{self._ordinal(i)} Place"
                })
        
        return prizes
    
    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return f"{n}{suffix}"
    
    def get_winners_data(self) -> dict:
        """Get winners data as dictionary"""
        import json
        if self.winners_data:
            return json.loads(self.winners_data)
        return {}
    
    def set_schedule(self, start_date: datetime, end_date: datetime, drawing_date: datetime = None):
        """Set raffle schedule"""
        self.start_date = start_date
        self.end_date = end_date
        
        if drawing_date:
            self.drawing_date = drawing_date
        else:
            # Default: drawing 1 day after end
            self.drawing_date = end_date + timedelta(days=1)
    
    def feature_raffle(self):
        """Feature this raffle"""
        self.is_featured = True
    
    def unfeature_raffle(self):
        """Remove featured status"""
        self.is_featured = False


class RaffleEntry(Base):
    """
    RaffleEntry model for InstantIn.me Link-in-Bio Commerce Platform.
    Represents individual user entries in raffles with ticket tracking.
    """
    
    __tablename__ = "raffle_entries"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    raffle_id = Column(UUID(as_uuid=True), ForeignKey("raffles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Entry details
    ticket_count = Column(Integer, nullable=False, default=1)           # Number of tickets
    entry_method = Column(String(50), nullable=False, default="purchase") # How tickets were earned
    qualifying_amount = Column(Numeric(10, 2), nullable=True)          # Amount that qualified for tickets
    bonus_tickets = Column(Integer, nullable=False, default=0)         # Bonus tickets earned
    referral_tickets = Column(Integer, nullable=False, default=0)      # Tickets from referrals
    
    # Entry source tracking
    source_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True) # Source order
    source_storefront_id = Column(UUID(as_uuid=True), ForeignKey("storefronts.id"), nullable=True) # Source storefront
    referral_code = Column(String(50), nullable=True)                  # Referral code used
    utm_source = Column(String(100), nullable=True)                    # Marketing source
    
    # Entry validation
    is_valid = Column(Boolean, nullable=False, default=True)           # Entry is valid
    validation_notes = Column(Text, nullable=True)                     # Validation details
    disqualified = Column(Boolean, nullable=False, default=False)      # Disqualified entry
    disqualification_reason = Column(Text, nullable=True)              # Reason for disqualification
    
    # Winner status
    is_winner = Column(Boolean, nullable=False, default=False)         # Won a prize
    prize_place = Column(Integer, nullable=True)                       # Prize placement (1st, 2nd, etc.)
    prize_amount = Column(Numeric(10, 2), nullable=True)               # Prize value won
    prize_claimed = Column(Boolean, nullable=False, default=False)     # Prize claimed
    prize_claim_date = Column(DateTime(timezone=True), nullable=True)  # When prize was claimed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    raffle = relationship("Raffle", back_populates="entries")
    user = relationship("User", back_populates="raffle_entries")
    source_order = relationship("Order")
    source_storefront = relationship("Storefront")
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_raffle_entries_raffle_user', 'raffle_id', 'user_id'),
        Index('ix_raffle_entries_raffle_tickets', 'raffle_id', 'ticket_count'),
        Index('ix_raffle_entries_user_created', 'user_id', 'created_at'),
        Index('ix_raffle_entries_winners', 'is_winner', 'prize_place'),
        Index('ix_raffle_entries_valid', 'is_valid', 'disqualified'),
        Index('ix_raffle_entries_source', 'source_order_id', 'source_storefront_id'),
    )
    
    def __repr__(self):
        return f"<RaffleEntry(id={self.id}, raffle_id={self.raffle_id}, user_id={self.user_id}, tickets={self.total_tickets})>"
    
    # Helper properties
    @property
    def total_tickets(self) -> int:
        """Get total tickets including bonuses"""
        return self.ticket_count + self.bonus_tickets + self.referral_tickets
    
    @property
    def is_qualified(self) -> bool:
        """Check if entry is qualified"""
        return self.is_valid and not self.disqualified
    
    @property
    def prize_display(self) -> str:
        """Get formatted prize amount"""
        if not self.prize_amount:
            return "N/A"
        return f"${self.prize_amount:.2f}"
    
    @property
    def place_display(self) -> str:
        """Get formatted prize place"""
        if not self.prize_place:
            return "N/A"
        
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(self.prize_place % 10, 4)]
        if 11 <= (self.prize_place % 100) <= 13:
            suffix = 'th'
        return f"{self.prize_place}{suffix} Place"
    
    @property
    def tickets_display(self) -> str:
        """Get formatted ticket count"""
        total = self.total_tickets
        if total == 1:
            return "1 ticket"
        return f"{total} tickets"
    
    # Business logic methods
    def add_bonus_tickets(self, count: int, reason: str = None):
        """Add bonus tickets to entry"""
        self.bonus_tickets += count
        if reason and self.validation_notes:
            self.validation_notes += f"\nBonus: +{count} tickets ({reason})"
        elif reason:
            self.validation_notes = f"Bonus: +{count} tickets ({reason})"
    
    def add_referral_tickets(self, count: int):
        """Add referral tickets to entry"""
        self.referral_tickets += count
    
    def disqualify_entry(self, reason: str):
        """Disqualify this entry"""
        self.disqualified = True
        self.disqualification_reason = reason
        self.is_valid = False
    
    def mark_as_winner(self, place: int, amount: float):
        """Mark entry as winner"""
        self.is_winner = True
        self.prize_place = place
        self.prize_amount = amount
    
    def claim_prize(self):
        """Mark prize as claimed"""
        if self.is_winner:
            self.prize_claimed = True
            self.prize_claim_date = datetime.utcnow()
    
    def validate_entry(self, notes: str = None):
        """Validate entry"""
        self.is_valid = True
        if notes:
            self.validation_notes = notes
    
    def invalidate_entry(self, reason: str):
        """Invalidate entry"""
        self.is_valid = False
        self.validation_notes = reason


# Add the relationship back to Raffle now that RaffleEntry is defined
Raffle.entries = relationship("RaffleEntry", back_populates="raffle", cascade="all, delete-orphan") 