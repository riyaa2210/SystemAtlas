"""Pydantic schemas for repository and scan job endpoints."""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, HttpUrl, field_validator


class AddRepositoryRequest(BaseModel):
    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip()
        if "github.com" not in v:
            raise ValueError("URL must be a GitHub repository URL")
        return v


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    full_name: str
    github_url: str
    description: str | None
    languages: list[str]
    frameworks: list[str]
    default_branch: str
    is_private: bool
    star_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScanJobResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    status: str
    stage: str | None
    error_message: str | None
    files_scanned: int
    nodes_created: int
    edges_created: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepositoryDetailResponse(RepositoryResponse):
    latest_scan: ScanJobResponse | None = None
