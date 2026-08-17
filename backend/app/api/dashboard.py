from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.agent import ScanRun
from app.models.patch import Patch
from app.models.repository import Repository
from app.models.sbom import SBOMComponent
from app.models.vulnerability import Vulnerability

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    repos = db.query(Repository).all()
    vulns = db.query(Vulnerability).all()
    components = db.query(SBOMComponent).all()
    patches = db.query(Patch).all()

    # "Current" outstanding risk excludes vulnerabilities already resolved by an approved patch —
    # this is what should visibly shrink as the autonomous pipeline remediates issues.
    open_vulns = [v for v in vulns if v.status not in ("PATCHED", "RESOLVED")]

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for v in open_vulns:
        severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

    reachable = sum(1 for v in open_vulns if v.reachability and v.reachability.is_reachable)
    patchable = sum(1 for v in open_vulns if v.fixed_version)

    ecosystem_counts: dict[str, int] = {}
    for c in components:
        ecosystem_counts[c.ecosystem] = ecosystem_counts.get(c.ecosystem, 0) + 1

    by_repo = []
    for r in repos:
        repo_vulns = [v for v in open_vulns if v.repository_id == r.id]
        by_repo.append({
            "repository": r.name,
            "critical": sum(1 for v in repo_vulns if v.severity == "CRITICAL"),
            "high": sum(1 for v in repo_vulns if v.severity == "HIGH"),
            "medium": sum(1 for v in repo_vulns if v.severity == "MEDIUM"),
            "low": sum(1 for v in repo_vulns if v.severity == "LOW"),
            "risk_score": r.risk_score,
        })

    tested_patches = [p for p in patches if p.status in ("APPROVED", "TESTED", "REJECTED", "NEEDS_REVIEW")]
    success_rate = round(100 * sum(1 for p in patches if p.security_approval == "APPROVED") / len(patches), 1) if patches else 0.0

    scan_runs = db.query(ScanRun).filter(ScanRun.status == "COMPLETED").order_by(ScanRun.completed_at.asc()).all()
    risk_trend = [
        {"date": (s.completed_at or s.started_at).strftime("%Y-%m-%d %H:%M"), "score_before": s.security_score_before, "score_after": s.security_score_after}
        for s in scan_runs
    ]

    return {
        "repositories_scanned": sum(1 for r in repos if r.status == "SCANNED"),
        "total_repositories": len(repos),
        "total_dependencies": sum(r.total_dependencies for r in repos),
        "critical_vulnerabilities": severity_counts["CRITICAL"],
        "high_vulnerabilities": severity_counts["HIGH"],
        "reachable_vulnerabilities": reachable,
        "patches_available": patchable,
        "patches_generated": len(patches),
        "average_risk_score": round(sum(r.risk_score for r in repos) / len(repos), 1) if repos else 0,
        "severity_distribution": severity_counts,
        "ecosystem_distribution": ecosystem_counts,
        "vulnerabilities_by_repository": by_repo,
        "patch_success_rate": success_rate,
        "risk_trend": risk_trend,
    }
