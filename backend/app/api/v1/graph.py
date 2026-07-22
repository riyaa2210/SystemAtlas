"""
Graph endpoints.
Serves graph data from PostgreSQL (always available) with Neo4j as optional enhancement.
"""
import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser, DBSession
from app.repositories.repo_repository import RepoRepository
from app.schemas.graph import GraphResponse, GraphNode, GraphEdge, NodeDetailResponse
from app.utils.exceptions import NotFoundError, UnauthorizedError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{repo_id}", response_model=GraphResponse)
async def get_graph(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    snapshot = await repo_repo.get_latest_snapshot(repo_id)
    if not snapshot or not snapshot.graph_data:
        # Try Neo4j fallback
        try:
            from app.db.neo4j import get_neo4j_driver
            from app.repositories.graph_repository import GraphRepository
            driver = await get_neo4j_driver()
            async with driver.session(database="neo4j") as neo4j_session:
                graph_repo = GraphRepository(neo4j_session)
                nodes_data, edges_data = await graph_repo.get_graph(str(repo_id))
                if nodes_data:
                    nodes = [GraphNode(**n) for n in nodes_data]
                    edges = [GraphEdge(**e) for e in edges_data]
                    return GraphResponse(nodes=nodes, edges=edges, repo_id=str(repo_id), node_count=len(nodes), edge_count=len(edges))
        except Exception as e:
            logger.info("Neo4j not available for graph fallback", error=str(e)[:80])

        return GraphResponse(nodes=[], edges=[], repo_id=str(repo_id), node_count=0, edge_count=0)

    # Serve from PostgreSQL JSONB — always works
    raw = snapshot.graph_data
    raw_nodes = raw.get("nodes", [])
    raw_edges = raw.get("edges", [])

    nodes = [GraphNode(
        id=n["id"],
        type=n.get("type", "File"),
        label=n.get("label", n["id"]),
        properties=n.get("properties", {}),
    ) for n in raw_nodes]

    edges = [GraphEdge(
        id=e["id"],
        source=e["source"],
        target=e["target"],
        type=e.get("type", "UNKNOWN"),
        properties=e.get("properties", {}),
    ) for e in raw_edges]

    logger.info("Graph served from PostgreSQL", nodes=len(nodes), edges=len(edges), repo_id=str(repo_id))
    return GraphResponse(nodes=nodes, edges=edges, repo_id=str(repo_id), node_count=len(nodes), edge_count=len(edges))


@router.get("/{repo_id}/node/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(repo_id: uuid.UUID, node_id: str, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    snapshot = await repo_repo.get_latest_snapshot(repo_id)
    if not snapshot or not snapshot.graph_data:
        raise HTTPException(status_code=404, detail="No graph data found. Scan the repository first.")

    raw = snapshot.graph_data
    all_nodes = {n["id"]: n for n in raw.get("nodes", [])}
    all_edges = raw.get("edges", [])

    target = all_nodes.get(node_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in graph")

    # Find all connected edges and neighbors
    outgoing = [e for e in all_edges if e["source"] == node_id]
    incoming = [e for e in all_edges if e["target"] == node_id]

    def make_node(n: dict) -> GraphNode:
        return GraphNode(id=n["id"], type=n.get("type", "File"), label=n.get("label", n["id"]), properties=n.get("properties", {}))

    def make_edge(e: dict) -> GraphEdge:
        return GraphEdge(id=e["id"], source=e["source"], target=e["target"], type=e.get("type", "UNKNOWN"), properties=e.get("properties", {}))

    neighbor_ids = {e["target"] for e in outgoing} | {e["source"] for e in incoming}
    neighbor_ids.discard(node_id)
    neighbors = [make_node(all_nodes[nid]) for nid in neighbor_ids if nid in all_nodes]

    return NodeDetailResponse(
        node=make_node(target),
        neighbors=neighbors,
        incoming_edges=[make_edge(e) for e in incoming],
        outgoing_edges=[make_edge(e) for e in outgoing],
    )
