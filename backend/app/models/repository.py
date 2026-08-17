from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String, index=True)
    full_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    url: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    primary_language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    frameworks: Mapped[list] = mapped_column(JSON, default=list)
    package_managers: Mapped[list] = mapped_column(JSON, default=list)
    dependency_files: Mapped[list] = mapped_column(JSON, default=list)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    default_branch: Mapped[str] = mapped_column(String, default="main")

    status: Mapped[str] = mapped_column(String, default="UNSCANNED")  # UNSCANNED, SCANNING, SCANNED, ERROR
    health_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    total_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    direct_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    transitive_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)
    reachable_count: Mapped[int] = mapped_column(Integer, default=0)

    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    components: Mapped[list["SBOMComponent"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    scan_runs: Mapped[list["ScanRun"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
