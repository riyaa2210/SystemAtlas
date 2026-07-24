"""
Shared FastAPI dependencies injected into route handlers.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session
from app.core.auth.jwt import verify_token
from app.repositories.user_repository import UserRepository
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Dependency that extracts and validates the JWT from the Authorization header.
    Raises 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# Convenience type alias for route handlers
CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
