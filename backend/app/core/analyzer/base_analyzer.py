"""
Abstract base class for all language-specific analyzers.
Enforces a consistent interface across Python, JS, Java analyzers.
"""
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.analyzer.analysis_result import FileAnalysisResult


class BaseAnalyzer(ABC):
    """
    Contract for all language analyzers.
    Each subclass handles one language using Tree-sitter or AST parsing.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """File extensions this analyzer handles, e.g. ['.py']"""
        ...

    @abstractmethod
    def analyze_file(self, file_path: Path, repo_root: Path) -> FileAnalysisResult:
        """
        Parse a single file and return its analysis result.
        Must not raise — return partial result on error.
        """
        ...

    def can_analyze(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
