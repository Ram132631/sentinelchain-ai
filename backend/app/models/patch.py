from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class Patch(Base, TimestampMixin):
    __tablename__ = "patches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    vulnerability_id: Mapped[str] = mapped_column(ForeignKey("vulnerabilities.id"), index=True)

    component_name: Mapped[str] = mapped_column(String)
    current_version: Mapped[str] = mapped_column(String)
    target_version: Mapped[str] = mapped_column(String)
    dependency_file: Mapped[str] = mapped_column(String)
    diff_text: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    breaking_change_risk: Mapped[str] = mapped_column(String, default="LOW")  # LOW/MEDIUM/HIGH
    breaking_change_reason: Mapped[str] = mapped_column(Text, default="")

    risk_before: Mapped[int] = mapped_column(Integer, default=0)
    risk_after: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String, default="GENERATED")
    security_approval: Mapped[str] = mapped_column(String, default="PENDING")  # APPROVED/REJECTED/NEEDS_HUMAN_REVIEW/PENDING
    auditor_notes: Mapped[str] = mapped_column(Text, default="")

    vulnerability: Mapped["Vulnerability"] = relationship(back_populates="patches")
    test_results: Mapped[list["TestResult"]] = relationship(back_populates="patch", cascade="all, delete-orphan")
    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="patch", cascade="all, delete-orphan")


class TestResult(Base, TimestampMixin):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    patch_id: Mapped[str] = mapped_column(ForeignKey("patches.id"), index=True)

    test_type: Mapped[str] = mapped_column(String)  # UNIT, SECURITY_SCAN, STATIC_ANALYSIS, REGRESSION, SBOM_DIFF
    status: Mapped[str] = mapped_column(String, default="PASS")  # PASS/FAIL
    summary: Mapped[str] = mapped_column(String, default="")
    details: Mapped[str] = mapped_column(Text, default="")
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    patch: Mapped["Patch"] = relationship(back_populates="test_results")
