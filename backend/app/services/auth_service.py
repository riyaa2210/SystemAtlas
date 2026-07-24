"""
Authentication service — orchestrates user registration and login.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.core.auth.password import hash_password, verify_password
from app.core.auth.jwt import create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserProfile
from app.utils.exceptions import ConflictError, UnauthorizedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def register(self, request: RegisterRequest) -> UserProfile:
        """Register a new user. Raises ConflictError if email already exists."""
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise ConflictError(f"An account with email '{request.email}' already exists")

        password_hash = hash_password(request.password)
        user = await self.user_repo.create(
            name=request.name,
            email=request.email.lower(),
            password_hash=password_hash,
        )
        logger.info("New user registered", user_id=str(user.id), email=user.email)
        return UserProfile.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user and return a JWT access token."""
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        token = create_access_token(str(user.id))
        logger.info("User logged in", user_id=str(user.id))
        return TokenResponse(access_token=token)
