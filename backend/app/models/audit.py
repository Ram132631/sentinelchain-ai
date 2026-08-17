from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import gen_id, utcnow


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    repository_id: Mapped[Optional[str]] = mapped_column(ForeignKey("repositories.id"), nullable=True, index=True)
    scan_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("scan_runs.id"), nullable=True, index=True)

    agent_name: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    input_data: Mapped[str] = mapped_column(Text, default="")
    output_data: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="COMPLETED")
    user_approval: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    severity: Mapped[str] = mapped_column(String, default="INFO")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    patch_id: Mapped[Optional[str]] = mapped_column(ForeignKey("patches.id"), nullable=True, index=True)
    vulnerability_id: Mapped[Optional[str]] = mapped_column(ForeignKey("vulnerabilities.id"), nullable=True)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision: Mapped[str] = mapped_column(String, default="PENDING")

    risk_level: Mapped[str] = mapped_column(String, default="CRITICAL")
    component_name: Mapped[str] = mapped_column(String, default="")
    proposed_change: Mapped[str] = mapped_column(Text, default="")
    ai_reasoning: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str] = mapped_column(String, default="")


class SecurityReport(Base):
    __tablename__ = "security_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    scan_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("scan_runs.id"), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    executive_summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[dict] = mapped_column(JSON, default=dict)
