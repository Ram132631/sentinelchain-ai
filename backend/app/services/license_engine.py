from __future__ import annotations

PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense", "CC0-1.0"}
WEAK_COPYLEFT = {"LGPL-2.1", "LGPL-3.0", "MPL-2.0", "EPL-2.0"}
COPYLEFT = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "AGPL-1.0"}


def classify_license(license_id: str) -> str:
    if not license_id or license_id == "Unknown":
        return "UNKNOWN"
    normalized = license_id.strip()
    if normalized in PERMISSIVE:
        return "PERMISSIVE"
    if normalized in WEAK_COPYLEFT:
        return "WEAK_COPYLEFT"
    if normalized in COPYLEFT:
        return "COPYLEFT"
    return "UNKNOWN"


def evaluate_policy(component_name: str, license_id: str, policy: str = "permissive-only") -> tuple[bool, str]:
    classification = classify_license(license_id)

    if policy == "permissive-only":
        if classification == "COPYLEFT":
            return True, (
                f"{license_id} dependency detected ({component_name}) in a project with a "
                f"permissive-license policy. Strong copyleft licenses like {license_id} can require "
                f"derivative works to be released under the same license — legal review recommended "
                f"before distribution."
            )
        if classification == "WEAK_COPYLEFT":
            return True, (
                f"{component_name} is licensed under {license_id} (weak copyleft). Permitted for "
                f"dynamic linking in most cases, but flagged for review under a permissive-only policy."
            )
        if classification == "UNKNOWN":
            return True, (
                f"{component_name} has no machine-readable license metadata. Unknown-license packages "
                f"are flagged by default until manually verified."
            )
        return False, f"{license_id} is a permissive license, compliant with the permissive-only policy."

    return False, f"{license_id} evaluated under policy '{policy}': no violation detected."
