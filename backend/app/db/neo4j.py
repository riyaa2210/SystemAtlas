"""
Neo4j driver singleton using the official neo4j Python driver.
Lazy-initialised — only connects when first used, so auth endpoints
work without a live Neo4j instance.
"""
from __future__ import annotations

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_driver = None


async def get_neo4j_driver():
    """Returns the singleton Neo4j async driver, creating it if needed."""
    global _driver
    if _driver is None:
        from neo4j import AsyncGraphDatabase  # lazy import
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        logger.info("Neo4j driver initialized")
    return _driver


async def close_neo4j_driver() -> None:
    """Close the Neo4j driver on shutdown."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def get_neo4j_session():
    """FastAPI dependency that yields a Neo4j async session."""
    driver = await get_neo4j_driver()
    async with driver.session(database="neo4j") as session:
        yield session
