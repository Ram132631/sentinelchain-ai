from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import resume_after_approvals
from app.database.session import get_db
from app.models.audit import Approval, AuditLog
from app.models.patch import Patch, TestResult
from app.schemas.serializers import patch_to_dict
from app.testing.qa_runner import QAContext, run_qa_suite

router = APIRouter(prefix="/api/patches", tags=["patches"])


@router.get("")
def list_patches(repository_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Patch)
    if repository_id:
        q = q.filter(Patch.repository_id == repository_id)
    patches = q.order_by(Patch.created_at.desc()).all()
    return [patch_to_dict(p) for p in patches]


@router.get("/{patch_id}")
def get_patch(patch_id: str, db: Session = Depends(get_db)):
    p = db.get(Patch, patch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patch not found")
    return patch_to_dict(p)


@router.post("/{patch_id}/test")
def rerun_patch_tests(patch_id: str, db: Session = Depends(get_db)):
    p = db.get(Patch, patch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patch not found")
    db.query(TestResult).filter(TestResult.patch_id == p.id).delete()
    ctx = QAContext(
        package_name=p.component_name, current_version=p.current_version, target_version=p.target_version,
        fixed_version=p.target_version, breaking_change_risk=p.breaking_change_risk,
        dependency_count_before=p.repository.total_dependencies, dependency_count_after=p.repository.total_dependencies,
    )
    for result_dict in run_qa_suite(ctx):
        db.add(TestResult(patch_id=p.id, **result_dict))
    p.status = "TESTED"
    db.commit()
    db.refresh(p)
    return patch_to_dict(p)


@router.post("/{patch_id}/approve")
def approve_patch(patch_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    p = db.get(Patch, patch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patch not found")
    p.security_approval = "APPROVED"
    p.status = "APPROVED"
    approval = db.query(Approval).filter(Approval.patch_id == p.id).first()
    scan_run_id = None
    if approval:
        approval.decision = "APPROVED"
        approval.decided_at = datetime.now(timezone.utc)
        approval.decided_by = "security-lead"
        from app.models.agent import ScanRun
        latest = db.query(ScanRun).filter(ScanRun.repository_id == p.repository_id).order_by(ScanRun.started_at.desc()).first()
        scan_run_id = latest.id if latest else None
    db.add(AuditLog(repository_id=p.repository_id, agent_name="Human Reviewer", action=f"Approved patch for {p.component_name}",
                     status="COMPLETED", user_approval=True, severity="INFO"))
    db.commit()
    if scan_run_id:
        background_tasks.add_task(resume_after_approvals, scan_run_id)
    db.refresh(p)
    return patch_to_dict(p)


@router.post("/{patch_id}/reject")
def reject_patch(patch_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    p = db.get(Patch, patch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patch not found")
    p.security_approval = "REJECTED"
    p.status = "REJECTED"
    approval = db.query(Approval).filter(Approval.patch_id == p.id).first()
    scan_run_id = None
    if approval:
        approval.decision = "REJECTED"
        approval.decided_at = datetime.now(timezone.utc)
        approval.decided_by = "security-lead"
        from app.models.agent import ScanRun
        latest = db.query(ScanRun).filter(ScanRun.repository_id == p.repository_id).order_by(ScanRun.started_at.desc()).first()
        scan_run_id = latest.id if latest else None
    db.add(AuditLog(repository_id=p.repository_id, agent_name="Human Reviewer", action=f"Rejected patch for {p.component_name}",
                     status="REJECTED", user_approval=False, severity="WARNING"))
    db.commit()
    if scan_run_id:
        background_tasks.add_task(resume_after_approvals, scan_run_id)
    db.refresh(p)
    return patch_to_dict(p)
