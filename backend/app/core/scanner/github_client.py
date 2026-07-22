"""
GitHub REST API v3 wrapper.
Fetches repo metadata AND file contents directly via the API.
NO git clone needed — faster, works everywhere, no git binary required.
"""
import base64
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable

import httpx

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)
settings = get_settings()

GITHUB_API_BASE = "https://api.github.com"

ANALYZABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rb", ".rs", ".cs",
}

SKIP_PATHS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target", "coverage",
    "vendor", ".gradle", ".mvn", "bower_components",
}

MAX_FILE_SIZE_BYTES = 100_000
MAX_FILES = 300


@dataclass
class GitHubRepoInfo:
    name: str
    full_name: str
    description: Optional[str]
    default_branch: str
    is_private: bool
    star_count: int
    clone_url: str
    languages_url: str
    topics: list[str]
    size_kb: int


@dataclass
class GitHubFile:
    path: str
    content: str
    size: int
    language: str = ""


_EXT_TO_LANG: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".jsx": "JavaScript", ".java": "Java",
    ".go": "Go", ".rb": "Ruby", ".rs": "Rust", ".cs": "C#",
}


class GitHubClient:
    """
    Async GitHub API client — fetches file trees and contents directly.
    No git clone required. Typically 5-10x faster than cloning.
    """

    def __init__(self):
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            self._headers["Authorization"] = f"Bearer {settings.github_token}"

    async def get_repo_info(self, owner: str, repo: str) -> GitHubRepoInfo:
        """Fetch metadata for a repository, following redirects automatically."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(
            headers=self._headers, timeout=15.0, follow_redirects=True
        ) as client:
            response = await client.get(url)

        if response.status_code == 404:
            raise ExternalServiceError(
                "GitHub", f"Repository '{owner}/{repo}' not found or is private"
            )
        if response.status_code == 403:
            raise ExternalServiceError(
                "GitHub",
                "Rate limit exceeded. Add GITHUB_TOKEN to .env for 5000 req/hr.",
            )
        if response.status_code != 200:
            raise ExternalServiceError(
                "GitHub", f"API returned {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        return GitHubRepoInfo(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            default_branch=data.get("default_branch", "main"),
            is_private=data.get("private", False),
            star_count=data.get("stargazers_count", 0),
            clone_url=data["clone_url"],
            languages_url=data["languages_url"],
            topics=data.get("topics", []),
            size_kb=data.get("size", 0),
        )

    async def get_languages(self, languages_url: str) -> list[str]:
        """Fetch languages sorted by bytes of code."""
        async with httpx.AsyncClient(
            headers=self._headers, timeout=10.0, follow_redirects=True
        ) as client:
            response = await client.get(languages_url)
        if response.status_code != 200:
            logger.warning("Failed to fetch languages", status=response.status_code)
            return []
        data = response.json()
        return [lang for lang, _ in sorted(data.items(), key=lambda x: x[1], reverse=True)]

    async def get_file_tree(self, owner: str, repo: str, branch: str) -> list[dict]:
        """
        Get the full recursive file tree using the Git Trees API.
        Single API call — much faster than cloning.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        async with httpx.AsyncClient(
            headers=self._headers, timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)

        if response.status_code == 409:
            return []   # empty repo
        if response.status_code == 404:
            return []   # branch not found — caller will try fallback
        if response.status_code != 200:
            raise ExternalServiceError(
                "GitHub", f"Failed to get file tree: {response.status_code}"
            )

        data = response.json()
        if data.get("truncated"):
            logger.warning("File tree truncated (repo > 100k files)")

        return [item for item in data.get("tree", []) if item.get("type") == "blob"]

    async def fetch_files(
        self,
        owner: str,
        repo: str,
        file_tree: list[dict],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list["GitHubFile"]:
        """
        Download analyzable file contents concurrently (10 at a time).
        No git clone — fetches only files we need via the Blobs API.
        """
        # Filter to analyzable files only
        analyzable = []
        for item in file_tree:
            path = item.get("path", "")
            size = item.get("size", 0)

            parts = path.split("/")
            if any(part in SKIP_PATHS for part in parts):
                continue

            ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext not in ANALYZABLE_EXTENSIONS:
                continue

            if size > MAX_FILE_SIZE_BYTES:
                continue

            analyzable.append(item)
            if len(analyzable) >= MAX_FILES:
                break

        logger.info("Fetching files", total=len(analyzable), repo=f"{owner}/{repo}")

        semaphore = asyncio.Semaphore(10)

        async def fetch_one(item: dict, idx: int) -> Optional[GitHubFile]:
            async with semaphore:
                path = item["path"]
                sha = item["sha"]
                try:
                    content = await self._fetch_blob(owner, repo, sha)
                    if content is not None:
                        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
                        lang = _EXT_TO_LANG.get(ext, "Unknown")
                        if progress_callback:
                            progress_callback(idx + 1, len(analyzable))
                        return GitHubFile(
                            path=path,
                            content=content,
                            size=item.get("size", 0),
                            language=lang,
                        )
                except Exception as e:
                    logger.warning("Failed to fetch file", path=path, error=str(e))
                return None

        tasks = [fetch_one(item, i) for i, item in enumerate(analyzable)]
        results = await asyncio.gather(*tasks)
        files = [f for f in results if f is not None]
        logger.info("Files fetched", count=len(files))
        return files

    async def _fetch_blob(self, owner: str, repo: str, sha: str) -> Optional[str]:
        """Fetch and decode a single file blob by SHA."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/blobs/{sha}"
        async with httpx.AsyncClient(
            headers=self._headers, timeout=15.0, follow_redirects=True
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        if data.get("encoding") == "base64":
            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            except Exception:
                return None
        return data.get("content", "")

    async def check_rate_limit(self) -> dict:
        """Returns current GitHub API rate limit info."""
        async with httpx.AsyncClient(
            headers=self._headers, timeout=10.0, follow_redirects=True
        ) as client:
            response = await client.get(f"{GITHUB_API_BASE}/rate_limit")
        if response.status_code == 200:
            core = response.json().get("rate", {})
            logger.info(
                "GitHub rate limit",
                remaining=core.get("remaining"),
                limit=core.get("limit"),
            )
            return core
        return {}

    @staticmethod
    def parse_github_url(url: str) -> tuple[str, str]:
        """Parse owner and repo from any GitHub URL format."""
        url = url.strip().rstrip("/").removesuffix(".git")
        normalized = url.lower()

        if not any(normalized.startswith(p) for p in (
            "https://github.com", "http://github.com",
            "github.com", "git@github.com",
        )):
            raise ValueError(
                f"Not a GitHub URL: '{url}'. "
                "Expected format: https://github.com/owner/repository"
            )

        for prefix in ("https://", "http://", "git@github.com:"):
            if url.startswith(prefix):
                url = url[len(prefix):]
                break

        parts = [p for p in url.replace("github.com/", "").split("/") if p]
        if len(parts) < 2:
            raise ValueError(
                "Cannot parse GitHub URL. Expected: https://github.com/owner/repo"
            )
        return parts[0], parts[1]
