"""
Repository service — orchestrates the full scan pipeline.
Triggered via FastAPI BackgroundTasks so it never blocks the API response.

Pipeline stages:
  1. clone        — shallow git clone to temp dir
  2. analyzing    — language detection + manifest parsing
  3. building_graph — static code analysis + Neo4j graph construction
  4. scoring      — risk detection + architecture metrics
  5. done         — cleanup, status update
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repo_repository import RepoRepository
from app.core.scanner.github_client import GitHubClient
from app.core.scanner.repo_cloner import RepoCloner
from app.core.scanner.language_detector import LanguageDetector
from app.core.scanner.manifest_parser import ManifestParser
from app.core.analyzer.python_analyzer import PythonAnalyzer
from app.core.analyzer.js_analyzer import JsAnalyzer
from app.core.analyzer.java_analyzer import JavaAnalyzer
from app.core.analyzer.analysis_result import FileAnalysisResult
from app.core.graph.graph_builder import GraphBuilder
from app.core.graph.risk_detector import RiskDetector
from app.core.analytics.metrics_engine import MetricsEngine
from app.utils.logger import get_logger
from app.utils.exceptions import NotFoundError, UnauthorizedError

logger = get_logger(__name__)

# Directories to skip during file analysis walk
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "target", "coverage",
}

# Safety cap — prevents runaway scans on enormous repos
MAX_FILES = 500


class RepositoryService:
    def __init__(self, db: AsyncSession):
        self.repo_repo = RepoRepository(db)
        self.db = db

    async def add_repository(self, user_id: uuid.UUID, github_url: str):
        """
        Validate the GitHub URL, fetch metadata from the API, persist to PostgreSQL.
        Does NOT trigger a scan — that is a separate explicit action.
        """
        client = GitHubClient()
        owner, repo_name = GitHubClient.parse_github_url(github_url)
        info = await client.get_repo_info(owner, repo_name)
        languages = await client.get_languages(info.languages_url)

        repo = await self.repo_repo.create_repository(
            user_id=user_id,
            name=info.name,
            full_name=info.full_name,
            github_url=github_url,
            description=info.description,
            languages=languages,
            default_branch=info.default_branch,
            is_private=info.is_private,
            star_count=info.star_count,
        )
        logger.info("Repository added", repo_id=str(repo.id), full_name=repo.full_name)
        return repo

    async def trigger_scan(self, repo_id: uuid.UUID, user_id: uuid.UUID):
        """Create a scan job record. The pipeline runs as a background task."""
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("You do not have access to this repository")

        job = await self.repo_repo.create_scan_job(repository_id=repo_id)
        logger.info("Scan job created", job_id=str(job.id), repo_id=str(repo_id))
        return job

    async def run_scan_pipeline(self, job_id: uuid.UUID, repo_id: uuid.UUID) -> None:
        """
        Full async scan pipeline — runs as a FastAPI BackgroundTask.
        Opens its own DB session since the request session has already closed.
        """
        from app.db.postgres import AsyncSessionFactory

        async with AsyncSessionFactory() as db:
            repo_repo = RepoRepository(db)
            job = await repo_repo.get_scan_job(job_id)
            repo = await repo_repo.get_by_id(repo_id)

            if not job or not repo:
                logger.error("Scan aborted: job or repo not found", job_id=str(job_id))
                return

            cloner = RepoCloner(str(job_id))

            try:
                # ── Stage 1: Clone ─────────────────────────────────────────────
                await repo_repo.update_scan_job(
                    job,
                    status="running",
                    stage="cloning",
                    started_at=datetime.now(timezone.utc),
                )
                await db.commit()

                clone_path = await cloner.clone(repo.github_url, repo.default_branch)

                # ── Stage 2: Detect languages + parse manifests ────────────────
                await repo_repo.update_scan_job(job, stage="analyzing")
                await db.commit()

                detection = LanguageDetector().detect(clone_path)
                manifest = ManifestParser().parse(clone_path)

                # Merge GitHub API languages with locally detected ones (deduplicated)
                merged_languages = list(dict.fromkeys(
                    detection.languages + (repo.languages or [])
                ))

                await repo_repo.update_repository(
                    repo,
                    languages=merged_languages,
                    frameworks=manifest.frameworks,
                )
                await db.commit()

                logger.info(
                    "Analysis complete",
                    job_id=str(job_id),
                    languages=merged_languages,
                    frameworks=manifest.frameworks,
                    total_files=detection.total_files,
                )

                # ── Stage 3: Analyze files ─────────────────────────────────────
                analyzers = [PythonAnalyzer(), JsAnalyzer(), JavaAnalyzer()]
                results: list[FileAnalysisResult] = []

                for file_path in clone_path.rglob("*"):
                    if any(skip in file_path.parts for skip in SKIP_DIRS):
                        continue
                    if not file_path.is_file():
                        continue
                    if len(results) >= MAX_FILES:
                        logger.warning(
                            "File cap reached, stopping analysis",
                            cap=MAX_FILES,
                            job_id=str(job_id),
                        )
                        break

                    for analyzer in analyzers:
                        if analyzer.can_analyze(file_path):
                            result = analyzer.analyze_file(file_path, clone_path)
                            results.append(result)
                            break

                await repo_repo.update_scan_job(job, files_scanned=len(results))
                await db.commit()

                # ── Stage 4: Build Neo4j graph ────────────────────────────────
                await repo_repo.update_scan_job(job, stage="building_graph")
                await db.commit()

                try:
                    from app.db.neo4j import get_neo4j_driver
                    driver = await get_neo4j_driver()
                    async with driver.session(database="neo4j") as neo4j_session:
                        builder = GraphBuilder()
                        nodes, edges = await builder.build(
                            str(repo_id), repo.full_name, results, neo4j_session
                        )
                except Exception as e:
                    logger.warning(
                        "Neo4j graph build failed — continuing without graph",
                        error=str(e),
                        job_id=str(job_id),
                    )
                    nodes, edges = 0, 0

                await repo_repo.update_scan_job(
                    job, nodes_created=nodes, edges_created=edges
                )
                await db.commit()

                # ── Stage 5: Compute metrics ──────────────────────────────────
                await repo_repo.update_scan_job(job, stage="scoring")
                await db.commit()

                from app.core.graph.risk_detector import RiskDetector
                from app.core.analytics.metrics_engine import MetricsEngine
                from app.core.graph.risk_detector import RiskReport

                risk_report = RiskReport()  # defaults to empty (Phase 8 fills this)
                try:
                    from app.db.neo4j import get_neo4j_driver
                    driver = await get_neo4j_driver()
                    async with driver.session(database="neo4j") as neo4j_session:
                        risk_report = await RiskDetector().detect(str(repo_id), neo4j_session)
                except Exception:
                    pass  # non-fatal

                missing_docs = sum(1 for r in results if not r.has_documentation)

                metrics = MetricsEngine().compute(
                    risk_report=risk_report,
                    total_files=len(results),
                    total_modules=max(nodes, len(results)),
                    total_deps=edges,
                    missing_docs=missing_docs,
                    has_tests=detection.has_tests,
                )

                await repo_repo.create_snapshot(
                    repository_id=repo_id,
                    scan_job_id=job_id,
                    architecture_score=metrics.architecture_score,
                    total_modules=metrics.total_modules,
                    total_files=metrics.total_files,
                    total_dependencies=metrics.total_dependencies,
                    circular_deps=metrics.circular_deps,
                    dead_modules=metrics.dead_modules,
                    highly_coupled=metrics.highly_coupled,
                    missing_docs=metrics.missing_docs,
                    metrics_json=metrics.metrics_json,
                )

                # ── Done ──────────────────────────────────────────────────────
                await repo_repo.update_scan_job(
                    job,
                    status="completed",
                    stage="done",
                    completed_at=datetime.now(timezone.utc),
                )
                await db.commit()

                logger.info(
                    "Scan pipeline completed",
                    job_id=str(job_id),
                    files=len(results),
                    score=metrics.architecture_score,
                )

            except Exception as e:
                logger.error(
                    "Scan pipeline failed",
                    job_id=str(job_id),
                    error=str(e),
                    exc_info=True,
                )
                try:
                    await repo_repo.update_scan_job(
                        job,
                        status="failed",
                        error_message=str(e)[:500],
                        completed_at=datetime.now(timezone.utc),
                    )
                    await db.commit()
                except Exception:
                    pass
            finally:
                cloner.cleanup()
