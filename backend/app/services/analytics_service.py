"""
Analytics service — fetches architecture metrics for a repository.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repo_repository import RepoRepository
from app.schemas.analytics import AnalyticsResponse, RiskItem
from app.utils.exceptions import NotFoundError, UnauthorizedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.repo_repo = RepoRepository(db)

    async def get_analytics(
        self, repo_id: uuid.UUID, user_id: uuid.UUID
    ) -> AnalyticsResponse:
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("Access denied")

        snapshot = await self.repo_repo.get_latest_snapshot(repo_id)
        if not snapshot:
            raise NotFoundError("Analytics", str(repo_id))

        return AnalyticsResponse.model_validate(snapshot)

    async def get_risks(
        self, repo_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[RiskItem]:
        """
        Builds a list of risk items from the latest analytics snapshot.
        Phase 8: will also pull live data from Neo4j.
        """
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("Access denied")

        snapshot = await self.repo_repo.get_latest_snapshot(repo_id)
        if not snapshot:
            return []

        risks: list[RiskItem] = []

        if snapshot.circular_deps > 0:
            risks.append(RiskItem(
                type="circular_dependency",
                severity="high",
                title=f"{snapshot.circular_deps} Circular Dependenc{'y' if snapshot.circular_deps == 1 else 'ies'} Detected",
                description="Circular dependencies make code hard to test, refactor, and reason about.",
            ))

        if snapshot.highly_coupled > 0:
            risks.append(RiskItem(
                type="high_coupling",
                severity="medium",
                title=f"{snapshot.highly_coupled} Highly Coupled Module{'s' if snapshot.highly_coupled > 1 else ''}",
                description="Modules with too many dependencies are fragile and difficult to change.",
            ))

        if snapshot.dead_modules > 0:
            risks.append(RiskItem(
                type="dead_module",
                severity="low",
                title=f"{snapshot.dead_modules} Dead Module{'s' if snapshot.dead_modules > 1 else ''} Found",
                description="Modules with no incoming dependencies may be unused and can be removed.",
            ))

        if snapshot.missing_docs > 0:
            risks.append(RiskItem(
                type="missing_docs",
                severity="low",
                title=f"{snapshot.missing_docs} Module{'s' if snapshot.missing_docs > 1 else ''} Missing Documentation",
                description="Undocumented modules increase onboarding time and reduce maintainability.",
            ))

        return risks
