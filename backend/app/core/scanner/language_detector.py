"""
Detects programming languages used in a cloned repository
by scanning file extensions and counting files per language.
Also detects test file presence.
"""
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field

# Extension → language name
EXTENSION_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".R": "R",
    ".dart": "Dart",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".sql": "SQL",
    ".tf": "Terraform",
    ".md": "Markdown",
}

# Directories to skip entirely during scanning
SKIP_DIRS: set[str] = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "out", "target", ".idea", ".vscode",
    "coverage", ".pytest_cache", ".mypy_cache", ".tox",
    "vendor", "bower_components", ".gradle", ".mvn",
}

# File/dir name patterns that indicate test code
TEST_INDICATORS = {"test", "tests", "spec", "specs", "__tests__", "e2e"}


@dataclass
class DetectionResult:
    languages: list[str]        # sorted by file count, most common first
    has_tests: bool
    total_files: int
    language_counts: dict[str, int] = field(default_factory=dict)


class LanguageDetector:
    """
    Scans a cloned repository tree to identify primary programming languages.
    Uses file extension counting — fast and reliable enough for our purpose.
    """

    def detect(self, repo_path: Path) -> DetectionResult:
        """
        Walk the repo and count files per language.
        Returns languages sorted by file count, filtered to those with >= 2 files.
        """
        counts: Counter = Counter()
        has_tests = False
        total_files = 0

        for file_path in repo_path.rglob("*"):
            # Skip ignored directories
            if any(skip in file_path.parts for skip in SKIP_DIRS):
                continue

            if not file_path.is_file():
                continue

            total_files += 1

            # Detect test files
            parts_lower = {p.lower() for p in file_path.parts}
            name_lower = file_path.stem.lower()
            if (parts_lower & TEST_INDICATORS) or name_lower.startswith("test_") or name_lower.endswith("_test"):
                has_tests = True

            # Count language
            lang = EXTENSION_MAP.get(file_path.suffix.lower())
            if lang:
                counts[lang] += 1

        # Only include languages with at least 2 files
        filtered = {lang: count for lang, count in counts.items() if count >= 2}
        sorted_langs = [lang for lang, _ in sorted(filtered.items(), key=lambda x: x[1], reverse=True)]

        return DetectionResult(
            languages=sorted_langs,
            has_tests=has_tests,
            total_files=total_files,
            language_counts=dict(counts.most_common()),
        )
