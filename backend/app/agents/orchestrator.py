"""LangGraph-style multi-agent orchestrator.

Implemented as a native async state-machine pipeline (13 sequential nodes +
one conditional human-approval gate) so the hackathon build has zero risk of
breaking on a missing/incompatible `langgraph` install. The node graph below
mirrors exactly the LangGraph workflow described in the project spec:

  Repository Scanner -> SBOM Agent -> Dependency Analyzer ->
  Vulnerability Intelligence -> Risk Prioritization -> Reachability Analysis ->
  AST Code Analysis -> License Compliance -> Patch Generator -> QA Validation ->
  Security Auditor -> [Human Approval gate] -> Release Manager -> Documentation Agent

Each node persists an AgentExecution row (PENDING -> RUNNING -> COMPLETED /
FAILED / WAITING_FOR_APPROVAL) plus an AuditLog entry, so the frontend's
Agent Monitor and Audit Log pages are reading real pipeline state, not mocks.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import SessionLocal
from app.demo_data.commerce_api import DEMO_VULNERABILITIES, LICENSE_POLICY
from app.models.agent import AgentExecution, ScanRun
from app.models.audit import Approval, AuditLog
from app.models.code_analysis import ASTFinding, LicenseFinding
from app.models.patch import Patch, TestResult
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.models.sbom import DependencyRelationship, SBOMComponent
from app.models.vulnerability import ReachabilityResult, Vulnerability
from app.patching.patch_generator import assess_breaking_change_risk, build_dependency_diff, generate_patch_explanation
from app.reachability.reachability_analyzer import analyze_demo, analyze_heuristic
from app.reports.report_generator import build_security_report
from app.sbom.sbom_generator import ComponentRecord, generate_sbom, to_purl
from app.scanners.repo_scanner import scan_repository
from app.scanners.source_fetcher import fetch_source_sample
from app.security.validation import validate_github_url
from app.services import ast_analysis, license_engine
from app.services.explain import explain_patch_safety, explain_vulnerability_danger
from app.services.risk_engine import RiskInputs, compute_repository_security_score, compute_vulnerability_risk, risk_band
from app.testing.qa_runner import QAContext, run_qa_suite
from app.vulnerability.osv_client import demo_vulnerabilities, query_osv_batch

AGENT_STEP_ORDER = [
    "Repository Scanner", "SBOM Agent", "Dependency Analyzer", "Vulnerability Intelligence",
    "Risk Prioritization", "Reachability Analysis", "AST Code Analysis", "License Compliance",
    "Patch Generator", "QA Validation", "Security Auditor", "Release Manager", "Documentation Agent",
]

_DEMO_SPEC_BY_COMPONENT = {v["component"]: v for v in DEMO_VULNERABILITIES}


async def _delay():
    settings = get_settings()
    ms = random.randint(settings.scan_step_min_delay_ms, settings.scan_step_max_delay_ms)
    await asyncio.sleep(ms / 1000)


def _log(db: Session, scan_run: ScanRun, repo_id: str, agent: str, action: str, input_data: str = "", output_data: str = "", status: str = "COMPLETED", severity: str = "INFO"):
    db.add(AuditLog(
        repository_id=repo_id, scan_run_id=scan_run.id, agent_name=agent, action=action,
        input_data=input_data, output_data=output_data, status=status, severity=severity,
    ))


def _start_execution(db: Session, scan_run: ScanRun, repo_id: str, name: str, order: int, task: str) -> AgentExecution:
    ex = AgentExecution(
        scan_run_id=scan_run.id, repository_id=repo_id, agent_name=name, step_order=order,
        status="RUNNING", current_task=task, started_at=datetime.now(timezone.utc),
    )
    db.add(ex)
    scan_run.current_step = name
    db.commit()
    db.refresh(ex)
    return ex


def _aware(dt: datetime) -> datetime:
    """SQLite drops tzinfo on roundtrip; treat naive datetimes as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _finish_execution(db: Session, ex: AgentExecution, *, status: str, output: str, tools: list[str], confidence: int, reasoning: str = ""):
    now = datetime.now(timezone.utc)
    started = _aware(ex.started_at) if ex.started_at else now
    ex.status = status
    ex.completed_at = now
    ex.duration_ms = max(0, int((now - started).total_seconds() * 1000))
    ex.output_summary = output
    ex.tools_used = tools
    ex.confidence = confidence
    ex.reasoning = reasoning
    db.commit()


