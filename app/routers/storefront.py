from fastapi import APIRouter, Depends, Query, Path, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.storefront import StorefrontService
from app.schemas.storefront import (
    StorefrontCreate,
    StorefrontUpdate, 
    StorefrontResponse,
    StorefrontListResponse,
    StorefrontStats
)
from app.utils.exceptions import (
    StorefrontNotFoundError,
    SlugAlreadyExistsError,
    UnauthorizedError
)

# Initialize router and templates
router = APIRouter(prefix="/storefronts", tags=["storefronts"])
templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/",
    response_model=StorefrontResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new storefront",
    description="Create a new storefront for the authenticated user"
)
async def create_storefront(
    storefront_data: StorefrontCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontResponse:
    """
    Create a new storefront for the authenticated user.
    
    - **name**: Display name for the storefront
    - **slug**: URL-friendly identifier (must be unique)
    - **description**: Detailed description (optional)
    - **bio**: Short bio or tagline (optional)
    - **theme**: Theme preset (light, dark, custom)
    - **primary_color**: Brand primary color in hex format
    - **accent_color**: Brand accent color in hex format
    - **Social links**: Instagram, Twitter, TikTok, YouTube, LinkedIn, Website
    - **SEO settings**: Meta title and description
    - **Platform settings**: Enable/disable features
    - **is_published**: Whether storefront is publicly accessible
    
    Returns the created storefront with generated ID and timestamps.
    """
    return await StorefrontService.create_storefront(db, storefront_data, current_user.id)


@router.get(
    "/me",
    response_model=StorefrontListResponse,
    summary="Get current user's storefronts",
    description="Get paginated list of storefronts owned by the authenticated user"
)
async def get_my_storefronts(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    published_only: bool = Query(False, description="Only include published storefronts"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontListResponse:
    """
    Get paginated list of storefronts owned by the authenticated user.
    
    Query parameters:
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-100, default: 10)
    - **published_only**: Filter to only published storefronts (default: false)
    
    Returns paginated list with metadata including total count and page information.
    """
    return await StorefrontService.list_user_storefronts(
        db, current_user.id, page, per_page, published_only
    )


@router.get(
    "/search",
    response_model=StorefrontListResponse,
    summary="Search public storefronts",
    description="Search published storefronts by name, bio, or description"
)
async def search_storefronts(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    featured_only: bool = Query(False, description="Only include featured storefronts"),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontListResponse:
    """
    Search published storefronts by name, bio, or description.
    
    Query parameters:
    - **q**: Search query (required, 1-100 characters)
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-50, default: 10)
    - **featured_only**: Filter to only featured storefronts (default: false)
    
    Results are ranked by relevance (view count) and only include published storefronts.
    """
    return await StorefrontService.search_storefronts(db, q, page, per_page, featured_only)


@router.get(
    "/{slug}",
    response_model=StorefrontResponse,
    summary="Get storefront by slug",
    description="Get a published storefront by its URL slug"
)
async def get_storefront_by_slug(
    slug: str = Path(..., min_length=3, max_length=100, description="Storefront URL slug"),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontResponse:
    """
    Get a published storefront by its URL slug.
    
    This endpoint:
    - Only returns published storefronts
    - Automatically increments the view count
    - Tracks analytics for the storefront
    
    Path parameters:
    - **slug**: URL-friendly storefront identifier
    
    Returns the storefront data or 404 if not found/unpublished.
    """
    storefront = await StorefrontService.get_storefront_by_slug(db, slug)
    if not storefront:
        raise StorefrontNotFoundError(f"Storefront '{slug}' not found")
    return storefront


# Demo endpoint for testing without database (MUST come before /{slug}/page)
@router.get(
    "/demo/page",
    response_class=HTMLResponse,
    summary="Demo storefront page",
    description="Demo storefront page with sample data (works without database)"
)
async def demo_storefront_page(request: Request) -> HTMLResponse:
    """
    Demo storefront page with sample data for testing the UI.
    
    This endpoint works without database connection and shows:
    - Beautiful responsive design
    - Interactive animations
    - Social media integration
    - Link cards with hover effects
    - Product showcases
    - Analytics dashboard
    - All visual features working
    
    Perfect for testing the visual interface!
    """
    # Sample storefront data for demo
    demo_storefront = {
        "id": "demo-id",
        "name": "Alex Johnson",
        "slug": "alex-johnson",
        "tagline": "Digital Creator & Designer",
        "bio": "🎨 Helping businesses create stunning visuals | 📱 Social media expert | ✨ Available for freelance projects",
        "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face&auto=format",
        "cover_image_url": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&h=300&fit=crop&auto=format",
        "website_url": "https://alexjohnson.design",
        "contact_email": "hello@alexjohnson.design",
        "theme": "light",
        "primary_color": "#3B82F6",
        "accent_color": "#EF4444",
        "is_verified": True,
        "enable_analytics": True,
        "view_count": 2847,
        "click_count": 892,
        "instagram_url": "https://instagram.com/alexjohnson",
        "twitter_url": "https://twitter.com/alexjohnson",
        "tiktok_url": "https://tiktok.com/@alexjohnson",
        "youtube_url": "https://youtube.com/c/alexjohnson",
        "linkedin_url": "https://linkedin.com/in/alexjohnson",
        "cta_text": "Book a Free Consultation",
        "cta_url": "https://calendly.com/alexjohnson",
        "links": [
            {
                "title": "Portfolio Website",
                "description": "Check out my latest design work",
                "url": "https://alexjohnson.design/portfolio",
                "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=50&h=50&fit=crop&auto=format"
            },
            {
                "title": "Free Design Resources",
                "description": "Download my free Figma templates",
                "url": "https://alexjohnson.design/freebies",
                "image_url": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=50&h=50&fit=crop&auto=format"
            },
            {
                "title": "Design Course",
                "description": "Learn UI/UX design from scratch",
                "url": "https://alexjohnson.design/course",
                "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=50&h=50&fit=crop&auto=format"
            },
            {
                "title": "Newsletter",
                "description": "Weekly design tips and inspiration",
                "url": "https://alexjohnson.design/newsletter",
                "image_url": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=50&h=50&fit=crop&auto=format"
            },
            {
                "title": "1-on-1 Mentoring",
                "description": "Personalized design mentorship",
                "url": "https://alexjohnson.design/mentoring",
                "image_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=50&h=50&fit=crop&auto=format"
            }
        ],
        "products": [
            {
                "name": "Logo Design Package",
                "description": "Professional logo design with 3 concepts",
                "price": 299.99,
                "image_url": "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=200&h=150&fit=crop&auto=format"
            },
            {
                "name": "Website Template",
                "description": "Modern Figma website template",
                "price": 49.99,
                "image_url": "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=200&h=150&fit=crop&auto=format"
            },
            {
                "name": "Brand Guidelines",
                "description": "Complete brand identity package",
                "price": 199.99,
                "image_url": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=200&h=150&fit=crop&auto=format"
            },
            {
                "name": "UI Kit",
                "description": "Comprehensive design system",
                "price": 79.99,
                "image_url": "https://images.unsplash.com/photo-1551650975-87deedd944c3?w=200&h=150&fit=crop&auto=format"
            }
        ]
    }
    
    # Create a simple object to mimic the storefront model
    class DemoStorefront:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)
    
    storefront = DemoStorefront(demo_storefront)
    
    return templates.TemplateResponse(
        "storefront.html",
        {
            "request": request,
            "storefront": storefront
        }
    )


@router.get(
    "/{slug}/page",
    response_class=HTMLResponse,
    summary="Render storefront page",
    description="Render the HTML page for a storefront by slug"
)
async def render_storefront_page(
    request: Request,
    slug: str = Path(..., description="Storefront slug"),
    db: AsyncSession = Depends(get_async_session)
) -> HTMLResponse:
    """
    Render the beautiful HTML page for a storefront.
    
    Path parameters:
    - **slug**: Unique storefront slug
    
    Returns a fully rendered HTML page with:
    - Responsive design optimized for mobile and desktop
    - Dynamic theming based on storefront settings
    - SEO optimization with meta tags
    - Social media integration
    - Interactive elements and animations
    - Analytics tracking
    - Social sharing capabilities
    
    The page includes all storefront content:
    - Profile information and bio
    - Social media links with beautiful icons
    - Custom links with descriptions and images
    - Featured products (if any)
    - Call-to-action buttons
    - Contact information
    - Analytics dashboard (if enabled)
    
    This endpoint serves the actual user-facing storefront page that visitors see.
    """
    # Get storefront data
    storefront = await StorefrontService.get_storefront_by_slug(db, slug)
    
    # Render the template with storefront data
    return templates.TemplateResponse(
        "storefront.html",
        {
            "request": request,
            "storefront": storefront
        }
    )


@router.put(
    "/{storefront_id}",
    response_model=StorefrontResponse,
    summary="Update storefront",
    description="Update an existing storefront (owner only)"
)
async def update_storefront(
    storefront_id: UUID = Path(..., description="Storefront ID"),
    storefront_data: StorefrontUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontResponse:
    """
    Update an existing storefront. Only the owner can update their storefront.
    
    Path parameters:
    - **storefront_id**: UUID of the storefront to update
    
    Body: StorefrontUpdate schema with optional fields
    - Any field can be updated individually
    - Slug changes are validated for uniqueness
    - Timestamps are automatically updated
    - Publication date is set when first published
    
    Returns the updated storefront data.
    """
    return await StorefrontService.update_storefront(db, storefront_id, storefront_data, current_user.id)


@router.delete(
    "/{storefront_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete storefront",
    description="Delete a storefront (owner only)"
)
async def delete_storefront(
    storefront_id: UUID = Path(..., description="Storefront ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a storefront. Only the owner can delete their storefront.
    
    Path parameters:
    - **storefront_id**: UUID of the storefront to delete
    
    This operation:
    - Permanently deletes the storefront
    - Cascades to delete related products, orders, etc.
    - Cannot be undone
    - Requires ownership verification
    
    Returns 204 No Content on successful deletion.
    """
    await StorefrontService.delete_storefront(db, storefront_id, current_user.id)


@router.get(
    "/{storefront_id}/stats",
    response_model=StorefrontStats,
    summary="Get storefront analytics",
    description="Get analytics and statistics for a storefront (owner only)"
)
async def get_storefront_stats(
    storefront_id: UUID = Path(..., description="Storefront ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontStats:
    """
    Get analytics and statistics for a storefront. Only the owner can view stats.
    
    Path parameters:
    - **storefront_id**: UUID of the storefront
    
    Returns comprehensive analytics including:
    - View count and click count
    - Unique visitor estimates
    - Conversion rate calculation
    - Top referral sources
    - Popular pages
    
    Note: Advanced analytics will be enhanced when PageView integration is complete.
    """
    return await StorefrontService.get_storefront_stats(db, storefront_id, current_user.id)


@router.post(
    "/{storefront_id}/click",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Track click event",
    description="Track a click event on a storefront (for analytics)"
)
async def track_click(
    storefront_id: UUID = Path(..., description="Storefront ID"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Track a click event on a storefront for analytics purposes.
    
    Path parameters:
    - **storefront_id**: UUID of the storefront where click occurred
    
    This endpoint:
    - Increments the click count for analytics
    - Used by frontend to track user interactions
    - Helps calculate conversion rates
    - Anonymous (no authentication required)
    
    Returns 204 No Content after tracking the click.
    """
    await StorefrontService.increment_click_count(db, storefront_id)


# Admin endpoints (for platform management)
@router.get(
    "/admin/featured",
    response_model=StorefrontListResponse,
    summary="Get featured storefronts (Admin)",
    description="Get list of featured storefronts for platform showcase"
)
async def get_featured_storefronts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_async_session)
) -> StorefrontListResponse:
    """
    Get list of featured storefronts for platform showcase.
    
    This endpoint returns storefronts marked as featured by platform admins.
    Used for homepage, discovery pages, and marketing.
    
    Query parameters:
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-100, default: 20)
    
    Returns paginated list of featured storefronts.
    """
    return await StorefrontService.search_storefronts(
        db, query="", page=page, per_page=per_page, featured_only=True
    )


# Utility endpoints
@router.post(
    "/utils/generate-slug",
    summary="Generate slug from name",
    description="Generate a URL-friendly slug from a storefront name"
)
async def generate_slug(
    name: str = Query(..., min_length=1, max_length=255, description="Storefront name")
) -> dict:
    """
    Generate a URL-friendly slug from a storefront name.
    
    Query parameters:
    - **name**: Storefront name to convert to slug
    
    Returns suggested slug that can be used for storefront creation.
    Note: Slug uniqueness still needs to be verified during creation.
    """
    slug = StorefrontService.generate_slug_from_name(name)
    return {"suggested_slug": slug, "original_name": name} 