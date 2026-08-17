from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class ScanRun(Base, TimestampMixin):
    """Groups one end-to-end autonomous pipeline execution across all 13 agents."""

    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)

    status: Mapped[str] = mapped_column(String, default="RUNNING")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    security_score_before: Mapped[int] = mapped_column(Integer, default=0)
    security_score_after: Mapped[int] = mapped_column(Integer, default=0)
    critical_before: Mapped[int] = mapped_column(Integer, default=0)
    critical_after: Mapped[int] = mapped_column(Integer, default=0)
    high_before: Mapped[int] = mapped_column(Integer, default=0)
    high_after: Mapped[int] = mapped_column(Integer, default=0)
    reachable_before: Mapped[int] = mapped_column(Integer, default=0)
    reachable_after: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String, default="")
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="scan_runs")
    executions: Mapped[list["AgentExecution"]] = relationship(back_populates="scan_run", cascade="all, delete-orphan")


class AgentExecution(Base, TimestampMixin):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    scan_run_id: Mapped[str] = mapped_column(ForeignKey("scan_runs.id"), index=True)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)

    agent_name: Mapped[str] = mapped_column(String, index=True)
    step_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    current_task: Mapped[str] = mapped_column(String, default="")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    tools_used: Mapped[list] = mapped_column(JSON, default=list)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    scan_run: Mapped["ScanRun"] = relationship(back_populates="executions")
