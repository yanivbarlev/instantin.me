from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class ProductType(str, enum.Enum):
    """Enumeration of product types supported by InstantIn.me platform"""
    DIGITAL = "digital"        # Digital downloads (files, courses, etc.)
    PHYSICAL = "physical"      # Physical goods requiring shipping
    SERVICE = "service"        # Services and consultations
    MEMBERSHIP = "membership"  # Recurring subscriptions
    TIP = "tip"               # Tips and donations
    LINK = "link"             # External links (affiliate, etc.)
    EVENT = "event"           # Events and bookings


class ProductStatus(str, enum.Enum):
    """Product availability status"""
    ACTIVE = "active"         # Available for purchase
    INACTIVE = "inactive"     # Hidden from storefront
    DRAFT = "draft"          # Work in progress
    SOLD_OUT = "sold_out"    # Out of stock
    ARCHIVED = "archived"     # No longer available


class Product(Base):
    """
    Product model for InstantIn.me Link-in-Bio Commerce Platform.
    Supports multiple product types: digital, physical, services, memberships, tips, links, events.
    """
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationship to Storefront
    storefront_id = Column(UUID(as_uuid=True), ForeignKey("storefronts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic product information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)  # For previews/cards
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False, index=True)  # Main price in cents
    compare_at_price = Column(Numeric(10, 2), nullable=True)    # Original price for discounts
    currency = Column(String(3), nullable=False, default="USD") # ISO currency code
    
    # Product classification
    product_type = Column(Enum(ProductType), nullable=False, index=True)
    status = Column(Enum(ProductStatus), nullable=False, default=ProductStatus.DRAFT, index=True)
    
    # Media and assets
    image_url = Column(String(500), nullable=True)              # Main product image
    gallery_urls = Column(Text, nullable=True)                  # JSON array of additional images
    file_url = Column(String(500), nullable=True)               # Digital file download URL
    preview_url = Column(String(500), nullable=True)            # Preview/sample file
    
    # Inventory and availability
    inventory_count = Column(Integer, nullable=True)            # NULL = unlimited
    sold_count = Column(Integer, nullable=False, default=0)     # Total sales
    max_quantity_per_order = Column(Integer, nullable=True)     # Purchase limits
    
    # Digital product specific
    file_size_bytes = Column(Integer, nullable=True)            # File size for downloads
    download_limit = Column(Integer, nullable=True)             # Download attempts per purchase
    file_type = Column(String(50), nullable=True)               # MIME type or extension
    
    # Physical product specific
    weight_grams = Column(Integer, nullable=True)               # For shipping calculations
    dimensions_cm = Column(String(50), nullable=True)           # "10x15x5" format
    requires_shipping = Column(Boolean, nullable=False, default=False)
    
    # Service/Event specific
    duration_minutes = Column(Integer, nullable=True)           # Service duration
    calendar_link = Column(String(500), nullable=True)          # Calendly, etc.
    booking_url = Column(String(500), nullable=True)            # External booking
    location = Column(String(255), nullable=True)               # Physical or virtual
    
    # Membership specific
    billing_interval = Column(String(20), nullable=True)        # monthly, yearly, etc.
    trial_days = Column(Integer, nullable=True)                 # Free trial period
    
    # Link product specific
    external_url = Column(String(500), nullable=True)           # Affiliate/external link
    click_count = Column(Integer, nullable=False, default=0)    # Link analytics
    
    # Tips/donations specific
    suggested_amounts = Column(Text, nullable=True)             # JSON array of suggested tip amounts
    allow_custom_amount = Column(Boolean, nullable=False, default=True)
    minimum_amount = Column(Numeric(10, 2), nullable=True)      # Minimum tip amount
    
    # SEO and discoverability
    slug = Column(String(100), nullable=True, index=True)       # URL-friendly identifier
    meta_title = Column(String(60), nullable=True)              # SEO title
    meta_description = Column(String(160), nullable=True)       # SEO description
    tags = Column(Text, nullable=True)                          # JSON array of tags
    
    # Ordering and display
    sort_order = Column(Integer, nullable=False, default=0)     # Display order in storefront
    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    is_hidden = Column(Boolean, nullable=False, default=False)  # Hidden but available via direct link
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    storefront = relationship("Storefront", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    # Note: Additional relationships will be added as models are created:
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_products_storefront_status', 'storefront_id', 'status'),
        Index('ix_products_type_status', 'product_type', 'status'),
        Index('ix_products_featured_sort', 'is_featured', 'sort_order'),
        Index('ix_products_storefront_sort', 'storefront_id', 'sort_order'),
        Index('ix_products_price_range', 'price', 'status'),
    )
    
    def __init__(self, **kwargs):
        """Initialize product with default values"""
        super().__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self._generate_slug_from_name(self.name)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', type={self.product_type}, price={self.price})>"
    
    # Helper properties
    @property
    def price_display(self) -> str:
        """Get formatted price for display"""
        if self.price == 0:
            return "Free"
        elif self.product_type == ProductType.TIP:
            return f"${self.minimum_amount:.2f}+" if self.minimum_amount else "Pay what you want"
        else:
            return f"${self.price:.2f}"
    
    @property
    def is_available(self) -> bool:
        """Check if product is available for purchase"""
        if self.status != ProductStatus.ACTIVE:
            return False
        if self.inventory_count is not None and self.inventory_count <= 0:
            return False
        return True
    
    @property
    def is_digital(self) -> bool:
        """Check if this is a digital product"""
        return self.product_type == ProductType.DIGITAL
    
    @property
    def is_physical(self) -> bool:
        """Check if this is a physical product"""
        return self.product_type == ProductType.PHYSICAL
    
    @property
    def is_service(self) -> bool:
        """Check if this is a service/booking"""
        return self.product_type in [ProductType.SERVICE, ProductType.EVENT]
    
    @property
    def is_subscription(self) -> bool:
        """Check if this is a recurring subscription"""
        return self.product_type == ProductType.MEMBERSHIP
    
    @property
    def inventory_status(self) -> str:
        """Get inventory status description"""
        if self.inventory_count is None:
            return "Unlimited"
        elif self.inventory_count <= 0:
            return "Sold Out"
        elif self.inventory_count <= 5:
            return f"Low Stock ({self.inventory_count} left)"
        else:
            return f"In Stock ({self.inventory_count} available)"
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage if compare_at_price is set"""
        if not self.compare_at_price or self.compare_at_price <= self.price:
            return 0.0
        return ((self.compare_at_price - self.price) / self.compare_at_price) * 100
    
    @property
    def full_url(self) -> str:
        """Get the full URL for this product"""
        if self.slug:
            return f"https://instantin.me/{self.storefront.slug}/product/{self.slug}"
        else:
            return f"https://instantin.me/{self.storefront.slug}/product/{self.id}"
    
    # Business logic methods
    def _generate_slug_from_name(self, name: str) -> str:
        """Generate URL-friendly slug from product name"""
        import re
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
        slug = slug.strip('-')
        return slug[:100]
    
    def can_purchase(self, quantity: int = 1) -> tuple[bool, str]:
        """Check if product can be purchased with given quantity"""
        if not self.is_available:
            return False, f"Product is not available ({self.status})"
        
        if self.inventory_count is not None:
            if quantity > self.inventory_count:
                return False, f"Insufficient inventory (only {self.inventory_count} available)"
        
        if self.max_quantity_per_order and quantity > self.max_quantity_per_order:
            return False, f"Maximum {self.max_quantity_per_order} per order"
        
        return True, "Available"
    
    def reserve_inventory(self, quantity: int):
        """Reserve inventory for an order"""
        if self.inventory_count is not None:
            self.inventory_count = max(0, self.inventory_count - quantity)
            if self.inventory_count == 0:
                self.status = ProductStatus.SOLD_OUT
    
    def release_inventory(self, quantity: int):
        """Release reserved inventory (e.g., cancelled order)"""
        if self.inventory_count is not None:
            self.inventory_count += quantity
            if self.status == ProductStatus.SOLD_OUT and self.inventory_count > 0:
                self.status = ProductStatus.ACTIVE
    
    def record_sale(self, quantity: int = 1):
        """Record a successful sale"""
        self.sold_count += quantity
    
    def increment_clicks(self):
        """Increment click count for link products"""
        if self.product_type == ProductType.LINK:
            self.click_count += 1
    
    def publish(self):
        """Publish the product"""
        self.status = ProductStatus.ACTIVE
        self.published_at = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the product"""
        self.status = ProductStatus.INACTIVE 