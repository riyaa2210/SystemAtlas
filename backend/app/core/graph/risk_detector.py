"""Architecture risk detection using Neo4j graph queries."""
from dataclasses import dataclass, field
from app.core.graph.graph_queries import GraphQueries
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskReport:
    circular_dependencies: list[list[str]] = field(default_factory=list)
    highly_coupled_modules: list[dict] = field(default_factory=list)
    dead_modules: list[dict] = field(default_factory=list)


class RiskDetector:
    async def detect(self, repo_id: str, neo4j_session, coupling_threshold: int = 10) -> RiskReport:
        logger.info("Running risk detection", repo_id=repo_id)
        report = RiskReport()

        try:
            result = await neo4j_session.run(GraphQueries.FIND_CIRCULAR_DEPS, repo_id=repo_id)
            records = await result.data()
            seen: set[frozenset] = set()
            for record in records:
                cycle = record.get("cycle", [])
                if cycle:
                    key = frozenset(cycle)
                    if key not in seen:
                        seen.add(key)
                        report.circular_dependencies.append(cycle)
        except Exception as e:
            logger.error("Circular dependency query failed", repo_id=repo_id, error=str(e))

        try:
            result = await neo4j_session.run(GraphQueries.FIND_HIGHLY_COUPLED, repo_id=repo_id, threshold=coupling_threshold)
            records = await result.data()
            for record in records:
                report.highly_coupled_modules.append({"id": record.get("id"), "name": record.get("name"), "degree": record.get("degree")})
        except Exception as e:
            logger.error("Highly-coupled query failed", repo_id=repo_id, error=str(e))

        try:
            result = await neo4j_session.run(GraphQueries.FIND_DEAD_MODULES, repo_id=repo_id)
            records = await result.data()
            for record in records:
                report.dead_modules.append({"id": record.get("id"), "name": record.get("name")})
        except Exception as e:
            logger.error("Dead modules query failed", repo_id=repo_id, error=str(e))

        logger.info("Risk detection complete", repo_id=repo_id, circular=len(report.circular_dependencies), coupled=len(report.highly_coupled_modules), dead=len(report.dead_modules))
        return report
