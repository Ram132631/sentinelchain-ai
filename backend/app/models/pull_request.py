from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, gen_id


class PullRequest(Base, TimestampMixin):
    __tablename__ = "pull_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    patch_id: Mapped[str] = mapped_column(ForeignKey("patches.id"), index=True)

    pr_number: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    branch_name: Mapped[str] = mapped_column(String, default="")
    base_branch: Mapped[str] = mapped_column(String, default="main")
    files_changed: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String, default="READY_FOR_REVIEW")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    risk_before: Mapped[int] = mapped_column(Integer, default=0)
    risk_after: Mapped[int] = mapped_column(Integer, default=0)
    vulnerability_fixed: Mapped[str] = mapped_column(String, default="")
    ai_explanation: Mapped[str] = mapped_column(Text, default="")

    patch: Mapped["Patch"] = relationship(back_populates="pull_requests")
