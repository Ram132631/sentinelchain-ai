from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.vulnerability import Vulnerability
from app.schemas.serializers import vulnerability_to_dict
from app.services.explain import explain_vulnerability_danger

router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])


@router.get("")
def list_vulnerabilities(severity: str | None = None, reachable: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(Vulnerability)
    if severity:
        q = q.filter(Vulnerability.severity == severity.upper())
    vulns = q.order_by(Vulnerability.risk_score.desc()).all()
    results = [vulnerability_to_dict(v) for v in vulns]
    if reachable is not None:
        results = [r for r in results if r["reachability"] and r["reachability"]["is_reachable"] == reachable]
    return results


@router.get("/{vuln_id}")
def get_vulnerability(vuln_id: str, db: Session = Depends(get_db)):
    v = db.get(Vulnerability, vuln_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    data = vulnerability_to_dict(v)
    data["ai_danger_explanation"] = explain_vulnerability_danger({
        "cve_id": v.cve_id, "ghsa_id": v.ghsa_id, "severity": v.severity, "cvss_score": v.cvss_score,
        "component": v.package_name, "summary": v.summary,
    })
    data["patches"] = [
        {"id": p.id, "target_version": p.target_version, "status": p.status, "security_approval": p.security_approval}
        for p in v.patches
    ]
    return data
