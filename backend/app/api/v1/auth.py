"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DBSession
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserProfile, UpdateProfileRequest
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import ConflictError, UnauthorizedError

router = APIRouter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: DBSession):
    try:
        service = AuthService(db)
        return await service.register(request)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DBSession):
    try:
        service = AuthService(db)
        return await service.login(request)
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: CurrentUser):
    return UserProfile.model_validate(current_user)


@router.put("/me", response_model=UserProfile)
async def update_me(request: UpdateProfileRequest, current_user: CurrentUser, db: DBSession):
    user_repo = UserRepository(db)
    updated = await user_repo.update_name(current_user, request.name)
    return UserProfile.model_validate(updated)
