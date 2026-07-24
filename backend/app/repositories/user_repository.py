"""
Data access layer for User entities.
All database queries for users live here.
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Handles all PostgreSQL operations for the User model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()   # get the generated ID without committing
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(str(user_id)))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def update_name(self, user: User, name: str) -> User:
        user.name = name
        await self.db.flush()
        await self.db.refresh(user)
        return user