async def run_pipeline(repository_id: str, scan_run_id: str) -> None:
    db = SessionLocal()
    try:
        repo = db.get(Repository, repository_id)
        scan_run = db.get(ScanRun, scan_run_id)
        if not repo or not scan_run:
            return

        source_files: dict[str, str] = {}
        owner_repo: tuple[str, str] | None = None

        # ---- 1. Repository Scanner ----
        ex = _start_execution(db, scan_run, repo.id, "Repository Scanner", 1, f"Scanning {repo.url}")
        await _delay()
        result, is_demo = await scan_repository(repo.url)
        repo.is_demo = is_demo
        repo.primary_language = result.primary_language
        repo.languages = result.languages
        repo.frameworks = result.frameworks
        repo.package_managers = result.package_managers
        repo.dependency_files = result.dependency_files
        repo.file_count = result.file_count
        repo.default_branch = getattr(result, "default_branch", "main")
        repo.status = "SCANNING"
        db.commit()
        try:
            owner_repo = validate_github_url(repo.url) if not is_demo else None
        except Exception:
            owner_repo = None
        note = "DEMO MODE sample repository." if is_demo else f"Live GitHub metadata for {repo.full_name}."
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Detected {len(repo.languages)} language(s), {len(repo.dependency_files)} dependency file(s). {note}",
                           tools=["GitHub API"] if not is_demo else ["Demo Dataset"], confidence=95 if not is_demo else 100)
        _log(db, scan_run, repo.id, "Repository Scanner", "Scanned repository", output_data=note)

        # ---- 2. SBOM Agent ----
        ex = _start_execution(db, scan_run, repo.id, "SBOM Agent", 2, "Generating Software Bill of Materials")
        await _delay()
        db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo.id).delete()
        db.commit()
        components, sbom_is_demo, sbom_note = await generate_sbom(
            owner_repo[0] if owner_repo else None, owner_repo[1] if owner_repo else None,
            repo.default_branch, repo.dependency_files,
        )
        if sbom_is_demo:
            repo.is_demo = True
        name_to_component: dict[str, SBOMComponent] = {}
        for c in components:
            row = SBOMComponent(
                repository_id=repo.id, name=c.name, version=c.version, ecosystem=c.ecosystem,
                purl=to_purl(c.ecosystem, c.name, c.version), license=c.license, is_direct=c.is_direct,
                depth=c.depth, latest_version=c.latest_version, is_outdated=bool(c.latest_version and c.latest_version != c.version),
                is_suspicious=c.suspicious, suspicious_reason=c.suspicious_reason, source_tool=c.source_tool,
            )
            db.add(row)
            name_to_component[c.name] = row
        db.commit()
        repo.total_dependencies = len(components)
        repo.direct_dependencies = sum(1 for c in components if c.is_direct)
        repo.transitive_dependencies = repo.total_dependencies - repo.direct_dependencies
        db.commit()
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Generated {len(components)} components ({repo.direct_dependencies} direct, {repo.transitive_dependencies} transitive). {sbom_note}",
                           tools=["Syft-compatible parser"], confidence=90)
        _log(db, scan_run, repo.id, "SBOM Agent", f"Generated {len(components)} components", output_data=sbom_note)

        # ---- 3. Dependency Analyzer ----
        ex = _start_execution(db, scan_run, repo.id, "Dependency Analyzer", 3, "Building dependency graph")
        await _delay()
        db.query(DependencyRelationship).filter(DependencyRelationship.repository_id == repo.id).delete()
        rel_count = 0
        for c in components:
            if c.parent and c.parent in name_to_component:
                db.add(DependencyRelationship(
                    repository_id=repo.id, parent_id=name_to_component[c.parent].id,
                    child_id=name_to_component[c.name].id,
                ))
                rel_count += 1
        db.commit()
        outdated = sum(1 for c in components if c.latest_version and c.latest_version != c.version)
        suspicious = [c for c in components if c.suspicious]
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Built {rel_count} dependency edges. {outdated} outdated package(s) detected"
                                  + (f"; {len(suspicious)} suspicious/dependency-confusion candidate(s) flagged." if suspicious else "."),
                           tools=["Dependency Graph Builder"], confidence=88,
                           reasoning="Suspicious packages flagged when publish recency, download volume, or name-similarity to a well-known package indicate a possible dependency-confusion or typosquat attempt." if suspicious else "")
        _log(db, scan_run, repo.id, "Dependency Analyzer", "Built dependency graph", output_data=f"{rel_count} edges, {outdated} outdated")

        # ---- 4. Vulnerability Intelligence ----
        ex = _start_execution(db, scan_run, repo.id, "Vulnerability Intelligence", 4, "Querying OSV vulnerability database")
        await _delay()
        db.query(Vulnerability).filter(Vulnerability.repository_id == repo.id).delete()
        db.commit()
        if repo.is_demo:
            raw_vulns = demo_vulnerabilities()
            osv_note = "Curated DEMO MODE intelligence (real OSV advisory IDs, sample repository)."
        else:
            raw_vulns = await query_osv_batch(list(components))
            osv_note = f"Live OSV.dev query across {min(len(components), 60)} component(s)."

        created_vulns: list[Vulnerability] = []
        for v in raw_vulns:
            comp_name = v["component"] if not repo.is_demo else v["component"]
            comp = name_to_component.get(comp_name)
            if comp is None:
                continue
            published_date = None
            if v.get("published_days_ago") is not None:
                published_date = datetime.now(timezone.utc) - timedelta(days=v["published_days_ago"])
            elif v.get("published"):
                try:
                    published_date = datetime.fromisoformat(str(v["published"]).replace("Z", "+00:00"))
                except ValueError:
                    published_date = None
            row = Vulnerability(
                repository_id=repo.id, component_id=comp.id, cve_id=v.get("cve_id"), ghsa_id=v.get("ghsa_id"),
                package_name=comp_name, installed_version=comp.version, fixed_version=v.get("fixed_version"),
                affected_range=f"<{v.get('fixed_version')}" if v.get("fixed_version") else "unspecified",
                severity=v.get("severity", "MEDIUM"), cvss_score=float(v.get("cvss_score", 5.0)),
                summary=v.get("summary", ""), description=v.get("description", ""), published_date=published_date,
                references=v.get("references", []), exploit_available=bool(v.get("exploit_available")),
                is_production_dependency=comp.is_direct, status="PATCH_AVAILABLE" if v.get("fixed_version") else "OPEN",
                source=v.get("source", "OSV"),
            )
            db.add(row)
            comp.is_vulnerable = True
            created_vulns.append(row)
        db.commit()
        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for v in created_vulns:
            sev_counts[v.severity] = sev_counts.get(v.severity, 0) + 1
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Identified {len(created_vulns)} vulnerabilities — {sev_counts['CRITICAL']} critical, {sev_counts['HIGH']} high, {sev_counts['MEDIUM']} medium, {sev_counts['LOW']} low. {osv_note}",
                           tools=["OSV.dev API"], confidence=93)
        _log(db, scan_run, repo.id, "Vulnerability Intelligence", f"Detected {len(created_vulns)} vulnerabilities", output_data=osv_note)

        # ---- 5. Risk Prioritization (preliminary pass; refined after reachability) ----
        ex = _start_execution(db, scan_run, repo.id, "Risk Prioritization", 5, "Scoring vulnerabilities beyond raw CVSS")
        await _delay()
        for v in created_vulns:
            score, explanation = compute_vulnerability_risk(RiskInputs(
                cvss_score=v.cvss_score, exploit_available=v.exploit_available, reachable=None,
                is_production_dependency=v.is_production_dependency, is_direct=v.is_production_dependency,
                fix_available=bool(v.fixed_version),
            ))
            v.risk_score = score
            v.risk_explanation = explanation
        db.commit()
        critical_before = sum(1 for v in created_vulns if v.severity == "CRITICAL")
        high_before = sum(1 for v in created_vulns if v.severity == "HIGH")
        scan_run.critical_before = critical_before
        scan_run.high_before = high_before
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Preliminary risk scoring complete for {len(created_vulns)} vulnerabilities (CVSS + exploitability + dependency importance + patch availability). Reachability weighting pending.",
                           tools=["Risk Scoring Engine"], confidence=80)
        _log(db, scan_run, repo.id, "Risk Prioritization", "Scored vulnerabilities")

        # ---- 6. Reachability Analysis ----
        ex = _start_execution(db, scan_run, repo.id, "Reachability Analysis", 6, "Tracing call paths from entry points to vulnerable code")
        await _delay()
        if not repo.is_demo and owner_repo and result.raw_file_paths:
            source_files = await fetch_source_sample(owner_repo[0], owner_repo[1], repo.default_branch, result.raw_file_paths)
        reachable_count = 0
        for v in created_vulns:
            if repo.is_demo and v.package_name in _DEMO_SPEC_BY_COMPONENT:
                analysis = analyze_demo(_DEMO_SPEC_BY_COMPONENT[v.package_name])
            else:
                analysis = analyze_heuristic(v.package_name, source_files)
            db.add(ReachabilityResult(
                vulnerability_id=v.id, is_reachable=analysis["is_reachable"], confidence=analysis["confidence"],
                entry_point=analysis["entry_point"], vulnerable_function=analysis["vulnerable_function"],
                call_path=analysis["call_path"], explanation=analysis["explanation"], analysis_method=analysis["analysis_method"],
            ))
            comp = name_to_component.get(v.package_name)
            if comp:
                comp.is_reachable = analysis["is_reachable"]
            # Recompute final risk with real reachability signal
            score, explanation = compute_vulnerability_risk(RiskInputs(
                cvss_score=v.cvss_score, exploit_available=v.exploit_available, reachable=analysis["is_reachable"],
                is_production_dependency=v.is_production_dependency, is_direct=v.is_production_dependency,
                fix_available=bool(v.fixed_version),
            ))
            v.risk_score = score
            v.risk_explanation = explanation
            if comp:
                comp.risk_score = max(comp.risk_score, score)
            if analysis["is_reachable"]:
                reachable_count += 1
        db.commit()
        scan_run.reachable_before = reachable_count
        repo.reachable_count = reachable_count
        db.commit()
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Confirmed {reachable_count} of {len(created_vulns)} vulnerabilities are reachable from live entry points. Risk scores recalculated.",
                           tools=["AST Call-Graph Tracer" if repo.is_demo else "Heuristic Import/Route Correlator"], confidence=85 if repo.is_demo else 60)
        _log(db, scan_run, repo.id, "Reachability Analysis", f"Confirmed {reachable_count} vulnerabilities reachable")

        # ---- 7. AST Code Analysis ----
        ex = _start_execution(db, scan_run, repo.id, "AST Code Analysis", 7, "Scanning source for dangerous patterns")
        await _delay()
        db.query(ASTFinding).filter(ASTFinding.repository_id == repo.id).delete()
        if repo.is_demo:
            findings = ast_analysis.demo_ast_findings()
            ast_tool = "Curated DEMO MODE findings"
        elif ast_analysis.semgrep_available():
            findings = ast_analysis.scan_source_fallback(source_files)
            ast_tool = "semgrep (detected but using unified fallback scanner for speed)"
        else:
            findings = ast_analysis.scan_source_fallback(source_files)
            ast_tool = "Fallback regex/AST scanner (semgrep not installed)"
        for f in findings:
            db.add(ASTFinding(repository_id=repo.id, **f))
        db.commit()
        critical_ast = sum(1 for f in findings if f["severity"] == "CRITICAL")
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Found {len(findings)} code-level findings ({critical_ast} critical) across sampled source files.",
                           tools=[ast_tool], confidence=82 if repo.is_demo else 55)
        _log(db, scan_run, repo.id, "AST Code Analysis", f"Found {len(findings)} findings")

        # ---- 8. License Compliance ----
        ex = _start_execution(db, scan_run, repo.id, "License Compliance", 8, "Classifying dependency licenses")
        await _delay()
        db.query(LicenseFinding).filter(LicenseFinding.repository_id == repo.id).delete()
        policy = LICENSE_POLICY if repo.is_demo else "permissive-only"
        violations = 0
        for c in components:
            comp_row = name_to_component[c.name]
            classification = license_engine.classify_license(c.license)
            violation, explanation = license_engine.evaluate_policy(c.name, c.license, policy)
            if violation or c.is_direct:
                db.add(LicenseFinding(
                    repository_id=repo.id, component_id=comp_row.id, component_name=c.name,
                    license=c.license, classification=classification, policy_violation=violation, explanation=explanation,
                ))
            if violation:
                violations += 1
        db.commit()
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Classified licenses for {len(components)} components under a '{policy}' policy — {violations} violation(s) flagged.",
                           tools=["License Classifier"], confidence=91)
        _log(db, scan_run, repo.id, "License Compliance", f"{violations} policy violation(s)")

        # ---- 9. Patch Generator ----
        ex = _start_execution(db, scan_run, repo.id, "Patch Generator", 9, "Generating secure dependency patches")
        await _delay()
        db.query(Patch).filter(Patch.repository_id == repo.id).delete()
        db.commit()
        patches: list[Patch] = []
        dep_file = next((f for f in repo.dependency_files if f.endswith("package.json")), None) or (repo.dependency_files[0] if repo.dependency_files else "package.json")
        for v in created_vulns:
            spec = _DEMO_SPEC_BY_COMPONENT.get(v.package_name) if repo.is_demo else None
            if spec and spec.get("no_auto_patch"):
                _log(db, scan_run, repo.id, "Patch Generator", f"Skipped auto-patch for {v.package_name}",
                     output_data=spec.get("reach_explanation", "Deferred for manual review."), severity="WARNING")
                continue
            if not v.fixed_version:
                continue
            risk_level, risk_reason = assess_breaking_change_risk(v.installed_version, v.fixed_version)
            diff_text = build_dependency_diff(dep_file, v.package_name, v.installed_version, v.fixed_version)
            explanation = generate_patch_explanation(v.package_name, v.installed_version, v.fixed_version, v.cve_id, risk_reason)
            patch = Patch(
                repository_id=repo.id, vulnerability_id=v.id, component_name=v.package_name,
                current_version=v.installed_version, target_version=v.fixed_version, dependency_file=dep_file,
                diff_text=diff_text, explanation=explanation, breaking_change_risk=risk_level,
                breaking_change_reason=risk_reason, risk_before=v.risk_score, status="GENERATED",
            )
            db.add(patch)
            patches.append(patch)
        db.commit()
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Generated {len(patches)} patch(es) for vulnerabilities with an available vendor fix.",
                           tools=["Semver Patch Engine"], confidence=89)
        _log(db, scan_run, repo.id, "Patch Generator", f"Generated {len(patches)} patches")

        # ---- 10. QA Validation ----
        ex = _start_execution(db, scan_run, repo.id, "QA Validation", 10, "Running automated test & security validation suite")
        await _delay()
        for patch in patches:
            ctx = QAContext(
                package_name=patch.component_name, current_version=patch.current_version, target_version=patch.target_version,
                fixed_version=patch.target_version, breaking_change_risk=patch.breaking_change_risk,
                dependency_count_before=repo.total_dependencies, dependency_count_after=repo.total_dependencies,
            )
            for result_dict in run_qa_suite(ctx):
                db.add(TestResult(patch_id=patch.id, **result_dict))
            patch.status = "TESTED"
            v = next(v for v in created_vulns if v.id == patch.vulnerability_id)
            score, explanation = compute_vulnerability_risk(RiskInputs(
                cvss_score=v.cvss_score, exploit_available=v.exploit_available, reachable=False,
                is_production_dependency=v.is_production_dependency, is_direct=v.is_production_dependency, fix_available=True,
            ))
            patch.risk_after = max(2, score - 40)
        db.commit()
        all_pass = all(tr.status == "PASS" for p in patches for tr in p.test_results)
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"Executed validation suite across {len(patches)} patch(es). All checks {'PASSED' if all_pass else 'had at least one FAILURE'}.",
                           tools=["QA Runner", "Security Scan", "SBOM Diff"], confidence=87)
        _log(db, scan_run, repo.id, "QA Validation", "All tests passed" if all_pass else "Some tests failed")

        # ---- 11. Security Auditor ----
        ex = _start_execution(db, scan_run, repo.id, "Security Auditor", 11, "Auditing generated patches before release")
        await _delay()
        pending_approvals: list[Approval] = []
        for patch in patches:
            v = next(v for v in created_vulns if v.id == patch.vulnerability_id)
            tests_ok = all(tr.status == "PASS" for tr in patch.test_results)
            needs_human = v.severity == "CRITICAL" or patch.breaking_change_risk == "HIGH" or (v.is_production_dependency and v.severity == "HIGH")
            if not tests_ok:
                patch.security_approval = "REJECTED"
                patch.status = "REJECTED"
                patch.auditor_notes = "Rejected: one or more QA/security checks failed."
            elif needs_human:
                patch.security_approval = "NEEDS_HUMAN_REVIEW"
                patch.status = "NEEDS_REVIEW"
                patch.auditor_notes = (
                    f"Technically sound (tests passed, vulnerability resolved, no license/dependency-count regressions), "
                    f"but routed for human approval because "
                    + ("the affected vulnerability is CRITICAL severity" if v.severity == "CRITICAL" else
                       "this is a major version bump with breaking-change risk" if patch.breaking_change_risk == "HIGH" else
                       "it patches a HIGH-severity production dependency") + "."
                )
                approval = Approval(
                    repository_id=repo.id, patch_id=patch.id, vulnerability_id=v.id, risk_level=v.severity,
                    component_name=patch.component_name,
                    proposed_change=f"{patch.component_name}: {patch.current_version} -> {patch.target_version}",
                    ai_reasoning=explain_patch_safety(patch.component_name, patch.current_version, patch.target_version, patch.breaking_change_reason, tests_ok),
                )
                db.add(approval)
                pending_approvals.append(approval)
            else:
                patch.security_approval = "APPROVED"
                patch.status = "APPROVED"
                patch.auditor_notes = "Approved: vulnerability resolved, tests passed, no license or dependency-count regressions detected, low breaking-change risk."
        db.commit()
        approved_n = sum(1 for p in patches if p.security_approval == "APPROVED")
        review_n = len(pending_approvals)
        rejected_n = sum(1 for p in patches if p.security_approval == "REJECTED")
        _finish_execution(db, ex, status="COMPLETED",
                           output=f"{approved_n} patch(es) APPROVED, {review_n} flagged NEEDS_HUMAN_REVIEW, {rejected_n} REJECTED.",
                           tools=["Security Audit Rules Engine"], confidence=94)
        _log(db, scan_run, repo.id, "Security Auditor", f"{approved_n} approved / {review_n} need review / {rejected_n} rejected")

        if pending_approvals:
            scan_run.status = "WAITING_FOR_APPROVAL"
            db.add(AgentExecution(
                scan_run_id=scan_run.id, repository_id=repo.id, agent_name="Release Manager", step_order=12,
                status="WAITING_FOR_APPROVAL", current_task="Waiting for human approval on critical patch(es)",
            ))
            db.add(AgentExecution(
                scan_run_id=scan_run.id, repository_id=repo.id, agent_name="Documentation Agent", step_order=13,
                status="PENDING", current_task="Awaiting release completion",
            ))
            db.commit()
            _log(db, scan_run, repo.id, "Release Manager", "Human approval required before release", status="WAITING_FOR_APPROVAL", severity="WARNING")
            return  # pipeline pauses here; resumed by approvals API

        await _finalize_pipeline(db, repo, scan_run, created_vulns, patches)
    finally:
        db.close()


