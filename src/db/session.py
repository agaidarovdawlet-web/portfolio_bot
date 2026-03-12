"""
Async database engine and session factory.

Import ``async_session_factory`` wherever you need a DB session, or use
the ``get_session`` async context manager for clean resource handling.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.db.models import Base

# The engine is module-level so it is created once for the process lifetime.
engine = create_async_engine(
    settings.database_url,
    echo=False,           # Set to True for SQL query logging during dev.
    future=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Avoids lazy-load errors on detached instances.
    class_=AsyncSession,
)


async def create_tables() -> None:
    """Create all ORM-mapped tables (idempotent via ``checkfirst=True``)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a transactional DB session.

    Commits on success, rolls back on any exception, and always closes
    the session.

    Example::

        async with get_session() as session:
            session.add(some_model_instance)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
