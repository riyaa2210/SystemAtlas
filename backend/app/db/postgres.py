"""
PostgreSQL async engine and session factory using SQLAlchemy 2.0.

Supabase note:
  - Port 6543 = Transaction Pooler (pgbouncer) — does NOT support prepared statements
  - Port 5432 = Session Pooler / Direct connection — works with SQLAlchemy
  - We pass statement_cache_size=0 via connect_args to disable prepared statements,
    which makes both pooler modes work correctly.
"""
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,                     # disable SQL logging noise in dev
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    # ← This is the fix for Supabase pgbouncer "prepared statement already exists" error
    connect_args={"statement_cache_size": 0},
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a database session per request."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_tables() -> None:
    """Create all tables in dev. Use Alembic for production migrations."""
    from app.models import user, repository, scan_job  # noqa — register models

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # Safe column additions for existing tables (idempotent)
            await conn.execute(text(
                "ALTER TABLE analytics_snapshots "
                "ADD COLUMN IF NOT EXISTS graph_data JSONB"
            ))

        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(
            "Database connection failed",
            error=str(e),
            hint="Check DATABASE_URL in .env — use port 5432 (Session Pooler) for Supabase",
        )
        raise
