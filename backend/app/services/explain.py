"""AI Explainability layer.

Uses Anthropic Claude for natural-language reasoning when ANTHROPIC_API_KEY
is configured AND the `anthropic` package is installed. Otherwise falls back
to deterministic, template-based explanations built from the same structured
risk/reachability data — so the platform's core explainability promise holds
even with zero external credentials.
"""
from __future__ import annotations

from app.config import get_settings

_client = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    settings = get_settings()
    if not settings.anthropic_configured:
        return None
    try:
        import anthropic  # type: ignore
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except Exception:
        _client = None
    return _client


def ask_claude(prompt: str, max_tokens: int = 400) -> str | None:
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in resp.content if hasattr(block, "text")).strip()
    except Exception:
        return None


def explain_vulnerability_danger(vuln) -> str:
    prompt = (
        f"In 2-3 sentences, explain why vulnerability {vuln.get('cve_id') or vuln.get('ghsa_id')} "
        f"({vuln.get('severity')}, CVSS {vuln.get('cvss_score')}) in package {vuln.get('component')} is dangerous: "
        f"{vuln.get('summary')}"
    )
    ai_answer = ask_claude(prompt)
    if ai_answer:
        return ai_answer
    return (
        f"{vuln.get('severity')} severity ({'CVSS ' + str(vuln.get('cvss_score'))}): {vuln.get('summary')} "
        f"An attacker who can reach the vulnerable function in {vuln.get('component')} could exploit this to "
        f"compromise confidentiality, integrity, or availability of the application, particularly if the "
        f"package sits on a production request path."
    )


def explain_patch_safety(package: str, current: str, target: str, breaking_reason: str, tests_passed: bool) -> str:
    prompt = (
        f"In 2 sentences, explain why upgrading {package} from {current} to {target} is a safe security patch. "
        f"Context: {breaking_reason} Tests passed: {tests_passed}."
    )
    ai_answer = ask_claude(prompt)
    if ai_answer:
        return ai_answer
    return (
        f"{package} was upgraded from {current} to {target} because {target} contains the vendor security fix. "
        f"{breaking_reason} " + ("All QA and regression checks passed for this change." if tests_passed else "Some QA checks require follow-up before merge.")
    )
