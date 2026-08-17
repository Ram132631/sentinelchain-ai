"""Repository Scanner Agent implementation.

Attempts a REAL GitHub API lookup (public repos need no token for basic
metadata + file-tree reads, subject to rate limits). Falls back to
DEMO MODE data when the network/API/token is unavailable, the repo cannot
be reached, or it is the built-in demo repository.
"""
from __future__ import annotations

import httpx

from app.config import get_settings
from app.demo_data.commerce_api import DEMO_REPO
from app.security.validation import validate_github_url

DEPENDENCY_FILE_SIGNATURES = {
    "package.json": ("JavaScript/TypeScript", "npm"),
    "package-lock.json": ("JavaScript/TypeScript", "npm"),
    "yarn.lock": ("JavaScript/TypeScript", "yarn"),
    "pnpm-lock.yaml": ("JavaScript/TypeScript", "pnpm"),
    "requirements.txt": ("Python", "pip"),
    "pyproject.toml": ("Python", "poetry/pip"),
    "Pipfile": ("Python", "pipenv"),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java/Kotlin", "gradle"),
    "go.mod": ("Go", "go modules"),
    "Cargo.toml": ("Rust", "cargo"),
    "Gemfile": ("Ruby", "bundler"),
    "composer.json": ("PHP", "composer"),
}


class RepoScanResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


async def scan_repository(url: str) -> tuple[RepoScanResult, bool]:
    """Returns (result, is_demo). Never raises for reachable network errors —
    degrades to demo data with a clear reason instead."""
    settings = get_settings()

    try:
        owner, repo = validate_github_url(url)
    except Exception:
        return _demo_result(reason="URL did not match https://github.com/<owner>/<repo> — using DEMO MODE sample data."), True

    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            repo_resp = await client.get(f"{settings.github_api_url}/repos/{owner}/{repo}", headers=headers)
            if repo_resp.status_code != 200:
                return _demo_result(
                    reason=f"GitHub API returned {repo_resp.status_code} for {owner}/{repo} "
                    "(private repo, rate limit, or no token configured) — using DEMO MODE sample data."
                ), True
            repo_json = repo_resp.json()

            default_branch = repo_json.get("default_branch", "main")
            tree_resp = await client.get(
                f"{settings.github_api_url}/repos/{owner}/{repo}/git/trees/{default_branch}",
                params={"recursive": "1"},
                headers=headers,
            )
            file_paths: list[str] = []
            if tree_resp.status_code == 200:
                tree_json = tree_resp.json()
                file_paths = [item["path"] for item in tree_json.get("tree", []) if item.get("type") == "blob"]

            languages_resp = await client.get(f"{settings.github_api_url}/repos/{owner}/{repo}/languages", headers=headers)
            languages = list(languages_resp.json().keys()) if languages_resp.status_code == 200 else []

            dependency_files = []
            package_managers = set()
            for path in file_paths:
                base = path.rsplit("/", 1)[-1]
                if base in DEPENDENCY_FILE_SIGNATURES:
                    dependency_files.append(path)
                    package_managers.add(DEPENDENCY_FILE_SIGNATURES[base][1])

            result = RepoScanResult(
                name=repo_json.get("name", repo),
                full_name=repo_json.get("full_name", f"{owner}/{repo}"),
                url=repo_json.get("html_url", url),
                description=repo_json.get("description") or "",
                primary_language=repo_json.get("language") or (languages[0] if languages else "Unknown"),
                languages=languages or ([repo_json.get("language")] if repo_json.get("language") else []),
                frameworks=[],
                package_managers=sorted(package_managers) or ["unknown"],
                dependency_files=dependency_files,
                file_count=len(file_paths),
                default_branch=default_branch,
                is_demo=False,
                demo_reason="",
                raw_file_paths=file_paths,
            )
            return result, False
    except httpx.HTTPError as exc:
        return _demo_result(reason=f"GitHub API unreachable ({exc.__class__.__name__}) — using DEMO MODE sample data."), True


def _demo_result(reason: str) -> RepoScanResult:
    data = dict(DEMO_REPO)
    return RepoScanResult(
        name=data["name"],
        full_name=data["full_name"],
        url=data["url"],
        description=data["description"],
        primary_language=data["primary_language"],
        languages=data["languages"],
        frameworks=data["frameworks"],
        package_managers=data["package_managers"],
        dependency_files=data["dependency_files"],
        file_count=data["file_count"],
        default_branch=data["default_branch"],
        is_demo=True,
        demo_reason=reason,
        raw_file_paths=[],
    )
