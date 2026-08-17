"""Central application configuration.

Reads from environment variables / .env. Every external integration
(GitHub, Anthropic Claude, OSV, Syft, Grype, Semgrep) is optional: the
platform must run fully in DEMO MODE when credentials/tools are absent.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
WORKSPACE_DIR = DATA_DIR / "workspaces"  # sandboxed clone/download targets
DB_PATH = DATA_DIR / "sentinelchain.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SentinelChain AI"
    environment: str = "development"
    api_prefix: str = "/api"

    database_url: str = f"sqlite:///{DB_PATH.as_posix()}"

    # --- Optional external credentials. Absence => graceful demo fallback. ---
    github_token: str | None = None
    anthropic_api_key: str | None = None
    osv_api_url: str = "https://api.osv.dev/v1"
    github_api_url: str = "https://api.github.com"

    # --- Security / sandboxing limits ---
    max_repo_size_mb: int = 250
    max_files_scanned: int = 5000
    subprocess_timeout_seconds: int = 60
    scan_step_min_delay_ms: int = 350
    scan_step_max_delay_ms: int = 900

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]

    demo_repo_slug: str = "demo-commerce-api"

    @property
    def github_configured(self) -> bool:
        return bool(self.github_token)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mask_secret(value: str | None) -> str:
    """Never echo full secrets back to clients or logs."""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
