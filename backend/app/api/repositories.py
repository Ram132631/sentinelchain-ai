from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_pipeline
from app.database.session import get_db
from app.demo_data.commerce_api import DEMO_REPO
from app.models.agent import ScanRun
from app.models.code_analysis import ASTFinding, LicenseFinding
from app.models.repository import Repository
from app.models.sbom import DependencyRelationship, SBOMComponent
from app.models.vulnerability import Vulnerability
from app.schemas.requests import RepositoryCreate
from app.schemas.serializers import (
    ast_finding_to_dict, component_to_dict, license_finding_to_dict, repository_to_dict,
    scan_run_to_dict, vulnerability_to_dict,
)
from app.security.validation import ValidationError, validate_github_url

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("")
def list_repositories(db: Session = Depends(get_db)):
    repos = db.query(Repository).order_by(Repository.created_at.desc()).all()
    return [repository_to_dict(r) for r in repos]


@router.post("", status_code=201)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    try:
        owner, name = validate_github_url(payload.url)
        full_name = f"{owner}/{name}"
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = db.query(Repository).filter(Repository.full_name == full_name).first()
    if existing:
        return repository_to_dict(existing)

    repo = Repository(name=payload.name or name, full_name=full_name, url=payload.url, status="UNSCANNED")
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repository_to_dict(repo)


@router.post("/demo-seed")
def ensure_demo_repository(db: Session = Depends(get_db)):
    """Idempotently ensures the built-in demo-commerce-api repository exists."""
    existing = db.query(Repository).filter(Repository.full_name == DEMO_REPO["full_name"]).first()
    if existing:
        return repository_to_dict(existing)
    repo = Repository(
        name=DEMO_REPO["name"], full_name=DEMO_REPO["full_name"], url=DEMO_REPO["url"],
        description=DEMO_REPO["description"], is_demo=True, status="UNSCANNED",
        primary_language=DEMO_REPO["primary_language"], languages=DEMO_REPO["languages"],
        frameworks=DEMO_REPO["frameworks"], package_managers=DEMO_REPO["package_managers"],
        dependency_files=DEMO_REPO["dependency_files"], file_count=DEMO_REPO["file_count"],
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repository_to_dict(repo)


@router.get("/{repo_id}")
def get_repository(repo_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository_to_dict(repo)


@router.delete("/{repo_id}", status_code=204)
def delete_repository(repo_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    db.delete(repo)
    db.commit()
    return None


@router.post("/{repo_id}/scan")
def trigger_scan(repo_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    active = db.query(ScanRun).filter(ScanRun.repository_id == repo_id, ScanRun.status.in_(["RUNNING", "WAITING_FOR_APPROVAL"])).first()
    if active:
        return scan_run_to_dict(active)

    scan_run = ScanRun(repository_id=repo.id, status="RUNNING", is_demo=repo.is_demo, started_at=datetime.now(timezone.utc))
    repo.status = "SCANNING"
    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)

    background_tasks.add_task(run_pipeline, repo.id, scan_run.id)
    return scan_run_to_dict(scan_run)


@router.get("/{repo_id}/scan-runs")
def list_scan_runs(repo_id: str, db: Session = Depends(get_db)):
    runs = db.query(ScanRun).filter(ScanRun.repository_id == repo_id).order_by(ScanRun.started_at.desc()).all()
    return [scan_run_to_dict(r) for r in runs]


@router.get("/{repo_id}/scan-runs/latest")
def latest_scan_run(repo_id: str, db: Session = Depends(get_db)):
    run = db.query(ScanRun).filter(ScanRun.repository_id == repo_id).order_by(ScanRun.started_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No scan runs yet")
    return scan_run_to_dict(run)


@router.get("/{repo_id}/sbom")
def get_sbom(repo_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    components = db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo_id).all()
    return {"repository": repository_to_dict(repo), "components": [component_to_dict(c) for c in components]}


@router.get("/{repo_id}/sbom/cyclonedx")
def get_sbom_cyclonedx(repo_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    components = db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo_id).all()
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {"type": "application", "name": repo.name, "version": "scanned"},
            "tools": [{"vendor": "SentinelChain AI", "name": "SBOM Agent", "version": "1.0.0"}],
        },
        "components": [
            {
                "type": "library", "bom-ref": c.purl or f"{c.name}@{c.version}", "name": c.name, "version": c.version,
                "purl": c.purl, "licenses": [{"license": {"id": c.license}}] if c.license != "Unknown" else [],
                "scope": "required" if c.is_direct else "optional",
            } for c in components
        ],
    }


@router.get("/{repo_id}/dependencies")
def get_dependencies(repo_id: str, db: Session = Depends(get_db)):
    components = db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo_id).all()
    return [component_to_dict(c) for c in components]


@router.get("/{repo_id}/dependency-graph")
def get_dependency_graph(repo_id: str, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    components = db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo_id).all()
    relationships = db.query(DependencyRelationship).filter(DependencyRelationship.repository_id == repo_id).all()
    vulns = db.query(Vulnerability).filter(Vulnerability.repository_id == repo_id).all()
    vulns_by_component: dict[str, list[dict]] = {}
    for v in vulns:
        vulns_by_component.setdefault(v.component_id, []).append(vulnerability_to_dict(v))

    nodes = [{
        "id": "root", "type": "application", "name": repo.name, "version": "app",
    }]
    for c in components:
        nodes.append({
            "id": c.id, "type": "package", "name": c.name, "version": c.version, "ecosystem": c.ecosystem,
            "is_direct": c.is_direct, "is_vulnerable": c.is_vulnerable, "is_reachable": c.is_reachable,
            "is_suspicious": c.is_suspicious, "risk_score": c.risk_score, "license": c.license,
            "vulnerabilities": vulns_by_component.get(c.id, []),
        })
    edges = [{"source": "root", "target": c.id} for c in components if c.is_direct]
    edges += [{"source": r.parent_id, "target": r.child_id} for r in relationships if r.parent_id]
    return {"nodes": nodes, "edges": edges}


@router.get("/{repo_id}/ast-findings")
def get_ast_findings(repo_id: str, db: Session = Depends(get_db)):
    findings = db.query(ASTFinding).filter(ASTFinding.repository_id == repo_id).all()
    return [ast_finding_to_dict(f) for f in findings]


@router.get("/{repo_id}/license-findings")
def get_license_findings(repo_id: str, db: Session = Depends(get_db)):
    findings = db.query(LicenseFinding).filter(LicenseFinding.repository_id == repo_id).all()
    return [license_finding_to_dict(f) for f in findings]


@router.get("/{repo_id}/vulnerabilities")
def get_repo_vulnerabilities(repo_id: str, db: Session = Depends(get_db)):
    vulns = db.query(Vulnerability).filter(Vulnerability.repository_id == repo_id).order_by(Vulnerability.risk_score.desc()).all()
    return [vulnerability_to_dict(v) for v in vulns]
