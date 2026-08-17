from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import agents, approvals, audit_logs, dashboard, patches, pull_requests, reports, repositories, vulnerabilities
from app.config import get_settings
from app.database.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelchain")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("SentinelChain AI backend ready. GitHub configured=%s Anthropic configured=%s", settings.github_configured, settings.anthropic_configured)
    yield


app = FastAPI(
    title="SentinelChain AI",
    description="Autonomous Software Supply Chain Security & Self-Healing SBOM Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error. The dashboard should degrade gracefully — please retry."})


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "SentinelChain AI",
        "demo_mode_available": True,
        "github_configured": settings.github_configured,
        "anthropic_configured": settings.anthropic_configured,
    }


@app.get("/")
def root():
    return {"message": "SentinelChain AI API — see /docs for the interactive API reference."}


app.include_router(repositories.router)
app.include_router(vulnerabilities.router)
app.include_router(patches.router)
app.include_router(pull_requests.router)
app.include_router(agents.router)
app.include_router(audit_logs.router)
app.include_router(reports.router)
app.include_router(approvals.router)
app.include_router(dashboard.router)
