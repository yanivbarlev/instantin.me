from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import logging
import json

from app.models.product import Product, ProductType, ProductStatus
from app.models.storefront import Storefront
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductStatsResponse,
    DigitalProductCreate,
    PhysicalProductCreate,
    ServiceProductCreate,
    MembershipProductCreate,
    LinkProductCreate,
    TipProductCreate,
    EventProductCreate,
    ProductCreateUnion
)
from app.utils.exceptions import (
    ProductNotFoundError,
    StorefrontNotFoundError,
    UnauthorizedError,
    ValidationError,
    InsufficientInventoryError,
    SlugAlreadyExistsError
)

logger = logging.getLogger(__name__)


class ProductService:
    """Service for managing product operations across all product types"""

    @staticmethod
    async def create_product(
        db: AsyncSession,
        product_data: ProductCreateUnion,
        user_id: UUID
    ) -> ProductResponse:
        """
        Create a new product for a storefront
        
        Args:
            db: Database session
            product_data: Product creation data (any product type)
            user_id: User ID for ownership verification
            
        Returns:
            Created product response
            
        Raises:
            StorefrontNotFoundError: If storefront doesn't exist or user doesn't own it
            SlugAlreadyExistsError: If slug already exists in the storefront
            ValidationError: If data validation fails
        """
        try:
            # Verify storefront exists and user owns it
            storefront_result = await db.execute(
                select(Storefront).where(
                    and_(
                        Storefront.id == product_data.storefront_id,
                        Storefront.user_id == user_id
                    )
                )
            )
            storefront = storefront_result.scalar_one_or_none()
            if not storefront:
                raise StorefrontNotFoundError("Storefront not found or not owned by user")

            # Check slug uniqueness within storefront if provided
            if product_data.slug:
                existing_slug = await db.execute(
                    select(Product).where(
                        and_(
                            Product.storefront_id == product_data.storefront_id,
                            Product.slug == product_data.slug
                        )
                    )
                )
                if existing_slug.scalar_one_or_none():
                    raise SlugAlreadyExistsError(f"Slug '{product_data.slug}' already exists in this storefront")

            # Validate type-specific requirements
            await ProductService._validate_product_data(product_data)

            # Create product instance
            product_dict = product_data.model_dump(exclude_unset=True)
            
            # Handle JSON fields
            if hasattr(product_data, 'gallery_urls') and product_data.gallery_urls:
                product_dict['gallery_urls'] = json.dumps([str(url) for url in product_data.gallery_urls])
            
            if hasattr(product_data, 'tags') and product_data.tags:
                product_dict['tags'] = json.dumps(product_data.tags)
                
            if hasattr(product_data, 'suggested_amounts') and product_data.suggested_amounts:
                product_dict['suggested_amounts'] = json.dumps([float(amount) for amount in product_data.suggested_amounts])

            product = Product(**product_dict)
            
            # Auto-generate slug if not provided
            if not product.slug and product.name:
                product.slug = await ProductService._generate_unique_slug(db, product.name, product.storefront_id)
            
            db.add(product)
            await db.commit()
            await db.refresh(product)
            
            logger.info(f"✅ Created {product.product_type} product '{product.name}' for storefront {storefront.slug}")
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to create product: {e}")
            raise

    @staticmethod
    async def get_product_by_id(
        db: AsyncSession,
        product_id: UUID,
        user_id: Optional[UUID] = None,
        include_inactive: bool = False
    ) -> Optional[ProductResponse]:
        """
        Get product by ID
        
        Args:
            db: Database session
            product_id: Product ID
            user_id: Optional user ID for ownership verification
            include_inactive: Whether to include inactive products
            
        Returns:
            Product response or None if not found
        """
        try:
            query = select(Product).options(selectinload(Product.storefront))
            query = query.where(Product.id == product_id)
            
            if not include_inactive:
                query = query.where(Product.status != ProductStatus.ARCHIVED)
            
            result = await db.execute(query)
            product = result.scalar_one_or_none()
            
            if not product:
                return None
                
            # Check ownership if user_id provided
            if user_id and product.storefront.user_id != user_id:
                raise UnauthorizedError("Not authorized to access this product")
            
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            logger.error(f"❌ Failed to get product by ID {product_id}: {e}")
            raise

    @staticmethod
    async def get_product_by_slug(
        db: AsyncSession,
        storefront_slug: str,
        product_slug: str,
        track_view: bool = True
    ) -> Optional[ProductResponse]:
        """
        Get product by storefront slug and product slug
        
        Args:
            db: Database session
            storefront_slug: Storefront slug
            product_slug: Product slug
            track_view: Whether to track the view (for analytics)
            
        Returns:
            Product response or None if not found
        """
        try:
            query = select(Product).join(Storefront).where(
                and_(
                    Storefront.slug == storefront_slug,
                    Product.slug == product_slug,
                    Product.status == ProductStatus.ACTIVE,
                    Storefront.is_published == True
                )
            )
            
            result = await db.execute(query)
            product = result.scalar_one_or_none()
            
            if product and track_view:
                # Increment click count for link products or product views for others
                if product.product_type == ProductType.LINK:
                    product.click_count += 1
                    await db.commit()
            
            return ProductResponse.model_validate(product) if product else None
            
        except Exception as e:
            logger.error(f"❌ Failed to get product by slug {storefront_slug}/{product_slug}: {e}")
            raise

    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: UUID,
        product_data: ProductUpdate,
        user_id: UUID
    ) -> ProductResponse:
        """
        Update an existing product
        
        Args:
            db: Database session
            product_id: Product ID to update
            product_data: Product update data
            user_id: User ID for ownership verification
            
        Returns:
            Updated product response
            
        Raises:
            ProductNotFoundError: If product doesn't exist
            UnauthorizedError: If user doesn't own the product
            SlugAlreadyExistsError: If new slug already exists
        """
        try:
            # Get product with storefront
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.storefront))
                .where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()
                
            if product.storefront.user_id != user_id:
                raise UnauthorizedError("Not authorized to update this product")

            # Check slug uniqueness if being updated
            if product_data.slug and product_data.slug != product.slug:
                existing_slug = await db.execute(
                    select(Product).where(
                        and_(
                            Product.storefront_id == product.storefront_id,
                            Product.slug == product_data.slug,
                            Product.id != product_id
                        )
                    )
                )
                if existing_slug.scalar_one_or_none():
                    raise SlugAlreadyExistsError(f"Slug '{product_data.slug}' already exists in this storefront")

            # Update fields
            update_data = product_data.model_dump(exclude_unset=True)
            
            # Handle JSON fields
            if 'gallery_urls' in update_data and update_data['gallery_urls']:
                update_data['gallery_urls'] = json.dumps([str(url) for url in update_data['gallery_urls']])
            
            if 'tags' in update_data and update_data['tags']:
                update_data['tags'] = json.dumps(update_data['tags'])
                
            if 'suggested_amounts' in update_data and update_data['suggested_amounts']:
                update_data['suggested_amounts'] = json.dumps([float(amount) for amount in update_data['suggested_amounts']])

            # Apply updates
            for field, value in update_data.items():
                setattr(product, field, value)
            
            await db.commit()
            await db.refresh(product)
            
            logger.info(f"✅ Updated product '{product.name}' (ID: {product_id})")
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to update product {product_id}: {e}")
            raise

    @staticmethod
    async def delete_product(
        db: AsyncSession,
        product_id: UUID,
        user_id: UUID,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a product (soft delete by default)
        
        Args:
            db: Database session
            product_id: Product ID to delete
            user_id: User ID for ownership verification
            soft_delete: Whether to soft delete (archive) or hard delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ProductNotFoundError: If product doesn't exist
            UnauthorizedError: If user doesn't own the product
        """
        try:
            # Get product with storefront
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.storefront))
                .where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()
                
            if product.storefront.user_id != user_id:
                raise UnauthorizedError("Not authorized to delete this product")

            if soft_delete:
                # Soft delete - mark as archived
                product.status = ProductStatus.ARCHIVED
                await db.commit()
                logger.info(f"✅ Archived product '{product.name}' (ID: {product_id})")
            else:
                # Hard delete
                await db.delete(product)
                await db.commit()
                logger.info(f"✅ Deleted product '{product.name}' (ID: {product_id})")
            
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to delete product {product_id}: {e}")
            raise

    @staticmethod
    async def list_products(
        db: AsyncSession,
        storefront_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        product_type: Optional[ProductType] = None,
        status: Optional[ProductStatus] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> ProductListResponse:
        """
        List products with filtering and pagination
        
        Args:
            db: Database session
            storefront_id: Filter by storefront ID
            user_id: Filter by user ID (via storefront)
            product_type: Filter by product type
            status: Filter by status
            is_featured: Filter by featured status
            search: Search in name and description
            page: Page number (1-based)
            per_page: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Paginated product list response
        """
        try:
            # Build query
            query = select(Product).options(selectinload(Product.storefront))
            
            # Apply filters
            if storefront_id:
                query = query.where(Product.storefront_id == storefront_id)
                
            if user_id:
                query = query.join(Storefront).where(Storefront.user_id == user_id)
                
            if product_type:
                query = query.where(Product.product_type == product_type)
                
            if status:
                query = query.where(Product.status == status)
            else:
                # Default: exclude archived products
                query = query.where(Product.status != ProductStatus.ARCHIVED)
                
            if is_featured is not None:
                query = query.where(Product.is_featured == is_featured)
                
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.short_description.ilike(search_term)
                    )
                )

            # Count total results
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar()

            # Apply sorting
            sort_column = getattr(Product, sort_by, Product.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)

            # Apply pagination
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            # Execute query
            result = await db.execute(query)
            products = result.scalars().all()

            # Convert to response models
            product_responses = [ProductResponse.model_validate(product) for product in products]

            total_pages = (total + per_page - 1) // per_page

            return ProductListResponse(
                products=product_responses,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to list products: {e}")
            raise

    @staticmethod
    async def get_product_stats(
        db: AsyncSession,
        storefront_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> ProductStatsResponse:
        """
        Get product statistics
        
        Args:
            db: Database session
            storefront_id: Filter by storefront ID
            user_id: Filter by user ID (via storefront)
            
        Returns:
            Product statistics response
        """
        try:
            # Build base query
            base_query = select(Product)
            
            if storefront_id:
                base_query = base_query.where(Product.storefront_id == storefront_id)
            elif user_id:
                base_query = base_query.join(Storefront).where(Storefront.user_id == user_id)

            # Get counts by status
            stats_queries = {
                'total_products': base_query.where(Product.status != ProductStatus.ARCHIVED),
                'active_products': base_query.where(Product.status == ProductStatus.ACTIVE),
                'draft_products': base_query.where(Product.status == ProductStatus.DRAFT),
                'sold_out_products': base_query.where(Product.status == ProductStatus.SOLD_OUT)
            }

            stats = {}
            for stat_name, query in stats_queries.items():
                count_query = select(func.count()).select_from(query.subquery())
                result = await db.execute(count_query)
                stats[stat_name] = result.scalar()

            # Get total sales and revenue
            sales_query = select(
                func.sum(Product.sold_count),
                func.sum(Product.price * Product.sold_count)
            )
            
            if storefront_id:
                sales_query = sales_query.where(Product.storefront_id == storefront_id)
            elif user_id:
                sales_query = sales_query.join(Storefront).where(Storefront.user_id == user_id)

            sales_result = await db.execute(sales_query)
            total_sales, total_revenue = sales_result.first()

            # Get top selling products
            top_products_query = base_query.where(
                and_(
                    Product.status == ProductStatus.ACTIVE,
                    Product.sold_count > 0
                )
            ).order_by(desc(Product.sold_count)).limit(5)

            top_result = await db.execute(top_products_query)
            top_products = [ProductResponse.model_validate(p) for p in top_result.scalars().all()]

            return ProductStatsResponse(
                total_products=stats['total_products'],
                active_products=stats['active_products'],
                draft_products=stats['draft_products'],
                sold_out_products=stats['sold_out_products'],
                total_sales=total_sales or 0,
                total_revenue=total_revenue or Decimal('0.00'),
                top_selling_products=top_products
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get product stats: {e}")
            raise

    @staticmethod
    async def reserve_inventory(
        db: AsyncSession,
        product_id: UUID,
        quantity: int
    ) -> bool:
        """
        Reserve inventory for an order
        
        Args:
            db: Database session
            product_id: Product ID
            quantity: Quantity to reserve
            
        Returns:
            True if reserved successfully
            
        Raises:
            ProductNotFoundError: If product doesn't exist
            InsufficientInventoryError: If not enough inventory
        """
        try:
            result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()

            # Check if product can be purchased
            can_purchase, message = product.can_purchase(quantity)
            if not can_purchase:
                raise InsufficientInventoryError(message)

            # Reserve inventory
            product.reserve_inventory(quantity)
            await db.commit()
            
            logger.info(f"✅ Reserved {quantity} units of product '{product.name}'")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to reserve inventory for product {product_id}: {e}")
            raise

    @staticmethod
    async def release_inventory(
        db: AsyncSession,
        product_id: UUID,
        quantity: int
    ) -> bool:
        """
        Release reserved inventory (e.g., cancelled order)
        
        Args:
            db: Database session
            product_id: Product ID
            quantity: Quantity to release
            
        Returns:
            True if released successfully
        """
        try:
            result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()

            product.release_inventory(quantity)
            await db.commit()
            
            logger.info(f"✅ Released {quantity} units of product '{product.name}'")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to release inventory for product {product_id}: {e}")
            raise

    @staticmethod
    async def record_sale(
        db: AsyncSession,
        product_id: UUID,
        quantity: int = 1
    ) -> bool:
        """
        Record a successful sale
        
        Args:
            db: Database session
            product_id: Product ID
            quantity: Quantity sold
            
        Returns:
            True if recorded successfully
        """
        try:
            result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()

            product.record_sale(quantity)
            await db.commit()
            
            logger.info(f"✅ Recorded sale of {quantity} units for product '{product.name}'")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to record sale for product {product_id}: {e}")
            raise

    @staticmethod
    async def publish_product(
        db: AsyncSession,
        product_id: UUID,
        user_id: UUID
    ) -> ProductResponse:
        """
        Publish a product (change status to active)
        
        Args:
            db: Database session
            product_id: Product ID
            user_id: User ID for ownership verification
            
        Returns:
            Updated product response
        """
        try:
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.storefront))
                .where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()
                
            if product.storefront.user_id != user_id:
                raise UnauthorizedError("Not authorized to publish this product")

            product.publish()
            await db.commit()
            
            logger.info(f"✅ Published product '{product.name}'")
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to publish product {product_id}: {e}")
            raise

    @staticmethod
    async def unpublish_product(
        db: AsyncSession,
        product_id: UUID,
        user_id: UUID
    ) -> ProductResponse:
        """
        Unpublish a product (change status to inactive)
        
        Args:
            db: Database session
            product_id: Product ID
            user_id: User ID for ownership verification
            
        Returns:
            Updated product response
        """
        try:
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.storefront))
                .where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                raise ProductNotFoundError()
                
            if product.storefront.user_id != user_id:
                raise UnauthorizedError("Not authorized to unpublish this product")

            product.unpublish()
            await db.commit()
            
            logger.info(f"✅ Unpublished product '{product.name}'")
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to unpublish product {product_id}: {e}")
            raise

    # Helper methods
    @staticmethod
    async def _validate_product_data(product_data: ProductCreateUnion) -> None:
        """
        Validate product data based on product type
        
        Args:
            product_data: Product creation data
            
        Raises:
            ValidationError: If validation fails
        """
        if product_data.product_type == ProductType.DIGITAL:
            # Digital products should have file_url for complete products
            pass  # File URL can be set later via upload
            
        elif product_data.product_type == ProductType.PHYSICAL:
            # Physical products should have weight for shipping
            if not hasattr(product_data, 'weight_grams') or not product_data.weight_grams:
                logger.warning("Physical product created without weight - shipping calculations may be affected")
                
        elif product_data.product_type == ProductType.LINK:
            # Link products must have external_url
            if not hasattr(product_data, 'external_url') or not product_data.external_url:
                raise ValidationError("Link products must have an external_url")
                
        elif product_data.product_type == ProductType.MEMBERSHIP:
            # Membership products should have billing_interval
            if not hasattr(product_data, 'billing_interval') or not product_data.billing_interval:
                logger.warning("Membership product created without billing_interval")

    @staticmethod
    async def _generate_unique_slug(
        db: AsyncSession,
        name: str,
        storefront_id: UUID
    ) -> str:
        """
        Generate a unique slug for a product within a storefront
        
        Args:
            db: Database session
            name: Product name
            storefront_id: Storefront ID
            
        Returns:
            Unique slug
        """
        import re
        
        # Create base slug from name
        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
        base_slug = base_slug.strip('-')[:100]
        
        # Check if base slug is unique
        slug = base_slug
        counter = 1
        
        while True:
            existing = await db.execute(
                select(Product).where(
                    and_(
                        Product.storefront_id == storefront_id,
                        Product.slug == slug
                    )
                )
            )
            
            if not existing.scalar_one_or_none():
                break
                
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug