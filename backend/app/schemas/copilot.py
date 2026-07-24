"""Pydantic schemas for AI copilot endpoints."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class CopilotAskRequest(BaseModel):
    repo_id: uuid.UUID
    question: str
    context_node_id: str | None = None   # optional: focus on a specific node


class CopilotSource(BaseModel):
    type: str          # module | file | api | documentation
    label: str
    node_id: str | None = None


class CopilotAskResponse(BaseModel):
    answer: str
    sources: list[CopilotSource] = []
    question: str


class ChatMessage(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    question: str
    answer: str
    created_at: datetime

    model_config = {"from_attributes": True}
