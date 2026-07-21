"""Graph visualization endpoints."""
import uuid

from fastapi import APIRouter, HTTPException, Depends

from app.dependencies import CurrentUser, DBSession
from app.db.neo4j import get_neo4j_session
from app.services.graph_service import GraphService
from app.schemas.graph import GraphResponse, NodeDetailResponse
from app.utils.exceptions import NotFoundError, UnauthorizedError

router = APIRouter()


@router.get("/{repo_id}", response_model=GraphResponse)
async def get_graph(
    repo_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    neo4j=Depends(get_neo4j_session),
):
    try:
        service = GraphService(db, neo4j)
        return await service.get_graph(repo_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{repo_id}/node/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(
    repo_id: uuid.UUID,
    node_id: str,
    current_user: CurrentUser,
    db: DBSession,
    neo4j=Depends(get_neo4j_session),
):
    try:
        service = GraphService(db, neo4j)
        return await service.get_node_detail(repo_id, node_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
