from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class ASTFinding(Base, TimestampMixin):
    """Static/AST code analysis findings (dangerous calls, secrets, injection patterns)."""

    __tablename__ = "ast_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)

    file_path: Mapped[str] = mapped_column(String)
    line: Mapped[int] = mapped_column(Integer, default=0)
    function_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    issue_type: Mapped[str] = mapped_column(String)  # e.g. "Hardcoded Secret", "SQL Injection"
    severity: Mapped[str] = mapped_column(String, default="MEDIUM")
    code_snippet: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    rule_id: Mapped[str] = mapped_column(String, default="")
    tool: Mapped[str] = mapped_column(String, default="semgrep-fallback")


class LicenseFinding(Base, TimestampMixin):
    __tablename__ = "license_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("sbom_components.id"))

    component_name: Mapped[str] = mapped_column(String)
    license: Mapped[str] = mapped_column(String)
    classification: Mapped[str] = mapped_column(String, default="UNKNOWN")  # PERMISSIVE, WEAK_COPYLEFT, COPYLEFT, UNKNOWN
    policy_violation: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[str] = mapped_column(Text, default="")
