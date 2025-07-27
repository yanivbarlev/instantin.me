"""Create users table with authentication fields

Revision ID: ec1fc9276250
Revises: 
Create Date: 2025-07-22 17:38:12.398929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec1fc9276250'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table with all authentication and profile fields"""
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('google_id', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('stripe_account_id', sa.String(length=255), nullable=True),
        sa.Column('paypal_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_suspended', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('stripe_account_id'),
        sa.UniqueConstraint('email_verification_token'),
        sa.UniqueConstraint('password_reset_token')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
    op.create_index('ix_users_is_verified', 'users', ['is_verified'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop users table and all related indexes"""
    # Drop indexes first
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_is_verified', table_name='users')
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop the table
    op.drop_table('users')
