"""Analytics endpoints."""
import uuid

from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUser, DBSession
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import AnalyticsResponse, RiskItem
from app.utils.exceptions import NotFoundError, UnauthorizedError

router = APIRouter()


@router.get("/{repo_id}", response_model=AnalyticsResponse)
async def get_analytics(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    try:
        service = AnalyticsService(db)
        return await service.get_analytics(repo_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{repo_id}/risks", response_model=list[RiskItem])
async def get_risks(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    try:
        service = AnalyticsService(db)
        return await service.get_risks(repo_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
