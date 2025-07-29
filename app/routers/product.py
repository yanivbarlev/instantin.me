from fastapi import APIRouter, Depends, Query, Path, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.product import ProductType, ProductStatus
from app.services.product import ProductService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductStatsResponse,
    ProductCreateUnion,
    DigitalProductCreate,
    PhysicalProductCreate,
    ServiceProductCreate,
    MembershipProductCreate,
    LinkProductCreate,
    TipProductCreate,
    EventProductCreate
)
from app.utils.exceptions import (
    ProductNotFoundError,
    StorefrontNotFoundError,
    UnauthorizedError,
    InsufficientInventoryError
)

# Initialize router
router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product in a storefront (any type)"
)
async def create_product(
    product_data: ProductCreateUnion,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a new product in a storefront. Supports all 7 product types.
    
    **Product Types:**
    - **digital**: Digital downloads, courses, files
    - **physical**: Physical goods requiring shipping
    - **service**: Services and consultations
    - **membership**: Recurring subscriptions
    - **tip**: Tips and donations
    - **link**: External/affiliate links
    - **event**: Events and bookings
    
    **Required Fields:**
    - **storefront_id**: ID of the storefront (must be owned by user)
    - **name**: Product name (1-255 characters)
    - **price**: Product price (0 for free products)
    - **product_type**: One of the supported types
    
    **Type-Specific Requirements:**
    - **Link products**: Must include external_url
    - **Physical products**: Should include weight_grams for shipping
    - **Memberships**: Should include billing_interval
    
    Returns the created product with generated ID and timestamps.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/digital",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a digital product",
    description="Create a digital product with file-specific fields"
)
async def create_digital_product(
    product_data: DigitalProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a digital product with file-specific fields.
    
    **Digital Product Features:**
    - **file_url**: Download file URL (can be set later via upload)
    - **file_size_bytes**: File size in bytes (max 5GB)
    - **download_limit**: Maximum download attempts per purchase
    - **file_type**: MIME type or file extension
    - **preview_url**: Preview or sample file URL
    
    Perfect for: courses, ebooks, software, templates, digital art, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/physical",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a physical product",
    description="Create a physical product with shipping-specific fields"
)
async def create_physical_product(
    product_data: PhysicalProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a physical product with shipping-specific fields.
    
    **Physical Product Features:**
    - **weight_grams**: Product weight for shipping calculations
    - **dimensions_cm**: Product dimensions in LxWxH format
    - **requires_shipping**: Whether shipping is required (default: true)
    - **inventory_count**: Available stock (null = unlimited)
    
    Perfect for: merchandise, books, artwork, handmade goods, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/service",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service product",
    description="Create a service product with booking-specific fields"
)
async def create_service_product(
    product_data: ServiceProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a service product with booking-specific fields.
    
    **Service Product Features:**
    - **duration_minutes**: Service duration for scheduling
    - **calendar_link**: Booking calendar URL (Calendly, etc.)
    - **booking_url**: External booking system URL
    - **location**: Service location (physical or virtual)
    
    Perfect for: consultations, coaching, design services, tutorials, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/membership",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a membership product",
    description="Create a membership product with subscription-specific fields"
)
async def create_membership_product(
    product_data: MembershipProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a membership product with subscription-specific fields.
    
    **Membership Product Features:**
    - **billing_interval**: weekly, monthly, quarterly, yearly
    - **trial_days**: Free trial period in days
    - **price**: Recurring billing amount
    
    Perfect for: premium content, communities, SaaS access, courses, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/link",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a link product",
    description="Create a link product for affiliate/external URLs"
)
async def create_link_product(
    product_data: LinkProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a link product for affiliate/external URLs.
    
    **Link Product Features:**
    - **external_url**: Target URL (required)
    - **price**: Usually 0 for affiliate tracking
    - **click_count**: Automatically tracked analytics
    
    Perfect for: affiliate links, recommendations, external content, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/tip",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tip product",
    description="Create a tip product for donations and support"
)
async def create_tip_product(
    product_data: TipProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create a tip product for donations and support.
    
    **Tip Product Features:**
    - **suggested_amounts**: Pre-set tip amounts (max 10)
    - **allow_custom_amount**: Allow custom tip amounts
    - **minimum_amount**: Minimum tip amount
    - **price**: Default amount (0 = pay what you want)
    
    Perfect for: buy me a coffee, donations, creator support, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.post(
    "/event",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event product",
    description="Create an event product with booking-specific fields"
)
async def create_event_product(
    product_data: EventProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Create an event product with booking-specific fields.
    
    **Event Product Features:**
    - **duration_minutes**: Event duration
    - **location**: Event location (physical address or virtual)
    - **inventory_count**: Maximum attendees (null = unlimited)
    - **calendar_link**: Event booking/registration URL
    
    Perfect for: workshops, webinars, meetups, conferences, classes, etc.
    """
    return await ProductService.create_product(db, product_data, current_user.id)


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List products",
    description="Get paginated list of products with filtering and search"
)
async def list_products(
    storefront_id: Optional[UUID] = Query(None, description="Filter by storefront ID"),
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str = Query("created_at", description="Sort field (created_at, name, price, sold_count)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order (asc or desc)"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductListResponse:
    """
    Get paginated list of products with advanced filtering and search.
    
    **Query Parameters:**
    - **storefront_id**: Filter by specific storefront (optional)
    - **product_type**: Filter by product type (digital, physical, service, etc.)
    - **status**: Filter by status (active, draft, inactive, sold_out)
    - **is_featured**: Filter by featured products only
    - **search**: Search in product name and description
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-100, default: 20)
    - **sort_by**: Sort field (created_at, name, price, sold_count)
    - **sort_order**: Sort direction (asc, desc)
    
    **Authorization:**
    - If authenticated: Shows user's products (including drafts)
    - If not authenticated: Shows only active products from published storefronts
    
    Returns paginated results with metadata including total count.
    """
    user_id = current_user.id if current_user else None
    
    # If no storefront_id specified and user is authenticated, show their products
    if not storefront_id and user_id:
        return await ProductService.list_products(
            db=db,
            user_id=user_id,
            product_type=product_type,
            status=status,
            is_featured=is_featured,
            search=search,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
    else:
        # Show products from specific storefront or public products
        return await ProductService.list_products(
            db=db,
            storefront_id=storefront_id,
            product_type=product_type,
            status=status or ProductStatus.ACTIVE,  # Default to active for public
            is_featured=is_featured,
            search=search,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )


@router.get(
    "/search",
    response_model=ProductListResponse,
    summary="Search products",
    description="Search active products across all published storefronts"
)
async def search_products(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    featured_only: bool = Query(False, description="Only include featured products"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page (max 50)"),
    db: AsyncSession = Depends(get_async_session)
) -> ProductListResponse:
    """
    Search active products across all published storefronts.
    
    **Query Parameters:**
    - **q**: Search query (required, 1-100 characters)
    - **product_type**: Filter by specific product type
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **featured_only**: Only include featured products
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-50, default: 20)
    
    **Search Scope:**
    - Product name and description
    - Only active products from published storefronts
    - Results ranked by relevance (sold count)
    
    Perfect for product discovery and marketplace functionality.
    """
    # TODO: Add price range filtering logic to the service
    return await ProductService.list_products(
        db=db,
        status=ProductStatus.ACTIVE,
        is_featured=featured_only if featured_only else None,
        search=q,
        page=page,
        per_page=per_page,
        sort_by="sold_count",
        sort_order="desc"
    )


@router.get(
    "/me",
    response_model=ProductListResponse,
    summary="Get my products",
    description="Get paginated list of products owned by authenticated user"
)
async def get_my_products(
    storefront_id: Optional[UUID] = Query(None, description="Filter by storefront ID"),
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductListResponse:
    """
    Get paginated list of products owned by the authenticated user.
    
    **Query Parameters:**
    - **storefront_id**: Filter by specific storefront
    - **product_type**: Filter by product type
    - **status**: Filter by status (includes drafts)
    - **is_featured**: Filter by featured products
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-100, default: 20)
    
    **Authorization:** Requires authentication
    
    Returns all products owned by the user across their storefronts.
    """
    return await ProductService.list_products(
        db=db,
        storefront_id=storefront_id,
        user_id=current_user.id,
        product_type=product_type,
        status=status,
        is_featured=is_featured,
        page=page,
        per_page=per_page,
        sort_by="updated_at",
        sort_order="desc"
    )


@router.get(
    "/stats",
    response_model=ProductStatsResponse,
    summary="Get product statistics",
    description="Get analytics and statistics for user's products"
)
async def get_product_stats(
    storefront_id: Optional[UUID] = Query(None, description="Filter by storefront ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductStatsResponse:
    """
    Get analytics and statistics for the authenticated user's products.
    
    **Query Parameters:**
    - **storefront_id**: Filter by specific storefront (optional)
    
    **Authorization:** Requires authentication
    
    **Returns:**
    - Product counts by status (total, active, draft, sold out)
    - Total sales count and revenue
    - Top 5 selling products
    - Performance metrics
    
    Perfect for dashboard analytics and business insights.
    """
    return await ProductService.get_product_stats(
        db=db,
        storefront_id=storefront_id,
        user_id=current_user.id
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Get a specific product by its ID"
)
async def get_product_by_id(
    product_id: UUID = Path(..., description="Product ID"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Get a specific product by its ID.
    
    **Path Parameters:**
    - **product_id**: UUID of the product
    
    **Authorization:**
    - If authenticated: Can view own products (including drafts)
    - If not authenticated: Can only view active products from published storefronts
    
    **Returns:** Complete product data including all type-specific fields
    """
    user_id = current_user.id if current_user else None
    include_inactive = bool(current_user)  # Only show inactive to authenticated users
    
    product = await ProductService.get_product_by_id(
        db=db,
        product_id=product_id,
        user_id=user_id,
        include_inactive=include_inactive
    )
    
    if not product:
        raise ProductNotFoundError()
    
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    description="Update an existing product (owner only)"
)
async def update_product(
    product_id: UUID = Path(..., description="Product ID"),
    product_data: ProductUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Update an existing product. Only the owner can update their product.
    
    **Path Parameters:**
    - **product_id**: UUID of the product to update
    
    **Body:** ProductUpdate schema with optional fields
    - Any field can be updated individually
    - Type-specific fields can be modified
    - Slug changes are validated for uniqueness within storefront
    - Timestamps are automatically updated
    
    **Authorization:** Requires authentication and ownership
    
    Returns the updated product data.
    """
    return await ProductService.update_product(db, product_id, product_data, current_user.id)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete a product (owner only)"
)
async def delete_product(
    product_id: UUID = Path(..., description="Product ID"),
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a product. Only the owner can delete their product.
    
    **Path Parameters:**
    - **product_id**: UUID of the product to delete
    
    **Query Parameters:**
    - **hard_delete**: If true, permanently delete. If false, archive (default)
    
    **Soft Delete (default):**
    - Changes status to "archived"
    - Preserves data for analytics
    - Can be restored if needed
    
    **Hard Delete:**
    - Permanently removes from database
    - Cannot be undone
    - Cascades to related order items
    
    **Authorization:** Requires authentication and ownership
    
    Returns 204 No Content on successful deletion.
    """
    await ProductService.delete_product(db, product_id, current_user.id, soft_delete=not hard_delete)


@router.post(
    "/{product_id}/publish",
    response_model=ProductResponse,
    summary="Publish product",
    description="Publish a product (change status to active)"
)
async def publish_product(
    product_id: UUID = Path(..., description="Product ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Publish a product by changing its status to active.
    
    **Path Parameters:**
    - **product_id**: UUID of the product to publish
    
    **Actions:**
    - Changes status from draft/inactive to active
    - Sets published_at timestamp
    - Makes product visible in storefront
    - Enables purchase functionality
    
    **Authorization:** Requires authentication and ownership
    
    Returns the updated product data.
    """
    return await ProductService.publish_product(db, product_id, current_user.id)


@router.post(
    "/{product_id}/unpublish",
    response_model=ProductResponse,
    summary="Unpublish product",
    description="Unpublish a product (change status to inactive)"
)
async def unpublish_product(
    product_id: UUID = Path(..., description="Product ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ProductResponse:
    """
    Unpublish a product by changing its status to inactive.
    
    **Path Parameters:**
    - **product_id**: UUID of the product to unpublish
    
    **Actions:**
    - Changes status from active to inactive
    - Hides product from storefront
    - Disables purchase functionality
    - Preserves product data
    
    **Authorization:** Requires authentication and ownership
    
    Returns the updated product data.
    """
    return await ProductService.unpublish_product(db, product_id, current_user.id)


@router.post(
    "/{product_id}/reserve",
    summary="Reserve inventory",
    description="Reserve inventory for an order (internal use)"
)
async def reserve_inventory(
    product_id: UUID = Path(..., description="Product ID"),
    quantity: int = Body(..., ge=1, embed=True, description="Quantity to reserve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Reserve inventory for an order. Internal use for order processing.
    
    **Path Parameters:**
    - **product_id**: UUID of the product
    
    **Body:**
    - **quantity**: Quantity to reserve (must be positive)
    
    **Actions:**
    - Reduces available inventory
    - Prevents overselling
    - Changes status to sold_out if inventory reaches 0
    
    **Authorization:** Requires authentication
    
    **Note:** This endpoint is primarily for internal order processing.
    """
    await ProductService.reserve_inventory(db, product_id, quantity)
    return {"message": f"Reserved {quantity} units successfully"}


@router.post(
    "/{product_id}/release",
    summary="Release inventory",
    description="Release reserved inventory (internal use)"
)
async def release_inventory(
    product_id: UUID = Path(..., description="Product ID"),
    quantity: int = Body(..., ge=1, embed=True, description="Quantity to release"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Release reserved inventory (e.g., cancelled order). Internal use.
    
    **Path Parameters:**
    - **product_id**: UUID of the product
    
    **Body:**
    - **quantity**: Quantity to release (must be positive)
    
    **Actions:**
    - Increases available inventory
    - Changes status from sold_out to active if inventory > 0
    
    **Authorization:** Requires authentication
    
    **Note:** This endpoint is primarily for internal order processing.
    """
    await ProductService.release_inventory(db, product_id, quantity)
    return {"message": f"Released {quantity} units successfully"}


@router.post(
    "/{product_id}/sale",
    summary="Record sale",
    description="Record a successful sale (internal use)"
)
async def record_sale(
    product_id: UUID = Path(..., description="Product ID"),
    quantity: int = Body(1, ge=1, embed=True, description="Quantity sold"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Record a successful sale for analytics. Internal use for order processing.
    
    **Path Parameters:**
    - **product_id**: UUID of the product
    
    **Body:**
    - **quantity**: Quantity sold (default: 1)
    
    **Actions:**
    - Increments sold_count for analytics
    - Updates product performance metrics
    
    **Authorization:** Requires authentication
    
    **Note:** This endpoint is primarily for internal order processing.
    """
    await ProductService.record_sale(db, product_id, quantity)
    return {"message": f"Recorded sale of {quantity} units successfully"}