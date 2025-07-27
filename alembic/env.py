import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Add the parent directory to the Python path to import our app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our app configuration and database setup
try:
    from app.config import settings
    from app.database import Base
    
    # Import all models to ensure they're registered with Base.metadata
    # As we create models in future tasks, add imports here:
    from app.models.user import User
    from app.models.storefront import Storefront
    from app.models.product import Product
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.drop import Drop
    from app.models.drop_participant import DropParticipant
    from app.models.raffle import Raffle, RaffleEntry
    from app.models.analytics import PageView
    
except ImportError as e:
    print(f"Warning: Could not import app modules: {e}")
    print("Falling back to basic configuration")
    settings = None
    Base = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from our settings if available
if settings:
    # Use the sync database URL for migrations
    config.set_main_option("sqlalchemy.url", settings.get_database_url_sync())
    
    # Set target metadata from our Base class
    target_metadata = Base.metadata
    
    print(f"🔧 Using database URL: {settings.get_database_url_sync()[:50]}...")
    print(f"📋 Target metadata: {target_metadata}")
else:
    # Fallback if app modules can't be imported
    target_metadata = None
    print("⚠️  Warning: Using fallback configuration")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Helper function to run migrations with a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # Include additional configuration for better migration detection
        render_as_batch=True,  # Better support for SQLite and other databases
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in async mode for async database engines."""
    from app.database import async_engine
    
    async with async_engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await async_engine.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Check if we should use async or sync mode
    if settings and hasattr(settings, 'database_url') and 'asyncpg' in settings.database_url:
        print("🔄 Running migrations in async mode...")
        asyncio.run(run_async_migrations())
    else:
        print("🔄 Running migrations in sync mode...")
        # Use sync engine for migrations
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)


# Migration execution
if context.is_offline_mode():
    print("📴 Running migrations in offline mode...")
    run_migrations_offline()
else:
    print("🌐 Running migrations in online mode...")
    run_migrations_online()

print("✅ Migration execution completed!")
