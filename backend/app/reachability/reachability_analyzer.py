"""Reachability Analysis Agent.

For the DEMO repository, reachability is backed by a curated, explicit
call-path dataset (see demo_data/commerce_api.py) so the UI can show a real
CVE -> vulnerable function -> import -> endpoint -> user input chain.

For a REAL repository, a lightweight heuristic static analyzer inspects
fetched source files (via GitHub API, read-only, sandboxed) using Python's
built-in `ast` module for .py files and regex-based import/route detection
for JS/TS, looking for: (a) an import of the vulnerable package, and
(b) that import occurring in a file that also defines an HTTP route/handler
(Flask/FastAPI/Express-style decorators or app.get/post/etc). This is a
best-effort heuristic, not a full taint-tracking engine — it is labeled as
such in the output.
"""
from __future__ import annotations

import ast
import re

ROUTE_PATTERNS = [
    re.compile(r"app\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"router\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"@(app|router)\.(get|post|put|delete|patch)\("),
]


def analyze_demo(vuln_spec: dict) -> dict:
    return {
        "is_reachable": bool(vuln_spec.get("reachable")),
        "confidence": 92 if vuln_spec.get("reachable") else 85,
        "entry_point": vuln_spec.get("entry_point"),
        "vulnerable_function": vuln_spec.get("vulnerable_function"),
        "call_path": vuln_spec.get("call_path", []),
        "explanation": vuln_spec.get("reach_explanation", ""),
        "analysis_method": "curated-demo-call-graph",
    }


def analyze_heuristic(package_name: str, source_files: dict[str, str]) -> dict:
    """source_files: {relative_path: file_content}. Best-effort static heuristic."""
    import_hits: list[str] = []
    route_files: set[str] = set()

    for path, content in source_files.items():
        if _imports_package(path, content, package_name):
            import_hits.append(path)
        if any(p.search(content) for p in ROUTE_PATTERNS):
            route_files.add(path)

    reachable_files = [f for f in import_hits if f in route_files]
    if reachable_files:
        return {
            "is_reachable": True,
            "confidence": 62,
            "entry_point": reachable_files[0],
            "vulnerable_function": f"{package_name} (imported)",
            "call_path": [f"HTTP route handler in {reachable_files[0]}", f"imports '{package_name}'"],
            "explanation": (
                f"Heuristic static analysis found that '{package_name}' is imported directly inside a "
                f"file that also defines an HTTP route handler ({reachable_files[0]}), indicating a "
                f"plausible path from an exposed endpoint to the vulnerable package."
            ),
            "analysis_method": "heuristic-import-route-correlation",
        }
    if import_hits:
        return {
            "is_reachable": False,
            "confidence": 55,
            "entry_point": None,
            "vulnerable_function": f"{package_name} (imported)",
            "call_path": [f"Imported in {import_hits[0]}", "No HTTP route handler detected in the same file"],
            "explanation": (
                f"'{package_name}' is imported in {len(import_hits)} file(s), but none of them define an "
                f"HTTP route handler in this lightweight heuristic scan, so no direct reachability path "
                f"from external input was identified."
            ),
            "analysis_method": "heuristic-import-route-correlation",
        }
    return {
        "is_reachable": False,
        "confidence": 40,
        "entry_point": None,
        "vulnerable_function": None,
        "call_path": [],
        "explanation": (
            f"No import of '{package_name}' was found in the sampled source files. Reachability cannot be "
            f"confirmed positively; treated as not reachable with low-moderate confidence."
        ),
        "analysis_method": "heuristic-import-route-correlation",
    }


def _imports_package(path: str, content: str, package_name: str) -> bool:
    if path.endswith(".py"):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return package_name in content
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name.split(".")[0] == package_name for alias in node.names):
                    return True
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] == package_name:
                    return True
        return False
    if path.endswith((".js", ".ts", ".jsx", ".tsx")):
        pattern = re.compile(rf"""(require\(['"]{re.escape(package_name)}['"]\)|from\s+['"]{re.escape(package_name)}['"])""")
        return bool(pattern.search(content))
    return False