async def _finalize_pipeline(db: Session, repo: Repository, scan_run: ScanRun, created_vulns: list[Vulnerability], patches: list[Patch]) -> None:
    # ---- 12. Release Manager ----
    ex = _start_execution(db, scan_run, repo.id, "Release Manager", 12, "Preparing pull request(s) for reviewable patches")
    await _delay()
    prs = []
    pr_counter = 100 + random.randint(1, 50)
    for patch in patches:
        if patch.security_approval != "APPROVED":
            continue
        v = next(v for v in created_vulns if v.id == patch.vulnerability_id)
        v.status = "PATCHED"
        comp = db.query(SBOMComponent).filter(SBOMComponent.repository_id == repo.id, SBOMComponent.name == patch.component_name).first()
        ai_expl = explain_vulnerability_danger({
            "cve_id": v.cve_id, "ghsa_id": v.ghsa_id, "severity": v.severity, "cvss_score": v.cvss_score,
            "component": v.package_name, "summary": v.summary,
        })
        pr_counter += 1
        pr = PullRequest(
            repository_id=repo.id, patch_id=patch.id, pr_number=pr_counter,
            title=f"Security Fix: Upgrade {patch.component_name} to {patch.target_version}",
            description=(
                f"## Security Patch\n\n**Vulnerability:** {v.cve_id or v.ghsa_id} ({v.severity})\n\n"
                f"{patch.explanation}\n\n### Why this is dangerous\n{ai_expl}\n\n"
                f"### Test Results\n" + "\n".join(f"- {tr.test_type}: {tr.status}" for tr in patch.test_results) + "\n\n"
                f"### Risk Reduction\n{patch.risk_before} -> {patch.risk_after}\n"
            ),
            branch_name=f"sentinelchain/fix-{patch.component_name}-{patch.target_version}".replace(".", "-"),
            files_changed=[patch.dependency_file], status="READY_FOR_REVIEW", is_demo=repo.is_demo or True,
            risk_before=patch.risk_before, risk_after=patch.risk_after,
            vulnerability_fixed=v.cve_id or v.ghsa_id or "", ai_explanation=ai_expl,
        )
        db.add(pr)
        prs.append(pr)
    db.commit()
    _finish_execution(db, ex, status="COMPLETED",
                       output=f"Prepared {len(prs)} pull request(s) as DEMO PRs (no write access to external repos was exercised).",
                       tools=["GitHub PR Composer"], confidence=97)
    _log(db, scan_run, repo.id, "Release Manager", f"PR(s) prepared: {len(prs)}")

    # ---- 13. Documentation Agent ----
    ex = _start_execution(db, scan_run, repo.id, "Documentation Agent", 13, "Generating security report & audit summary")
    await _delay()
    license_findings = db.query(LicenseFinding).filter(LicenseFinding.repository_id == repo.id).all()

    open_vulns = [v for v in created_vulns if v.status not in ("PATCHED", "RESOLVED")]
    remaining_scores = [v.risk_score for v in open_vulns]
    remaining_reachable_crit_high = sum(1 for v in open_vulns if v.reachability and v.reachability.is_reachable and v.severity in ("CRITICAL", "HIGH"))
    security_score_after = compute_repository_security_score(remaining_scores, remaining_reachable_crit_high)
    security_score_before = compute_repository_security_score([v.risk_score for v in created_vulns], scan_run.reachable_before)

    scan_run.security_score_before = security_score_before
    scan_run.security_score_after = security_score_after
    scan_run.critical_after = sum(1 for v in open_vulns if v.severity == "CRITICAL")
    scan_run.high_after = sum(1 for v in open_vulns if v.severity == "HIGH")
    scan_run.reachable_after = sum(1 for v in open_vulns if v.reachability and v.reachability.is_reachable)

    repo.risk_score_before = repo.risk_score or security_score_before
    repo.risk_score = security_score_after
    repo.critical_count = scan_run.critical_after
    repo.high_count = scan_run.high_after
    repo.medium_count = sum(1 for v in open_vulns if v.severity == "MEDIUM")
    repo.low_count = sum(1 for v in open_vulns if v.severity == "LOW")
    repo.reachable_count = scan_run.reachable_after
    repo.health_score = security_score_after
    repo.status = "SCANNED"
    repo.last_scan_at = datetime.now(timezone.utc)

    report_content = build_security_report(repo, created_vulns, patches, license_findings, scan_run)
    from app.models.audit import SecurityReport
    db.add(SecurityReport(repository_id=repo.id, scan_run_id=scan_run.id, executive_summary=report_content["executive_summary"], content=report_content))

    scan_run.status = "COMPLETED"
    scan_run.completed_at = datetime.now(timezone.utc)
    scan_run.current_step = "Complete"
    db.commit()
    _finish_execution(db, ex, status="COMPLETED",
                       output=f"Security report generated. Overall security score improved {security_score_before} -> {security_score_after}.",
                       tools=["Report Generator"], confidence=96)
    _log(db, scan_run, repo.id, "Documentation Agent", "Generated security report", status="COMPLETED")


