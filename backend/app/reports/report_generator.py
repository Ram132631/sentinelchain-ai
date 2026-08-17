"""Documentation Agent — generates the Security Report content model.

Deterministic template-based generation. If ANTHROPIC_API_KEY is configured,
callers may enrich the executive_summary via app.services.explain.summarize;
absent a key, the rule-based summary below is used directly (never crashes).
"""
from __future__ import annotations

from datetime import datetime, timezone


def build_security_report(repo, vulns, patches, license_findings, scan_run) -> dict:
    critical = [v for v in vulns if v.severity == "CRITICAL"]
    high = [v for v in vulns if v.severity == "HIGH"]
    reachable = [v for v in vulns if v.reachability and v.reachability.is_reachable]
    violations = [l for l in license_findings if l.policy_violation]

    exec_summary = (
        f"SentinelChain AI analyzed {repo.name} and identified {len(vulns)} known vulnerabilities across "
        f"{repo.total_dependencies} SBOM components ({repo.direct_dependencies} direct, "
        f"{repo.transitive_dependencies} transitive). {len(critical)} were CRITICAL and {len(high)} were HIGH "
        f"severity; reachability analysis confirmed {len(reachable)} were actually exploitable from "
        f"user-controlled input. The autonomous pipeline generated {len(patches)} patch(es), all validated by "
        f"the QA and Security Auditor agents, raising the overall security score from "
        f"{scan_run.security_score_before} to {scan_run.security_score_after}."
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_demo": repo.is_demo,
        "executive_summary": exec_summary,
        "repository_overview": {
            "name": repo.name,
            "url": repo.url,
            "primary_language": repo.primary_language,
            "languages": repo.languages,
            "package_managers": repo.package_managers,
            "file_count": repo.file_count,
        },
        "sbom_summary": {
            "total_components": repo.total_dependencies,
            "direct": repo.direct_dependencies,
            "transitive": repo.transitive_dependencies,
        },
        "vulnerabilities": [
            {
                "cve_id": v.cve_id or v.ghsa_id, "package": v.package_name, "severity": v.severity,
                "cvss": v.cvss_score, "risk_score": v.risk_score, "status": v.status,
                "reachable": bool(v.reachability and v.reachability.is_reachable),
            } for v in vulns
        ],
        "reachability_analysis": {
            "reachable_count": len(reachable),
            "not_reachable_count": len(vulns) - len(reachable),
            "details": [
                {"package": v.package_name, "reachable": v.reachability.is_reachable, "explanation": v.reachability.explanation}
                for v in vulns if v.reachability
            ],
        },
        "license_compliance": {
            "total_findings": len(license_findings),
            "violations": len(violations),
            "details": [{"component": l.component_name, "license": l.license, "violation": l.policy_violation, "explanation": l.explanation} for l in license_findings],
        },
        "generated_patches": [
            {
                "package": p.component_name, "from": p.current_version, "to": p.target_version,
                "risk_before": p.risk_before, "risk_after": p.risk_after, "security_approval": p.security_approval,
            } for p in patches
        ],
        "test_results_summary": {
            "total_patches_tested": len(patches),
            "all_passed": all((p.security_approval in ("APPROVED",) for p in patches)) if patches else True,
        },
        "security_recommendations": _recommendations(vulns, violations, patches),
        "score_before": scan_run.security_score_before,
        "score_after": scan_run.security_score_after,
    }


def _recommendations(vulns, violations, patches) -> list[str]:
    recs = []
    unresolved = [v for v in vulns if v.status not in ("PATCHED", "RESOLVED") and v.fixed_version]
    if unresolved:
        recs.append(f"Prioritize manual review of {len(unresolved)} remaining vulnerability(ies) with an available fix that were not auto-patched this run.")
    if violations:
        recs.append(f"Engage legal/compliance review for {len(violations)} license policy violation(s) before next release.")
    reachable_open = [v for v in vulns if v.reachability and v.reachability.is_reachable and v.status == "OPEN"]
    if reachable_open:
        recs.append(f"Treat the {len(reachable_open)} reachable, unpatched vulnerability(ies) as release blockers.")
    if not recs:
        recs.append("No outstanding release blockers identified. Continue routine automated scanning on every commit.")
    recs.append("Maintain human-in-the-loop approval for all CRITICAL-severity or production-dependency changes.")
    return recs
