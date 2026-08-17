from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class SBOMComponent(Base, TimestampMixin):
    __tablename__ = "sbom_components"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)

    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    ecosystem: Mapped[str] = mapped_column(String)  # npm, PyPI, Maven, Go, crates.io
    purl: Mapped[str] = mapped_column(String, default="")
    license: Mapped[str] = mapped_column(String, default="Unknown")
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_direct: Mapped[bool] = mapped_column(Boolean, default=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    latest_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_outdated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    suspicious_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_vulnerable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reachable: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    source_tool: Mapped[str] = mapped_column(String, default="fallback-parser")  # syft | fallback-parser

    repository: Mapped["Repository"] = relationship(back_populates="components")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(back_populates="component", cascade="all, delete-orphan")


class DependencyRelationship(Base, TimestampMixin):
    __tablename__ = "dependency_relationships"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("sbom_components.id"), nullable=True)
    child_id: Mapped[str] = mapped_column(ForeignKey("sbom_components.id"))
