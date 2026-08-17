from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class AgentStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    REJECTED = "REJECTED"


class PatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    TESTED = "TESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class PullRequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    OPEN = "OPEN"
    MERGED = "MERGED"
    CLOSED = "CLOSED"


class ApprovalDecision(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class VulnerabilityStatus(str, enum.Enum):
    OPEN = "OPEN"
    PATCH_AVAILABLE = "PATCH_AVAILABLE"
    PATCHED = "PATCHED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


AGENT_NAMES = [
    "Repository Scanner",
    "SBOM Agent",
    "Dependency Analyzer",
    "Vulnerability Intelligence",
    "Risk Prioritization",
    "Reachability Analysis",
    "AST Code Analysis",
    "License Compliance",
    "Patch Generator",
    "QA Validation",
    "Security Auditor",
    "Release Manager",
    "Documentation Agent",
]
