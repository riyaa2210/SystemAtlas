"""
Architecture score computation engine.
Stub — full implementation in Phase 8.
"""
from dataclasses import dataclass
from app.core.graph.risk_detector import RiskReport
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MetricsResult:
    architecture_score: float
    total_modules: int
    total_files: int
    total_dependencies: int
    circular_deps: int
    dead_modules: int
    highly_coupled: int
    missing_docs: int
    metrics_json: dict


class MetricsEngine:
    """
    Computes architecture health metrics and scores from graph data.
    
    Score formula (0–100, deductions):
      - Circular dependencies:  -5 per cycle   (max -30)
      - Highly coupled modules: -3 per module  (max -15)
      - Dead modules:           -2 per module  (max -10)
      - Missing documentation:  -1 per module  (max -15)
      - No test files detected: -10 flat
    """

    def compute(
        self,
        risk_report: RiskReport,
        total_files: int,
        total_modules: int,
        total_deps: int,
        missing_docs: int,
        has_tests: bool,
    ) -> MetricsResult:
        score = 100.0

        circular = len(risk_report.circular_dependencies)
        coupled = len(risk_report.highly_coupled_modules)
        dead = len(risk_report.dead_modules)

        score -= min(circular * 5, 30)
        score -= min(coupled * 3, 15)
        score -= min(dead * 2, 10)
        score -= min(missing_docs * 1, 15)
        if not has_tests:
            score -= 10

        score = max(0.0, min(100.0, score))

        return MetricsResult(
            architecture_score=round(score, 1),
            total_modules=total_modules,
            total_files=total_files,
            total_dependencies=total_deps,
            circular_deps=circular,
            dead_modules=dead,
            highly_coupled=coupled,
            missing_docs=missing_docs,
            metrics_json={
                "score_breakdown": {
                    "base": 100,
                    "circular_dep_penalty": min(circular * 5, 30),
                    "coupling_penalty": min(coupled * 3, 15),
                    "dead_module_penalty": min(dead * 2, 10),
                    "missing_docs_penalty": min(missing_docs * 1, 15),
                    "no_tests_penalty": 10 if not has_tests else 0,
                }
            },
        )