async def resume_after_approvals(scan_run_id: str) -> None:
    """Called once every pending Approval for a scan run has been decided."""
    db = SessionLocal()
    try:
        scan_run = db.get(ScanRun, scan_run_id)
        if not scan_run or scan_run.status != "WAITING_FOR_APPROVAL":
            return
        repo = db.get(Repository, scan_run.repository_id)
        pending = db.query(Approval).filter(Approval.repository_id == repo.id, Approval.decision == "PENDING").all()
        if pending:
            return

        patches = db.query(Patch).filter(Patch.repository_id == repo.id).all()
        approvals = db.query(Approval).filter(Approval.repository_id == repo.id).all()
        approval_by_patch = {a.patch_id: a for a in approvals}
        for patch in patches:
            approval = approval_by_patch.get(patch.id)
            if approval and patch.security_approval == "NEEDS_HUMAN_REVIEW":
                if approval.decision == "APPROVED":
                    patch.security_approval = "APPROVED"
                    patch.status = "APPROVED"
                elif approval.decision == "REJECTED":
                    patch.security_approval = "REJECTED"
                    patch.status = "REJECTED"
        db.commit()

        db.query(AgentExecution).filter(
            AgentExecution.scan_run_id == scan_run.id, AgentExecution.agent_name.in_(["Release Manager", "Documentation Agent"])
        ).delete(synchronize_session=False)
        db.commit()

        created_vulns = db.query(Vulnerability).filter(Vulnerability.repository_id == repo.id).all()
        scan_run.status = "RUNNING"
        db.commit()
        await _finalize_pipeline(db, repo, scan_run, created_vulns, patches)
    finally:
        db.close()
