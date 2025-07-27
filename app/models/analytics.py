from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class DeviceType(str, enum.Enum):
    """Device type for analytics"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    BOT = "bot"
    UNKNOWN = "unknown"


class TrafficSource(str, enum.Enum):
    """Traffic source categories"""
    DIRECT = "direct"                   # Direct traffic
    ORGANIC = "organic"                 # Organic search
    SOCIAL = "social"                   # Social media
    REFERRAL = "referral"               # Other websites
    EMAIL = "email"                     # Email campaigns
    PAID = "paid"                       # Paid advertising
    UNKNOWN = "unknown"                 # Unknown source


class PageView(Base):
    """
    PageView model for InstantIn.me Link-in-Bio Commerce Platform.
    Tracks page views and visitor analytics for storefronts and platform pages.
    """
    
    __tablename__ = "page_views"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Page and content identification
    storefront_id = Column(UUID(as_uuid=True), ForeignKey("storefronts.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    drop_id = Column(UUID(as_uuid=True), ForeignKey("drops.id", ondelete="SET NULL"), nullable=True, index=True)
    raffle_id = Column(UUID(as_uuid=True), ForeignKey("raffles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Page details
    page_url = Column(String(2048), nullable=False, index=True)         # Full page URL
    page_path = Column(String(1024), nullable=False, index=True)        # URL path
    page_title = Column(String(255), nullable=True)                     # Page title
    page_type = Column(String(50), nullable=False, index=True)          # storefront, product, drop, etc.
    
    # Visitor identification and tracking
    visitor_ip = Column(String(45), nullable=False, index=True)         # IPv4/IPv6 address
    user_agent = Column(Text, nullable=False)                           # Full user agent string
    session_id = Column(String(255), nullable=True, index=True)         # Session identifier
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Device and browser information
    device_type = Column(Enum(DeviceType), nullable=False, default=DeviceType.UNKNOWN, index=True)
    browser_name = Column(String(100), nullable=True)                   # Chrome, Firefox, Safari, etc.
    browser_version = Column(String(50), nullable=True)                 # Browser version
    operating_system = Column(String(100), nullable=True)               # Windows, macOS, Linux, etc.
    device_model = Column(String(100), nullable=True)                   # iPhone, Samsung Galaxy, etc.
    screen_resolution = Column(String(20), nullable=True)               # 1920x1080, 414x896, etc.
    
    # Geographic information
    country = Column(String(100), nullable=True, index=True)            # Country name
    country_code = Column(String(2), nullable=True, index=True)         # ISO country code
    region = Column(String(100), nullable=True)                         # State/province
    city = Column(String(100), nullable=True)                           # City name
    timezone = Column(String(50), nullable=True)                        # Timezone
    latitude = Column(Numeric(10, 8), nullable=True)                    # Latitude coordinate
    longitude = Column(Numeric(11, 8), nullable=True)                   # Longitude coordinate
    
    # Traffic source and attribution
    traffic_source = Column(Enum(TrafficSource), nullable=False, default=TrafficSource.UNKNOWN, index=True)
    referrer_url = Column(String(2048), nullable=True)                  # Referring page URL
    referrer_domain = Column(String(255), nullable=True, index=True)    # Referring domain
    utm_source = Column(String(255), nullable=True, index=True)         # UTM source parameter
    utm_medium = Column(String(255), nullable=True, index=True)         # UTM medium parameter
    utm_campaign = Column(String(255), nullable=True, index=True)       # UTM campaign parameter
    utm_term = Column(String(255), nullable=True)                       # UTM term parameter
    utm_content = Column(String(255), nullable=True)                    # UTM content parameter
    
    # Engagement and behavior tracking
    time_on_page = Column(Integer, nullable=True)                       # Seconds spent on page
    scroll_depth = Column(Numeric(5, 2), nullable=True)                # Percentage scrolled
    bounce = Column(Boolean, nullable=False, default=False)             # Single page session
    exit_page = Column(Boolean, nullable=False, default=False)          # Last page in session
    conversion = Column(Boolean, nullable=False, default=False)         # Led to purchase/action
    
    # Page load and performance
    load_time = Column(Integer, nullable=True)                          # Page load time in ms
    server_response_time = Column(Integer, nullable=True)               # Server response time in ms
    dom_content_loaded = Column(Integer, nullable=True)                 # DOM ready time in ms
    first_contentful_paint = Column(Integer, nullable=True)             # FCP metric in ms
    
    # A/B testing and experiments
    experiment_id = Column(String(100), nullable=True, index=True)      # A/B test identifier
    variant_id = Column(String(100), nullable=True)                     # Test variant
    
    # Bot and spam detection
    is_bot = Column(Boolean, nullable=False, default=False, index=True) # Identified as bot
    bot_name = Column(String(100), nullable=True)                       # Bot identifier
    spam_score = Column(Numeric(3, 2), nullable=False, default=0)       # Spam likelihood (0-1)
    
    # Custom tracking and metadata
    custom_data = Column(Text, nullable=True)                           # JSON custom tracking data
    tags = Column(Text, nullable=True)                                  # JSON array of tags
    notes = Column(Text, nullable=True)                                 # Manual notes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    storefront = relationship("Storefront", back_populates="page_views")
    product = relationship("Product")
    drop = relationship("Drop")
    raffle = relationship("Raffle")
    user = relationship("User", back_populates="page_views")
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_page_views_storefront_created', 'storefront_id', 'created_at'),
        Index('ix_page_views_date_source', 'created_at', 'traffic_source'),
        Index('ix_page_views_country_device', 'country_code', 'device_type'),
        Index('ix_page_views_utm_tracking', 'utm_source', 'utm_medium', 'utm_campaign'),
        Index('ix_page_views_session_tracking', 'session_id', 'created_at'),
        Index('ix_page_views_conversion_tracking', 'conversion', 'storefront_id', 'created_at'),
        Index('ix_page_views_performance', 'load_time', 'device_type'),
        Index('ix_page_views_engagement', 'time_on_page', 'scroll_depth'),
        Index('ix_page_views_bot_filtering', 'is_bot', 'spam_score'),
        Index('ix_page_views_experiments', 'experiment_id', 'variant_id'),
    )
    
    def __repr__(self):
        return f"<PageView(id={self.id}, storefront_id={self.storefront_id}, page_type='{self.page_type}', country='{self.country}')>"
    
    # Helper properties
    @property
    def is_mobile(self) -> bool:
        """Check if view is from mobile device"""
        return self.device_type == DeviceType.MOBILE
    
    @property
    def is_returning_visitor(self) -> bool:
        """Check if visitor has previous views"""
        return self.user_id is not None
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score based on time and scroll"""
        score = 0.0
        
        # Time on page (40% weight)
        if self.time_on_page:
            # Normalize to 0-1 (5 minutes = perfect score)
            time_score = min(1.0, self.time_on_page / 300)
            score += time_score * 0.4
        
        # Scroll depth (30% weight)
        if self.scroll_depth:
            scroll_score = self.scroll_depth / 100
            score += scroll_score * 0.3
        
        # Non-bounce (30% weight)
        if not self.bounce:
            score += 0.3
        
        return round(score, 3)
    
    @property
    def performance_grade(self) -> str:
        """Get performance grade based on load time"""
        if not self.load_time:
            return "N/A"
        
        if self.load_time <= 1000:  # 1 second
            return "A"
        elif self.load_time <= 2500:  # 2.5 seconds
            return "B"
        elif self.load_time <= 5000:  # 5 seconds
            return "C"
        elif self.load_time <= 10000:  # 10 seconds
            return "D"
        else:
            return "F"
    
    @property
    def source_display(self) -> str:
        """Get formatted traffic source"""
        if self.utm_source:
            return f"{self.traffic_source.title()} ({self.utm_source})"
        return self.traffic_source.title()
    
    @property
    def location_display(self) -> str:
        """Get formatted location"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        
        return ", ".join(parts) if parts else "Unknown"
    
    @property
    def device_display(self) -> str:
        """Get formatted device information"""
        parts = []
        if self.device_model:
            parts.append(self.device_model)
        if self.browser_name:
            browser = self.browser_name
            if self.browser_version:
                browser += f" {self.browser_version}"
            parts.append(browser)
        if self.operating_system:
            parts.append(self.operating_system)
        
        return " | ".join(parts) if parts else self.device_type.title()
    
    @property
    def time_display(self) -> str:
        """Get formatted time on page"""
        if not self.time_on_page:
            return "0s"
        
        if self.time_on_page < 60:
            return f"{self.time_on_page}s"
        elif self.time_on_page < 3600:
            minutes = self.time_on_page // 60
            seconds = self.time_on_page % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = self.time_on_page // 3600
            minutes = (self.time_on_page % 3600) // 60
            return f"{hours}h {minutes}m"
    
    # Business logic methods
    def categorize_traffic_source(self):
        """Automatically categorize traffic source based on referrer"""
        if not self.referrer_domain:
            self.traffic_source = TrafficSource.DIRECT
            return
        
        domain = self.referrer_domain.lower()
        
        # Social media platforms
        social_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'pinterest.com', 'snapchat.com',
            'reddit.com', 'tumblr.com', 'discord.com'
        ]
        
        # Search engines
        search_domains = [
            'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
            'baidu.com', 'yandex.com', 'ask.com'
        ]
        
        # Check UTM parameters first
        if self.utm_medium:
            medium = self.utm_medium.lower()
            if medium in ['social', 'social-media']:
                self.traffic_source = TrafficSource.SOCIAL
            elif medium in ['email', 'newsletter']:
                self.traffic_source = TrafficSource.EMAIL
            elif medium in ['cpc', 'ppc', 'paid', 'ads']:
                self.traffic_source = TrafficSource.PAID
            elif medium == 'organic':
                self.traffic_source = TrafficSource.ORGANIC
            else:
                self.traffic_source = TrafficSource.REFERRAL
        # Check domain patterns
        elif any(social in domain for social in social_domains):
            self.traffic_source = TrafficSource.SOCIAL
        elif any(search in domain for search in search_domains):
            self.traffic_source = TrafficSource.ORGANIC
        else:
            self.traffic_source = TrafficSource.REFERRAL
    
    def detect_device_type(self):
        """Detect device type from user agent"""
        if not self.user_agent:
            self.device_type = DeviceType.UNKNOWN
            return
        
        user_agent = self.user_agent.lower()
        
        # Bot detection
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget']
        if any(indicator in user_agent for indicator in bot_indicators):
            self.device_type = DeviceType.BOT
            self.is_bot = True
            return
        
        # Mobile detection
        mobile_indicators = ['mobile', 'iphone', 'android', 'phone']
        if any(indicator in user_agent for indicator in mobile_indicators):
            self.device_type = DeviceType.MOBILE
            return
        
        # Tablet detection
        tablet_indicators = ['tablet', 'ipad']
        if any(indicator in user_agent for indicator in tablet_indicators):
            self.device_type = DeviceType.TABLET
            return
        
        # Default to desktop
        self.device_type = DeviceType.DESKTOP
    
    def parse_user_agent(self):
        """Parse user agent for browser and OS information"""
        if not self.user_agent:
            return
        
        user_agent = self.user_agent.lower()
        
        # Browser detection
        if 'chrome' in user_agent and 'chromium' not in user_agent:
            self.browser_name = 'Chrome'
        elif 'firefox' in user_agent:
            self.browser_name = 'Firefox'
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            self.browser_name = 'Safari'
        elif 'edge' in user_agent:
            self.browser_name = 'Edge'
        elif 'opera' in user_agent:
            self.browser_name = 'Opera'
        
        # OS detection
        if 'windows' in user_agent:
            self.operating_system = 'Windows'
        elif 'mac os' in user_agent or 'macos' in user_agent:
            self.operating_system = 'macOS'
        elif 'linux' in user_agent:
            self.operating_system = 'Linux'
        elif 'android' in user_agent:
            self.operating_system = 'Android'
        elif 'ios' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
            self.operating_system = 'iOS'
    
    def calculate_spam_score(self):
        """Calculate spam likelihood score"""
        score = 0.0
        
        # Check for suspicious patterns
        if self.is_bot:
            score += 0.5
        
        if self.time_on_page and self.time_on_page < 2:  # Less than 2 seconds
            score += 0.3
        
        if self.referrer_domain and 'spam' in self.referrer_domain.lower():
            score += 0.4
        
        # Multiple rapid requests from same IP (would need additional logic)
        # This is a simplified version
        if not self.user_agent or len(self.user_agent) < 20:
            score += 0.2
        
        self.spam_score = min(1.0, score)
    
    def mark_conversion(self):
        """Mark this page view as leading to conversion"""
        self.conversion = True
    
    def set_exit_page(self):
        """Mark as exit page"""
        self.exit_page = True
    
    def set_bounce(self):
        """Mark as bounce (single page session)"""
        self.bounce = True
    
    def update_engagement(self, time_on_page: int = None, scroll_depth: float = None):
        """Update engagement metrics"""
        if time_on_page is not None:
            self.time_on_page = time_on_page
        if scroll_depth is not None:
            self.scroll_depth = scroll_depth
    
    def set_performance_metrics(self, load_time: int = None, server_time: int = None, 
                              dom_time: int = None, fcp_time: int = None):
        """Set performance timing metrics"""
        if load_time is not None:
            self.load_time = load_time
        if server_time is not None:
            self.server_response_time = server_time
        if dom_time is not None:
            self.dom_content_loaded = dom_time
        if fcp_time is not None:
            self.first_contentful_paint = fcp_time
    
    def set_location(self, country: str = None, country_code: str = None, 
                    region: str = None, city: str = None, timezone: str = None):
        """Set geographic location information"""
        if country:
            self.country = country
        if country_code:
            self.country_code = country_code
        if region:
            self.region = region
        if city:
            self.city = city
        if timezone:
            self.timezone = timezone
    
    def add_custom_data(self, data: dict):
        """Add custom tracking data"""
        import json
        self.custom_data = json.dumps(data)
    
    def get_custom_data(self) -> dict:
        """Get custom tracking data"""
        import json
        if self.custom_data:
            return json.loads(self.custom_data)
        return {}
    
    def add_tags(self, tags: list):
        """Add tracking tags"""
        import json
        self.tags = json.dumps(tags)
    
    def get_tags(self) -> list:
        """Get tracking tags"""
        import json
        if self.tags:
            return json.loads(self.tags)
        return [] 