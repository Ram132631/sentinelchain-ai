"""Lightweight, explicit serializers from SQLAlchemy models to JSON-safe dicts.

Chosen over full nested Pydantic ORM models for hackathon velocity — request
bodies still use Pydantic (see api/*.py) for validation, but response shaping
is done here to keep control over exactly what's exposed to the frontend
(and to keep the risk_score/explanation fields consistently named for the UI).
"""
from __future__ import annotations

from datetime import datetime


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def repository_to_dict(r) -> dict:
    return {
        "id": r.id, "name": r.name, "full_name": r.full_name, "url": r.url, "description": r.description,
        "is_demo": r.is_demo, "primary_language": r.primary_language, "languages": r.languages,
        "frameworks": r.frameworks, "package_managers": r.package_managers, "dependency_files": r.dependency_files,
        "file_count": r.file_count, "default_branch": r.default_branch, "status": r.status,
        "health_score": r.health_score, "risk_score": r.risk_score, "risk_score_before": r.risk_score_before,
        "total_dependencies": r.total_dependencies, "direct_dependencies": r.direct_dependencies,
        "transitive_dependencies": r.transitive_dependencies, "critical_count": r.critical_count,
        "high_count": r.high_count, "medium_count": r.medium_count, "low_count": r.low_count,
        "reachable_count": r.reachable_count, "last_scan_at": _iso(r.last_scan_at), "created_at": _iso(r.created_at),
    }


def component_to_dict(c) -> dict:
    return {
        "id": c.id, "repository_id": c.repository_id, "name": c.name, "version": c.version, "ecosystem": c.ecosystem,
        "purl": c.purl, "license": c.license, "is_direct": c.is_direct, "depth": c.depth,
        "latest_version": c.latest_version, "is_outdated": c.is_outdated, "is_suspicious": c.is_suspicious,
        "suspicious_reason": c.suspicious_reason, "is_vulnerable": c.is_vulnerable, "is_reachable": c.is_reachable,
        "risk_score": c.risk_score, "source_tool": c.source_tool,
    }


def vulnerability_to_dict(v, include_reachability: bool = True) -> dict:
    out = {
        "id": v.id, "repository_id": v.repository_id, "component_id": v.component_id,
        "cve_id": v.cve_id, "ghsa_id": v.ghsa_id, "package_name": v.package_name,
        "installed_version": v.installed_version, "fixed_version": v.fixed_version, "affected_range": v.affected_range,
        "severity": v.severity, "cvss_score": v.cvss_score, "summary": v.summary, "description": v.description,
        "published_date": _iso(v.published_date), "references": v.references, "exploit_available": v.exploit_available,
        "is_production_dependency": v.is_production_dependency, "risk_score": v.risk_score,
        "risk_explanation": v.risk_explanation, "status": v.status, "source": v.source,
        "repository_name": v.repository.name if v.repository else None,
    }
    if include_reachability and v.reachability:
        out["reachability"] = reachability_to_dict(v.reachability)
    else:
        out["reachability"] = None
    return out


def reachability_to_dict(r) -> dict:
    return {
        "id": r.id, "vulnerability_id": r.vulnerability_id, "is_reachable": r.is_reachable,
        "confidence": r.confidence, "entry_point": r.entry_point, "vulnerable_function": r.vulnerable_function,
        "call_path": r.call_path, "explanation": r.explanation, "analysis_method": r.analysis_method,
    }


def ast_finding_to_dict(f) -> dict:
    return {
        "id": f.id, "repository_id": f.repository_id, "file_path": f.file_path, "line": f.line,
        "function_name": f.function_name, "issue_type": f.issue_type, "severity": f.severity,
        "code_snippet": f.code_snippet, "recommendation": f.recommendation, "rule_id": f.rule_id, "tool": f.tool,
    }


def license_finding_to_dict(f) -> dict:
    return {
        "id": f.id, "repository_id": f.repository_id, "component_id": f.component_id,
        "component_name": f.component_name, "license": f.license, "classification": f.classification,
        "policy_violation": f.policy_violation, "explanation": f.explanation,
    }


