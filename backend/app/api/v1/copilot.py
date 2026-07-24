"""AI Copilot endpoints."""
from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUser, DBSession
from app.services.copilot_service import CopilotService
from app.schemas.copilot import CopilotAskRequest, CopilotAskResponse
from app.utils.exceptions import NotFoundError, UnauthorizedError, ExternalServiceError

router = APIRouter()


@router.post("/ask", response_model=CopilotAskResponse)
async def ask_copilot(
    request: CopilotAskRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    try:
        service = CopilotService(db)
        return await service.ask(request, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
