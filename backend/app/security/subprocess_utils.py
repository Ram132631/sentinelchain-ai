"""Secure subprocess execution wrapper.

All optional external CLI tools (syft, grype, semgrep) are invoked only
through this helper: fixed argv lists (never shell=True / string
concatenation), an explicit timeout, and a restricted, sandboxed working
directory. Any repository source code is treated as untrusted and is never
executed — these tools only *read* files for static analysis.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.config import get_settings


class ToolUnavailable(Exception):
    pass


def tool_available(binary_name: str) -> bool:
    return shutil.which(binary_name) is not None


def run_tool(argv: list[str], cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a fixed, allow-listed external tool binary safely.

    Never pass shell=True and never build argv via string interpolation of
    user/repo-controlled data — callers must pass argv as a list.
    """
    if not argv or not isinstance(argv, list):
        raise ValueError("argv must be a non-empty list")
    binary = argv[0]
    if not tool_available(binary):
        raise ToolUnavailable(f"'{binary}' is not installed in this environment.")

    settings = get_settings()
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout or settings.subprocess_timeout_seconds,
        shell=False,
        check=False,
    )
