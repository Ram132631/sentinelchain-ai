from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit import SecurityReport
from app.models.repository import Repository

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{repository_id}")
def get_latest_report(repository_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    report = (
        db.query(SecurityReport)
        .filter(SecurityReport.repository_id == repository_id)
        .order_by(SecurityReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No security report generated yet. Run a scan first.")
    return {"id": report.id, "generated_at": report.generated_at.isoformat(), **report.content}


@router.get("/{repository_id}/history")
def get_report_history(repository_id: str, db: Session = Depends(get_db)):
    reports = (
        db.query(SecurityReport)
        .filter(SecurityReport.repository_id == repository_id)
        .order_by(SecurityReport.generated_at.desc())
        .all()
    )
    return [{"id": r.id, "generated_at": r.generated_at.isoformat(), "executive_summary": r.executive_summary,
             "score_before": r.content.get("score_before"), "score_after": r.content.get("score_after")} for r in reports]
