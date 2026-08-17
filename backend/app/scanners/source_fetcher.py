"""Fetches a bounded sample of source files from GitHub for real-repo AST /
reachability analysis. Read-only, sandboxed by a strict file-count cap —
never writes to disk, never executes fetched content.
"""
from __future__ import annotations

import base64

import httpx

from app.config import get_settings

SOURCE_EXTENSIONS = (".js", ".ts", ".jsx", ".tsx", ".py")
MAX_SOURCE_FILES = 15
MAX_FILE_BYTES = 60_000


async def fetch_source_sample(owner: str, repo: str, branch: str, file_paths: list[str]) -> dict[str, str]:
    settings = get_settings()
    headers = {"Accept": "application/vnd.github.raw+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    candidates = [p for p in file_paths if p.endswith(SOURCE_EXTENSIONS)][:MAX_SOURCE_FILES]
    out: dict[str, str] = {}
    if not candidates:
        return out

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for path in candidates:
                resp = await client.get(
                    f"{settings.github_api_url}/repos/{owner}/{repo}/contents/{path}",
                    params={"ref": branch},
                    headers=headers,
                )
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                content = payload.get("content", "")
                if not content or payload.get("size", 0) > MAX_FILE_BYTES:
                    continue
                try:
                    out[path] = base64.b64decode(content).decode("utf-8", errors="ignore")
                except Exception:
                    continue
    except httpx.HTTPError:
        return out
    return out
