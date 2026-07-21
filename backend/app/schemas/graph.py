"""Pydantic schemas for graph endpoints."""
from typing import Any
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str          # Service | Module | File | Api | Database
    label: str
    properties: dict[str, Any] = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str          # CALLS | IMPORTS | DEPENDS_ON | READS | WRITES
    properties: dict[str, Any] = {}


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    repo_id: str
    node_count: int
    edge_count: int


class NodeDetailResponse(BaseModel):
    node: GraphNode
    neighbors: list[GraphNode]
    incoming_edges: list[GraphEdge]
    outgoing_edges: list[GraphEdge]
