"""
FastAPI application entry point.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.router import api_router
from app.db.postgres import create_db_tables
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("Starting Living Architecture Map API", version=settings.app_version)

    # Ensure temp directory exists
    os.makedirs(settings.temp_dir, exist_ok=True)

    # Create PostgreSQL tables on every startup (idempotent — CREATE TABLE IF NOT EXISTS)
    try:
        await create_db_tables()
    except Exception as e:
        logger.warning(
            "Database not available at startup",
            error=str(e),
        )

    logger.info("Application startup complete")
    yield

    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered software architecture visualization and code intelligence platform.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — accept all origins in production (tighten after confirming deployment works)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
