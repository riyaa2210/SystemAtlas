"""Data access layer for Neo4j graph operations."""
from app.core.graph.graph_queries import GraphQueries
from app.utils.logger import get_logger

logger = get_logger(__name__)

_LABEL_TO_TYPE: dict[str, str] = {"Repository": "Service", "Module": "Module", "File": "File", "Api": "Api", "Database": "Database"}


def _resolve_type(labels: list[str]) -> str:
    for label in (labels or []):
        if label in _LABEL_TO_TYPE:
            return _LABEL_TO_TYPE[label]
    return "Unknown"


class GraphRepository:
    def __init__(self, neo4j_session):
        self.session = neo4j_session

    async def get_graph(self, repo_id: str) -> tuple[list[dict], list[dict]]:
        nodes, edges = [], []
        try:
            result = await self.session.run(GraphQueries.GET_ALL_NODES, repo_id=repo_id)
            for record in await result.data():
                node = record.get("n")
                if node is None: continue
                props = dict(node)
                nid = props.get("id") or str(id(node))
                ntype = _resolve_type(record.get("labels", []))
                label = props.get("name") or props.get("path") or nid
                nodes.append({"id": nid, "type": ntype, "label": label, "properties": props})
        except Exception as e:
            logger.error("get_graph nodes failed", repo_id=repo_id, error=str(e))

        try:
            result = await self.session.run(GraphQueries.GET_ALL_RELATIONSHIPS, repo_id=repo_id)
            for record in await result.data():
                sid, tid = record.get("source_id"), record.get("target_id")
                if sid is None or tid is None: continue
                rid = record.get("rel_id")
                edges.append({"id": str(rid) if rid is not None else f"{sid}->{tid}", "source": sid, "target": tid, "type": record.get("rel_type", "UNKNOWN"), "properties": dict(record.get("rel_props") or {})})
        except Exception as e:
            logger.error("get_graph edges failed", repo_id=repo_id, error=str(e))

        return nodes, edges

    async def get_node_with_neighbors(self, node_id: str) -> dict | None:
        try:
            result = await self.session.run(GraphQueries.GET_NODE_WITH_NEIGHBORS, node_id=node_id)
            record = await result.single()
            if record is None: return None
            raw_node = record.get("n")
            if raw_node is None: return None
            node_props = dict(raw_node)
            ntype = _resolve_type(record.get("node_labels", []))
            label = node_props.get("name") or node_props.get("path") or node_id

            def _parse(entry: dict) -> dict | None:
                n = entry.get("node")
                if n is None: return None
                props = dict(n)
                return {"id": props.get("id") or str(id(n)), "type": _resolve_type(entry.get("labels") or []), "label": props.get("name") or props.get("path") or "", "properties": props, "rel_type": entry.get("rel")}

            outgoing_edges, incoming_edges, neighbors = [], [], []
            for entry in (record.get("outgoing") or []):
                nb = _parse(entry)
                if nb:
                    outgoing_edges.append({"type": entry.get("rel"), "node": nb})
                    neighbors.append(nb)
            for entry in (record.get("incoming") or []):
                nb = _parse(entry)
                if nb:
                    incoming_edges.append({"type": entry.get("rel"), "node": nb})
                    if not any(n["id"] == nb["id"] for n in neighbors):
                        neighbors.append(nb)

            return {"node": {"id": node_id, "type": ntype, "label": label, "properties": node_props}, "neighbors": neighbors, "incoming_edges": incoming_edges, "outgoing_edges": outgoing_edges}
        except Exception as e:
            logger.error("get_node_with_neighbors failed", node_id=node_id, error=str(e))
            return None

    async def delete_repo_graph(self, repo_id: str) -> None:
        try:
            await self.session.run(GraphQueries.DELETE_REPO_GRAPH, repo_id=repo_id)
            logger.info("Deleted graph", repo_id=repo_id)
        except Exception as e:
            logger.error("delete_repo_graph failed", repo_id=repo_id, error=str(e))
