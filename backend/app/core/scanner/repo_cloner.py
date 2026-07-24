"""
Clones a GitHub repository to a temporary local directory.
Uses GitPython with depth=1 (shallow clone) for speed.
Handles cleanup after analysis completes.
"""
import os
import shutil
from pathlib import Path

import git

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import ScanError

logger = get_logger(__name__)
settings = get_settings()


class RepoCloner:
    """
    Manages cloning and cleanup of temporary repository directories.
    One instance per scan job — job_id is the temp dir name.
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.clone_path = Path(settings.temp_dir) / job_id

    async def clone(self, clone_url: str, branch: str = "main") -> Path:
        """
        Shallow-clone the repository to a temp directory.
        Returns the path to the cloned repo root.

        Uses depth=1 + single-branch for speed — we only need the latest snapshot,
        not the full history. Typical clone time: 3-30s depending on repo size.
        """
        logger.info(
            "Cloning repository",
            job_id=self.job_id,
            url=clone_url,
            branch=branch,
            path=str(self.clone_path),
        )

        os.makedirs(settings.temp_dir, exist_ok=True)

        # Clean up any leftover directory from a previous failed run
        if self.clone_path.exists():
            shutil.rmtree(self.clone_path, ignore_errors=True)

        # Inject token into HTTPS URL for higher rate limits / private repos
        authenticated_url = self._inject_token(clone_url)

        try:
            git.Repo.clone_from(
                authenticated_url,
                str(self.clone_path),
                branch=branch,
                depth=1,
                single_branch=True,
                # Suppress git output
                env={"GIT_TERMINAL_PROMPT": "0"},
            )
        except git.GitCommandError as e:
            error_msg = str(e)
            # Try main/master fallback if branch not found
            if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
                fallback = "master" if branch == "main" else "main"
                logger.warning(
                    "Branch not found, trying fallback",
                    original_branch=branch,
                    fallback=fallback,
                )
                try:
                    git.Repo.clone_from(
                        authenticated_url,
                        str(self.clone_path),
                        branch=fallback,
                        depth=1,
                        single_branch=True,
                        env={"GIT_TERMINAL_PROMPT": "0"},
                    )
                except git.GitCommandError as e2:
                    raise ScanError(f"Failed to clone repository: {e2}", stage="cloning")
            else:
                raise ScanError(f"Failed to clone repository: {e}", stage="cloning")

        logger.info(
            "Repository cloned successfully",
            path=str(self.clone_path),
            size_mb=round(self._dir_size_mb(self.clone_path), 1),
        )
        return self.clone_path

    def cleanup(self) -> None:
        """
        Remove the cloned directory after analysis is complete.
        Called in a finally block so it always runs even on error.
        """
        if self.clone_path.exists():
            shutil.rmtree(self.clone_path, ignore_errors=True)
            logger.info("Cleaned up clone directory", path=str(self.clone_path))

    def _inject_token(self, clone_url: str) -> str:
        """Add GitHub token to HTTPS URL if available."""
        if settings.github_token and "github.com" in clone_url:
            return clone_url.replace(
                "https://github.com",
                f"https://{settings.github_token}@github.com",
            )
        return clone_url

    @staticmethod
    def _dir_size_mb(path: Path) -> float:
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return total / (1024 * 1024)
