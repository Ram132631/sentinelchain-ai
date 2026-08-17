"""Input validation & sandboxing guards.

These helpers exist so the platform never executes arbitrary host commands,
never writes outside its own sandboxed workspace directory, and never
ingests a repository beyond configured size/file-count limits.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from app.config import WORKSPACE_DIR, get_settings

GITHUB_URL_RE = re.compile(r"^https?://github\.com/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+?)(\.git)?/?$")


class ValidationError(ValueError):
    pass


def validate_github_url(url: str) -> tuple[str, str]:
    """Validate & parse a GitHub repository URL. Returns (owner, repo)."""
    url = (url or "").strip()
    if not url:
        raise ValidationError("Repository URL is required.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("Only https:// GitHub URLs are supported.")
    match = GITHUB_URL_RE.match(url)
    if not match:
        raise ValidationError("URL must look like https://github.com/<owner>/<repo>.")
    owner, repo, _ = match.groups()
    return owner, repo


def safe_workspace_path(*parts: str) -> Path:
    """Resolve a path strictly inside the sandboxed workspace directory."""
    candidate = (WORKSPACE_DIR / Path(*parts)).resolve()
    if WORKSPACE_DIR.resolve() not in candidate.parents and candidate != WORKSPACE_DIR.resolve():
        raise ValidationError("Path traversal outside sandbox workspace is not permitted.")
    return candidate


def enforce_repo_limits(file_count: int, size_mb: float) -> None:
    settings = get_settings()
    if file_count > settings.max_files_scanned:
        raise ValidationError(
            f"Repository exceeds the scan file limit ({file_count} > {settings.max_files_scanned})."
        )
    if size_mb > settings.max_repo_size_mb:
        raise ValidationError(
            f"Repository exceeds the scan size limit ({size_mb:.1f}MB > {settings.max_repo_size_mb}MB)."
        )
