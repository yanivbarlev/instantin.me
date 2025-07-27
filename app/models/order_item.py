from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class OrderItem(Base):
    """
    OrderItem model for InstantIn.me Link-in-Bio Commerce Platform.
    Represents individual products within an order (line items).
    """
    
    __tablename__ = "order_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Product details at time of purchase (for order history integrity)
    product_name = Column(String(255), nullable=False)              # Product name when ordered
    product_description = Column(Text, nullable=True)               # Product description when ordered
    product_type = Column(String(50), nullable=False)               # Product type when ordered
    
    # Quantity and pricing
    quantity = Column(Integer, nullable=False, default=1)           # Number of items ordered
    unit_price = Column(Numeric(10, 2), nullable=False)            # Price per unit at time of purchase
    total_price = Column(Numeric(10, 2), nullable=False)           # Total for this line item
    currency = Column(String(3), nullable=False, default="USD")     # ISO currency code
    
    # Discounts and promotions
    original_unit_price = Column(Numeric(10, 2), nullable=True)    # Original price before discounts
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0) # Discount applied per unit
    discount_code = Column(String(50), nullable=True)              # Promo code used
    
    # Digital product specific
    download_url = Column(String(500), nullable=True)              # Secure download link
    download_expires_at = Column(DateTime(timezone=True), nullable=True) # Download expiration
    download_attempts = Column(Integer, nullable=False, default=0) # Number of downloads
    max_downloads = Column(Integer, nullable=True)                 # Download limit
    
    # Physical product specific
    weight_grams = Column(Integer, nullable=True)                  # Item weight for shipping
    requires_shipping = Column(Boolean, nullable=False, default=False)
    shipped_separately = Column(Boolean, nullable=False, default=False) # Ships separate from other items
    
    # Service/Event specific
    scheduled_date = Column(DateTime(timezone=True), nullable=True) # Service/event date
    duration_minutes = Column(Integer, nullable=True)              # Service duration
    location = Column(String(255), nullable=True)                  # Service location
    booking_confirmed = Column(Boolean, nullable=False, default=False)
    
    # Membership specific
    subscription_starts_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    billing_cycle = Column(String(20), nullable=True)              # monthly, yearly, etc.
    
    # Fulfillment tracking
    fulfillment_status = Column(String(50), nullable=True)         # pending, shipped, delivered, etc.
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)  # When item was fulfilled
    tracking_number = Column(String(255), nullable=True)           # Individual item tracking
    
    # Customer customization
    customization_options = Column(Text, nullable=True)            # JSON of custom options
    customer_notes = Column(Text, nullable=True)                   # Customer notes for this item
    
    # Inventory tracking
    inventory_reserved_at = Column(DateTime(timezone=True), nullable=True) # When inventory was reserved
    inventory_committed_at = Column(DateTime(timezone=True), nullable=True) # When inventory was committed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_order_items_order_product', 'order_id', 'product_id'),
        Index('ix_order_items_product_created', 'product_id', 'created_at'),
        Index('ix_order_items_fulfillment_status', 'fulfillment_status', 'fulfilled_at'),
        Index('ix_order_items_download_tracking', 'download_attempts', 'max_downloads'),
        Index('ix_order_items_subscription_dates', 'subscription_starts_at', 'subscription_ends_at'),
    )
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product='{self.product_name}', qty={self.quantity}, total={self.total_price})>"
    
    # Helper properties
    @property
    def line_total_display(self) -> str:
        """Get formatted line total for display"""
        if self.total_price == 0:
            return "Free"
        return f"${self.total_price:.2f}"
    
    @property
    def unit_price_display(self) -> str:
        """Get formatted unit price for display"""
        if self.unit_price == 0:
            return "Free"
        return f"${self.unit_price:.2f}"
    
    @property
    def has_discount(self) -> bool:
        """Check if item has a discount applied"""
        return self.discount_amount > 0
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage"""
        if not self.original_unit_price or self.original_unit_price <= self.unit_price:
            return 0.0
        return ((self.original_unit_price - self.unit_price) / self.original_unit_price) * 100
    
    @property
    def is_digital(self) -> bool:
        """Check if this is a digital product item"""
        return self.product_type == "digital"
    
    @property
    def is_physical(self) -> bool:
        """Check if this is a physical product item"""
        return self.product_type == "physical"
    
    @property
    def is_service(self) -> bool:
        """Check if this is a service item"""
        return self.product_type in ["service", "event"]
    
    @property
    def is_subscription(self) -> bool:
        """Check if this is a subscription item"""
        return self.product_type == "membership"
    
    @property
    def can_download(self) -> bool:
        """Check if digital item can still be downloaded"""
        if not self.is_digital or not self.download_url:
            return False
        
        # Check download expiration
        if self.download_expires_at and datetime.utcnow() > self.download_expires_at:
            return False
        
        # Check download limit
        if self.max_downloads and self.download_attempts >= self.max_downloads:
            return False
        
        return True
    
    @property
    def downloads_remaining(self) -> int:
        """Get remaining download attempts"""
        if not self.max_downloads:
            return -1  # Unlimited
        return max(0, self.max_downloads - self.download_attempts)
    
    @property
    def subscription_active(self) -> bool:
        """Check if subscription is currently active"""
        if not self.is_subscription:
            return False
        
        now = datetime.utcnow()
        
        if self.subscription_starts_at and now < self.subscription_starts_at:
            return False
        
        if self.subscription_ends_at and now > self.subscription_ends_at:
            return False
        
        return True
    
    # Business logic methods
    def calculate_total(self):
        """Calculate total price for this line item"""
        self.total_price = (self.unit_price - self.discount_amount) * self.quantity
    
    def apply_discount(self, discount_amount: float, discount_code: str = None):
        """Apply discount to this line item"""
        if not self.original_unit_price:
            self.original_unit_price = self.unit_price
        
        self.discount_amount = discount_amount
        self.discount_code = discount_code
        self.unit_price = self.original_unit_price - discount_amount
        self.calculate_total()
    
    def record_download(self):
        """Record a download attempt"""
        if self.is_digital:
            self.download_attempts += 1
            # Update the related product's download count as well
            if self.product:
                self.product.record_sale(0)  # Don't increment sold count, just track activity
    
    def mark_fulfilled(self, tracking_number: str = None):
        """Mark this item as fulfilled"""
        self.fulfillment_status = "fulfilled"
        self.fulfilled_at = datetime.utcnow()
        if tracking_number:
            self.tracking_number = tracking_number
    
    def generate_download_url(self, base_url: str = "https://instantin.me") -> str:
        """Generate secure download URL for digital products"""
        if not self.is_digital:
            return ""
        
        # This would typically generate a signed URL with expiration
        # For now, return a placeholder structure
        return f"{base_url}/download/{self.id}/{self.order_id}"
    
    def set_download_expiration(self, days: int = 30):
        """Set download expiration date"""
        if self.is_digital:
            self.download_expires_at = datetime.utcnow() + datetime.timedelta(days=days)
    
    def activate_subscription(self, start_date: datetime = None, duration_months: int = 1):
        """Activate subscription for membership items"""
        if self.is_subscription:
            self.subscription_starts_at = start_date or datetime.utcnow()
            # Calculate end date based on billing cycle
            if self.billing_cycle == "yearly":
                duration_months = 12
            elif self.billing_cycle == "monthly":
                duration_months = 1
            
            # Add duration to start date
            import calendar
            from dateutil.relativedelta import relativedelta
            self.subscription_ends_at = self.subscription_starts_at + relativedelta(months=duration_months)
    
    def reserve_inventory(self):
        """Reserve inventory for this item"""
        self.inventory_reserved_at = datetime.utcnow()
        if self.product:
            self.product.reserve_inventory(self.quantity)
    
    def commit_inventory(self):
        """Commit reserved inventory"""
        self.inventory_committed_at = datetime.utcnow()
        if self.product:
            self.product.record_sale(self.quantity)
    
    def release_inventory(self):
        """Release reserved inventory (e.g., order cancelled)"""
        if self.product and self.inventory_reserved_at and not self.inventory_committed_at:
            self.product.release_inventory(self.quantity)
        self.inventory_reserved_at = None
    
    def confirm_booking(self, scheduled_date: datetime = None, location: str = None):
        """Confirm booking for service/event items"""
        if self.is_service:
            self.booking_confirmed = True
            if scheduled_date:
                self.scheduled_date = scheduled_date
            if location:
                self.location = location 