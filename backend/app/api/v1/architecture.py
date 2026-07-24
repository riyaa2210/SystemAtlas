"""
System Architecture Diagram endpoint.
Serves pre-computed architecture data from PostgreSQL JSONB.
Does NOT recompute on request — data is generated once during scan and cached in DB.
"""
import uuid

from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUser, DBSession
from app.repositories.repo_repository import RepoRepository
from app.schemas.architecture import (
    ArchitectureResponse,
    ArchitectureNode,
    ArchitectureEdge,
    ArchitectureMetadata,
    ArchNodePosition,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _parse_response(raw: dict, repo_id: str) -> ArchitectureResponse:
    """Convert raw JSONB dict → validated ArchitectureResponse."""
    raw_nodes = raw.get("nodes", [])
    raw_edges = raw.get("edges", [])

    nodes: list[ArchitectureNode] = []
    for n in raw_nodes:
        pos = n.get("position", {})
        nodes.append(ArchitectureNode(
            id=n["id"],
            layer=n.get("layer", "unknown"),
            label=n.get("label", n["id"]),
            technologies=n.get("technologies", []),
            file_count=n.get("file_count", 0),
            color=n.get("color", "#6b7280"),
            icon=n.get("icon", "box"),
            description=n.get("description", ""),
            position=ArchNodePosition(
                x=pos.get("x", 0.0),
                y=pos.get("y", 0.0),
            ),
        ))

    edges: list[ArchitectureEdge] = []
    for e in raw_edges:
        edges.append(ArchitectureEdge(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            label=e.get("label", ""),
            type=e.get("type", "depends_on"),
        ))

    metadata = ArchitectureMetadata(
        detected_technologies=raw.get("detected_technologies", []),
        detected_layers=raw.get("detected_layers", []),
        frameworks=raw.get("frameworks", []),
        languages=raw.get("languages", []),
    )

    return ArchitectureResponse(
        nodes=nodes,
        edges=edges,
        metadata=metadata,
        repo_id=repo_id,
        node_count=len(nodes),
        edge_count=len(edges),
    )


@router.get("/{repo_id}", response_model=ArchitectureResponse)
async def get_architecture(
    repo_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Returns the pre-computed system architecture diagram for a repository.
    Architecture is generated during scan and stored in PostgreSQL — loads instantly.
    Returns 404 if the repository has not been scanned yet.
    """
    repo_repo = RepoRepository(db)

    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    snapshot = await repo_repo.get_latest_snapshot(repo_id)
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail="No scan data found. Scan the repository first.",
        )

    if not snapshot.architecture_data:
        # Snapshot exists but was created before architecture feature was added.
        # Return an empty structure rather than hard 404 so the UI can display a
        # helpful "rescan to generate" message instead of an error page.
        logger.info(
            "No architecture_data in snapshot — returning empty",
            repo_id=str(repo_id),
        )
        return ArchitectureResponse(
            nodes=[],
            edges=[],
            metadata=ArchitectureMetadata(
                frameworks=repo.frameworks or [],
                languages=repo.languages or [],
            ),
            repo_id=str(repo_id),
            node_count=0,
            edge_count=0,
        )

    response = _parse_response(snapshot.architecture_data, str(repo_id))
    logger.info(
        "Architecture served",
        repo_id=str(repo_id),
        nodes=response.node_count,
        edges=response.edge_count,
    )
    return response
