"""Pydantic schemas for the system architecture diagram endpoint."""
from typing import Any
from pydantic import BaseModel


class ArchNodePosition(BaseModel):
    x: float
    y: float


class ArchitectureNode(BaseModel):
    id: str
    layer: str
    label: str
    technologies: list[str] = []
    file_count: int = 0
    color: str = "#6b7280"
    icon: str = "box"
    description: str = ""
    position: ArchNodePosition


class ArchitectureEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str = ""
    type: str = "depends_on"


class ArchitectureMetadata(BaseModel):
    detected_technologies: list[str] = []
    detected_layers: list[str] = []
    frameworks: list[str] = []
    languages: list[str] = []


class ArchitectureResponse(BaseModel):
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]
    metadata: ArchitectureMetadata
    repo_id: str
    node_count: int
    edge_count: int