def patch_to_dict(p) -> dict:
    return {
        "id": p.id, "repository_id": p.repository_id, "vulnerability_id": p.vulnerability_id,
        "component_name": p.component_name, "current_version": p.current_version, "target_version": p.target_version,
        "dependency_file": p.dependency_file, "diff_text": p.diff_text, "explanation": p.explanation,
        "breaking_change_risk": p.breaking_change_risk, "breaking_change_reason": p.breaking_change_reason,
        "risk_before": p.risk_before, "risk_after": p.risk_after, "status": p.status,
        "security_approval": p.security_approval, "auditor_notes": p.auditor_notes,
        "test_results": [test_result_to_dict(t) for t in p.test_results],
        "pull_requests": [pull_request_to_dict(pr) for pr in p.pull_requests],
        "vulnerability": {"cve_id": p.vulnerability.cve_id, "ghsa_id": p.vulnerability.ghsa_id, "severity": p.vulnerability.severity} if p.vulnerability else None,
        "created_at": _iso(p.created_at),
    }


def test_result_to_dict(t) -> dict:
    return {
        "id": t.id, "patch_id": t.patch_id, "test_type": t.test_type, "status": t.status,
        "summary": t.summary, "details": t.details, "simulated": t.simulated, "duration_ms": t.duration_ms,
    }


def pull_request_to_dict(pr) -> dict:
    return {
        "id": pr.id, "repository_id": pr.repository_id, "patch_id": pr.patch_id, "pr_number": pr.pr_number,
        "title": pr.title, "description": pr.description, "branch_name": pr.branch_name, "base_branch": pr.base_branch,
        "files_changed": pr.files_changed, "status": pr.status, "is_demo": pr.is_demo, "url": pr.url,
        "risk_before": pr.risk_before, "risk_after": pr.risk_after, "vulnerability_fixed": pr.vulnerability_fixed,
        "ai_explanation": pr.ai_explanation, "created_at": _iso(pr.created_at),
    }


def agent_execution_to_dict(e) -> dict:
    return {
        "id": e.id, "scan_run_id": e.scan_run_id, "repository_id": e.repository_id, "agent_name": e.agent_name,
        "step_order": e.step_order, "status": e.status, "current_task": e.current_task,
        "started_at": _iso(e.started_at), "completed_at": _iso(e.completed_at), "duration_ms": e.duration_ms,
        "tools_used": e.tools_used, "input_summary": e.input_summary, "output_summary": e.output_summary,
        "reasoning": e.reasoning, "confidence": e.confidence, "error_message": e.error_message,
    }


def scan_run_to_dict(s, include_executions: bool = True) -> dict:
    out = {
        "id": s.id, "repository_id": s.repository_id, "status": s.status, "is_demo": s.is_demo,
        "started_at": _iso(s.started_at), "completed_at": _iso(s.completed_at),
        "security_score_before": s.security_score_before, "security_score_after": s.security_score_after,
        "critical_before": s.critical_before, "critical_after": s.critical_after,
        "high_before": s.high_before, "high_after": s.high_after,
        "reachable_before": s.reachable_before, "reachable_after": s.reachable_after,
        "current_step": s.current_step, "error_message": s.error_message,
    }
    if include_executions:
        out["executions"] = [agent_execution_to_dict(e) for e in sorted(s.executions, key=lambda e: e.step_order)]
    return out


def audit_log_to_dict(a) -> dict:
    return {
        "id": a.id, "timestamp": _iso(a.timestamp), "repository_id": a.repository_id, "scan_run_id": a.scan_run_id,
        "agent_name": a.agent_name, "action": a.action, "input_data": a.input_data, "output_data": a.output_data,
        "status": a.status, "user_approval": a.user_approval, "severity": a.severity,
    }


def approval_to_dict(a) -> dict:
    return {
        "id": a.id, "repository_id": a.repository_id, "patch_id": a.patch_id, "vulnerability_id": a.vulnerability_id,
        "requested_at": _iso(a.requested_at), "decided_at": _iso(a.decided_at), "decision": a.decision,
        "risk_level": a.risk_level, "component_name": a.component_name, "proposed_change": a.proposed_change,
        "ai_reasoning": a.ai_reasoning, "reasoning": a.reasoning, "decided_by": a.decided_by,
    }
