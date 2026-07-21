"""
Copilot service — assembles context and calls the Gemini API.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repo_repository import RepoRepository
from app.core.copilot.context_builder import ContextBuilder
from app.core.copilot.gemini_client import ask_gemini
from app.schemas.copilot import CopilotAskRequest, CopilotAskResponse, CopilotSource
from app.utils.exceptions import NotFoundError, UnauthorizedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CopilotService:
    def __init__(self, db: AsyncSession):
        self.repo_repo = RepoRepository(db)
        self.context_builder = ContextBuilder()

    async def ask(
        self, request: CopilotAskRequest, user_id: uuid.UUID
    ) -> CopilotAskResponse:
        repo = await self.repo_repo.get_by_id(request.repo_id)
        if not repo:
            raise NotFoundError("Repository", str(request.repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("Access denied")

        snapshot = await self.repo_repo.get_latest_snapshot(request.repo_id)

        # Build structured context (no embeddings needed)
        context = self.context_builder.build(
            repo=repo,
            snapshot=snapshot,
            node_context=None,  # Phase 9: inject node context when node_id provided
        )

        answer = await ask_gemini(context, request.question)

        sources: list[CopilotSource] = [
            CopilotSource(type="documentation", label=f"Repository: {repo.full_name}")
        ]

        logger.info("Copilot answered question", repo_id=str(request.repo_id))
        return CopilotAskResponse(
            answer=answer,
            sources=sources,
            question=request.question,
        )
