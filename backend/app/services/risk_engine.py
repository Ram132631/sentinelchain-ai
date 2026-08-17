"""Deterministic, explainable risk-scoring engine.

The platform intentionally does NOT rank vulnerabilities by CVSS alone. Each
vulnerability's practical risk score blends six signals, and every score is
paired with a plain-English explanation so a human reviewer can see exactly
why a number was produced.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskInputs:
    cvss_score: float          # 0-10
    exploit_available: bool
    reachable: bool | None      # None = unknown/not yet analyzed
    is_production_dependency: bool
    is_direct: bool
    fix_available: bool


def compute_vulnerability_risk(inputs: RiskInputs) -> tuple[int, str]:
    """Returns (risk_score 0-100, human-readable explanation)."""

    cvss_component = (inputs.cvss_score / 10.0) * 40  # up to 40 pts
    exploit_component = 15 if inputs.exploit_available else 3
    if inputs.reachable is True:
        reach_component = 25
    elif inputs.reachable is False:
        reach_component = 2
    else:
        reach_component = 12  # unknown, treat as moderate caution

    importance_component = 10 if inputs.is_direct else 5
    if not inputs.is_production_dependency:
        importance_component = max(2, importance_component - 6)

    exposure_component = 8 if inputs.is_production_dependency and inputs.reachable else 3
    patch_component = 2 if inputs.fix_available else 8  # unpatched CVEs carry more residual risk

    raw = cvss_component + exploit_component + reach_component + importance_component + exposure_component + patch_component
    score = max(0, min(100, round(raw)))

    reasons = []
    reasons.append(f"CVSS base score is {inputs.cvss_score}.")
    if inputs.reachable is True:
        reasons.append("the vulnerable function is directly reachable from user/attacker-controlled input")
    elif inputs.reachable is False:
        reasons.append("static reachability analysis found no path from any exposed entry point to the vulnerable function, substantially lowering practical risk")
    else:
        reasons.append("reachability has not yet been analyzed for this finding")
    if inputs.exploit_available:
        reasons.append("a public exploit or proof-of-concept is known to exist")
    if inputs.is_direct and inputs.is_production_dependency:
        reasons.append("the affected package is a direct, production dependency")
    elif not inputs.is_direct:
        reasons.append("the affected package is a transitive (indirect) dependency")
    if not inputs.fix_available:
        reasons.append("no fixed version is currently published, so remediation requires a mitigating control")

    explanation = (
        f"Although this dependency has a CVSS score of {inputs.cvss_score}, "
        + ", and ".join(reasons[1:]) + f". Combining these factors, the practical risk score is {score}/100."
    )
    return score, explanation


def risk_band(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"


def compute_repository_security_score(vuln_risk_scores: list[int], reachable_critical_high: int) -> int:
    """Aggregate posture score (0-100, HIGHER is better/safer)."""
    if not vuln_risk_scores:
        return 96
    top = sorted(vuln_risk_scores, reverse=True)[:8]
    avg_top = sum(top) / len(top)
    penalty = avg_top * 0.78 + reachable_critical_high * 4
    score = max(3, min(100, round(100 - penalty)))
    return score
