from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID, Index, Numeric, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    """Order processing status"""
    PENDING = "pending"               # Order created, awaiting payment
    PROCESSING = "processing"         # Payment received, order being fulfilled
    SHIPPED = "shipped"              # Physical products shipped
    DELIVERED = "delivered"          # Order completed successfully
    CANCELLED = "cancelled"          # Order cancelled before fulfillment
    REFUNDED = "refunded"           # Payment refunded
    FAILED = "failed"               # Payment or processing failed
    DRAFT = "draft"                 # Incomplete order (cart state)


class PaymentProvider(str, enum.Enum):
    """Payment processing provider"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MANUAL = "manual"               # Manual/offline payment
    FREE = "free"                   # Free products


class Order(Base):
    """
    Order model for InstantIn.me Link-in-Bio Commerce Platform.
    Handles order processing, payment tracking, and fulfillment.
    """
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationship to Storefront
    storefront_id = Column(UUID(as_uuid=True), ForeignKey("storefronts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Customer information
    buyer_email = Column(String(255), nullable=False, index=True)
    buyer_name = Column(String(255), nullable=True)
    buyer_phone = Column(String(50), nullable=True)
    
    # Shipping information (for physical products)
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Billing information
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)
    
    # Order totals and pricing
    subtotal_amount = Column(Numeric(10, 2), nullable=False)        # Items total before fees
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)   # Tax amount
    shipping_amount = Column(Numeric(10, 2), nullable=False, default=0) # Shipping cost
    platform_fee_amount = Column(Numeric(10, 2), nullable=False, default=0) # InstantIn.me fee
    total_amount = Column(Numeric(10, 2), nullable=False, index=True) # Final total
    currency = Column(String(3), nullable=False, default="USD")      # ISO currency code
    
    # Payment processing
    payment_provider = Column(Enum(PaymentProvider), nullable=False, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True, unique=True)
    paypal_order_id = Column(String(255), nullable=True, unique=True, index=True)
    paypal_capture_id = Column(String(255), nullable=True, unique=True)
    
    # Order status and workflow
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DRAFT, index=True)
    fulfillment_status = Column(String(50), nullable=True)           # shipped, delivered, etc.
    
    # Customer communication
    customer_notes = Column(Text, nullable=True)                     # Customer order notes
    internal_notes = Column(Text, nullable=True)                     # Internal fulfillment notes
    
    # Tracking and fulfillment
    tracking_number = Column(String(255), nullable=True)             # Shipping tracking
    tracking_url = Column(String(500), nullable=True)                # Carrier tracking URL
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)    # Payment confirmed
    shipped_at = Column(DateTime(timezone=True), nullable=True)      # Order shipped
    delivered_at = Column(DateTime(timezone=True), nullable=True)    # Order delivered
    
    # Fraud and risk management
    risk_score = Column(Numeric(3, 2), nullable=True)               # 0.00 to 1.00 risk score
    is_flagged_for_review = Column(Boolean, nullable=False, default=False)
    reviewed_by_admin = Column(Boolean, nullable=False, default=False)
    
    # Digital delivery
    download_attempts = Column(Integer, nullable=False, default=0)   # For digital products
    last_download_at = Column(DateTime(timezone=True), nullable=True)
    
    # Refund information
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    storefront = relationship("Storefront", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    # Note: Additional relationships will be added as models are created:
    
    # Table indexes for performance
    __table_args__ = (
        Index('ix_orders_storefront_status', 'storefront_id', 'status'),
        Index('ix_orders_buyer_email_created', 'buyer_email', 'created_at'),
        Index('ix_orders_status_created', 'status', 'created_at'),
        Index('ix_orders_payment_provider_status', 'payment_provider', 'status'),
        Index('ix_orders_total_created', 'total_amount', 'created_at'),
        Index('ix_orders_flagged_review', 'is_flagged_for_review', 'reviewed_by_admin'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, storefront_id={self.storefront_id}, total={self.total_amount}, status={self.status})>"
    
    # Helper properties
    @property
    def order_number(self) -> str:
        """Generate human-readable order number"""
        # Use last 8 characters of UUID for shorter order numbers
        return f"ORD-{str(self.id)[-8:].upper()}"
    
    @property
    def is_paid(self) -> bool:
        """Check if order has been paid"""
        return self.status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
    
    @property
    def is_complete(self) -> bool:
        """Check if order is completed"""
        return self.status == OrderStatus.DELIVERED
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]
    
    @property
    def can_be_refunded(self) -> bool:
        """Check if order can be refunded"""
        return self.status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
    
    @property
    def shipping_address(self) -> dict:
        """Get formatted shipping address"""
        if not self.shipping_address_line1:
            return {}
        
        return {
            "line1": self.shipping_address_line1,
            "line2": self.shipping_address_line2,
            "city": self.shipping_city,
            "state": self.shipping_state,
            "postal_code": self.shipping_postal_code,
            "country": self.shipping_country
        }
    
    @property
    def billing_address(self) -> dict:
        """Get formatted billing address"""
        if not self.billing_address_line1:
            return {}
        
        return {
            "line1": self.billing_address_line1,
            "line2": self.billing_address_line2,
            "city": self.billing_city,
            "state": self.billing_state,
            "postal_code": self.billing_postal_code,
            "country": self.billing_country
        }
    
    @property
    def payment_info(self) -> dict:
        """Get payment processing information"""
        return {
            "provider": self.payment_provider,
            "stripe_payment_intent": self.stripe_payment_intent_id,
            "stripe_charge": self.stripe_charge_id,
            "paypal_order": self.paypal_order_id,
            "paypal_capture": self.paypal_capture_id
        }
    
    @property
    def total_display(self) -> str:
        """Get formatted total for display"""
        if self.total_amount == 0:
            return "Free"
        return f"${self.total_amount:.2f}"
    
    # Business logic methods
    def calculate_platform_fee(self, fee_percentage: float = 0.029) -> float:
        """Calculate platform fee (default 2.9%)"""
        return float(self.subtotal_amount * fee_percentage)
    
    def update_totals(self):
        """Recalculate order totals"""
        # This will be enhanced when OrderItems are implemented
        self.total_amount = self.subtotal_amount + self.tax_amount + self.shipping_amount + self.platform_fee_amount
    
    def confirm_payment(self, payment_intent_id: str = None, charge_id: str = None):
        """Confirm payment and update order status"""
        self.status = OrderStatus.PROCESSING
        self.confirmed_at = datetime.utcnow()
        
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
        if charge_id:
            self.stripe_charge_id = charge_id
    
    def mark_shipped(self, tracking_number: str = None, tracking_url: str = None):
        """Mark order as shipped"""
        self.status = OrderStatus.SHIPPED
        self.shipped_at = datetime.utcnow()
        
        if tracking_number:
            self.tracking_number = tracking_number
        if tracking_url:
            self.tracking_url = tracking_url
    
    def mark_delivered(self):
        """Mark order as delivered"""
        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
    
    def cancel_order(self, reason: str = None):
        """Cancel the order"""
        self.status = OrderStatus.CANCELLED
        if reason:
            self.internal_notes = f"Cancelled: {reason}"
    
    def process_refund(self, amount: float, reason: str = None):
        """Process a refund for the order"""
        self.status = OrderStatus.REFUNDED
        self.refund_amount = amount
        self.refund_reason = reason
        self.refunded_at = datetime.utcnow()
    
    def flag_for_review(self, risk_score: float = None):
        """Flag order for manual review"""
        self.is_flagged_for_review = True
        if risk_score:
            self.risk_score = risk_score
    
    def approve_after_review(self):
        """Approve order after manual review"""
        self.reviewed_by_admin = True
        self.is_flagged_for_review = False
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.PROCESSING
    
    def record_download(self):
        """Record a download attempt for digital products"""
        self.download_attempts += 1
        self.last_download_at = datetime.utcnow()
    
    def set_shipping_address(self, address: dict):
        """Set shipping address from dictionary"""
        self.shipping_address_line1 = address.get('line1')
        self.shipping_address_line2 = address.get('line2')
        self.shipping_city = address.get('city')
        self.shipping_state = address.get('state')
        self.shipping_postal_code = address.get('postal_code')
        self.shipping_country = address.get('country')
    
    def set_billing_address(self, address: dict):
        """Set billing address from dictionary"""
        self.billing_address_line1 = address.get('line1')
        self.billing_address_line2 = address.get('line2')
        self.billing_city = address.get('city')
        self.billing_state = address.get('state')
        self.billing_postal_code = address.get('postal_code')
        self.billing_country = address.get('country') 