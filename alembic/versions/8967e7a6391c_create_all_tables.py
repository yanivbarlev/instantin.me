"""create all tables

Revision ID: 8967e7a6391c
Revises: ec1fc9276250
Create Date: 2025-07-23 16:35:10.917208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8967e7a6391c'
down_revision: Union[str, None] = 'ec1fc9276250'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    order_status_enum = postgresql.ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 'failed', 'draft', name='orderstatus')
    payment_provider_enum = postgresql.ENUM('stripe', 'paypal', 'apple_pay', 'google_pay', 'manual', name='paymentprovider')
    product_status_enum = postgresql.ENUM('active', 'inactive', 'draft', 'archived', name='productstatus')
    product_type_enum = postgresql.ENUM('physical', 'digital', 'service', 'subscription', name='producttype')
    drop_status_enum = postgresql.ENUM('upcoming', 'active', 'ended', 'paused', name='dropstatus')
    raffle_status_enum = postgresql.ENUM('upcoming', 'active', 'ended', 'cancelled', name='rafflestatus')
    device_type_enum = postgresql.ENUM('DESKTOP', 'MOBILE', 'TABLET', 'BOT', 'UNKNOWN', name='devicetype')
    traffic_source_enum = postgresql.ENUM('DIRECT', 'ORGANIC', 'SOCIAL', 'REFERRAL', 'EMAIL', 'PAID', 'UNKNOWN', name='trafficsource')
    
    order_status_enum.create(op.get_bind())
    payment_provider_enum.create(op.get_bind())
    product_status_enum.create(op.get_bind())
    product_type_enum.create(op.get_bind())
    drop_status_enum.create(op.get_bind())
    raffle_status_enum.create(op.get_bind())
    device_type_enum.create(op.get_bind())
    traffic_source_enum.create(op.get_bind())

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_premium', sa.Boolean(), nullable=False),
        sa.Column('date_joined', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('reset_password_token', sa.String(255), nullable=True),
        sa.Column('reset_password_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('social_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_date_joined', 'users', ['date_joined'])

    # Create storefronts table
    op.create_table('storefronts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('banner_url', sa.String(500), nullable=True),
        sa.Column('custom_domain', sa.String(255), nullable=True),
        sa.Column('theme_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('social_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('business_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('seo_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('analytics_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('custom_domain')
    )
    op.create_index('idx_storefronts_user_id', 'storefronts', ['user_id'])
    op.create_index('idx_storefronts_slug', 'storefronts', ['slug'], unique=True)
    op.create_index('idx_storefronts_is_active', 'storefronts', ['is_active'])
    op.create_index('idx_storefronts_is_featured', 'storefronts', ['is_featured'])

    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storefront_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('compare_at_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('track_inventory', sa.Boolean(), nullable=False),
        sa.Column('inventory_quantity', sa.Integer(), nullable=True),
        sa.Column('low_stock_threshold', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Numeric(8, 3), nullable=True),
        sa.Column('dimensions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('shipping_required', sa.Boolean(), nullable=False),
        sa.Column('shipping_weight', sa.Numeric(8, 3), nullable=True),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('product_type', product_type_enum, nullable=False),
        sa.Column('status', product_status_enum, nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('seo_title', sa.String(200), nullable=True),
        sa.Column('seo_description', sa.String(500), nullable=True),
        sa.Column('digital_file_url', sa.String(500), nullable=True),
        sa.Column('download_limit', sa.Integer(), nullable=True),
        sa.Column('subscription_interval', sa.String(20), nullable=True),
        sa.Column('trial_period_days', sa.Integer(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('featured', sa.Boolean(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('sale_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['storefront_id'], ['storefronts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('storefront_id', 'slug')
    )
    op.create_index('idx_products_storefront_id', 'products', ['storefront_id'])
    op.create_index('idx_products_status', 'products', ['status'])
    op.create_index('idx_products_featured', 'products', ['featured'])
    op.create_index('idx_products_price', 'products', ['price'])

    # Create orders table
    op.create_table('orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storefront_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('status', order_status_enum, nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('shipping_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('payment_status', sa.String(20), nullable=False),
        sa.Column('payment_provider', payment_provider_enum, nullable=True),
        sa.Column('payment_transaction_id', sa.String(255), nullable=True),
        sa.Column('payment_method_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('billing_address', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('shipping_address', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('shipping_method', sa.String(100), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('tracking_url', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('fulfilled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['storefront_id'], ['storefronts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index('idx_orders_storefront_id', 'orders', ['storefront_id'])
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])

    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('product_sku', sa.String(100), nullable=True),
        sa.Column('product_variant_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('digital_download_url', sa.String(500), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('download_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE')
    )
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('idx_order_items_product_id', 'order_items', ['product_id'])

    # Create drops table
    op.create_table('drops',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storefront_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('banner_image_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', drop_status_enum, nullable=False),
        sa.Column('participant_limit', sa.Integer(), nullable=True),
        sa.Column('minimum_revenue_share', sa.Numeric(5, 2), nullable=False),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('terms_and_conditions', sa.Text(), nullable=True),
        sa.Column('featured_products', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('marketing_materials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_revenue', sa.Numeric(12, 2), nullable=False),
        sa.Column('participant_count', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('application_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['storefront_id'], ['storefronts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('storefront_id', 'slug')
    )
    op.create_index('idx_drops_storefront_id', 'drops', ['storefront_id'])
    op.create_index('idx_drops_creator_id', 'drops', ['creator_id'])
    op.create_index('idx_drops_status', 'drops', ['status'])
    op.create_index('idx_drops_start_date', 'drops', ['start_date'])

    # Create drop_participants table
    op.create_table('drop_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('drop_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('revenue_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('application_message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('total_sales', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_commission', sa.Numeric(12, 2), nullable=False),
        sa.Column('referral_code', sa.String(50), nullable=True),
        sa.Column('tracking_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['drop_id'], ['drops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('drop_id', 'user_id'),
        sa.UniqueConstraint('referral_code')
    )
    op.create_index('idx_drop_participants_drop_id', 'drop_participants', ['drop_id'])
    op.create_index('idx_drop_participants_user_id', 'drop_participants', ['user_id'])
    op.create_index('idx_drop_participants_status', 'drop_participants', ['status'])

    # Create raffles table
    op.create_table('raffles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_prize_pool', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', raffle_status_enum, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rules', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('draw_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('winner_announced_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_tickets', sa.Integer(), nullable=False),
        sa.Column('ticket_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_tickets_per_user', sa.Integer(), nullable=True),
        sa.Column('prizes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('winners', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('draw_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('marketing_banner_url', sa.String(500), nullable=True),
        sa.Column('terms_and_conditions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('month', 'year')
    )
    op.create_index('idx_raffles_status', 'raffles', ['status'])
    op.create_index('idx_raffles_start_date', 'raffles', ['start_date'])
    op.create_index('idx_raffles_month_year', 'raffles', ['month', 'year'])

    # Create raffle_entries table
    op.create_table('raffle_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raffle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticket_count', sa.Integer(), nullable=False),
        sa.Column('total_amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('payment_transaction_id', sa.String(255), nullable=True),
        sa.Column('payment_status', sa.String(20), nullable=False),
        sa.Column('ticket_numbers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_winner', sa.Boolean(), nullable=False),
        sa.Column('prize_won', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('entry_source', sa.String(50), nullable=True),
        sa.Column('referral_code', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['raffle_id'], ['raffles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_raffle_entries_raffle_id', 'raffle_entries', ['raffle_id'])
    op.create_index('idx_raffle_entries_user_id', 'raffle_entries', ['user_id'])
    op.create_index('idx_raffle_entries_payment_status', 'raffle_entries', ['payment_status'])

    # Create page_views table (analytics)
    op.create_table('page_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storefront_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('drop_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raffle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('visitor_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('path', sa.String(1024), nullable=False),
        sa.Column('page_title', sa.String(500), nullable=True),
        sa.Column('page_type', sa.String(50), nullable=True),
        sa.Column('referrer_url', sa.String(2048), nullable=True),
        sa.Column('referrer_domain', sa.String(255), nullable=True),
        sa.Column('utm_source', sa.String(255), nullable=True),
        sa.Column('utm_medium', sa.String(255), nullable=True),
        sa.Column('utm_campaign', sa.String(255), nullable=True),
        sa.Column('utm_term', sa.String(255), nullable=True),
        sa.Column('utm_content', sa.String(255), nullable=True),
        sa.Column('device_type', device_type_enum, nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('browser_version', sa.String(50), nullable=True),
        sa.Column('operating_system', sa.String(100), nullable=True),
        sa.Column('device_model', sa.String(100), nullable=True),
        sa.Column('screen_resolution', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('traffic_source', traffic_source_enum, nullable=True),
        sa.Column('is_bounce', sa.Boolean(), nullable=False),
        sa.Column('time_on_page', sa.Integer(), nullable=True),
        sa.Column('scroll_depth', sa.Integer(), nullable=True),
        sa.Column('is_conversion', sa.Boolean(), nullable=False),
        sa.Column('conversion_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_exit_page', sa.Boolean(), nullable=False),
        sa.Column('page_load_time', sa.Integer(), nullable=True),
        sa.Column('server_response_time', sa.Integer(), nullable=True),
        sa.Column('dom_content_loaded_time', sa.Integer(), nullable=True),
        sa.Column('first_contentful_paint', sa.Integer(), nullable=True),
        sa.Column('is_returning_visitor', sa.Boolean(), nullable=False),
        sa.Column('visit_count', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.String(100), nullable=True),
        sa.Column('variant_id', sa.String(100), nullable=True),
        sa.Column('is_bot', sa.Boolean(), nullable=False),
        sa.Column('bot_name', sa.String(100), nullable=True),
        sa.Column('spam_score', sa.Integer(), nullable=True),
        sa.Column('custom_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['storefront_id'], ['storefronts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['drop_id'], ['drops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raffle_id'], ['raffles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create comprehensive indexes for analytics queries
    op.create_index('idx_page_views_storefront_created', 'page_views', ['storefront_id', 'created_at'])
    op.create_index('idx_page_views_traffic_source_created', 'page_views', ['traffic_source', 'created_at'])
    op.create_index('idx_page_views_country_device', 'page_views', ['country', 'device_type'])
    op.create_index('idx_page_views_utm_campaign', 'page_views', ['utm_campaign', 'created_at'])
    op.create_index('idx_page_views_session_id', 'page_views', ['session_id'])
    op.create_index('idx_page_views_conversion', 'page_views', ['is_conversion', 'conversion_value'])
    op.create_index('idx_page_views_performance', 'page_views', ['page_load_time', 'created_at'])
    op.create_index('idx_page_views_bot_filter', 'page_views', ['is_bot', 'spam_score'])
    op.create_index('idx_page_views_experiment', 'page_views', ['experiment_id', 'variant_id'])
    op.create_index('idx_page_views_user_returning', 'page_views', ['user_id', 'is_returning_visitor'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('page_views')
    op.drop_table('raffle_entries')
    op.drop_table('raffles')
    op.drop_table('drop_participants')
    op.drop_table('drops')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('storefronts')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='trafficsource').drop(op.get_bind())
    sa.Enum(name='devicetype').drop(op.get_bind())
    sa.Enum(name='rafflestatus').drop(op.get_bind())
    sa.Enum(name='dropstatus').drop(op.get_bind())
    sa.Enum(name='producttype').drop(op.get_bind())
    sa.Enum(name='productstatus').drop(op.get_bind())
    sa.Enum(name='paymentprovider').drop(op.get_bind())
    sa.Enum(name='orderstatus').drop(op.get_bind())
