"""
Builds a structured context string from repository metadata and graph data
to inject into the AI prompt. No embeddings — structured injection.
"""
from app.models.repository import Repository
from app.models.scan_job import AnalyticsSnapshot
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """
    Assembles a focused context prompt from:
    - Repository metadata
    - Architecture analytics
    - Graph node info (when context_node_id is provided)
    """

    def build(
        self,
        repo: Repository,
        snapshot: AnalyticsSnapshot | None,
        node_context: dict | None = None,
    ) -> str:
        lines = [
            f"# Repository: {repo.full_name}",
            f"Description: {repo.description or 'No description provided'}",
            f"Languages: {', '.join(repo.languages or [])}",
            f"Frameworks: {', '.join(repo.frameworks or [])}",
            "",
        ]

        if snapshot:
            lines += [
                "## Architecture Summary",
                f"- Architecture Score: {snapshot.architecture_score}/100",
                f"- Total Files: {snapshot.total_files}",
                f"- Total Modules: {snapshot.total_modules}",
                f"- Total Dependencies: {snapshot.total_dependencies}",
                f"- Circular Dependencies: {snapshot.circular_deps}",
                f"- Highly Coupled Modules: {snapshot.highly_coupled}",
                f"- Dead Modules: {snapshot.dead_modules}",
                f"- Modules Missing Docs: {snapshot.missing_docs}",
                "",
            ]

        if node_context:
            lines += [
                "## Focused Node Context",
                f"Node: {node_context.get('label', 'Unknown')} ({node_context.get('type', '')})",
                f"Path: {node_context.get('path', '')}",
                "",
            ]
            neighbors = node_context.get("neighbors", [])
            if neighbors:
                lines.append("Connected to:")
                for n in neighbors[:10]:
                    lines.append(f"  - {n.get('label')} ({n.get('type')})")
                lines.append("")

        lines.append("Answer the developer's question based on this architecture context.")
        return "\n".join(lines)
