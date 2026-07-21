"""
Data access layer for Repository and ScanJob entities.
"""
import uuid
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.repository import Repository
from app.models.scan_job import ScanJob, AnalyticsSnapshot


class RepoRepository:
    """Handles all PostgreSQL operations for Repository and ScanJob models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Repository ────────────────────────────────────────────────────────────

    async def create_repository(
        self,
        user_id: uuid.UUID,
        name: str,
        full_name: str,
        github_url: str,
        **kwargs,
    ) -> Repository:
        repo = Repository(
            user_id=user_id,
            name=name,
            full_name=full_name,
            github_url=github_url,
            **kwargs,
        )
        self.db.add(repo)
        await self.db.flush()
        await self.db.refresh(repo)
        return repo

    async def get_by_id(self, repo_id: uuid.UUID) -> Repository | None:
        result = await self.db.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        return result.scalar_one_or_none()

    async def get_user_repositories(self, user_id: uuid.UUID) -> list[Repository]:
        result = await self.db.execute(
            select(Repository)
            .where(Repository.user_id == user_id)
            .order_by(desc(Repository.created_at))
        )
        return list(result.scalars().all())

    async def update_repository(self, repo: Repository, **kwargs) -> Repository:
        for key, value in kwargs.items():
            setattr(repo, key, value)
        await self.db.flush()
        await self.db.refresh(repo)
        return repo

    async def delete_repository(self, repo: Repository) -> None:
        await self.db.delete(repo)
        await self.db.flush()

    # ── ScanJob ───────────────────────────────────────────────────────────────

    async def create_scan_job(self, repository_id: uuid.UUID) -> ScanJob:
        job = ScanJob(repository_id=repository_id, status="pending")
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_scan_job(self, job_id: uuid.UUID) -> ScanJob | None:
        result = await self.db.execute(
            select(ScanJob).where(ScanJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_scan_job(self, repo_id: uuid.UUID) -> ScanJob | None:
        result = await self.db.execute(
            select(ScanJob)
            .where(ScanJob.repository_id == repo_id)
            .order_by(desc(ScanJob.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_scan_jobs(self, repo_id: uuid.UUID) -> list[ScanJob]:
        result = await self.db.execute(
            select(ScanJob)
            .where(ScanJob.repository_id == repo_id)
            .order_by(desc(ScanJob.created_at))
        )
        return list(result.scalars().all())

    async def update_scan_job(self, job: ScanJob, **kwargs) -> ScanJob:
        for key, value in kwargs.items():
            setattr(job, key, value)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    # ── AnalyticsSnapshot ─────────────────────────────────────────────────────

    async def create_snapshot(self, **kwargs) -> AnalyticsSnapshot:
        snapshot = AnalyticsSnapshot(**kwargs)
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(self, repo_id: uuid.UUID) -> AnalyticsSnapshot | None:
        result = await self.db.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.repository_id == repo_id)
            .order_by(desc(AnalyticsSnapshot.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
