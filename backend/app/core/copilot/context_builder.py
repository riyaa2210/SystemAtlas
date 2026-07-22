"""
Assembles a rich, structured context for the AI copilot.
Uses repo metadata, analytics snapshot, and README content.
No embeddings — structured context injection is fast, cheap, and reliable.
"""
from app.models.repository import Repository
from app.models.scan_job import AnalyticsSnapshot
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Builds a focused, information-dense prompt context for Gemini."""

    def build(
        self,
        repo: Repository,
        snapshot: AnalyticsSnapshot | None,
        node_context: dict | None = None,
    ) -> str:
        parts = []

        # ── Repo overview ──────────────────────────────────────────────────
        parts.append(f"# Repository: {repo.full_name}")
        if repo.description:
            parts.append(f"**Description:** {repo.description}")

        langs = ", ".join(repo.languages or []) or "Unknown"
        fws   = ", ".join(repo.frameworks or []) or "None detected"
        parts.append(f"**Languages:** {langs}")
        parts.append(f"**Frameworks:** {fws}")

        # ── Architecture metrics ───────────────────────────────────────────
        if snapshot:
            score = snapshot.architecture_score or 0
            score_label = (
                "Excellent" if score >= 80 else
                "Good"      if score >= 60 else
                "Fair"      if score >= 40 else "Poor"
            )
            parts.append(f"\n## Architecture Analysis")
            parts.append(f"- **Health Score:** {score}/100 ({score_label})")
            parts.append(f"- **Files analyzed:** {snapshot.total_files}")
            parts.append(f"- **Modules:** {snapshot.total_modules}")
            parts.append(f"- **Dependencies:** {snapshot.total_dependencies}")

            # Risks
            risks = []
            if snapshot.circular_deps:
                risks.append(f"{snapshot.circular_deps} circular dependenc{'y' if snapshot.circular_deps == 1 else 'ies'} (HIGH risk)")
            if snapshot.highly_coupled:
                risks.append(f"{snapshot.highly_coupled} highly-coupled modules")
            if snapshot.dead_modules:
                risks.append(f"{snapshot.dead_modules} potentially dead modules")
            if snapshot.missing_docs:
                risks.append(f"{snapshot.missing_docs} undocumented modules")

            if risks:
                parts.append(f"- **Risks identified:** {'; '.join(risks)}")
            else:
                parts.append("- **Risks:** None detected — architecture looks clean!")

            # Score breakdown
            if snapshot.metrics_json:
                bd = snapshot.metrics_json.get("score_breakdown", {})
                if bd:
                    parts.append("\n**Score deductions:**")
                    for k, v in bd.items():
                        if v < 0:
                            parts.append(f"  - {k.replace('_', ' ')}: {v} pts")

                # Additional context from scan
                fws_from_scan = snapshot.metrics_json.get("detected_frameworks", [])
                if fws_from_scan:
                    parts.append(f"\n**Detected frameworks:** {', '.join(fws_from_scan)}")

                readme = snapshot.metrics_json.get("readme_preview", "")
                if readme:
                    parts.append(f"\n## README (excerpt)\n{readme[:2000]}")

        # ── Focused node context ───────────────────────────────────────────
        if node_context:
            parts.append(f"\n## Currently Focused: {node_context.get('label', 'Unknown')} ({node_context.get('type', '')})")
            if node_context.get("path"):
                parts.append(f"Path: `{node_context['path']}`")
            neighbors = node_context.get("neighbors", [])
            if neighbors:
                parts.append(f"Connected to: {', '.join(n.get('label', '') for n in neighbors[:8])}")

        parts.append("\n---")
        parts.append("You are an expert software architect helping a developer understand their codebase.")
        parts.append("Be specific, actionable, and reference actual files/modules when relevant.")
        parts.append("Format your response with clear sections and bullet points when listing items.")

        return "\n".join(parts)
