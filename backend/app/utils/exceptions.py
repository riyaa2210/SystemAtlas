"""
Custom exception hierarchy for the application.
All domain exceptions inherit from LAMException so they can be
caught uniformly in exception handlers.
"""
from fastapi import HTTPException, status


class LAMException(Exception):
    """Base exception for all application errors."""
    pass


class NotFoundError(LAMException):
    """Raised when a requested resource does not exist."""
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' not found")


class UnauthorizedError(LAMException):
    """Raised when an action is not permitted for the current user."""
    pass


class ConflictError(LAMException):
    """Raised when a resource already exists (e.g., duplicate email)."""
    def __init__(self, message: str):
        super().__init__(message)


class ScanError(LAMException):
    """Raised when the scan pipeline encounters an unrecoverable error."""
    def __init__(self, message: str, stage: str):
        self.stage = stage
        super().__init__(f"[{stage}] {message}")


class ExternalServiceError(LAMException):
    """Raised when an external API (GitHub, Gemini) call fails."""
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"{service} error: {message}")


# ── FastAPI exception handlers ─────────────────────────────────────────────────

def not_found_handler(exc: NotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )


def conflict_handler(exc: ConflictError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


def unauthorized_handler(exc: UnauthorizedError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(exc),
    )
