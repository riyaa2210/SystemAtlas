"""Pydantic schemas for analytics endpoints."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class RiskItem(BaseModel):
    type: str          # circular_dependency | high_coupling | dead_module | missing_docs
    severity: str      # high | medium | low
    title: str
    description: str
    affected_nodes: list[str] = []


class CircularDependency(BaseModel):
    cycle: list[str]   # ordered list of node IDs forming the cycle
    length: int


class AnalyticsResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    architecture_score: float
    total_modules: int
    total_files: int
    total_dependencies: int
    circular_deps: int
    dead_modules: int
    highly_coupled: int
    missing_docs: int
    metrics_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
