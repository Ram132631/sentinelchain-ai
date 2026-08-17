from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import resume_after_approvals
from app.database.session import get_db
from app.models.agent import ScanRun
from app.models.audit import Approval, AuditLog
from app.models.patch import Patch
from app.schemas.requests import ApprovalDecisionRequest
from app.schemas.serializers import approval_to_dict

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("")
def list_approvals(repository_id: str | None = None, decision: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Approval)
    if repository_id:
        q = q.filter(Approval.repository_id == repository_id)
    if decision:
        q = q.filter(Approval.decision == decision.upper())
    approvals = q.order_by(Approval.requested_at.desc()).all()
    return [approval_to_dict(a) for a in approvals]


@router.get("/pending")
def list_pending_approvals(db: Session = Depends(get_db)):
    approvals = db.query(Approval).filter(Approval.decision == "PENDING").order_by(Approval.requested_at.asc()).all()
    return [approval_to_dict(a) for a in approvals]


@router.get("/{approval_id}")
def get_approval(approval_id: str, db: Session = Depends(get_db)):
    a = db.get(Approval, approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval_to_dict(a)


@router.post("/{approval_id}/decide")
def decide_approval(approval_id: str, payload: ApprovalDecisionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.decision != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval already decided: {approval.decision}")

    approval.decision = payload.decision
    approval.reasoning = payload.reasoning or ""
    approval.decided_by = payload.decided_by
    approval.decided_at = datetime.now(timezone.utc)

    patch = db.get(Patch, approval.patch_id) if approval.patch_id else None
    if patch:
        if payload.decision == "APPROVED":
            patch.security_approval = "APPROVED"
            patch.status = "APPROVED"
        elif payload.decision == "REJECTED":
            patch.security_approval = "REJECTED"
            patch.status = "REJECTED"

    db.add(AuditLog(
        repository_id=approval.repository_id, agent_name="Human Reviewer",
        action=f"Human {payload.decision.lower()} change for {approval.component_name}",
        input_data=approval.proposed_change, output_data=payload.reasoning or "",
        status="COMPLETED", user_approval=(payload.decision == "APPROVED"),
        severity="INFO" if payload.decision == "APPROVED" else "WARNING",
    ))
    db.commit()

    latest_run = db.query(ScanRun).filter(ScanRun.repository_id == approval.repository_id).order_by(ScanRun.started_at.desc()).first()
    if latest_run and latest_run.status == "WAITING_FOR_APPROVAL":
        background_tasks.add_task(resume_after_approvals, latest_run.id)

    db.refresh(approval)
    return approval_to_dict(approval)
