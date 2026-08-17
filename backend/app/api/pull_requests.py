from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.patch import Patch
from app.models.pull_request import PullRequest
from app.schemas.requests import PullRequestCreateRequest
from app.schemas.serializers import pull_request_to_dict

router = APIRouter(prefix="/api/pull-requests", tags=["pull-requests"])


@router.get("")
def list_pull_requests(repository_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PullRequest)
    if repository_id:
        q = q.filter(PullRequest.repository_id == repository_id)
    prs = q.order_by(PullRequest.created_at.desc()).all()
    return [pull_request_to_dict(pr) for pr in prs]


@router.get("/{pr_id}")
def get_pull_request(pr_id: str, db: Session = Depends(get_db)):
    pr = db.get(PullRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return pull_request_to_dict(pr)


@router.post("", status_code=201)
def create_pull_request(payload: PullRequestCreateRequest, db: Session = Depends(get_db)):
    """Manually prepare a DEMO pull request for an already-approved patch
    (the autonomous Release Manager agent normally does this automatically).
    Never opens a real PR against an external repository — GitHub write
    access is intentionally out of scope for this hackathon build; see
    README 'Security Considerations'.
    """
    patch = db.get(Patch, payload.patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    if patch.security_approval != "APPROVED":
        raise HTTPException(status_code=400, detail="Patch must be APPROVED before a pull request can be prepared")

    existing = db.query(PullRequest).filter(PullRequest.patch_id == patch.id).first()
    if existing:
        return pull_request_to_dict(existing)

    pr = PullRequest(
        repository_id=patch.repository_id, patch_id=patch.id, pr_number=0,
        title=f"Security Fix: Upgrade {patch.component_name} to {patch.target_version}",
        description=patch.explanation, branch_name=f"sentinelchain/fix-{patch.component_name}".replace(".", "-"),
        files_changed=[patch.dependency_file], status="READY_FOR_REVIEW", is_demo=True,
        risk_before=patch.risk_before, risk_after=patch.risk_after,
        vulnerability_fixed=patch.vulnerability.cve_id or patch.vulnerability.ghsa_id if patch.vulnerability else "",
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pull_request_to_dict(pr)
