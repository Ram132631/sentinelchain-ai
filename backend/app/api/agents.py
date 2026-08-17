from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.agent import AgentExecution, ScanRun
from app.models.base import AGENT_NAMES
from app.schemas.serializers import agent_execution_to_dict, scan_run_to_dict

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
def list_agent_definitions():
    return [{"name": n, "order": i + 1} for i, n in enumerate(AGENT_NAMES)]


@router.get("/executions")
def list_executions(scan_run_id: str | None = None, repository_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(AgentExecution)
    if scan_run_id:
        q = q.filter(AgentExecution.scan_run_id == scan_run_id)
    if repository_id:
        q = q.filter(AgentExecution.repository_id == repository_id)
    executions = q.order_by(AgentExecution.step_order.asc()).all()
    return [agent_execution_to_dict(e) for e in executions]


@router.get("/scan-runs/{scan_run_id}")
def get_scan_run(scan_run_id: str, db: Session = Depends(get_db)):
    run = db.get(ScanRun, scan_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scan run not found")
    return scan_run_to_dict(run)


@router.get("/{execution_id}")
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    ex = db.get(AgentExecution, execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Agent execution not found")
    return agent_execution_to_dict(ex)
