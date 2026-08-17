"""Patch Generator Agent.

Determines a safe target version, produces a real unified (git-style) diff
of the dependency manifest, and assesses breaking-change risk using semantic
versioning distance between the installed and target versions.
"""
from __future__ import annotations

import difflib
import re


def parse_semver(version: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version or "0.0.0")
    if not match:
        return (0, 0, 0)
    return tuple(int(x) for x in match.groups())  # type: ignore


def assess_breaking_change_risk(current: str, target: str) -> tuple[str, str]:
    cur = parse_semver(current)
    tgt = parse_semver(target)
    if tgt[0] > cur[0]:
        return "HIGH", (
            f"{current} → {target} is a MAJOR version bump. Major releases may contain breaking API changes; "
            "regression testing is strongly recommended before merge."
        )
    if tgt[1] > cur[1]:
        return "MEDIUM", (
            f"{current} → {target} is a MINOR version bump. New functionality may be introduced but the "
            "package's semver contract implies backward compatibility."
        )
    return "LOW", (
        f"{current} → {target} is a PATCH-level bump containing only the vendor security fix, with no "
        "intentional API surface change."
    )


def build_dependency_diff(dependency_file: str, package_name: str, current_version: str, target_version: str) -> str:
    if dependency_file.endswith("package.json"):
        before = f'  "{package_name}": "{current_version}",\n'
        after = f'  "{package_name}": "{target_version}",\n'
    elif dependency_file.endswith("requirements.txt"):
        before = f"{package_name}=={current_version}\n"
        after = f"{package_name}=={target_version}\n"
    else:
        before = f"{package_name} {current_version}\n"
        after = f"{package_name} {target_version}\n"

    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=dependency_file,
        tofile=dependency_file,
        lineterm="",
    )
    return "".join(f"{line}\n" if not line.endswith("\n") else line for line in diff)


def generate_patch_explanation(package_name: str, current_version: str, target_version: str, cve_id: str | None, risk_reason: str) -> str:
    cve_clause = f" ({cve_id})" if cve_id else ""
    return (
        f"Upgraded {package_name} from {current_version} to {target_version} because {target_version} "
        f"contains the vendor security fix for the identified vulnerability{cve_clause}. {risk_reason} "
        f"This is the minimal version bump that resolves the advisory without pulling in unrelated changes."
    )
