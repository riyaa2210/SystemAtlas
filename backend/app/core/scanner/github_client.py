"""
GitHub REST API v3 wrapper.
Handles repo metadata, language detection, and URL parsing.
Uses httpx for async HTTP. Falls back gracefully on rate limit errors.
"""
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)
settings = get_settings()

GITHUB_API_BASE = "https://api.github.com"


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


class GitHubClient:
    """
    Thin async wrapper around the GitHub REST API v3.
    Injects PAT if available for higher rate limits (5000 req/hr vs 60).
    """

    def __init__(self):
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            self._headers["Authorization"] = f"Bearer {settings.github_token}"

    async def get_repo_info(self, owner: str, repo: str) -> GitHubRepoInfo:
        """Fetch metadata for a repository from the GitHub API."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

        async with httpx.AsyncClient(headers=self._headers, timeout=15.0) as client:
            response = await client.get(url)

        if response.status_code == 404:
            raise ExternalServiceError(
                "GitHub", f"Repository '{owner}/{repo}' not found or is private"
            )
        if response.status_code == 403:
            raise ExternalServiceError(
                "GitHub",
                "Rate limit exceeded. Add a GITHUB_TOKEN to .env to increase limit.",
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
        """
        Fetch languages used in a repo, sorted by bytes of code.
        Returns names only (e.g. ['Python', 'TypeScript']).
        """
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            response = await client.get(languages_url)

        if response.status_code != 200:
            logger.warning("Failed to fetch languages", status=response.status_code)
            return []

        # GitHub returns {language: bytes}, sort by bytes descending
        data = response.json()
        return [lang for lang, _ in sorted(data.items(), key=lambda x: x[1], reverse=True)]

    async def check_rate_limit(self) -> dict:
        """Returns current API rate limit status. Useful for debugging."""
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            response = await client.get(f"{GITHUB_API_BASE}/rate_limit")
        if response.status_code == 200:
            return response.json().get("rate", {})
        return {}

    @staticmethod
    def parse_github_url(url: str) -> tuple[str, str]:
        """
        Extract owner and repo name from any GitHub URL format.

        Handles:
          https://github.com/owner/repo
          https://github.com/owner/repo.git
          https://github.com/owner/repo/
          github.com/owner/repo
        """
        url = url.strip().rstrip("/").removesuffix(".git")

        # Validate it's actually a GitHub URL
        normalized = url.lower()
        if "github.com" not in normalized or (
            "github.com" in normalized and
            not any(normalized.startswith(p) for p in (
                "https://github.com", "http://github.com",
                "github.com", "git@github.com"
            ))
        ):
            raise ValueError(
                f"Not a GitHub URL: '{url}'. "
                "Expected format: https://github.com/owner/repository"
            )

        # Normalise: strip protocol prefix
        for prefix in ("https://", "http://", "git@github.com:"):
            if url.startswith(prefix):
                url = url[len(prefix):]
                break

        # Now url should be: github.com/owner/repo  or  owner/repo
        parts = url.replace("github.com/", "").split("/")
        parts = [p for p in parts if p]  # remove empty strings

        if len(parts) < 2:
            raise ValueError(
                f"Cannot parse GitHub URL '{url}'. "
                "Expected format: https://github.com/owner/repository"
            )

        return parts[0], parts[1]
