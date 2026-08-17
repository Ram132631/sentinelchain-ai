from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit import AuditLog
from app.schemas.serializers import audit_log_to_dict

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("")
def list_audit_logs(repository_id: str | None = None, limit: int = 200, db: Session = Depends(get_db)):
    q = db.query(AuditLog)
    if repository_id:
        q = q.filter(AuditLog.repository_id == repository_id)
    logs = q.order_by(AuditLog.timestamp.desc()).limit(min(limit, 500)).all()
    return [audit_log_to_dict(a) for a in logs]
