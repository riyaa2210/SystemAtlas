"""Aggregates all v1 API routers into a single router."""
from fastapi import APIRouter

api_router = APIRouter()


def _build_router() -> None:
    """
    Register all sub-routers. Called once at import time.
    Using a function avoids circular import issues when multiple
    route modules are loaded in the same interpreter session.
    """
    from app.api.v1 import auth, repositories, graph, analytics, copilot  # noqa

    api_router.include_router(auth.router,         prefix="/auth",         tags=["Authentication"])
    api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
    api_router.include_router(graph.router,        prefix="/graph",        tags=["Graph"])
    api_router.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])
    api_router.include_router(copilot.router,      prefix="/copilot",      tags=["AI Copilot"])


_build_router()
