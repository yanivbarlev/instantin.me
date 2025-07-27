from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import re

from app.models.storefront import Storefront
from app.models.user import User
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
    UnauthorizedError,
    ValidationError
)

logger = logging.getLogger(__name__)


class StorefrontService:
    """Service for managing storefront operations"""

    @staticmethod
    async def create_storefront(
        db: AsyncSession,
        storefront_data: StorefrontCreate,
        user_id: UUID
    ) -> StorefrontResponse:
        """
        Create a new storefront for a user
        
        Args:
            db: Database session
            storefront_data: Storefront creation data
            user_id: Owner user ID
            
        Returns:
            Created storefront response
            
        Raises:
            SlugAlreadyExistsError: If slug already exists
            ValidationError: If data validation fails
        """
        try:
            # Check if slug already exists
            existing_slug = await db.execute(
                select(Storefront).where(Storefront.slug == storefront_data.slug)
            )
            if existing_slug.scalar_one_or_none():
                raise SlugAlreadyExistsError(f"Slug '{storefront_data.slug}' already exists")

            # Verify user exists
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValidationError("Invalid user ID")

            # Create storefront instance
            storefront = Storefront(
                user_id=user_id,
                **storefront_data.model_dump()
            )
            
            db.add(storefront)
            await db.commit()
            await db.refresh(storefront)
            
            logger.info(f"✅ Created storefront {storefront.slug} for user {user_id}")
            return StorefrontResponse.model_validate(storefront)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to create storefront: {e}")
            raise

    @staticmethod
    async def get_storefront_by_slug(
        db: AsyncSession,
        slug: str,
        include_unpublished: bool = False
    ) -> Optional[StorefrontResponse]:
        """
        Get storefront by slug
        
        Args:
            db: Database session
            slug: Storefront slug
            include_unpublished: Whether to include unpublished storefronts
            
        Returns:
            Storefront response or None if not found
        """
        try:
            query = select(Storefront).where(Storefront.slug == slug)
            
            if not include_unpublished:
                query = query.where(Storefront.is_published == True)
            
            result = await db.execute(query)
            storefront = result.scalar_one_or_none()
            
            if storefront:
                # Increment view count
                await StorefrontService._increment_view_count(db, storefront.id)
                await db.refresh(storefront)
                return StorefrontResponse.model_validate(storefront)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get storefront by slug {slug}: {e}")
            raise

    @staticmethod
    async def get_storefront_by_id(
        db: AsyncSession,
        storefront_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[StorefrontResponse]:
        """
        Get storefront by ID
        
        Args:
            db: Database session
            storefront_id: Storefront ID
            user_id: Optional user ID for ownership verification
            
        Returns:
            Storefront response or None if not found
        """
        try:
            query = select(Storefront).where(Storefront.id == storefront_id)
            
            if user_id:
                query = query.where(Storefront.user_id == user_id)
            
            result = await db.execute(query)
            storefront = result.scalar_one_or_none()
            
            if storefront:
                return StorefrontResponse.model_validate(storefront)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get storefront by ID {storefront_id}: {e}")
            raise

    @staticmethod
    async def update_storefront(
        db: AsyncSession,
        storefront_id: UUID,
        storefront_data: StorefrontUpdate,
        user_id: UUID
    ) -> StorefrontResponse:
        """
        Update storefront
        
        Args:
            db: Database session
            storefront_id: Storefront ID to update
            storefront_data: Update data
            user_id: Owner user ID
            
        Returns:
            Updated storefront response
            
        Raises:
            StorefrontNotFoundError: If storefront not found
            UnauthorizedError: If user doesn't own storefront
            SlugAlreadyExistsError: If new slug already exists
        """
        try:
            # Get storefront and verify ownership
            storefront = await StorefrontService._get_user_storefront(db, storefront_id, user_id)
            
            # Prepare update data
            update_data = storefront_data.model_dump(exclude_unset=True)
            
            # Check slug uniqueness if being updated
            if 'slug' in update_data and update_data['slug'] != storefront.slug:
                existing_slug = await db.execute(
                    select(Storefront).where(
                        and_(
                            Storefront.slug == update_data['slug'],
                            Storefront.id != storefront_id
                        )
                    )
                )
                if existing_slug.scalar_one_or_none():
                    raise SlugAlreadyExistsError(f"Slug '{update_data['slug']}' already exists")

            # Update timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update publication timestamp if being published
            if update_data.get('is_published') and not storefront.is_published:
                update_data['last_published_at'] = datetime.utcnow()

            # Perform update
            await db.execute(
                update(Storefront)
                .where(Storefront.id == storefront_id)
                .values(**update_data)
            )
            
            await db.commit()
            
            # Get updated storefront
            updated_storefront = await StorefrontService.get_storefront_by_id(db, storefront_id, user_id)
            
            logger.info(f"✅ Updated storefront {storefront_id} for user {user_id}")
            return updated_storefront
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to update storefront {storefront_id}: {e}")
            raise

    @staticmethod
    async def delete_storefront(
        db: AsyncSession,
        storefront_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete storefront
        
        Args:
            db: Database session
            storefront_id: Storefront ID to delete
            user_id: Owner user ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            StorefrontNotFoundError: If storefront not found
            UnauthorizedError: If user doesn't own storefront
        """
        try:
            # Verify ownership
            storefront = await StorefrontService._get_user_storefront(db, storefront_id, user_id)
            
            # Delete storefront (cascade will handle related records)
            await db.execute(
                delete(Storefront).where(Storefront.id == storefront_id)
            )
            
            await db.commit()
            
            logger.info(f"✅ Deleted storefront {storefront_id} for user {user_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to delete storefront {storefront_id}: {e}")
            raise

    @staticmethod
    async def list_user_storefronts(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        per_page: int = 10,
        published_only: bool = False
    ) -> StorefrontListResponse:
        """
        List user's storefronts with pagination
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-based)
            per_page: Items per page
            published_only: Whether to include only published storefronts
            
        Returns:
            Paginated storefront list
        """
        try:
            # Base query
            query = select(Storefront).where(Storefront.user_id == user_id)
            
            if published_only:
                query = query.where(Storefront.is_published == True)
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Paginate
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)
            query = query.order_by(Storefront.updated_at.desc())
            
            result = await db.execute(query)
            storefronts = result.scalars().all()
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page
            
            return StorefrontListResponse(
                storefronts=[StorefrontResponse.model_validate(sf) for sf in storefronts],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to list storefronts for user {user_id}: {e}")
            raise

    @staticmethod
    async def search_storefronts(
        db: AsyncSession,
        query: str,
        page: int = 1,
        per_page: int = 10,
        featured_only: bool = False
    ) -> StorefrontListResponse:
        """
        Search published storefronts
        
        Args:
            db: Database session
            query: Search query
            page: Page number
            per_page: Items per page
            featured_only: Whether to include only featured storefronts
            
        Returns:
            Paginated search results
        """
        try:
            # Build search query
            search_query = select(Storefront).where(
                and_(
                    Storefront.is_published == True,
                    or_(
                        Storefront.name.ilike(f"%{query}%"),
                        Storefront.bio.ilike(f"%{query}%"),
                        Storefront.description.ilike(f"%{query}%")
                    )
                )
            )
            
            if featured_only:
                search_query = search_query.where(Storefront.is_featured == True)
            
            # Count total
            count_query = select(func.count()).select_from(search_query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Paginate and order by relevance (view count)
            offset = (page - 1) * per_page
            search_query = search_query.offset(offset).limit(per_page)
            search_query = search_query.order_by(
                func.cast(Storefront.view_count, db.dialect.name == 'postgresql' and 'INTEGER' or 'SIGNED').desc()
            )
            
            result = await db.execute(search_query)
            storefronts = result.scalars().all()
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page
            
            return StorefrontListResponse(
                storefronts=[StorefrontResponse.model_validate(sf) for sf in storefronts],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to search storefronts with query '{query}': {e}")
            raise

    @staticmethod
    async def get_storefront_stats(
        db: AsyncSession,
        storefront_id: UUID,
        user_id: UUID
    ) -> StorefrontStats:
        """
        Get storefront analytics and statistics
        
        Args:
            db: Database session
            storefront_id: Storefront ID
            user_id: Owner user ID
            
        Returns:
            Storefront statistics
        """
        try:
            # Verify ownership
            storefront = await StorefrontService._get_user_storefront(db, storefront_id, user_id)
            
            # Basic stats from storefront
            view_count = int(storefront.view_count) if storefront.view_count.isdigit() else 0
            click_count = int(storefront.click_count) if storefront.click_count.isdigit() else 0
            
            # TODO: Implement advanced analytics from PageView model
            # For now, return basic stats
            return StorefrontStats(
                view_count=view_count,
                click_count=click_count,
                visitor_count=int(view_count * 0.7),  # Estimated unique visitors
                conversion_rate=round((click_count / max(view_count, 1)) * 100, 2),
                top_referrers=["direct", "instagram.com", "twitter.com"],
                popular_pages=["/", "/products", "/about"]
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats for storefront {storefront_id}: {e}")
            raise

    @staticmethod
    async def _get_user_storefront(
        db: AsyncSession,
        storefront_id: UUID,
        user_id: UUID
    ) -> Storefront:
        """
        Get storefront and verify user ownership
        
        Args:
            db: Database session
            storefront_id: Storefront ID
            user_id: User ID
            
        Returns:
            Storefront model instance
            
        Raises:
            StorefrontNotFoundError: If storefront not found
            UnauthorizedError: If user doesn't own storefront
        """
        result = await db.execute(
            select(Storefront).where(Storefront.id == storefront_id)
        )
        storefront = result.scalar_one_or_none()
        
        if not storefront:
            raise StorefrontNotFoundError(f"Storefront {storefront_id} not found")
        
        if storefront.user_id != user_id:
            raise UnauthorizedError("You don't have permission to access this storefront")
        
        return storefront

    @staticmethod
    async def _increment_view_count(db: AsyncSession, storefront_id: UUID):
        """Increment storefront view count"""
        try:
            await db.execute(
                update(Storefront)
                .where(Storefront.id == storefront_id)
                .values(view_count=func.cast(Storefront.view_count, 'INTEGER') + 1)
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to increment view count for storefront {storefront_id}: {e}")

    @staticmethod
    async def increment_click_count(db: AsyncSession, storefront_id: UUID):
        """Increment storefront click count"""
        try:
            await db.execute(
                update(Storefront)
                .where(Storefront.id == storefront_id)
                .values(click_count=func.cast(Storefront.click_count, 'INTEGER') + 1)
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to increment click count for storefront {storefront_id}: {e}")

    @staticmethod
    def generate_slug_from_name(name: str) -> str:
        """Generate URL-friendly slug from storefront name"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure it meets our validation requirements
        if not slug or len(slug) < 3:
            slug = f"storefront-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return slug[:100]  # Limit to max length 