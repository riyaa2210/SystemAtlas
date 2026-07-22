"""
Repository service — scan pipeline using GitHub API (no git clone).
Graph is stored in PostgreSQL (JSONB) so it always works without Neo4j.
Neo4j is used additionally if available for richer graph queries.
"""
import uuid
import json as _json
import os as _os
import re as _re
import tempfile
import shutil
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path as _Path, PurePosixPath

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repo_repository import RepoRepository
from app.core.scanner.github_client import GitHubClient, GitHubFile
from app.core.scanner.manifest_parser import ManifestParser
from app.core.analyzer.python_analyzer import PythonAnalyzer
from app.core.analyzer.js_analyzer import JsAnalyzer
from app.core.analyzer.java_analyzer import JavaAnalyzer
from app.core.analyzer.analysis_result import FileAnalysisResult
from app.core.graph.graph_builder import GraphBuilder
from app.core.graph.risk_detector import RiskDetector, RiskReport
from app.core.analytics.metrics_engine import MetricsEngine
from app.utils.logger import get_logger
from app.utils.exceptions import NotFoundError, UnauthorizedError

logger = get_logger(__name__)

_SCAN_TMP = _os.path.join(
    _os.environ.get("TEMP", _os.environ.get("TMP", "/tmp")), "lam_scan"
)

_EXT_MAP = {
    "Python": ".py",
    "TypeScript": ".ts",
    "JavaScript": ".js",
    "Java": ".java",
}


