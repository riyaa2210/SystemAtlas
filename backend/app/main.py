"""FastAPI application entry point."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("lam")


def _get_settings():
    try:
        from app.config import get_settings
        return get_settings()
    except Exception as e:
        log.error(f"Failed to load settings: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("LAM API starting up...")
    settings = _get_settings()

    try:
        os.makedirs(settings.temp_dir, exist_ok=True)
    except Exception as e:
        log.warning(f"Could not create temp dir: {e}")

    # DB tables — non-fatal, server starts even if DB is unreachable
    try:
        from app.db.postgres import create_db_tables
        await create_db_tables()
        log.info("Database tables ready")
    except Exception as e:
        log.warning(f"DB startup warning (non-fatal): {e}")

    log.info("LAM API startup complete")
    yield
    log.info("LAM API shutting down")


def create_app() -> FastAPI:
    settings = _get_settings()

    app = FastAPI(
        title="Living Architecture Map",
        version="1.0.0",
        description="AI-powered software architecture visualization platform.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — must be first middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routes
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()
