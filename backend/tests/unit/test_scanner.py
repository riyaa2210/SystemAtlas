"""
Unit tests for the GitHub scanner components.
These run without network or database access.
"""
import json
import tempfile
from pathlib import Path

import pytest


# ── GitHubClient.parse_github_url ─────────────────────────────────────────────

class TestParseGitHubUrl:
    def _parse(self, url):
        from app.core.scanner.github_client import GitHubClient
        return GitHubClient.parse_github_url(url)

    def test_standard_https(self):
        assert self._parse("https://github.com/fastapi/fastapi") == ("fastapi", "fastapi")

    def test_trailing_slash(self):
        assert self._parse("https://github.com/owner/repo/") == ("owner", "repo")

    def test_dot_git_suffix(self):
        assert self._parse("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_no_protocol(self):
        assert self._parse("github.com/owner/repo") == ("owner", "repo")

    def test_invalid_url(self):
        with pytest.raises(ValueError):
            self._parse("https://notgithub.com/owner/repo")

    def test_org_with_hyphen(self):
        owner, repo = self._parse("https://github.com/my-org/my-repo")
        assert owner == "my-org"
        assert repo == "my-repo"


# ── LanguageDetector ──────────────────────────────────────────────────────────

class TestLanguageDetector:
    def _make_repo(self, files: dict[str, str]) -> Path:
        """Create a temp directory with given files."""
        tmp = Path(tempfile.mkdtemp())
        for rel_path, content in files.items():
            full = tmp / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)
        return tmp

    def test_detects_python(self):
        from app.core.scanner.language_detector import LanguageDetector
        repo = self._make_repo({
            "main.py": "print('hello')",
            "utils.py": "def foo(): pass",
            "tests/test_main.py": "def test_foo(): pass",
        })
        result = LanguageDetector().detect(repo)
        assert "Python" in result.languages
        assert result.has_tests is True

    def test_detects_typescript(self):
        from app.core.scanner.language_detector import LanguageDetector
        repo = self._make_repo({
            "src/app.ts": "const x = 1",
            "src/utils.ts": "export function foo() {}",
            "src/types.ts": "type Foo = string",
        })
        result = LanguageDetector().detect(repo)
        assert "TypeScript" in result.languages

    def test_skips_node_modules(self):
        from app.core.scanner.language_detector import LanguageDetector
        repo = self._make_repo({
            "src/app.py": "pass",
            "src/utils.py": "pass",
            "node_modules/lib/index.js": "module.exports = {}",
            "node_modules/lib/utils.js": "module.exports = {}",
            "node_modules/lib/other.js": "module.exports = {}",
        })
        result = LanguageDetector().detect(repo)
        assert "JavaScript" not in result.languages

    def test_no_test_files(self):
        from app.core.scanner.language_detector import LanguageDetector
        repo = self._make_repo({
            "app.py": "pass",
            "utils.py": "pass",
        })
        result = LanguageDetector().detect(repo)
        assert result.has_tests is False

    def test_min_two_files_threshold(self):
        from app.core.scanner.language_detector import LanguageDetector
        repo = self._make_repo({
            "app.py": "pass",          # only 1 Python file
            "main.js": "var x = 1",    # only 1 JS file
        })
        result = LanguageDetector().detect(repo)
        # Neither reaches threshold of 2
        assert "Python" not in result.languages
        assert "JavaScript" not in result.languages


# ── ManifestParser ─────────────────────────────────────────────────────────────

class TestManifestParser:
    def _make_repo_with(self, filename: str, content: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / filename).write_text(content, encoding="utf-8")
        return tmp

    def test_package_json_detects_react(self):
        from app.core.scanner.manifest_parser import ManifestParser
        pkg = json.dumps({
            "name": "my-app",
            "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0", "next": "14.0.0"},
        })
        repo = self._make_repo_with("package.json", pkg)
        result = ManifestParser().parse(repo)
        assert "React" in result.frameworks
        assert "Next.js" in result.frameworks
        assert result.package_name == "my-app"

    def test_requirements_txt_detects_fastapi(self):
        from app.core.scanner.manifest_parser import ManifestParser
        content = "fastapi==0.111.0\nuvicorn[standard]==0.29.0\nsqlalchemy>=2.0\n"
        repo = self._make_repo_with("requirements.txt", content)
        result = ManifestParser().parse(repo)
        assert "FastAPI" in result.frameworks
        assert "fastapi" in result.dependencies

    def test_requirements_skips_comments(self):
        from app.core.scanner.manifest_parser import ManifestParser
        content = "# production deps\ndjango>=4.0\n# dev deps\npytest\n"
        repo = self._make_repo_with("requirements.txt", content)
        result = ManifestParser().parse(repo)
        assert "django" in result.dependencies
        assert "pytest" in result.dependencies

    def test_dockerfile_extracts_base_image(self):
        from app.core.scanner.manifest_parser import ManifestParser
        content = "FROM python:3.11-slim\nRUN pip install fastapi\n"
        repo = self._make_repo_with("Dockerfile", content)
        result = ManifestParser().parse(repo)
        assert result.docker_base_image == "python:3.11-slim"

    def test_empty_repo_returns_empty_result(self):
        from app.core.scanner.manifest_parser import ManifestParser
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        result = ManifestParser().parse(tmp)
        assert result.frameworks == []
        assert result.dependencies == []