def _make_id(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _build_in_memory_graph(
    repo_id: str,
    repo_name: str,
    results: list[FileAnalysisResult],
) -> tuple[list[dict], list[dict]]:
    """
    Build graph nodes and edges from analysis results in memory.
    Stored in PostgreSQL JSONB — works without Neo4j.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    file_id_map: dict[str, str] = {}

    # Repository node
    repo_node_id = _make_id("repository", repo_id)
    nodes.append({
        "id": repo_node_id, "type": "Service",
        "label": repo_name,
        "properties": {"name": repo_name, "repo_id": repo_id},
    })

    # Module grouping
    module_map: dict[str, list] = {}
    for r in results:
        top = str(PurePosixPath(r.file_path.replace("\\", "/")).parts[0]) if "/" in r.file_path else "."
        module_map.setdefault(top, []).append(r)

    module_id_map: dict[str, str] = {}
    for module_path, files in module_map.items():
        mid = _make_id("module", repo_id, module_path)
        module_id_map[module_path] = mid
        nodes.append({
            "id": mid, "type": "Module",
            "label": module_path,
            "properties": {"name": module_path, "path": module_path, "repo_id": repo_id, "file_count": len(files)},
        })
        edges.append({"id": f"{repo_node_id}->{mid}", "source": repo_node_id, "target": mid, "type": "CONTAINS", "properties": {}})

    for result in results:
        norm = result.file_path.replace("\\", "/")
        fid = _make_id("file", repo_id, norm)
        file_id_map[norm] = fid
        top = str(PurePosixPath(norm).parts[0]) if "/" in norm else "."
        fname = PurePosixPath(norm).name

        nodes.append({
            "id": fid, "type": "File",
            "label": fname,
            "properties": {
                "name": fname, "path": norm, "repo_id": repo_id,
                "language": result.language, "lines_of_code": result.lines_of_code,
                "has_documentation": result.has_documentation,
                "functions": len(result.functions),
                "classes": len(result.classes),
            },
        })

        mid = module_id_map.get(top)
        if mid:
            edges.append({"id": f"{mid}->{fid}", "source": mid, "target": fid, "type": "CONTAINS", "properties": {}})

        # API endpoints
        for ep in result.api_endpoints:
            aid = _make_id("api", repo_id, norm, ep.path, ep.method)
            nodes.append({
                "id": aid, "type": "Api",
                "label": f"{ep.method} {ep.path}",
                "properties": {"name": ep.handler, "path": ep.path, "method": ep.method, "repo_id": repo_id},
            })
            edges.append({"id": f"{fid}->{aid}", "source": fid, "target": aid, "type": "DEFINES", "properties": {}})

    # Import edges
    for result in results:
        norm = result.file_path.replace("\\", "/")
        src_id = file_id_map.get(norm)
        if not src_id:
            continue
        src_dir = str(PurePosixPath(norm).parent)
        for imp in result.imports:
            # Try to resolve to known file
            for candidate in _resolve_candidates(imp.module, imp.is_relative, src_dir, result.language):
                tgt_id = file_id_map.get(candidate)
                if tgt_id and tgt_id != src_id:
                    eid = f"{src_id}->{tgt_id}"
                    edges.append({"id": eid, "source": src_id, "target": tgt_id, "type": "IMPORTS", "properties": {}})
                    break

    return nodes, edges


def _resolve_candidates(module: str, is_relative: bool, source_dir: str, language: str) -> list[str]:
    m = module.replace("\\", "/").lstrip("/")
    if language == "Python":
        base = f"{source_dir}/{m.replace('.', '/')}" if is_relative else m.replace(".", "/")
        return [f"{base}.py", f"{base}/__init__.py"]
    elif language in ("JavaScript", "TypeScript"):
        base = f"{source_dir}/{m}" if is_relative else m
        base = str(PurePosixPath(base))
        return [f"{base}{ext}" for ext in (".ts", ".tsx", ".js", ".jsx")] + [f"{base}/index.ts", f"{base}/index.js"]
    elif language == "Java":
        base = m.replace(".", "/")
        return [f"{base}.java", f"src/main/java/{base}.java"]
    return []


class RepositoryService:
    def __init__(self, db: AsyncSession):
        self.repo_repo = RepoRepository(db)
        self.db = db

    async def add_repository(self, user_id: uuid.UUID, github_url: str):
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
        """Create a new scan job. Previous scan results are preserved until new scan completes."""
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != user_id:
            raise UnauthorizedError("You do not have access to this repository")
        job = await self.repo_repo.create_scan_job(repository_id=repo_id)
        logger.info("Scan job created", job_id=str(job.id))
        return job

    async def run_scan_pipeline(self, job_id: uuid.UUID, repo_id: uuid.UUID) -> None:
        from app.db.postgres import AsyncSessionFactory

        async with AsyncSessionFactory() as db:
            repo_repo = RepoRepository(db)
            job = await repo_repo.get_scan_job(job_id)
            repo = await repo_repo.get_by_id(repo_id)

            if not job or not repo:
                logger.error("Scan aborted: not found", job_id=str(job_id))
                return

            client = GitHubClient()

            try:
                # 1. Fetch file tree
                await repo_repo.update_scan_job(job, status="running", stage="fetching_tree", started_at=datetime.now(timezone.utc))
                await db.commit()

                owner, repo_name = GitHubClient.parse_github_url(repo.github_url)

                rate = await client.check_rate_limit()
                if rate.get("remaining", 60) < 10:
                    raise Exception(f"GitHub rate limit: {rate.get('remaining')}/{rate.get('limit')} remaining. Add GITHUB_TOKEN to .env.")

                file_tree = await client.get_file_tree(owner, repo_name, repo.default_branch)
                if not file_tree and repo.default_branch == "main":
                    file_tree = await client.get_file_tree(owner, repo_name, "master")

                # 2. Download files
                await repo_repo.update_scan_job(job, stage="downloading")
                await db.commit()

                files_fetched: list[GitHubFile] = await client.fetch_files(owner, repo_name, file_tree)
                await repo_repo.update_scan_job(job, files_scanned=len(files_fetched))
                await db.commit()

                # 3. Language detection + manifest parsing
                await repo_repo.update_scan_job(job, stage="analyzing")
                await db.commit()

                lang_counts: Counter = Counter()
                has_tests = False
                readme_content = ""
                manifest_deps: list[str] = []

                for f in files_fetched:
                    lang_counts[f.language] += 1
                    if "test" in f.path.lower():
                        has_tests = True
                    fname = f.path.split("/")[-1].lower()
                    if fname == "package.json":
                        try:
                            data = _json.loads(f.content)
                            manifest_deps.extend(data.get("dependencies", {}).keys())
                            manifest_deps.extend(data.get("devDependencies", {}).keys())
                        except Exception:
                            pass
                    elif fname == "requirements.txt":
                        for line in f.content.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#"):
                                pkg = _re.split(r"[>=<!~;\[]", line)[0].strip().lower()
                                if pkg:
                                    manifest_deps.append(pkg)
                    elif fname in ("readme.md", "readme.rst", "readme.txt"):
                        readme_content = f.content[:3000]

                detected_langs = [l for l, _ in lang_counts.most_common() if l != "Unknown"]
                manifest_frameworks = ManifestParser()._detect_frameworks(manifest_deps)
                merged_languages = list(dict.fromkeys(detected_langs + (repo.languages or [])))

                await repo_repo.update_repository(repo, languages=merged_languages, frameworks=manifest_frameworks)
                await db.commit()

                # 4. Analyze file contents
                analyzers = {"Python": PythonAnalyzer(), "TypeScript": JsAnalyzer(), "JavaScript": JsAnalyzer(), "Java": JavaAnalyzer()}
                results: list[FileAnalysisResult] = []
                _os.makedirs(_SCAN_TMP, exist_ok=True)

                for gh_file in files_fetched:
                    analyzer = analyzers.get(gh_file.language)
                    if not analyzer:
                        continue
                    try:
                        ext = _EXT_MAP.get(gh_file.language, ".txt")
                        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, encoding="utf-8", delete=False, dir=_SCAN_TMP) as tmp:
                            tmp.write(gh_file.content)
                            tmp_path = _Path(tmp.name)
                        result = analyzer.analyze_file(tmp_path, tmp_path.parent)
                        result.file_path = gh_file.path
                        result.language = gh_file.language
                        results.append(result)
                        try:
                            _os.unlink(tmp_path)
                        except Exception:
                            pass
                    except Exception as e:
                        logger.warning("Analysis failed", path=gh_file.path, error=str(e))

                # 5. Build graph in memory (always works) + Neo4j if available
                await repo_repo.update_scan_job(job, stage="building_graph")
                await db.commit()

                graph_nodes, graph_edges = _build_in_memory_graph(str(repo_id), repo.full_name, results)
                nodes = len(graph_nodes)
                edges = len(graph_edges)

                # Try Neo4j as well
                try:
                    from app.db.neo4j import get_neo4j_driver
                    driver = await get_neo4j_driver()
                    async with driver.session(database="neo4j") as neo4j_session:
                        await GraphBuilder().build(str(repo_id), repo.full_name, results, neo4j_session)
                    logger.info("Graph also written to Neo4j")
                except Exception as e:
                    logger.info("Neo4j not available — using PostgreSQL graph only", reason=str(e)[:80])

                await repo_repo.update_scan_job(job, nodes_created=nodes, edges_created=edges)
                await db.commit()

                # 6. Score
                await repo_repo.update_scan_job(job, stage="scoring")
                await db.commit()

                risk_report = RiskReport()
                try:
                    from app.db.neo4j import get_neo4j_driver
                    driver = await get_neo4j_driver()
                    async with driver.session(database="neo4j") as neo4j_session:
                        risk_report = await RiskDetector().detect(str(repo_id), neo4j_session)
                except Exception:
                    pass

                missing_docs = sum(1 for r in results if not r.has_documentation)
                metrics = MetricsEngine().compute(
                    risk_report=risk_report,
                    total_files=len(files_fetched),
                    total_modules=max(nodes, max(len(results), 1)),
                    total_deps=edges,
                    missing_docs=missing_docs,
                    has_tests=has_tests,
                )

                metrics.metrics_json["readme_preview"] = readme_content
                metrics.metrics_json["manifest_deps_count"] = len(manifest_deps)
                metrics.metrics_json["detected_frameworks"] = manifest_frameworks

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
                    # Persist graph in Postgres
                    graph_data={"nodes": graph_nodes, "edges": graph_edges},
                )

                await repo_repo.update_scan_job(job, status="completed", stage="done", completed_at=datetime.now(timezone.utc))
                await db.commit()

                logger.info("Scan complete", job_id=str(job_id), files=len(results), score=metrics.architecture_score, nodes=nodes, edges=edges)

            except Exception as e:
                logger.error("Scan failed", job_id=str(job_id), error=str(e), exc_info=True)
                try:
                    await repo_repo.update_scan_job(job, status="failed", error_message=str(e)[:500], completed_at=datetime.now(timezone.utc))
                    await db.commit()
                except Exception:
                    pass
            finally:
                try:
                    shutil.rmtree(_SCAN_TMP, ignore_errors=True)
                except Exception:
                    pass
