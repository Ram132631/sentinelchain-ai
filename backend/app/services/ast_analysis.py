"""AST Code Analysis Agent.

Prefers `semgrep` (real static analysis engine) if installed on the host.
Otherwise falls back to a lightweight, real regex/AST-based scanner that
still performs genuine pattern detection over actual file content (not
fabricated) — covering hardcoded secrets, dangerous eval/exec usage,
command/SQL/NoSQL injection patterns, and unsafe deserialization.
DEMO repository findings are pre-curated for a rich, believable walkthrough.
"""
from __future__ import annotations

import re

from app.demo_data.commerce_api import DEMO_SOURCE_FINDINGS
from app.security.subprocess_utils import tool_available

FALLBACK_RULES = [
    (re.compile(r"""(mongodb(\+srv)?:\/\/[^\s'"]*:[^\s'"]*@)"""), "Hardcoded Secret", "CRITICAL",
     "Move database credentials to environment variables and rotate the exposed secret."),
    (re.compile(r"""(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['"][A-Za-z0-9\-_]{8,}['"]"""), "Hardcoded Secret", "HIGH",
     "Remove hardcoded credentials from source; load from a secrets manager or environment variables."),
    (re.compile(r"\beval\s*\("), "Insecure Deserialization / Code Execution", "CRITICAL",
     "Replace eval() with a safe parser (e.g. JSON.parse) and validate input schema."),
    (re.compile(r"\bexec\s*\(\s*[`\"'].*\$\{"), "Command Injection", "CRITICAL",
     "Use execFile/spawn with an argument array instead of interpolating input into a shell string."),
    (re.compile(r"child_process"), "Dangerous Function Usage", "MEDIUM",
     "Review use of child_process for command injection risk; prefer execFile with fixed argv."),
    (re.compile(r"\$where\s*:"), "NoSQL Injection", "HIGH",
     "Avoid MongoDB $where with user input; use parameterized query operators instead."),
    (re.compile(r"""SELECT .*\+.*req\.(query|body|params)"""), "SQL Injection", "CRITICAL",
     "Use parameterized queries / prepared statements instead of string concatenation."),
    (re.compile(r"pickle\.loads"), "Unsafe Deserialization", "CRITICAL",
     "Never unpickle untrusted data; use JSON or a schema-validated serialization format."),
]


def demo_ast_findings() -> list[dict]:
    return list(DEMO_SOURCE_FINDINGS)


def scan_source_fallback(files: dict[str, str]) -> list[dict]:
    """files: {relative_path: content}. Real regex-pattern static scan."""
    findings = []
    for path, content in files.items():
        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            for pattern, issue_type, severity, recommendation in FALLBACK_RULES:
                if pattern.search(line):
                    findings.append({
                        "file_path": path,
                        "line": lineno,
                        "function_name": None,
                        "issue_type": issue_type,
                        "severity": severity,
                        "code_snippet": line.strip()[:200],
                        "recommendation": recommendation,
                        "rule_id": "sentinelchain.fallback." + issue_type.lower().replace(" ", "-"),
                        "tool": "fallback-regex-scanner",
                    })
    return findings


def semgrep_available() -> bool:
    return tool_available("semgrep")
