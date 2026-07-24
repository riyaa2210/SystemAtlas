"""
Graph service — orchestrates Neo4j read operations for the API.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.graph_repository import GraphRepository
from app.repositories.repo_repository import RepoRepository
from app.schemas.graph import GraphResponse, GraphNode, GraphEdge, NodeDetailResponse
from app.utils.exceptions import NotFoundError, UnauthorizedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphService:
    def __init__(self, db: AsyncSession, neo4j_session):
        self.repo_repo = RepoRepository(db)
        self.graph_repo = GraphRepository(neo4j_session)

    async def get_graph(
        self, repo_id: uuid.UUID, user_id: uuid.UUID
    ) -> GraphResponse:
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("Access denied")

        nodes_data, edges_data = await self.graph_repo.get_graph(str(repo_id))

        nodes = [GraphNode(**n) for n in nodes_data]
        edges = [GraphEdge(**e) for e in edges_data]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            repo_id=str(repo_id),
            node_count=len(nodes),
            edge_count=len(edges),
        )

    async def get_node_detail(
        self, repo_id: uuid.UUID, node_id: str, user_id: uuid.UUID
    ) -> NodeDetailResponse:
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("Access denied")

        # Phase 6: full implementation
        raise NotFoundError("Node", node_id)
