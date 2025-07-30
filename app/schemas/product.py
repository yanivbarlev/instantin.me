from typing import Optional, List, Union
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum
import uuid

from app.models.product import ProductType, ProductStatus


class ProductBaseSchema(BaseModel):
    """Base schema with common product fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Brief description for previews")
    
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Product price")
    compare_at_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Original price for discounts")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO currency code")
    
    product_type: ProductType = Field(..., description="Type of product")
    status: ProductStatus = Field(default=ProductStatus.DRAFT, description="Product status")
    
    # Media
    image_url: Optional[HttpUrl] = Field(None, description="Main product image URL")
    gallery_urls: Optional[List[HttpUrl]] = Field(None, description="Additional product images")
    
    # Inventory
    inventory_count: Optional[int] = Field(None, ge=0, description="Available inventory (null = unlimited)")
    max_quantity_per_order: Optional[int] = Field(None, ge=1, description="Maximum quantity per order")
    
    # SEO and display
    slug: Optional[str] = Field(None, max_length=100, description="URL-friendly identifier")
    meta_title: Optional[str] = Field(None, max_length=60, description="SEO title")
    meta_description: Optional[str] = Field(None, max_length=160, description="SEO description")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    
    sort_order: int = Field(default=0, description="Display order in storefront")
    is_featured: bool = Field(default=False, description="Featured product flag")
    is_hidden: bool = Field(default=False, description="Hidden but accessible via direct link")

    @validator('currency')
    def validate_currency(cls, v):
        """Validate ISO currency code"""
        if v.upper() not in ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']:
            raise ValueError('Currency must be a valid ISO code (USD, EUR, GBP, CAD, AUD, JPY)')
        return v.upper()

    @validator('compare_at_price')
    def validate_compare_at_price(cls, v, values):
        """Ensure compare_at_price is greater than price"""
        if v is not None and 'price' in values and v <= values['price']:
            raise ValueError('Compare at price must be greater than regular price')
        return v

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        if v is not None:
            import re
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


# Type-specific field schemas
class DigitalProductFields(BaseModel):
    """Fields specific to digital products"""
    file_url: Optional[HttpUrl] = Field(None, description="Download file URL")
    preview_url: Optional[HttpUrl] = Field(None, description="Preview/sample file URL")
    file_size_bytes: Optional[int] = Field(None, ge=1, description="File size in bytes")
    download_limit: Optional[int] = Field(None, ge=1, description="Download attempts per purchase")
    file_type: Optional[str] = Field(None, max_length=50, description="File MIME type or extension")

    @validator('file_size_bytes')
    def validate_file_size(cls, v):
        """Ensure file size is within limits (5GB)"""
        if v is not None and v > 5 * 1024 * 1024 * 1024:  # 5GB in bytes
            raise ValueError('File size cannot exceed 5GB')
        return v


class PhysicalProductFields(BaseModel):
    """Fields specific to physical products"""
    weight_grams: Optional[int] = Field(None, ge=1, description="Product weight in grams")
    dimensions_cm: Optional[str] = Field(None, description="Dimensions in LxWxH format (e.g., '10x15x5')")
    requires_shipping: bool = Field(default=True, description="Whether product requires shipping")

    @validator('dimensions_cm')
    def validate_dimensions(cls, v):
        """Validate dimensions format"""
        if v is not None:
            import re
            if not re.match(r'^\d+(\.\d+)?x\d+(\.\d+)?x\d+(\.\d+)?$', v):
                raise ValueError('Dimensions must be in LxWxH format (e.g., "10x15x5")')
        return v


class ServiceProductFields(BaseModel):
    """Fields specific to services and events"""
    duration_minutes: Optional[int] = Field(None, ge=1, description="Service duration in minutes")
    calendar_link: Optional[HttpUrl] = Field(None, description="Booking calendar URL (Calendly, etc.)")
    booking_url: Optional[HttpUrl] = Field(None, description="External booking system URL")
    location: Optional[str] = Field(None, max_length=255, description="Service location (physical or virtual)")


class MembershipProductFields(BaseModel):
    """Fields specific to membership/subscription products"""
    billing_interval: Optional[str] = Field(None, description="Billing frequency")
    trial_days: Optional[int] = Field(None, ge=0, description="Free trial period in days")

    @validator('billing_interval')
    def validate_billing_interval(cls, v):
        """Validate billing interval"""
        if v is not None and v not in ['weekly', 'monthly', 'quarterly', 'yearly']:
            raise ValueError('Billing interval must be: weekly, monthly, quarterly, or yearly')
        return v


class LinkProductFields(BaseModel):
    """Fields specific to link products"""
    external_url: HttpUrl = Field(..., description="External/affiliate link URL")


class TipProductFields(BaseModel):
    """Fields specific to tip/donation products"""
    suggested_amounts: Optional[List[Decimal]] = Field(None, description="Suggested tip amounts")
    allow_custom_amount: bool = Field(default=True, description="Allow custom tip amounts")
    minimum_amount: Optional[Decimal] = Field(None, ge=0.01, decimal_places=2, description="Minimum tip amount")

    @validator('suggested_amounts')
    def validate_suggested_amounts(cls, v):
        """Validate suggested amounts"""
        if v is not None:
            if len(v) > 10:
                raise ValueError('Maximum 10 suggested amounts allowed')
            if any(amount <= 0 for amount in v):
                raise ValueError('All suggested amounts must be positive')
        return v


# Create/Update schemas for each product type
class ProductCreate(ProductBaseSchema):
    """Schema for creating a new product"""
    storefront_id: uuid.UUID = Field(..., description="ID of the storefront this product belongs to")

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Premium Digital Course",
                "description": "Complete guide to building SaaS applications",
                "short_description": "Learn to build SaaS apps from scratch",
                "price": 99.99,
                "compare_at_price": 149.99,
                "currency": "USD",
                "product_type": "digital",
                "status": "draft",
                "image_url": "https://example.com/course-image.jpg",
                "inventory_count": 100,
                "is_featured": True,
                "tags": ["course", "programming", "saas"]
            }
        }


class DigitalProductCreate(ProductCreate, DigitalProductFields):
    """Schema for creating digital products"""
    product_type: ProductType = Field(default=ProductType.DIGITAL, description="Must be 'digital'")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.DIGITAL:
            raise ValueError('Product type must be "digital" for digital products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Premium Digital Course",
                "description": "Complete guide to building SaaS applications",
                "price": 99.99,
                "product_type": "digital",
                "file_url": "https://s3.amazonaws.com/mybucket/course.zip",
                "file_size_bytes": 104857600,
                "download_limit": 3,
                "file_type": "application/zip"
            }
        }


class PhysicalProductCreate(ProductCreate, PhysicalProductFields):
    """Schema for creating physical products"""
    product_type: ProductType = Field(default=ProductType.PHYSICAL, description="Must be 'physical'")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.PHYSICAL:
            raise ValueError('Product type must be "physical" for physical products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Premium T-Shirt",
                "description": "High-quality cotton t-shirt with custom design",
                "price": 29.99,
                "product_type": "physical",
                "weight_grams": 200,
                "dimensions_cm": "25x35x2",
                "requires_shipping": True,
                "inventory_count": 50
            }
        }


class ServiceProductCreate(ProductCreate, ServiceProductFields):
    """Schema for creating service products"""
    product_type: ProductType = Field(default=ProductType.SERVICE, description="Must be 'service'")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.SERVICE:
            raise ValueError('Product type must be "service" for service products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "1-on-1 Consultation",
                "description": "Personal consultation session",
                "price": 150.00,
                "product_type": "service",
                "duration_minutes": 60,
                "calendar_link": "https://calendly.com/username/consultation",
                "location": "Virtual (Zoom)"
            }
        }


class MembershipProductCreate(ProductCreate, MembershipProductFields):
    """Schema for creating membership products"""
    product_type: ProductType = Field(default=ProductType.MEMBERSHIP, description="Must be 'membership'")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.MEMBERSHIP:
            raise ValueError('Product type must be "membership" for membership products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Premium Membership",
                "description": "Access to all premium content and features",
                "price": 19.99,
                "product_type": "membership",
                "billing_interval": "monthly",
                "trial_days": 7
            }
        }


class LinkProductCreate(ProductCreate, LinkProductFields):
    """Schema for creating link products"""
    product_type: ProductType = Field(default=ProductType.LINK, description="Must be 'link'")
    price: Decimal = Field(default=0, ge=0, description="Price for affiliate tracking (usually 0)")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.LINK:
            raise ValueError('Product type must be "link" for link products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Recommended Book",
                "description": "My favorite book on entrepreneurship",
                "price": 0,
                "product_type": "link",
                "external_url": "https://amazon.com/book-link?ref=affiliate123"
            }
        }


class TipProductCreate(ProductCreate, TipProductFields):
    """Schema for creating tip/donation products"""
    product_type: ProductType = Field(default=ProductType.TIP, description="Must be 'tip'")
    price: Decimal = Field(default=0, ge=0, description="Default tip amount (0 for pay-what-you-want)")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.TIP:
            raise ValueError('Product type must be "tip" for tip products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Buy me a coffee",
                "description": "Support my work with a tip",
                "price": 0,
                "product_type": "tip",
                "suggested_amounts": [5.00, 10.00, 25.00],
                "minimum_amount": 1.00,
                "allow_custom_amount": True
            }
        }


class EventProductCreate(ProductCreate, ServiceProductFields):
    """Schema for creating event products"""
    product_type: ProductType = Field(default=ProductType.EVENT, description="Must be 'event'")

    @validator('product_type')
    def validate_product_type(cls, v):
        if v != ProductType.EVENT:
            raise ValueError('Product type must be "event" for event products')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Workshop: Building APIs",
                "description": "Hands-on workshop for API development",
                "price": 75.00,
                "product_type": "event",
                "duration_minutes": 180,
                "location": "San Francisco, CA",
                "inventory_count": 20
            }
        }


# Update schemas
class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    compare_at_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    status: Optional[ProductStatus] = None
    
    image_url: Optional[HttpUrl] = None
    gallery_urls: Optional[List[HttpUrl]] = None
    
    inventory_count: Optional[int] = Field(None, ge=0)
    max_quantity_per_order: Optional[int] = Field(None, ge=1)
    
    slug: Optional[str] = Field(None, max_length=100)
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    tags: Optional[List[str]] = None
    
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None
    is_hidden: Optional[bool] = None

    # Type-specific fields (all optional for updates)
    # Digital
    file_url: Optional[HttpUrl] = None
    preview_url: Optional[HttpUrl] = None
    file_size_bytes: Optional[int] = Field(None, ge=1)
    download_limit: Optional[int] = Field(None, ge=1)
    file_type: Optional[str] = Field(None, max_length=50)
    
    # Physical
    weight_grams: Optional[int] = Field(None, ge=1)
    dimensions_cm: Optional[str] = None
    requires_shipping: Optional[bool] = None
    
    # Service/Event
    duration_minutes: Optional[int] = Field(None, ge=1)
    calendar_link: Optional[HttpUrl] = None
    booking_url: Optional[HttpUrl] = None
    location: Optional[str] = Field(None, max_length=255)
    
    # Membership
    billing_interval: Optional[str] = None
    trial_days: Optional[int] = Field(None, ge=0)
    
    # Link
    external_url: Optional[HttpUrl] = None
    
    # Tip
    suggested_amounts: Optional[List[Decimal]] = None
    allow_custom_amount: Optional[bool] = None
    minimum_amount: Optional[Decimal] = Field(None, ge=0.01, decimal_places=2)

    @validator('compare_at_price')
    def validate_compare_at_price(cls, v, values):
        if v is not None and 'price' in values and values['price'] is not None and v <= values['price']:
            raise ValueError('Compare at price must be greater than regular price')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Product Name",
                "price": 79.99,
                "status": "active",
                "is_featured": True
            }
        }


# Response schemas
class ProductResponse(ProductBaseSchema):
    """Schema for product API responses"""
    id: uuid.UUID
    storefront_id: uuid.UUID
    sold_count: int
    click_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    # Include all type-specific fields for complete response
    # Digital fields
    file_url: Optional[HttpUrl]
    preview_url: Optional[HttpUrl]
    file_size_bytes: Optional[int]
    download_limit: Optional[int]
    file_type: Optional[str]
    
    # Physical fields
    weight_grams: Optional[int]
    dimensions_cm: Optional[str]
    requires_shipping: bool
    
    # Service/Event fields
    duration_minutes: Optional[int]
    calendar_link: Optional[HttpUrl]
    booking_url: Optional[HttpUrl]
    location: Optional[str]
    
    # Membership fields
    billing_interval: Optional[str]
    trial_days: Optional[int]
    
    # Link fields
    external_url: Optional[HttpUrl]
    
    # Tip fields
    suggested_amounts: Optional[List[Decimal]]
    allow_custom_amount: bool
    minimum_amount: Optional[Decimal]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "storefront_id": "660e8400-e29b-41d4-a716-446655440001",
                "name": "Premium Digital Course",
                "description": "Complete guide to building SaaS applications",
                "price": 99.99,
                "product_type": "digital",
                "status": "active",
                "sold_count": 42,
                "click_count": 0,
                "is_featured": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ProductListResponse(BaseModel):
    """Schema for paginated product list responses"""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "products": [],
                "total": 25,
                "page": 1,
                "per_page": 10,
                "total_pages": 3
            }
        }


class ProductStatsResponse(BaseModel):
    """Schema for product statistics"""
    total_products: int
    active_products: int
    draft_products: int
    sold_out_products: int
    total_sales: int
    total_revenue: Decimal
    top_selling_products: List[ProductResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total_products": 15,
                "active_products": 12,
                "draft_products": 2,
                "sold_out_products": 1,
                "total_sales": 234,
                "total_revenue": 12567.89,
                "top_selling_products": []
            }
        }


# Union type for create schemas
ProductCreateUnion = Union[
    DigitalProductCreate,
    PhysicalProductCreate,
    ServiceProductCreate,
    MembershipProductCreate,
    LinkProductCreate,
    TipProductCreate,
    EventProductCreate
]