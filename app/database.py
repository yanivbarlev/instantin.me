from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import logging
import time

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Declarative Base
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Uses SQLAlchemy 2.0 DeclarativeBase.
    """
    pass

# Async Database Engine
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=300,     # Recycle connections every 5 minutes
    pool_size=10,         # Connection pool size
    max_overflow=20,      # Maximum overflow connections
    future=True           # Use SQLAlchemy 2.0 style
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync Database Engine (for Alembic migrations)
sync_engine = create_engine(
    settings.get_database_url_sync(),
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    future=True
)

# Sync Session Factory (for Alembic migrations)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    Use this in FastAPI endpoints for database operations.
    
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


def get_sync_session():
    """
    Get synchronous database session.
    Used primarily for Alembic migrations and testing.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Sync database session error: {e}")
        raise
    finally:
        db.close()


async def create_tables():
    """
    Create all database tables.
    Should be called on application startup if needed.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created successfully")


async def drop_tables():
    """
    Drop all database tables.
    Use with caution - only for development/testing!
    """
    if settings.is_production:
        raise RuntimeError("Cannot drop tables in production environment!")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("🗑️ Database tables dropped")


async def check_database_connection():
    """
    Check if database connection is working.
    Returns True if successful, False otherwise.
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def close_database_connections():
    """
    Close all database connections.
    Should be called on application shutdown.
    """
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("🔌 Database connections closed")


# Database initialization functions
async def init_database():
    """
    Initialize database on application startup.
    Checks connection and creates tables if needed.
    """
    logger.info("🔄 Initializing database...")
    
    # Check database connection
    if not await check_database_connection():
        raise RuntimeError("Failed to connect to database")
    
    # Import all models to ensure they're registered with Base
    # This ensures all models are available for table creation and relationships
    try:
        # Core user and storefront models
        from app.models.user import User  # noqa: F401
        from app.models.storefront import Storefront  # noqa: F401
        logger.info("✅ User and Storefront models imported successfully")
        
        # E-commerce models
        from app.models.product import Product  # noqa: F401
        from app.models.order import Order  # noqa: F401
        from app.models.order_item import OrderItem  # noqa: F401
        logger.info("✅ E-commerce models imported successfully")
        
        # Collaborative drops models
        from app.models.drop import Drop  # noqa: F401
        from app.models.drop_participant import DropParticipant  # noqa: F401
        logger.info("✅ Collaborative drops models imported successfully")
        
        # Raffle system models
        from app.models.raffle import Raffle, RaffleEntry  # noqa: F401
        logger.info("✅ Raffle system models imported successfully")
        
        # Analytics models
        from app.models.analytics import PageView  # noqa: F401
        logger.info("✅ Analytics models imported successfully")
        
        logger.info("🎯 All 10 database models imported and registered with Base.metadata")
        
    except ImportError as e:
        logger.warning(f"Some models not yet created: {e}")
        # Continue with available models - fault-tolerant approach
    
    # Create tables (will be no-op if tables already exist)
    if settings.is_development:
        await create_tables()
    
    logger.info("✅ Database initialization complete")


# Health check for database
async def database_health_check() -> dict:
    """
    Perform database health check.
    Returns status information for monitoring.
    """
    try:
        start_time = time.time()
        connection_ok = await check_database_connection()
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "database": {
                "status": "healthy" if connection_ok else "unhealthy",
                "response_time_ms": round(response_time, 2),
                "engine": "PostgreSQL",
                "async_engine_info": {
                    "pool_size": async_engine.pool.size(),
                    "checked_in": async_engine.pool.checkedin(),
                    "checked_out": async_engine.pool.checkedout(),
                }
            }
        }
    except Exception as e:
        return {
            "database": {
                "status": "error",
                "error": str(e),
                "engine": "PostgreSQL"
            }
        }


if __name__ == "__main__":
    import asyncio
    import time
    
    async def test_database():
        """Test database connectivity"""
        print("🧪 Testing database connection...")
        await init_database()
        health = await database_health_check()
        print(f"📊 Health check result: {health}")
        await close_database_connections()
    
    # Run test
    asyncio.run(test_database()) 