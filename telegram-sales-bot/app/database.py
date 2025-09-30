from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import asyncio
from typing import AsyncGenerator

from app.config import get_settings
from app.models.base import Base

settings = get_settings()

# Convert sync database URL to async if needed
if settings.database_url.startswith("postgresql://"):
    async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif settings.database_url.startswith("sqlite:///"):
    # SQLite for async
    async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else:
    async_database_url = settings.database_url

# Async engine and session
async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    poolclass=NullPool,
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for migrations and admin tasks
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_session() -> Session:
    """Context manager for sync database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await async_engine.dispose()


def init_db_sync():
    """Initialize database tables synchronously"""
    Base.metadata.create_all(bind=sync_engine)


if __name__ == "__main__":
    # Create tables if running directly
    asyncio.run(init_db())
    print("Database tables created successfully!")
