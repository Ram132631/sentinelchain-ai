from __future__ import annotations

from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    url: str = Field(..., description="https://github.com/<owner>/<repo>")
    name: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED|NEEDS_REVIEW)$")
    reasoning: str | None = None
    decided_by: str = "security-lead"


class PullRequestCreateRequest(BaseModel):
    patch_id: str
